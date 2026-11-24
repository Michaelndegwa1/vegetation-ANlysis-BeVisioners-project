# 02 Ingest per site (spec v0.3)

v0.3 changes (2026-11-24, from docs/benchmarks/benchmarks.md; NOT yet built): (a) Sentinel-1 preprocessing, (b) 2/5/10 km rings with protected-area masking, (c) per-year two-observation coverage statistic (VM0009 test), (d) per-mask sanity bounds, (e) production runs via Drive mode, (f) pipeline version in sidecar, (g) three further acceptance tests. Everything in v0.2 below stays unless contradicted here.

v0.2 changes (2026-11-24, from first test run): Hansen asset moved to `2025_v1_13` (2024_v1_12 is deprecated); added a third mask `woody` (WorldCover v200 tree+shrub) because Hansen tree cover is near zero at Kasigau (see 03 Q2); empty cells are written as `band=_none` rows instead of vanishing; values rounded to 6 decimals for reproducible output; local mode runs one getInfo per month (72 reductions at once hit `Too many concurrent aggregations`).

Replaced the single-AOI Week-1 prototype (archived outside the project).

## Goal
For every site in the registry and every month from monitoring_start (S1 from 2015-01), compute summary statistics of S2 indices and S1 backscatter for (a) the site polygon and (b) its leakage ring, and write small tables. No full-resolution rasters.

## Inputs
- `canopyledger/sites/sites.geojson` (spec 01).
- Datasets (all verified to exist): COPERNICUS/S2_SR_HARMONIZED, COPERNICUS/S2_CLOUD_PROBABILITY, COPERNICUS/S1_GRD, UMD/hansen/global_forest_change_2025_v1_13, ESA/WorldCover/v200.
- CLI: `python -m canopyledger.pipeline.ingest [--sites ID ...] [--start YYYY] [--end YYYY] [--run]`. Dry run by default (coverage report only), as in the current script.

## Processing (tested on 2023)
- s2cloudless pixel mask (probability > 40, dilate 100 m) plus SCL shadow (3) and saturated (1). A scene with no cloud-probability match is treated as fully cloudy (affects ~1.4% of Chyulu 2023).
- Indices NDVI, EVI, NDWI (McFeeters, (G-NIR)/(G+NIR)); S1 VV, VH, VH_VV (GRD already in dB; median composite).
- Monthly median composites, server-side. S2_N = clear-observation count per pixel.
- v0.3 Sentinel-1 preprocessing (benchmarks E5; Mullissa 2021, Vollrath 2020): keep a single orbit direction per site-year (the direction with more scenes over the site; recorded in the sidecar), apply a speckle filter (Refined Lee or a documented focal-median substitute, recorded in the sidecar), apply radiometric terrain normalisation with SRTM (slope correction) and mask layover/shadow. Chyulu (hilly) is the priority; the effect is measured by comparing VV monthly standard deviation before/after on one year. If the full method is too heavy in GEE, record the chosen simplification and its cost in the sidecar rather than silently skipping it.
- v0.3 Cloud mask: s2cloudless (prob 40, dilate 100 m) stays until the CloudScore+ comparison in 03a pre-build check 5 reports; the mask choice is a config parameter recorded in the sidecar.
- Tree mask for stats (v1, simple): Hansen treecover2000 >= T and not lost before that month. T is a per-site parameter (default 30; see Q2 in 03). Statistics are reported for `all` pixels, `tree` (Hansen) pixels and `woody` (WorldCover 2021 tree or shrub; static map) pixels separately.

## Statistics
reduceRegion at 30 m by default (config value), tileScale 4. Per site x zone (`site`|`ring_2km`|`ring_5km`|`ring_10km`; v0.2 files used `ring` = the 2 km ring) x month x mask (`all`|`tree`|`woody`): mean, median, p10, p90, stdDev of NDVI, EVI, NDWI, VV, VH, VH_VV; `valid_frac` (pixels with S2_N>=1 over total); `n_pixels`; mean S2_N.
Months with valid_frac < 0.5 are kept and flagged `low_coverage=1`, never dropped or interpolated.
Rings (v0.3): each ring is buffer(site, width) minus site for the widths in `leakage_rings_m`; when `mask_protected_in_ring` is true, WDPA polygons (WCMC/WDPA/current/polygons; existence verified earlier) are removed from the ring and the ring's `n_pixels` reflects that. Rings are cumulative belts around the site, not annuli. Rings are an indicator, not Verra leakage accounting (Chyulu itself uses large activity-shifting areas).
Yearly coverage row (v0.3, VM0009 s6.8.4 double-coverage test): per site, zone, year and mask, one extra row with band=`_coverage`, stat=`frac_n_ge2`, month=0, value = share of pixels with at least two clear observations in the calendar year, plus a boolean in the sidecar for >= 0.90 of the site area.

## Output
`data/processed/stats/<site_id>_<year>.csv` (long format) plus sidecar `<site_id>_<year>.json` (spec version, run date, dataset IDs, parameters, boundary_quality, GEE task id). One export task per site-year (3 sites x 7 years = 21 tasks) via Export.table.toDrive, or getInfo directly for small test runs.
Columns: site_id, zone, year, month, mask, band, stat, value, n_pixels, valid_frac, s2_n_mean, low_coverage, boundary_quality. The sidecar also records `pipeline_version` (semantic version of ingest.py, plus git commit id once the project is under git) and the S1 orbit direction/filters used.
Production runs (v0.3, benchmarks E9): use `--mode drive` (batch export) for all-sites runs; `--mode local` (getInfo) is for tests and small sites only. Log GEE compute use per run; confirm the noncommercial EECU tier before large runs (quota tiers unconfirmed).

