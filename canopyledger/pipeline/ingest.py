"""CanopyLedger ingest per site (docs/specs/02-ingest-spec.md).

For each site in sites.geojson and each month: summary statistics of S2 indices and S1 backscatter
for the site polygon and its leakage ring, for all pixels and for Hansen tree-mask pixels.
Writes small long-format CSV tables, no rasters.

Usage (run from the repo root with PYTHONPATH=.):
  python -m canopyledger.pipeline.ingest --sites kasigau_ph1_rukinga --start 2023 --end 2023
      dry run: per-month scene counts over each polygon
  ... --run                  compute statistics via getInfo and write data/processed/stats
  ... --run --mode drive     start Drive CSV export tasks (large sites); convert downloads with
  python -m canopyledger.pipeline.ingest --from-csv <downloaded.csv>
"""
import argparse
import datetime
import json
import time

import ee
import pandas as pd
from shapely.geometry import shape

from canopyledger import config as C
from canopyledger.sites.validate import validate

STAT_NAMES = ['mean', 'median', 'p10', 'p90', 'stdDev']


def init_ee():
    try:
        ee.Initialize(project=C.GEE_PROJECT)
    except Exception as e:
        print(f'Earth Engine init failed ({e}); authenticating...')
        ee.Authenticate()
        ee.Initialize(project=C.GEE_PROJECT)


# ---------------------------------------------------------------- sites
def load_sites(only=None):
    errors, warnings = validate(C.SITES_FILE)
    for w in warnings:
        print('WARN ', w)
    if errors:
        raise SystemExit('sites.geojson invalid:\n  ' + '\n  '.join(errors))
    feats = json.loads(C.SITES_FILE.read_text(encoding='utf-8'))['features']
    if only:
        known = {f['properties']['site_id'] for f in feats}
        missing = set(only) - known
        if missing:
            raise SystemExit(f'unknown site_id(s): {sorted(missing)}; known: {sorted(known)}')
        feats = [f for f in feats if f['properties']['site_id'] in only]
    return feats


def site_geometries(feat):
    """(site, ring) as ee.Geometry. Ring = buffer(site, m) minus site."""
    site = ee.Geometry(feat['geometry'], None, False)
    ring = site.buffer(feat['properties']['leakage_buffer_m'], 20).difference(site, 20)
    return site, ring


# ---------------------------------------------------------------- imagery
def load_s2(aoi, start, end):
    s2 = ee.ImageCollection(C.DS_S2).filterBounds(aoi).filterDate(start, end)
    clouds = ee.ImageCollection(C.DS_S2_CLOUD).filterBounds(aoi).filterDate(start, end)
    joined = ee.ImageCollection(ee.Join.saveFirst('cloud_prob').apply(
        primary=s2, secondary=clouds,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))

    def mask_and_index(img):
        prob_img = ee.Image(img.get('cloud_prob'))
        # unmatched scene -> treated as fully cloudy
        prob = ee.Image(ee.Algorithms.If(
            prob_img, prob_img.select('probability'), ee.Image.constant(100)))
        scl = img.select('SCL')
        bad = prob.gt(C.CLOUD_PROB_MAX).Or(scl.eq(3)).Or(scl.eq(1))
        bad = (bad.focalMax(C.CLOUD_DILATE_M, 'circle', 'meters')
               .reproject(crs=img.select('B4').projection(), scale=20))
        refl = img.select(['B2', 'B3', 'B4', 'B8']).multiply(0.0001).updateMask(bad.Not())
        ndvi = refl.normalizedDifference(['B8', 'B4']).rename('NDVI')
        evi = refl.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {'NIR': refl.select('B8'), 'RED': refl.select('B4'), 'BLUE': refl.select('B2')}
        ).rename('EVI')
        ndwi = refl.normalizedDifference(['B3', 'B8']).rename('NDWI')  # McFeeters
        return (ee.Image.cat([ndvi, evi, ndwi]).toFloat()
                .copyProperties(img, ['system:time_start']))

    return joined.map(mask_and_index)


