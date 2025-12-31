#!/usr/bin/env python3
"""
Real-time wind generation forecasting system.
Uses trained power curve models + ECMWF/NESO forecasts to predict generation.
Identifies arbitrage opportunities when our prediction differs from NESO.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
import joblib
import os
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# CONFIGURATION
# -------------------------

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

MODEL_DIR = "models/wind_power_curves"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
WORKSHEET_NAME = "Wind Arbitrage Signals"

# -------------------------
# LOAD TRAINED MODELS
# -------------------------

def load_models():
    """Load all trained power curve models."""
    models = {}
    
    if not os.path.exists(MODEL_DIR):
        print(f"❌ Model directory not found: {MODEL_DIR}")
        return models
    
    model_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.joblib')]
    
    for model_file in model_files:
        farm_name = model_file.replace('.joblib', '').replace('_', ' ')
        model_path = os.path.join(MODEL_DIR, model_file)
        models[farm_name] = joblib.load(model_path)
        print(f"  ✅ Loaded: {farm_name}")
    
    return models

# -------------------------
# FETCH LATEST FORECASTS
# -------------------------

def fetch_neso_forecast():
    """Fetch latest NESO wind forecast."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    query = f"""
    SELECT
        startTime,
        publishTime,
        generation as neso_forecast_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_windfor_iris`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 6 HOUR)
      AND startTime >= CURRENT_TIMESTAMP()
      AND startTime <= TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY publishTime DESC, startTime
    """
    
    df = client.query(query).to_dataframe()
    
    # Keep only latest publish time for each forecast time
    df = df.sort_values('publishTime', ascending=False).drop_duplicates(
        subset=['startTime'], keep='first'
    )
    
    return df

def fetch_latest_weather():
    """Fetch latest weather data (Open-Meteo or ECMWF if available)."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Try ECMWF first (if table exists and has data)
    try:
        query = f"""
        SELECT
            farm_name,
            valid_time,
            wind_speed_ms as wind_speed_100m,
            EXTRACT(HOUR FROM valid_time) as hour_of_day,
            EXTRACT(MONTH FROM valid_time) as month,
            EXTRACT(DAYOFWEEK FROM valid_time) as day_of_week
        FROM `{PROJECT_ID}.{DATASET}.ecmwf_wind_latest`
        WHERE valid_time >= CURRENT_TIMESTAMP()
          AND valid_time <= TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
        ORDER BY farm_name, valid_time
        """
        df = client.query(query).to_dataframe()
        
        if len(df) > 0:
            print(f"  ✅ Using ECMWF forecast: {len(df)} rows")
            return df, 'ECMWF'
    except:
        pass
    
    # Fallback: Use latest Open-Meteo historical data as proxy
    print("  ⚠️  ECMWF not available, using latest historical weather")
    query = f"""
    SELECT
        farm_name,
        time_utc as valid_time,
        wind_speed_100m,
        wind_direction_10m,
        wind_gusts_10m,
        EXTRACT(HOUR FROM time_utc) as hour_of_day,
        EXTRACT(MONTH FROM time_utc) as month,
        EXTRACT(DAYOFWEEK FROM time_utc) as day_of_week
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE time_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    ORDER BY farm_name, time_utc DESC
    LIMIT 1000
    """
    df = client.query(query).to_dataframe()
    return df, 'Historical'

# -------------------------
# MAKE PREDICTIONS
# -------------------------

def predict_generation(models, weather_df):
    """
    Use trained models to predict generation for each farm.
    
    Args:
        models: Dict of {farm_name: model}
        weather_df: DataFrame with weather features
    
    Returns:
        DataFrame with predictions
    """
    predictions = []
    
    for farm_name, model in models.items():
        farm_weather = weather_df[weather_df['farm_name'] == farm_name].copy()
        
        if len(farm_weather) == 0:
            print(f"  ⚠️  No weather data for {farm_name}")
            continue
        
        # Prepare features (match training features)
        features = [
            'wind_speed_100m',
            'wind_direction_10m',
            'hour_of_day',
            'month',
            'day_of_week',
            'wind_gusts_10m'
        ]
        
        # Fill missing columns
        for feat in features:
            if feat not in farm_weather.columns:
                farm_weather[feat] = 0
        
        X = farm_weather[features].fillna(0)
        
        # Predict
        farm_weather['predicted_generation_mw'] = model.predict(X)
        farm_weather['predicted_generation_mw'] = farm_weather['predicted_generation_mw'].clip(lower=0)
        
        predictions.append(farm_weather[['farm_name', 'valid_time', 'predicted_generation_mw', 'wind_speed_100m']])
    
    if predictions:
        return pd.concat(predictions, ignore_index=True)
    return pd.DataFrame()

# -------------------------
# IDENTIFY ARBITRAGE OPPORTUNITIES
# -------------------------

def identify_arbitrage(predictions_df, neso_forecast_df):
    """
    Compare our predictions with NESO forecast.
    Opportunities: Our prediction significantly differs from NESO.
    """
    # Aggregate our predictions by settlement period
    predictions_df['settlementDate'] = predictions_df['valid_time'].dt.date
    predictions_df['hour'] = predictions_df['valid_time'].dt.hour
    predictions_df['settlementPeriod'] = (predictions_df['hour'] * 2) + 1  # Simplified
    
    our_forecast = predictions_df.groupby(['settlementDate', 'settlementPeriod']).agg({
        'predicted_generation_mw': 'sum'
    }).reset_index()
    our_forecast.columns = ['settlementDate', 'settlementPeriod', 'our_forecast_mw']
    
    # Join with NESO
    neso_forecast_df['settlementDate'] = neso_forecast_df['settlementDate'].dt.date
    
    comparison = our_forecast.merge(
        neso_forecast_df[['settlementDate', 'settlementPeriod', 'neso_forecast_mw']],
        on=['settlementDate', 'settlementPeriod'],
        how='inner'
    )
    
    # Calculate difference
    comparison['forecast_diff_mw'] = comparison['our_forecast_mw'] - comparison['neso_forecast_mw']
    comparison['forecast_diff_pct'] = (comparison['forecast_diff_mw'] / comparison['neso_forecast_mw']) * 100
    
    # Flag significant differences (>5% or >500 MW)
    comparison['is_opportunity'] = (
        (abs(comparison['forecast_diff_pct']) > 5) |
        (abs(comparison['forecast_diff_mw']) > 500)
    )
    
    # Trading signal
    comparison['signal'] = 'HOLD'
    comparison.loc[comparison['forecast_diff_mw'] > 500, 'signal'] = 'SHORT'  # We predict MORE wind → prices DOWN
    comparison.loc[comparison['forecast_diff_mw'] < -500, 'signal'] = 'LONG'   # We predict LESS wind → prices UP
    
    return comparison

# -------------------------
# UPDATE DASHBOARD
# -------------------------

def update_dashboard(arbitrage_df):
    """Update Google Sheets with arbitrage signals."""
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
        gc = gspread.authorize(creds)
        
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Try to get existing worksheet or create new
        try:
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except:
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=10)
        
        # Prepare data
        output = arbitrage_df[arbitrage_df['is_opportunity']].sort_values('forecast_diff_mw', ascending=False).head(20)
        
        # Format for sheets
        data = [['Date', 'SP', 'NESO (MW)', 'Our Forecast (MW)', 'Diff (MW)', 'Diff (%)', 'Signal', 'Updated']]
        
        for _, row in output.iterrows():
            data.append([
                str(row['settlementDate']),
                int(row['settlementPeriod']),
                f"{row['neso_forecast_mw']:.0f}",
                f"{row['our_forecast_mw']:.0f}",
                f"{row['forecast_diff_mw']:.0f}",
                f"{row['forecast_diff_pct']:.1f}%",
                row['signal'],
                datetime.now().strftime('%Y-%m-%d %H:%M')
            ])
        
        # Update sheet
        worksheet.clear()
        worksheet.update('A1', data)
        
        print(f"  ✅ Updated {WORKSHEET_NAME} with {len(output)} signals")
        
    except Exception as e:
        print(f"  ❌ Dashboard update failed: {e}")

# -------------------------
# MAIN EXECUTION
# -------------------------

def main():
    print("=" * 70)
    print("Real-Time Wind Generation Forecasting")
    print("=" * 70)
    
    # Load models
    print("\n📦 Loading trained models...")
    models = load_models()
    
    if not models:
        print("❌ No models found! Run build_wind_power_curves.py first")
        return 1
    
    print(f"✅ Loaded {len(models)} farm models")
    
    # Fetch NESO forecast
    print("\n📡 Fetching NESO wind forecast...")
    neso_df = fetch_neso_forecast()
    print(f"  ✅ NESO forecast: {len(neso_df)} settlement periods")
    
    # Fetch weather
    print("\n🌤️  Fetching latest weather data...")
    weather_df, source = fetch_latest_weather()
    print(f"  ✅ Weather source: {source}")
    
    # Make predictions
    print("\n🔮 Predicting wind generation...")
    predictions_df = predict_generation(models, weather_df)
    
    if len(predictions_df) == 0:
        print("❌ No predictions generated")
        return 1
    
    print(f"  ✅ Predictions: {len(predictions_df)} hourly values")
    print(f"  ✅ Total predicted: {predictions_df['predicted_generation_mw'].sum():.0f} MWh")
    
    # Identify arbitrage
    print("\n💰 Identifying arbitrage opportunities...")
    arbitrage_df = identify_arbitrage(predictions_df, neso_df)
    
    opportunities = arbitrage_df[arbitrage_df['is_opportunity']]
    print(f"  ✅ Found {len(opportunities)} potential arbitrage opportunities")
    
    if len(opportunities) > 0:
        print(f"\n  🔝 Top 5 Opportunities:")
        for _, row in opportunities.head(5).iterrows():
            signal_emoji = "📈" if row['signal'] == 'LONG' else "📉"
            print(f"     {signal_emoji} {row['settlementDate']} SP{row['settlementPeriod']}: "
                  f"{row['signal']} ({row['forecast_diff_mw']:.0f} MW diff)")
    
    # Update dashboard
    print("\n📊 Updating Google Sheets dashboard...")
    update_dashboard(arbitrage_df)
    
    print("\n✅ Real-time forecasting complete!")
    
    return 0

if __name__ == "__main__":
    exit(main())
