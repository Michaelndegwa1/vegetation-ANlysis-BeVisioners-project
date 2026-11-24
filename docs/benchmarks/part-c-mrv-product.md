# Part C - MRV standards, market practice, Kenya rules and report-product benchmarks

Research date: 2026-11-24. Method: web search plus direct text extraction from primary PDFs (VM0009 v3.0, VMD0055 v1.1, VM0048 v1.0, Chyulu Project Description and Monitoring Report, Kenya REDD+ Nesting Guidelines). Reliability labels: STANDARD = methodology/standard text read directly; PROJECT DOC = registered project document read directly; REGULATOR = government document; PEER = peer-reviewed; VENDOR = company material; SECONDARY = law-firm, news or summary reporting (not checked against the primary text). Nothing here is from memory unless marked "from memory, unverified" (none used).

---

## 1. Verra REDD+ requirements and what Chyulu / Kasigau actually use

### 1.1 Methodology actually used
| Project | Methodology | Evidence | Reliability |
|---|---|---|---|
| Chyulu Hills REDD+ (VCS 1408) | VM0009 v3.0 "Methodology for Avoided Ecosystem Conversion", "no deviations from the methodology" (PD s4.3). Two project accounting areas: Forest (265,548 ha) and Grassland (109,131 ha) | Project Description v1.42, 23 Jun 2015, PD s4.1-4.3, Table 27. https://coolEffect.org/lib/content/wp-content/uploads/2021/01/Africa-Kenya-Chyulu-Hills-PROJ_DESC_1408_23JUN2015-1.pdf ; Monitoring Report (19 Sep 2013 - 31 Dec 2016, issued 21 Sep 2017) states the same methodology: https://coolEffect.org/lib/content/wp-content/uploads/2021/01/Africa-Chyulu-HIlls-MONIT_REP_1408_19SEP2013_31DEC2016.pdf | PROJECT DOC (2015, 2017) |
| Kasigau Corridor Phase II (VCS 612) | VM0009 (version not confirmed) | Bank-hosted registry summary lists "Protocol: VM0009"; IGES REDD database also lists VM0009. BMO summary: https://www.bmo.com/dam_asset/asset/381dc486-81a6-4cee-a017-adc6e5dcbb6d/VCS612-The-Kasigau-Corridor-REDD-Project-Phase-II-The-Community-Ranches.pdf | SECONDARY (third-party summary of the registry listing) |
| Kasigau Corridor Phase I (VCS 562) | VM0009 (version not confirmed) | Phase I project description (earthly.org mirror) is described as prepared for VCS 2007.1 using VM0009; mirror PDF could not be opened by me (file served as damaged). https://earthly.org/wp-content/uploads/2020/09/Kasigau-Project-Description.pdf | SECONDARY, partial |

VM0009 v3.0 itself: Verra, 6 June 2014, authored by Wildlife Works and ecoPartners (the Kasigau developer). https://verra.org/documents/vm0009-methodology-for-avoided-ecosystem-conversion-v3-0 (STANDARD).

### 1.2 VM0009 status and the VM0048 transition
- Verra inactivated VM0009 "effective immediately" (program notice); projects already validated under VM0009 may use it until they must transition to VM0048 or reach next baseline reassessment or crediting-period renewal, whichever is first. Source: https://verra.org/program-notice/verra-inactivates-and-updates-existing-redd-methodologies/ and https://verra.org/methodologies-main/transition-process-by-project-status/ (REGULATOR/program owner; read via search summary, not full text).
- A Calyx commentary (Apr 2026) says existing AUD projects transition to VM0048 at their next verification once the jurisdiction's risk maps have been available six months. https://calyxglobal.com/research-hub/commentary/vm0048-after-two-years-first-credits-on-the-horizon (SECONDARY). Whether Kenya has such maps: not found.
- Under VM0048 developers do not pick their own reference areas; Verra supplies activity data (AD) via an "AD Baseline Allocation Report" (VMD0055 v1.1 s5.1.3, A1.2.2; ICVCM assessment says this "substantially reduces" over-crediting risk). STANDARD + SECONDARY.

