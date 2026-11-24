import pandas as pd
import numpy as np

def classify_vegetation(value, crop_type="wheat"):
    """Classifies vegetation health based on index value and crop type thresholds"""
    
    # Set thresholds based on crop type (wheat or barley)
    if crop_type == "wheat":
        thresholds = {'healthy': 0.75, 'warning': 0.5, 'alert': 0.2}
    elif crop_type == "barley":
        thresholds = {'healthy': 0.65, 'warning': 0.4, 'alert': 0.15}
    else:
        thresholds = {'healthy': 0.7, 'warning': 0.45, 'alert': 0.2}  # Default

    # Classify based on thresholds
    if value > thresholds['healthy']:
        return "Healthy"
    elif value > thresholds['warning']:
        return "Warning"
    else:
        return "Alert"

def compute_crop_thresholds(pixel_df, crop_type="wheat"):
    """Compute thresholds based on 10th percentile for a given crop"""
    crop_df = pixel_df[pixel_df['crop_type'] == crop_type]
    
    # Calculate 10th percentile of NDVI for the crop
    ndvi_10th_percentile = np.percentile(crop_df['ndvi'].dropna(), 10)
    
    # Set thresholds based on the 10th percentile and crop type
    if crop_type == "wheat":
        thresholds = {'healthy': ndvi_10th_percentile + 0.15, 'warning': ndvi_10th_percentile + 0.05, 'alert': ndvi_10th_percentile - 0.1}
    elif crop_type == "barley":
        thresholds = {'healthy': ndvi_10th_percentile + 0.10, 'warning': ndvi_10th_percentile + 0.03, 'alert': ndvi_10th_percentile - 0.15}
    
    return thresholds

def process_vegetation_health(pixel_df, crop_type="wheat"):
    """Classifies vegetation health and calculates crop-specific thresholds"""
    
    # Compute the crop-specific thresholds based on 10th percentile
    thresholds = compute_crop_thresholds(pixel_df, crop_type)
    
    # Apply classification to NDVI values based on thresholds
    pixel_df["status"] = pixel_df["ndvi"].apply(lambda x: classify_vegetation(x, crop_type))
    
    # Show crop-specific thresholds
    print(f"Thresholds for {crop_type} crop:")
    print(f"Healthy: {thresholds['healthy']}")
    print(f"Warning: {thresholds['warning']}")
    print(f"Alert: {thresholds['alert']}")
    
    return pixel_df

def save_processed_data(pixel_df, output_path="processed_vegetation_data.csv"):
    """Save the processed DataFrame with classifications"""
    pixel_df.to_csv(output_path, index=False)
    print(f"Processed data saved to {output_path}")

# -----------------------------
# Main function to execute the process
# -----------------------------
def main():
    # Load pixel data
    pixel_df = pd.read_csv("data/time_series/pixel_time_series.csv")
    
    # Assuming the crop information is in the 'crop_type' column (wheat, barley)
    # If the crop information is not available in your data, you may need to add it manually or modify this step
    pixel_df['crop_type'] = 'wheat'  # You can set it to 'barley' as needed or classify the data based on crop
    
    # Process the vegetation health and classification based on selected crop type (e.g., wheat or barley)
    crop_type = "wheat"  # Change to "barley" if needed
    processed_df = process_vegetation_health(pixel_df, crop_type=crop_type)
    
    # Save the processed data for dashboard integration
    save_processed_data(processed_df)

if __name__ == "__main__":
    main()