# CanopyLedger benchmarks: what "good" looks like from ETL to the final report

Merged 2026-11-24 from three web-research passes (`part-a-data-etl.md`, `part-b-classification-validation.md`, `part-c-mrv-product.md`). Compared against specs 00-03a as they stand today. This file recommends; it changes no spec until the user approves.

## How to read this
- **Grades:** [S] standard or regulator text read directly; [P] peer-reviewed or agency document; [V] vendor/blog; [Sum] relayed through a search summary, primary text not read; [Own] our design choice, no external source.
- Many Part B figures are [Sum] because the primary PDFs were blocked. Treat every [Sum] number as a lead to re-check, not a fact.
- "Current" = what the specs or code do today. "Gap" = difference from the benchmark. "Action" = proposed change.
- No fixed minimum map-accuracy figure (such as 90%) exists in VM0009, VM0048, VMD0055 or the UN forest-monitoring guidance, as far as the research could find. The accuracy targets below are therefore peer-benchmark targets plus our own choices, not market requirements.

## 1. Headline findings (what these benchmarks change)

1. **100 points per site checks overall accuracy to about ±7 points, and no better.** Wilson 95% intervals at n=100: OA 0.80 gives 0.71-0.87; 0.85 gives 0.77-0.91; 0.90 gives 0.83-0.95. At n=50 per stratum the width is about ±10 points. It cannot support tight area estimates. [Part B, computed]
2. **Our training labels are weaker than assumed.** WorldCover v200 has 76.7% global OA (continents 73-82%) [P/Sum]. Per-class and Kenya figures were not found. Dynamic World shrub 47% and grass 34% averaged across three maps [Sum]. Pseudo-labels cap achievable accuracy and carry shrub/grass confusion into the model. No documented accuracy loss for pseudo-label training or year-to-year transfer was found, so the validation is a real experiment.
3. **Hansen and GEDI cannot supply a Kasigau baseline.** Hansen missed about 48% of loss in sub-Saharan Africa versus 14-17% elsewhere (2001-2014 version) [Sum]. GEDI RH98 in African savanna has bias -0.55 m, RMSE 1.64 m, and cannot resolve shrubs below about 2.3 m [Sum]. Spec 03a lists GEDI as a baseline option; for Kasigau it is not viable. The pre-2019 baseline for dryland sites should be Landsat-based (30 m, verified to exist; 2012 has only Landsat 7 with stripe gaps).
4. **Sentinel-1 preprocessing is incomplete.** GEE GRD is calibrated and terrain-corrected, but speckle filtering, radiometric terrain normalisation, layover/shadow masking and single-orbit compositing are left to the user [P: Mullissa 2021, Vollrath 2020]. Our ingest uses a plain median of all scenes. Chyulu is hilly, so this matters there most.
5. **Our leakage ring is at the floor of Verra practice.** VMD0055 v1.1: belt is forest within 10 km, narrowed to equal project forest area, with a minimum width of 2 km in all cases [S, read]. Chyulu itself uses large activity-shifting leakage areas (292,861 ha forest vs 265,548 ha project forest), which VM0009 calls "more purposeful than a belt" [S, read]. Recommend 2/5/10 km sensitivity rings, and state that our ring is an indicator, not credit accounting.
6. **Report area uncertainty as a two-sided 90% CI** (VM0048, ART TREES) [S / Sum], not only 95%. VMD0055 inflates area estimates when uncertainty exceeds 10% [S, read]; flag >10% as low precision (flag threshold is our choice).
7. **Kenya's forest definition is 15% canopy, 0.5 ha, 2 m height** (FAO: 10%, 0.5 ha, 5 m) [P/Sum]. Our woody class (>=20% cover in a 30 m plot, no height rule) is not the legal definition. Label it "woody vegetation" everywhere and add a 15% sensitivity run.
8. **CanopyLedger must not imply verification or a credit rating.** Verra inactivated VM0009; existing projects move to VM0048 at their next transition trigger; ICVCM never assessed VM0009, so Chyulu and Kasigau credits cannot carry the CCP label [S/P]. Kenya's July 2025 nesting guidelines require third-party verification by an accredited entity [S, read].
9. **Independent studies show widespread over-crediting from reference-area bias** (Swinfield et al., Nat. Commun. 2026: about 10.7x; West et al., Science 2023: about 3x) [P]. Neither evaluates Kasigau or Chyulu. Our product must not claim a project over- or under-issued.

