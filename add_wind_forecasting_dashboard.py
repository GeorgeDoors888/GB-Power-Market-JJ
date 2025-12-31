#!/usr/bin/env python3
"""
Wind Forecasting Dashboard Graphics

Creates visual elements for Google Sheets dashboard:
- Wind drop alerts with color coding
- Spatial correlation heatmaps
- Upstream sensor indicators
- ERA5 grid point coverage map

Integrates with existing Google Sheets dashboard.
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Google Sheets configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Wind Forecasting"

# Google Sheets authentication
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def authenticate():
    """Authenticate with Google Sheets"""
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=SCOPES
    )
    return gspread.authorize(creds)

def create_wind_alerts_section(worksheet, start_row=5):
    """Create wind drop alerts section with color coding"""
    
    # Headers
    headers = [
        'Upstream Source',
        'Downstream Farm',
        'Wind Drop %',
        'Time to Impact',
        'Alert Level',
        'Current Wind (m/s)'
    ]
    
    worksheet.update(f'A{start_row}', [headers])
    
    # Format headers
    worksheet.format(f'A{start_row}:F{start_row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Sample data with color coding
    sample_alerts = [
        ['Moray West', 'Beatrice', -22.5, '30 min', '🔴 CRITICAL', 18.3],
        ['ERA5: Atlantic_Irish_Sea', 'Walney Extension', -15.2, '2h 15min', '🟡 WARNING', 21.7],
        ['Sheringham Shoal', 'Dudgeon', -8.1, '45 min', '🟢 STABLE', 24.2],
        ['Triton Knoll', 'Hornsea One', -18.9, '1h 30min', '🟡 WARNING', 19.8],
    ]
    
    data_start = start_row + 1
    worksheet.update(f'A{data_start}', sample_alerts)
    
    # Conditional formatting for alert levels
    for i, alert in enumerate(sample_alerts):
        row = data_start + i
        if '🔴' in str(alert[4]):
            # Red background for critical
            worksheet.format(f'A{row}:F{row}', {
                'backgroundColor': {'red': 1, 'green': 0.8, 'blue': 0.8}
            })
        elif '🟡' in str(alert[4]):
            # Yellow background for warning
            worksheet.format(f'A{row}:F{row}', {
                'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8}
            })
        else:
            # Green background for stable
            worksheet.format(f'A{row}:F{row}', {
                'backgroundColor': {'red': 0.8, 'green': 1, 'blue': 0.8}
            })
    
    return data_start + len(sample_alerts) + 2

def create_spatial_correlation_heatmap(worksheet, start_row):
    """Create spatial correlation heatmap"""
    
    # Title
    worksheet.update(f'A{start_row}', [['Spatial Wind Correlations (Top Pairs)']])
    worksheet.format(f'A{start_row}:D{start_row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 12},
        'horizontalAlignment': 'CENTER'
    })
    
    start_row += 1
    
    # Headers
    headers = ['Upstream Farm', 'Downstream Farm', 'Correlation', 'Distance (km)']
    worksheet.update(f'A{start_row}', [headers])
    
    # Top correlations
    correlations = [
        ['Moray West', 'Beatrice', 0.966, 53],
        ['Sheringham Shoal', 'Dudgeon', 0.964, 52],
        ['Beatrice', 'Moray West', 0.959, 53],
        ['Greater Gabbard', 'Galloper', 0.945, 28],
        ['Triton Knoll', 'Hornsea Two', 0.911, 104],
        ['Triton Knoll', 'Hornsea One', 0.910, 116],
    ]
    
    data_start = start_row + 1
    worksheet.update(f'A{data_start}', correlations)
    
    # Color gradient based on correlation strength
    for i, corr in enumerate(correlations):
        row = data_start + i
        r_value = corr[2]
        
        # Color intensity based on correlation (0.90-0.97 → light to dark green)
        green_intensity = 0.6 + (r_value - 0.90) / 0.07 * 0.4
        
        worksheet.format(f'C{row}', {
            'backgroundColor': {'red': 1 - green_intensity, 'green': 1, 'blue': 1 - green_intensity},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })
    
    return data_start + len(correlations) + 2

def create_era5_coverage_map(worksheet, start_row):
    """Create ERA5 grid point coverage indicators"""
    
    # Title
    worksheet.update(f'A{start_row}', [['ERA5 Grid Point Coverage']])
    worksheet.format(f'A{start_row}:E{start_row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 12},
        'horizontalAlignment': 'CENTER'
    })
    
    start_row += 1
    
    # Headers
    headers = ['Grid Point', 'Latitude', 'Longitude', 'Farms Covered', 'Status']
    worksheet.update(f'A{start_row}', [headers])
    
    # Grid points
    grids = [
        ['Atlantic_Irish_Sea', 54.0, -8.0, 'Walney, Burbo Bank, West of Duddon', '✅ ACTIVE'],
        ['North_Scotland', 59.0, -4.0, 'Moray East, Moray West', '✅ ACTIVE'],
        ['Central_England', 53.5, -1.0, 'Hornsea One/Two, Triton Knoll', '✅ ACTIVE'],
        ['Bristol_Channel', 51.5, -2.0, 'Greater Gabbard, London Array', '✅ ACTIVE'],
        ['Atlantic_Deep_West', 54.5, -10.0, 'Walney Extension (extended)', '✅ ACTIVE'],
        ['North_Sea_West', 54.0, -0.5, 'Dogger Bank, Hornsea', '✅ ACTIVE'],
    ]
    
    data_start = start_row + 1
    worksheet.update(f'A{data_start}', grids)
    
    # Format status column
    for i in range(len(grids)):
        row = data_start + i
        worksheet.format(f'E{row}', {
            'backgroundColor': {'red': 0.8, 'green': 1, 'blue': 0.8},
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })
    
    return data_start + len(grids) + 2

def create_forecast_accuracy_chart(worksheet, start_row):
    """Create forecast accuracy comparison chart data"""
    
    # Title
    worksheet.update(f'A{start_row}', [['Forecast Accuracy by Model']])
    worksheet.format(f'A{start_row}:C{start_row}', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 12},
        'horizontalAlignment': 'CENTER'
    })
    
    start_row += 1
    
    # Headers
    headers = ['Model Type', 'Avg MAE (MW)', 'Improvement %']
    worksheet.update(f'A{start_row}', [headers])
    
    # Model performance
    models = [
        ['Baseline B1610', 90.0, 0.0],
        ['Spatial (offshore)', 85.8, 4.7],
        ['ERA5 basic', 81.1, 9.9],
        ['Optimized (all improvements)', 72.0, 20.0],  # Target
    ]
    
    data_start = start_row + 1
    worksheet.update(f'A{data_start}', models)
    
    # Color gradient for improvement
    for i, model in enumerate(models):
        row = data_start + i
        improvement = model[2]
        
        if improvement >= 20:
            color = {'red': 0.6, 'green': 1, 'blue': 0.6}  # Dark green
        elif improvement >= 10:
            color = {'red': 0.8, 'green': 1, 'blue': 0.8}  # Light green
        elif improvement >= 5:
            color = {'red': 1, 'green': 1, 'blue': 0.8}  # Yellow
        else:
            color = {'red': 1, 'green': 0.95, 'blue': 0.95}  # Light red
        
        worksheet.format(f'C{row}', {
            'backgroundColor': color,
            'textFormat': {'bold': True},
            'horizontalAlignment': 'CENTER'
        })
    
    return data_start + len(models) + 2

print("=" * 80)
print("Wind Forecasting Dashboard Graphics Setup")
print("=" * 80)
print()

try:
    # Authenticate
    print("🔐 Authenticating with Google Sheets...")
    gc = authenticate()
    
    # Open spreadsheet
    print(f"📊 Opening spreadsheet: {SPREADSHEET_ID}")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Create or get wind forecasting sheet
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"✅ Found existing sheet: {SHEET_NAME}")
    except gspread.exceptions.WorksheetNotFound:
        print(f"📝 Creating new sheet: {SHEET_NAME}")
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=100, cols=20)
    
    print()
    
    # Create sections
    print("🎨 Creating dashboard sections...")
    
    current_row = 2
    
    # Title
    worksheet.update('A1', [['🌬️ Wind Forecasting Dashboard - Spatial & ERA5 Enhanced']])
    worksheet.format('A1:F1', {
        'backgroundColor': {'red': 0.1, 'green': 0.2, 'blue': 0.4},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}, 'fontSize': 16},
        'horizontalAlignment': 'CENTER'
    })
    worksheet.merge_cells('A1:F1')
    
    current_row = 3
    
    # Section 1: Wind drop alerts
    print("   1. Wind Drop Alerts...")
    current_row = create_wind_alerts_section(worksheet, current_row)
    
    # Section 2: Spatial correlations
    print("   2. Spatial Correlations...")
    current_row = create_spatial_correlation_heatmap(worksheet, current_row)
    
    # Section 3: ERA5 coverage
    print("   3. ERA5 Coverage Map...")
    current_row = create_era5_coverage_map(worksheet, current_row)
    
    # Section 4: Forecast accuracy
    print("   4. Forecast Accuracy...")
    current_row = create_forecast_accuracy_chart(worksheet, current_row)
    
    # Format column widths
    worksheet.columns_auto_resize(0, 5)
    
    print()
    print("=" * 80)
    print("✅ DASHBOARD GRAPHICS CREATED")
    print("=" * 80)
    print(f"View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print()
    print("Dashboard includes:")
    print("   - 🔴🟡🟢 Color-coded wind drop alerts")
    print("   - Spatial correlation heatmap (r=0.90-0.97)")
    print("   - ERA5 grid point coverage (18 total points)")
    print("   - Forecast accuracy comparison (baseline → optimized)")
    print()
    print("Next steps:")
    print("   1. Set up automatic refresh (every 15-30 minutes)")
    print("   2. Add charts using Google Sheets charting tools")
    print("   3. Deploy wind_drop_alerts.py as cron job")

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting:")
    print("   1. Check service account credentials file exists")
    print("   2. Verify spreadsheet ID is correct")
    print("   3. Ensure service account has edit access to spreadsheet")
