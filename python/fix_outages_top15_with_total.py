#!/usr/bin/env python3
"""
Dashboard V3 - TOP 15 Outages + Complete Deduplication Fix

User Requirements:
1. Show TOP 15 outages only (not all 156)
2. Calculate TOTAL from ALL outages
3. Fix duplicates (same BM unit appearing multiple times)
"""

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET = "Dashboard V3"

def main():
    print("🔧 Fixing Dashboard V3 - TOP 15 Outages + Complete TOTAL")
    print("="*80)
    
    # Initialize credentials
    creds = service_account.Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/bigquery'
        ]
    )
    
    # Initialize BigQuery
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    # Initialize Google Sheets
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    # Get TOP 15 + TOTAL of ALL
    top_15, total_stats = get_outages_top_15_and_total(bq_client)
    
    # Update dashboard
    update_dashboard_outages(sheet, top_15, total_stats)
    
    print("\n" + "="*80)
    print("✅ COMPLETE!")

def get_outages_top_15_and_total(client):
    """
    Get TOP 15 outages by MW lost
    Calculate TOTAL from ALL outages (properly deduplicated)
    """
    print("\n📊 Querying outages...")
    
    # Query: Get ALL deduplicated outages first
    query = f"""
    WITH latest_revisions AS (
        -- Get latest revision for each unique outage event
        SELECT 
            affectedUnit,
            eventStartTime,
            MAX(revisionNumber) as max_revision
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND (normalCapacity - availableCapacity) >= 50
        GROUP BY affectedUnit, eventStartTime
    ),
    deduplicated_outages AS (
        -- Join back to get full row for latest revision only
        SELECT 
            u.affectedUnit,
            u.assetName,
            u.fuelType,
            u.normalCapacity,
            u.availableCapacity,
            (u.normalCapacity - u.availableCapacity) as unavailable_mw,
            u.eventStartTime,
            u.eventEndTime,
            u.eventStatus
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.eventStartTime = lr.eventStartTime
            AND u.revisionNumber = lr.max_revision
        WHERE u.eventStatus = 'Active'
          AND (u.normalCapacity - u.availableCapacity) >= 50
    ),
    total_capacity AS (
        SELECT 42000.0 as total_gb_capacity
    ),
    enriched_outages AS (
        -- Add plant names and % calculations
        SELECT 
            o.affectedUnit as bm_unit,
            COALESCE(bmu.bmunitname, o.assetName, o.affectedUnit) as plant_name,
            o.fuelType as fuel_type,
            ROUND(o.unavailable_mw, 0) as mw_lost,
            ROUND((o.unavailable_mw / tc.total_gb_capacity) * 100, 2) as pct_lost,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', o.eventStartTime) as start_time,
            CASE 
                WHEN o.eventEndTime IS NULL THEN 'Ongoing'
                ELSE FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', o.eventEndTime)
            END as end_time,
            o.eventStatus as status,
            o.unavailable_mw as unavailable_mw_for_sort
        FROM deduplicated_outages o
        LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
            ON o.affectedUnit = bmu.nationalgridbmunit
        CROSS JOIN total_capacity tc
    )
    -- Return TOP 15 by MW lost
    SELECT 
        bm_unit,
        plant_name,
        fuel_type,
        mw_lost,
        pct_lost,
        start_time,
        end_time,
        status
    FROM enriched_outages
    ORDER BY unavailable_mw_for_sort DESC
    LIMIT 15
    """
    
    top_15_df = client.query(query).to_dataframe()
    
    print(f"   ✅ Retrieved TOP 15 outages (properly deduplicated)")
    
    # Calculate TOTAL from ALL deduplicated outages
    total_query = f"""
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            eventStartTime,
            MAX(revisionNumber) as max_revision
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND (normalCapacity - availableCapacity) >= 50
        GROUP BY affectedUnit, eventStartTime
    ),
    deduplicated_outages AS (
        SELECT 
            u.affectedUnit,
            (u.normalCapacity - u.availableCapacity) as unavailable_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.eventStartTime = lr.eventStartTime
            AND u.revisionNumber = lr.max_revision
        WHERE u.eventStatus = 'Active'
          AND (u.normalCapacity - u.availableCapacity) >= 50
    )
    SELECT 
        COUNT(DISTINCT affectedUnit) as total_units,
        ROUND(SUM(unavailable_mw), 0) as total_mw,
        ROUND((SUM(unavailable_mw) / 42000.0) * 100, 2) as total_pct
    FROM deduplicated_outages
    """
    
    total_df = client.query(total_query).to_dataframe()
    total_stats = {
        'units': int(total_df['total_units'].iloc[0]),
        'mw': int(total_df['total_mw'].iloc[0]),
        'pct': float(total_df['total_pct'].iloc[0])
    }
    
    print(f"   ✅ Calculated TOTAL from ALL {total_stats['units']} unique outages")
    print(f"   ✅ TOTAL: {total_stats['mw']:,} MW ({total_stats['pct']}%)")
    
    return top_15_df, total_stats

def update_dashboard_outages(sheet, top_15_df, total_stats):
    """Update dashboard with TOP 15 + TOTAL row"""
    print("\n📝 Updating Dashboard V3...")
    
    # Section label
    sheet.update(values=[['🚨 ACTIVE OUTAGES (TOP 15 by MW Lost)']], range_name='A22')
    
    # Headers
    headers = ['BM Unit', 'Plant Name', 'Fuel Type', 'MW Lost', '% Lost', 'Start Time', 'End Time', 'Status']
    sheet.update(values=[headers], range_name='A23')
    
    # TOP 15 data rows (rows 24-38)
    data_rows = []
    for _, row in top_15_df.iterrows():
        data_rows.append([
            row['bm_unit'],
            row['plant_name'],
            row['fuel_type'],
            int(row['mw_lost']),
            f"{row['pct_lost']:.2f}%",
            row['start_time'],
            row['end_time'],
            row['status']
        ])
    
    sheet.update(values=data_rows, range_name='A24:H38')
    print(f"   ✅ Updated TOP 15 outages (rows 24-38)")
    
    # Empty row
    sheet.update(values=[['']*8], range_name='A39:H39')
    
    # TOTAL ROW (row 40)
    total_row = [
        '═══════════',
        f'TOTAL UNAVAILABLE ({total_stats["units"]} plants)',
        '═══════════',
        total_stats['mw'],
        f"{total_stats['pct']:.2f}%",
        '',
        '',
        f'{total_stats["units"]} unique'
    ]
    sheet.update(values=[total_row], range_name='A40:H40')
    print(f"   ✅ Updated TOTAL row (row 40): {total_stats['mw']:,} MW from {total_stats['units']} plants")
    
    print(f"\n   📋 Summary:")
    print(f"      - TOP 15 outages displayed (largest by MW)")
    print(f"      - TOTAL calculated from ALL {total_stats['units']} unique outages")
    print(f"      - Duplicates FIXED: Using affectedUnit+eventStartTime+MAX(revisionNumber)")

if __name__ == "__main__":
    main()
