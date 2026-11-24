# Notes on legacy_uk/dashboard.py

Source: `legacy_uk/dashboard.py`, 1,020 lines, read in full. Line numbers refer to that file. Nothing was executed and nothing in `legacy_uk` was modified.
Items marked **(unverified)** are inferences. They were not tested by running the code or by checking data files.

## 1. Structure

Single script, Streamlit + Plotly + pydeck. One class, one `main()`, no other functions.

| Lines | Item |
|---|---|
| 1-16 | Imports. `pandas` is imported twice (lines 2 and 14). `warnings.filterwarnings('ignore')` is set at line 16. |
| 19-24 | `st.set_page_config`, title "Farm Vegetation Monitor - DSR Approach", wide layout. |
| 27-88 | Custom CSS: `.farm-header`, `.status-healthy/warning/alert/critical`, `.metric-card`, `.dsr-section`. |
| 90-91 | Late imports of `statsmodels.api as sm` and `prophet.Prophet`. They are hard imports, so if either is missing the whole app fails at import. |
| 93-305 | `class EnhancedVegetationAnalyzer` |
| 94-113 | `__init__`: hardcoded `farm_location`, `crop_info`, empty `crop_thresholds`. |
| 115-136 | `compute_percentile_thresholds(ndvi_data, crop_type)` |
| 138-155 | `analyze_vegetation_health(ndvi_value, crop_type)` returns (label, emoji). |
| 157-186 | `calculate_z_score_anomalies(df, window_size=12)` |
| 188-236 | `fit_simple_forecast(ts_data, periods=12)`: linear regression plus a fixed sine wave. |
| 238-250 | `calculate_model_metrics`: MAE, RMSE, sMAPE. **Never called.** |
| 252-305 | `load_actual_data()` |
| 307-1017 | `main()` |
| 1019-1020 | `if __name__ == "__main__": main()` |

### main() flow
- 308: DSR banner.
- 314-323: sidebar farm info.
- 326-347: load data. The dataset is `processed_data` if present, otherwise `pixel_time_series`.
- 350-361: drop rows with a bad date, then derive `crop_type` and `area_id` if those columns are missing.
- 364-366: compute thresholds per crop.
- 369-388: crop selectbox, area multiselect, and `filtered_df`.
- 395-422: latest-per-area row, current NDVI/EVI/NDWI, and status.
- 425-440: header with the status badge.
- 443-450: `st.tabs`.
- 1005-1017: footer.

### The 6 tabs (443-450)
1. **Overview** (452-548).
   - Four metric cards: NDVI with status, EVI, NDWI, and the crop's thresholds.
   - A line chart of mean NDVI per date with 3 hlines for the thresholds.
   - A bar chart "Health Distribution by Area", coloured by Health class.
2. **Model Forecast** (550-614).
   - Uses `fit_simple_forecast` on `daily_avg`.
   - Plots history, forecast, a fixed +/-0.1 band, and the threshold lines.
   - Shows the mean forecast.
3. **Alerts & Actions** (616-718).
   - Three `st.metric`s (NDVI, EVI, NDWI).
   - A recommendation block by status, with hardcoded irrigation and pest advice (652-691).
   - Per-area expanders with NDVI/EVI/NDWI. For Alert/Critical areas, an NDWI-based message (712-718).
4. **Spatial Analysis** (720-811).
   - Farm details text and a crop summary table.
   - A line chart per area with thresholds.
   - A "Point ID" explainer.
   - A pydeck satellite map of points from a hardcoded CSV (778-811).
5. **Z-Score Anomalies** (813-883).
   - Explainer text, 3 metrics, and a scatter (date vs NDVI, coloured by z).
   - A table of anomalies in the last 90 days.
6. **Model Comparison** (886-1003).
   - Prophet vs ARIMA on monthly mean NDVI: metrics table, CI width, forecast comparison chart, raw monthly table.
   - Then thresholds dump, location dump and DSR documentation text.

## 2. Inputs

### Files (relative to the working directory, not to the script; 257-263)
- `data/time_series/pixel_time_series.csv` (loaded 266).
- `data/time_series/spatial_statistics.csv` (loaded 277). Never used after loading.
- `data/processed/processed_vegetation_data.csv` (loaded 287). Preferred main dataset (339).
- `data/time_series/analysis_summary.json` (loaded 297). Never used after loading.
- `data/processed/data_inventory.csv` is listed in `file_paths` but never loaded.
- **Hardcoded absolute path at 778:** `E:\vegitation analysis\data\all_index_coordinates.csv`. It is read outside any try/except and outside the loader.

### Columns relied on
- Main df: `date`, `point_id`, `ndvi`. Optional: `crop_type`, `area_id`, `evi`, `ndwi`.
  - `point_id` must be numeric (355, 360).
  - `date` is parsed with `errors='coerce'` (270 etc.).
  - Lines 406-407 and 700-701 guard `evi`/`ndwi` with `if 'evi' in columns`, but the groupby at 500-504 does not, so it raises KeyError when they are missing.
- Coordinates CSV (778-810): `crop_type`, `latitude`, `longitude`. The tooltip references `{value}` (810). Whether a `value` column exists is **(unverified)**.