### 1.3 Monitoring frequency, accuracy, uncertainty (primary text)
| Item | Requirement | Source |
|---|---|---|
| Monitoring period length | VM0009 v3.0: each monitoring period "must be less than or equal to five years" (s2.2 definition of monitoring period) | VM0009 v3.0 (STANDARD) |
| Plot remeasurement | VM0009: carbon plots remeasured at least every five years | VM0009 v3.0 (STANDARD) |
| Baseline revision | VM0009: at least every 10 years (s6.20); conversion parameters re-estimated at least every five years | VM0009 v3.0 (STANDARD) |
| Imagery for baseline | VM0009 s6.8.4: "double coverage" (>= 2 cloud-free images) for >= 90% of the reference area across the reference period; minimum spatial resolution 30 m | VM0009 v3.0 (STANDARD) |
| Sample size for conversion rate | VM0009 s6.8.5: optional; ~300 points suggested; precision +/-15% of conversion proportion | VM0009 v3.0 (STANDARD) |
| Map accuracy | VM0009 uses point-sample interpretation of imagery and a standard-error "confidence deduction" (s8.4.1.1, [F.57]); it is "not based on propagation of error"; negative values set to zero. I found NO fixed minimum map-accuracy percentage (e.g. 90%) in VM0009 | VM0009 v3.0 (STANDARD) |
| Image co-registration | Chyulu PD: max image-to-image error 0.4 pixel (12 m) at 90% CI | Chyulu PD PDR.53 (PROJECT DOC) |
| VM0048 reporting | Each monitoring report must give deforestation area in project area and leakage belt, per year, "with an estimate of uncertainty, representing sampling error as a two-sided 90 percent confidence interval" | VM0048 v1.0 (STANDARD) https://verra.org/documents/vm0048-reducing-emissions-from-deforestation-and-forest-degradation-v1-0 |
| VM0048/VMD0055 AD method | Monitoring AD must be sample-based, human interpretation of imagery 10 m or finer in sample plots; FCBM (forest cover benchmark map) resolution 30 m or finer; MMU must match forest-definition area threshold; stratified design | VMD0055 v1.1 s5.3.3.2, A1.x (STANDARD) https://verra.org/documents/vmd0055-estimation-emission-reductions-from-avoiding-unplanned-deforestation-v1-1 |
| VMD0055 uncertainty rule | If % uncertainty of deforestation area <= 10% (90% CI): no change. If > 10%: area is scaled up by an inflation factor built from U% and the t-values for a one-sided 66.67% interval (0.4307) and two-sided 90% interval (1.6449) (eq. 29-30; exact formula garbled in my text extraction), i.e. conservative inflation, not a map-accuracy threshold | VMD0055 v1.1 (STANDARD) |
| VM0048 forest definition | "Forest" must include woody vegetation with canopy cover between 10 and 30 percent "as used in the relevant country's international reporting to the UNFCCC, or as otherwise officially elected" | VM0048 v1.0 definitions (STANDARD) |
| Permanence / buffer | Chyulu used VCS AFOLU Non-Permanence Risk Tool v3.2: overall risk "moderate" (percentage not extracted by me); credits = GER minus confidence deduction minus buffer allocation | Chyulu PD s5.6 (PROJECT DOC). Current VM0048 buffer percentage: not verified |

Not found: a numeric "90% minimum map accuracy" requirement in VM0009 or VMD0055. Treat any such figure as a vendor/internal convention, not a Verra rule.

