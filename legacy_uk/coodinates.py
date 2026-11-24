import rasterio
import numpy as np
import pandas as pd
import os

input_folder = r"E:\vegitation analysis\data\raw_geotiffs"
output_csv = r"E:\vegitation analysis\data\all_index_coordinates.csv"

all_data = []

print("\nScanning for GeoTIFFs (recursive)...")

for root, _, files in os.walk(input_folder):
    for filename in files:
        if filename.lower().endswith((".tif", ".tiff")):
            filepath = os.path.join(root, filename)
            print(f"Processing: {filepath}")
            try:
                with rasterio.open(filepath) as src:
                    band = src.read(1)
                    transform = src.transform
                    rows, cols = np.where(band != src.nodata)
                    if len(rows) == 0:
                        print(f"  â›” Skipped (no valid pixels): {filename}")
                        continue
                    values = band[rows, cols]
                    xs, ys = rasterio.transform.xy(transform, rows, cols)
                    df = pd.DataFrame({
                        "longitude": xs,
                        "latitude": ys,
                        "value": values,
                        "source": filename
                    })
                    all_data.append(df)
            except Exception as e:
                print(f"  âŒ Error reading {filename}: {e}")

# Combine and save
if all_data:
    final_df = pd.concat(all_data, ignore_index=True)
    final_df.to_csv(output_csv, index=False)
    print(f"\nâœ… Done! CSV saved to: {output_csv}")
else:
    print("\nâš ï¸ No valid GeoTIFF data found to export.")