### Hardcoded values
- Farm (96-103): "North East England Farm", Northumberland, lat 55.0054, lon -1.6816, `area_km2` 10, 4-corner bbox [-1.7516..-1.6116, 54.9604..55.0504].
- `crop_info` (107-110): wheat = Area_1, Area_2; barley = Area_3, Area_4, Area_5. It is never read.
- Crop assignment (354-356): `point_id < 55` is wheat, otherwise barley.
- Area assignment (359-361): `Area_{min(point_id//22 + 1, 5)}`.
- Footer text names Sentinel-2 `COPERNICUS/S2_SR_HARMONIZED` (1009).
- Map style `mapbox://styles/mapbox/satellite-streets-v12` (793). It needs a Mapbox token; whether one is configured is **(unverified)**.

### Session state
There is **no `st.session_state` and no `st.cache_data` / `st.cache_resource`**. Everything reloads and recomputes on every rerun. The widgets are:
- sidebar `selectbox` (370),
- sidebar `multiselect` (374),
- an unkeyed `selectbox` inside tab 4 (784).

## 3. Models and analysis

### Zone classification (thresholds are data-derived, not fixed)
- `compute_percentile_thresholds` (115-136) takes valid NDVI in [-1, 1] and returns:
  - alert = P10,
  - warning = P25,
  - healthy = P75 (percentiles over all dates and points of that crop).
- Fallback defaults {healthy 0.6, warning 0.3, alert 0.1} are used when the data is empty (118, 123) or the crop is missing from the dict (142).
- Classification (148-155 and duplicated inline at 411-422):
  - NDVI >= healthy: **Healthy**
  - NDVI >= warning: **Warning**
  - NDVI >= alert: **Alert**
  - below alert: **Critical** (a 4th class, with red colouring).
  - `analyze_vegetation_health` also returns "No Data" for NaN. The inline version at 411-422 has no NaN branch, so NaN falls through to Critical.
- The thresholds are relative to the crop's own history, not agronomic absolutes. By construction about 25% of observations always sit below "Warning" and about 10% below "Critical".
- Heading at 987 says "10th Percentile Based", which is only partly true (P10, P25 and P75 are all used).

### Z-score anomalies (157-186)
- Per `point_id`, sorted by date.
- Centered rolling mean and std over `window_size` observations, not a time window. The default is 12 but the call at 828 passes 6.
- Anomaly if |z| > 2.5 (175).
- Points with a NaN z-score get z = 0 and is_anomaly = False.
- Points with fewer observations than the window are skipped.
- The tab only runs if `len(filtered_df) > 50` (826).

### Forecasting
- Tab 2, `fit_simple_forecast` (188-236):
  - Plain `LinearRegression` on the datetime as int64.
  - Plus a fixed `0.1*sin(2*pi*k/12)`, clipped to [-1, 1].
  - "CI" is yhat +/- 0.1, a constant.
  - It is labelled "95% Confidence Interval" (586), which is not true. It is not statistical.
- Tab 6 (904-956):
  - Prophet(yearly_seasonality=True), 12 monthly periods.
  - `sm.tsa.ARIMA(order=(1,1,1), seasonal_order=(1,1,1,12))`.
  - Metrics are MAE, RMSE and sMAPE, plus the mean CI width.
  - The "quality thresholds" (944-949) are static text only, not computed.

### Other hardcoded cut-offs
- NDVI "trend arrow" at >0.5 / <0.3 (627), unrelated to the crop thresholds.
- NDWI water status at +/-0.2 (642).
- Area diagnosis at +/-0.3 (713, 715).
- Alert-level advice text, for example "increase water by 50%" (652-691).

## 4. Reuse for the Kenya forest-carbon monitoring dashboard

These are suggestions, not facts about the file.

### Ideas worth keeping
- **Layout:** header with a status badge, a metric-card row, and a tab structure (Overview / Forecast / Alerts / Spatial / Anomalies). CSS blocks at 27-88 are reusable.
- **Portfolio map:** the pydeck pattern at 792-811. Swap `ScatterplotLayer` for a `GeoJsonLayer` of site polygons coloured by status. Use a token-free basemap.
- **Site report:** the per-area expander (696-718) maps to a per-site card with a latest-index summary.
- **Canopy-over-time:** the line chart with threshold hlines (509-520, 752-762), with `daily_avg` and `area_comparison` as templates.
- **Alerts:** status-to-message mapping (652-691) and the NDWI sub-diagnosis.
- **Anomalies:** rolling z-score. Convert it to a time-based window against a seasonal baseline.
- **Model comparison:** the Prophet vs ARIMA scaffolding in tab 6, once fixed (see section 5).

### Must be rewritten
- Data layer: paths, loader (no caching) and column schema. Drop `point_id` arithmetic for crop/area; use site IDs and polygons.
- Crop/farm logic: `crop_info`, wheat/barley, `farm_location`, and the DSR and irrigation text.
- Thresholds: percentile-of-own-history needs an explicit baseline or reference definition for forests.
- Export: **there is none** (no `download_button` found). Needs to be built.
- The monthly resampling in tab 6.
- Forecast uncertainty, the validation split, and the map credentials and path.
- Caching, and error handling around the model fits.

