# beVisioneers Application: Forest Restoration Monitoring

Nov 10, 2026 · @i want wire frames for my project

## Project summary

**Working name: CanopyLedger Kenya** (change it freely).

CanopyLedger is an independent, satellite-based monitoring tool that shows funders, carbon credit buyers and implementing agencies whether the forests they paid to restore or protect in Kenya are actually growing and staying there. Each funded site is tracked against its pre-funding baseline using Sentinel-1 and Sentinel-2 imagery and machine learning, producing a regular site report: canopy gained, canopy lost, and alerts when a site degrades. The same monitoring data also flags catchments where vegetation loss is raising flood and drought risk, so nearby communities and county planners can act early.

**One-line pitch:** Follow the money to the trees: independent, satellite-verified evidence that funded restoration in Kenya is working.

## Application answers (ready to paste)

Text in \[square brackets\] is for you to fill in or confirm before submitting.

### Category of environmental challenge

Deforestation and land degradation (with climate resilience: floods and droughts).

### Describe the environmental challenge and how your project tackles it

Kenya faces accelerating deforestation and land degradation, which weakens natural buffers against flooding, drought and famine. This damage is often invisible until it is already done, because ground-based monitoring is slow, expensive and cannot cover large or remote areas continuously. The same blind spot makes it hard for city planners to make informed decisions when expanding urban areas near forests, wetlands or watersheds. It also leaves carbon credit markets and restoration funding open to unverifiable or overstated claims, which undermines trust and investment in genuine conservation.

CanopyLedger removes that blind spot with one satellite monitoring system that serves all three needs. It tracks forest cover, vegetation health and water stress every month using free Sentinel-1 radar and Sentinel-2 optical imagery, and machine learning detects clearing, fire, drought die-off and regrowth as they happen. From that single data layer it produces: (1) early warnings for catchments where vegetation loss is raising flood, drought and famine risk, so communities and responders can act before a crisis; (2) ecological sensitivity maps that planners can check before approving development near forests, wetlands or watersheds; and (3) independent site reports for funded restoration and carbon projects, showing canopy gained or lost since funding began and whether deforestation has simply moved next door. The prototype starts with the funded-site reports in one pilot landscape, because that is where a clear user, funders and project developers, already needs the evidence.

### Who benefits, and how many people or communities are you working with or aiming to reach?

- **Funders and carbon credit buyers:** independent evidence that their money produced real, lasting forest.
- **Implementing agencies and community forest associations:** early alerts so they can replant, protect or fix a failing site while it is still recoverable.
- **Downstream communities and county planners:** earlier warning of rising flood and drought risk in degraded catchments.

Pilot target: \[number\] funded restoration sites in \[Mau Forest Complex / chosen county\], covering about \[number\] hectares, with \[number\] partner organisations, in a catchment that supports about \[number\] people. Next step after the pilot: offer site reports to all restoration and carbon projects in the county.

### What have you done to develop or explore this project so far?

I have built and tested the core technical pipeline in a satellite-based vegetation monitoring system for wheat and barley farmland in North East England (225 km², 2020 to 2024). Using Sentinel-2 imagery in Google Earth Engine, I calculated monthly NDVI, EVI and NDWI composites (cloud cover under 15%), trained a SARIMA model on 2020 to 2023 data to forecast 2024 vegetation health, and used z-score anomaly detection to flag stressed pixels. In testing, it correctly picked up drought-related NDVI drops in specific months. I built an interactive Streamlit and Plotly dashboard that classifies land into Healthy, Warning and Alert zones.

What did not work: fixed thresholds (such as NDVI at 0.3) were too rigid across different land types, and a 15% cloud filter would leave large gaps in Kenya's rainy seasons. I am addressing both in the Kenya prototype by adding Sentinel-1 radar (which sees through cloud), training a forest classifier with land-cover-specific thresholds, and replacing crop forecasting with trend-break change detection designed for forests. \[Add: link to the Kenya prototype once it runs, and any conversations with forest associations, KFS or carbon project developers.\]

### Does your project align with a national strategy or policy?

Yes. Kenya's National Programme for Accelerated Forestry and Rangelands Restoration (launched 2022) aims to restore 10.6 million hectares and grow 15 billion trees by 2032, raising tree cover to 30% to reduce the impacts of floods and droughts. Progress has fallen behind \[confirm figure and source: about 1.7 billion trees after four years\], and the lack of monitoring of tree survival is widely cited as a bottleneck. CanopyLedger provides exactly that monitoring. Kenya's Climate Change (Carbon Markets) Regulations, 2024 also require carbon projects to carry out regular monitoring, reporting and third-party verification; CanopyLedger supplies an independent, imagery-based monitoring layer that supports that process.

**Named programmes:** National Programme for Accelerated Forestry and Rangelands Restoration / 15 Billion Trees Initiative (Kenya Forest Service, Ministry of Environment, Climate Change and Forestry); Climate Change (Carbon Markets) Regulations, 2024 (NEMA as Designated National Authority).

### Where do you want to implement your project?

Kenya, starting with a pilot in \[Mau Forest Complex / chosen county\].

### Who you are and your personal connection

I'm Michael Ndegwa, a software engineer from Nairobi, Kenya, specialising in AI/ML and satellite remote sensing. I built a satellite system in the UK that detected crop stress before it was visible on the ground, and it made me ask why we don't watch Kenya's forests the same way. Kenya is spending billions of shillings and planting millions of trees, yet nobody can easily say how many survive. Kenya loses about \[confirm figure and source: 12,000\] hectares of forest a year, \[add one personal example here, such as a flood or drought that affected your home area or family\]. I have the skills to give funders, agencies and communities a clear, honest picture of whether restoration is working, and I want to build it at home.

