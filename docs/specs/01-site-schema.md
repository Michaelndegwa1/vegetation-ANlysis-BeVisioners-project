# 01 Site registry schema (spec v0.1)

File: `canopyledger/sites/sites.geojson` (promote from `sites_draft.geojson` once migrated). One Feature per project or separately credited phase. CRS EPSG:4326. Geometry: valid Polygon or MultiPolygon.

## Properties
| Field | Type | Required | Rule |
|---|---|---|---|
| site_id | string | yes | unique lowercase slug, e.g. `chyulu_hills_redd`, `kasigau_ph1_rukinga`, `kasigau_ph2_ranches` |
| name | string | yes | display name |
| project_type | enum | yes | `REDD+` `ARR` `IFM`; anything else is rejected as unsupported |
| registry | string | yes | e.g. `Verra VCS` |
| registry_id | int/null | yes | null until user-confirmed |
| registry_id_status | enum | yes | `confirmed` `unverified` |
| registry_id_candidate | int/null | no | e.g. 612 / 1051 for Kasigau (unverified) |
| funding_start | date/null | yes | crediting start; null if sources conflict |
| funding_start_note | string | no | why null / source conflict |
| crediting_end | date/null | no | |
| monitoring_start | date | yes | first month with usable S2 (default 2019-01-01) |
| baseline_method | enum | yes | `hansen_2000_to_2018` (default) |
| boundary_quality | enum | yes | `approximate` `official` |
| boundary_source | string | yes | document + figure/page, or registry file |
| position_error_km | number/null | yes | numeric upper estimate; null if official |
| area_ha_documented | number/null | yes | from project documents |
| area_ha_documented_source | string | yes | |
| area_ha_alt | object | no | other documented values keyed by source |
| area_ha_polygon | number | computed | geodesic area of the geometry; recomputed, never hand-edited |
| leakage_buffer_m | int | yes | default 2000 |
| notes | string | no | |

## Validation (`canopyledger/sites/validate.py`, written in the ingest session)
1. Valid geometry; lon 33.5-42, lat -5 to 5.5 (Kenya box).
2. Unique site_id; required fields present; enums legal.
3. |area_ha_polygon - area_ha_documented| / documented <= 15% else warning; > 30% error.
4. boundary_quality=approximate requires a numeric position_error_km.
5. Leakage ring = buffer(site, leakage_buffer_m) minus site, computed in a metric CRS (EPSG:32737 for the current sites), not stored.

## Migration of sites_draft.geojson (current gaps)
- Chyulu uses `vcs_id`, `doc_area_ha` and a text `position_error_km`. Normalise to the fields above (registry_id=1408, status unverified until the user confirms on the registry).
- Add site_id, registry_id_status, monitoring_start, baseline_method, numeric position_error_km (3 / 4 / 4 as upper bounds), leakage_buffer_m.
- Kasigau Phase I funding_start stays null (2005 vs 2010 conflict). Phase II 2010-01-01 stays flagged.
- Chyulu area conflict (374,678 vs 410,534 ha vs traced 422,977): keep all in area_ha_alt; documented = 374,678 (2016 CCB report) until the registry confirms.
