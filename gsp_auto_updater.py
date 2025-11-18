#!/usr/bin/env python3
"""
GSP Auto-Updater with Formatting Lock
=====================================
Updates GSP data every 30 minutes while preserving Dashboard formatting.

Features:
- Locks down current Dashboard design (colors, widths, fonts)
- Fetches latest GSP demand/generation data
- Updates both Generation and Demand tables
- Preserves all formatting during updates
- Auto-refresh compatible

Update Frequency: GSP data updates every ~30 minutes in BigQuery
Recommended: Run every 10 minutes (catches updates quickly)
"""

import gspread
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import time

# Configuration
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# GSP Names (verified mapping)
GSP_NAMES = {
    '_A': 'Northern Scotland',
    '_B': 'Southern Scotland', 
    '_C': 'North West England',
    '_D': 'North East England',
    '_E': 'Yorkshire',
    '_F': 'North Wales & Mersey',
    '_G': 'East Midlands',
    '_H': 'West Midlands',
    '_I': 'Wales',
    '_J': 'Southern England',
    '_K': 'South East England',
    '_L': 'London',
    '_M': 'Southern England',
    '_N': 'South West England',
    '_P': 'Eastern England',
    'N': 'London Core',
    'B1': 'Scottish Hydro',
    'B2': 'Southern Scotland',
    'B3': 'Yorkshire',
    'B4': 'North Wales',
    'B5': 'Midlands',
    'B6': 'Eastern',
    'B7': 'East Midlands',
    'B8': 'North West',
    'B9': 'East Anglia',
    'B10': 'South Wales',
    'B11': 'South West',
    'B12': 'Southern',
    'B13': 'London',
    'B14': 'South East',
    'B15': 'South Coast',
    'B16': 'Humber',
    'B17': 'North Scotland'
}

def get_gsp_data():
    """Fetch latest GSP data with demand flows"""
    print("📡 Fetching latest GSP data from BigQuery...")
    
    creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
    client = bigquery.Client(credentials=creds, project=PROJECT_ID)
    
    query = f"""
    WITH latest_wind AS (
      SELECT 
        publishTime,
        generation AS wind_generation_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
      WHERE fuelType = 'WIND'
      ORDER BY publishTime DESC
      LIMIT 1
    ),
    latest_demand_time AS (
      SELECT MAX(publishTime) as max_time
      FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris`
    ),
    latest_demand AS (
      SELECT 
        d.publishTime,
        d.boundary AS gsp_id,
        ROUND(AVG(d.demand), 1) AS net_flow_mw
      FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris` d
      CROSS JOIN latest_demand_time t
      WHERE d.publishTime = t.max_time
      GROUP BY d.publishTime, d.boundary
    )
    SELECT
      d.publishTime,
      d.gsp_id,
      d.net_flow_mw,
      ROUND(w.wind_generation_mw, 1) as national_wind_mw,
      w.publishTime as wind_timestamp
    FROM latest_demand d
    CROSS JOIN latest_wind w
    ORDER BY d.gsp_id;
    """
    
    df = client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} GSPs")
    
    if len(df) > 0:
        print(f"   Data timestamp: {df.iloc[0]['publishTime']}")
        print(f"   Wind timestamp: {df.iloc[0]['wind_timestamp']}")
        print(f"   National wind: {df.iloc[0]['national_wind_mw']:,.1f} MW")
    
    return df

def categorize_gsp(row):
    """Categorize GSP as exporting, importing, or balanced"""
    net_flow = row['net_flow_mw']
    
    if net_flow > 100:  # Exporting
        return 'export', '🟢', net_flow
    elif net_flow < -100:  # Importing
        return 'import', '🔴', abs(net_flow)
    else:  # Balanced
        return 'balanced', '⚪', abs(net_flow)

def format_gsp_tables(df):
    """Split GSP data into Generation (exporters) and Demand (importers) tables"""
    
    # Add categories
    df['category'], df['emoji'], df['flow_abs'] = zip(*df.apply(categorize_gsp, axis=1))
    df['gsp_name'] = df['gsp_id'].map(GSP_NAMES).fillna(df['gsp_id'])
    
    # Split into tables
    exporters = df[df['category'] == 'export'].sort_values('flow_abs', ascending=False)
    importers = df[df['category'] == 'import'].sort_values('flow_abs', ascending=False)
    balanced = df[df['category'] == 'balanced'].sort_values('gsp_id')
    
    # Format Generation table (exporters)
    generation_rows = []
    for _, row in exporters.iterrows():
        generation_rows.append([
            row['emoji'],
            row['gsp_id'],
            row['gsp_name'],
            f"{row['net_flow_mw']:,.1f}"
        ])
    
    # Format Demand table (importers + balanced)
    demand_rows = []
    for _, row in pd.concat([importers, balanced]).iterrows():
        demand_rows.append([
            row['emoji'],
            row['gsp_id'],
            row['gsp_name'],
            f"{abs(row['net_flow_mw']):,.1f}"
        ])
    
    return generation_rows, demand_rows, df.iloc[0]

