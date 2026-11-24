import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json
import warnings
import os
import pandas as pd
import pydeck as pdk
warnings.filterwarnings('ignore')

# Set page configuration
st.set_page_config(
    page_title="Farm Vegetation Monitor - DSR Approach",
    page_icon="ðŸŒ±",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    #stDecoration {display:none;}
    
    .farm-header {
        background: linear-gradient(90deg, #006400, #228B22);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .farm-title {
        font-size: 2rem;
        font-weight: bold;
        margin: 0;
    }
    
    .farm-location {
        background: rgba(255,193,7,0.9);
        color: #000;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    
    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
    }
    
    .status-healthy { background-color: #28a745; }
    .status-warning { background-color: #ffc107; color: #000; }
    .status-alert { background-color: #fd7e14; }
    .status-critical { background-color: #dc3545; }
    
    .metric-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .dsr-section {
        background: linear-gradient(135deg, #e3f2fd, #bbdefb);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

import statsmodels.api as sm
from prophet import Prophet

class EnhancedVegetationAnalyzer:
    def __init__(self):
        # Actual farm details from your project
        self.farm_location = {
            'name': 'North East England Farm',
            'address': 'Northumberland, NE England',
            'latitude': 55.0054,
            'longitude': -1.6816,
            'area_km2': 10,  # Your actual AOI size
            'coordinates': [[-1.7516, 55.0504], [-1.7516, 54.9604], 
                          [-1.6116, 54.9604], [-1.6116, 55.0504]]
        }
        
        # Crop-specific information
        self.crop_info = {
            'wheat': {'areas': ['Area_1', 'Area_2'], 'season': 'Winter/Spring'},
            'barley': {'areas': ['Area_3', 'Area_4', 'Area_5'], 'season': 'Spring'}
        }
        
        # Will be computed from actual data using 10th percentile approach
        self.crop_thresholds = {}
        
    def compute_percentile_thresholds(self, ndvi_data, crop_type):
        """Compute crop-specific thresholds using 10th percentile approach"""
        if len(ndvi_data) == 0:
            return {'healthy': 0.6, 'warning': 0.3, 'alert': 0.1}
            
        valid_ndvi = ndvi_data[(ndvi_data >= -1) & (ndvi_data <= 1)]
        
        if len(valid_ndvi) == 0:
            return {'healthy': 0.6, 'warning': 0.3, 'alert': 0.1}
        
        # Use 10th, 25th, and 75th percentiles for thresholds
        p10 = np.percentile(valid_ndvi, 10)
        p25 = np.percentile(valid_ndvi, 25)
        p75 = np.percentile(valid_ndvi, 75)
        
        thresholds = {
            'alert': p10,      # 10th percentile - critical threshold
            'warning': p25,    # 25th percentile - warning threshold  
            'healthy': p75     # 75th percentile - healthy threshold
        }
        
        return thresholds
    
    def analyze_vegetation_health(self, ndvi_value, crop_type):
        """Analyze vegetation health based on NDVI and crop-specific thresholds"""
        if crop_type not in self.crop_thresholds:
            # Default thresholds if crop not found
            thresholds = {'healthy': 0.6, 'warning': 0.3, 'alert': 0.1}
        else:
            thresholds = self.crop_thresholds[crop_type]
        
        if pd.isna(ndvi_value):
            return "No Data", "â“"
        elif ndvi_value >= thresholds['healthy']:
            return "Healthy", "ðŸŸ¢"
        elif ndvi_value >= thresholds['warning']:
            return "Warning", "ðŸŸ¡"
        elif ndvi_value >= thresholds['alert']:
            return "Alert", "ðŸŸ "
        else:
            return "Critical", "ðŸ”´"
    
    def calculate_z_score_anomalies(self, df, window_size=12):
        """Calculate Z-score based anomaly detection"""
        anomalies = []
        
        for point_id in df['point_id'].unique():
            point_data = df[df['point_id'] == point_id].sort_values('date')
            
            if len(point_data) < window_size:
                continue
                
            # Rolling statistics for anomaly detection
            rolling_mean = point_data['ndvi'].rolling(window=window_size, center=True).mean()
            rolling_std = point_data['ndvi'].rolling(window=window_size, center=True).std()
            
            # Calculate Z-scores
            z_scores = (point_data['ndvi'] - rolling_mean) / rolling_std
            
            # Identify anomalies (|Z| > 2.5)
            is_anomaly = np.abs(z_scores) > 2.5
            
            for idx, row in point_data.iterrows():
                anomalies.append({
                    'date': row['date'],
                    'point_id': row['point_id'],
                    'value': row['ndvi'],
                    'z_score': z_scores.loc[idx] if not pd.isna(z_scores.loc[idx]) else 0,
                    'is_anomaly': is_anomaly.loc[idx] if not pd.isna(is_anomaly.loc[idx]) else False
                })
        
        return pd.DataFrame(anomalies)
    
    def fit_simple_forecast(self, ts_data, periods=12):
        """Fit a simple linear trend + seasonal forecast"""
        try:
            # Ensure we have enough data
            if len(ts_data) < 12:
                return None, None
            
            # Sort by date
            ts_data = ts_data.sort_values('date')
            
            # Convert dates to numeric for fitting
            ts_data['date_numeric'] = pd.to_datetime(ts_data['date']).astype(int)
            
            # Simple linear regression
            from sklearn.linear_model import LinearRegression
            X = ts_data['date_numeric'].values.reshape(-1, 1)
            y = ts_data['ndvi'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate future dates
            last_date = pd.to_datetime(ts_data['date'].max())
            future_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=periods, freq='M')
            future_numeric = future_dates.astype('int64').values.reshape(-1, 1)
            
            # Predict
            predictions = model.predict(future_numeric)
            
            # Add seasonal component (simple sine wave)
            seasonal_component = 0.1 * np.sin(2 * np.pi * np.arange(periods) / 12)
            predictions += seasonal_component
            
            # Clip to valid NDVI range
            predictions = np.clip(predictions, -1, 1)
            
            # Create forecast dataframe
            forecast_df = pd.DataFrame({
                'ds': future_dates,
                'yhat': predictions,
                'yhat_lower': predictions - 0.1,
                'yhat_upper': predictions + 0.1
            })
            
            return model, forecast_df
            
        except Exception as e:
            st.warning(f"Forecasting failed: {e}")
            return None, None
    
    def calculate_model_metrics(self, actual, predicted):
        """Calculate model performance metrics"""
        mae = mean_absolute_error(actual, predicted)
        rmse = np.sqrt(mean_squared_error(actual, predicted))
        
        # sMAPE calculation
        smape = np.mean(2 * np.abs(predicted - actual) / (np.abs(actual) + np.abs(predicted))) * 100
        
        return {
            'MAE': mae,
            'RMSE': rmse,
            'sMAPE': smape
        }
    
    def load_actual_data(self):
        """Load actual data from your files"""
        datasets = {}
        
        # Define file paths
        file_paths = {
            'pixel_time_series': "data/time_series/pixel_time_series.csv",
            'spatial_stats': "data/time_series/spatial_statistics.csv",
            'data_inventory': "data/processed/data_inventory.csv",
            'analysis_summary': "data/time_series/analysis_summary.json",
            'processed_data': "data/processed/processed_vegetation_data.csv"
        }
        
        # Load pixel time series data
        if os.path.exists(file_paths['pixel_time_series']):
            try:
                df = pd.read_csv(file_paths['pixel_time_series'])
                # Convert date column properly
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                datasets['pixel_time_series'] = df
                st.sidebar.success("âœ… Pixel time series loaded")
            except Exception as e:
                st.sidebar.error(f"âŒ Error loading pixel time series: {e}")
        
        # Load spatial statistics
        if os.path.exists(file_paths['spatial_stats']):
            try:
                df = pd.read_csv(file_paths['spatial_stats'])
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                datasets['spatial_stats'] = df
                st.sidebar.success("âœ… Spatial stats loaded")
            except Exception as e:
                st.sidebar.error(f"âŒ Error loading spatial stats: {e}")
        
        # Load processed data if available
        if os.path.exists(file_paths['processed_data']):
            try:
                df = pd.read_csv(file_paths['processed_data'])
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                datasets['processed_data'] = df
                st.sidebar.success("âœ… Processed data loaded")
            except Exception as e:
                st.sidebar.error(f"âŒ Error loading processed data: {e}")
        
        # Load analysis summary
        if os.path.exists(file_paths['analysis_summary']):
            try:
                with open(file_paths['analysis_summary'], 'r') as f:
                    datasets['analysis_summary'] = json.load(f)
                st.sidebar.success("âœ… Analysis summary loaded")
            except Exception as e:
                st.sidebar.error(f"âŒ Error loading analysis summary: {e}")
        
        return datasets if datasets else None

def main():
    st.markdown('<div class="dsr-section"><h3>ðŸ”¬ DSR Approach: Design Science Research for Farm Monitoring</h3><p>This dashboard follows the Design Science Research methodology: <strong>Design</strong> (vegetation monitoring system), <strong>Science</strong> (satellite remote sensing), <strong>Research</strong> (predictive analytics for crop management)</p></div>', unsafe_allow_html=True)
    
    # Initialize analyzer
    analyzer = EnhancedVegetationAnalyzer()
    
    # Sidebar for farm and crop selection
    st.sidebar.header("ðŸ›ï¸ Farm Selection")
    
    # Farm location info
    st.sidebar.markdown(f"""
    **ðŸ“ Current Farm:**
    - **Location:** {analyzer.farm_location['name']}
    - **Address:** {analyzer.farm_location['address']}
    - **Coordinates:** {analyzer.farm_location['latitude']:.4f}Â°N, {analyzer.farm_location['longitude']:.4f}Â°W
    - **Area:** {analyzer.farm_location['area_km2']} kmÂ²
    """)
    
    # Load data
    datasets = analyzer.load_actual_data()
    
    if not datasets:
        st.error("âŒ No data files found! Please check your data directory structure.")
        st.info("""
        Expected files:
        - data/time_series/pixel_time_series.csv
        - data/time_series/spatial_statistics.csv
        - data/processed/processed_vegetation_data.csv
        """)
        return
    
    # Use the best available dataset
    if 'processed_data' in datasets:
        main_df = datasets['processed_data'].copy()
        st.sidebar.info("Using processed vegetation data")
    elif 'pixel_time_series' in datasets:
        main_df = datasets['pixel_time_series'].copy()
        st.sidebar.info("Using pixel time series data")
    else:
        st.error("âŒ No suitable data found!")
        return
    
    # Remove rows with invalid dates
    main_df = main_df.dropna(subset=['date'])
    
    # Add crop assignments if not present
    if 'crop_type' not in main_df.columns:
        main_df['crop_type'] = main_df['point_id'].apply(
            lambda x: 'wheat' if x < 55 else 'barley'
        )
    
    if 'area_id' not in main_df.columns:
        main_df['area_id'] = main_df['point_id'].apply(
            lambda x: f'Area_{min((x//22) + 1, 5)}'
        )
    
    # Compute crop-specific thresholds
    for crop in main_df['crop_type'].unique():
        crop_data = main_df[main_df['crop_type'] == crop]['ndvi'].dropna()
        analyzer.crop_thresholds[crop] = analyzer.compute_percentile_thresholds(crop_data, crop)
    
    # Crop selection
    available_crops = sorted(main_df['crop_type'].unique())
    selected_crop = st.sidebar.selectbox("ðŸŒ¾ Select Crop Type", available_crops)
    
    # Area selection for selected crop
    crop_areas = sorted(main_df[main_df['crop_type'] == selected_crop]['area_id'].unique())
    selected_areas = st.sidebar.multiselect(
        "ðŸ“ Select Areas", 
        crop_areas, 
        default=crop_areas[:3] if len(crop_areas) > 3 else crop_areas
    )
    
    if not selected_areas:
        st.warning("Please select at least one area to continue.")
        return
    
    # Filter data
    filtered_df = main_df[
        (main_df['crop_type'] == selected_crop) & 
        (main_df['area_id'].isin(selected_areas))
    ]
    
    if filtered_df.empty:
        st.error("No data found for selected filters!")
        return
    
    # Get current status
    latest_data = filtered_df.loc[filtered_df.groupby(['area_id'])['date'].idxmax()]
    latest_date = latest_data['date'].max()
    
    if pd.isna(latest_date):
        st.error("Invalid date data!")
        return
    
    latest_date_str = latest_date.strftime('%Y-%m-%d')
    
    # Calculate current status
    current_ndvi = latest_data['ndvi'].mean()
    current_evi = latest_data['evi'].mean() if 'evi' in latest_data.columns else 0
    current_ndwi = latest_data['ndwi'].mean() if 'ndwi' in latest_data.columns else 0
    
    # Determine status based on crop-specific thresholds
    thresholds = analyzer.crop_thresholds[selected_crop]
    if current_ndvi >= thresholds['healthy']:
        status = "Healthy"
        status_class = "healthy"
    elif current_ndvi >= thresholds['warning']:
        status = "Warning"
        status_class = "warning"
    elif current_ndvi >= thresholds['alert']:
        status = "Alert"
        status_class = "alert"
    else:
        status = "Critical"
        status_class = "critical"
    
    # Header
    st.markdown(f"""
    <div class="farm-header">
        <div>
            <div class="farm-title">ðŸŒ± Farm Vegetation Monitor</div>
            <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                Crop: <strong>{selected_crop.title()}</strong> | 
                Areas: <strong>{len(selected_areas)} selected</strong>
            </div>
        </div>
        <div class="farm-location">{analyzer.farm_location['name']}</div>
        <div style="text-align: right;">
            <div style="font-size: 0.9rem;">Last Updated: {latest_date_str}</div>
            <div class="status-badge status-{status_class}">Status: {status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "ðŸ“Š Overview", 
        "ðŸ“ˆ Model Forecast", 
        "ðŸš¨ Alerts & Actions", 
        "ðŸ—ºï¸ Spatial Analysis", 
        "ðŸ”¬ Z-Score Anomalies",
        "ðŸ¤– Model Comparison"  # NEW TAB
    ])
    
    with tab1:
        # Current metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h4>ðŸŒ± NDVI Status</h4>
                <h2 style="color: {'#28a745' if status == 'Healthy' else '#ffc107' if status == 'Warning' else '#dc3545'};">
                    {current_ndvi:.3f}
                </h2>
                <p>{status}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h4>ðŸŒ¿ EVI Value</h4>
                <h2>{current_evi:.3f}</h2>
                <p>Enhanced Vegetation</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h4>ðŸ’§ NDWI Value</h4>
                <h2>{current_ndwi:.3f}</h2>
                <p>Water Content</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            # Show thresholds for selected crop
            st.markdown(f"""
            <div class="metric-card">
                <h4>ðŸ“Š {selected_crop.title()} Thresholds</h4>
                <p style="color: green;">Healthy: â‰¥{thresholds['healthy']:.2f}</p>
                <p style="color: orange;">Warning: â‰¥{thresholds['warning']:.2f}</p>
                <p style="color: red;">Alert: â‰¥{thresholds['alert']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Time series overview
        st.subheader(f"ðŸ“ˆ {selected_crop.title()} NDVI Time Series")
        
        # Aggregate by date for overview
        daily_avg = filtered_df.groupby('date').agg({
            'ndvi': ['mean', 'std'],
            'evi': 'mean',
            'ndwi': 'mean'
        }).reset_index()
        
        daily_avg.columns = ['date', 'ndvi_mean', 'ndvi_std', 'evi_mean', 'ndwi_mean']
        
        # Plot with thresholds
        fig = px.line(daily_avg, x='date', y='ndvi_mean', 
                     title=f'NDVI Trends for {selected_crop.title()}')
        
        # Add threshold lines
        fig.add_hline(y=thresholds['healthy'], line_dash="dash", line_color="green", 
                     annotation_text="Healthy Threshold")
        fig.add_hline(y=thresholds['warning'], line_dash="dash", line_color="orange", 
                     annotation_text="Warning Threshold")
        fig.add_hline(y=thresholds['alert'], line_dash="dash", line_color="red", 
                     annotation_text="Alert Threshold")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Health distribution
        st.subheader("ðŸ¥ Health Distribution by Area")
        
        health_data = []
        for area in selected_areas:
            area_latest = latest_data[latest_data['area_id'] == area]
            if not area_latest.empty:
                area_ndvi = area_latest['ndvi'].iloc[0]
                health, icon = analyzer.analyze_vegetation_health(area_ndvi, selected_crop)
                
                health_data.append({
                    'Area': area,
                    'NDVI': area_ndvi,
                    'Health': health,
                    'Crop': selected_crop
                })
        
        if health_data:
            health_df = pd.DataFrame(health_data)
            fig_health = px.bar(health_df, x='Area', y='NDVI', color='Health',
                               color_discrete_map={
                                   'Healthy': '#28a745',
                                   'Warning': '#ffc107',
                                   'Alert': '#fd7e14',
                                   'Critical': '#dc3545'
                               })
            st.plotly_chart(fig_health, use_container_width=True)
    
    with tab2:
        st.header("ðŸ“ˆ Vegetation Forecasting")
        st.info("Simple trend-based forecasting for vegetation health prediction")
        
        if len(daily_avg) > 6:  # Need sufficient data for modeling
            # Fit simple forecast model
            with st.spinner("Generating forecast..."):
                model, forecast = analyzer.fit_simple_forecast(daily_avg, periods=12)
            
            if model and forecast is not None:
                # Plot historical + forecast
                fig = go.Figure()
                
                # Historical data
                fig.add_trace(go.Scatter(
                    x=daily_avg['date'], y=daily_avg['ndvi_mean'],
                    mode='lines+markers', name='Historical NDVI',
                    line=dict(color='blue')
                ))
                
                # Forecast
                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat'],
                    mode='lines', name='Forecast',
                    line=dict(color='red', dash='dash')
                ))
                
                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat_upper'],
                    mode='lines', line=dict(width=0), showlegend=False
                ))
                fig.add_trace(go.Scatter(
                    x=forecast['ds'], y=forecast['yhat_lower'],
                    mode='lines', line=dict(width=0), 
                    fill='tonexty', fillcolor='rgba(255,0,0,0.2)',
                    name='95% Confidence Interval'
                ))
                
                # Add threshold lines
                fig.add_hline(y=thresholds['healthy'], line_dash="dash", line_color="green")
                fig.add_hline(y=thresholds['warning'], line_dash="dash", line_color="orange")
                fig.add_hline(y=thresholds['alert'], line_dash="dash", line_color="red")
                
                fig.update_layout(
                    title=f'12-Month Forecast for {selected_crop.title()}',
                    xaxis_title='Date',
                    yaxis_title='NDVI',
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Forecast summary
                avg_forecast = forecast['yhat'].mean()
                st.markdown(f"""
                ### ðŸ“Š Forecast Summary
                - **Average Predicted NDVI:** {avg_forecast:.3f}
                - **Forecast Period:** 12 months
                - **Model Type:** Linear trend + seasonal components
                """)
            else:
                st.error("Unable to generate forecast with available data")
        else:
            st.warning("Insufficient data for forecasting. Need at least 6 months of data.")
    
    with tab3:
        st.header("ðŸš¨ Real-time Alerts & Recommended Actions")
        
        # Get current date and status
        current_date = datetime.now().strftime('%Y-%m-%d')
        st.info(f"ðŸ“… **Alert Status for {current_date}** - Based on latest satellite data from {latest_date_str}")
        
        # Display current values with proper context
        col1, col2, col3 = st.columns(3)
        
        with col1:
            trend = "â†—ï¸" if current_ndvi > 0.5 else "â†˜ï¸" if current_ndvi < 0.3 else "â†’"
            st.metric(
                "ðŸŒ± NDVI Current", 
                f"{current_ndvi:.3f}",
                delta=f"{trend} {status.lower()}"
            )
        
        with col2:
            st.metric(
                "ðŸŒ¿ EVI Current", 
                f"{current_evi:.3f}",
                delta="Enhanced Vegetation"
            )
        
        with col3:
            water_status = "High" if current_ndwi > 0.2 else "Low" if current_ndwi < -0.2 else "Normal"
            st.metric(
                "ðŸ’§ NDWI Current", 
                f"{current_ndwi:.3f}",
                delta=f"Water: {water_status}"
            )
        
        # Alert level and recommendations
        st.subheader("ðŸŽ¯ Recommended Actions")
        
        if status == "Critical":
            st.error("ðŸ”´ **CRITICAL ALERT** - Immediate Action Required")
            st.markdown("""
            **Immediate Actions (Next 24-48 hours):**
            - ðŸš° Emergency irrigation - increase water supply by 50%
            - ðŸ” Field inspection for pest/disease signs
            - ðŸ§ª Soil moisture and nutrient testing
            - ðŸ“± Contact agricultural extension service
            - ðŸšœ Avoid heavy machinery operations
            """)
        
        elif status == "Alert":
            st.warning("ðŸŸ  **ALERT** - Action Needed Soon")
            st.markdown("""
            **Actions Needed (Next Week):**
            - ðŸ’§ Increase irrigation frequency by 25%
            - ðŸ” Monitor daily for stress indicators
            - ðŸ§ª Test soil conditions
            - ðŸ“Š Review weather forecasts for planning
            """)
        
        elif status == "Warning":
            st.warning("ðŸŸ¡ **WARNING** - Monitor Closely")
            st.markdown("""
            **Monitoring Actions:**
            - ðŸ‘ï¸ Daily visual field inspections
            - ðŸ“Š Continue current irrigation schedule
            - ðŸŒ¡ï¸ Monitor weather conditions closely
            - ðŸ“ˆ Track NDVI trends weekly
            """)
        
        else:
            st.success("ðŸŸ¢ **HEALTHY** - Continue Current Management")
            st.markdown("""
            **Maintenance Actions:**
            - âœ… Continue current crop management practices
            - ðŸ“… Regular monitoring schedule (weekly)
            - ðŸŒ± Optimal conditions for growth
            - ðŸ“ˆ Consider this as baseline for future comparisons
            """)
        
        # Area-specific alerts
        st.subheader("ðŸ“ Area-Specific Status")
        
        for area in selected_areas:
            area_data = latest_data[latest_data['area_id'] == area]
            if not area_data.empty:
                area_ndvi = area_data['ndvi'].iloc[0]
                area_evi = area_data['evi'].iloc[0] if 'evi' in area_data.columns else 0
                area_ndwi = area_data['ndwi'].iloc[0] if 'ndwi' in area_data.columns else 0
                
                # Determine area status
                area_health, area_icon = analyzer.analyze_vegetation_health(area_ndvi, selected_crop)
                
                with st.expander(f"{area_icon} {area} - {area_health} (NDVI: {area_ndvi:.3f})"):
                    col1, col2, col3 = st.columns(3)
                    col1.metric("NDVI", f"{area_ndvi:.3f}")
                    col2.metric("EVI", f"{area_evi:.3f}")
                    col3.metric("NDWI", f"{area_ndwi:.3f}")
                    
                    if area_health in ["Alert", "Critical"]:
                        if area_ndwi < -0.3:
                            st.error("ðŸ’§ Drought stress detected - Priority irrigation needed")
                        elif area_ndwi > 0.3:
                            st.warning("ðŸŒŠ Potential waterlogging - Check drainage")
                        else:
                            st.error("ðŸŒ± Poor vegetation health - Investigate causes")
    
    with tab4:
        st.header("ðŸ—ºï¸ Spatial Analysis")
        
        # Farm location details
        st.subheader("ðŸ“ Farm Location & Coverage")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"""
            **ðŸ›ï¸ Farm Details:**
            - **Name:** {analyzer.farm_location['name']}
            - **Address:** {analyzer.farm_location['address']}
            - **Coordinates:** {analyzer.farm_location['latitude']:.4f}Â°N, {analyzer.farm_location['longitude']:.4f}Â°W
            - **Total Area:** {analyzer.farm_location['area_km2']} kmÂ²
            - **Selected Crop:** {selected_crop.title()}
            - **Monitoring Points:** {len(filtered_df['point_id'].unique())} active sensors
            """)
        
        with col2:
            # Area summary by crop
            crop_summary = main_df.groupby('crop_type').agg({
                'area_id': 'nunique',
                'point_id': 'nunique',
                'ndvi': 'mean'
            }).round(3)
            crop_summary.columns = ['Areas', 'Points', 'Avg_NDVI']
            st.dataframe(crop_summary)
        
        # Time series by area
        st.subheader(f"ðŸ“ˆ Area Comparison - {selected_crop.title()}")
        
        area_comparison = filtered_df.groupby(['date', 'area_id'])['ndvi'].mean().reset_index()
        
        fig_areas = px.line(area_comparison, x='date', y='ndvi', color='area_id',
                           title=f'NDVI Trends by Area - {selected_crop.title()}')
        
        # Add threshold lines
        fig_areas.add_hline(y=thresholds['healthy'], line_dash="dash", line_color="green")
        fig_areas.add_hline(y=thresholds['warning'], line_dash="dash", line_color="orange")
        fig_areas.add_hline(y=thresholds['alert'], line_dash="dash", line_color="red")
        
        st.plotly_chart(fig_areas, use_container_width=True)
        
        # Point ID explanation
        st.subheader("ðŸŽ¯ Understanding Point IDs")
        st.info(f"""
        **Point ID System:** Each point ID represents a specific monitoring location within the farm:
        - **Total Points:** {len(main_df['point_id'].unique())} monitoring locations
        - **Wheat Areas:** Points {main_df[main_df['crop_type']=='wheat']['point_id'].min()}-{main_df[main_df['crop_type']=='wheat']['point_id'].max()}
        - **Barley Areas:** Points {main_df[main_df['crop_type']=='barley']['point_id'].min()}-{main_df[main_df['crop_type']=='barley']['point_id'].max()}
        - **Purpose:** Track vegetation health at precise locations for targeted management
        """)

        # Add this to your dashboard.py in the appropriate tab (e.g., Spatial View)


        # Load your coordinates data (ensure crop_type column exists)
        df = pd.read_csv(r"E:\vegitation analysis\data\all_index_coordinates.csv")

        # If crop_type is not present, you need to merge with another DataFrame that has crop_type info for each point

        # Let user select crop type
        crop_types = df['crop_type'].unique()
        selected_crop = st.selectbox("Select crop type to view distribution:", crop_types)

        # Filter data by selected crop
        filtered_df = df[df['crop_type'] == selected_crop]

        st.subheader(f"Spatial Distribution of {selected_crop.title()} Points")

        # Show map using Pydeck
        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/satellite-streets-v12",
            initial_view_state=pdk.ViewState(
                latitude=filtered_df['latitude'].mean(),
                longitude=filtered_df['longitude'].mean(),
                zoom=13,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=filtered_df,
                    get_position='[longitude, latitude]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=10,
                    pickable=True,
                ),
            ],
            tooltip={"text": "Lat: {latitude}\nLon: {longitude}\nValue: {value}"}
        ))
    
    with tab5:
        st.header("ðŸ“Š Z-Score Anomaly Detection")
        
        st.markdown("""
        ### ðŸ§® What is Z-Score Anomaly Detection?
        
        **Z-Score** measures how many standard deviations a data point is from the mean:
        - **Z > 2.5 or Z < -2.5:** Considered anomalous (statistically significant)
        - **Purpose:** Identify unusual vegetation patterns that may indicate stress, disease, or exceptional growth
        - **Application:** Early warning system for crop health issues
        """)
        
        # Calculate anomalies if we have enough data
        if len(filtered_df) > 50:  # Need sufficient data for anomaly detection
            with st.spinner("Calculating Z-score anomalies..."):
                anomaly_data = analyzer.calculate_z_score_anomalies(filtered_df, window_size=6)
            
            if not anomaly_data.empty:
                # Summary statistics
                total_points = len(anomaly_data)
                anomaly_count = anomaly_data['is_anomaly'].sum()
                anomaly_percent = (anomaly_count / total_points) * 100
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Data Points", total_points)
                col2.metric("Anomalies Detected", anomaly_count)
                col3.metric("Anomaly Rate", f"{anomaly_percent:.1f}%")
                
                # Anomaly visualization
                st.subheader("ðŸ” Anomaly Detection Results")
                
                fig_anomaly = px.scatter(
                    anomaly_data,
                    x='date',
                    y='value',
                    color='z_score',
                    size=anomaly_data['z_score'].abs(),
                    symbol='is_anomaly',
                    title='NDVI Anomalies Over Time (Z-Score Analysis)',
                    color_continuous_scale='RdBu',
                    hover_data={'point_id': True, 'z_score': ':.2f'}
                )
                
                # Add threshold lines for anomaly detection
                fig_anomaly.add_hline(y=thresholds['healthy'], line_dash="dash", 
                                    line_color="green", annotation_text="Healthy")
                fig_anomaly.add_hline(y=thresholds['warning'], line_dash="dash", 
                                    line_color="orange", annotation_text="Warning")
                fig_anomaly.add_hline(y=thresholds['alert'], line_dash="dash", 
                                    line_color="red", annotation_text="Alert")
                
                st.plotly_chart(fig_anomaly, use_container_width=True)
                
                # Recent anomalies
                recent_anomalies = anomaly_data[
                    (anomaly_data['is_anomaly'] == True) & 
                    (anomaly_data['date'] >= (datetime.now() - timedelta(days=90)))
                ].sort_values('date', ascending=False)
                
                if not recent_anomalies.empty:
                    st.subheader("ðŸš¨ Recent Anomalies (Last 90 Days)")
                    display_anomalies = recent_anomalies[['date', 'point_id', 'value', 'z_score']].copy()
                    display_anomalies['date'] = display_anomalies['date'].dt.strftime('%Y-%m-%d')
                    display_anomalies = display_anomalies.round(3)
                    st.dataframe(display_anomalies, use_container_width=True)
                else:
                    st.success("âœ… No recent anomalies detected in the last 90 days")
            else:
                st.warning("Could not calculate anomalies - insufficient data variation")
        else:
            st.warning("Insufficient data for reliable anomaly detection. Need more historical data.")
        
    
    with tab6:
        st.header("ðŸ¤– Model Comparison: Prophet vs ARIMA")
        st.markdown("""
        This section compares two time series forecasting models:
        - **Prophet** (additive trend + seasonality)
        - **ARIMA** (AutoRegressive Integrated Moving Average)
        """)
        
        # Prepare data
        ts = daily_avg[['date', 'ndvi_mean']].dropna()
        ts = ts.set_index('date')
        ts = ts.asfreq('M')
        ts = ts.fillna(method='ffill')

        # Only proceed if enough data for modeling
        if len(ts.dropna()) < 2:
            st.warning("Not enough data for model comparison. At least 2 non-NaN monthly values are required.")
        else:
            # Prophet Model
            prophet_df = ts.reset_index().rename(columns={'date': 'ds', 'ndvi_mean': 'y'})
            prophet_model = Prophet(yearly_seasonality=True)
            prophet_model.fit(prophet_df)
            future = prophet_model.make_future_dataframe(periods=12, freq='M')
            prophet_forecast = prophet_model.predict(future)

            # ARIMA Model
            arima_model = sm.tsa.ARIMA(ts['ndvi_mean'], order=(1,1,1), seasonal_order=(1,1,1,12))
            arima_result = arima_model.fit()
            arima_forecast = arima_result.get_forecast(steps=12)
            arima_pred = arima_forecast.predicted_mean
            arima_ci = arima_forecast.conf_int()

            # Metrics calculation
            def calc_metrics(actual, pred):
                mae = mean_absolute_error(actual, pred)
                rmse = np.sqrt(mean_squared_error(actual, pred))
                smape = np.mean(2 * np.abs(pred - actual) / (np.abs(actual) + np.abs(pred))) * 100
                return mae, rmse, smape

            # Use last 12 months for validation
            if len(ts) > 24:
                actual = ts['ndvi_mean'][-12:]
                prophet_pred = prophet_forecast['yhat'][-24:-12].values
                arima_pred_val = arima_result.predict(start=len(ts)-12, end=len(ts)-1)
                prophet_mae, prophet_rmse, prophet_smape = calc_metrics(actual, prophet_pred)
                arima_mae, arima_rmse, arima_smape = calc_metrics(actual, arima_pred_val)
            else:
                prophet_mae = prophet_rmse = prophet_smape = arima_mae = arima_rmse = arima_smape = np.nan

            # Show metrics
            st.subheader("ðŸ“Š Performance Metrics (last 12 months)")
            metrics_df = pd.DataFrame({
                "Model": ["Prophet", "ARIMA"],
                "MAE": [prophet_mae, arima_mae],
                "RMSE": [prophet_rmse, arima_rmse],
                "sMAPE (%)": [prophet_smape, arima_smape]
            })
            st.dataframe(metrics_df.round(3), use_container_width=True)
            st.markdown("""
            **Quality Thresholds:**  
            - MAE < 0.1 (Excellent), < 0.2 (Good)  
            - RMSE < 0.15 (Excellent), < 0.25 (Good)  
            - sMAPE < 10% (Excellent), < 20% (Good)
            """)

            # Confidence interval width
            st.subheader("ðŸ“ Confidence Interval Width (Model Reliability)")
            prophet_ci_width = (prophet_forecast['yhat_upper'][-12:] - prophet_forecast['yhat_lower'][-12:]).mean()
            arima_ci_width = (arima_ci['upper ndvi_mean'] - arima_ci['lower ndvi_mean']).mean()
            st.write(f"Prophet CI Avg Width: {prophet_ci_width:.3f}")
            st.write(f"ARIMA CI Avg Width: {arima_ci_width:.3f}")

            # Plot comparison
            st.subheader("ðŸ“ˆ Forecast Comparison")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=ts.index, y=ts['ndvi_mean'], mode='lines+markers', name='Actual'))
            fig.add_trace(go.Scatter(x=prophet_forecast['ds'], y=prophet_forecast['yhat'], mode='lines', name='Prophet Forecast'))
            fig.add_trace(go.Scatter(x=arima_pred.index, y=arima_pred, mode='lines', name='ARIMA Forecast'))
            fig.add_trace(go.Scatter(
                x=prophet_forecast['ds'], y=prophet_forecast['yhat_upper'],
                mode='lines', line=dict(width=0), showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=prophet_forecast['ds'], y=prophet_forecast['yhat_lower'],
                mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(0,100,255,0.1)', name='Prophet CI'
            ))
            fig.add_trace(go.Scatter(
                x=arima_ci.index, y=arima_ci['upper ndvi_mean'],
                mode='lines', line=dict(width=0), showlegend=False
            ))
            fig.add_trace(go.Scatter(
                x=arima_ci.index, y=arima_ci['lower ndvi_mean'],
                mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(255,0,0,0.1)', name='ARIMA CI'
            ))
            fig.update_layout(title="Prophet vs ARIMA NDVI Forecast", xaxis_title="Date", yaxis_title="NDVI")
            st.plotly_chart(fig, use_container_width=True)

            st.write("Monthly NDVI points available:", len(ts.dropna()))
            st.write(ts)

            # Crop-specific thresholds
            st.subheader("ðŸŒ¾ Crop-Specific Thresholds (10th Percentile Based)")
            st.write(analyzer.crop_thresholds)

            # Location info
            st.subheader("ðŸ“ Location Information")
            st.write(analyzer.farm_location)

            # Enhanced DSR Documentation
            st.header("ðŸ“š Enhanced DSR Documentation")
            st.markdown("""
            **Design Science Research (DSR) Framework:**  
            - **Design:** Dashboard, alerting, forecasting, spatial analysis  
            - **Science:** Remote sensing, time series, anomaly detection  
            - **Research:** Early stress prediction, model comparison, threshold optimization  
            - **Evaluation:** MAE, RMSE, sMAPE, CI width  
            - **Communication:** Interactive dashboard for stakeholders  
            """)

    # Footer with data source info
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        <strong>ðŸ›°ï¸ Data Source:</strong> Sentinel-2 Satellite Imagery (COPERNICUS/S2_SR_HARMONIZED) | 
        <strong>ðŸ“ Location:</strong> {analyzer.farm_location['name']} ({analyzer.farm_location['area_km2']} kmÂ²)<br>
        <strong>ðŸŒ¾ Crops:</strong> Wheat & Barley | 
        <strong>â° Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>ðŸ”¬ Method:</strong> DSR Framework | <strong>ðŸ“Š Models:</strong> Trend + Seasonal | 
        <strong>ðŸŽ¯ Thresholds:</strong> Crop-specific percentile-based<br>
        <strong>ðŸ“ˆ Data Points:</strong> {len(main_df)} records | <strong>ðŸŽ¯ Monitoring Points:</strong> {len(main_df['point_id'].unique())} locations
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()