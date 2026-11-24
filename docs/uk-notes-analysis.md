# legacy_uk analysis (read-only mapping)

Scope: fully read `vegetation analyss.py` (VA), `data manager.py` (DM), `crop,veg.py` (CV), `data diagonistic.py` (DD), `coodinates.py` (CO), `indicesextraction.py` (IE), `README.md`. For claim verification I also grepped and partly read `dashboard.py` (DASH, 1019 lines; only lines 94-240 and 896-935 read, rest grep only), `data colecetion.py` (COL, lines 1-194 read) and `dataprocesing.py` (DP, grep plus header only). Nothing in legacy_uk was modified. Nothing was executed. Anything marked (unverified) is inference.

## 1. Classes, functions, I/O, hardcoded names

Upstream chain (from code): COL (Google Earth Engine) -> Drive GeoTIFFs -> DM -> VA -> CV / DASH.

### COL `data colecetion.py` (script, no functions besides `apply_scale_factors` L50, `calculate_indices` L63)
- GEE project id hardcoded L8/L14. AOI polygon L18-25: lon -1.7516..-1.6116, lat 54.9604..55.0504 (labelled "Placeholder ... 10km square").
- Collection `COPERNICUS/S2_SR_HARMONIZED` L44, 2020-01-01 to 2024-12-31 (L35-39), `CLOUDY_PIXEL_PERCENTAGE < 15` L47. Bands B2,B3,B4,B8 scaled x0.0001 (L51).
- Indices (L63-88): NDVI=(B8-B4)/(B8+B4); EVI=2.5*(NIR-RED)/(NIR+6*RED-7.5*BLUE+1) (L=1, correct); NDWI McFeeters=(B3-B8)/(B3+B8) (green minus NIR).
- Monthly median composite per month (L96-118), skipped if no images. Export L142-158: bands NDVI,EVI,NDWI (this order = band 1,2,3), scale=10, crs `EPSG:27700`, Drive folder `vegetation_analysis_2020_2024_full_data`, name `NE_England_S2_Indices_{YYYY}_{MM}_{MonthName}`.
- No SCL/QA60 pixel-level cloud mask, only scene-level filter. No per-crop or per-field geometry.

