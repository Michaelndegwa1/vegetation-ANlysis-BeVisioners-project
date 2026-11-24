# 03 Outlines for later specs (not yet buildable; each needs a verification step first)

| Id | Stage | Intent | Must be verified/decided first |
|---|---|---|---|
| 03a | Forest mask / classifier | Per-year forest vs non-forest from S1+S2 (random forest in GEE) | Q1, Q2 |
| 03b | Change detection | CCDC on NDVI (and VV) from 2019: break date and magnitude | CCDC runtime on large polygons; S2 from 2019 gives only ~5-6 years for the harmonic fit |
| 03c | Adaptive alerts | Per-class thresholds from each class's own history (replaces fixed NDVI 0.3) | needs 03a classes; CHIRPS rainfall to separate drought from clearing |
| 03d | Scorecard + leakage | Baseline vs current canopy (ha), loss events with dates, ring comparison | Hansen baseline definition; WDPA masking of the ring |
| 03e | Risk layer | Indicator of loss plus negative rainfall anomaly on steep slopes | SRTM slope, CHIRPS anomaly; indicator, not forecast |
| 03f | Dashboard | Portfolio map, site report, risk view, PDF export | design reuse from the legacy dashboard (docs/uk-notes-dashboard.md) |

## Open questions
- Q1 Validation independence: Hansen labels cannot both train and validate (circular). Needs independent reference points, e.g. visual interpretation of high-resolution imagery by the user on a stratified sample per site (n to be set). Decide before 03a.
- Q2 Forest definition in dryland sites: Kasigau and Chyulu are dry woodland, bushland and savanna. Choose canopy thresholds per site (tree cover 10/20/30%) and state the definition in outputs. Check the Hansen treecover2000 distribution inside each polygon before fixing T.
- Q3 Pre-2019 baseline: Hansen only, or add Landsat? Verify Landsat collection IDs and cloud handling.
- Q4 GEDI L4A biomass (optional): the collection exists (67,000 monthly images); sampling is sparse, so treat it as a site-level indication only.
- Q5 Needed from the user: confirmed Verra IDs, Kasigau start dates, official boundary files.