def load_s1(aoi, start, end):
    s1 = (ee.ImageCollection(C.DS_S1).filterBounds(aoi).filterDate(start, end)
          .filter(ee.Filter.eq('instrumentMode', 'IW'))
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))

    def prep(img):  # GRD in GEE is already in dB
        vv, vh = img.select('VV'), img.select('VH')
        return (ee.Image.cat([vv, vh, vh.subtract(vv).rename('VH_VV')]).toFloat()
                .copyProperties(img, ['system:time_start']))

    return s1.map(prep)


def _masked_dummy(names):
    """Fully masked image with the given bands, so median()/count() on an empty month still
    yields every band (all masked) instead of an image with no bands."""
    return ee.Image.constant([0] * len(names)).rename(names).toFloat().updateMask(0)


def month_composite(s2, s1, y, m):
    t0 = ee.Date.fromYMD(y, m, 1)
    t1 = t0.advance(1, 'month')
    s2m = s2.filterDate(t0, t1).merge(ee.ImageCollection([_masked_dummy(['NDVI', 'EVI', 'NDWI'])]))
    s1m = s1.filterDate(t0, t1).merge(ee.ImageCollection([_masked_dummy(['VV', 'VH', 'VH_VV'])]))
    s2_n = s2m.select('NDVI').count().rename('S2_N').toFloat()
    return ee.Image.cat([s2m.median(), s1m.median(), s2_n])


def tree_mask(year, tree_min):
    """Hansen treecover2000 >= tree_min and not lost in an EARLIER year (loss in the same year
    still counts as tree; lossyear is 1..24 for 2001..2024)."""
    h = ee.Image(C.DS_HANSEN)
    lost_before = h.select('lossyear').gt(0).And(h.select('lossyear').lt(year - 2000))
    return h.select('treecover2000').gte(tree_min).And(lost_before.Not())


# ---------------------------------------------------------------- statistics
def _reducer():
    r = (ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True)
         .combine(ee.Reducer.percentile([10, 90]), sharedInputs=True)
         .combine(ee.Reducer.stdDev(), sharedInputs=True)
         .combine(ee.Reducer.count(), sharedInputs=True))
    return r


def month_features(site_id, props, geoms, s2, s1, y, m):
    """Server-side: ee.List of 4 Features (zone x mask) for one month."""
    comp = month_composite(s2, s1, y, m)
    valid = comp.select('S2_N').unmask(0).gt(0).rename('valid').toFloat()
    one = ee.Image.constant(1).rename('one').toFloat()
    img = ee.Image.cat([comp, valid, one])
    tmask = tree_mask(y, props.get('tree_cover_min', C.TREE_COVER_MIN_DEFAULT))
    out = []
    for zone, geom in zip(('site', 'ring'), geoms):
        for mask_name, image in (('all', img), ('tree', img.updateMask(tmask))):
            stats = image.reduceRegion(
                reducer=_reducer(), geometry=geom, scale=C.STATS_SCALE_M,
                maxPixels=1e13, tileScale=C.TILE_SCALE)
            out.append(ee.Feature(None, stats).set(
                {'site_id': site_id, 'zone': zone, 'year': y, 'month': m, 'mask': mask_name}))
    return out


def site_year_collection(feat, y, s2, s1):
    p = feat['properties']
    geoms = site_geometries(feat)
    feats = []
    for m in range(1, 13):
        feats += month_features(p['site_id'], p, geoms, s2, s1, y, m)
    return ee.FeatureCollection(feats)


