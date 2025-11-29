#!/usr/bin/env python3
"""
update_outages_for_v2.py
------------------------
Fixed outages updater for Dashboard V2 (Orange Theme)
- Writes to rows 93-104 (max 12 outages)
- Uses correct spreadsheet ID
- Formats properly with orange theme
- Doesn't interfere with chart zones
"""

import pickle
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration - DASHBOARD V2
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'  # Dashboard V2
DASHBOARD_SHEET = 'Dashboard'
OUTAGES_SHEET = 'Outages'  # Full history
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

# Layout - FIXED POSITIONS
OUTAGES_START_ROW = 93  # Data starts at row 93 (after header at row 91)
MAX_OUTAGES = 12  # Top 12 only

# Unit type emojis
UNIT_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'OCGT': '🔥',
    'FOSSIL GAS': '🔥',
    'GAS': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'Wind Offshore': '💨',
    'Hydro Pumped Storage': '💧',
    'BIOMASS': '🌱',
    'COAL': '⛏️',
    'INTERCONNECTOR': '🔌',
    'Interconnector': '🔌'
}

def get_active_outages():
    """Fetch active outages from BigQuery"""
    try:
        credentials = service_account.Credentials.from_service_account_file(SA_FILE)
        client = bigquery.Client(credentials=credentials, project=PROJECT_ID)
        
        query = f"""
        WITH latest_mels AS (
            SELECT 
                bmUnit,
                mep,
                CAST(mels AS INT64) as max_mw,
                PARSE_DATE('%Y-%m-%d', settlementDate) as settlement_date_parsed,
                settlementPeriod,
                ROW_NUMBER() OVER (PARTITION BY bmUnit ORDER BY PARSE_DATE('%Y-%m-%d', settlementDate) DESC, settlementPeriod DESC) as rn
            FROM `{PROJECT_ID}.{DATASET}.balancing_physical_mels`
            WHERE PARSE_DATE('%Y-%m-%d', settlementDate) >= CURRENT_DATE() - 2
        ),
        latest_mils AS (
            SELECT 
                bmUnit,
                mep,
                CAST(mils AS INT64) as available_mw,
                PARSE_DATE('%Y-%m-%d', settlementDate) as settlement_date_parsed,
                settlementPeriod
            FROM `{PROJECT_ID}.{DATASET}.balancing_physical_mils`
            WHERE PARSE_DATE('%Y-%m-%d', settlementDate) >= CURRENT_DATE() - 2
        ),
        outages AS (
            SELECT 
                mels.bmUnit as affectedUnit,
                mels.mep as impactedResource,
                COALESCE(gen.fuel_type, 'Unknown') as fuelType,
                mels.max_mw,
                COALESCE(mils.available_mw, 0) as available_mw,
                (mels.max_mw - COALESCE(mils.available_mw, 0)) as unavailable_mw,
                mels.settlement_date_parsed,
                mels.settlementPeriod
            FROM latest_mels mels
            LEFT JOIN latest_mils mils 
                ON mels.bmUnit = mils.bmUnit 
                AND mels.settlement_date_parsed = mils.settlement_date_parsed
                AND mels.settlementPeriod = mils.settlementPeriod
            LEFT JOIN `{PROJECT_ID}.{DATASET}.all_generators` gen
                ON mels.bmUnit = gen.bm_unit
            WHERE mels.rn = 1
                AND (mels.max_mw - COALESCE(mils.available_mw, 0)) > 50
        )
        SELECT 
            affectedUnit,
            impactedResource,
            fuelType,
            unavailable_mw,
            settlement_date_parsed as settlementDate,
            settlementPeriod
        FROM outages
        WHERE unavailable_mw > 50  -- Only significant outages
        ORDER BY unavailable_mw DESC
        LIMIT 50  -- Get top 50, we'll filter to top 12 for display
        """
        
        df = client.query(query).to_dataframe()
        return df
        
    except Exception as e:
        print(f"❌ Error fetching outages: {e}")
        return pd.DataFrame()

def format_outage_row(row):
    """Format a single outage row for dashboard"""
    emoji = UNIT_EMOJIS.get(row.get('fuelType', ''), '⚡')
    bm_unit = row.get('affectedUnit', 'Unknown')
    plant = row.get('impactedResource', 'Unknown')
    fuel = row.get('fuelType', 'Unknown')
    mw_lost = int(row.get('unavailable_mw', 0))
    
    # Parse timestamp from settlement date/period
    settlement_date = row.get('settlementDate')
    settlement_period = row.get('settlementPeriod', 1)
    
    if settlement_date:
        try:
            if isinstance(settlement_date, str):
                dt = datetime.fromisoformat(settlement_date)
            else:
                dt = settlement_date
            # Add settlement period time (30 min periods starting at 23:00 previous day)
            hour = ((int(settlement_period) - 1) * 30) // 60
            minute = ((int(settlement_period) - 1) * 30) % 60
            time_str = dt.strftime('%Y-%m-%d') + f" {hour:02d}:{minute:02d}"
        except:
            time_str = str(settlement_date)[:10] if settlement_date else 'Unknown'
    else:
        time_str = 'Unknown'
    
    # Status
    if mw_lost > 500:
        status = '🔴 Critical'
    elif mw_lost > 200:
        status = '🟠 Major'
    else:
        status = '🟡 Minor'
    
    return [
        bm_unit,
        plant,
        fuel,
        mw_lost,
        'GB',  # Region - can be enhanced later
        time_str,
        'Ongoing',  # End time
        status
    ]

