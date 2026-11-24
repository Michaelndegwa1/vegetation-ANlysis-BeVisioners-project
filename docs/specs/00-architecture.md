# 00 Architecture (spec v0.1, 2026-11-24)

## Purpose
Independent, satellite-based check of whether funded forest carbon/restoration projects in Kenya keep their canopy. Output per site: canopy status over time, loss events with dates, leakage-ring comparison, alerts.

## Scope
- DECISION (user, 2026-11-24): the monitored class is woody vegetation (tree + shrub), because Kasigau is dryland thicket where Hansen tree cover is ~0. 'Forest' in the application text should read 'woody vegetation / canopy' where it applies to these sites.
- IN: forest-type projects (REDD+, ARR, IFM) as polygons in the site registry. Start: Chyulu Hills (Verra 1408), Kasigau Phase I and II.
- OUT: soil/grassland carbon (e.g. Northern Kenya Rangelands), certification, additionality, survival of individual seedlings (not visible at 10 m), flood/famine prediction (the risk layer is an indicator only).

## Verified constraints that shape the design (source: docs/verification-gee.md)
1. Sentinel-2 L2A is usable only from 2019 at both sites (2017-18 has 3-20 scenes/yr). Funding started 2010/2013, so there is NO S2 pre-funding baseline.
2. Baseline = Hansen GFC (treecover2000, loss, lossyear to 2024). Sentinel-1 exists from 2014-10 (use from 2015). Landsat is a candidate baseline source (IDs not yet verified).
3. Sites are large (Chyulu ~4,200 km2). Full 10 m rasters are ~1.6 GB/month for Chyulu, so the pipeline exports per-site statistics tables, not rasters (rasters only on demand for small areas).
4. Boundaries are traced (+/-2-4 km), labelled approximate. Every output carries the boundary_quality label.

## Data flow
```
sites/sites.geojson --> pipeline/ingest (GEE, per site x month) --> data/processed/stats/*.csv
                                  |                                         |
                      Hansen/WorldCover/DW/CHIRPS/SRTM            classifier -> change detection -> alerts
                                                                             |
                                                  scorecard (site vs leakage ring) --> outputs/ + dashboard
```
Stages communicate only through files (site GeoJSON in, CSV tables out). Each stage runs alone and is idempotent.

## Folder map
`canopyledger/pipeline/` one module per stage; `canopyledger/sites/` registry; `canopyledger/dashboard/` Streamlit; `data/raw|processed` gitignored; `outputs/` reports; `docs/specs/` these specs. No absolute paths; resolve from the repo root.

## Cross-cutting rules
- Every number in a table or UI states its source and whether it is verified, approximate or modelled.
- Registry facts the user has not confirmed stay null, never guessed.
- Classifier accuracy is measured on points NOT used for training and NOT derived from the same labels (03 open question Q1).
- Config (GEE project id, thresholds, scales) lives in one config module.
- Each exported table has a sidecar JSON (spec version, run date, dataset IDs, parameters).

## Build order (one session each; each ends with a progress.md update)
01 schema migration -> 02 ingest per site -> 03a forest mask/classifier -> 03b change detection -> 03c adaptive alerts -> 03d scorecard + leakage -> 03e risk layer -> 03f dashboard. See 03-later-specs.md.