### 1.4 Leakage actually used by Chyulu
- Chyulu uses VM0009 "activity-shifting leakage areas", one per accounting area, not a fixed-width belt. Forest leakage area 292,861 ha vs forest PAA 265,548 ha; grassland leakage area 101,616 ha vs PAA 109,131 ha (Table 27). Leakage areas must be un-converted at project start, similar landscape, equally accessible to conversion agents, and no larger than the PAA (PDR.107-109). Chyulu PD (PROJECT DOC).
- VM0009 v3.0 text: the activity-shifting leakage area "is more purposeful than a belt or an arbitrary buffer around the project area" (Introduction). STANDARD.
- Ex-ante leakage assumption in Chyulu PD: 8% annual leakage rate; the PD says Kasigau Phase I and II "have continually enjoyed leakage rates under 10%" in their 4th monitoring period (developer statement, unverified independently). PROJECT DOC.
- Chyulu Hills first monitoring period (2013-2016) reported 2,033,002 tCO2e prevented (developer claim, verified by SCS Global Services). PROJECT DOC.
- Kasigau Phase I leakage monitoring area 38,889 ha and reference area 329,022 ha per IGES REDD database (SECONDARY; leakage management area size "not given"). https://redd-database.iges.or.jp/download/project_id=91.pdf (could not re-open the PDF myself; figures as relayed by search summary).

---

## 2. Independent monitoring, ratings, criticism

### 2.1 ICVCM Core Carbon Principles
- ICVCM approved three REDD+ methodologies in Nov 2024: ART TREES v2.0, Verra VM0048 v1.0 and JNR v4.1. Verra excluded VM0006, VM0007, VM0009, VM0015, VM0037 from assessment, so credits issued under them "will not be able to receive the CCP label". Mixed-methodology projects: only projects solely using approved methodologies are eligible. Source: https://icvcm.org/integrity-council-approves-three-redd-methodologies/ (REGULATOR/standard-setter, via search summary). Consequence: Chyulu and Kasigau credits issued under VM0009 are not CCP-eligible. The CanopyLedger report must not imply CCP status.
- Nov 2025 clarification: nested projects in JNR Scenario 1 are covered. https://verra.org/icvcm-clarifies-approval-of-verras-vm0048-to-include-jurisdictional-and-nested-redd-framework-scenario-1/ (SECONDARY summary).

### 2.2 ART TREES
- Uncertainty: Monte Carlo (>= 10,000 iterations), 90% CI, uncertainty adjustment UA = 0.524417 x HW90 / 1.645006; deduction = (ER + removals) x UA; "systematic underestimation is acceptable, overestimation prohibited". Source: a training site (seamusrobertmurphy.quarto.pub, REDD+ Uncertainty Training), NOT the ART standard text. SECONDARY. Official ART TREES v2.0 text not retrieved.
- Under the FCPF scheme: no deduction if uncertainty <= 15% (reported by same SECONDARY source).

### 2.3 Rating agencies and MRV vendors
| Actor | What is public | Reliability / notes |
|---|---|---|
| Sylvera | Blog 24 Sep 2021 "Rating African drylands": rated Kasigau, Kariba, Chyulu Hills; used ALOS PALSAR radar mosaics back to 2007, ML drylands prototypes, FAO Global Drylands Assessment data for benchmarks; says its standard forest method "did not give accurate results for drylands". Overall letter grades for Kasigau/Chyulu NOT given in the post. https://www.sylvera.com/blog/rating-african-drylands | VENDOR |
| BeZero | A Fastmarkets article says a Kasigau project was put on ratings watch then reaffirmed at BBB (article calls it "Phase 1 (VCS 612)", but 612 is Phase II: internal inconsistency). https://www.fastmarkets.com/insights/redd-projects-show-broad-price-ratings-correlation-but-project-specific-factors-remain/ . Chyulu BeZero rating: not found. | SECONDARY |
| Carbon Market Watch 2023 | Agencies (BeZero, Calyx, Renoster, Sylvera) often disagree; the same project can be top tier at one and low at another; a "B" means different things per scale; safeguards not in core ratings. https://carbonmarketwatch.org/wp-content/uploads/2023/09/PCG_CMW_rating_agencies_final_report_.pdf | NGO report (funded study), 2023 |
| Chloris Geospatial | Claims validation vs airborne LiDAR and field data in its own white papers. https://emu-piccolo-m9bl.squarespace.com/resources/validation-of-chloris-geospatial-estimates-4fc39 | VENDOR. Independent savanna-specific error figures: not found |
| Planet / NICFI, Pachama/Renoster, Carbon Direct, Cumberland | No accuracy figures retrieved | not found |
| Biomass-map validation generally | No community-accepted standard for satellite biomass map validation; global AGB map errors are spatially correlated over ~50-104 km (cited in search results from CEOS-linked review and a 2022 framework paper; citations not individually opened) | PEER/review, via summary |

