import rasterio
import numpy as np
import os
import matplotlib.pyplot as plt

# Define functions to calculate NDVI, EVI, NDWI
def calculate_ndvi(nir_band, red_band):
    return (nir_band - red_band) / (nir_band + red_band)

def calculate_evi(nir_band, red_band, blue_band, G=2.5, C1=6, C2=7.5, L=10000):
    return G * ((nir_band - red_band) / (nir_band + C1 * red_band - C2 * blue_band + L))

def calculate_ndwi(nir_band, green_band):
    return (nir_band - green_band) / (nir_band + green_band)

# Load GeoTIFF file and extract the bands (Blue, Green, Red, NIR)
def load_image(image_path):
    with rasterio.open(image_path) as src:
        num_bands = src.count  # Get the number of bands in the image
        print(f"File {image_path} has {num_bands} bands.")
        
        if num_bands >= 3:
            bands = src.read([1, 2, 3])  # Assuming Band 1 (Blue), Band 2 (Green), Band 3 (Red)
            meta = src.meta
        else:
            raise ValueError(f"Image {image_path} does not have enough bands.")
    
    return bands, meta, num_bands

# Extract indices from image files in a directory
def extract_indices_from_directory(directory_path):
    # List all years in the directory
    years = os.listdir(directory_path)
    
    for year in years:
        year_path = os.path.join(directory_path, year)
        
        if os.path.isdir(year_path):  # Process only folders (years)
            print(f"Processing year: {year}")
            
            # List all GeoTIFF files in the year folder
            files = [f for f in os.listdir(year_path) if f.endswith('.tif')]
            
            for file in files:
                file_path = os.path.join(year_path, file)
                print(f"Processing file: {file_path}")
                
                # Load the image and check for available bands
                bands, meta, num_bands = load_image(file_path)
                
                # Get the individual bands (Blue, Green, Red)
                blue_band = bands[0]  # Band 1 (Blue)
                green_band = bands[1]  # Band 2 (Green)
                red_band = bands[2]  # Band 3 (Red)

                # Check if NIR band is available (Band 4)
                if num_bands >= 4:
                    nir_band = src.read(4)  # Band 4 (NIR)
                    # Calculate NDVI, EVI, NDWI
                    ndvi = calculate_ndvi(nir_band, red_band)
                    ndwi = calculate_ndwi(nir_band, green_band)
                    print("NIR band found. Calculating NDVI and NDWI.")
                else:
                    ndvi, ndwi = None, None
                    print("NIR band missing, skipping NDVI and NDWI calculations.")

                # Always calculate EVI (requires Blue, Red, and optionally NIR if available)
                evi = calculate_evi(nir_band if num_bands >= 4 else np.zeros_like(red_band), red_band, blue_band)
                
                # Plot the indices
                fig, ax = plt.subplots(1, 3, figsize=(15, 5))
                
                if ndvi is not None:
                    ax[0].imshow(ndvi, cmap='RdYlGn')
                    ax[0].set_title('NDVI')
                else:
                    ax[0].imshow(np.zeros_like(red_band), cmap='RdYlGn')
                    ax[0].set_title('NDVI (NIR missing)')
                
                ax[0].axis('off')

                ax[1].imshow(evi, cmap='Spectral')
                ax[1].set_title('EVI')
                ax[1].axis('off')
                
                if ndwi is not None:
                    ax[2].imshow(ndwi, cmap='Blues')
                    ax[2].set_title('NDWI')
                else:
                    ax[2].imshow(np.zeros_like(green_band), cmap='Blues')
                    ax[2].set_title('NDWI (NIR missing)')
                
                ax[2].axis('off')
                
                plt.show()

                # Optionally: Save the results as new GeoTIFF files
                if ndvi is not None:
                    save_index_to_geotiff(ndvi, meta, f"{file_path}_ndvi.tif")
                if ndwi is not None:
                    save_index_to_geotiff(ndwi, meta, f"{file_path}_ndwi.tif")
                save_index_to_geotiff(evi, meta, f"{file_path}_evi.tif")

# Function to save the indices to GeoTIFF
def save_index_to_geotiff(index, meta, output_path):
    with rasterio.open(output_path, 'w', **meta) as dest:
        dest.write(index, 1)

# Main function: Provide the path to the `raw_geotiffs` directory
directory_path = 'E:/vegitation analysis/data/raw_geotiffs'  # Update this path if necessary
extract_indices_from_directory(directory_path)