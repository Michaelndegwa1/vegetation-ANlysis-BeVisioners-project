"""CanopyLedger ingest per site (docs/specs/02-ingest-spec.md).

For each site in sites.geojson and each month: summary statistics of S2 indices and S1 backscatter
for the site polygon and its leakage ring, for all pixels, Hansen tree pixels and WorldCover woody (tree+shrub) pixels.
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
    if C.SKIP_FILE.exists():
        skip = {ln.strip() for ln in C.SKIP_FILE.read_text(encoding='utf-8').splitlines()
                if ln.strip() and not ln.startswith('#')}
        skipped = [f['properties']['site_id'] for f in feats if f['properties']['site_id'] in skip]
        if skipped:
            print(f'SKIPPED by {C.SKIP_FILE.name}: {skipped}')
        feats = [f for f in feats if f['properties']['site_id'] not in skip]
    if only:
        known = {f['properties']['site_id'] for f in feats}
        missing = set(only) - known - (skip if C.SKIP_FILE.exists() else set())
        if missing:
            raise SystemExit(f'unknown site_id(s): {sorted(missing)}; known: {sorted(known)}')
        feats = [f for f in feats if f['properties']['site_id'] in only]
    return feats


def site_geometries(feat):
    """(site, ring) as ee.Geometry. Ring = buffer(site, m) minus site."""
    site = ee.Geometry(feat['geometry'], None, False)
    ring = site.buffer(feat['properties']['leakage_buffer_m'], 20).difference(site, 20)
    return site, ring


def zone_geometries(feat):
    """{zone: ee.Geometry}. 'site' plus cumulative rings 'ring_<km>km' = buffer(site, w) minus site
    for each width in leakage_rings_m."""
    site = ee.Geometry(feat['geometry'], None, False)
    zones = {'site': site}
    for w in feat['properties']['leakage_rings_m']:
        zones[f'ring_{w // 1000}km'] = site.buffer(w, 20).difference(site, 20)
    return zones


def collection_aoi(feat):
    """Region used to filter imagery: the site buffered by the widest ring."""
    site = ee.Geometry(feat['geometry'], None, False)
    return site.buffer(max(feat['properties']['leakage_rings_m']), 20)


def protected_free(aoi):
    """Image that is 1 outside WDPA protected areas and 0 inside (polygons rasterised at use scale)."""
    wdpa = ee.FeatureCollection(C.DS_WDPA).filterBounds(aoi)
    return ee.Image(0).byte().paint(wdpa, 1).eq(0)


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
    # lossyear is MASKED (not 0) where there was no loss; without unmask(0) the whole mask turns
    # masked there and only pixels with later loss survive (bug found 2026-11-24 in v0.2/v0.3 runs).
    ly = h.select('lossyear').unmask(0)
    lost_before = ly.gt(0).And(ly.lt(year - 2000))
    return h.select('treecover2000').unmask(0).gte(tree_min).And(lost_before.Not())


def woody_mask():
    """WorldCover 2021 tree (10) or shrub (20). Static map, so it does not respond to loss after 2021;
    used to describe woody vegetation at dryland sites where Hansen tree cover is near zero."""
    wc = ee.ImageCollection(C.DS_WORLDCOVER).first().select('Map')
    return wc.eq(10).Or(wc.eq(20))


# ---------------------------------------------------------------- statistics
def _reducer():
    r = (ee.Reducer.mean().combine(ee.Reducer.median(), sharedInputs=True)
         .combine(ee.Reducer.percentile([10, 90]), sharedInputs=True)
         .combine(ee.Reducer.stdDev(), sharedInputs=True)
         .combine(ee.Reducer.count(), sharedInputs=True))
    return r


def _mask_variants(img, y, props):
    woody = woody_mask()
    tmask = tree_mask(y, props.get('tree_cover_min', C.TREE_COVER_MIN_DEFAULT))
    return (('all', img), ('tree', img.updateMask(tmask)), ('woody', img.updateMask(woody)))


def _zone_images(img, zones, props, aoi):
    """(zone, geometry, image) with protected areas removed from the rings when configured."""
    out = []
    pf = protected_free(aoi) if props.get('mask_protected_in_ring') else None
    for zone, geom in zones.items():
        zimg = img if (zone == 'site' or pf is None) else img.updateMask(pf)
        out.append((zone, geom, zimg))
    return out


def month_features(site_id, props, zones, aoi, s2, s1, y, m):
    """Server-side: list of Features (zone x mask) for one month."""
    comp = month_composite(s2, s1, y, m)
    valid = comp.select('S2_N').unmask(0).gt(0).rename('valid').toFloat()
    one = ee.Image.constant(1).rename('one').toFloat()
    img = ee.Image.cat([comp, valid, one])
    out = []
    for zone, geom, zimg in _zone_images(img, zones, props, aoi):
        for mask_name, image in _mask_variants(zimg, y, props):
            stats = image.reduceRegion(
                reducer=_reducer(), geometry=geom, scale=C.STATS_SCALE_M,
                maxPixels=1e13, tileScale=C.TILE_SCALE)
            out.append(ee.Feature(None, stats).set(
                {'site_id': site_id, 'zone': zone, 'year': y, 'month': m, 'mask': mask_name}))
    return out


def coverage_features(site_id, props, zones, aoi, s2, y):
    """Yearly VM0009 double-coverage statistic: share of pixels with >= 2 clear S2 observations in
    the calendar year, per zone and mask. Written with month = 0."""
    s2y = s2.merge(ee.ImageCollection([_masked_dummy(['NDVI', 'EVI', 'NDWI'])]))
    n = s2y.select('NDVI').count()
    img = ee.Image.cat([n.gte(2).rename('n_ge2').toFloat(), ee.Image.constant(1).rename('one').toFloat()])
    red = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    out = []
    for zone, geom, zimg in _zone_images(img, zones, props, aoi):
        for mask_name, image in _mask_variants(zimg, y, props):
            stats = image.reduceRegion(reducer=red, geometry=geom, scale=C.STATS_SCALE_M,
                                       maxPixels=1e13, tileScale=C.TILE_SCALE)
            out.append(ee.Feature(None, stats).set(
                {'site_id': site_id, 'zone': zone, 'year': y, 'month': 0, 'mask': mask_name}))
    return out


def site_year_collection(feat, y, s2, s1):
    p = feat['properties']
    zones, aoi = zone_geometries(feat), collection_aoi(feat)
    feats = coverage_features(p['site_id'], p, zones, aoi, s2, y)
    for m in range(1, 13):
        feats += month_features(p['site_id'], p, zones, aoi, s2, s1, y, m)
    return ee.FeatureCollection(feats)


# ---------------------------------------------------------------- tables
def to_long(wide, boundary_quality):
    """Wide rows (one per site/zone/year/month/mask) -> long format of spec 02."""
    rows = []
    for r in wide:
        n_pix = r.get('one_count')
        if int(r['month']) == 0:  # yearly coverage row (VM0009 double-coverage test)
            rows.append(dict(site_id=r['site_id'], zone=r['zone'], year=int(r['year']), month=0,
                             mask=r['mask'], n_pixels=n_pix or 0, valid_frac=None, s2_n_mean=None,
                             low_coverage=0, boundary_quality=boundary_quality,
                             band='_coverage', stat='frac_n_ge2', value=r.get('n_ge2_mean')))
            continue
        valid_frac = r.get('valid_mean')
        low = int(valid_frac is None or valid_frac < C.LOW_COVERAGE_FRAC)
        base = dict(site_id=r['site_id'], zone=r['zone'], year=int(r['year']),
                    month=int(r['month']), mask=r['mask'], n_pixels=n_pix,
                    valid_frac=valid_frac, s2_n_mean=r.get('S2_N_mean'),
                    low_coverage=low, boundary_quality=boundary_quality)
        n_before = len(rows)
        for band in C.BANDS_OUT:
            for st in STAT_NAMES:
                v = r.get(f'{band}_{st}')
                if v is not None:
                    rows.append(dict(base, band=band, stat=st, value=v))
        if len(rows) == n_before:  # no valid pixels: keep a visible row instead of dropping the cell
            rows.append(dict(base, n_pixels=n_pix or 0, band='_none', stat='_none', value=None))
    cols = ['site_id', 'zone', 'year', 'month', 'mask', 'band', 'stat', 'value', 'n_pixels',
            'valid_frac', 's2_n_mean', 'low_coverage', 'boundary_quality']
    df = pd.DataFrame(rows, columns=cols)
    # GEE parallel summation differs ~1e-14 between runs; rounding keeps outputs reproducible
    df[['value', 'valid_frac', 's2_n_mean']] = df[['value', 'valid_frac', 's2_n_mean']].astype(float).round(6)
    return df.sort_values(['zone', 'mask', 'month', 'band', 'stat']).reset_index(drop=True)


def sanity_flags(df):
    flags = []
    for mask, bounds in C.SANITY.items():
        for band, (lo, hi) in bounds.items():
            sub = df[(df['mask'] == mask) & (df.band == band) & (df.stat == 'mean')]
            bad = sub[(sub.value < lo) | (sub.value > hi)]
            for _, r in bad.iterrows():
                flags.append(f'{r.zone}/{mask} {r.year}-{r.month:02d} {band} mean={r.value:.3f} '
                             f'outside {lo}..{hi}')
    return flags


def _coverage_pass(df):
    c = df[(df.band == '_coverage') & (df.zone == 'site') & (df['mask'] == 'all')]
    return None if c.empty or pd.isna(c.value.iloc[0]) else bool(c.value.iloc[0] >= C.COVERAGE_MIN_AREA_FRAC)


def write_outputs(df, site_id, year, feat, extra):
    C.STATS_DIR.mkdir(parents=True, exist_ok=True)
    csv = C.STATS_DIR / f'{site_id}_{year}.csv'
    df.to_csv(csv, index=False)
    side = {
        'site_id': site_id, 'year': year, 'spec': C.SPEC_VERSION,
        'run_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
        'datasets': [C.DS_S2, C.DS_S2_CLOUD, C.DS_S1, C.DS_HANSEN, C.DS_WORLDCOVER, C.DS_WDPA],
        'parameters': {k: getattr(C, k) for k in (
            'CLOUD_PROB_MAX', 'CLOUD_DILATE_M', 'STATS_SCALE_M', 'TILE_SCALE',
            'LOW_COVERAGE_FRAC', 'TREE_COVER_MIN_DEFAULT', 'COVERAGE_MIN_AREA_FRAC')},
        'boundary_quality': feat['properties']['boundary_quality'],
        'position_error_km': feat['properties']['position_error_km'],
        'rows': int(len(df)),
        'pipeline_version': C.PIPELINE_VERSION,
        'tree_mask_version': 'v2 (lossyear unmask fix, 2026-11-24); earlier files have an almost empty tree mask',
        'leakage_rings_m': feat['properties']['leakage_rings_m'],
        'mask_protected_in_ring': feat['properties']['mask_protected_in_ring'],
        's1_preprocessing': 'none: plain median of all IW scenes (spec v0.3 orbit/speckle/terrain steps NOT yet implemented)',
        'double_coverage_ge90pct_site_all': _coverage_pass(df),
    }
    side.update(extra)
    csv.with_suffix('.json').write_text(json.dumps(side, indent=1), encoding='utf-8')
    return csv


# ---------------------------------------------------------------- CLI actions
def scene_report(feats, years):
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


def _get_info(fc, label):
    for attempt in range(4):
        try:
            return fc.getInfo()
        except ee.EEException as e:
            print(f'    {label} attempt {attempt + 1} failed: {e}', flush=True)
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f'{label} failed after retries')


def run_local(feats, years):
    """getInfo mode: for tests and small sites. A failed site-year is logged and skipped (nothing
    written for it); the run continues and exits non-zero at the end if anything failed."""
    failures = []
    for feat in feats:
        p = feat['properties']
        zones, aoi = zone_geometries(feat), collection_aoi(feat)
        for y in range(years[0], years[1] + 1):
            t0 = time.time()
            try:
                s2 = load_s2(aoi, f'{y}-01-01', f'{y + 1}-01-01')
                s1 = load_s1(aoi, f'{y}-01-01', f'{y + 1}-01-01')
                wide = []
                # one getInfo per unit (12 reductions): many at once hit "Too many concurrent aggregations"
                fc = ee.FeatureCollection(coverage_features(p['site_id'], p, zones, aoi, s2, y))
                wide += [f['properties'] for f in _get_info(fc, f'coverage {y}')['features']]
                for m in range(1, 13):
                    fc = ee.FeatureCollection(month_features(p['site_id'], p, zones, aoi, s2, s1, y, m))
                    wide += [f['properties'] for f in _get_info(fc, f'month {m}')['features']]
                    print(f"  {p['site_id']} {y}-{m:02d} done ({time.time() - t0:.0f}s)", flush=True)
            except RuntimeError as e:
                print(f"  FAILED {p['site_id']} {y}: {e}; nothing written, continuing", flush=True)
                failures.append(f"{p['site_id']} {y}")
                continue
            df = to_long(wide, p['boundary_quality'])
            csv = write_outputs(df, p['site_id'], y, feat, {'mode': 'local',
                                                            'seconds': round(time.time() - t0, 1)})
            print(f'  wrote {csv} ({len(df)} rows, {time.time() - t0:.0f}s)', flush=True)
            for fl in sanity_flags(df):
                print('  SANITY', fl)
    if failures:
        print('FAILED SITE-YEARS (re-run these):', failures)
        raise SystemExit(1)


def run_drive(feats, years):
    for feat in feats:
        p = feat['properties']
        aoi = collection_aoi(feat)
        for y in range(years[0], years[1] + 1):
            s2 = load_s2(aoi, f'{y}-01-01', f'{y + 1}-01-01')
            s1 = load_s1(aoi, f'{y}-01-01', f'{y + 1}-01-01')
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
        scene_report(feats, (a.start, a.end))
        print('\nDry run only. Add --run to compute statistics.')
        return
    (run_local if a.mode == 'local' else run_drive)(feats, (a.start, a.end))


if __name__ == '__main__':
    main()