## 2. Benchmark by pipeline stage

### 2.1 Data collection and ETL (spec 02, `pipeline/ingest.py`)

| # | Benchmark / target | Source | Current | Gap / action |
|---|---|---|---|---|
| E1 | Use `S2_SR_HARMONIZED`; do not use QA60 alone (QA60 stopped being produced 2022-01-25) | GEE catalog [S] | HARMONIZED + s2cloudless + SCL | None |
| E2 | Cloud mask: s2cloudless composite settings prob 40, buffer 100 m (tutorial values, temperate demo); CloudScore+ `cs_cdf` 0.50-0.65, 0.60 in Google's example. Only head-to-head found: OA 73% vs 72% (Google blog) | GEE tutorials/catalog [V] | prob 40, dilate 100 m | Add a CloudScore+ comparison on our sites before fixing the mask; no evidence it is "recommended over" s2cloudless |
| E3 | Cloud-mask sanity band: about 80-90% OA for Sentinel-2 masks | Skakun 2022 CMIX [P] | not measured | Measure on labelled points: record mask OA against the validation sample |
| E4 | Co-registration requirement <= 0.3 px (2 sigma); geometric refinement began 2021-08-23 | SentiWiki [S] requirement only | not checked | Flag 2019 to mid-2021 as possibly unrefined; compare a stable target before/after |
| E5 | S1: speckle filter (Refined Lee), radiometric terrain normalisation, layover/shadow mask, one orbit direction/track per composite | Mullissa 2021; Vollrath 2020 [P]; orbit rule from memory | plain median of all IW scenes | Add orbit-direction control and terrain handling (priority: Chyulu) |
| E6 | S1+S2 fusion expected gain about 0-4 pts OA (Sahel, S. African savanna); do not set as a pass criterion | Zhang 2019; Fundisi 2022; Heckel 2020 [P/Sum] | fused features planned | Treat as expectation only |
| E7 | Compositing statistic: median (evidence is Landsat only) | IJDE 2023; Flood 2013 [P/Sum] | median | Test p20/p50/p80 in 03a; nothing better established |
| E8 | Per-site-month completeness reported; monthly composites are materially less complete than seasonal (68.8% vs 98.5% in one China study) | Dynamic World China study [Sum] | `valid_frac`, `low_coverage` flag | OK; add the VM0009 test below (R3) |
| E9 | GEE: explicit `scale`, `maxPixels` set, `tileScale` 2-4 on memory errors, no `bestEffort` for reported stats; batch exports for heavy jobs, not `getInfo` | GEE docs [S] | scale 30, maxPixels 1e13, tileScale 4; `getInfo` per month for local runs | Use Drive mode for the production run and for any site-wide loop; `getInfo` only for tests |
| E10 | GEE noncommercial quota tiers (150 or 1,000 EECU-hours/month; about 2 concurrent batch tasks), dates unconfirmed | GEE usage pages [Sum] | one `getInfo` stream | Log EECU use; confirm quota before large runs |
| E11 | Provenance: STAC-style metadata, semantic versioning of pipeline and dataset | STAC/OGC, FAIR [P] | JSON sidecar per file | Add a pipeline version number and git/commit id when the repo is under git |
| E12 | Pipeline tests: idempotency, regression tests, range/completeness thresholds. No citable standard found | from memory | idempotent, spot check, ring area, sanity bounds | Keep ours; document them as our own |
| E13 | Latency benchmark: GLAD-S2 5-day cadence; integrated alerts daily; DIST-ALERT weekly; optical revisit 1-4 days; RADD radar up to about 12 days | GFW pages [Sum] | monthly stats | Monthly is acceptable for ledger statistics; alerts need their own cadence, state latency honestly |

### 2.2 Classification (spec 03a)

