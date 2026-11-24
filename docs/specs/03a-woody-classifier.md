# 03a Woody-vegetation classifier (spec v0.3, 2026-11-24)

v0.3 changes (from docs/benchmarks/benchmarks.md; NOT yet built): GEDI and Hansen removed as dryland baseline options (Landsat-based baseline instead); added CloudScore+ comparison; sensitivity set 10/15/20/30%; report producer's and user's accuracy, multi-class OA and 90% CI on areas with a >10% low-precision flag; 0.5 ha minimum mapping unit; explicit definition note. Open decisions D1-D3 (reliability rule, sample size, extra training labels) are still with the user; the v0.2 rules stand until answered.

v0.2 DECISIONS (user, 2026-11-24): (1) woody = canopy >= 20% of a 30 m plot, sensitivity at 10%/30% reported; (2) 100 validation points per site, 300 total; (3) reliability flag thresholds OA < 0.75 or woody F1 < 0.70 on independent points; (4) high-resolution imagery: the user accepted the proposals, but availability of dated Google Earth imagery near Y_ref=2023 at the sample areas is NOT yet confirmed (it is a check at labelling time, with a per-site fallback year).

Decision it implements (user, 2026-11-24): the monitored class is WOODY VEGETATION (tree + shrub), not Hansen "forest". Depends on 00, 01, 02 (ingest). Feeds 03b-03d.

## Goal
For each site and each year 2019-2024, a 10 m binary map woody / non-woody, summarised as woody hectares and woody fraction for the site polygon and its leakage ring, with accuracy measured on independent, human-labelled reference points. Output is an estimate with stated uncertainty, not ground truth.

## Verified inputs (docs/verification-gee.md, checked 2026-11-24)
- Sentinel-2 L2A harmonized + s2cloudless, Sentinel-1 GRD: usable from 2019 (ingest code reused, tested).
- ESA WorldCover v200 (2021, 30 m): tree 10, shrub 20. Class shares: Kasigau I shrub 72.5% / tree 0.6%; Kasigau II shrub 92.1% / tree 0.2%; Chyulu tree 18.5% / shrub 23.7%.
- Landsat Collection 2 Level 2 (exist, scenes at Kasigau I): LT05 1984-2011, LE07 1999-2024 (SLC-off stripes after 2003), LC08 2013-, LC09 2021-. Scenes per year at the site: 2000: 32, 2005: 37, 2009: 57, 2010: 40, 2013: 98, 2016: 123, 2018: 118. Gap: 2012 has only Landsat 7.
- GEDI L2A and L4A monthly: 2019-04 to 2025-07. Quality-filtered (l4_quality_flag=1, degrade_flag=0) L4A cell count 2019-2024: Kasigau I ~9,300, Kasigau II ~68,000, Chyulu ~85,000. Enough for height/biomass reference per site (not per pixel). CAVEAT (benchmarks, Part B): GEDI RH98 in African savanna has bias -0.55 m, RMSE 1.64 m and cannot resolve shrubs below about 2.3 m, so it is NOT a viable baseline at Kasigau (shrub-dominated); at Chyulu it can support tree-height context only.
- Not verified: dated high-resolution imagery at the sample points (see Pre-build checks).

