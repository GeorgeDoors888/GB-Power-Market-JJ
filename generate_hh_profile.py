#!/usr/bin/env python3
"""
HH Profile Generator for HH Data Sheet
Generates synthetic half-hourly load profiles based on demand parameters

Reads parameters from: BESS sheet cells B15:B17 (Min kW, Avg kW, Max kW)
Writes HH data to: HH Data sheet (auto-clears existing data first)
Generates: 365 days of half-hourly data (17,520 periods)
"""

import pandas as pd
import numpy as np
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Google Sheets configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
PARAM_SHEET = 'BESS'  # Where parameters are read from (B15:B17)
DATA_SHEET = 'HH Data'  # Where HH data is written

# HH data will be written starting at row 2 (row 1 = headers)
HH_START_ROW = 2
HH_HEADER_ROW = 1


def generate_hh_profile(min_kw, avg_kw, max_kw, days=365):
    """
    Generate realistic half-hourly load profile
    
    Args:
        min_kw: Minimum demand (kW)
        avg_kw: Average demand (kW)
        max_kw: Maximum demand (kW)
        days: Number of days to generate (default 365 = 1 year)
    
    Returns:
        pandas DataFrame with timestamp and kw columns
    """
    print(f"\n📊 Generating HH Profile:")
    print(f"   Min: {min_kw} kW")
    print(f"   Avg: {avg_kw} kW")
    print(f"   Max: {max_kw} kW")
    print(f"   Duration: {days} days")
    
    # Generate timestamps (48 HH per day)
    start_date = datetime(2025, 1, 1)
    periods = days * 48
    timestamps = [start_date + timedelta(minutes=30*i) for i in range(periods)]
    
    # Create base load profile with realistic patterns
    np.random.seed(42)  # For reproducibility
    
    profile = []
    for ts in timestamps:
        hour = ts.hour
        minute = ts.minute
        weekday = ts.weekday()  # 0=Monday, 6=Sunday
        month = ts.month
        
        # Base load (starts at avg)
        load = avg_kw
        
        # Daily pattern (morning and evening peaks)
        if 6 <= hour < 9:  # Morning ramp
            daily_factor = 0.8 + (hour - 6) * 0.15
        elif 9 <= hour < 16:  # Daytime
            daily_factor = 1.2
        elif 16 <= hour < 20:  # Evening peak
            daily_factor = 1.3 + (hour - 16) * 0.05
        elif 20 <= hour < 23:  # Evening decline
            daily_factor = 1.1 - (hour - 20) * 0.1
        else:  # Night (23-06)
            daily_factor = 0.6
        
        # Weekend reduction
        if weekday >= 5:  # Weekend
            daily_factor *= 0.7
        
        # Seasonal variation (winter higher, summer lower)
        if month in [12, 1, 2]:  # Winter
            seasonal_factor = 1.15
        elif month in [6, 7, 8]:  # Summer
            seasonal_factor = 0.9
        else:  # Spring/Autumn
            seasonal_factor = 1.0
        
        # Apply factors
        load = load * daily_factor * seasonal_factor
        
        # Add random variation (±10%)
        load = load * (1 + np.random.normal(0, 0.1))
        
        # Constrain to min/max bounds
        load = max(min_kw, min(max_kw, load))
        
        profile.append({
            'timestamp': ts,
            'kw': round(load, 2)
        })
    
    df = pd.DataFrame(profile)
    
    # Verify constraints
    actual_min = df['kw'].min()
    actual_avg = df['kw'].mean()
    actual_max = df['kw'].max()
    
    print(f"\n✅ Profile Generated:")
    print(f"   Actual Min: {actual_min:.2f} kW")
    print(f"   Actual Avg: {actual_avg:.2f} kW")
    print(f"   Actual Max: {actual_max:.2f} kW")
    print(f"   Total periods: {len(df)}")
    
    return df


def clear_hh_data(worksheet):
    """Clear existing HH data from sheet (keep headers)"""
    print("\n🗑️  Clearing existing HH data...")
    
    # Clear from row 2 onwards (keep headers at row 1)
    try:
        all_values = worksheet.get_all_values()
        rows_to_clear = len(all_values) - HH_START_ROW + 1
        
        if rows_to_clear > 0:
            # Clear data (keep headers at row 1)
            clear_range = f'A{HH_START_ROW}:D{len(all_values)}'
            worksheet.batch_clear([clear_range])
            print(f"   Cleared {rows_to_clear} rows from HH Data sheet")
    except Exception as e:
        print(f"   Note: {e}")
        # If error, just clear a large range to be safe
        worksheet.batch_clear([f'A{HH_START_ROW}:D20000'])


def write_hh_data(worksheet, df):
    """Write HH data to sheet"""
    print("\n📝 Writing HH data to sheet...")
    
    # Prepare data for sheet (format timestamps)
    data = []
    for _, row in df.iterrows():
        data.append([
            row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            row['kw'],
            '',  # Empty column C
            ''   # Empty column D (can be used for notes/calculations)
        ])
    
    # Write headers first
    headers = [['Timestamp', 'Demand (kW)', 'Notes', 'Calculated']]
    worksheet.update(range_name=f'A{HH_HEADER_ROW}:D{HH_HEADER_ROW}', values=headers)
    
    # Write data in batches (Google Sheets API has limits)
    batch_size = 1000
    total_rows = len(data)
    
    for i in range(0, total_rows, batch_size):
        batch = data[i:i+batch_size]
        start_row = HH_START_ROW + i
        end_row = start_row + len(batch) - 1
        
        worksheet.update(range_name=f'A{start_row}:D{end_row}', values=batch)
        print(f"   Written rows {start_row} to {end_row} ({len(batch)} rows)")
    
    print(f"\n✅ Total: {total_rows} HH periods written")