| # | Benchmark / target | Source | Current | Gap / action |
|---|---|---|---|---|
| C1 | OA woody vs non-woody per site >= 0.85 with Wilson 95% interval reported (n=100 gives lower bound 0.77) | Borges 2020: best 86.3% for S1+S2 in savanna [P]; WorldCover 76.7% as floor | flag low reliability if OA < 0.75 or F1 < 0.70 | Reliability rule should use the interval; see decision D1 |
| C2 | Multi-class (tree/shrub/grass) OA >= 0.77 (beat WorldCover global) | WorldCover v200 [P/Sum] | not specified | Add to 03a validation report as a secondary metric |
| C3 | Woody-class producer's accuracy >= 0.71 (Sahel SVM baseline), aim higher | Li, Lyu, Fensholt 2019 [Sum] | F1 >= 0.70 | Report PA and UA separately, not only F1 |
| C4 | Stratified random reference sample; >= 50 per stratum, 75-100 for rare strata; area from sample not pixel count; OA/UA/PA with CIs | Olofsson 2014, quoted via secondary source [Sum] | 100 per site (about 50 per map class) | Meets the minimum only; area CI will be wide; see D2 |
| C5 | Expected user's accuracy for sample design 0.70-0.75 (illustrative) | sits book [Sum] | not used | Use to compute sample sizes if D2 is reopened |
| C6 | Training on a global map: WorldCover (about 76.7% OA) caps accuracy | Part B section 6 | WorldCover pseudo-labels | Fallback: train with cross-validated human labels (needs a fresh headline sample) |
| C7 | Forest definition layer: Kenya >= 15% canopy, >= 0.5 ha, >= 2 m; FAO 10%/0.5 ha/5 m as sensitivity | CIFOR-ICRAF WP 24; JICA; Nesting Guidelines [P/S] | 20% cover, 30 m plot | Add 15% to the 10/30% sensitivity set; apply 0.5 ha minimum mapping unit (about 6 Sentinel-2 30 m cells) to loss/gain events |
| C8 | Report class definitions and data accuracy next to each output (e.g. WorldCover 76.7% OA global) | Part C [S/Sum] | sidecar JSON only | Add a data-source table to every report |

### 2.3 Change detection and alerts (spec 03b, 03c)

| # | Benchmark / target | Source | Gap / action |
|---|---|---|---|
| D-a | CCDC Earth Engine defaults: minObservations 6, chi-square 0.99, minNumOfYearsScaler 1.33 (starting values) | EE docs via search summary [Sum] | Start with these, tune on validation |
| D-b | CCDC with Sentinel-2: about 20% omission at 30-40 day lag (reference to match, not guaranteed) | IJAEOG 2024 [Sum] | Measure ours on labelled loss events |
| D-c | Alert precision for events >= 0.2 ha: UA 97.6%, PA 95% (RADD, humid forest only); 74% of core pixels confirmed within 24 days, 95% within 48 days | Reiche 2021 [P, read] | No dryland figure exists; our dryland false-alarm rate is unknown and must be measured |
| D-d | Minimum validated alert size 0.2 ha (RADD) | Reiche 2021 [P] | Our minimum mapping unit is 0.5 ha (C7); small clearings below it are not claimed |
| D-e | Alerts are signals for verification, not area estimates | GFW guidance [Sum] | State on every alert |
| D-f | Only about 5-6 years of Sentinel-2 history (2019-2024) for harmonic fits; no source gives a minimum | Part B | Compare CCDC with a simple annual-difference baseline and report both |

### 2.4 Uncertainty, leakage and scorecard (spec 03d)

