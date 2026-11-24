import pandas as pd
import numpy as np
import rasterio
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy import stats
from scipy.signal import savgol_filter
import warnings
warnings.filterwarnings('ignore')

class VegetationTimeSeriesAnalyzer:
    def __init__(self, data_manager):
        """Initialize the time series analyzer with data manager"""
        self.data_manager = data_manager
        self.processed_dir = data_manager.processed_dir
        self.timeseries_dir = data_manager.timeseries_dir
        
        # Thresholds for vegetation health assessment
        self.ndvi_thresholds = {
            'healthy': 0.6,      # NDVI > 0.6 = healthy vegetation
            'warning': 0.4,      # 0.4 < NDVI <= 0.6 = warning
            'alert': 0.2         # NDVI <= 0.4 = alert (0.2 is critical)
        }
        
        self.evi_thresholds = {
            'healthy': 0.4,
            'warning': 0.25,
            'alert': 0.15
        }
        
        # Store time series data
        self.pixel_timeseries = None
        self.spatial_stats = None
        self.anomaly_detections = None
        
    def extract_pixel_time_series(self, sample_points=None, grid_size=10):
        """
        Extract time series for representative pixel locations
        
        Args:
            sample_points: List of (x, y) pixel coordinates, or None for grid sampling
            grid_size: If sample_points is None, create a grid of this size
        """
        print("Extracting pixel time series...")
        
        # Load data inventory
        inventory_file = self.processed_dir / "data_inventory.csv"
        if not inventory_file.exists():
            print("No data inventory found. Run data_manager.scan_available_data() first.")
            return None
            
        inventory_df = pd.read_csv(inventory_file)
        inventory_df = inventory_df.sort_values(['year', 'month']).reset_index(drop=True)
        
        time_series_data = []
        
        # Get image dimensions from first file
        first_file = Path(inventory_df.iloc[0]['full_path'])
        with rasterio.open(first_file) as src:
            height, width = src.height, src.width
            
        # Define sample points
        if sample_points is None:
            # Create regular grid of sample points
            x_coords = np.linspace(width//10, width-width//10, grid_size)
            y_coords = np.linspace(height//10, height-height//10, grid_size)
            sample_points = [(int(x), int(y)) for x in x_coords for y in y_coords]
        
        print(f"Sampling {len(sample_points)} pixel locations across {len(inventory_df)} time points...")
        
        # Extract time series for each file
        for idx, row in inventory_df.iterrows():
            file_path = Path(row['full_path'])
            
            try:
                with rasterio.open(file_path) as src:
                    # Read all bands
                    ndvi_band = src.read(1)  # Band 1 = NDVI
                    evi_band = src.read(2)   # Band 2 = EVI  
                    ndwi_band = src.read(3)  # Band 3 = NDWI
                    
                    # Create date
                    date = datetime(row['year'], row['month'], 15)  # Mid-month
                    
                    # Extract values for each sample point
                    for point_id, (x, y) in enumerate(sample_points):
                        if 0 <= y < height and 0 <= x < width:
                            ndvi_val = ndvi_band[y, x]
                            evi_val = evi_band[y, x]
                            ndwi_val = ndwi_band[y, x]
                            
                            # Only add if values are valid
                            if not (np.isnan(ndvi_val) or np.isnan(evi_val) or np.isnan(ndwi_val)):
                                time_series_data.append({
                                    'date': date,
                                    'year': row['year'],
                                    'month': row['month'],
                                    'month_name': row['month_name'],
                                    'point_id': point_id,
                                    'pixel_x': x,
                                    'pixel_y': y,
                                    'ndvi': ndvi_val,
                                    'evi': evi_val,
                                    'ndwi': ndwi_val
                                })
                                
            except Exception as e:
                print(f"Error processing {file_path.name}: {e}")
                continue
        
        # Convert to DataFrame
        self.pixel_timeseries = pd.DataFrame(time_series_data)
        
        if not self.pixel_timeseries.empty:
            # Save time series data
            ts_file = self.timeseries_dir / "pixel_time_series.csv"
            self.pixel_timeseries.to_csv(ts_file, index=False)
            print(f"Time series data saved to: {ts_file}")
            print(f"Data shape: {self.pixel_timeseries.shape}")
            print(f"Date range: {self.pixel_timeseries['date'].min()} to {self.pixel_timeseries['date'].max()}")
            
        return self.pixel_timeseries
    
    def calculate_spatial_statistics(self):
        """Calculate spatial statistics for each time point"""
        print("Calculating spatial statistics...")
        
        if self.pixel_timeseries is None:
            print("No time series data available. Run extract_pixel_time_series() first.")
            return None
        
        # Group by date and calculate statistics
        spatial_stats = []
        
        for date, group in self.pixel_timeseries.groupby('date'):
            stats_dict = {
                'date': date,
                'year': group['year'].iloc[0],
                'month': group['month'].iloc[0],
                'month_name': group['month_name'].iloc[0],
                'pixel_count': len(group),
            }
            
            # Calculate statistics for each index
            for index in ['ndvi', 'evi', 'ndwi']:
                values = group[index].dropna()
                if len(values) > 0:
                    stats_dict.update({
                        f'{index}_mean': values.mean(),
                        f'{index}_median': values.median(),
                        f'{index}_std': values.std(),
                        f'{index}_min': values.min(),
                        f'{index}_max': values.max(),
                        f'{index}_q25': values.quantile(0.25),
                        f'{index}_q75': values.quantile(0.75)
                    })
                    
            spatial_stats.append(stats_dict)
        
        self.spatial_stats = pd.DataFrame(spatial_stats)
        self.spatial_stats = self.spatial_stats.sort_values('date').reset_index(drop=True)
        
        # Save spatial statistics
        stats_file = self.timeseries_dir / "spatial_statistics.csv"
        self.spatial_stats.to_csv(stats_file, index=False)
        print(f"Spatial statistics saved to: {stats_file}")
        
        return self.spatial_stats
    
    def detect_anomalies_and_trends(self, window_size=5):
        """
        Detect anomalies and trends in vegetation indices
        
        Args:
            window_size: Size of moving window for smoothing
        """
        print("Detecting anomalies and trends...")
        
        if self.spatial_stats is None:
            print("No spatial statistics available. Run calculate_spatial_statistics() first.")
            return None
        
        anomaly_results = []
        
        # Analyze each vegetation index
        for index in ['ndvi', 'evi', 'ndwi']:
            mean_col = f'{index}_mean'
            
            if mean_col not in self.spatial_stats.columns:
                continue
                
            values = self.spatial_stats[mean_col].dropna()
            dates = self.spatial_stats.loc[values.index, 'date']
            
            if len(values) < window_size:
                continue
            
            # Apply smoothing
            smoothed = savgol_filter(values, window_size, 2)
            
            # Calculate residuals (difference from smoothed trend)
            residuals = values - smoothed
            
            # Detect anomalies using z-score
            z_scores = np.abs(stats.zscore(residuals))
            anomaly_threshold = 2.0  # 2 standard deviations
            
            # Calculate trend (slope of linear regression)
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Assess current vegetation health
            current_value = values.iloc[-1]
            health_status = self.assess_vegetation_health(current_value, index)
            
            # Store results for each time point
            for i, (date, value, smooth_val, residual, z_score) in enumerate(
                zip(dates, values, smoothed, residuals, z_scores)):
                
                anomaly_results.append({
                    'date': date,
                    'index': index.upper(),
                    'value': value,
                    'smoothed_value': smooth_val,
                    'residual': residual,
                    'z_score': z_score,
                    'is_anomaly': z_score > anomaly_threshold,
                    'trend_slope': slope,
                    'trend_r2': r_value**2,
                    'trend_p_value': p_value,
                    'health_status': health_status if i == len(values)-1 else None
                })
        
        self.anomaly_detections = pd.DataFrame(anomaly_results)
        
        # Save anomaly detection results
        anomaly_file = self.timeseries_dir / "anomaly_detections.csv"
        self.anomaly_detections.to_csv(anomaly_file, index=False)
        print(f"Anomaly detection results saved to: {anomaly_file}")
        
        return self.anomaly_detections
    
    def assess_vegetation_health(self, index_value, index_type):
        """Assess vegetation health based on index values"""
        
        thresholds = self.ndvi_thresholds if index_type == 'ndvi' else self.evi_thresholds
        
        if index_value >= thresholds['healthy']:
            return 'Healthy'
        elif index_value >= thresholds['warning']:
            return 'Warning'
        else:
            return 'Alert'
    
    def diagnose_vegetation_problems(self):
        """
        Diagnose potential causes of vegetation problems based on index patterns
        """
        if self.spatial_stats is None or self.anomaly_detections is None:
            print("Need spatial statistics and anomaly detections first.")
            return None
        
        # Get recent data (last 6 months)
        recent_date = self.spatial_stats['date'].max()
        six_months_ago = recent_date - timedelta(days=180)
        recent_stats = self.spatial_stats[self.spatial_stats['date'] >= six_months_ago]
        
        diagnosis = {}
        
        # Analyze NDVI trends
        ndvi_trend = self.anomaly_detections[self.anomaly_detections['index'] == 'NDVI']['trend_slope'].iloc[-1]
        current_ndvi = recent_stats['ndvi_mean'].iloc[-1]
        current_ndwi = recent_stats['ndwi_mean'].iloc[-1]
        
        # Drought detection
        if current_ndvi < 0.3 and current_ndwi < -0.1 and ndvi_trend < -0.001:
            diagnosis['primary_issue'] = 'Drought Stress'
            diagnosis['confidence'] = 'High'
            diagnosis['indicators'] = ['Low NDVI', 'Low NDWI', 'Declining trend']
            
        # Flood/waterlogging detection  
        elif current_ndwi > 0.3 and current_ndvi < 0.4:
            diagnosis['primary_issue'] = 'Waterlogging/Flood Damage'
            diagnosis['confidence'] = 'Medium'
            diagnosis['indicators'] = ['High NDWI', 'Low NDVI']
            
        # Disease/pest detection (rapid NDVI decline)
        elif ndvi_trend < -0.002 and current_ndvi < 0.5:
            diagnosis['primary_issue'] = 'Possible Disease/Pest Attack'
            diagnosis['confidence'] = 'Medium'
            diagnosis['indicators'] = ['Rapid NDVI decline', 'Below normal vegetation']
            
        # Seasonal variation (normal)
        else:
            diagnosis['primary_issue'] = 'Normal Seasonal Variation'
            diagnosis['confidence'] = 'Low'
            diagnosis['indicators'] = ['Values within normal range']
            
        diagnosis['current_ndvi'] = current_ndvi
        diagnosis['current_ndwi'] = current_ndwi
        diagnosis['health_status'] = self.assess_vegetation_health(current_ndvi, 'ndvi')
        diagnosis['assessment_date'] = recent_date.strftime('%Y-%m-%d')
        
        return diagnosis
    
    def create_analysis_summary(self):
        """Create a comprehensive analysis summary"""
        print("Creating analysis summary...")
        
        if self.pixel_timeseries is None:
            print("No analysis data available.")
            return None
        
        # Run diagnosis
        diagnosis = self.diagnose_vegetation_problems()
        
        # Create summary
        summary = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_period': f"{self.pixel_timeseries['date'].min().strftime('%Y-%m')} to {self.pixel_timeseries['date'].max().strftime('%Y-%m')}",
            'total_pixels_analyzed': self.pixel_timeseries['point_id'].nunique(),
            'total_time_points': self.pixel_timeseries['date'].nunique(),
            'vegetation_diagnosis': diagnosis
        }
        
        # Add recent statistics
        if self.spatial_stats is not None:
            latest_stats = self.spatial_stats.iloc[-1]
            summary['latest_statistics'] = {
                'date': latest_stats['date'].strftime('%Y-%m-%d'),
                'mean_ndvi': round(latest_stats['ndvi_mean'], 3),
                'mean_evi': round(latest_stats['evi_mean'], 3),
                'mean_ndwi': round(latest_stats['ndwi_mean'], 3),
                'ndvi_std': round(latest_stats['ndvi_std'], 3)
            }
        
        # Add anomaly count
        if self.anomaly_detections is not None:
            recent_anomalies = self.anomaly_detections[
                self.anomaly_detections['date'] >= (self.anomaly_detections['date'].max() - timedelta(days=90))
            ]
            summary['recent_anomalies'] = len(recent_anomalies[recent_anomalies['is_anomaly']])
        
        # Save summary
        import json
        summary_file = self.timeseries_dir / "analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"Analysis summary saved to: {summary_file}")
        return summary
    
    def visualize_time_series(self, save_plots=True):
        """Create comprehensive time series visualizations"""
        if self.spatial_stats is None:
            print("No spatial statistics available for visualization.")
            return
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Vegetation Time Series Analysis - North East England', fontsize=16)
        
        # Plot 1: NDVI time series with health zones
        ax1 = axes[0, 0]
        ax1.plot(self.spatial_stats['date'], self.spatial_stats['ndvi_mean'], 'g-', linewidth=2, label='NDVI Mean')
        ax1.fill_between(self.spatial_stats['date'], 
                        self.spatial_stats['ndvi_mean'] - self.spatial_stats['ndvi_std'],
                        self.spatial_stats['ndvi_mean'] + self.spatial_stats['ndvi_std'],
                        alpha=0.3, color='green')
        
        # Add health zone lines
        ax1.axhline(y=self.ndvi_thresholds['healthy'], color='darkgreen', linestyle='--', alpha=0.7, label='Healthy')
        ax1.axhline(y=self.ndvi_thresholds['warning'], color='orange', linestyle='--', alpha=0.7, label='Warning')
        ax1.axhline(y=self.ndvi_thresholds['alert'], color='red', linestyle='--', alpha=0.7, label='Alert')
        
        ax1.set_title('NDVI Time Series with Health Zones')
        ax1.set_ylabel('NDVI')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: EVI time series
        ax2 = axes[0, 1]
        ax2.plot(self.spatial_stats['date'], self.spatial_stats['evi_mean'], 'b-', linewidth=2, label='EVI Mean')
        ax2.fill_between(self.spatial_stats['date'], 
                        self.spatial_stats['evi_mean'] - self.spatial_stats['evi_std'],
                        self.spatial_stats['evi_mean'] + self.spatial_stats['evi_std'],
                        alpha=0.3, color='blue')
        ax2.set_title('EVI Time Series')
        ax2.set_ylabel('EVI')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: NDWI time series
        ax3 = axes[1, 0]
        ax3.plot(self.spatial_stats['date'], self.spatial_stats['ndwi_mean'], 'c-', linewidth=2, label='NDWI Mean')
        ax3.fill_between(self.spatial_stats['date'], 
                        self.spatial_stats['ndwi_mean'] - self.spatial_stats['ndwi_std'],
                        self.spatial_stats['ndwi_mean'] + self.spatial_stats['ndwi_std'],
                        alpha=0.3, color='cyan')
        ax3.set_title('NDWI Time Series (Water Content)')
        ax3.set_ylabel('NDWI')
        ax3.set_xlabel('Date')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Anomaly detection
        ax4 = axes[1, 1]
        if self.anomaly_detections is not None:
            ndvi_anomalies = self.anomaly_detections[self.anomaly_detections['index'] == 'NDVI']
            normal_points = ndvi_anomalies[~ndvi_anomalies['is_anomaly']]
            anomaly_points = ndvi_anomalies[ndvi_anomalies['is_anomaly']]
            
            ax4.scatter(normal_points['date'], normal_points['value'], 
                       c='green', alpha=0.6, label='Normal', s=30)
            ax4.scatter(anomaly_points['date'], anomaly_points['value'], 
                       c='red', alpha=0.8, label='Anomaly', s=50, marker='x')
            ax4.plot(ndvi_anomalies['date'], ndvi_anomalies['smoothed_value'], 
                    'k--', alpha=0.7, label='Trend')
        
        ax4.set_title('NDVI Anomaly Detection')
        ax4.set_ylabel('NDVI')
        ax4.set_xlabel('Date')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_plots:
            plot_file = self.timeseries_dir / "vegetation_time_series_analysis.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"Time series plots saved to: {plot_file}")
        
        plt.show()
        
        return fig

# Usage example
def run_time_series_analysis():
    """Run the complete time series analysis pipeline"""
    from data_manager import VegetationDataManager
    
    print("Starting Vegetation Time Series Analysis")
    print("=" * 60)
    
    # Initialize components
    data_manager = VegetationDataManager()
    analyzer = VegetationTimeSeriesAnalyzer(data_manager)
    
    # Step 1: Extract pixel time series
    print("\nStep 1: Extracting pixel time series...")
    pixel_ts = analyzer.extract_pixel_time_series(grid_size=15)  # 15x15 grid = 225 sample points
    
    if pixel_ts is None or pixel_ts.empty:
        print("No time series data extracted. Check your data availability.")
        return None
    
    # Step 2: Calculate spatial statistics
    print("\nStep 2: Calculating spatial statistics...")
    spatial_stats = analyzer.calculate_spatial_statistics()
    
    # Step 3: Detect anomalies and trends
    print("\nStep 3: Detecting anomalies and trends...")
    anomalies = analyzer.detect_anomalies_and_trends()
    
    # Step 4: Create analysis summary
    print("\nStep 4: Creating analysis summary...")
    summary = analyzer.create_analysis_summary()
    
    # Step 5: Create visualizations
    print("\nStep 5: Creating visualizations...")
    analyzer.visualize_time_series()
    
    # Display key results
    if summary:
        print("\n" + "=" * 60)
        print("VEGETATION HEALTH ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Analysis Period: {summary['data_period']}")
        print(f"Sample Points: {summary['total_pixels_analyzed']}")
        print(f"Time Points: {summary['total_time_points']}")
        
        if 'vegetation_diagnosis' in summary and summary['vegetation_diagnosis']:
            diag = summary['vegetation_diagnosis']
            print(f"\nCURRENT VEGETATION STATUS:")
            print(f"  Health Status: {diag['health_status']}")
            print(f"  Primary Issue: {diag['primary_issue']}")
            print(f"  Confidence: {diag['confidence']}")
            print(f"  Current NDVI: {diag['current_ndvi']:.3f}")
            print(f"  Current NDWI: {diag['current_ndwi']:.3f}")
            print(f"  Indicators: {', '.join(diag['indicators'])}")
        
        if 'latest_statistics' in summary:
            stats = summary['latest_statistics']
            print(f"\nLATEST MEASUREMENTS ({stats['date']}):")
            print(f"  Mean NDVI: {stats['mean_ndvi']}")
            print(f"  Mean EVI: {stats['mean_evi']}")
            print(f"  Mean NDWI: {stats['mean_ndwi']}")
        
        print(f"\nRecent Anomalies (last 3 months): {summary.get('recent_anomalies', 0)}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("Ready to build interactive dashboard with these results.")
    
    return analyzer

if __name__ == "__main__":
    analyzer = run_time_series_analysis()