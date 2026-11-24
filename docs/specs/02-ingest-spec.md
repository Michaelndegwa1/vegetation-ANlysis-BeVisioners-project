# 02 Ingest per site (spec v0.1)

Replaces `canopyledger/pipeline/kenya_ingest.py` (single placeholder Mau AOI).

## Goal
For every site in the registry and every month from monitoring_start (S1 from 2015-01), compute summary statistics of S2 indices and S1 backscatter for (a) the site polygon and (b) its leakage ring, and write small tables. No full-resolution rasters.

## Inputs
- `canopyledger/sites/sites.geojson` (spec 01).
- Datasets (all verified to exist): COPERNICUS/S2_SR_HARMONIZED, COPERNICUS/S2_CLOUD_PROBABILITY, COPERNICUS/S1_GRD, UMD/hansen/global_forest_change_2024_v1_12.
- CLI: `python -m canopyledger.pipeline.ingest [--sites ID ...] [--start YYYY] [--end YYYY] [--run]`. Dry run by default (coverage report only), as in the current script.

## Processing (reuse from kenya_ingest.py, tested on 2023)
- s2cloudless pixel mask (probability > 40, dilate 100 m) plus SCL shadow (3) and saturated (1). A scene with no cloud-probability match is treated as fully cloudy (affects ~1.4% of Chyulu 2023).
- Indices NDVI, EVI, NDWI (McFeeters, (G-NIR)/(G+NIR)); S1 VV, VH, VH_VV (GRD already in dB; median composite).
- Monthly median composites, server-side. S2_N = clear-observation count per pixel.
- Tree mask for stats (v1, simple): Hansen treecover2000 >= T and not lost before that month. T is a per-site parameter (default 30; see Q2 in 03). Statistics are reported for ALL pixels and for tree-mask pixels separately.

## Statistics
reduceRegion at 30 m by default (config value), tileScale 4. Per site x zone (`site`|`ring`) x month x mask (`all`|`tree`): mean, median, p10, p90, stdDev of NDVI, EVI, NDWI, VV, VH, VH_VV; `valid_frac` (pixels with S2_N>=1 over total); `n_pixels`; mean S2_N.
Months with valid_frac < 0.5 are kept and flagged `low_coverage=1`, never dropped or interpolated.

## Output
`data/processed/stats/<site_id>_<year>.csv` (long format) plus sidecar `<site_id>_<year>.json` (spec version, run date, dataset IDs, parameters, boundary_quality, GEE task id). One export task per site-year (3 sites x 7 years = 21 tasks) via Export.table.toDrive, or getInfo directly for small test runs.
Columns: site_id, zone, year, month, mask, band, stat, value, n_pixels, valid_frac, s2_n_mean, low_coverage, boundary_quality.

## Acceptance tests
1. Dry run lists all sites and per-month S2/S1 scene counts for each polygon (not a point), flagging months with no scenes.
2. 2023 run on Kasigau Phase I (smallest) completes. NDVI and VV fall within sanity bounds (NDVI 0.1-0.8, VV -6 to -18 dB; to be tightened after the first run). Site `all` stats match a manual getInfo spot check for one month within 1%.
3. Ring excludes the site; ring area is buffer area minus site area within 1%.
4. Re-running gives identical files (idempotent, no duplicate rows).
5. Every output row carries boundary_quality.

## Known risks (unresolved)
- Polygon-level scene coverage not yet measured (verification used point queries).
- Compute: Chyulu ~4,200 km2 x 84 months; time one year first, fall back to 60 m scale or quarterly tasks.
- Protected areas (Tsavo) fall inside the 2 km ring for Kasigau and Chyulu; the ring then measures park, not displacement. Decide in 03d whether to mask WDPA areas out.
- Dryland tree cover is low; a Hansen >=30% threshold may mask most of Kasigau (Q2).
