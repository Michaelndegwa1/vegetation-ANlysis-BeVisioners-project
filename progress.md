# Progress log

## 2026-11-24
- Done: Week-1 ingest prototype (Week-1 single-AOI script (now archived), tested 2023 on old placeholder Mau box; still single-AOI, EPSG:32736, needs rewrite to loop over sites and export stats tables).
- Done: approximate boundaries for Chyulu Hills (Verra 1408), Kasigau Phase I and II in `canopyledger/sites/sites_draft.geojson`.
- Done: folder structure, CLAUDE.md, .gitignore.
- Next: (1) verify dataset IDs/claims; (2) specs in `docs/specs/` incl. site-file schema; (3) rewrite ingest per site.
- Open (user): confirm Verra IDs/status, Kasigau start dates, official boundary files, 12,000 ha/yr and 1.7bn trees sources.

## 2026-11-24 (later) - Phase 1 mapping done
- UK crop-monitoring material removed from the project on 2026-11-24 (moved to D:\New Projects\vegetation_uk_archive, outside the repo). The application text still describes that earlier project: pending user decision.
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
- Next: 02 ingest per site (per-site rewrite, done).

## Ingest rewrite (spec 02 v0.2) - built and tested on Kasigau I 2023
- New: `canopyledger/config.py`, `canopyledger/pipeline/ingest.py` (per site, site+ring, masks all/tree/woody, local + Drive modes, `--from-csv`). `kenya_ingest.py` now superseded (keep until Chyulu run confirmed, then archive).
- Tests passed (see end of docs/specs/02-ingest-spec.md): polygon-level dry run, sanity bounds, spot check 0.000%, ring area, idempotent output.
- Bugs found and fixed: Hansen 2024_v1_12 deprecated -> 2025_v1_13 (my earlier verification missed it); 72 simultaneous reductions -> "Too many concurrent aggregations" (now per-month getInfo); empty tree-mask cells vanished silently (now `_none` rows); 1e-14 non-reproducibility (rounded).
- MAJOR FINDING (docs/specs/03 Q2): Hansen tree cover is ~0 at Kasigau (>=30% cover: 0.1%/0.0% of area); WorldCover says 72-92% shrubland. Hansen-based baseline/classifier labels cannot work there. Needs user decision before 03a: woody-vegetation definition + independent labels + GEDI/Landsat baseline.
- Next: Chyulu runtime result; run all sites 2019-2024; then 03a once Q1/Q2 decided.

## 03a classifier spec written (v0.1): docs/specs/03a-woody-classifier.md
- Needs from user before build: confirm woody definition (default >=20% cover in 30 m plot), points per site (proposal 100), whether Google Earth Pro historical imagery near 2023 is usable at the sample areas, reliability thresholds (OA<0.75 or F1<0.70 -> low reliability).
- Ingest all-sites run (2019-2024) was running in background; check data/processed/stats and scratch/ingest_all.log.

- 03a decisions recorded (v0.2): 20% woody definition, 100 pts/site, reliability OA<0.75 or F1<0.70. Imagery date availability still unconfirmed.

## Benchmarks merged (2026-11-24): docs/benchmarks/benchmarks.md (+ part-a/b/c source notes)
- Web research by 3 subagents; many figures are search-summary only and flagged. Key results: 100 pts/site = about +/-7 pts OA (Wilson), no tight area CIs; WorldCover ~76.7% OA caps pseudo-label quality; Hansen (48% loss omission in SSA) and GEDI (cannot resolve shrubs <2.3 m) cannot baseline Kasigau -> Landsat baseline; S1 preprocessing incomplete (no speckle/terrain/orbit control); leakage ring 2 km is Verra's minimum -> add 5/10 km sensitivity rings and mask Tsavo; report 90% CI; Kenya forest def 15%/0.5 ha/2 m (our woody class is NOT the legal definition); VM0009 inactivated, CCP not applicable; never claim verification or over-crediting.
- Proposed spec changes listed in benchmarks.md section 4 (NOT applied). Decisions needed D1-D5 (section 5): reliability rule (CI lower bound vs point estimate), sample size, pseudo-label fallback, Landsat baseline, Kasigau methodology docs.
- Discrepancy to resolve: verification-claims.md says Kenya LN 84/2024 text was read; benchmark Part C could not fetch it. Re-check before quoting regulation numbers.
- Ingest all-sites run still in progress (6 of 18 site-years at merge time).

## Spec changes from benchmarks APPLIED to docs (not to code), 2026-11-24
- 01 -> v0.2 (leakage_rings_m, mask_protected_in_ring); 02 -> v0.3 (S1 orbit/speckle/terrain, 2/5/10 km rings + WDPA mask, yearly >=2-observation coverage row, per-mask sanity bounds, Drive mode for production, pipeline_version, tests 6-8); 03a -> v0.3 (no GEDI/Hansen baseline for Kasigau, CloudScore+ comparison, 10/15/20/30% sensitivity, PA+UA, 90% CI area + >10% low-precision flag, 0.5 ha MMU, definition note); 03 index: 03b parameters, 03d leakage-as-indicator, 03f report requirements P1-P7, new 03g Landsat baseline.
- NOT changed: application text (benchmarks section 4 item 5), code (config sanity bounds, sites.geojson fields, validate.py, ingest.py). Still open: D1-D3, D5.
- Ingest all-sites run complete: 18/18 site-years, 32,571 rows; 5 low-coverage site-months (Kasigau I 2019-10, 2022-09, 2024-01; Kasigau II 2019-10, 2024-01). Existing files use zone `ring` (= 2 km) and the v0.2 sanity bounds.
- Next build session: update sites.geojson + validate.py (01 v0.2), then ingest v0.3 (S1 preprocessing, rings, coverage row), then 03a pre-build checks.