### 2.4 Over-crediting evidence
- Swinfield et al., "Learning lessons from over-crediting to ensure additionality in forest carbon credits", Nature Communications, Apr 2026, doi 10.1038/s41467-026-71552-3: pooled six ex-post evaluations of 44 first-generation REDD+ projects; credits ~10.7x the independently estimated avoided deforestation; cause is reference-area selection bias and unrealistic ex-ante modelling, not the forest-cover data. PEER (read abstract/press only). https://research.bangor.ac.uk/en/publications/learning-lessons-from-over-crediting-to-ensure-additionality-in-f/
- West et al. 2023, Science 381:873-877, doi 10.1126/science.ade3535: 27 projects, synthetic controls; offsets ~3x what was mitigated. Study countries per Bonn release: Peru, Colombia, DRC, Tanzania, Zambia, Cambodia. Kenya not listed; Kasigau/Chyulu not confirmed in the study. PEER.
- Kasigau specifics found: (a) Context news: critics say project overstates deforestation threat (SECONDARY); (b) Chomba 2016 Land Use Policy on benefit distribution (SECONDARY mention); (c) 2023 KHRC/SOMO abuse allegations, Verra halted issuance then lifted it 1 Feb 2024 after review. https://verra.org/verra-completes-review-of-kasigau-projects/ (program owner); KHRC/SOMO criticise the review's reliance on Wildlife Works' internal investigation. (d) S&P Global (Jul 2026) headline: Wildlife Works exploring new issuance from Kasigau after methodology changes stalled issuance for four years (headline only read). Chyulu-specific controversy: not found. A project-specific quasi-experimental over-crediting estimate for Kasigau or Chyulu: not found.

---

## 3. Kenya requirements