## 5. Bugs, dead code, inconsistencies

### Likely to break
1. **778:** hardcoded `E:\...` CSV is read with no existence check. If it is missing, the exception aborts the script at that point inside tab 4. Tabs 5 and 6 and the footer will not render. **(unverified in practice)**
2. **784/787 shadow variables:** `df`, `selected_crop` and **`filtered_df` are overwritten** with the coordinates data. Tab 5 (826-828) then runs on that frame, not on the NDVI frame. Whether the coordinates CSV has `ndvi`/`point_id`/`date` is **(unverified)**; if it does not, the tab raises a KeyError.
3. **Tab 6 resampling (895-898):** `asfreq('M')` only keeps rows whose date is exactly a month-end. A Sentinel-style per-date series is therefore mostly NaN. `resample('M').mean()` was probably intended.
   - If NaN leads the series, Prophet/sklearn can fail.
   - Prophet and ARIMA have no try/except.
   - ARIMA with a seasonal order of 12 on a short series can fail or give junk.
4. **Gate mismatch in tab 2:** the gate is `len(daily_avg) > 6` (554), but `fit_simple_forecast` needs >= 12 rows (192). It then silently returns None and shows "Unable to generate forecast". The warning text "at least 6 months" is also wrong, because `daily_avg` is per date, not per month.
5. **Line 500:** the groupby requires `evi` and `ndwi`, so it is a KeyError when they are missing, unlike the guards at 406-407.
6. **Deprecated or removed pandas APIs:**
   - `freq='M'` (211, 897, 908) is deprecated in pandas 2.2 (to 'ME').
   - `fillna(method='ffill')` (898) is deprecated in 2.1.
   - `.astype(int)` on datetimes (199) and `future_dates.astype('int64')` (212) assume nanosecond units.
   - The impact on the installed pandas version is **(unverified)**.

### Logic and inconsistency
- **In-sample "validation" (926-931):** Prophet and ARIMA are fit on the full series, then scored on the last 12 months, which they have already seen. The "last 12 months" metrics are in-sample, not a hold-out. The ARIMA predict is also in-sample.
- **"Latest" is a single point:** `latest_data` (395) takes `idxmax` of date per area, so one row per area. `current_ndvi` is the mean of those single points, not a field or area mean. The latest date may differ per area.
- **Seasonality ignored in status:** status uses the latest date's NDVI against whole-season percentiles. A harvested or bare-soil date will read as Critical or Alert.
- **Unfair "recent anomalies":** the table uses `datetime.now() - 90 days` (869). For historical data it will always say "no recent anomalies". Tab 3 is titled "Real-time", but the data is historic.
- **Crop/area mapping contradiction:**
  - Points 44-54 get Area_3 and wheat; points 55-65 also get Area_3 but barley (354-361). So Area_3 mixes crops.
  - This contradicts `crop_info` (107-110), where wheat is Area_1-2 and barley is Area_3-5.
  - Applies only when `crop_type`/`area_id` columns are absent.
- **Forecast label:** "95% Confidence Interval" is a fixed +/-0.1 band (225-230, 586). The sine seasonality is anchored to the horizon index, not the calendar month.
- **Footer (1013)** says "Models: Trend + Seasonal", but tab 6 uses Prophet/ARIMA.
- **Alert colour:** the NDVI card colour (460) makes both Alert and Critical red; the badge CSS has distinct classes.
- **Tab 6 docs:** the "Enhanced DSR Documentation" block (994-1003) and the thresholds/location dumps are inside the `else:` branch (indented under it). They disappear if data is insufficient.
- **Coordinates display:** longitude -1.6816 is printed with `:.4f` plus "W" (321, 733), giving "-1.6816 W".
- **Farm area:** `area_km2 = 10`, but the bbox in 102-103 is about 0.14 deg x 0.09 deg. That is roughly 8.9 km x 10 km, about 89 km2 by my own estimate.
- **Per-run cost:** Streamlit executes all tab bodies on every rerun, so Prophet, ARIMA and z-scores run every time. There is no caching. The z-score loop uses `iterrows` (177).

### Dead code and unused
- Imports: `make_subplots`, `stats`, `StandardScaler`, the second `pandas`, and `datetime`/`timedelta` partly. I did not run a linter.
- Methods and data: `calculate_model_metrics` (238-250), `crop_info`, `farm_location['coordinates']`, the `spatial_stats` / `analysis_summary` / `data_inventory` datasets, and the `ndvi_std` column.
- Stale comments at 774-780 (a paste note: "Add this to your dashboard.py ...").

### Mojibake
Every emoji and symbol in the file displays garbled in the read output (for example the page icon at line 21 and the degree sign at 321). Visible garbling appears at lines 21, 147-155, 272-303, 308, 321-322, 428-1017 and others.
- It looks like UTF-8 bytes re-saved as Windows-1252.
- Whether the bytes on disk are really garbled, or only the viewer, is **(unverified)**; I did not inspect raw bytes.
- If real, the page icon, the status emoji, tab titles and the degree and squared signs all render as junk.
