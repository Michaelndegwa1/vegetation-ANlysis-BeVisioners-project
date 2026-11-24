import ee
import geemap
import datetime
import time # Import time for polling task status

# --- Step 0: Authentication and Initialization ---
try:
    ee.Initialize(project='premium-episode-423509-g8')
    print("Earth Engine initialized successfully!")
except Exception as e:
    print(f"Error initializing Earth Engine: {e}")
    print("Attempting to authenticate...")
    ee.Authenticate() # This will open a browser for authentication
    ee.Initialize(project='premium-episode-423509-g8')
    print("Earth Engine re-initialized after authentication.")

# --- Step 1: Area of Interest (AOI) --- 
aoi_coordinates_from_gee_editor = [
    [[-1.7516, 55.0504], # Placeholder: Approx. top-left of a 10km square in NE England
     [-1.7516, 54.9604], # Placeholder: Approx. bottom-left
     [-1.6116, 54.9604], # Placeholder: Approx. bottom-right
     [-1.6116, 55.0504], # Placeholder: Approx. top-right
     [-1.7516, 55.0504]] # Placeholder: Closes the polygon (same as first point)
]
aoi = ee.Geometry.Polygon(aoi_coordinates_from_gee_editor)
print("\nAOI defined:")
print(aoi.getInfo())
# Verify the area in Python 
# Divide by 1e6 to convert from square meters to square kilometers.
area_sqkm_ee = aoi.area().divide(1e6)
print(f"Calculated AOI area in GEE (kmÂ²): {area_sqkm_ee.getInfo():.2f}")
# --- Step 2: Access and Filter Sentinel-2 Data ---

# --- MODIFICATION FOR FULL DATA: Expanding to all months from 2020 to 2024 ---
start_year = 2020
end_year = 2024 # Process data up to the end of 2024

start_date_str = f'{start_year}-01-01'
end_date_str = f'{end_year}-12-31' # Ensures this covers all of 2024

print(f"\nFiltering Sentinel-2 data from {start_date_str} to {end_date_str} over AOI...")

# Load the Sentinel-2 Surface Reflectance (Level-2A) harmonized collection.
s2_collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
    .filterBounds(aoi) \
    .filterDate(start_date_str, end_date_str) \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 15)) # Filter for less than 15% cloud cover

# Function to apply scaling factors. Sentinel-2 SR bands are scaled by 10000.
def apply_scale_factors(image):
    optical_bands = image.select(['B2', 'B3', 'B4', 'B8']).multiply(0.0001)
    return image.addBands(optical_bands, None, True)

s2_collection = s2_collection.map(apply_scale_factors)

initial_collection_size = s2_collection.size().getInfo()
print(f"Number of initial filtered Sentinel-2 images (before compositing): {initial_collection_size}")

# --- Step 3: Calculate Vegetation Indices (NDVI, EVI, NDWI) ---

print("\nCalculating vegetation indices (NDVI, EVI, NDWI)...")

def calculate_indices(image):
    """Calculates NDVI, EVI, and NDWI for a Sentinel-2 image and casts to Float32."""
    # NDVI: (NIR - RED) / (NIR + RED)
    # Uses B8 (NIR) and B4 (Red) bands.
    # IMPORTANT: Keep .toFloat() to ensure consistent data types for export.
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI').toFloat()

    # EVI: 2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))
    # Uses B8 (NIR), B4 (Red), B2 (Blue) bands.
    L = 1; C1 = 6; C2 = 7.5; G = 2.5
    # IMPORTANT: Keep .toFloat() to ensure consistent data types for export.
    evi = image.expression(
        'G * ((NIR - RED) / (NIR + C1 * RED - C2 * BLUE + L))',
        {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
            'BLUE': image.select('B2'),
            'L': L, 'C1': C1, 'C2': C2, 'G': G
        }).rename('EVI').toFloat()

    # NDWI (McFeeters method): (GREEN - NIR) / (GREEN + NIR)
    # Uses B3 (Green) and B8 (NIR) bands.
    # IMPORTANT: Keep .toFloat() to ensure consistent data types for export.
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI').toFloat()

    return image.addBands([ndvi, evi, ndwi])

s2_with_indices = s2_collection.map(calculate_indices)

# --- Step 4: Create Monthly Composites ---

print("\nCreating monthly median composites for all months from 2020 to 2024...")

monthly_composites = ee.ImageCollection([])

