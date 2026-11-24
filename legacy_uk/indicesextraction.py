# indices_extract.py
# pip install rasterio numpy pandas
import numpy as np, pandas as pd, rasterio
from rasterio.transform import xy

IN_TIF = r"E:\vegitation analysis\data\raw_geotiffs\2020\NE_England_S2_Indices_2020_01_January.tif"   # <- change

with rasterio.open(IN_TIF) as src:
    ndvi = src.read(1).astype("float32")
    evi  = src.read(2).astype("float32")
    ndwi = src.read(3).astype("float32")
    meta = src.meta.copy()
    nodata_vals = src.nodatavals

# mask NoData to NaN
def mask_nodata(arr, nodata):
    if nodata is None:
        return arr
    return np.where(arr == nodata, np.nan, arr)

ndvi = mask_nodata(ndvi, nodata_vals[0])
evi  = mask_nodata(evi,  nodata_vals[1])
ndwi = mask_nodata(ndwi, nodata_vals[2])

# --- Fix EVI scale (your file looks ~Ã—100) ---
if np.nanmax(np.abs(evi)) > 5:
    evi = evi / 100.0
evi = np.clip(evi, -1, 1)  # keep tidy

# --- Save single-band GeoTIFFs (same georeference/CRS) ---
def save_band(path, arr, meta):
    m = meta.copy()
    m.update(count=1, dtype="float32", nodata=np.nan, compress="lzw")
    with rasterio.open(path, "w", **m) as dst:
        dst.write(arr.astype("float32"), 1)

save_band(IN_TIF.replace(".tif","_NDVI.tif"), ndvi, meta)
save_band(IN_TIF.replace(".tif","_EVI.tif"),  evi,  meta)
save_band(IN_TIF.replace(".tif","_NDWI.tif"), ndwi, meta)

# --- Optional: export a quick point sample to CSV (for charts/maps) ---
# sample up to N valid pixels to keep file small
N = 50000
valid = np.where(~np.isnan(ndvi))
if valid[0].size > N:
    idx = np.random.default_rng(42).choice(valid[0].size, N, replace=False)
    rows, cols = valid[0][idx], valid[1][idx]
else:
    rows, cols = valid

with rasterio.open(IN_TIF) as src:
    xs, ys = xy(src.transform, rows, cols)

df = pd.DataFrame({
    "row": rows, "col": cols,
    "lon": xs, "lat": ys,
    "ndvi": ndvi[rows, cols],
    "evi":  evi[rows, cols],
    "ndwi": ndwi[rows, cols],
})
out_csv = IN_TIF.replace(".tif", "_indices_sample.csv")
df.to_csv(out_csv, index=False)

print("Done:",
      out_csv,
      IN_TIF.replace(".tif","_NDVI.tif"),
      IN_TIF.replace(".tif","_EVI.tif"),
      IN_TIF.replace(".tif","_NDWI.tif"), sep="\n - ")