def update_summary_info(bess_worksheet, df, min_kw, avg_kw, max_kw):
    """Update summary information in BESS sheet"""
    print("\n📊 Updating summary in BESS sheet...")
    
    # Calculate statistics
    actual_min = df['kw'].min()
    actual_avg = df['kw'].mean()
    actual_max = df['kw'].max()
    
    start_date = df['timestamp'].min().strftime('%Y-%m-%d')
    end_date = df['timestamp'].max().strftime('%Y-%m-%d')
    generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Write summary info in BESS sheet at rows 18-20 (below parameters)
    summary = [
        ['HH Profile Generated:', generation_time],
        ['Period:', f'{start_date} to {end_date}'],
        ['Stats:', f'{len(df)} records | Min: {actual_min:.1f}kW | Avg: {actual_avg:.1f}kW | Max: {actual_max:.1f}kW']
    ]
    
    bess_worksheet.update(range_name='A18:B20', values=summary)
    print("   Summary updated in BESS sheet")


def generate_and_upload_hh_data(min_kw=500, avg_kw=1500, max_kw=2500, days=365):
    """
    Main function to generate HH profile and upload to HH Data sheet
    Reads parameters from BESS B15:B17, writes data to HH Data sheet
    
    Args:
        min_kw: Minimum demand (default 500 kW)
        avg_kw: Average demand (default 1500 kW)
        max_kw: Maximum demand (default 2500 kW)
        days: Number of days (default 365)
    """
    print("=" * 80)
    print("HH Profile Generator")
    print("=" * 80)
    
    # Connect to Google Sheets
    print("\n🔐 Connecting to Google Sheets...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    bess_ws = sh.worksheet(PARAM_SHEET)
    
    # Create HH Data sheet if it doesn't exist
    try:
        hh_data_ws = sh.worksheet(DATA_SHEET)
        print(f"   ✅ Found existing {DATA_SHEET} sheet")
    except:
        print(f"   ⚠️  {DATA_SHEET} sheet not found, creating...")
        hh_data_ws = sh.add_worksheet(title=DATA_SHEET, rows=20000, cols=10)
        # Add headers
        hh_data_ws.update('A1:D1', [['Timestamp', 'Demand (kW)', 'Notes', 'Calculated']])
        print(f"   ✅ Created {DATA_SHEET} sheet with headers")
    
    print(f"   ✅ Connected to {PARAM_SHEET} and {DATA_SHEET} sheets")
    
    # Generate profile
    df = generate_hh_profile(min_kw, avg_kw, max_kw, days)
    
    # Clear existing data from HH Data sheet
    clear_hh_data(hh_data_ws)
    
    # Write new data to HH Data sheet
    write_hh_data(hh_data_ws, df)
    
    # Update summary in BESS sheet
    update_summary_info(bess_ws, df, min_kw, avg_kw, max_kw)
    
    print("\n" + "=" * 80)
    print("✅ HH PROFILE GENERATION COMPLETE!")
    print("=" * 80)
    print(f"\n📋 Summary:")
    print(f"   Parameters from: {PARAM_SHEET} sheet (B15:B17)")
    print(f"   Data written to: {DATA_SHEET} sheet")
    print(f"   Rows: {HH_HEADER_ROW} to {HH_START_ROW + len(df) - 1}")
    print(f"   Periods: {len(df)} (half-hourly)")
    print(f"   Duration: {days} days")
    print(f"   Min: {df['kw'].min():.2f} kW")
    print(f"   Avg: {df['kw'].mean():.2f} kW")
    print(f"   Max: {df['kw'].max():.2f} kW")
    
    return df


if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    if len(sys.argv) >= 4:
        min_kw = float(sys.argv[1])
        avg_kw = float(sys.argv[2])
        max_kw = float(sys.argv[3])
        days = int(sys.argv[4]) if len(sys.argv) >= 5 else 365
    else:
        # Read from BESS sheet cells B15:B17
        print("📖 Reading demand parameters from BESS sheet B15:B17...")
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SHEET_ID)
        bess_ws = sh.worksheet(PARAM_SHEET)
        
        try:
            # Read from cells B15:B17
            params = bess_ws.get('B15:B17')
            
            # Extract values, use defaults if empty
            min_kw = float(params[0][0]) if params and len(params[0]) > 0 and params[0][0] else 500
            avg_kw = float(params[1][0]) if len(params) > 1 and len(params[1]) > 0 and params[1][0] else 1500
            max_kw = float(params[2][0]) if len(params) > 2 and len(params[2]) > 0 and params[2][0] else 2500
            
            # If any were empty, initialize them in the sheet
            if not (params and len(params[0]) > 0 and params[0][0]):
                print(f"   ℹ️  Initializing B15:B17 with defaults: {min_kw}, {avg_kw}, {max_kw}")
                bess_ws.update(range_name='B15:B17', values=[[min_kw], [avg_kw], [max_kw]])
            
            print(f"   ✅ Parameters: Min={min_kw}kW, Avg={avg_kw}kW, Max={max_kw}kW")
        except Exception as e:
            # Use defaults if cells are empty or error
            print(f"   ⚠️  Error reading parameters: {e}")
            min_kw = 500
            avg_kw = 1500
            max_kw = 2500
            print(f"   ℹ️  Using defaults: Min={min_kw}, Avg={avg_kw}, Max={max_kw}")
            # Initialize sheet with defaults
            bess_ws.update(range_name='B15:B17', values=[[min_kw], [avg_kw], [max_kw]])
        
        days = 365  # Default to 1 year
    
    # Generate and upload
    generate_and_upload_hh_data(min_kw, avg_kw, max_kw, days)
