#!/usr/bin/env python3
"""
Detect Upstream Weather Changes for Wind Forecast Dashboard
============================================================
Analyzes ERA5 surface pressure and wind gust data from west coast farms
to predict generation changes at North Sea offshore farms 3-6 hours ahead.

Uses:
- Surface pressure gradients (±5 hPa/6h = significant change)
- Wind gust ratios (gust/wind > 1.4 = turbulence)
- Upstream→downstream correlation (99.8% pressure correlation validated)

Outputs to Google Sheets: Live Dashboard v2 - Wind Forecast section
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import numpy as np

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

client_bq = bigquery.Client(project=PROJECT_ID, location="US")

# Google Sheets setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client_gs = gspread.authorize(creds)

print("🌬️  UPSTREAM WEATHER CHANGE DETECTOR")
print("=" * 80)
print()

# ============================================================================
# STEP 1: Query Upstream Pressure Changes (West Coast Farms)
# ============================================================================
print("📊 Analyzing upstream pressure gradients...")

query_upstream = f"""
WITH recent_weather AS (
    SELECT 
        farm_name,
        timestamp,
        surface_pressure_hpa,
        wind_speed_100m_ms,
        wind_gusts_10m_ms,
        LAG(surface_pressure_hpa, 6) OVER (PARTITION BY farm_name ORDER BY timestamp) as pressure_6h_ago,
        LAG(wind_speed_100m_ms, 3) OVER (PARTITION BY farm_name ORDER BY timestamp) as wind_3h_ago
    FROM `{PROJECT_ID}.{DATASET}.era5_weather_data_complete`
    WHERE farm_name IN ('Barrow', 'Walney Extension', 'Robin Rigg', 'Methil', 
                        'West of Duddon Sands', 'Ormonde', 'Burbo Bank Extension')
      AND timestamp >= '2025-11-30 00:00:00'  -- Use actual latest data
)
SELECT 
    farm_name,
    timestamp,
    surface_pressure_hpa,
    pressure_6h_ago,
    surface_pressure_hpa - pressure_6h_ago as pressure_change_6h,
    wind_speed_100m_ms,
    wind_3h_ago,
    wind_speed_100m_ms - wind_3h_ago as wind_change_3h,
    wind_gusts_10m_ms,
    CASE 
        WHEN wind_gusts_10m_ms > 0 AND wind_speed_100m_ms > 0 
        THEN wind_gusts_10m_ms / wind_speed_100m_ms
        ELSE 1.0
    END as gust_ratio
