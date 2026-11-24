import pandas as pd
import os
import json

def diagnose_data_structure(data_path="data"):
    """Diagnose your actual data structure"""
    print("=== DATA STRUCTURE DIAGNOSTIC ===\n")
    
    # Check directory structure
    print(f"1. CHECKING DIRECTORY: {data_path}")
    if not os.path.exists(data_path):
        print(f"âŒ Directory '{data_path}' does not exist!")
        return
    print(f"âœ… Directory exists")
    
    # Check subdirectories
    processed_dir = f"{data_path}/processed"
    time_series_dir = f"{data_path}/time_series"
    
    print(f"\n2. CHECKING SUBDIRECTORIES:")
    print(f"   - {processed_dir}: {'âœ… exists' if os.path.exists(processed_dir) else 'âŒ missing'}")
    print(f"   - {time_series_dir}: {'âœ… exists' if os.path.exists(time_series_dir) else 'âŒ missing'}")
    
    # Check individual files and their structure
    files_to_check = [
        f"{processed_dir}/data_inventory.csv",
        f"{time_series_dir}/pixel_time_series.csv", 
        f"{time_series_dir}/spatial_statistics.csv",
        f"{time_series_dir}/analysis_summary.json",
        f"{processed_dir}/processed_vegetation_data.csv"
    ]
    
    print(f"\n3. CHECKING FILES AND THEIR STRUCTURE:")
    
    for file_path in files_to_check:
        file_name = os.path.basename(file_path)
        print(f"\n--- {file_name} ---")
        
        if not os.path.exists(file_path):
            print(f"âŒ File missing: {file_path}")
            continue
            
        print(f"âœ… File exists: {file_path}")
        
        try:
            if file_path.endswith('.csv'):
                # Read first few rows to check structure
                df = pd.read_csv(file_path)
                print(f"   ðŸ“Š Shape: {df.shape} (rows, columns)")
                print(f"   ðŸ“‹ Columns: {list(df.columns)}")
                print(f"   ðŸ“… Data types:")
                for col, dtype in df.dtypes.items():
                    print(f"      - {col}: {dtype}")
                
                # Check for key vegetation indices
                veg_indices = ['ndvi', 'evi', 'ndwi', 'savi', 'ndre']
                found_indices = [idx for idx in veg_indices if idx in df.columns]
                missing_indices = [idx for idx in veg_indices if idx not in df.columns]
                
                print(f"   ðŸŒ± Vegetation indices found: {found_indices}")
                if missing_indices:
                    print(f"   âŒ Missing indices: {missing_indices}")
                
                # Show first few rows
                print(f"   ðŸ“„ First 3 rows:")
                print(df.head(3).to_string(index=False))
                
            elif file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"   ðŸ“‹ JSON keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dictionary'}")
                
        except Exception as e:
            print(f"   âŒ Error reading file: {e}")
    
    print(f"\n=== DIAGNOSTIC COMPLETE ===")

# Run the diagnostic
if __name__ == "__main__":
    # Change this path to match your data directory
    diagnose_data_structure("data")