def update_dashboard():
    """Update Dashboard V2 with top 12 outages"""
    print("=" * 70)
    print("⚠️  UPDATING DASHBOARD V2 - TOP 12 OUTAGES")
    print("=" * 70)
    print()
    
    try:
        # Connect to sheets
        creds = service_account.Credentials.from_service_account_file(
            SA_FILE,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        dash = sh.worksheet(DASHBOARD_SHEET)
        
        print(f"✅ Connected to Dashboard V2")
        
        # Get outages
        print("📊 Fetching active outages from BigQuery...")
        df = get_active_outages()
        
        if df.empty:
            print("⚠️  No active outages found")
            # Clear outages section
            clear_range = f"A{OUTAGES_START_ROW}:H{OUTAGES_START_ROW + MAX_OUTAGES}"
            dash.batch_clear([clear_range])
            dash.update([[f"No active outages (checked: {datetime.now().strftime('%Y-%m-%d %H:%M')})"]], 
                       f"A{OUTAGES_START_ROW}")
            return
        
        print(f"✅ Found {len(df)} total outages")
        
        # Format top 12 for dashboard
        outage_rows = []
        for idx, row in df.head(MAX_OUTAGES).iterrows():
            outage_rows.append(format_outage_row(row))
        
        print(f"📝 Updating top {len(outage_rows)} outages in dashboard...")
        
        # Clear existing outages (rows 93-104)
        clear_range = f"A{OUTAGES_START_ROW}:H{OUTAGES_START_ROW + MAX_OUTAGES}"
        dash.batch_clear([clear_range])
        
        # Write new outages
        if outage_rows:
            update_range = f"A{OUTAGES_START_ROW}:H{OUTAGES_START_ROW + len(outage_rows) - 1}"
            dash.update(outage_rows, update_range)
            print(f"   ✅ Updated {len(outage_rows)} outages")
        
        # Update total
        total_mw = int(df['unavailable_mw'].sum())
        dash.update([[f"TOTAL UNAVAILABLE: {total_mw:,} MW"]], f"A{OUTAGES_START_ROW + MAX_OUTAGES + 1}")
        
        # Update timestamp in row 2
        dash.update([[f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]], "A2")
        
        print()
        print("=" * 70)
        print("✅ DASHBOARD V2 OUTAGES UPDATE COMPLETE")
        print("=" * 70)
        print(f"📊 Total Outages: {len(df)}")
        print(f"📋 Displayed: {len(outage_rows)} (top {MAX_OUTAGES})")
        print(f"⚡ Total MW Lost: {total_mw:,} MW")
        print()
        
        # Also update full Outages sheet
        update_full_outages_sheet(sh, df)
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()

def update_full_outages_sheet(sh, df):
    """Update the full Outages sheet with all outages"""
    try:
        # Get or create Outages sheet
        try:
            outages_ws = sh.worksheet(OUTAGES_SHEET)
        except gspread.WorksheetNotFound:
            outages_ws = sh.add_worksheet(title=OUTAGES_SHEET, rows=1000, cols=10)
            # Add headers
            headers = [["BM Unit ID", "Plant Name", "Fuel", "MW Unavailable", "Region",
                       "Outage Start", "Outage End", "Reason", "Status", "Last Updated"]]
            outages_ws.update(headers, "A1")
        
        # Format all outages for full sheet
        all_rows = []
        for idx, row in df.iterrows():
            formatted = format_outage_row(row)
            # Add reason and last updated
            formatted.append('MELS/MILS data')  # No message field from this query
            formatted.append(datetime.now().strftime('%Y-%m-%d %H:%M'))
            all_rows.append(formatted)
        
        # Clear and update
        if len(all_rows) > 0:
            outages_ws.batch_clear([f"A2:J{len(all_rows) + 10}"])
            outages_ws.update(all_rows, f"A2:J{len(all_rows) + 1}")
            print(f"✅ Updated {len(all_rows)} outages in Outages sheet")
        
    except Exception as e:
        print(f"⚠️  Could not update Outages sheet: {e}")

if __name__ == "__main__":
    update_dashboard()