## Prototype plan

The goal is a working demo you can show in 5 minutes: pick a funded site on a map, see its canopy change since funding started, and get an alert where it is degrading. It reuses most of the UK pipeline (`datacollection.py`, `index_forecast.py`, `map_utils.py`, `dashboard.py`).

### Scope for the demo

- **Pilot area:** one landscape of roughly 200 to 500 km², similar to the UK study. Suggested: part of the Mau Forest Complex (heavy degradation, many restoration projects, well documented).
- **Sites:** 3 to 5 polygons standing in for funded projects. Use real restoration or carbon project boundaries if public (Verra and Gold Standard registries list Kenyan projects), otherwise draw demo polygons and label them as illustrative.
- **Period:** 2017 to present, with a "funding start" date per site as the baseline.

### Data (all free, all in Google Earth Engine)

| Dataset | Used for |
| --- | --- |
| Sentinel-2 L2A (10 m) | NDVI, EVI, NDWI monthly composites, as in the UK project |
| s2cloudless cloud probability | Pixel-level cloud masking instead of the 15% scene filter |
| Sentinel-1 GRD radar | Canopy signal through cloud in the rainy seasons |
| Hansen Global Forest Change | Reference labels for forest loss and validation |
| ESA WorldCover / Dynamic World | Land-cover classes for per-class thresholds |
| CHIRPS rainfall | Separating drought stress from clearing |
| SRTM elevation | Slope for the flood and drought risk layer |
| GEDI L4A biomass (optional) | Rough above-ground biomass per site for the carbon view |

### Build steps

1. **Ingest (adapt `datacollection.py`).** Swap the UK area for the Kenya pilot, replace the scene cloud filter with s2cloudless masking, and add Sentinel-1 VV/VH monthly medians.
2. **Indices (keep).** Same NDVI, EVI and NDWI monthly composites.
3. **Forest classifier (new).** Random forest in GEE on Sentinel-1 + Sentinel-2 bands, trained with labels sampled from Hansen and WorldCover. Output: forest / non-forest map per year. Report accuracy on held-out points.
4. **Change detection (replace SARIMA for forests).** Run CCDC (built into GEE) on NDVI to find the date and size of breaks per pixel. Keep SARIMA plus z-scores for the seasonal stress forecast.
5. **Adaptive alerts (fixes the UK lesson).** Compute anomaly thresholds per land-cover class from each class's own history, instead of a fixed NDVI 0.3.
6. **Site scorecard (new).** For each funded polygon: baseline canopy (ha), current canopy (ha), net change, loss events with dates, and a leakage check on a 2 km buffer around the site.
7. **Risk layer (new, simple).** Flag catchments where forest loss and negative rainfall anomalies coincide on steep slopes. Present it as a risk indicator, not a forecast.
8. **Dashboard (adapt `dashboard.py`).** Rename zones to Stable, Regrowing, Degrading and Cleared, and add the site view below.

### Dashboard screens

- **Portfolio map:** all funded sites coloured by status, with total hectares funded vs hectares of canopy verified.
- **Site report:** before/after imagery slider, canopy-over-time chart from the funding date, list of alerts, leakage ring result, exportable PDF summary.
- **Risk view:** catchments ranked by flood and drought risk indicator.

### Demo script (5 minutes)

1. The problem in one sentence: money goes in, nobody checks the trees.
2. Open the portfolio map: three funded sites, one flagged red.
3. Open the red site: canopy grew after funding, then a clearing event appears in a specific month, with before/after imagery.
4. Show the leakage ring on a green site: no displacement, so the gain is credible.
5. Close with the risk view and the accuracy figure from the classifier.

### Suggested timeline

- **Week 1:** Kenya area, cloud masking, Sentinel-1, indices.
- **Week 2:** Forest classifier and accuracy check.
- **Week 3:** CCDC change detection and adaptive alerts.
- **Week 4:** Site scorecard, leakage ring, risk layer.
- **Week 5:** Dashboard, demo polish, README and screenshots on GitHub.

## Honest limits and submission checklist

State these limits in the application or pitch; reviewers trust a project that knows its edges.

- **Young trees are hard to see.** Seedlings rarely show a clear signal at 10 m resolution for the first few years. Plan simple ground checks (geotagged photos or survival counts by community monitors) for early-stage sites.
- **Monitoring is not certification.** CanopyLedger supports verification; accredited verifiers still certify carbon credits.
- **Carbon credits need more than trees present.** Additionality is outside the tool's scope; leakage (via the buffer ring) and permanence (via long-term tracking) are inside it.
- **The risk layer is an indicator.** It flags rising risk; it does not predict specific floods or famines.

### Before you submit

- [ ] Delete the leftover advice text from the old draft (the "You can attach the report itself" and "One honest note" paragraphs)
- [ ] Replace the IEEE placeholder author names in the UK report with your name
- [ ] Fill every \[square bracket\] in the answers above
- [ ] Confirm the 12,000 ha/year loss and 1.7 billion trees figures, and keep the source links
- [ ] Pick the pilot area and draw the site polygons
- [ ] Push the UK project and the Kenya prototype to github.com/Michaelndegwa1 with a README and screenshots
- [ ] Link the repo (or a short demo video) in the "share your work" field
- [ ] If possible, contact one community forest association or carbon project developer and mention it under "What have you done"