# --- MODIFICATION FOR FULL DATA: Looping through all years and all 12 months ---
for year in range(start_year, end_year + 1): # Iterate through all years from 2020 to 2024
    for month in range(1, 13): # Iterate through all 12 months
        month_start_date_ee = ee.Date.fromYMD(year, month, 1)
        # Convert ee.Date to Python datetime for easier printing/manipulation of properties
        month_start_date_py = datetime.datetime.fromtimestamp(month_start_date_ee.getInfo()['value'] / 1000.0) # Use millis() for consistency

        end_month_date_ee = month_start_date_ee.advance(1, 'month')
        monthly_images = s2_with_indices.filterDate(month_start_date_ee, end_month_date_ee)

        if monthly_images.size().getInfo() > 0:
            median_composite = monthly_images.median() \
                .set('system:time_start', month_start_date_ee.millis()) \
                .set('year', month_start_date_py.year) \
                .set('month', month_start_date_py.month) \
                .set('month_name', month_start_date_ee.format('MMMM').getInfo())

            monthly_composites = monthly_composites.merge(ee.ImageCollection([median_composite]))
            print(f"  Added composite for {month_start_date_py.strftime('%Y-%m')}")
        else:
            print(f"  No clear Sentinel-2 images for {month_start_date_py.strftime('%Y-%m')}. Skipping.")

final_composite_count = monthly_composites.size().getInfo()
print(f"\nTotal monthly composites created: {final_composite_count}")

# --- Step 5: Export Monthly Composites to Google Drive ---

print("\nInitiating export tasks to Google Drive...")
print(f"WARNING: This will initiate up to {final_composite_count} export tasks, which may take a very long time to complete and consume significant Google Drive space and Earth Engine processing quota.")
export_folder = 'vegetation_analysis_2020_2024_full_data' # Suggest a new folder name to keep test data separate

# List of bands to export (only the calculated indices)
bands_to_export = ['NDVI', 'EVI', 'NDWI']

# Get the list of images (composites) to export from the ImageCollection
monthly_composite_list_ee = monthly_composites.toList(final_composite_count)

# Store the started tasks to monitor them later.
started_tasks = []
for i in range(final_composite_count):
    image_to_export = ee.Image(monthly_composite_list_ee.get(i))

    # Extract properties for generating unique filenames.
    year = image_to_export.get('year').getInfo()
    month = image_to_export.get('month').getInfo()
    month_name = image_to_export.get('month_name').getInfo()

    description = f'NE_England_S2_Indices_{year}_{month:02d}_{month_name}'
    file_name_prefix = description

    # Define the export task.
    task = ee.batch.Export.image.toDrive(
        image=image_to_export.select(bands_to_export),
        description=description,
        folder=export_folder, # Export to the specified folder
        fileNamePrefix=file_name_prefix,
        region=aoi,
        scale=10,
        crs='EPSG:27700',
        maxPixels=1e10,
        fileFormat='GeoTIFF'
    )
    task.start()
    started_tasks.append(task)
    print(f"  Export task started for: {description}")

print("\nAll export tasks have been initiated. You can monitor their progress.")
print("Proceed to the next step (Task Monitoring) in this script, or check the GEE Code Editor Tasks tab (https://code.earthengine.google.com/tasks) in your web browser.")


# --- Step 6: Monitor Export Tasks ---
# This loop will periodically check the status of all initiated export tasks
# and print updates until all are completed, failed, or cancelled.

print("\nMonitoring export task progress (this may take a while, depending on data volume and GEE queue)...")
all_completed = False
while not all_completed:
    all_completed = True
    print("-" * 50)
    for task in started_tasks:
        status = task.status()
        state = status['state']
        description = status['description']
        print(f"Task '{description}': Status: {state}")
        if state not in ['COMPLETED', 'FAILED', 'CANCELLED']:
            all_completed = False
    if not all_completed:
        print("Tasks still running or pending. Waiting 60 seconds before re-checking...")
        time.sleep(60) # Wait for 60 seconds before checking task statuses again.
    else:
        print("\nAll export tasks have finished!")
        for task in started_tasks:
            status = task.status()
            print(f"Final status for '{status['description']}': {status['state']}")
            if status['state'] == 'FAILED':
                print(f"  Error message: {status.get('error_message', 'No error message provided.')}")

print(f"\nData collection and export process complete. Your GeoTIFFs should now be in your Google Drive under the '{export_folder}' folder.")