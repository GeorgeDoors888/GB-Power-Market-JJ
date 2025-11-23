#!/usr/bin/env python3
"""
Dashboard Update with Outage Deduplication
Fixes the issue where same fault (e.g., IFA cable) appears multiple times
Groups by affected unit and keeps highest unavailable capacity
"""

import pickle
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
DASHBOARD_SHEET = 'Dashboard'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

# Unit type emojis
UNIT_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'OCGT': '🔥',
    'GAS': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'BIOMASS': '🌱',
    'COAL': '⛏️',
    'INTERCONNECTOR': '🔌'
}

def connect():
    """Connect to Google Sheets and BigQuery"""
    print("🔧 Connecting...")
    
    if not TOKEN_FILE.exists():
        print(f"❌ Token file not found: {TOKEN_FILE}")
        return None, None
    
    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    if SA_FILE.exists():
        bq_creds = service_account.Credentials.from_service_account_file(
            str(SA_FILE),
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds)
    else:
        bq_client = bigquery.Client(project=PROJECT_ID)
    
    print("✅ Connected")
    return dashboard, bq_client

def query_outages_deduplicated(bq_client):
    """Query outages and deduplicate by affected unit"""
    print("\n🔴 Querying outages (with deduplication)...")
    
    query = f"""
    WITH all_outages AS (
        SELECT 
            assetName,
            affectedUnit,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            ROUND(unavailableCapacity / NULLIF(normalCapacity, 0) * 100, 1) as pct_unavailable,
            cause,
            publishTime,
            eventStartTime,
            eventEndTime
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
          AND unavailableCapacity >= 100
    ),
    deduplicated AS (
        SELECT 
            affectedUnit,
            ANY_VALUE(assetName) as assetName,
            ANY_VALUE(fuelType) as fuelType,
            MAX(normalCapacity) as normalCapacity,
            MAX(unavailableCapacity) as unavailableCapacity,
            MAX(pct_unavailable) as pct_unavailable,
            ANY_VALUE(cause) as cause,
            MAX(publishTime) as publishTime
        FROM all_outages
        GROUP BY affectedUnit
    )
    SELECT *
    FROM deduplicated
    ORDER BY unavailableCapacity DESC
    LIMIT 10
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} unique outages (deduplicated)")
    
    if len(df) > 0:
        total_unavail = df['unavailableCapacity'].sum()
        print(f"   Total unavailable: {total_unavail:,.0f} MW")
    
    return df

def update_outages_section(dashboard, outages_df):
    """Update outages section with deduplicated data"""
    print("\n📝 Updating outages section...")
    
    if len(outages_df) == 0:
        print("✅ No active outages")
        return
    
    outage_rows = []
    
    for _, row in outages_df.iterrows():
        # Determine emoji based on fuel type or unit name
        fuel = str(row['fuelType']).upper() if row['fuelType'] else 'UNKNOWN'
        asset = row['assetName'] if row['assetName'] else 'Unknown'
        unit = row['affectedUnit'] if row['affectedUnit'] else ''
        
        # Check if interconnector
        if 'I_IE' in unit or 'IFA' in unit.upper() or 'INTER' in asset.upper():
            emoji = '🔌'
            # Get friendly name
            if 'IFA2' in unit.upper():
                display_name = '🔌 IFA2 France'
            elif 'IFA1' in unit.upper() or (unit.startswith('I_IE') and 'FRAN1' in unit):
                display_name = '🔌 IFA France (ElecLink)'
            elif 'ELEC' in unit.upper():
                display_name = '🔌 ElecLink (France)'
            else:
                display_name = f"{emoji} {asset[:25]}"
        else:
            emoji = UNIT_EMOJIS.get(fuel, '⚡')
            display_name = f"{emoji} {asset[:25]}"
        
        normal_mw = int(row['normalCapacity']) if row['normalCapacity'] else 0
        unavail_mw = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
        pct = float(row['pct_unavailable']) if row['pct_unavailable'] else 0
        
        # Progress bar
        filled = min(int(pct / 10), 10)
        bar = '🟥' * filled + '⬜' * (10 - filled) + f" {pct:.1f}%"
        
        cause = (str(row['cause'])[:40] + '...') if row['cause'] and len(str(row['cause'])) > 40 else (str(row['cause']) if row['cause'] else 'Unspecified')
        
        publish_time = str(row['publishTime'])[:19] if row['publishTime'] else ''
        
        outage_rows.append([display_name, unit, fuel, normal_mw, unavail_mw, bar, cause, publish_time])
    
    # Pad to 10 rows
    while len(outage_rows) < 10:
        outage_rows.append(['', '', '', '', '', '', '', ''])
    
    # Update Dashboard (adjust row numbers based on your layout)
    # Assuming outages start at row 23
    dashboard.update('A23:H32', outage_rows, value_input_option='USER_ENTERED')
    print(f"✅ Updated {len(outages_df)} unique outages (deduplicated from duplicates)")

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 DASHBOARD UPDATE WITH OUTAGE DEDUPLICATION")
    print("=" * 80)
    
    dashboard, bq_client = connect()
    if not dashboard or not bq_client:
        return
    
    # Query deduplicated outages
    outages_df = query_outages_deduplicated(bq_client)
    
    # Update dashboard
    update_outages_section(dashboard, outages_df)
    
    # Update timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    dashboard.update_acell('B2', f'⏰ Last Updated: {timestamp} | ✅ FRESH')
    
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   • Unique outages: {len(outages_df)}")
    if len(outages_df) > 0:
        print(f"   • Total unavailable: {outages_df['unavailableCapacity'].sum():,.0f} MW")
    print(f"   • Timestamp: {timestamp}")
    print()

if __name__ == '__main__':
    main()