| # | Benchmark / target | Source | Current | Gap / action |
|---|---|---|---|---|
| R1 | Report area with two-sided 90% CI; probability-sample reference data; confusion matrix | VM0048 v1.0 [S]; Olofsson 2014; ART TREES (secondary) | 95% Wilson planned | Report 90% CI on areas, keep 95% on accuracy and say which |
| R2 | Flag area estimates with uncertainty > 10% as low precision; Verra inflates conservatively above 10% | VMD0055 v1.1 eq. 29-30 [S, read] | none | Add flag (threshold is Verra's rule, using it as a flag is our choice) |
| R3 | Coverage test: at least two cloud-free observations for >= 90% of the area in each period | VM0009 v3.0 s6.8.4 [S, read] | `valid_frac` for >= 1 clear obs per month | Add a per-year check: share of pixels with S2_N >= 2; record pass/fail |
| R4 | Leakage ring minimum 2 km; belt up to 10 km, cap about the project forest area | VMD0055 v1.1 A1.2.2 [S, read] | fixed 2 km, Tsavo inside the ring | Add 5 and 10 km rings; mask protected areas (WDPA) in the ring; state ring = indicator |
| R5 | Imagery resolution 30 m or finer; Verra uses 10 m or finer for AD interpretation; monitoring period <= 5 years (VM0009), annual activity data (VM0048) | VM0009 v3.0; VMD0055 [S] | 10 m S2, 30 m stats | Fine; headline numbers annual |
| R6 | Co-registration <= 0.4 px at 90% CI (Chyulu project standard) | Chyulu PD PDR.53 [S] | not tested | Same check as E4 |
| R7 | Baselines: independent studies find reference-area bias drove over-crediting | Swinfield 2026; West 2023 [P] | baseline method not yet built | Do not claim over/under-issuance; describe our baseline and its limits |

### 2.5 Report and product (spec 03f)

| # | Requirement | Source | Action |
|---|---|---|---|
| P1 | Never claim CCP, Verra verification or crediting status; CanopyLedger is not an accredited verifier | ICVCM Nov 2024; Nesting Guidelines paras 26-29 [S] | Put this notice on every page and PDF |
| P2 | Disclose approximate boundaries and the +/- km error on every map and number | Own (no source found; Part C could not find guidance) | Already in `boundary_quality`; render it in the UI |
| P3 | Dryland caveat: optical tree-cover change is harder in savanna; omission likely for small clearings | Tyukavina 2018 and woodland study [Sum] | Add to the limitations section |
| P4 | Data-source disclosure: dataset, version, date range, resolution, known accuracy | ESA WorldCover [S] | Auto-generated table from sidecar JSON |
| P5 | Cadence: annual headline numbers plus monthly series plus alerts with honest latency per source and a confidence class | VM0009/VMD0055; GFW [S/Sum] | Dashboard design |
| P6 | Disclose Kenyan context: monitoring expected to align with the national forest monitoring system; third-party verification by an accredited entity | Nesting Guidelines (July 2025) [S, read] | Add a "how this relates to Kenyan rules" box |
| P7 | No example site reports from rating agencies, ART TREES, MapBiomas or NICFI were found, and no funder benchmark for alert latency | Part C | Design our own report; test it with a real reader |

## 3. Consolidated KPI scorecard (what we will measure and pass)

Pass levels are the targets above; those marked [Own] are our choices.

| Stage | KPI | Target | Measured how | Status now |
|---|---|---|---|---|
| ETL | Sites/years produced | 3 sites x 2019-2024 | files in `data/processed/stats` | run in progress (6 of 18 site-years written when this was merged) |
| ETL | Idempotent output | byte-identical on re-run | diff two runs | PASS (Kasigau I 2023) |
| ETL | Spot-check vs independent computation | within 1% [Own] | manual getInfo | PASS (0.000%) |
| ETL | Per-month valid pixel fraction reported | 100% of site-months | `valid_frac` column | PASS in tests |
| ETL | Two-observation coverage per year | >= 90% of area [VM0009] | S2_N >= 2 share | not yet computed |
| ETL | Cloud-mask accuracy | about 80-90% OA [Skakun] | reference points | not measured |
| ETL | S1 preprocessing complete | speckle + terrain + orbit control | code review | NOT DONE |
| Classification | OA per site | >= 0.85, Wilson 95% interval shown | 100 blind human points/site | not started |
| Classification | Woody PA / UA | PA >= 0.71, UA reported | confusion matrix | not started |
| Classification | Reliability flag | per D1 | independent points | rule to confirm |
| Classification | Area estimate | error-adjusted, 90% CI, flagged if >10% | stratified estimator | not started |
| Classification | Definition sensitivity | 10/15/20/30% reported | re-label or re-threshold | not started |
| Change | Loss event precision / omission | measure; reference 20% omission at 30-40 d lag | labelled events | not started |
| Change | Minimum mapping unit | 0.5 ha [Kenya definition] | sieve in code | not started |
| Leakage | Rings reported | 2, 5, 10 km, protected areas masked | scorecard | NOT DONE (2 km only) |
| Report | Disclaimers | P1-P4, P6 present | checklist | not started |

## 4. Proposed changes to the specs (NOT applied; await approval)

1. **Spec 02 v0.3:** add Sentinel-1 orbit-direction control and a terrain/speckle step (E5); add 5 km and 10 km rings and an optional protected-area mask (R4); add a per-year two-observation coverage statistic (R3); use Drive mode for the production run (E9).
2. **Spec 03a v0.3:** remove GEDI as a Kasigau baseline option and name Landsat-based baseline for dryland sites; add a CloudScore+ comparison (E2); add 15% to the sensitivity set (C7); report PA and UA, multi-class OA, and 90% CI on area (C2, C3, R1, R2); add the definition note "woody vegetation, not the legal forest definition" (C7, P1).
3. **Spec 03b:** specify CCDC starting parameters (D-a), a minimum mapping unit of 0.5 ha, and a simple annual-difference comparison.
4. **Spec 03d/03f:** report template with P1-P7, 90% CI, leakage as indicator, honest alert latency.
5. **Application text:** replace "forest" with "woody vegetation" for the dryland sites, state that CanopyLedger supports but does not replace verification, and avoid any claim about over-crediting of Kasigau or Chyulu.

## 5. Decisions needed from the user

- **D1 Reliability rule.** Current rule uses point estimates (OA < 0.75 or F1 < 0.70). With n=100, a point estimate of 0.80 has lower bound 0.71. Options: (a) keep point-estimate rule and always show the interval; (b) use the lower bound >= 0.75 (stricter, fewer sites pass). Recommendation: (b) for the dashboard label, (a) for the internal gate.
- **D2 Sample size.** 100 per site gives about ±7 points on OA and wide area intervals. Options: keep 100 and report the width honestly; raise to 150 per site (about ±6); or add a second, separate human sample to train/adjust. Recommendation: keep 100 now, run the experiment, and enlarge only if intervals prove too wide.
- **D3 Pseudo-labels.** If validation shows poor accuracy at Kasigau, are you willing to label an extra training sample (separate from the validation points)?
- **D4 Confirm the baseline for dryland sites** as Landsat-based (not Hansen, not GEDI).
- **D5 Methodology facts:** Kasigau's methodology version (VM0009 version, leakage areas) is not confirmed; it needs the Kasigau project documents on the Verra registry.

## 6. What could not be verified (consolidated)

- No fixed minimum map-accuracy percentage in VM0009, VM0048, VMD0055 or UN forest-monitoring guidance (not found, not proven absent).
- WorldCover per-class and Africa/Kenya accuracy; Dynamic World's own paper numbers; Hansen dryland tree-cover accuracy; JRC TMF accuracy; accuracy loss for pseudo-label training and year-to-year transfer.
- Olofsson 2013/2014 primary text; ART TREES v2.0 official text; the 15% figure is TREES v1 via summary.
- CloudScore+ validation numbers and any explicit recommendation over s2cloudless; measured Sentinel-2 geolocation figures; S2 BRDF/terrain residuals; minimum observations per composite; dryland temporal resolution; clean S1+S2 gains in cloudy tropics.
- CCDC minimum observations/years and observation-density effects; dryland alert false-alarm rates.
- RADD/NICFI/SERVIR latency and completeness; funder expectations on cadence; example third-party site reports.
- Primary text of Kenya Legal Notice 84/2024: the earlier claims pass (`docs/verification-claims.md`) says it read the Kenya Law text, while Part C could not fetch it. Re-check before quoting regulation numbers. No confirmed 2025/2026 amendment found.
- Kasigau methodology version and leakage-area sizes (only secondary summaries); vendor ratings for the two projects (a BeZero BBB for a Kasigau project is reported by a source that mislabels the project number).
- Guidance on labelling approximate boundaries and avoiding implied certification: none found.

## 7. Source files
Full source lists, quotes, caveats and URLs are in the three part files in this folder. Part A: ETL and sensors. Part B: classification, validation, change detection, definitions. Part C: Verra, ICVCM, Kenya rules, leakage, rating vendors, reporting.