## Site file + validator updated to spec 01 v0.2 (2026-11-24)
- `sites.geojson`: added leakage_rings_m [2000,5000,10000] and mask_protected_in_ring true to all sites; Kasigau I/II baseline_method = landsat_pre2019 (Hansen cannot baseline dryland shrubland); Chyulu stays hansen_2000_to_2018 provisionally (baseline_note) until spec 03g.
- `validate.py`: checks rings (int list, increasing, >= 2000 m, contains primary buffer), mask flag boolean, new baseline enum. Tests: `PYTHONPATH=. python tests/test_validate_sites.py` (12 checks incl. real file, all pass). One-off script scratch/migrate_sites_v2.py.
- Ingest code (v0.2) still reads only leakage_buffer_m, so it runs unchanged on the new file; v0.3 (rings, S1 preprocessing, coverage row) is the next build.

## UK removal + ingest v0.3 partial build (2026-11-24)
- User instruction: remove everything about UK crop monitoring. Done: `legacy_uk/`, the two UK notes files and the superseded Week-1 script moved OUT of the project to `D:\New Projects\vegetation_uk_archive` (moved, not deleted); references removed from CLAUDE.md, specs 00/02/03, progress and memory. NOT touched: `docs/application/...md` still describes the earlier UK project in its answers (user decision pending).
- Old stats (v0.2, zone `ring` = 2 km, 18 site-years) moved to `data/processed/stats_v0.2/`; `data/processed/stats/` holds only new v0.3 output (Kasigau I 2023 so far).
- Ingest v0.3 built except Sentinel-1 preprocessing; results and an unexplained 0.4-1.9% pixel-count offset recorded at the end of docs/specs/02-ingest-spec.md. Tests: `tests/test_validate_sites.py` (12), `tests/test_ingest_tables.py` (9).
- Next: (1) test Drive mode + `--from-csv`; (2) re-run all 18 site-years in v0.3 format via Drive mode; (3) Sentinel-1 preprocessing; (4) 03a pre-build checks.

## BUG FOUND AND FIXED: Hansen tree mask (2026-11-24)
- Symptom: Chyulu `tree` mask had 193 pixels (expected ~35,000 at 90 m); Kasigau empty. Cause: Hansen `lossyear` is MASKED (not 0) where there was no loss, so `tree_mask` collapsed to pixels with later loss. Fix: `unmask(0)` on lossyear and treecover2000. Regression test `tests/test_tree_mask_gee.py` (Chyulu 34,708 px = tc>=30 minus lost-before; Kasigau I 27 px at 90 m; both pass).
- AFFECTED (tree mask only; `all` and `woody` masks were unaffected): every stats file produced before the fix, including `data/processed/stats_v0.2/` (original 18) and `data/processed/stats_v0.3_buggy_treemask/`. Do not use their `tree` rows. Earlier statements that "Hansen tree mask is empty at Kasigau" came from this bug: the true Kasigau I count is tiny but not zero (27 px at 90 m, 0.07%); the 0.1%/0.0% Hansen shares in spec 03 Q2 came from a separate histogram and remain valid.
- Production re-run started with the fix (Kasigau I, Kasigau II, then Chyulu, local mode); log scratch/ingest_v03b.log. A failed site-year is now skipped and listed at the end instead of stopping the run. Drive task `kasigau_ph1_rukinga_2023_wide` still READY (queued); it used the buggy mask too and is only useful for testing the converter.

## Scope change (user, 2026-11-24): ingest Kasigau only for now
- Chyulu Hills is DEFERRED, not removed from the registry. Mechanism: `data/skip_sites.txt` (one site_id per line, read by ingest `load_sites`; delete the line to re-enable). The running production loop will reach Chyulu last and skip it automatically. Chyulu 2019 v0.3 output was discarded with the tree-mask fix, so no valid Chyulu stats exist now.
- Running now: Kasigau I (2019-2024) then Kasigau II (2019-2024), local mode, log scratch/ingest_v03b.log.

## Production run stopped by the system (low memory), 2026-11-24 ~18:30
- Claude Code reaped the background shell because the machine was critically low on memory (not a fault of the ingest). Not restarted automatically.
- State: Kasigau I 2019-2024 complete (6/6, validated: 936/936 cells, coverage 100%, 3 low-coverage months). Kasigau II 2019 written (1125 s); 2020-2024 NOT done. Chyulu deferred (data/skip_sites.txt).
- To resume (only when memory allows): `PYTHONPATH=. python -m canopyledger.pipeline.ingest --sites kasigau_ph2_ranches --start 2020 --end 2024 --run --mode local` (about 19 min per site-year, ~95 min total).