## Acceptance tests
1. Dry run lists all sites and per-month S2/S1 scene counts for each polygon (not a point), flagging months with no scenes.
2. 2023 run on Kasigau Phase I (smallest) completes. NDVI and VV fall within sanity bounds (NDVI 0.1-0.8, VV -6 to -18 dB; to be tightened after the first run). Site `all` stats match a manual getInfo spot check for one month within 1%.
3. Ring excludes the site; ring area is buffer area minus site area within 1%.
4. Re-running gives identical files (idempotent, no duplicate rows).
5. Every output row carries boundary_quality.
6. (v0.3) Sentinel-1: sidecar states orbit direction and filters; VV monthly SD on Chyulu does not increase versus the v0.2 composite.
7. (v0.3) Rings: 2/5/10 km cumulative; with protected-area masking on, the ratio of masked to unmasked ring pixels matches the independently computed WDPA-free share within 1%; the yearly `_coverage` row exists for every site-year and mask. (Changed from 'ring area within 1%': absolute pixel counts differ 0.4-1.9% between two counting conventions, see results.)
8. (v0.3) Sanity bounds are per mask: `all` NDVI 0.1-0.8; `tree` and `woody` NDVI up to 0.9; VV -20 to -5 dB for every mask (the v0.2 bounds flagged 34 valid dense-forest values at Chyulu).

## Known risks (unresolved)
- Polygon-level scene coverage not yet measured (verification used point queries).
- Compute: Chyulu ~4,200 km2 x 84 months; time one year first, fall back to 60 m scale or quarterly tasks.
- Protected areas (Tsavo) fall inside the 2 km ring for Kasigau and Chyulu; the ring then measures park, not displacement. Decide in 03d whether to mask WDPA areas out.
- RESOLVED as a finding, not a fix: Hansen >=30% leaves 0 pixels at Kasigau Phase I (tested). See 03 Q2.

## Test results (2026-11-24, kasigau_ph1_rukinga 2023, local mode, ~75-90 s)
1. Dry run: PASS, all three sites, polygon-level scene counts (Chyulu 17-24 S2 scenes/month, Kasigau I 10-14, Kasigau II 15-21).
2. 2023 run: PASS. Site/all NDVI monthly mean 0.17-0.64 (dry season ~0.2, Dec short rains 0.64), VV -10 to -13 dB, valid_frac 0.84-1.00, no low_coverage months. Spot check Jun site/all NDVI mean csv 0.29544 vs independent computation 0.29544 (0.000%).
3. Ring: PASS, ring area 184.9 km2 equals buffer minus site (0.000%).
4. Idempotent: PASS after rounding (raw GEE output differed ~1e-14 between runs); two consecutive runs byte-identical.
5. boundary_quality on every row: PASS.
- Tree (Hansen>=30) mask at Kasigau I: 0 pixels, written as `_none` rows (visible, as designed).
- Not yet tested: Chyulu runtime (running), Drive mode, `--from-csv` conversion, S1-only months before 2019.

## v0.3 build status and test results (2026-11-24)
Built: rings 2/5/10 km (`ring_2km`, `ring_5km`, `ring_10km`) with WDPA masking, yearly `_coverage` row, per-mask sanity bounds, pipeline_version and ring settings in the sidecar, `--mode drive` retained. Code: `canopyledger/pipeline/ingest.py`, `canopyledger/config.py`.
NOT built: Sentinel-1 orbit-direction control, speckle filter, terrain normalisation (the sidecar states `s1_preprocessing: none`). v0.3 items (a) is therefore only partly done.
Tests (Kasigau Phase I 2023, local mode, 420 s, 2,940 rows):
- Offline: `tests/test_ingest_tables.py` 9/9 pass (low-coverage flag, `_none` rows, `_coverage` rows, per-mask sanity, reproducible order, rounding).
- Rings: PASS. Masked/unmasked pixel ratio for the 2 km ring: ingest 195,532/210,213 = 0.930 vs independent WDPA-free share 0.930 (7.0% protected). Protected share grows with ring width: 7.0% (2 km), 10.6% (5 km), 15.8% (10 km).
- Coverage: PASS. Share of pixels with >= 2 clear observations in 2023 is 1.00 for every zone and mask; sidecar `double_coverage_ge90pct_site_all` = true.
- Sanity: no flags with the per-mask bounds.
- OPEN, unexplained: absolute ring pixel counts from the ingest (multi-band composite reduction) are 0.4% to 1.9% higher than a single-band recount at 30 m (2 km ring: 195,532 vs 191,870; 5 km: 501,595 vs 497,726; 10 km: 1,073,044 vs 1,068,993). The same offset existed before masking (old v0.2 count 210,213 vs 206,330). The masked/unmasked ratio agrees, so masking is correct; the cause (grid or partial-pixel handling) is not identified and the area implied by n_pixels x 900 m2 should be treated as accurate to about 2%.
- Runtime: 420 s per Kasigau I site-year in local mode (yearly coverage call alone 244 s; 12 reductions per month). Production runs must use Drive mode (not yet tested end to end).
- Not yet tested: Drive export plus `--from-csv`, S1-only months before 2019.