| Topic | Finding | Source / reliability |
|---|---|---|
| Carbon Markets Regulations 2024 (LN 84 of 2024) | In force 17 May 2024; apply to voluntary and compliance markets; projects public/private/community; project approval chain (concept note -> letter of no objection -> PDD -> letter of approval; start within 12 months). | Oraro legal alert https://www.oraro.co.ke/wp-content/uploads/2024/05/Legal-Alert-The-Climate-Change-Carbon-Markets-Regulations-2024-.pdf (SECONDARY). Primary text (Kenya Law https://new.kenyalaw.org/akn/ke/act/ln/2024/84/eng@2024-06-07) could not be fetched; regulation numbers not verified. |
| National Carbon Registry | Under s23G of the Act; run by DNA (NEMA) as National Registrar; six sector registries | Oraro (SECONDARY) |
| Benefit sharing | Land-based projects on public/community land: annual social contribution of at least 40% of previous-year aggregate earnings; non-land-based: at least 25%. Private-land projects exempt (per other summary). | Oraro (SECONDARY) |
| Disclosure | Proponents must regularly disclose project costs, expected reductions, revenue and verified ERs issued to DNA | Oraro (SECONDARY) |
| Transition of existing projects | Pre-existing proponents must comply within two years of commencement (about May 2026); environmental audit within six months | Oraro (SECONDARY). What happened at the deadline: not found |
| MRV format | No prescribed digital MRV data format found in 2024 Regulations summaries | not found |
| REDD+ Nesting Guidelines (MoECCF, July 2025; hosted Feb 2026) | "Forest" = min 15% canopy cover, 0.5 ha, potential 2 m at maturity (Terms). Monitoring "should be aligned with" NFMS and use "latest versions of adopted national protocols" for AD and EFs (paras 26-28); nested projects use jurisdictional forest-inventory and remote-sensing methods; validation/verification by accredited third party (para 29); site-scale projects "should transition" to nested projects and the Approved Nested Baseline within one year of approval (para 31). Eligible methodologies: Verra JNR, TREES, others on DNA list (Annex I). | REGULATOR. https://forestry.go.ke/sites/default/files/2026-02/Kenya%27s%20REDD%2B%20Nesting%20Guidelines.pdf (read directly) |
| Guide for Strategic Engagement in Carbon Markets (v1, July 2026) | 10 MtCO2e cumulative cap on international transfers 2025-2030; letter of authorisation ex-post only; FOLU excluded from priority whitelist for this NDC period "pending better baseline data"; does not bar voluntary market; prefers digital MRV; Annex 3 MRV criteria (parameters, frequency, QC, data management) | RAMO article https://www.ramo.earth/blog-en/kenya-carbon-budget-article-6 (SECONDARY; guide itself not read) |
| 2025/2026 amendments to the 2024 Regulations | One commentary says draft Carbon Trading and Carbon Registry Regulations 2026 remain in draft; no confirmed amendment to LN 84 found | SECONDARY. Treat as unverified |
| Does Verra require the national forest definition? | VM0048: yes, as used in country's UNFCCC reporting or officially elected (10-30% canopy band). Kenya's definition is 15% / 0.5 ha / 2 m (also used in Kenya FREL, FCCC/TAR/2020/KEN: https://unfccc.int/sites/default/files/resource/tar2020_KEN.pdf). Chyulu PD (VM0009) reports Kenya's definition (15%, 0.5 ha, 2 m) and shows its sparsest stratum (16.2% cover, 3.7 m) just passes it. | STANDARD + REGULATOR + PROJECT DOC. Whether Kenya Regulations 2024 themselves mandate the definition: not found |

---

## 4. Leakage belt and baseline benchmarks

- VMD0055 v1.1 A1.2.2 (STANDARD): leakage belt = forest within a 10 km buffer of the project area (excluding foreign territory and mapped exclusions); if the forest in the 10 km buffer exceeds the project area's forest at start date, narrow the buffer until belt forest area equals project area; "The minimum UDef LB buffer width must in all cases be 2 km." Verra, not the developer, defines the belt. Non-contiguous patches separated by <= 4 km are grouped. Overlapping belts of other VCS AFOLU projects must be discounted or covered by a leakage belt agreement (s5.1.3). Project activities region extends 10 km (s5.1.6).
- Therefore a 2 km ring is the VM0048/VMD0055 floor and consistent with the lower bound of practice; the legacy VM0009 approach used for Chyulu is a large activity-shifting leakage area comparable in size to the project (about 1.1x forest area), not a ring. Recommendation derived: show 2 km as default and add a sensitivity ring (e.g. up to 10 km and an area-matched belt); this is a design inference, not a source statement.
- Reference regions: VM0009 requires a reference area chosen by the developer (Chyulu: 5-county region of south-eastern Kenya excluding other VCS project areas, PD s6.8.1.2). VM0048 replaces developer choice with jurisdictional/Verra allocation. Independent evidence says reference-area selection bias is the main driver of over-crediting (Swinfield 2026; West 2023, synthetic controls). A synthetic-control or matched-pixel comparison is therefore supported by peer-reviewed practice for independent evaluation. Specific matching variables, ring-vs-synthetic-control accuracy benchmarks: not found.
- Additionality caveat: independent estimates differ between studies and some industry voices dispute the over-crediting findings (per Swinfield summary). Do not report CanopyLedger comparisons as additionality or credit-quantity verification.

---

## 5. Reporting product benchmarks

Found (primary):
- Good-practice for change area from maps: probability sample reference data, error matrix with overall/user's/producer's accuracy, area estimated from the reference sample with CIs. Olofsson et al. 2014, Remote Sensing of Environment 148:42-57, doi 10.1016/j.rse.2014.02.015 (PEER).
- Verra monitoring reports report deforestation hectares with two-sided 90% CI (VM0048). VM0009 monitoring reports (Chyulu) include data/parameter tables with accuracy descriptions and frequency (MRR.87).
- GFW integrated alerts: GLAD-S2 and other optical systems revisit 1-4 days; RADD (Sentinel-1 radar, 10 m) "may take up to 12 days to detect change"; GLAD-L 30 m; confidence classes low/high/highest (highest = two systems agree); "false positives are effectively eliminated in the highest confidence class"; satellite alerts "subject to errors including false alerts". https://globalnaturewatch.org/blog/data-and-tools/integrated-deforestation-alerts (VENDOR/NGO, read directly).
- GFW also says alerts are not recommended for trend or area estimates (from search summary, wording not re-opened). RADD: high-confidence alerts require probability > 97.5% within 90 days; Congo Basin validation ~2% false positives and ~5% false negatives for disturbances > 0.2 ha (WUR page via search summary).
- Global products accuracy: ESA WorldCover 2021 v200 overall accuracy 76.7% (74.4% for 2020 v100), independently validated by Wageningen and IIASA; per-class tree cover and Africa-specific values not retrieved. https://worldcover2021.esa.int (REGULATOR-space agency / validation team).
- Dryland caveats: sample-based pan-tropical studies found nearly twice the gross tree cover loss in Africa (2000-2010) as the Hansen map (omission error); savanna seasonality and mixed tree/grass structure challenge optical tree-cover estimates; GFC tree cover levels in southern African woodland were higher than other estimates (different direction of bias). Sources surfaced: Tyukavina et al. Sci. Adv. 2018 and a southern African woodlands paper (https://www.unccd.int/sites/default/files/library/318_Article_eaat2993.full.pdf ; https://link.springer.com/content/pdf/10.1038/s41467-018-05386-z.pdf) (PEER, read via search summary only).

Not found: ART TREES monitoring report templates or example; published rating-agency site-report templates; MapBiomas or NICFI report templates; funder expectations for alert latency or monthly vs annual cadence. Cadence is therefore an engineering choice constrained by the sensors above (and the VM0009 <= 5-year monitoring period / VM0048 annual AD reporting), not a sourced market norm.

---

## 6. Responsible communication

- ICVCM: CCP label only for credits from approved methodologies; VM0009 not assessed, so VM0009 projects cannot carry it. (see 2.1)
- VCMI Claims Code v2.1 (Aug 2024) renamed "certification standard" to "carbon crediting program" and suggests wording for claims; https://vcmintegrity.org/wp-content/uploads/2024/10/VCMI-Claims-Code-v2.1.pdf (read only via search summary). That governs buyer claims, not an independent monitor, so it is context only.
- A specific source on labelling approximate boundaries or avoiding implied certification: not found. The recommendations below are therefore drafting guidance derived from the standards above (VM0048 requires boundaries as geo-referenced digital maps with accuracy; legacy boundaries as polygon files must be verified), not an external rule.

---

## Recommended targets and report requirements for CanopyLedger

| Requirement | Value | Source | Confidence |
|---|---|---|---|
| Leakage ring minimum width | 2 km minimum (default), with sensitivity ring up to 10 km; cap belt forest area at about the project forest area | VMD0055 v1.1 A1.2.2 | High (text read) |
| Report leakage comparison as indicator, not credit accounting | State legacy VM0009 uses activity-shifting leakage areas of similar size, not rings | VM0009 v3.0 intro; Chyulu PD Table 27 | High |
| Uncertainty reporting | Report area estimates with two-sided 90% CI | VM0048 v1.0 reporting params; ART TREES (secondary) | High (VM0048), Medium (ART) |
| Area estimation method | Probability sample reference data, confusion matrix, area from sample not pixel count, report OA/UA/PA with CIs | Olofsson et al. 2014 | High |
| Flag high uncertainty | Mark estimates with uncertainty > 10% of the area as low-precision; Verra inflates conservatively above 10% | VMD0055 v1.1 eq. 29-30 | High (as Verra's rule; using it as a flag threshold is our choice) |
| Forest/woody definition | Show Kenya definition (15% canopy, 0.5 ha, 2 m height) as the policy reference; label CanopyLedger "woody vegetation" and say it does not equal the legal forest definition | Kenya Nesting Guidelines; Chyulu PD Table 12; VM0048 definition | High |
| Minimum mapping unit / resolution | MMU should match definition area threshold (0.5 ha); imagery 30 m or finer; Verra uses 10 m or finer for monitoring AD interpretation | VMD0055 v1.1 | High |
| Imagery coverage | Verify at least two cloud-free observations for >= 90% of area in each period (VM0009 double-coverage test) | VM0009 v3.0 s6.8.4 | High |
| Image co-registration | Aim at <= 0.4 pixel at 90% CI (Chyulu PD standard) | Chyulu PD PDR.53 | Medium (project-specific) |
| Reporting cadence | Annual headline numbers plus alerts; Verra monitoring periods <= 5 years (VM0009), annual AD (VM0048) | VM0009 v3.0; VMD0055 | Medium (cadence is our design) |
| Alert latency expectation | Optical 1-4 day revisit; radar alerts up to ~12 days; state latency honestly per source; show confidence class | GFW integrated alerts page | High for the cited figures; no market benchmark found |
| Alert use limits | Alerts are signals for verification, not area estimates | GFW guidance (summary) | Medium |
| Do not claim CCP, Verra verification or crediting status | VM0009 projects are outside ICVCM CCP assessment | ICVCM Nov 2024 | High |
| Disclose Kenya context | Nesting guidelines expect alignment with national monitoring (NFMS) and third-party verification by an accredited entity; CanopyLedger is neither | Nesting Guidelines paras 26-29 | High |
| Caveat on baselines | Independent studies find reference-area bias drove over-crediting; avoid claims about credits being over/under-issued | Swinfield 2026; West 2023 | High for the studies; applicability to Kasigau/Chyulu not shown |
| Dryland caveat | State that optical tree-cover change is harder in savanna and omission is likely in small-scale clearing | Tyukavina 2018 and woodland study (summary) | Medium |
| Data-source disclosure | Name each dataset, version, date range, resolution, and known accuracy (e.g. WorldCover 76.7% OA global) | ESA WorldCover | High for the cited number |

## Could not verify

1. Kasigau Phase I/II VM0009 version applied and their leakage area sizes (primary PDs not readable by me; only secondary summaries and IGES figures).
2. Any fixed minimum map-accuracy percentage (e.g. 90%) in VM0009, VM0048 or VMD0055. Not present in the text I searched.
3. VM0048 current buffer percentage and whether VM0048 sets a fixed belt width beyond VMD0055's 2 km minimum.
4. ART TREES v2.0 official text (uncertainty formulas came from a training site).
5. Primary text of Kenya LN 84/2024 (regulation numbers, any MRV format or forest-definition mandate); 2025/2026 amendments; what happened at the two-year transition deadline.
6. Whether Kenya has VM0048-eligible activity data or jurisdictional risk maps; how Chyulu/Kasigau nest.
7. Sylvera and BeZero grades for Chyulu and Kasigau, and BeZero/Sylvera method details; accuracy of Planet, Pachama/Renoster, Carbon Direct, Cumberland.
8. Whether West 2023, Swinfield 2026 or any study evaluates Kasigau or Chyulu specifically.
9. Funder expectations on alert latency and update cadence; example site reports from rating agencies, ART TREES monitoring reports, MapBiomas, NICFI.
10. Guidance on labelling approximate boundaries and avoiding implied certification (no source found).
11. Primary-source details of VCMI Claims Code wording, RADD validation figures and Tyukavina/woodland papers (read via search summaries only).
