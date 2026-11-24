# GEE verification (run 2026-11-24, scratch/verify_gee.py, point queries at Chyulu 37.9E,-2.75 and Kasigau 38.65E,-3.8)

| Item | Result |
|---|---|
| COPERNICUS/S1_GRD | Exists; Kasigau 456 scenes, 2014-10-21 to 2026-11-21 |
| UCSB-CHG/CHIRPS/DAILY | Exists; 1981-01-01 to 2026-09-30 (latest data lags ~2 months) |
| GOOGLE/DYNAMICWORLD/V1 | Exists; Kasigau from 2015-10-04 to 2026-11-20 |
| ESA/WorldCover v100 (2020) and v200 (2021) | Both exist, 1 image each (static maps) |
| UMD/hansen/global_forest_change_2024_v1_12 | Exists but DEPRECATED (found when running ingest). Use `UMD/hansen/global_forest_change_2025_v1_13` (same bands; lossyear max 25 = 2025). Correction to the first pass, which did not check for newer versions. |
| USGS/SRTMGL1_003 | Exists; band elevation |
| LARSE/GEDI/GEDI04_A_002_MONTHLY | Exists; 67,000 images; bands agbd, agbd_se, degrade_flag... |
| ee.Algorithms.TemporalSegmentation.Ccdc | Exists |
| COPERNICUS/S2_SR_HARMONIZED scenes per year at point | Chyulu: 2016=10, 2017=10, 2018=20, 2019=144, 2020-24=144-190. Kasigau: 2017=3, 2018=11, 2019=70, 2020-24=72-74 |
| s2cloudless join by system:index | Chyulu 2017-2023: 100% except 2023 (142/144). Kasigau 100% all tested years |

## Consequences
- Usable Sentinel-2 L2A time series starts 2019 for both sites (2018 is sparse). Projects funded 2010/2013 have NO S2 pre-funding baseline. Pre-2019 baseline must come from Hansen GFC (tree cover 2000, loss by year) and/or Landsat; S1 reaches back to 2014-10 (from 2015 reliably).
- The code already handles a missed cloud-prob match (treated as cloudy), which affects ~1.4% of 2023 Chyulu scenes.
- Counts are for a single point, not the whole polygon; polygon coverage (tiles/orbits) not yet checked.
- Not yet verified: Landsat IDs, GEE quota/time for site-level stats over ~4,100 km2, s2cloudless threshold accuracy.

## Added 2026-11-24 for spec 03a
- Landsat C2 L2 exist: LT05 1984-2011, LE07 1999-2024, LC08 2013-, LC09 2021-. Scenes/yr at Kasigau I: 2000:32, 2005:37, 2009:57, 2010:40, 2013:98, 2016:123, 2018:118. 2012 only Landsat 7 (SLC-off).
- GEDI L2A and L4A monthly: 2019-04-01 to 2025-07-01. Quality-filtered L4A cells 2019-2024 (25 m cells, area-weighted count): Chyulu ~85k, Kasigau I ~9.3k, Kasigau II ~68k.
- Hansen: use 2025_v1_13 (2024_v1_12 deprecated).