## Class definition (DECIDED: 20% default)
- woody = tree or shrub canopy covering >= 20% of a 30 m x 30 m plot (woody plants, any height >= ~1 m). non-woody = grass, crop, bare, built, water, and woody cover < 20%.
- Labellers also record the detailed type (tree / shrub / grass / crop / bare / water / built / unsure) so 03c can use per-type thresholds. "Unsure" points are excluded and counted.
- The 20% threshold is a decision, not a fact. Report sensitivity of accuracy and area at 10%, 15% (Kenya's legal canopy threshold) and 30%.
- Definition note: Kenya's national forest definition is >= 15% canopy, >= 0.5 ha, >= 2 m height (FAO: 10%, 0.5 ha, 5 m). CanopyLedger's class is "woody vegetation" with no height rule and is NOT the legal forest definition; every output and report says so.
- Minimum mapping unit 0.5 ha (about 6 cells at 30 m, about 50 cells at 10 m): areas and events smaller than this are reported as sub-MMU, not as map units.

## Features (per site-year, calendar year composites, 10 m, all server-side)
- S2: percentiles p20, p50, p80 of NDVI, plus median EVI, NDWI, NBR (B8,B12), NDMI (B8,B11), red-edge (B5, B6, B7) and SWIR (B11, B12) bands. Percentiles instead of named seasons because Kenya has two rainy seasons.
- S2 clear-observation count (S2_N) as a quality band; pixels with S2_N=0 for the year are output as `no_data`, not guessed.
- S1: median VV, VH, VH_VV; VH temporal standard deviation.
- Terrain: SRTM elevation and slope (static).
- NOT used as predictors: WorldCover, Hansen, Dynamic World (stale or modelled maps would leak their errors into the result and the validation).

## Training labels (no human labelling needed for training)
- Pseudo-labels from WorldCover 2021: woody = classes 10, 20; non-woody = 30, 40, 50, 60, 80. Keep only pixels whose 3x3 30 m neighbourhood is the same class (edge removal), sample randomly and stratified per site and class, e.g. 2,000 points per class per site (to be tuned). Features taken from the 2021 composite.
- Rationale: WorldCover is noisy but independent of the later validation. Model and WorldCover errors may be correlated in dryland (grass vs shrub), which is why validation uses human labels only.
- Model: ee.Classifier.smileRandomForest (e.g. 300 trees, to be tuned by spatial cross-validation), one model per site initially (Kasigau and Chyulu differ in vegetation), plus a pooled model compared in the same cross-validation.
- Spatial cross-validation: split by 5 km blocks; report out-of-block accuracy against the pseudo-labels (training diagnostics only, never the headline accuracy).

## Validation (the headline accuracy)
- Reference sample stratified by MAP class (woody, non-woody) within each site, drawn AFTER the map exists, using a fixed random seed. Proposed n = 100 per site (about 50 per map class, minimum 40), total 300. If labelling capacity is lower, use 60 per site and report the wider interval.
- Reference year Y_ref (default 2023, chosen so training year 2021 and validation year differ, testing temporal transfer). The labeller must use imagery dated within +/- 6 months of Y_ref; the imagery date and source go in the label file.
- Tooling: script exports points to CSV and KML (open in Google Earth Pro, historical imagery) with empty columns `label_type`, `woody_cover_pct_class`, `imagery_date`, `confidence`; a second script reads the filled CSV. Labellers do not see the map class (blind labelling).
- Estimates: confusion matrix per site, overall accuracy, woody user's AND producer's accuracy (both always reported), F1, each with 95% Wilson interval (n=100 gives roughly +/-7 points on OA: 0.85 -> 0.77-0.91), and error-adjusted woody area using the stratified estimator (map-class strata weighted by mapped area; Olofsson et al. 2014 approach). Area estimates carry a two-sided 90% confidence interval (VM0048/ART convention) and are marked low-precision when the interval half-width exceeds 10% of the estimate (Verra VMD0055 rule used as our flag). Also report the multi-class (tree/shrub/grass/other) OA from the detailed labels, with reference value WorldCover 76.7% global OA.
- Reference targets (peer benchmarks, not market requirements; no fixed market threshold was found): binary OA >= 0.85 (Borges 2020 reached 86.3% for S1+S2 in savanna), woody producer's accuracy >= 0.71 (Sahel baseline), per-stratum sample >= 50 (Olofsson 2014 via a secondary source).
- Reliability flag per site (proposal): if overall accuracy < 0.75 or woody F1 < 0.70 on independent points, the site's woody outputs are labelled "low reliability" everywhere they are shown. Thresholds are a proposal for the user to confirm.
- Validation labels are locked once used: no tuning of the model on them. A re-label round needs new points.

## Outputs
- `data/processed/woody/<site_id>_<year>.csv`: site_id, zone (site|ring), year, woody_ha, nonwoody_ha, no_data_ha, woody_frac, reliability, boundary_quality, model_id.
- Annual maps stay in GEE (asset if the user's asset root is writable, otherwise Drive GeoTIFF uint8, ~42 MB/yr for Chyulu); no rasters in the repo.
- `docs/validation/<site_id>_woody_validation.md`: confusion matrix, intervals, sample size, imagery sources and dates, number of "unsure".
- Sidecar JSON per table: spec version, run date, dataset IDs, model parameters, training sample sizes, seed.

## What this stage does not do
- It does not detect change. Differencing two annual maps mixes classification noise with real change. Change dates and magnitudes come from 03b (CCDC) and are checked against these maps.
- It does not separate natural from human-caused loss, and it does not estimate carbon.
- It does not establish a pre-2019 baseline. The baseline for dryland sites is Landsat-based (separate spec 03g, to be written): Landsat Collection 2 L2 exists back to 1984 (verified; 2012 only Landsat 7 with SLC-off gaps). Hansen (about 48% loss omission in sub-Saharan Africa, 2001-2014 version, via summary) and GEDI (above) are not used to baseline Kasigau.

## Build sessions
1. Label tool: stratified point sampling, CSV/KML export, import and validation of the filled file (needs a map, therefore a first-pass model; session 2 first if sampling by map class).
2. Features and pseudo-label training, spatial CV, per-site vs pooled comparison. Check smileRandomForest memory/time on Chyulu.
3. Apply to 2019-2024, write tables, thumbnails.
4. Draw the validation sample, user labels, compute and publish accuracy.

## Pre-build checks (verify, do not assume)
1. DONE: class definition (20%), 100 points/site, reliability thresholds. OPEN: confirm Google Earth Pro historical imagery dated near Y_ref at the sample areas; if unavailable for a site, choose another Y_ref for that site.
2. Asset-root write access in project premium-episode-423509-g8 (test one tiny asset).
3. smileRandomForest on Chyulu (~4,200 km2) classification at 10 m for one year: runtime and memory.
4. Confirm S2 SWIR/red-edge bands (B5-B7, B11, B12) in S2_SR_HARMONIZED mask correctly with the existing cloud mask (reflectance scale 0.0001).
5. CloudScore+ comparison (benchmarks E2): build annual composites with s2cloudless (prob 40, dilate 100 m) and with CloudScore+ (`cs_cdf` >= 0.50, 0.60, 0.65) at both sites; compare clear-pixel fraction and, once labels exist, OA on the validation points. The only head-to-head evidence found is a Google blog case (73% vs 72%), so this is an experiment, not a switch. Also record mask accuracy against reference points (about 80-90% OA is the published range).
6. Co-registration check (benchmarks E4/R6): ESA geometric refinement began 2021-08-23; compare a stable target (e.g. a rock outcrop or road crossing) in 2019-2021 vs 2022+ composites; flag if the offset exceeds 0.4 px.

## Known risks
- Grass vs shrub confusion in dry season and after rain flushes; mitigated with percentile features, not eliminated.
- WorldCover pseudo-label noise at Kasigau (shrub-dominated, weak class contrast) may cap training quality; fallback is to train on the human labels via cross-validated folds (then a separate fresh sample is needed for the headline accuracy).
- The Kasigau ring includes Tsavo National Park (woody vegetation inside the park is not displacement).
- Fire scars and burned grass resemble non-woody change in S2 and SWIR features.
- 20% threshold sensitivity: area estimates can change substantially between 10% and 30%.
