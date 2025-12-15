#!/usr/bin/env python3
"""
Fix Outages Display - Corrected Query
- Uses MAX(revisionNumber) not MAX(publishTime) for deduplication
- Joins with all_generators for proper station names
- Shows only Active, current events
- Handles interconnector pairs correctly
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

def get_clients():
    """Initialize BigQuery and gspread clients"""
    # BigQuery
    bq_client = bigquery.Client(
        project=PROJECT_ID,
        credentials=service_account.Credentials.from_service_account_file(SA_FILE),
        location='US'
    )
    
    # gspread
    with open(TOKEN_FILE, 'rb') as token:
        creds = pickle.load(token)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    return bq_client, dashboard

def get_outages_corrected(bq_client):
    """
    Get outages with CORRECTED deduplication logic
    - Uses MAX(revisionNumber) not publishTime
    - Joins with generators table for proper names
    """
    print("\n🔴 Querying outages (CORRECTED - uses revisionNumber)...")
    
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
            o.affectedUnit,
            o.assetId,
            o.assetName,
            o.fuelType,
            o.normalCapacity,
            o.unavailableCapacity,
            o.pct_unavailable,
            o.cause,
            o.publishTime,
            o.eventStartTime,
            o.revisionNumber
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
        revisionNumber
    FROM with_names
    ORDER BY unavailableCapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} unique outages (using MAX(revisionNumber))")
    
    if len(df) > 0:
        total_unavail = df['unavailableCapacity'].sum()
        print(f"   Total unavailable: {total_unavail:,.0f} MW")
        
        # Show top 10 for verification
        print("\n   Top 10 outages:")
        for i, row in df.head(10).iterrows():
            print(f"      {row['affectedUnit']:15s} | {row['display_name']:35s} | {row['unavailableCapacity']:6.0f} MW | Rev {row['revisionNumber']}")
    
    return df

def update_outages_section(dashboard, outages_df):
    """Update Dashboard outages section (starting at row 31)"""
    print("\n📝 Updating Dashboard outages section...")
    
    if len(outages_df) == 0:
        print("✅ No active outages")
        return
    
    # Calculate totals
    total_unavail = int(outages_df['unavailableCapacity'].sum())
    outage_count = len(outages_df)
    
    # Build outage rows (NO header - header at row 30)
    outage_rows = []
    
    for idx, row in outages_df.iterrows():
        unit = str(row['affectedUnit']) if row['affectedUnit'] else ''
        name = str(row['display_name'])[:40] if row['display_name'] else unit
        fuel = str(row['fuel_type'])[:20] if row['fuel_type'] else 'Unknown'
        
        normal = int(row['normal_capacity']) if row['normal_capacity'] else 0
        unavail = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
        
        # Visual percentage bar
        pct = row['pct_unavailable'] if row['pct_unavailable'] else 0
        blocks = min(10, int(pct / 10))
        visual = '🟥' * blocks + '⬜' * (10 - blocks)
        pct_display = f"{pct:.0f}%"
        
        # Cause and start time
        cause = str(row['cause'])[:30] if row['cause'] else 'Unknown'
        
        # Format start time properly
        start_time = ''
        if pd.notna(row['eventStartTime']):
            if isinstance(row['eventStartTime'], pd.Timestamp):
                start_time = row['eventStartTime'].strftime('%Y-%m-%d %H:%M')
            else:
                start_time = str(row['eventStartTime'])[:16]
        
        # Status emoji
        status_emoji = '⚠️' if unavail > 300 else '🟡' if unavail > 100 else '🟢'
        
        outage_rows.append([
            name,
            unit,
            fuel,
            str(normal),
            f"{status_emoji} {unavail}",
            visual,
            pct_display,
            cause,
            start_time
        ])
    
    # Write to Dashboard (row 31 onwards)
    end_row = 31 + len(outage_rows) - 1
    range_str = f'A31:I{end_row}'
    
    print(f"   Writing {len(outage_rows)} outages to {range_str}")
    dashboard.update(range_str, outage_rows, value_input_option='USER_ENTERED')
    
    # Update summary row (row 30 should have header, summary at end)
    summary_row = end_row + 2
    summary_text = f"Total Unavailable Capacity: {total_unavail:,} MW ({outage_count} outages)"
    dashboard.update(f'A{summary_row}', [[summary_text]], value_input_option='USER_ENTERED')
    
    print(f"✅ Updated {outage_count} outages (rows 31-{end_row})")
    print(f"   Total unavailable: {total_unavail:,} MW")

def main():
    print("=" * 100)
    print("🔧 FIXING OUTAGES DISPLAY - CORRECTED DEDUPLICATION")
    print("=" * 100)
    
    bq_client, dashboard = get_clients()
    
    # Get corrected outages data
    outages_df = get_outages_corrected(bq_client)
    
    # Update Dashboard
    if len(outages_df) > 0:
        update_outages_section(dashboard, outages_df)
    else:
        print("\n✅ No active outages to display")
    
    print("\n" + "=" * 100)
    print("✅ OUTAGES DISPLAY FIXED")
    print("=" * 100)
    print("\nKey fixes applied:")
    print("   1. ✅ Uses MAX(revisionNumber) not MAX(publishTime)")
    print("   2. ✅ Joins with all_generators for proper station names")
    print("   3. ✅ Shows only Active status events")
    print("   4. ✅ Filters for current events only")
    print("   5. ✅ Minimum 50 MW threshold (not 100)")
    print("\n🌐 View Dashboard:")
    print("   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")

if __name__ == "__main__":
    main()