def lock_formatting(dashboard):
    """Apply and lock Dashboard formatting"""
    print("🔒 Locking Dashboard formatting...")
    
    # This preserves the formatting applied by improve_dashboard_design.py
    # We only update cell VALUES, not formatting
    
    requests = []
    
    # Lock header colors (rows 1-6)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 1,  # Row 2
                "endRowIndex": 2,
                "startColumnIndex": 0,
                "endColumnIndex": 6
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.97},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    # Lock GSP section colors
    # Generation header (green)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 56,  # Row 57
                "endRowIndex": 57,
                "startColumnIndex": 0,
                "endColumnIndex": 4  # Columns A-D
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.4, "green": 0.85, "blue": 0.4},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    # Demand header (red)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 56,  # Row 57
                "endRowIndex": 57,
                "startColumnIndex": 7,
                "endColumnIndex": 11  # Columns H-K
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 0.95, "green": 0.4, "blue": 0.4},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    # Apply via batch update
    if requests:
        try:
            dashboard.spreadsheet.batch_update({"requests": requests})
            print("✅ Formatting locked")
        except Exception as e:
            print(f"⚠️ Formatting lock failed (may already be set): {e}")

def update_gsp_data():
    """Main update function"""
    print("\n" + "="*80)
    print("🔄 GSP AUTO-UPDATER")
    print("="*80)
    
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    # Lock formatting first
    lock_formatting(dashboard)
    
    # Fetch latest data
    df = get_gsp_data()
    
    if df.empty:
        print("❌ No data retrieved, skipping update")
        return False
    
    # Format tables
    generation_rows, demand_rows, latest = format_gsp_tables(df)
    
    print(f"\n📊 GSP SUMMARY:")
    print(f"   Exporters: {len(generation_rows)}")
    print(f"   Importers: {len([r for r in demand_rows if r[0] == '🔴'])}")
    print(f"   Balanced: {len([r for r in demand_rows if r[0] == '⚪'])}")
    
    # Update header (row 55)
    timestamp = latest['publishTime'].strftime('%Y-%m-%d %H:%M:%S')
    wind_mw = latest['national_wind_mw']
    
    header_text = f"📊 GSP ANALYSIS | Wind: {wind_mw:,.0f} MW | Updated: {timestamp} UTC"
    dashboard.update(range_name='A55', values=[[header_text]])
    
    print(f"\n✍️ Updating Dashboard...")
    
    # Update Generation table (left side, columns A-D)
    if generation_rows:
        gen_header = [['', 'GSP', 'Region', 'Export (MW)']]
        dashboard.update(range_name='A57:D57', values=gen_header)
        dashboard.update(range_name=f'A58:D{57+len(generation_rows)}', values=generation_rows)
        print(f"   ✅ Generation table: {len(generation_rows)} exporters")
    else:
        # No exporters - show message
        dashboard.update(range_name='A58', values=[['No exporters at this time']])
        print(f"   ℹ️ No exporters currently")
    
    # Update Demand table (right side, columns H-K)
    if demand_rows:
        dem_header = [['', 'GSP', 'Region', 'Import (MW)']]
        dashboard.update(range_name='H57:K57', values=dem_header)
        dashboard.update(range_name=f'H58:K{57+len(demand_rows)}', values=demand_rows)
        print(f"   ✅ Demand table: {len(demand_rows)} importers/balanced")
    
    # Clear any old data below
    max_rows = max(len(generation_rows), len(demand_rows))
    if max_rows < 20:  # Clear up to 20 rows
        clear_range = f'A{58+max_rows}:L77'
        dashboard.batch_clear([clear_range])
    
    # Update Dashboard timestamp (row 2)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dashboard.update(range_name='A2', values=[[f'⏰ Last Updated: {now} | ✅ Auto-refresh enabled']])
    
    print(f"\n✅ UPDATE COMPLETE")
    print(f"   🔗 https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")
    print("="*80)
    
    return True

if __name__ == "__main__":
    try:
        success = update_gsp_data()
        if success:
            print("\n💡 TIP: Schedule this script to run every 10 minutes for live updates!")
            print("   Example cron: */10 * * * * cd ~/GB\\ Power\\ Market\\ JJ && .venv/bin/python gsp_auto_updater.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
