# Progress log

## 2026-11-24
- Done: Week-1 ingest prototype (`canopyledger/pipeline/kenya_ingest.py`, tested 2023 on old placeholder Mau box; still single-AOI, EPSG:32736, needs rewrite to loop over sites and export stats tables).
- Done: approximate boundaries for Chyulu Hills (Verra 1408), Kasigau Phase I and II in `canopyledger/sites/sites_draft.geojson`.
- Done: folder structure, CLAUDE.md, .gitignore.
- Next: (1) map unread parts of `legacy_uk/dashboard.py` + analysis code via subagents -> `docs/uk-pipeline-notes.md`; (2) verify dataset IDs/claims; (3) specs in `docs/specs/` incl. site-file schema; (4) rewrite ingest per site.
- Open (user): confirm Verra IDs/status, Kasigau start dates, official boundary files, 12,000 ha/yr and 1.7bn trees sources.

## 2026-11-24 (later) - Phase 1 mapping done
- Notes written by subagents (read-only, nothing executed): `docs/uk-notes-dashboard.md`, `docs/uk-notes-analysis.md`.
- Application claims vs UK code: SARIMA 2020-23 -> 2024 CONTRADICTED (ARIMA(1,1,1)(1,1,1,12) + Prophet, fit on whole series, in-sample validation, dashboard.py L906-912); 225 km2 CONTRADICTED (code says 10 km2; box ~89 km2 by calc; 225 = 15x15 sample grid); z-score CONFIRMED (|z|>2.0 in analysis, >2.5 in dashboard); NDVI 0.3 PARTIAL (drought rule/fallback only; main thresholds 0.6/0.4/0.2); 15% cloud filter CONFIRMED (scene level).
- Action: rewrite the application's "What have you done" paragraph to match the code before submitting.
- Next: Phase 2 verification list (dataset IDs, claims 12,000 ha/yr, 1.7bn trees), then specs.

## Phase 2 verification (GEE part done; web claims pending subagent -> docs/verification-claims.md)
- `docs/verification-gee.md`: all planned dataset IDs exist. KEY: Sentinel-2 L2A effectively starts 2019 at both sites -> no S2 pre-funding baseline for 2010/2013 projects; use Hansen/Landsat for baseline, S2+S1 for monitoring from 2019.
- Web claims done: `docs/verification-claims.md` (subagent; several primary sites blocked, some figures secondary). Findings: 12,000 ha/yr is an OLD gross estimate (do not call current/net; GFW gross loss 2024 ~14,057 ha, FAO FRA 2025 net = gain); 1.7bn trees = Deputy President, 22 May 2026, other govt figures ~2bn+ (survival unverified); targets 10.6 Mha/15bn/2032 confirmed from launch speech; Carbon Markets Regs 2024 verification requirement CONFIRMED (Legal Notice 84/2024, regs 16, 20, 26) but NEMA as DNA NOT supported by the text; tree cover 12.13% (NFRA 2021); Kasigau cleared by Verra review (Feb 2024) but issuance stalled since 2022; Chyulu active (5.1M+ credits registered); new Kenya REDD+ registry (Jul 2025), national carbon registry (Feb 2026).
- Application edits needed: remove NEMA-as-DNA wording; replace 12,000 ha figure; fix 1.7bn attribution/date; fix UK claims (SARIMA, 225 km2); fix "since funding began" (S2 starts 2019).
- Open: Climate Change Act s.8(2A) DNA; whether Regulations amended since 2024.

## Phase 3 specs written (v0.1, awaiting user review): docs/specs/00-03
- Next build session: implement 01 (migrate sites file + validate.py) then 02 (ingest per site). Decide Q1 (independent validation points) and Q2 (dryland forest definition) before 03a.

## Migration done (spec 01)
- `canopyledger/sites/sites.geojson` (3 sites, normalised schema) + `validate.py` (passes 0 errors/0 warnings; negative tests catch bad type, duplicate id, missing field, missing position error). Old draft archived in `sites/_archive/`. One-off script: `scratch/migrate_sites.py`.
- Polygon areas recomputed geodesically: Chyulu 423,112 ha (+12.9%), Rukinga 31,950 (+5.9%), Phase II 178,050 (+4.9%) vs documented.
- Run from repo root with PYTHONPATH=. (no package install yet).
- Next: 02 ingest per site (rewrite kenya_ingest.py).
