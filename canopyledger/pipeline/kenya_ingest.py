"""
CanopyLedger Kenya - Week 1 ingestion (adapted from `data colecetion.py`).

What changed versus the UK script
  1. Pixel-level cloud masking with s2cloudless (+ SCL shadow mask) instead of the
     15% whole-scene CLOUDY_PIXEL_PERCENTAGE filter, which would discard most
     rainy-season scenes in Kenya.
  2. Sentinel-1 VV / VH monthly medians (radar sees through cloud).
  3. Monthly composites built server-side (no getInfo() inside the month loop).
  4. Per-month count of clear Sentinel-2 observations (S2_N) so gaps are visible.
  5. Safe by default: prints a coverage report and exports NOTHING unless --export.

Usage
  python kenya_ingest.py                          # coverage report only
  python kenya_ingest.py --start 2019 --end 2024  # restrict years
  python kenya_ingest.py --export                 # start Drive export tasks
  python kenya_ingest.py --export --wait          # ...and poll until finished

Output bands per month (Float32, EPSG:32736, 10 m):
  NDVI, EVI, NDWI, VV, VH, VH_VV (dB difference), S2_N
"""
import argparse
import time

import ee

# ----------------------------------------------------------------------------
# CONFIG - edit here
# ----------------------------------------------------------------------------
GEE_PROJECT = 'premium-episode-423509-g8'

# PLACEHOLDER pilot AOI: a ~22 km x 17 km box over part of the Mau Forest
# Complex (Eastern/South-West Mau, Rift Valley). ~370 km2.
# Replace with the real pilot landscape / site polygons once chosen.
AOI_LON_MIN, AOI_LON_MAX = 35.55, 35.75
AOI_LAT_MIN, AOI_LAT_MAX = -0.60, -0.45

# Sentinel-2 L2A over Africa is patchy before ~2019 in GEE; the coverage report
# shows how many clear scenes each month really has.
START_YEAR_DEFAULT = 2018
END_YEAR_DEFAULT = 2024

EXPORT_CRS = 'EPSG:32736'   # WGS84 / UTM 36S (35.6E, 0.5S is in zone 36, southern hemisphere)
EXPORT_SCALE = 10
EXPORT_FOLDER = 'canopyledger_kenya_pilot'
FILE_PREFIX = 'Kenya_Mau_S2S1'

CLOUD_PROB_MAX = 40         # s2cloudless probability (%) above which a pixel is masked
CLOUD_DILATE_M = 100        # grow the cloud mask to catch thin edges
MIN_CLEAR_OBS = 1           # months with fewer clear S2 observations are skipped

BANDS_OUT = ['NDVI', 'EVI', 'NDWI', 'VV', 'VH', 'VH_VV', 'S2_N']


def init_ee():
    try:
        ee.Initialize(project=GEE_PROJECT)
    except Exception as e:  # not authenticated yet
        print(f"Earth Engine init failed ({e}); authenticating...")
        ee.Authenticate()
        ee.Initialize(project=GEE_PROJECT)


# ----------------------------------------------------------------------------
# Sentinel-2: s2cloudless masking + indices
# ----------------------------------------------------------------------------
def load_s2(aoi, start, end):
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
          .filterBounds(aoi).filterDate(start, end))
    clouds = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
              .filterBounds(aoi).filterDate(start, end))

    joined = ee.ImageCollection(ee.Join.saveFirst('cloud_prob').apply(
        primary=s2, secondary=clouds,
        condition=ee.Filter.equals(leftField='system:index', rightField='system:index')))

    def mask_and_index(img):
        prob_img = ee.Image(img.get('cloud_prob'))  # missing match -> handled below
        prob = ee.Image(ee.Algorithms.If(
            prob_img, prob_img.select('probability'), ee.Image.constant(100)))
        cloud = prob.gt(CLOUD_PROB_MAX)
        # SCL 3 = cloud shadow, 1 = saturated/defective
        scl = img.select('SCL')
        bad = cloud.Or(scl.eq(3)).Or(scl.eq(1))
        # dilate: erode the "clear" mask
        bad = (bad.focalMax(CLOUD_DILATE_M, 'circle', 'meters')
               .reproject(crs=img.select('B4').projection(), scale=20))
        refl = img.select(['B2', 'B3', 'B4', 'B8']).multiply(0.0001)
        refl = refl.updateMask(bad.Not())

        ndvi = refl.normalizedDifference(['B8', 'B4']).rename('NDVI')
        evi = refl.expression(
            '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
            {'NIR': refl.select('B8'), 'RED': refl.select('B4'), 'BLUE': refl.select('B2')}
        ).rename('EVI')
        ndwi = refl.normalizedDifference(['B3', 'B8']).rename('NDWI')
        return (ee.Image.cat([ndvi, evi, ndwi]).toFloat()
                .copyProperties(img, ['system:time_start']))

    return joined.map(mask_and_index)


