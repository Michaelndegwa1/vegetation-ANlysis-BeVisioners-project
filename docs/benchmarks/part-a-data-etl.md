# Part A: Data and ETL benchmarks (research notes)

Research date: 2026-11-24. Method: web search plus page fetches. Several figures come from search-engine snippets of the source and were not verified against the full text; these are flagged "snippet only". Reliability labels: PR = peer-reviewed, AG = agency/official documentation, VB = vendor/blog, TH = thesis/other grey literature.

## 1. Sentinel-2 cloud and shadow masking

| Item | Finding | Source (year, reliability) |
|---|---|---|
| CloudScore+ thresholds | Bands `cs` (instantaneous spectral similarity) and `cs_cdf` (likelihood of clear, from per-location score distribution over time). Values 0.50 to 0.65 "generally work well"; higher removes thin cloud, haze, cirrus shadow. Official example: `cs_cdf >= 0.60`, then median. Page gives no accuracy figures, no dilation advice, no mention of s2cloudless. | GEE catalog, Cloud Score+ S2_HARMONIZED V1. https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_CLOUD_SCORE_PLUS_V1_S2_HARMONIZED (AG-vendor documentation; current) |
| CloudScore+ method paper | Pasquarella, Brown, Czerwinski, Rucklidge, "Comprehensive Quality Assessment of Optical Satellite Imagery Using Weakly Supervised Video Learning", CVPRW 2023, DOI 10.1109/CVPRW59228.2023.00206. Quantitative validation numbers not retrieved. | cited in GEE catalog (2023, PR workshop; numbers not found) |
| CloudScore+ vs s2cloudless vs QA60 | Single land-cover case study (Ecuador), cs threshold 0.4: overall accuracy QA60 composite 71%, s2cloudless 72%, CS+ 73%. Gain over s2cloudless about 1 point. Single application, not a controlled mask benchmark. | "Cloud Score+ in Action: Land Cover Mapping in Ecuador", Google Earth blog. https://medium.com/google-earth/cloud-score-in-action-land-cover-mapping-in-ecuador-fd1c5c424317 (VB; vendor-authored; snippet only) |
| Is CloudScore+ "recommended over s2cloudless"? | Not found as an explicit statement. The catalog page makes no such claim. Evidence is a vendor blog showing a small gain (about 1 point OA) and the catalog's own example workflow. Treat as "Google's current documented option", not as independently validated superior. | see above |
| s2cloudless GEE tutorial parameters | Initial demo: cloud prob threshold 50 (%), NIR dark threshold 0.15 (shadow candidate), shadow search distance 1 km, buffer 50 m. Final composite settings in the same tutorial: prob 40, projection distance 2 km, buffer 100 m, NIR 0.15. These are tutorial values for a temperate (Oregon) scene, not validated for Kenya. | GEE community tutorial "Sentinel-2 Cloud Masking with s2cloudless". https://developers.google.com/earth-engine/tutorials/community/sentinel-2-s2cloudless (AG-vendor tutorial) |
| Intercomparison (CMIX) | Ten algorithms, five reference datasets, Landsat 8 and Sentinel-2. Average overall accuracy across algorithms 80.0 +/- 5.3% to 89.4 +/- 2.4% for Sentinel-2 (depends on reference dataset). Excluding thin/semi-transparent cloud from references raised OA by +1.5 to +7.4 points. Authors suggest favouring non-cloud-conservative masks for frequent revisits, except in very cloudy regions. Per-algorithm Sentinel-2 tables not retrieved. | Skakun et al., Remote Sensing of Environment 274 (2022), doi 10.1016/j.rse.2022.112990 (PR; via abstract/snippets) |
| Fmask / MAJA / Sen2Cor | Baetens et al. 2019 (as cited): Fmask and MAJA about 90% overall for cloud + shadow, Sen2Cor 84%. Zekoll et al. 2021 (disagreement areas only): Fmask about 89%, Sen2Cor about 92%. An ensemble of algorithms beat the best single algorithm by up to 2.7% OA. Dilating Sen2Cor masks lowered its score by about 6 points relative to others and is not recommended by the cited authors (bright surfaces misclassified as cloud). | Secondary citation inside Tarrio et al. and related papers (PR; reported second-hand, snippet only; primary papers not opened) |
| s2cloudless accuracy | Not found as a standalone figure in the sources opened. | not found |
| Sen2Cor SCL thresholds | Cirrus (B10) 0.012 clear to 0.035 thick cloud; cloud probability cutoffs 0.65 (high) and 0.35 (medium). Since PB 04.00 the product dilates clouds +80 m, shadows +40 m, snow +20 m (clouds of 3 px or fewer not dilated). No SCL accuracy percentage given. | SentiWiki "S2 processing". https://sentiwiki.copernicus.eu/web/s2-processing (AG, ESA) |
| QA60 caveat | QA60 cloud polygons stopped being produced on 2022-01-25. Any pipeline spanning 2019-2024 must not rely on QA60 alone. | GEE catalog COPERNICUS/S2_SR_HARMONIZED. https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED (AG-vendor) |