# ---------------------------------------------------------------- tables
def to_long(wide, boundary_quality):
    """Wide rows (one per site/zone/year/month/mask) -> long format of spec 02."""
    rows = []
    for r in wide:
        n_pix = r.get('one_count')
        valid_frac = r.get('valid_mean')
        low = int(valid_frac is None or valid_frac < C.LOW_COVERAGE_FRAC)
        base = dict(site_id=r['site_id'], zone=r['zone'], year=int(r['year']),
                    month=int(r['month']), mask=r['mask'], n_pixels=n_pix,
                    valid_frac=valid_frac, s2_n_mean=r.get('S2_N_mean'),
                    low_coverage=low, boundary_quality=boundary_quality)
        for band in C.BANDS_OUT:
            for st in STAT_NAMES:
                v = r.get(f'{band}_{st}')
                if v is not None:
                    rows.append(dict(base, band=band, stat=st, value=v))
    cols = ['site_id', 'zone', 'year', 'month', 'mask', 'band', 'stat', 'value', 'n_pixels',
            'valid_frac', 's2_n_mean', 'low_coverage', 'boundary_quality']
    df = pd.DataFrame(rows, columns=cols)
    return df.sort_values(['zone', 'mask', 'month', 'band', 'stat']).reset_index(drop=True)


def sanity_flags(df):
    flags = []
    for band, (lo, hi) in C.SANITY.items():
        sub = df[(df.band == band) & (df.stat == 'mean')]
        bad = sub[(sub.value < lo) | (sub.value > hi)]
        for _, r in bad.iterrows():
            flags.append(f'{r.zone}/{r["mask"]} {r.year}-{r.month:02d} {band} mean={r.value:.3f} '
                         f'outside {lo}..{hi}')
    return flags


def write_outputs(df, site_id, year, feat, extra):
    C.STATS_DIR.mkdir(parents=True, exist_ok=True)
    csv = C.STATS_DIR / f'{site_id}_{year}.csv'
    df.to_csv(csv, index=False)
    side = {
        'site_id': site_id, 'year': year, 'spec': C.SPEC_VERSION,
        'run_utc': datetime.datetime.utcnow().isoformat(timespec='seconds'),
        'datasets': [C.DS_S2, C.DS_S2_CLOUD, C.DS_S1, C.DS_HANSEN],
        'parameters': {k: getattr(C, k) for k in (
            'CLOUD_PROB_MAX', 'CLOUD_DILATE_M', 'STATS_SCALE_M', 'TILE_SCALE',
            'LOW_COVERAGE_FRAC', 'TREE_COVER_MIN_DEFAULT')},
        'boundary_quality': feat['properties']['boundary_quality'],
        'position_error_km': feat['properties']['position_error_km'],
        'rows': int(len(df)),
    }
    side.update(extra)
    csv.with_suffix('.json').write_text(json.dumps(side, indent=1), encoding='utf-8')
    return csv


# ---------------------------------------------------------------- CLI actions
def coverage_report(feats, years):
    """Scene counts per month over each polygon (scenes intersecting; NOT clear-pixel coverage)."""
    for feat in feats:
        p = feat['properties']
        site, _ = site_geometries(feat)
        y0, y1 = years
        s2 = ee.ImageCollection(C.DS_S2).filterBounds(site)
        s1 = (ee.ImageCollection(C.DS_S1).filterBounds(site)
              .filter(ee.Filter.eq('instrumentMode', 'IW')))
        months = [(y, m) for y in range(y0, y1 + 1) for m in range(1, 13)]

        def counts(ym):
            ym = ee.List(ym)
            t0 = ee.Date.fromYMD(ym.get(0), ym.get(1), 1)
            t1 = t0.advance(1, 'month')
            return ee.List([s2.filterDate(t0, t1).size(), s1.filterDate(t0, t1).size()])

        res = ee.List([counts([y, m]) for y, m in months]).getInfo()
        print(f"\n== {p['site_id']} ({p['boundary_quality']} boundary, +/-{p['position_error_km']} km)")
        print(f"{'month':8}{'S2 scenes':>10}{'S1 scenes':>10}")
        for (y, m), (n2, n1) in zip(months, res):
            note = '  <- no S2' if n2 == 0 else ''
            print(f'{y}-{m:02d}{n2:10d}{n1:10d}{note}')
    print('\nCounts are scenes intersecting the polygon, not clear-pixel coverage; '
          'valid_frac in the stats output gives that.')


