#!/usr/bin/env python3
"""
Update Dashboard Outages with Live Data and Totals
- Fetches only ACTIVE outages from BigQuery
- Removes resolved outages from the sheet
- Updates row 44 with total outages capacity (GW/MW) and count
- Maintains consistent formatting: GW, MW, £, %
"""

import pickle
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
DASHBOARD_SHEET = 'Dashboard'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

# Emojis for fuel types
FUEL_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'OCGT': '🔥',
    'FOSSIL GAS': '🔥',
    'GAS': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'Wind Offshore': '💨',
    'Wind Onshore': '💨',
    'Hydro Pumped Storage': '💧',
    'BIOMASS': '🌱',
    'COAL': '⛏️',
    'INTERCONNECTOR': '🔌',
    'Interconnector': '🔌',
    'Battery Storage': '🔋',
    'Solar': '☀️',
}

def get_clients():
    """Initialize BigQuery and Google Sheets clients"""
    print("🔧 Connecting to services...")
    
    # BigQuery client
    if not SA_FILE.exists():
        print(f"❌ Service account file not found: {SA_FILE}")
        return None, None
        
    bq_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE),
        scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds)
    
    # Google Sheets client
    if not TOKEN_FILE.exists():
        print(f"❌ Token file not found: {TOKEN_FILE}")
        return None, None
        
    with open(TOKEN_FILE, 'rb') as token:
        sheets_creds = pickle.load(token)
    
    gc = gspread.authorize(sheets_creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    print("✅ Connected to BigQuery and Google Sheets")
    return bq_client, dashboard

def fetch_active_outages(bq_client):
    """
    Fetch ONLY currently active outages from BigQuery
    - Status = 'Active'
    - Event has started
    - Event has not ended (or end time is in future)
    - Uses latest revision number per unit
    - Joins with generators table for proper names
    """
    print("\n🔴 Fetching active outages from BigQuery...")
    
    query = f"""
    WITH all_outages AS (
        SELECT 
            u.affectedUnit,
            u.assetId,
            u.assetName,
            u.fuelType,
            u.normalCapacity,
            u.unavailableCapacity,
            u.revisionNumber,
            ROUND(u.unavailableCapacity / NULLIF(u.normalCapacity, 0) * 100, 1) as pct_unavailable,
            u.cause,
            u.publishTime,
            u.eventStartTime,
            u.eventEndTime,
            u.eventStatus
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        WHERE u.eventStatus = 'Active'
          AND TIMESTAMP(u.eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(u.eventEndTime) >= CURRENT_TIMESTAMP() OR u.eventEndTime IS NULL)
          AND u.unavailableCapacity >= 50
    ),
    latest_per_unit AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_revision
        FROM all_outages
        GROUP BY affectedUnit
    ),
    with_latest AS (
        SELECT 
            o.*
        FROM all_outages o
        INNER JOIN latest_per_unit lpu 
            ON o.affectedUnit = lpu.affectedUnit 
            AND o.revisionNumber = lpu.max_revision
    ),
    with_names AS (
        SELECT 
            wl.*,
            bmu.bmunitname as bmu_name,
            bmu.fueltype as bmu_fuel,
            bmu.generationcapacity as bmu_capacity
        FROM with_latest wl
        LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
            ON wl.affectedUnit = bmu.nationalgridbmunit
            OR wl.affectedUnit = bmu.elexonbmunit
            OR wl.assetId = bmu.nationalgridbmunit
            OR wl.assetId = bmu.elexonbmunit
    )
    SELECT 
        affectedUnit,
        COALESCE(bmu_name, assetName, assetId, affectedUnit) as display_name,
        COALESCE(bmu_fuel, fuelType, 'Unknown') as fuel_type,
        COALESCE(bmu_capacity, normalCapacity, 0) as normal_capacity,
        unavailableCapacity,
        pct_unavailable,
        cause,
        publishTime,
        eventStartTime,
        eventEndTime,
        revisionNumber
    FROM with_names
    ORDER BY unavailableCapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if len(df) == 0:
        print("✅ No active outages found")
        return df
    
    total_mw = df['unavailableCapacity'].sum()
    total_gw = total_mw / 1000
    
    print(f"✅ Found {len(df)} active outages")
    print(f"   Total capacity unavailable: {total_mw:,.0f} MW ({total_gw:.2f} GW)")
    
    # Show top 5
    print("\n   Top 5 outages:")
    for i, row in df.head(5).iterrows():
        emoji = FUEL_EMOJIS.get(row['fuel_type'], '⚡')
        mw = row['unavailableCapacity']
        gw = mw / 1000
        print(f"      {emoji} {row['display_name'][:35]:35s} | {mw:6.0f} MW ({gw:.2f} GW) | {row['pct_unavailable']:.0f}%")
    
    return df

def format_mw_gw(mw_value):
    """Format capacity as both MW and GW"""
    mw = int(mw_value)
    gw = mw / 1000
    if gw >= 1:
        return f"{mw:,} MW ({gw:.2f} GW)"
    else:
        return f"{mw:,} MW"

def update_outages_section(dashboard, outages_df):
    """
    Update the outages section of the dashboard
    - Clear old outages (rows 31-42)
    - Write new active outages
    - Update row 44 with totals
    """
    print("\n📝 Updating Dashboard outages section...")
    
    # First, clear the existing outages area (rows 31-42)
    print("   Clearing old outages (rows 31-42)...")
    empty_rows = [[''] * 9 for _ in range(12)]  # 12 rows, 9 columns
    dashboard.update(range_name='A31:I42', values=empty_rows, value_input_option='USER_ENTERED')
    
    if len(outages_df) == 0:
        print("✅ No active outages to display")
        
        # Update row 44 with zero totals
        total_text = "📊 TOTAL OUTAGES: 0 MW (0 GW) | Count: 0 | Status: ✅ All Clear"
        dashboard.update(range_name='A44', values=[[total_text]], value_input_option='USER_ENTERED')
        dashboard.format('A44:I44', {
            'backgroundColor': {'red': 0.89, 'green': 0.22, 'blue': 0.21},  # Red #e43835
            'textFormat': {
                'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
                'fontSize': 12,
                'bold': True
            },
            'horizontalAlignment': 'LEFT'
        })
        return
    
    # Calculate totals
    total_mw = int(outages_df['unavailableCapacity'].sum())
    total_gw = total_mw / 1000
    outage_count = len(outages_df)
    
    # Build outage rows (max 12 to fit rows 31-42)
    outage_rows = []
    display_df = outages_df.head(12)  # Only show top 12
    
    for idx, row in display_df.iterrows():
        unit = str(row['affectedUnit']) if row['affectedUnit'] else ''
        name = str(row['display_name'])[:40] if row['display_name'] else unit
        
        # Get fuel type emoji
        fuel = str(row['fuel_type'])[:20] if row['fuel_type'] else 'Unknown'
        emoji = FUEL_EMOJIS.get(fuel, '⚡')
        fuel_display = f"{emoji} {fuel}"
        
        # Capacity values
        normal = int(row['normal_capacity']) if row['normal_capacity'] else 0
        unavail = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
        unavail_gw = unavail / 1000
        
        # Format capacity with GW/MW
        capacity_display = f"{unavail:,} MW"
        if unavail_gw >= 0.1:
            capacity_display = f"{unavail:,} MW ({unavail_gw:.2f} GW)"
        
        # Percentage with visual bar
        pct = row['pct_unavailable'] if row['pct_unavailable'] else 0
        blocks = min(10, int(pct / 10))
        visual = '🟥' * blocks + '⬜' * (10 - blocks)
        pct_display = f"{pct:.1f}%"
        
        # Cause
        cause = str(row['cause'])[:30] if row['cause'] else 'Unknown'
        
        # Format start time
        start_time = ''
        if pd.notna(row['eventStartTime']):
            if isinstance(row['eventStartTime'], pd.Timestamp):
                start_time = row['eventStartTime'].strftime('%d/%m/%Y %H:%M')
            else:
                start_time = str(row['eventStartTime'])[:16]
        
        # Status emoji based on severity
        if unavail > 500:
            status_emoji = '🔴'
        elif unavail > 200:
            status_emoji = '⚠️'
        elif unavail > 100:
            status_emoji = '🟡'
        else:
            status_emoji = '🟢'
        
        outage_rows.append([
            f"{status_emoji} {name}",
            unit,
            fuel_display,
            f"{normal:,} MW",
            capacity_display,
            visual,
            pct_display,
            cause,
            start_time
        ])
    
    # Write outages to Dashboard (rows 31-42)
    if len(outage_rows) > 0:
        end_row = 30 + len(outage_rows)
        range_str = f'A31:I{end_row}'
        print(f"   Writing {len(outage_rows)} outages to {range_str}")
        dashboard.update(range_name=range_str, values=outage_rows, value_input_option='USER_ENTERED')
    
    # Update row 44 with TOTALS
    print(f"\n   Updating row 44 with totals...")
    
    # Create comprehensive total row
    total_text = f"📊 TOTAL OUTAGES: {total_mw:,} MW ({total_gw:.2f} GW) | Count: {outage_count} | Status: "
    
    if total_mw > 5000:
        status = "🔴 Critical"
    elif total_mw > 3000:
        status = "⚠️ High"
    elif total_mw > 1000:
        status = "🟡 Moderate"
    else:
        status = "🟢 Low"
    
    total_text += status
    
    # If there are more outages than displayed
    if len(outages_df) > 12:
        additional = len(outages_df) - 12
        total_text += f" | +{additional} more"
    
    dashboard.update(range_name='A44', values=[[total_text]], value_input_option='USER_ENTERED')
    
    # Format row 44 with red background
    dashboard.format('A44:I44', {
        'backgroundColor': {'red': 0.89, 'green': 0.22, 'blue': 0.21},  # Red #e43835
        'textFormat': {
            'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
            'fontSize': 12,
            'bold': True
        },
        'horizontalAlignment': 'LEFT'
    })
    
    print(f"✅ Updated {len(outage_rows)} outages (rows 31-{end_row})")
    print(f"✅ Updated row 44 with totals: {total_mw:,} MW ({total_gw:.2f} GW), {outage_count} outages")

def main():
    print("=" * 100)
    print("🔄 UPDATING DASHBOARD WITH LIVE OUTAGES AND TOTALS")
    print("=" * 100)
    print(f"⏰ Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to services
    bq_client, dashboard = get_clients()
    
    if not bq_client or not dashboard:
        print("\n❌ Failed to connect to services")
        return
    
    # Fetch active outages
    outages_df = fetch_active_outages(bq_client)
    
    # Update Dashboard
    update_outages_section(dashboard, outages_df)
    
    print("\n" + "=" * 100)
    print("✅ DASHBOARD UPDATE COMPLETE")
    print("=" * 100)
    print("\n🌐 View Dashboard:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print("\nWhat was updated:")
    print("   ✅ Cleared resolved outages from rows 31-42")
    print("   ✅ Added current active outages with GW/MW formatting")
    print("   ✅ Updated row 44 with total capacity (GW/MW) and outage count")
    print("   ✅ Applied consistent formatting: GW, MW, %")
    print("   ✅ Added status indicators (🔴⚠️🟡🟢)")

if __name__ == "__main__":
    main()