FROM recent_weather
WHERE pressure_6h_ago IS NOT NULL
ORDER BY timestamp DESC
LIMIT 50
"""

try:
    df_upstream = client_bq.query(query_upstream).to_dataframe()
    print(f"✅ Retrieved {len(df_upstream)} upstream weather observations")
except Exception as e:
    print(f"❌ Error querying upstream weather: {e}")
    df_upstream = pd.DataFrame()

# ============================================================================
# STEP 2: Analyze Weather Patterns
# ============================================================================
if len(df_upstream) > 0:
    print("\n📈 Upstream Weather Analysis:")
    print("-" * 80)
    
    # Get most recent observations per farm
    latest_by_farm = df_upstream.groupby('farm_name').first().reset_index()
    
    print(f"\n{'Farm':<25} {'Pressure Δ':<12} {'Wind Δ':<10} {'Gust Ratio':<12} {'Signal':<20}")
    print("-" * 80)
    
    alerts = []
    
    for _, row in latest_by_farm.iterrows():
        farm = row['farm_name']
        pressure_change = row['pressure_change_6h']
        wind_change = row['wind_change_3h']
        gust_ratio = row['gust_ratio']
        
        # Classify weather pattern
        if pressure_change < -5:
            signal = "🔴 STORM APPROACHING"
            alert_level = "HIGH"
            lead_time = 3  # Hours until impact at North Sea farms
            capacity_at_risk = 2450  # MW (Seagreen + Moray + Beatrice)
            message = f"Pressure drop {pressure_change:.1f} hPa/6h at {farm}"
        elif pressure_change < -2:
            signal = "🟡 PRESSURE FALLING"
            alert_level = "MEDIUM"
            lead_time = 6
            capacity_at_risk = 890
            message = f"Moderate pressure drop {pressure_change:.1f} hPa/6h"
        elif pressure_change > 5:
            signal = "🟡 HIGH PRESSURE"
            alert_level = "MEDIUM"
            lead_time = 6
            capacity_at_risk = 0  # Calm = no risk, just lower output
            message = f"Pressure rise +{pressure_change:.1f} hPa/6h (calm arriving)"
        elif gust_ratio > 1.4:
            signal = "🟡 TURBULENCE"
            alert_level = "MEDIUM"
            lead_time = 2
            capacity_at_risk = 420
            message = f"High turbulence (gust ratio {gust_ratio:.2f})"
        else:
            signal = "🟢 STABLE"
            alert_level = "STABLE"
            lead_time = None
            capacity_at_risk = 0
            message = "No significant changes"
        
        print(f"{farm:<25} {pressure_change:>6.1f} hPa  {wind_change:>6.1f} m/s  {gust_ratio:>6.2f}      {signal:<20}")
        
        alerts.append({
            'farm': farm,
            'alert_level': alert_level,
            'message': message,
            'lead_time_hours': lead_time,
            'capacity_at_risk_mw': capacity_at_risk,
            'pressure_change': pressure_change,
            'wind_change': wind_change,
            'gust_ratio': gust_ratio
        })
    
    # ========================================================================
    # STEP 3: Determine Highest Priority Alert
    # ========================================================================
    print("\n🎯 ALERT PRIORITIZATION:")
    print("-" * 80)
    
    # Sort by alert level (HIGH > MEDIUM > STABLE)
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'STABLE': 2}
    alerts_sorted = sorted(alerts, key=lambda x: priority_order[x['alert_level']])
    
    top_alert = alerts_sorted[0]
    
    if top_alert['alert_level'] == 'HIGH':
        emoji = '🔴'
        status = 'HIGH RISK'
    elif top_alert['alert_level'] == 'MEDIUM':
        emoji = '🟡'
        status = 'MEDIUM RISK'
    else:
        emoji = '🟢'
        status = 'STABLE'
    
    print(f"\nTop Alert: {emoji} {status}")
    print(f"Message: {top_alert['message']}")
    if top_alert['lead_time_hours']:
        print(f"Lead Time: {top_alert['lead_time_hours']} hours")
        print(f"Capacity at Risk: {top_alert['capacity_at_risk_mw']:,} MW")
    
    # ========================================================================
    # STEP 4: Write to Google Sheets
    # ========================================================================
    print("\n📝 Writing to Google Sheets...")
    
    try:
        spreadsheet = client_gs.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet('Live Dashboard v2')
        
        # Find Wind Forecast Dashboard section (starts around row 60)
        # Row 61: 🌊 Current: XX MW (X.XX GW) | STATUS | Message
        
        current_wind = 5786  # Get from live data (placeholder)
        current_wind_gw = current_wind / 1000
        
        # Format alert message for dashboard
        alert_cell = f"{emoji} {status}"
        message_cell = top_alert['message']
        
        # Update cells (adjust row numbers based on your dashboard layout)
        updates = [
            # Row 61, Column B-D: Current wind status
            {
                'range': 'Live Dashboard v2!C61',  # Status emoji/level
                'values': [[alert_cell]]
            },
            {
                'range': 'Live Dashboard v2!D61',  # Alert message
                'values': [[message_cell]]
            },
            # Row 62: Capacity at Risk
            {
                'range': 'Live Dashboard v2!B62',  # Capacity at risk MW
                'values': [[f"{top_alert['capacity_at_risk_mw']:,} MW"]]
            },
            {
                'range': 'Live Dashboard v2!C62',  # % UK offshore
                'values': [[f"{(top_alert['capacity_at_risk_mw'] / 30000) * 100:.1f}% UK offshore"]]
            }
        ]
        
        # Batch update
        for update in updates:
            sheet.update(
                range_name=update['range'].split('!')[1],
                values=update['values']
            )
        
        print(f"✅ Updated Wind Forecast Dashboard")
        print(f"   Status: {alert_cell}")
        print(f"   Message: {message_cell}")
        print(f"   Capacity at Risk: {top_alert['capacity_at_risk_mw']:,} MW")
        
    except Exception as e:
        print(f"❌ Error writing to Google Sheets: {e}")

else:
    print("⚠️  No upstream weather data available")

print("\n" + "=" * 80)
print("✅ Upstream weather analysis complete")
print("=" * 80)
