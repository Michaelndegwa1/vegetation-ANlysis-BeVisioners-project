# Part B: Classification and validation benchmarks (CanopyLedger)

Compiled 2026-11-24 by web research. Reliability labels: PR = peer-reviewed, AG = agency/official, VN = vendor/NGO/secondary web page.
IMPORTANT CAVEAT: the fetch tool was blocked (Anubis/403) on the IIASA-hosted WorldCover validation reports, the Olofsson 2014 PDF, and the Xu et al. 2024 PDF. Where a number below came via a search-result summary rather than the document itself, it is marked "(via search summary)". Items marked "from memory, unverified" were not checked against a source this session. Items not found are marked "not found".

## 1. Accuracy-assessment good practice

- Olofsson, Foody, Herold, Stehman, Woodcock, Wulder (2014), "Good practices for estimating area and assessing accuracy of land change", Remote Sensing of Environment 148:42-57, doi 10.1016/j.rse.2014.02.015. PR. Full text not retrieved (403). Confirmed via search summaries: recommendations cover sampling design, response design, analysis; use probability sampling; report error matrix as area proportions with overall, user's and producer's accuracy; estimate class area from reference labels (not pixel counting); report confidence intervals for accuracy and area; stratified random sampling.
- Sample-size formula (Cochran 1977 stratified), as reproduced by the sits book (https://e-sensing.github.io/sitsbook/val_map.html, VN/secondary, fetched): n = (sum_i W_i S_i / S(O))^2, S_i = sqrt(U_i(1-U_i)), W_i = mapped area proportion of class i, U_i = expected user's accuracy, S(O) = target standard error of overall accuracy. The worked example there assumes U = 0.75 / 0.70 and S(O) = 0.01. The same page quotes Olofsson: "They propose three allocations where 50, 75, and 100 sample units are allocated to the less common classes", with proportional allocation for frequent classes, described as "suggestions". Area estimator A_j = A_tot * sum_i W_i (n_ij / n_i); 95% CI reported.
- Rare-class rule (Springer chapter https://link.springer.com/chapter/10.1007/978-3-030-90998-7_6, via search summary): compute n, allocate, any class with <50 gets 50, recompute; attributed to Olofsson 2014 and Finegold 2016. The "50 per class" rule originates with Hay 1979 / Congalton 1988 (map <500,000 ha, <=12 classes) (via search summary).
- Olofsson (2025), "Accuracy and area estimation", Comprehensive Remote Sensing 2nd ed., NASA NTRS https://ntrs.nasa.gov/api/citations/20250004331/downloads/Olofsson_CRS_2nd_ed.pdf, PR (book chapter). Downloaded and text-extracted: 95% CIs are the standard expression of precision. Sample-size section not located in the extracted text.
- Olofsson et al. 2013 (RSE 129:122-131, "Making better use of accuracy data in land change studies"): not retrieved; cited secondhand by the sits book (error-adjusted areas should come with CIs).
- GFOI Methods and Guidance Document (2014, https://redd.unfccc.int/uploads/2_77_redd_20140218_mgd_report_gfoi.pdf, AG): exists and has accuracy/area-estimation sections; contents not retrieved. Whether GFOI mandates a 90% vs 95% CI: not found.
- Implication for CanopyLedger: 100 hand-labelled points per site is NOT a Cochran-sized stratified sample for area estimation; it is adequate only for a rough overall-accuracy check. Use stratified random points with rare change/loss strata at >=50-100 each and the area-adjusted estimator.

### Wilson 95% intervals (computed, z = 1.96)
Formula: centre = (p + z^2/2n) / (1 + z^2/n); half-width = z * sqrt( p(1-p)/n + z^2/4n^2 ) / (1 + z^2/n); interval = centre +/- half-width.
Worked example n=100, p=0.85: z^2=3.8416; denominator 1.038416; centre = (0.85+0.019208)/1.038416 = 0.8370; half-width = 1.96*sqrt(0.001275+0.0000960)/1.038416 = 0.0703 (approx.); interval 0.767 - 0.907.

| n | observed OA | Wilson 95% low | Wilson 95% high | width | Wald low | Wald high | SE |
|---|---|---|---|---|---|---|---|
| 100 | 0.80 | 0.711 | 0.867 | 0.155 | 0.722 | 0.878 | 0.040 |
| 100 | 0.85 | 0.767 | 0.907 | 0.140 | 0.780 | 0.920 | 0.036 |
| 100 | 0.90 | 0.826 | 0.945 | 0.119 | 0.841 | 0.959 | 0.030 |
| 50 | 0.80 | 0.670 | 0.888 | 0.218 | 0.689 | 0.911 | 0.057 |
| 50 | 0.85 | 0.726 | 0.924 | 0.197 | 0.751 | 0.949 | 0.051 |
| 50 | 0.90 | 0.786 | 0.957 | 0.170 | 0.817 | 0.983 | 0.042 |

Reading: with n=100, an observed 0.85 cannot statistically exclude a true value of 0.77; with n=50 per class, class-level accuracy is known only to about +/-10 points. These are simple-random-sample intervals; stratified/area-weighted estimates and spatial autocorrelation change them. Computed by script, not from a source.

## 2. Reported accuracies of comparable products

| Product | Number | Source / URL / year / reliability |
|---|---|---|
| ESA WorldCover v200 (2021), global OA | 76.7% (v100/2020: ~75%); continental OA range 73-82% (via search summary) | Terrascope summary https://terrascope.be/en/cases/worldcover-worldwide-land-cover-mapping (VN); validation report PVR V2.0 https://pure.iiasa.ac.at/18981/1/WorldCover_PVR_V2.0.pdf (AG, 2022) NOT readable (blocked) |
| WorldCover Africa OA, tree/shrub UA/PA | NOT FOUND (a Digital Earth Africa page shows garbled values 73.6, 76.7, 76.5; not attributable) | https://docs.digitalearthafrica.org/fr/latest/data_specs/ESA_WorldCover_specs.html |
| Comparative validation of 10 m maps (WorldCover, GLAD GLC, Dynamic World, Esri) | OA 73.4% +/-0.7 to 83.8% +/-0.4; WorldCover highest global OA; DW and Esri less spatial detail; per-continent/class values NOT retrieved | Xu, Tsendbazar et al., RSE 2024 https://research.google/pubs/comparative-validation-of-recent-10m-resolution-global-land-cover-maps/ (PR; abstract only) |
| Dynamic World | 72% OA vs 75% Esri on global ground truth; shrub/scrub 47%, grass 34% (averaged across 3 maps, Tundra biome emphasis) | Venter et al. 2022 Remote Sensing 14(16):4101 https://www.mdpi.com/2072-4292/14/16/4101 (PR; via search summary). DW's own paper figure: not checked |
| Hansen GFC annual loss, Sub-Saharan Africa | false-negative rate 48% vs 14-17% other regions; false positives 4% (2001-2014 version, 3,000-pixel tropical sample) | Global Forest Watch blog summarising Tyukavina et al. https://www.globalforestwatch.org/blog/data/how-accurate-is-accurate-enough-examining-the-glad-global-tree-cover-change-data-part-1/ (VN summarising PR; via search summary, page not fetched) |
| Hansen tree cover vs field in southern African woodland | Hansen tree cover "markedly higher" than field-based data (overestimate) | McNicol et al. 2018 Nat. Commun. https://link.springer.com/content/pdf/10.1038/s41467-018-05386-z.pdf (PR; via search summary) |
| Drylands tree cover (visual interpretation of 210,000 0.5 ha plots) | dryland forest 40-47% higher than prior estimates (467 Mha previously unreported) | Bastin et al. 2017 Science https://eprints.whiterose.ac.uk/115833 (PR; via search summary). Shows global products miss dryland trees; not a Hansen accuracy figure |
| JRC Tropical Moist Forests | validated on 6,000 stratified points; UA/PA values NOT retrieved. Humid tropics only, so does not cover Kasigau thicket or Chyulu savanna | Vancutsem et al. 2021 Sci. Adv. 7:eabe1603 (PR); https://earth.esa.int/living-planet-symposium-2022-presentations/25.05.Wednesday/H2-02/0830-1010/06_Bourgoin.pdf |
| Copernicus GLC CGLS-LC100 | Africa discrete map OA 74.6% +/-2.1 (collection unconfirmed); C3 annual maps ~80% OA; Collection 1 Africa 74.3% | via search summary of Tsendbazar et al. papers; https://pure.iiasa.ac.at/18976/1/CGLOPS1_VR_LC100m-V3.0_I1.10.pdf (AG, blocked) |
| S1+S2 woody/non-woody savanna | best OA 86.3% +/-1.5; S1+S2 beat either alone; dry-season-only data limits herbaceous mapping | Borges et al. 2020 Remote Sensing 12(23):3862 https://e-space.mmu.ac.uk/626959/1/Borges_et_al_2020_remotesensing-12-03862-v3.pdf (PR; via search summary) |
| Sahel 10 m woody presence (SVM) | OA 93%; PA woody 71%, PA non-woody 98% | Li, Lyu, Fensholt 2019 (PR; via search summary) |
| S1+S2 RF fractional woody cover, Molopo South Africa | spatial-CV error 12% fractional cover | Lezama Valdes et al. 2019 RSE (PR; via search summary) |
| GEDI L2A RH98 in African savanna | leaf-on, RH98sim<15 m: R2 0.61, bias -0.55 m, RMSE 1.64 m (29.8%); leaf-off RMSE 2.03 m, bias -1.47 m; cannot reliably estimate shrubs <2.34 m | Li et al. 2023 RSE https://www.pure.ed.ac.uk/ws/files/314621473/RSE_D_22_00262_R1.pdf (PR; via search summary) |
| GEDI-derived savanna canopy-height map, Kruger | r 0.51-0.66, RMSE 3.88-4.09 m | Remote Sens. 18(10):1523 (2026) https://www.mdpi.com/2072-4292/18/10/1523 (PR; via search summary, model setups unclear) |
| GEDI biomass in savanna | NOT FOUND | |
| Quantified S2 shrub-vs-grass confusion in African savanna | NOT FOUND (only Venter DW shrub 47% / grass 34% above) | |

## 3. Change-detection benchmarks

- RADD (Sentinel-1), Reiche et al. 2021, Environ. Res. Lett. 16:024005, https://iopscience.iop.org/article/10.1088/1748-9326/abd0a8 (PR, fetched): confirmed alerts >=0.2 ha UA 97.6% +/-4.8, PA 95.0% +/-25.8; PA all sizes 83.5% +/-37.5; minimum mapped size 0.2 ha (20 pixels); alert date within 6-12 days of actual disturbance; core pixels 74% confirmed within 24 d, 95% within 48 d; boundary pixels 53% / 83%; commission errors came from non-forest swamp and savannah (7 of 12 samples) and swamp-forest dynamics. Humid forest only; dry forest was masked out, so NO dry-vs-humid accuracy comparison exists in this paper.
- GFW integrated alerts documentation https://data-api.globalforestwatch.org/dataset/gfw_integrated_alerts (agency/NGO docs, fetched): no numeric precision/recall; combining systems raises PA and lowers UA; "highest confidence" (2+ systems) effectively removes false detections; RADD MMU 0.1 ha in current version; GLAD-L masked to >=10% tree cover in 2000, 30 m resampled to 10 m; RADD coverage is humid primary forest (S. America, sub-Saharan Africa, SE Asia); not for area estimates or trends; cannot separate human vs natural cause. Dry-biome accuracy: not found.
- GLAD-S2 (Amazon comparison, ERL 2024, https://doaj.org/article/a415d09ce4ac4e15b08777badbcbec55, PR, via search summary): GLAD-S2 no false detections, PA 84.88%; radar systems PA ~90%.
- CCDC defaults (Earth Engine docs, via search summary of translated pages; https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_GLOBAL_CCDC_V1, vendor docs): minObservations 6, chiSquareProbability 0.99, minNumOfYearsScaler 1.33.
- CCDC original: Zhu & Woodcock 2014 RSE 144:152-171 (PR; via search summary): 519 Landsat images 1982-2011, one New England scene, land cover OA 90% (16 classes); change detection PA 98%, UA 86% spatial, 80% temporal (secondary source). Change = 3 consecutive anomalous observations (original algorithm). Years of data / observations needed to fit the harmonic model: not verified (from memory, unverified: original paper needs a minimum of about a dozen clear observations for model initialisation).
- CCDC with Sentinel-2, IJAEOG June 2024 (https://doaj.org/article/73b1407733a142fabaaa3cde5f169239, PR, via search summary only; page itself returned 403): omission ~20% at 30-40 day time lag; accuracy improves as the S2 series lengthens. A Wallonia thesis reports weak results (OA 60%, cloudy conditions; low reliability).
- Minimum detectable clearing size: RADD 0.2 ha validated (0.1 ha operational per GFW docs); Landsat-based (GLAD-L, Hansen) half-pixel at 30 m. CCDC on 10 m S2: not found.
- Dry vs humid false-alarm rates for alerts: NOT FOUND.

## 4. Thresholds in practice (REDD+/carbon)

- ART TREES: uncertainty quantified as the half-width of the 90% CI; v1 (Feb 2020) set 15% allowable uncertainty with crediting reduced by the calculated uncertainty; v2.0 moved to a risk-based sliding-scale deduction (via search summaries of https://www.artredd.org/wp-content/uploads/2021/12/TREES-2.0-August-2021-Clean.pdf, AG; not read directly). A tutorial states UNC = (ER + REMV) x UAF with Monte Carlo of >=10,000 iterations (https://seamusrobertmurphy.quarto.pub/redd-uncertainty-training/04-monte-carlo/index.html, VN, low reliability). Activity-data reporting requires user's and producer's accuracy of the classes used.
- Verra VM0007 (v1.8, 2024, https://verra.org/documents/vm0007-redd-methodology-framework-v1-8-clean, AG): a fixed OA threshold NOT found. A Verra page notes dryland-forest accuracy is a known weakness (via search summary).
- GFOI: sample-based area estimation with CIs recommended; fixed OA threshold NOT found. Commonly quoted "85%" or "90%" OA thresholds: not found, treat as unverified.
- Combining uncertainty: propagation (Monte Carlo, IPCC Approach 2) of activity-data and emission-factor errors, then deduct the CI half-width; sampling errors must be included (UK BEIS consultation comment, via search summary).

## 5. Class definitions

- Kenya national forest definition: minimum 0.5 ha, >=15% canopy cover, trees >=2 m height (CIFOR-ICRAF WP 24, https://cifor-icraf.org/publications/pdf_files/WPapers/CIFOR-ICRAF-WP-24.pdf, citing Ministry of Environment and Forestry 2020; JICA REDD+ report https://openjicareport.jica.go.jp/pdf/12364006_05.pdf; both via search summary, not read in full).
- FAO FRA: forest >0.5 ha, trees >5 m, canopy >10% (or able to reach in situ), excludes predominantly agricultural/urban use; Other Wooded Land = 5-10% canopy of trees >5 m, or >10% when shrubs/bushes included (FAO pages via search summary, https://www.fao.org/4/y2328e/y2328e25.htm; FRA 2020 terms https://fra-data.fao.org/definitions/fra/2020/en/tad). FRA 2025 wording not checked.
- Kenya's FRA 2010 country report used 10% canopy and 5 m, while national/UNFCCC use 15% and 2 m (JICA). So shrubland/thicket (typically 2-5 m) can meet Kenya's 2 m rule but fails FAO's 5 m rule. Kenya Forest Service: forest cover 5.9% (2018) to 8.83% (2021); tree cover 12.13% in 2022 (CIFOR-ICRAF WP, via search summary). Forest Conservation and Management Act 2016 text and NFRA class list: NOT retrieved; confirm before fixing class thresholds.
- Implication: decide whether "woody vegetation" (any woody >=2 m) is mapped, and report a Kenya-definition forest layer (>=15% cover, >=0.5 ha, >=2 m) as a derived product. Chyulu montane forest meets both definitions; Kasigau thicket depends on the 2 m vs 5 m height rule.

## 6. Pseudo-labels from a global map and temporal transfer

- No study found that measures accuracy loss when training on WorldCover pseudo-labels and applying the model to other years. NOT FOUND.
- Related (via search summaries, low specificity): naive temporal transfer vs a domain-adaptation method gave a 21-40% gap for invasive tree mapping (arXiv, not WorldCover); a noisy-label paper reports up to 6.45% accuracy difference between training with year-matched vs another year's labels (Remote Sensing 13(21):4194, https://api.crossref.org/works/10.3390%2FRS13214194); a 2025 review quotes 15-25% loss when Sentinel-2 models move region/period (original source unverified; hint only).
- Implication: pseudo-labels from WorldCover (about 75-77% OA globally) cap achievable accuracy; use for weak supervision only and measure against human points per site and per year.

## 7. Recommended targets for CanopyLedger classification and change detection

Only values found in sources above. "Confidence" = confidence the value is correctly sourced and transferable.

| Metric | Target | Source | Confidence |
|---|---|---|---|
| Overall accuracy, woody vs non-woody, per site | >= 0.85 with Wilson 95% interval reported (n=100 gives lower bound 0.77) | Borges 2020 best 86.3%; WorldCover 76.7% as global floor; Wilson computation here | Medium (peer benchmark comparison; no standard mandates it) |
| Multi-class (tree/shrub/grass) OA | >= 0.77 (beat WorldCover global 76.7%) | WorldCover v200 via Terrascope | Medium |
| Woody-class producer's accuracy | >= 0.71 (Sahel SVM baseline), aim higher | Li, Lyu, Fensholt 2019 | Low-Medium |
| Sample per stratum for area estimation | >= 50, ideally 75-100 for rare strata; stratified random, area-adjusted estimator, 95% CI | Olofsson 2014 as quoted by sits book | Medium (secondary quote) |
| Expected user's accuracy for sample design | 0.70-0.75 | sits book example | Low (illustrative) |
| Change alert precision, events >= 0.2 ha | UA ~0.976 (humid benchmark) | Reiche 2021 | Medium humid; Low for dry savanna |
| Change alert minimum validated size | 0.2 ha | Reiche 2021 | High (RADD only) |
| Alert detection delay | confirm within 24-48 days (74-95% of core pixels) | Reiche 2021 | Medium |
| CCDC omission and delay (Sentinel-2) | omission ~20% at 30-40 d lag as the reference to match | IJAEOG 2024 via search summary | Low-Medium |
| CCDC starting parameters | minObservations 6, chi2 0.99, minNumOfYearsScaler 1.33 | EE docs via search summary | Medium |
| Uncertainty reporting | 90% CI half-width, Monte Carlo propagation, conservative deduction | ART TREES via search summaries | Medium |
| Allowable activity-data uncertainty | 15% at 90% CI (TREES v1 only; v2.0 uses sliding scale) | ART TREES v1 via search summary | Low |
| Forest definition layer | >=15% canopy, >=0.5 ha, >=2 m (Kenya); FAO 10%/5 m as sensitivity | CIFOR-ICRAF WP 24, JICA | Medium |

## 8. Items not verified / not found
- WorldCover v200 per-class UA/PA (tree cover, shrubland, grassland) and Africa/Kenya OA; the PVR PDF was blocked.
- Dynamic World own-paper OA and class accuracies; Hansen tree-cover (not loss) dryland accuracy; JRC TMF UA/PA values; Copernicus LC100 shrub accuracy for Africa.
- Olofsson 2014 and 2013 primary text (sample-size section, exact UA assumptions, 50-100 phrasing); GFOI MGD CI-level requirement.
- Verra VM0007 / ART TREES v2.0 fixed accuracy thresholds; the 15% figure is from v1 via summary only.
- CCDC: minimum observations/years for harmonic fits and effect of observation density in numbers; Zhu 2014 omission/commission; CCDC accuracy in Kenyan drylands.
- Alert false-alarm and recall rates in dry biomes; GFW integrated-alerts numeric precision/recall.
- GEDI biomass validation in savanna; quantified S2 shrub-vs-grass confusion in East African savanna.
- Documented accuracy loss for WorldCover pseudo-label training and year-to-year transfer.
- Kenya Forest Conservation and Management Act 2016 definitions; Kenya NFRA class definitions.
- Every claim marked "via search summary" was relayed by the search tool, not read from the document.