## 2. Sentinel-2 L2A and Sentinel-1 quality

Sentinel-2:
- Mission requirements (not achieved values): absolute geolocation 20 m (2 sigma) without GCPs, 12.5 m with GCPs; multi-temporal registration <= 0.3 pixel (2 sigma); absolute radiometric uncertainty < 5% (goal 3%); inter-band relative radiometric 3%; multi-temporal relative radiometric 1%. Source: SentiWiki "S2 mission", https://sentiwiki.copernicus.eu/web/s2-mission (AG, ESA). Achieved values: not found (the monthly DQRs exist at sentinel.esa.int but that host was unreachable from this environment).
- Global Reference Image absolute geolocation "better than 6 m"; geometric refinement against the GRI applied worldwide since 2021-08-23 (so 2019 to mid-2021 scenes may be unrefined; pre-refinement pointing up to about 2 km). Source: SentiWiki "S2 processing" (AG, ESA).
- A 2016 L1C DQR projects absolute accuracy to 8.5 m (2 sigma) after refinement; this is a projection, not a measurement (snippet only).
- Processing baseline 04.00 (2022-01-25): L2A digital numbers shifted by BOA_ADD_OFFSET (typically -1000); reflectance = (DN + BOA_ADD_OFFSET) / 10000. Offset is tied to the processing baseline of the product, not acquisition date. GEE `COPERNICUS/S2_SR_HARMONIZED` shifts newer scenes back to the older range, so no manual offset is required if the HARMONIZED collection is used. Sources: ESA STEP forum post on PB04.00 offset (AG-community, https://forum.step.esa.int/t/info-introduction-of-additional-radiometric-offset-in-pb04-00-products/35431); SentiWiki; GEE catalog. Good practice: assert in tests that median band values of pre- and post-2022-01-25 composites over a stable target agree.
- Terrain/BRDF: Sen2Cor uses the 30 m Copernicus DEM, can apply topographic correction, treats surfaces as Lambertian with a constant viewing angle per tile; no surface BRDF correction found in the part of the page read. Implication: residual illumination effects on the Chyulu slopes are expected; no quantified error found. Source: SentiWiki "S2 processing" (AG; last 4,400 characters unread).

Sentinel-1:
- GEE `S1_GRD` already has orbit file, thermal noise removal, radiometric calibration and terrain correction to sigma0 in dB; speckle filtering and radiometric terrain normalization are the user's responsibility; SLC not ingested. Source: GEE Sentinel-1 Algorithms. https://developers.google.com/earth-engine/sentinel1 (AG-vendor).
- Mullissa et al., "Sentinel-1 SAR Backscatter Analysis Ready Data Preparation in Google Earth Engine", Remote Sensing 13(10):1954, 2021 (PR): adds border-noise removal, speckle filtering (Refined Lee used; boxcar, Lee, Gamma MAP, improved Lee sigma also offered) and radiometric terrain normalization; terrain normalization described as recommended for most forest applications.
- Vollrath et al., "Angular-Based Radiometric Slope Correction for Sentinel-1 on Google Earth Engine", Remote Sensing 2020 (PR): volume-scattering model suited to vegetation; layover/shadow invalid-data mask is a CEOS ARD requirement.
- Quantified accuracy gain from terrain normalization over Kenyan or dryland terrain: not found. Tropical forest shows flatter angular behaviour (0.06 dB/degree) in one study (snippet only).

## 3. Compositing practices

- Minimum clear observations per period: not found as a published threshold. No source retrieved states a required N for monthly composites.
- Coverage evidence: a monthly Dynamic World composite had 68.78% spatial coverage versus 98.52% for growing-season and 98.57% for full-year windows (China study; snippet only; land-cover not NDVI). Implication: monthly composites in cloudy months will have holes; completeness must be reported per month.
- Gap-filling errors: dryland NDVI reconstruction RMSE 0.02 for best method versus 0.073 for strongest competitor (SLU study, snippet only, setup unconfirmed). Surface-reflectance reconstruction RMSE 0.01 to 0.03 (Remote Sensing 2023, MDPI 15(9):2303, snippet only). Kenya drought-forecast study (MODIS/Landsat, not Sentinel-2) shows RMSE rising from about 0.025-0.029 at 2-week gaps to about 0.045-0.053 at 6-week gaps (arXiv 1911.10339; PR-preprint; snippet only).
- Median vs medoid vs percentile: Flood (2013, Remote Sensing 5:6481, PR) proposed the medoid; max-NDVI composites bias toward greener scenes. A 2023 Int. J. Digital Earth monthly Landsat study ranked classification accuracy: weighted scoring > median > max-NDVI > medoid, and noted median is computationally cheapest (snippet only). No Sentinel-2 index-bias comparison found.
- Phenology temporal resolution: Sentinel-2 EVI start-of-season RMSE 3.0 days best case versus 9.2 days MODIS in homogeneous landscapes (2020, Remote Sensing; not dryland-specific; snippet only). Dryland-specific recommended temporal resolution: not found. Sentinel-2 nominal revisit 5 days (GEE catalog).

## 4. S1 + S2 fusion

- Zhang et al. 2019, Remote Sensing of Environment (Sahel woody canopies, PR): S2 alone 91% OA, S1 alone 89%, combined significantly better (p < 0.05); about 93% combined appears in another listing, implying roughly +2 points (my inference from two snippets; unverified).
- Fundisi et al. 2022, European Journal of Remote Sensing (South African savanna, 27 species, PR): fused 76%, S2 alone 72%, S1 alone 71% (+4 points; species task, less comparable).
- Heckel et al. 2020, Remote Sensing 12(2):302 (forest cover, Germany and South African savanna, PR): fused OA 90.9% (South Africa) and 93.2% (Thuringia) with spatial CV; S1 alone 87.5%, S2 alone 91.9%; S1 time series helped in open savanna. Implied fusion gain over S2 is small or negative for South Africa from the numbers quoted (snippet only); the paper's own comparison should be read before claiming a gain.
- UCLouvain master's thesis (tropical moist forest): fusion +1 to +2 points over single sensor, S2 87-91%, S1 75-80% (TH, low reliability).
- Southern African dryland AGB (2022, PR, snippet only): S1+S2 random forest R2 0.95, RMSE 0.25 Mg/ha (value looks implausibly small; unit or scaling unverified); NDVI saturates above 80 Mg/ha, SAR and red-edge reduce saturation. Counter-example: a 2023 Limpopo rangeland biomass study dropped S1 variables because of moisture effects (Environ. Monit. Assess., snippet only).
- Summary: documented gains are modest, roughly 0 to 4 points OA; a larger benefit is argued mainly for data gaps and biomass saturation. No clean cloudy-tropics before/after figure found.

## 5. Reproducible geospatial ETL

- GEE best practices (AG-vendor, https://developers.google.com/earth-engine/guides/best_practices): filter and select before map; avoid `toList`, `reproject`, `ee.Algorithms.If` in map, and unnecessary `clip`; use `updateMask` not `mask`; combine reducers with `sharedInputs`; printing fails above 5,000 elements; use `bestEffort: true` or set `maxPixels` if scale matters; export when computations time out; embed an identifier in asset names for reproducibility; export intermediates.
- reduceRegion guidance (https://developers.google.com/earth-engine/guides/reducers_reduce_region): always specify `scale` (or CRS and transform); too-many-pixels fixes are raise `maxPixels`, raise `scale`, or `bestEffort`; `tileScale` range 0.1 to 16, values such as 2 or 4 use smaller tiles for memory-limited jobs; `getInfo()` blocks synchronously, long jobs belong in batch exports (AG-vendor).
- Quotas: since 2026-04-27 noncommercial projects get monthly compute allowances (Community 150 EECU-hours, Contributor 1,000 EECU-hours) and drop to restricted mode when exhausted. Older default limits cited: 40 concurrent requests, 100 requests/s per project, average 2 concurrent batch tasks, 3,000 pending tasks per project, 10-day batch task lifetime, 250 GB storage / 10,000 assets (sources conflict on whether batch concurrency depends on tier; page dates unconfirmed). Source: https://developers.google.com/earth-engine/guides/usage and .../noncommercial_tiers (AG-vendor; snippets only).
- STAC and FAIR: STAC follows semantic versioning (1.1.0 current stable per an OGC document); STAC validation schemas and tools exist in the spec repo; FAIR R1.2 requires detailed provenance; W3C PROV-O suggested for recording entities, activities, agents (arXiv 2110.07117; OGC STAC building blocks; EGU26-9158). PR/AG mixed, snippet only.
- Not found with a citable source: idempotency patterns, unit/regression-test conventions for geospatial ETL, concrete range and completeness check thresholds. Standard engineering practice (content-hashed output paths, config-hash in output metadata, golden-file regression tests, physical range checks such as reflectance in [0,1] and NDVI in [-1,1]) is from memory, unverified.

## 6. Operational targets of comparable systems

- GLAD-S2: in Peru 2019, flagged new changes on average 11 days earlier than GLAD-L, 33 days earlier in the wet season; 5-day update cadence for the Amazon basin listed in a GFW table (GFW blog, https://www.globalforestwatch.org/blog/data-and-tools/glad-s2-offers-high-resolution-deforestation-alerts; VB-NGO; snippet only).
- Integrated deforestation alerts: updated daily at 10 m per the GFW data API (https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts; AG-NGO; snippet only). Another listing says "unknown", so low confidence.
- DIST-ALERT: 30 m, updated weekly on GFW; underlying HLS data refresh every 2 to 4 days in cloud-free conditions; low-confidence alert 2 to 3 anomalous observations, high 4 or more (Global Nature Watch / GFW blog, fetched; VB-NGO).
- RADD latency, NICFI and SERVIR latency: not found.
- Completeness targets of comparable systems: not found.

## Recommended targets for CanopyLedger ETL

| Metric | Target value | Source | Confidence |
|---|---|---|---|
| Cloud mask threshold (starting value, to be calibrated on Kenya sites) | CloudScore+ `cs_cdf >= 0.60`, tested over range 0.50 to 0.65 | GEE catalog CS+ | Medium (vendor guidance; no Kenya validation) |
| Fallback/independent mask check | s2cloudless prob 40, shadow distance 2 km, buffer 100 m, NIR dark 0.15 (tutorial composite settings) | GEE s2cloudless tutorial | Low-medium (temperate demo values) |
| Do not use QA60 as sole mask for 2019-2024 | Required | GEE S2_SR_HARMONIZED catalog | High |
| Sentinel-2 collection | `COPERNICUS/S2_SR_HARMONIZED` (offset handled); regression test comparing pre/post 2022-01-25 stable-target medians | GEE catalog; ESA forum | High (collection); test design is my own |
| Reflectance scaling | divide by 10000 after offset handling | ESA forum, SentiWiki | High |
| Sentinel-2 co-registration to expect | requirement <= 0.3 px (2 sigma); flag 2019 to mid-2021 as possibly unrefined (refinement started 2021-08-23) | SentiWiki | Medium (requirement, not measured) |
| S1 preprocessing | GEE GRD plus speckle filter (Refined Lee) plus radiometric terrain normalization plus layover/shadow mask; keep one orbit direction/track per composite | Mullissa 2021; Vollrath 2020; GEE docs | Medium-high (method); orbit rule is from memory, unverified |
| Expected S1+S2 fusion gain (set as an expectation, not a pass criterion) | about 0 to 4 points overall accuracy over optical only | Zhang 2019; Fundisi 2022; Heckel 2020 | Low-medium |
| Cloud-mask accuracy sanity band | about 80 to 90% OA depending on reference definition | Skakun 2022 | Medium |
| Compositing statistic | median (cheapest, competitive accuracy) | Int. J. Digital Earth 2023 (Landsat); Flood 2013 | Low-medium |
| Per-month completeness reporting | report valid-pixel fraction per site-month; expect monthly composites to be materially less complete than seasonal ones (68.8% vs 98.5% in one study) | Dynamic World China study | Low (different region and product) |
| GEE reduceRegion | explicit `scale` (native 10 m or 20 m), `maxPixels` set, `tileScale` 2 to 4 on memory errors, avoid `bestEffort` for reported statistics, batch export for tables | GEE docs | High |
| GEE getInfo | not for heavy jobs; use batch exports | GEE docs | High |
| Quota budget | design for noncommercial monthly EECU allowance (150 or 1,000 EECU-hours); about 2 average concurrent batch tasks | GEE usage pages | Medium (dates unconfirmed) |
| Provenance | STAC-style item/collection metadata, semantic versioning of dataset and pipeline | STAC/OGC; FAIR | Medium |
| Update cadence benchmark (monthly product) | monthly cadence is slower than comparable alert systems (daily to weekly, GLAD-S2 5-day); acceptable for carbon-ledger statistics, not for alerts | GFW sources | Low-medium |

## Items I could not verify

- Quantitative CloudScore+ validation numbers, and any explicit Google recommendation of CloudScore+ over s2cloudless.
- s2cloudless standalone accuracy; per-algorithm CMIX Sentinel-2 tables; primary Baetens 2019 and Zekoll 2021 numbers.
- Achieved (measured) Sentinel-2 geolocation, multi-temporal registration and radiometric figures from the monthly DQRs.
- Sentinel-2 BRDF/terrain residual error on steep slopes; quantified Sentinel-1 terrain-normalization gain in Kenya or dry tropics.
- Minimum clear observations per composite; dryland-specific recommended temporal resolution; Sentinel-2 median vs medoid bias.
- Clean S1+S2 vs optical-only gains for woody cover in cloudy tropics or Kenya; the 0.25 Mg/ha RMSE biomass figure looks suspect.
- RADD, NICFI, SERVIR latency and completeness targets; GLAD-S2 and integrated-alert update frequencies conflict between sources.
- Citable standards for idempotency, pipeline regression tests, and range/completeness thresholds.
- Exact current GEE batch concurrency per noncommercial tier.
