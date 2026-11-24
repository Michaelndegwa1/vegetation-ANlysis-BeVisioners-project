# CanopyLedger Kenya

Independent satellite monitoring (Sentinel-1/2 via Google Earth Engine + ML) showing whether funded
forest carbon/restoration projects in Kenya are growing and staying. Portfolio of sites, not one pilot.
Forest-type projects only (REDD+, ARR, IFM). Soil/grassland projects are unsupported.

## Layout
- `canopyledger/pipeline/`  GEE ingestion, classifier, change detection, scorecard (one module per spec section)
- `canopyledger/sites/`     site registry GeoJSON (`sites.geojson` (spec 01; validate with `PYTHONPATH=. python -m canopyledger.sites.validate`), boundaries APPROXIMATE until official Verra files)
- `canopyledger/dashboard/` Streamlit app
- `data/raw`, `data/processed`, `outputs/`  gitignored working data; export small per-site stats tables, not full rasters
- `docs/specs/` specs (write before building); `docs/reference/` the two Claude best-practice guides; `docs/application/` beVisioneers text
- `legacy_uk/`  old UK wheat pipeline, READ-ONLY reference. Do not import or edit.
- `scratch/`    throwaway experiments (gitignored)
- `progress.md` session handoff log: update at the end of every session

## Rules
- Map, then verify facts from source, then spec, then build. One scoped task per session.
- Use subagents for large reads. Never assume: label each fact verified vs assumed, with source.
- Label approximate data "approximate". Never present traced boundaries as official.
- Output style: detailed, direct, objective.
- GEE project: `premium-episode-423509-g8`. Export CRS: UTM 37S (EPSG:32737) for Chyulu/Kasigau.
- No hardcoded absolute paths; use paths relative to the repo root.
- Unconfirmed: Verra IDs 612/1051 (Kasigau), Kasigau funding-start dates, 12,000 ha/yr loss and 1.7bn trees figures.