### DM `data manager.py` class `VegetationDataManager(data_dir="data")` (L10)
- Dirs (relative to cwd): `data/raw_geotiffs`, `data/processed`, `data/time_series` (L13-16, created L19).
- `organize_downloaded_files(download_folder)` L27: copies *.tif/*.tiff into `raw_geotiffs/<year>/`; year = first 4-digit token starting "20" (L58).
- `scan_available_data()` L79: `raw_dir.rglob("*.tif")`, writes `data/processed/data_inventory.csv`, columns: filename, path, year, month, month_name, size_mb, full_path (L109-117). Filename pattern parsed: year token, then month int, then month name (L97-104).
- `test_read_geotiff()` L146 (prints bands, assumes band1 NDVI, band2 EVI, band3 NDWI), `create_quick_visualization()` L191 (masks |NDVI|>1, vmin -0.5 vmax 1.0, saves `processed/sample_ndvi_visualization.png`), `main()` L221 uses `input()`.

### VA `vegetation analyss.py` class `VegetationTimeSeriesAnalyzer(data_manager)` (L15)
- Needs `data_manager.processed_dir`, `.timeseries_dir`.
- `extract_pixel_time_series(sample_points=None, grid_size=10)` L40: reads `processed/data_inventory.csv`, sorts by year,month; grid of grid_size^2 pixels between 10% and 90% of width/height (L69-71); reads band 1/2/3 as ndvi/evi/ndwi (L82-84); date = 15th of month (L87); output `time_series/pixel_time_series.csv` columns: date, year, month, month_name, point_id, pixel_x, pixel_y, ndvi, evi, ndwi.
- `calculate_spatial_statistics()` L128: per date mean/median/std/min/max/q25/q75 for each index plus pixel_count -> `time_series/spatial_statistics.csv`.
- `detect_anomalies_and_trends(window_size=5)` L174: per index on monthly spatial mean; Savitzky-Golay(window 5, poly 2) L203, residual = value - smooth, z-score of residuals `abs(stats.zscore(residuals))`, anomaly if z > 2.0 (L209-210, 231), linear regression on integer index (L213-214; slope is per month step) -> `time_series/anomaly_detections.csv` (date,index,value,smoothed_value,residual,z_score,is_anomaly,trend_slope,trend_r2,trend_p_value,health_status).
- `assess_vegetation_health(value, type)` L247, `diagnose_vegetation_problems()` L259 (rule-based, see section 2), `create_analysis_summary()` L310 -> `time_series/analysis_summary.json`, `visualize_time_series()` L357 -> `vegetation_time_series_analysis.png` (title "North East England" L365), `run_time_series_analysis()` L442 (grid_size=15, L455).

### CV `crop,veg.py`
- `classify_vegetation(value, crop_type)` L4, `compute_crop_thresholds(pixel_df, crop_type)` L23, `process_vegetation_health` L38, `save_processed_data` L55, `main` L63.
- Reads `data/time_series/pixel_time_series.csv` (L65); forces `crop_type='wheat'` for every row (L69); writes `processed_vegetation_data.csv` in cwd (L55 default), adds column `status`.

### DD `data diagonistic.py` `diagnose_data_structure("data")` L5
- Checks existence/columns of: `data/processed/data_inventory.csv`, `data/time_series/pixel_time_series.csv`, `data/time_series/spatial_statistics.csv`, `data/time_series/analysis_summary.json`, `data/processed/processed_vegetation_data.csv` (L25-31). Looks for indices ndvi, evi, ndwi, savi, ndre (L56).

### CO `coodinates.py` (script)
- In: `E:\vegitation analysis\data\raw_geotiffs` (L6) recursive. Out: `E:\vegitation analysis\data\all_index_coordinates.csv` (L7), columns longitude, latitude, value, source. Uses band 1 only, all non-nodata pixels of all files.

### IE `indicesextraction.py` (script)
- In: single file `E:\vegitation analysis\data\raw_geotiffs\2020\NE_England_S2_Indices_2020_01_January.tif` (L6). Out (same folder): `_NDVI.tif`, `_EVI.tif`, `_NDWI.tif`, `_indices_sample.csv` (cols row,col,lon,lat,ndvi,evi,ndwi). Masks nodata, rescales EVI /100 if max|EVI|>5 (L26-27), clips EVI to [-1,1], samples up to N=50000 pixels, seed 42 (L43-47).

## 2. Thresholds and models (exact values, and where they differ)

NDVI health classes
| Where | healthy | warning | alert | notes |
|---|---|---|---|---|
| VA L23-27 | 0.6 | 0.4 | 0.2 | classifier L247 uses only healthy/warning (>=); 0.2 only used as plot line L378. Comment L26 says "<=0.4 = alert" |
| CV L8-13 wheat | 0.75 | 0.5 | 0.2 | strict `>` (L16-18); barley 0.65/0.4/0.15; default 0.7/0.45/0.2; Alert is anything below warning (alert value never used) |
| CV L31-34 percentile | p10+0.15 (wheat) / +0.10 (barley) | p10+0.05 / +0.03 | p10-0.10 / -0.15 | computed and printed only, never used for classification (L45 calls hardcoded classify) |
| DASH L115-136 | p75 | p25 | p10 | percentiles of data, fallback 0.6/0.3/0.1 (L118,123,142); 4 classes incl. Critical (L148-155) |
| VA EVI L29-33 | 0.4 | 0.25 | 0.15 | EVI only |

Rule-based diagnosis, VA L280-301 (uses trend slope per month step and latest monthly spatial mean)
- Drought: NDVI < 0.3 and NDWI < -0.1 and slope < -0.001 (L280).
- Waterlogging: NDWI > 0.3 and NDVI < 0.4 (L286).
- Disease/pest: slope < -0.002 and NDVI < 0.5 (L292).
- else "Normal Seasonal Variation".
DASH L713/715 uses area NDWI < -0.3 / > 0.3; DASH L627 trend arrow: NDVI > 0.5 up, < 0.3 down.

Anomaly detection
- VA L203-231: SavGol(5,2) residuals, global z-score of residuals, |z| > 2.0, on monthly spatial mean (per index).
- DASH L157-175: per sample point, centered rolling mean/std window 12 (default; called with window_size=6 at L828), z = (ndvi - rollmean)/rollstd, |z| > 2.5. So 2.0 vs 2.5 and different method.

Forecast models (all in DASH only, none in the six requested files)
- Prophet(yearly_seasonality=True), 12 monthly periods (L906-909) fit on whole series.
- `sm.tsa.ARIMA(order=(1,1,1), seasonal_order=(1,1,1,12))` (L912), i.e. SARIMA(1,1,1)(1,1,1,12), fit on whole series, `get_forecast(steps=12)` (L914). Series: monthly mean NDVI, `asfreq('M')`, `fillna(method='ffill')` (L897-898).
- Validation L925-931: last 12 months, but both models were fit on all data, so this is in-sample, not a holdout. Metrics MAE, RMSE, sMAPE.
- `fit_simple_forecast` L188: LinearRegression on date + 0.1*sin seasonal, +/-0.1 fixed band (L218-229). Used in the "Model Forecast" tab (L557) as the "simple" forecast.

Other: percentile thresholds p10/p25/p75; NDWI formula differs (see bugs).

## 3. Reuse for Kenya forest-carbon pipeline

Reusable ideas (re-implement, do not import)
- Per-site monthly time-series table (date, site, index) built from monthly median composites; spatial summary stats per date (VA L128-172).
- Smooth-then-residual anomaly detection with z-score (VA L203-210), and per-site rolling z-score (DASH L157). Better: seasonal-aware baseline (same-month climatology or STL) because forests/crops are seasonal.
- Linear trend with slope, R2, p-value (VA L214); Mann-Kendall/Theil-Sen would be more robust (suggestion).
- Percentile-derived (p10/p25/p75) thresholds computed from the site's own data rather than fixed cutoffs (CV L23, DASH L115), if validated against forest NDVI/EVI behaviour.
- Data inventory/QA pattern (DM L79; DD checklist).
- GEE export recipe (COL): harmonised S2 SR, scene cloud filter, monthly median, 10 m export. Add SCL pixel masking.
- Model comparison harness idea (Prophet vs SARIMA, MAE/RMSE/sMAPE) but with a true train/test split.

Must be rewritten
- All hardcoded paths (`E:\vegitation analysis`, cwd-relative `data`), GEE project id, filename-based date parsing, space/comma file names.
- Crop logic (wheat/barley thresholds, forced `crop_type='wheat'`, farm geometry, "Area_1..5" with no geometry), fixed NDVI health bands (crop values are not valid for forest; forest NDVI is high and saturates, so EVI/NDMI/other indices would matter - suggestion).
- Drought/flood/disease rules in VA L280-301 (crop-specific, NDWI sign assumptions, slope units per month).
- Pixel grid sampling (fixed 10%-90% grid) replaced by site/polygon zonal statistics.
- Coordinates/lon-lat export (CRS bug), EVI scale fix hack.
- Forecasting: refit with explicit train/test windows; the dashboard is Streamlit-specific.
- Carbon-specific parts (biomass/allometry, baseline, additionality) do not exist in legacy code at all.

## 4. Bugs and inconsistencies

1. CO L27-31 and IE L52-60: `xy()` returns coordinates in the raster CRS, which COL exports as EPSG:27700 (L156), so columns named longitude/latitude/lon/lat hold British National Grid easting/northing in metres, not degrees. (Inferred from COL CRS; actual TIFF CRS not inspected.)
2. IE writes `*_NDVI.tif`, `*_EVI.tif`, `*_NDWI.tif`, `_indices_sample.csv` into `raw_geotiffs/2020/`. DM L87 `rglob("*.tif")` would then inventory those single-band derivatives as duplicate months (month_name parsed from the same tokens), and VA L83-84 `src.read(2)`/`read(3)` would fail on them (caught by try/except L111, silently skipped with a print).
3. CO L22: `band != src.nodata`; if nodata is None or NaN, every pixel passes (NaN != x is True), so NaN pixels are exported. No masking applied in VA L82-97 beyond NaN check, so a numeric nodata value would flow into statistics (unverified what nodata the GEE export has).
4. EVI inconsistency: COL L72-75 correct with L=1; DP L10 uses L=10000 (README also flags it); IE L26 assumes a x100 scale error in the file. Whether the exported EVI is scaled x100 was not verified; COL code does not scale it.
5. NDWI: COL L86 McFeeters (green - NIR); DP L13 reverses sign (NIR - green). VA L280 drought rule `NDWI < -0.1` is nearly always true for vegetated pixels under McFeeters (inference), and DASH L713-715 use +/-0.3.
6. Thresholds inconsistent across VA, CV, DASH (section 2). VA comment L26 contradicts classifier (0.2 unused). CV uses `>`, VA `>=`. CV `compute_crop_thresholds` result unused (L42 vs L45); CV L31-36 has no else, so any crop_type other than wheat/barley raises UnboundLocalError at L36.
7. CV L55 writes `processed_vegetation_data.csv` in cwd, but DD L30 expects it in `data/processed/`.
8. VA anomaly z-score is computed on the whole series including the anomalies (L209), uses annual-cycle-blind SavGol(5) which tracks real seasonal peaks; `health_status` stored only for the last row (L235). Trend slope is per month index (L213) but diagnosis thresholds (-0.001, -0.002) are unlabelled and the series has gaps (skipped empty months in COL L117), so index spacing is not time-uniform.
9. VA L87 `datetime(row['year'], row['month'], 15)` fails if year/month None (files not matching pattern); caught only by the broad except.
10. VA L275 `.iloc[-1]` of trend_slope assumes NDVI rows exist; L277 current values from 6-month window assume non-empty.
11. DM L87 only `*.tif` while L41 also accepts `*.tiff`. DM L58/98 year detection `startswith('20')`.
12. DASH forecast validation is in-sample (L925-931); `fillna(method='ffill')` (L898) deprecated in current pandas; `freq='M'` deprecated in pandas 2.2+ (suggest 'ME'). `Prophet`/`statsmodels` imports (L90-91) are required for the whole dashboard.
13. Mojibake in emoji/arrow strings in DM, DD, CO, DASH (encoding corruption of source files).
14. `warnings.filterwarnings('ignore')` VA L13 hides problems. VA L10 etc. import unused (PCA, StandardScaler, seaborn).
15. README says DP has `src.read(4)` outside `with`; I saw `src.read(4)` at DP L58 but did not verify the `with` scope (DP only partly read).

## 5. Verification of application-text claims

| Claim | Verdict | Evidence |
|---|---|---|
| SARIMA trained on 2020-2023, forecasting 2024 | Contradicted (partly). Not found as stated | No train/test split by year anywhere. The only SARIMA is DASH L912, `ARIMA(1,1,1)(1,1,1,12)` fit on the entire monthly series and forecasting the 12 months after the last data point (L914). The data requested by COL L35-36 is 2020-2024, so the model is not "2020-2023 -> 2024"; if data end 2024-12 it forecasts 2025 (unverified what months actually exist). Validation on last 12 months is in-sample (L925-931). Not in any of the six requested files; only in DASH. Prophet is also used (L906). |
| Z-score anomaly detection | Confirmed | VA L209-210 (|z|>2.0 on SavGol residuals) and DASH L172-175 (|z|>2.5 rolling window 12, 6 when called at L828). Two different thresholds/methods. |
| 225 km2 area | Contradicted | Code says 10 km2: COL L19 comment "10km square", DASH L101 `'area_km2': 10`. The AOI box in COL L18-24 is 0.14 deg lon x 0.09 deg lat at ~55 N, which I compute (not executed) as about 8.9 km x 10.0 km = ~89 km2. COL L30-31 prints the GEE-computed area but its output is not in the repo. The number 225 appears only as the 15x15 = 225 sample pixels (VA L455 comment), not an area. |
| NDVI threshold 0.3 | Partly confirmed, not as a single threshold | 0.3 appears as: VA L280 drought rule (NDVI < 0.3), DASH L118/123/142 fallback "warning" 0.3, DASH L627 down-arrow. The main classifiers use 0.6/0.4/0.2 (VA), 0.75/0.5/0.2 and 0.65/0.4/0.15 (CV). No cutoff of 0.3 used to mask or define vegetation. |
| Cloud filter 15% | Confirmed | COL L47 `ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15)` (strictly less than 15; scene-level only, no pixel mask). Not in any of the six requested Python files, only in COL. |

## Files referenced
All under `D:\New Projects\vegetation ANlysis BeVisioners project\legacy_uk\`: `vegetation analyss.py`, `data manager.py`, `crop,veg.py`, `data diagonistic.py`, `coodinates.py`, `indicesextraction.py`, `README.md`; plus `dashboard.py`, `data colecetion.py`, `dataprocesing.py` (partial reads as noted).