# ----------------------------------------------------------------------------
# Sentinel-1: VV / VH
# ----------------------------------------------------------------------------
def load_s1(aoi, start, end):
    s1 = (ee.ImageCollection('COPERNICUS/S1_GRD')
          .filterBounds(aoi).filterDate(start, end)
          .filter(ee.Filter.eq('instrumentMode', 'IW'))
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
          .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')))

    def prep(img):
        vv = img.select('VV')
        vh = img.select('VH')
        # GEE S1_GRD is already in dB.
        return (ee.Image.cat([vv, vh, vh.subtract(vv).rename('VH_VV')]).toFloat()
                .copyProperties(img, ['system:time_start']))

    return s1.map(prep)


# ----------------------------------------------------------------------------
# Monthly composites (server-side)
# ----------------------------------------------------------------------------
def month_starts(start_year, end_year):
    return [(y, m) for y in range(start_year, end_year + 1) for m in range(1, 13)]


def build_month(s2, s1, y, m):
    t0 = ee.Date.fromYMD(y, m, 1)
    t1 = t0.advance(1, 'month')
    s2m = s2.filterDate(t0, t1)
    s1m = s1.filterDate(t0, t1)
    s2_n = s2m.select('NDVI').count().rename('S2_N').toFloat()
    comp = ee.Image.cat([s2m.median(), s1m.median(), s2_n])
    return (comp.select(BANDS_OUT)
            .set({'year': y, 'month': m, 'system:time_start': t0.millis()}))


def coverage_report(s2, s1, months):
    """One batched getInfo for S2-clear-scene and S1-scene counts per month."""
    def counts(ym):
        ym = ee.List(ym)
        t0 = ee.Date.fromYMD(ym.get(0), ym.get(1), 1)
        t1 = t0.advance(1, 'month')
        return ee.List([s2.filterDate(t0, t1).size(), s1.filterDate(t0, t1).size()])

    out = ee.List([counts([y, m]) for y, m in months]).getInfo()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', type=int, default=START_YEAR_DEFAULT)
    ap.add_argument('--end', type=int, default=END_YEAR_DEFAULT)
    ap.add_argument('--export', action='store_true', help='start Drive export tasks')
    ap.add_argument('--wait', action='store_true', help='poll export tasks until done')
    ap.add_argument('--folder', default=EXPORT_FOLDER)
    args = ap.parse_args()

    init_ee()

    aoi = ee.Geometry.Rectangle([AOI_LON_MIN, AOI_LAT_MIN, AOI_LON_MAX, AOI_LAT_MAX])
    area_km2 = aoi.area(1).divide(1e6).getInfo()
    print(f"AOI: lon {AOI_LON_MIN}..{AOI_LON_MAX}, lat {AOI_LAT_MIN}..{AOI_LAT_MAX}  "
          f"(~{area_km2:.0f} km2)  [PLACEHOLDER - confirm pilot area]")

    start = f'{args.start}-01-01'
    end = f'{args.end + 1}-01-01'
    s2 = load_s2(aoi, start, end)
    s1 = load_s1(aoi, start, end)

    months = month_starts(args.start, args.end)
    print(f"\nChecking scene coverage for {len(months)} months...")
    cov = coverage_report(s2, s1, months)

    usable = []
    print(f"\n{'month':8} {'S2 scenes':>9} {'S1 scenes':>9}")
    for (y, m), (n2, n1) in zip(months, cov):
        flag = '' if n2 >= MIN_CLEAR_OBS else '  <- skipped (no S2)'
        print(f"{y}-{m:02d}  {n2:9d} {n1:9d}{flag}")
        if n2 >= MIN_CLEAR_OBS:
            usable.append((y, m))
    print(f"\nUsable months: {len(usable)} / {len(months)}")
    print("Note: S2 scene counts are BEFORE cloud masking; check the S2_N band in the "
          "exports for true clear-pixel counts per month.")

    if not args.export:
        print("\nDry run only. Re-run with --export to start Drive export tasks.")
        return

    n_bands = len(BANDS_OUT)
    est_mb = area_km2 * 1e6 / (EXPORT_SCALE ** 2) * n_bands * 4 / 1e6
    print(f"\nExporting {len(usable)} GeoTIFFs (~{est_mb:.0f} MB each, "
          f"~{est_mb * len(usable) / 1000:.1f} GB total) to Drive folder '{args.folder}'")

    tasks = []
    for y, m in usable:
        img = build_month(s2, s1, y, m)
        name = f'{FILE_PREFIX}_{y}_{m:02d}'
        task = ee.batch.Export.image.toDrive(
            image=img, description=name, folder=args.folder, fileNamePrefix=name,
            region=aoi, scale=EXPORT_SCALE, crs=EXPORT_CRS,
            maxPixels=1e10, fileFormat='GeoTIFF')
        task.start()
        tasks.append(task)
        print(f"  started {name}")

    if args.wait:
        print("\nWaiting for tasks (checking every 60 s)...")
        while True:
            states = [t.status()['state'] for t in tasks]
            done = sum(s in ('COMPLETED', 'FAILED', 'CANCELLED') for s in states)
            print(f"  {done}/{len(tasks)} finished")
            if done == len(tasks):
                break
            time.sleep(60)
        for t in tasks:
            st = t.status()
            if st['state'] != 'COMPLETED':
                print(f"  {st['description']}: {st['state']} {st.get('error_message', '')}")
    else:
        print("\nTasks running in the background: https://code.earthengine.google.com/tasks")


if __name__ == '__main__':
    main()