def run_local(feats, years):
    for feat in feats:
        p = feat['properties']
        site, _ = site_geometries(feat)
        for y in range(years[0], years[1] + 1):
            t0 = time.time()
            start, end = f'{y}-01-01', f'{y + 1}-01-01'
            # S2 only from monitoring_start; earlier months still get S1 (from S1_FIRST_YEAR)
            s2 = load_s2(site.buffer(p['leakage_buffer_m']), start, end)
            s1 = load_s1(site.buffer(p['leakage_buffer_m']), start, end)
            geoms = site_geometries(feat)
            wide = []
            # one getInfo per month (4 reductions): 48 at once hits "Too many concurrent aggregations"
            for m in range(1, 13):
                fc = ee.FeatureCollection(month_features(p['site_id'], p, geoms, s2, s1, y, m))
                info = None
                for attempt in range(4):
                    try:
                        info = fc.getInfo()
                        break
                    except ee.EEException as e:
                        print(f'    month {m} attempt {attempt + 1} failed: {e}', flush=True)
                        time.sleep(20 * (attempt + 1))
                if info is None:
                    raise SystemExit(f'month {y}-{m:02d} failed after retries; nothing written')
                wide += [f['properties'] for f in info['features']]
                print(f"  {p['site_id']} {y}-{m:02d} done ({time.time() - t0:.0f}s)", flush=True)
            df = to_long(wide, p['boundary_quality'])
            csv = write_outputs(df, p['site_id'], y, feat, {'mode': 'local',
                                                            'seconds': round(time.time() - t0, 1)})
            print(f'  wrote {csv} ({len(df)} rows, {time.time() - t0:.0f}s)')
            for fl in sanity_flags(df):
                print('  SANITY', fl)


def run_drive(feats, years):
    for feat in feats:
        p = feat['properties']
        site, _ = site_geometries(feat)
        for y in range(years[0], years[1] + 1):
            s2 = load_s2(site.buffer(p['leakage_buffer_m']), f'{y}-01-01', f'{y + 1}-01-01')
            s1 = load_s1(site.buffer(p['leakage_buffer_m']), f'{y}-01-01', f'{y + 1}-01-01')
            fc = site_year_collection(feat, y, s2, s1)
            name = f"{p['site_id']}_{y}_wide"
            task = ee.batch.Export.table.toDrive(
                collection=fc, description=name, folder=C.DRIVE_FOLDER,
                fileNamePrefix=name, fileFormat='CSV')
            task.start()
            print(f'started Drive export {name}')
    print(f'\nTasks: https://code.earthengine.google.com/tasks  (folder {C.DRIVE_FOLDER}).'
          '\nConvert each download with --from-csv.')


def convert_csv(path):
    from pathlib import Path
    path = Path(path)
    df = pd.read_csv(path)
    feats = {f['properties']['site_id']: f for f in load_sites()}
    out_frames = []
    for (sid, y), g in df.groupby(['site_id', 'year']):
        feat = feats[sid]
        long = to_long(g.where(g.notna(), None).to_dict('records'), feat['properties']['boundary_quality'])
        csv = write_outputs(long, sid, int(y), feat, {'mode': 'drive', 'source_csv': path.name})
        print(f'wrote {csv} ({len(long)} rows)')
        for fl in sanity_flags(long):
            print('  SANITY', fl)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('--sites', nargs='*', help='site_id list (default: all)')
    ap.add_argument('--start', type=int, default=2019)
    ap.add_argument('--end', type=int, default=2024)
    ap.add_argument('--run', action='store_true', help='compute statistics (default: dry run)')
    ap.add_argument('--mode', choices=['local', 'drive'], default='local')
    ap.add_argument('--from-csv', help='convert a downloaded wide Drive CSV to long outputs')
    a = ap.parse_args()

    if a.from_csv:
        convert_csv(a.from_csv)
        return
    init_ee()
    feats = load_sites(a.sites)
    print(f"Sites: {[f['properties']['site_id'] for f in feats]}  years {a.start}-{a.end}")
    if not a.run:
        coverage_report(feats, (a.start, a.end))
        print('\nDry run only. Add --run to compute statistics.')
        return
    (run_local if a.mode == 'local' else run_drive)(feats, (a.start, a.end))


if __name__ == '__main__':
    main()
