import os
import pandas as pd
import rasterio
import numpy as np
from pathlib import Path
import glob
from datetime import datetime
import matplotlib.pyplot as plt

class VegetationDataManager:
    def __init__(self, data_dir="data"):
        """Initialize the data manager with directory structure"""
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw_geotiffs"
        self.processed_dir = self.data_dir / "processed"
        self.timeseries_dir = self.data_dir / "time_series"
        
        # Create directories
        for dir_path in [self.raw_dir, self.processed_dir, self.timeseries_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        print(f"Data manager initialized:")
        print(f"  Raw data: {self.raw_dir}")
        print(f"  Processed: {self.processed_dir}")
        print(f"  Time series: {self.timeseries_dir}")
    
    def organize_downloaded_files(self, download_folder):
        """
        Organize GeoTIFF files downloaded from Google Drive
        
        Args:
            download_folder: Path to folder containing downloaded GeoTIFF files
        """
        download_path = Path(download_folder)
        
        if not download_path.exists():
            print(f"Error: Download folder {download_folder} does not exist!")
            return
        
        # Find all GeoTIFF files
        geotiff_files = list(download_path.glob("*.tif")) + list(download_path.glob("*.tiff"))
        
        if not geotiff_files:
            print(f"No GeoTIFF files found in {download_folder}")
            return
        
        print(f"Found {len(geotiff_files)} GeoTIFF files")
        
        # Organize by year
        for file_path in geotiff_files:
            filename = file_path.name
            
            # Extract year from filename (NE_England_S2_Indices_YYYY_MM_Month.tif)
            try:
                parts = filename.split('_')
                year = None
                for part in parts:
                    if part.isdigit() and len(part) == 4 and part.startswith('20'):
                        year = part
                        break
                
                if year:
                    year_dir = self.raw_dir / year
                    year_dir.mkdir(exist_ok=True)
                    
                    # Copy file to year directory
                    destination = year_dir / filename
                    destination.write_bytes(file_path.read_bytes())
                    print(f"  Organized: {filename} â†’ {year}/")
                else:
                    # If no year found, put in raw directory
                    destination = self.raw_dir / filename
                    destination.write_bytes(file_path.read_bytes())
                    print(f"  Copied: {filename} (no year detected)")
                    
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
    
    def scan_available_data(self):
        """Scan and inventory all available GeoTIFF files"""
        
        print("Scanning available data...")
        
        inventory = []
        
        # Scan all subdirectories
        for geotiff_file in self.raw_dir.rglob("*.tif"):
            try:
                # Extract information from filename
                filename = geotiff_file.name
                relative_path = geotiff_file.relative_to(self.raw_dir)
                
                # Parse filename for date information
                parts = filename.replace('.tif', '').split('_')
                
                year, month, month_name = None, None, None
                for i, part in enumerate(parts):
                    if part.isdigit() and len(part) == 4 and part.startswith('20'):
                        year = int(part)
                        if i + 1 < len(parts) and parts[i + 1].isdigit():
                            month = int(parts[i + 1])
                        if i + 2 < len(parts):
                            month_name = parts[i + 2]
                        break
                
                # Get file size
                file_size_mb = geotiff_file.stat().st_size / (1024 * 1024)
                
                inventory.append({
                    'filename': filename,
                    'path': str(relative_path),
                    'year': year,
                    'month': month,
                    'month_name': month_name,
                    'size_mb': round(file_size_mb, 2),
                    'full_path': str(geotiff_file)
                })
                
            except Exception as e:
                print(f"Error reading {geotiff_file}: {e}")
        
        # Create DataFrame
        df = pd.DataFrame(inventory)
        
        if not df.empty:
            df = df.sort_values(['year', 'month']).reset_index(drop=True)
            
            # Save inventory
            inventory_file = self.processed_dir / "data_inventory.csv"
            df.to_csv(inventory_file, index=False)
            
            print(f"\nData Inventory Summary:")
            print(f"  Total files: {len(df)}")
            print(f"  Date range: {df['year'].min()}-{df['year'].max()}")
            print(f"  Total size: {df['size_mb'].sum():.1f} MB")
            print(f"  Years available: {sorted(df['year'].unique())}")
            
            # Show sample
            print(f"\nFirst 5 files:")
            print(df[['filename', 'year', 'month', 'month_name', 'size_mb']].head())
            
            print(f"\nInventory saved to: {inventory_file}")
            
        return df
    
    def test_read_geotiff(self, sample_file=None):
        """Test reading a GeoTIFF file and display basic info"""
        
        if sample_file is None:
            # Find first available GeoTIFF
            geotiff_files = list(self.raw_dir.rglob("*.tif"))
            if not geotiff_files:
                print("No GeoTIFF files found!")
                return None
            sample_file = geotiff_files[0]
        
        try:
            print(f"\nTesting GeoTIFF read: {sample_file.name}")
            
            with rasterio.open(sample_file) as src:
                print(f"  Dimensions: {src.width} x {src.height}")
                print(f"  Bands: {src.count}")
                print(f"  Band names: {src.descriptions}")
                print(f"  CRS: {src.crs}")
                print(f"  Transform: {src.transform}")
                
                # Read first band (NDVI)
                band1 = src.read(1)
                print(f"  NDVI range: {np.nanmin(band1):.3f} to {np.nanmax(band1):.3f}")
                
                if src.count >= 2:
                    band2 = src.read(2)
                    print(f"  EVI range: {np.nanmin(band2):.3f} to {np.nanmax(band2):.3f}")
                
                if src.count >= 3:
                    band3 = src.read(3)
                    print(f"  NDWI range: {np.nanmin(band3):.3f} to {np.nanmax(band3):.3f}")
                
                return {
                    'width': src.width,
                    'height': src.height,
                    'bands': src.count,
                    'crs': src.crs,
                    'ndvi_data': band1
                }
                
        except Exception as e:
            print(f"Error reading GeoTIFF: {e}")
            return None
    
    def create_quick_visualization(self, sample_file=None):
        """Create a quick visualization of the data"""
        
        data = self.test_read_geotiff(sample_file)
        
        if data is None:
            return
        
        # Create visualization
        plt.figure(figsize=(10, 8))
        
        ndvi_data = data['ndvi_data']
        
        # Mask out invalid values
        ndvi_masked = np.ma.masked_where((ndvi_data < -1) | (ndvi_data > 1), ndvi_data)
        
        plt.imshow(ndvi_masked, cmap='RdYlGn', vmin=-0.5, vmax=1.0)
        plt.colorbar(label='NDVI')
        plt.title('Sample NDVI Data from North East England')
        plt.xlabel('Pixel X')
        plt.ylabel('Pixel Y')
        
        # Save plot
        plot_file = self.processed_dir / "sample_ndvi_visualization.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.show()
        
        print(f"Visualization saved to: {plot_file}")

# Usage example
def main():
    print("Vegetation Data Manager - Setting up data access")
    print("=" * 60)
    
    # Initialize data manager
    manager = VegetationDataManager()
    
    # Step 1: If you have downloaded files, organize them
    download_folder = input("\nEnter path to your downloaded GeoTIFF files (or press Enter to skip): ").strip()
    
    if download_folder and os.path.exists(download_folder):
        print("Organizing downloaded files...")
        manager.organize_downloaded_files(download_folder)
    
    # Step 2: Scan available data
    inventory_df = manager.scan_available_data()
    
    if inventory_df is not None and not inventory_df.empty:
        # Step 3: Test reading a file
        manager.test_read_geotiff()
        
        # Step 4: Create visualization
        print("\nCreating sample visualization...")
        manager.create_quick_visualization()
        
        print("\n" + "=" * 60)
        print("DATA ACCESS SETUP COMPLETE!")
        print("Your data is organized and ready for time series analysis.")
        print("Next step: Create time series from the organized data.")
    else:
        print("\nNo data files found. Please:")
        print("1. Download your GeoTIFF files from Google Drive")
        print("2. Place them in a folder")
        print("3. Run this script again with the folder path")

if __name__ == "__main__":
    main()