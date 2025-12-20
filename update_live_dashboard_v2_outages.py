#!/usr/bin/env python3
"""
Update outages section in Live Dashboard v2 sheet
Writes to columns G-Q:
  Row 30: Section title with total MW offline
  Row 31: Summary statistics
  Row 33: Column headers
  Rows 34+: Outage data (top 15 by capacity)
"""

import sys
import logging
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = '/home/george/inner-cinema-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_outages_data(bq_client):
    """Get current outages from bmrs_remit_unavailability with proper asset names and deduplication"""
    query = f"""
    WITH latest_revisions AS (
        SELECT
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
        GROUP BY affectedUnit
    ),
    deduplicated AS (
        SELECT
            u.affectedUnit as bmu_id,
            COALESCE(bmu.bmunitname, u.assetName, u.affectedUnit) as asset_name,
            COALESCE(bmu.fueltype, u.fuelType, 'Unknown') as fuel_type,
            CAST(u.unavailableCapacity AS INT64) as unavail_mw,
            CAST(u.normalCapacity AS INT64) as normal_mw,
            u.cause,
            u.unavailabilityType,
            u.participantName,
            u.affectedArea,
            u.biddingZone,
            u.eventStartTime,
            u.eventEndTime,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', u.eventStartTime) as start_time,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', u.eventEndTime) as end_time,
            TIMESTAMP_DIFF(COALESCE(u.eventEndTime, CURRENT_TIMESTAMP()), u.eventStartTime, HOUR) as duration_hours,
            u.eventType,
            ROW_NUMBER() OVER (PARTITION BY u.affectedUnit ORDER BY u.unavailableCapacity DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
        INNER JOIN latest_revisions lr
            ON u.affectedUnit = lr.affectedUnit
            AND u.revisionNumber = lr.max_rev
        LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
            ON u.affectedUnit = bmu.nationalgridbmunit
            OR u.affectedUnit = bmu.elexonbmunit
        WHERE u.eventStatus = 'Active'
          AND TIMESTAMP(u.eventStartTime) <= CURRENT_TIMESTAMP()
          AND (TIMESTAMP(u.eventEndTime) >= CURRENT_TIMESTAMP() OR u.eventEndTime IS NULL)
          AND u.unavailableCapacity > 50
    )
    SELECT * EXCEPT(rn)
    FROM deduplicated
    WHERE rn = 1
    ORDER BY unavail_mw DESC
    LIMIT 15
    """

    try:
        df = bq_client.query(query).to_dataframe()
        return df if not df.empty else None
    except Exception as e:
        logging.error(f"Error getting outages: {e}")
        return None

def update_outages():
    """Update outages section in Live Dashboard v2"""
    print("\n" + "=" * 80)
    print("⚡ UPDATING LIVE DASHBOARD V2 OUTAGES")
    print("=" * 80)

    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID, location='US')

    # Initialize Google Sheets client
    credentials = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)

    print(f"\n📥 Fetching outages data from BigQuery...")
    outages = get_outages_data(bq_client)

    if outages is None or len(outages) == 0:
        print("⚠️  No outages data found")
        return

    print(f"   ✅ Found {len(outages)} active outages")

    # Fuel type emojis
    fuel_emoji = {
        'Fossil Gas': '🏭', 'CCGT': '🏭', 'Gas': '🏭',
        'Nuclear': '⚛️', 'NUCLEAR': '⚛️',
        'Wind Onshore': '🌬️', 'Wind Offshore': '🌬️', 'WIND': '🌬️',
        'Hydro': '💧', 'NPSHYD': '💧', 'Hydro Pumped Storage': '🔋',
        'Pumped Storage': '🔋', 'PS': '🔋',
        'Biomass': '🌿', 'BIOMASS': '🌿',
        'Coal': '🪨', 'COAL': '🪨',
        'Oil': '🛢️', 'OIL': '🛢️',
        'Other': '❓', 'OTHER': '❓',
        'INTFR': '🇫🇷', 'INTEW': '🇮🇪', 'INTNED': '🇳🇱', 'INTIRL': '🇮🇪',
        'INTIFA2': '🇫🇷', 'INTNEM': '🇧🇪', 'INTNSL': '🇳🇴', 'INTVKL': '🇳🇴'
    }

    # Format outage data for Live Dashboard v2
    # Columns: G=Asset Name, H=Fuel Type, I=Unavail MW, J=Normal MW, K=Cause,
    #          L=Planned/Unplanned, M=Expected Return, N=Duration, O=Operator, P=Area, Q=Zone
    outage_data = []
    for _, row in outages.iterrows():
        asset = str(row['asset_name']) if pd.notna(row['asset_name']) else str(row['bmu_id'])
        fuel = row['fuel_type'] if pd.notna(row['fuel_type']) else 'Unknown'
        fuel_display = f"{fuel_emoji.get(fuel, '❓')} {fuel}" if fuel != 'Unknown' else 'Unknown'

        # Format duration (hours to days/hours)
        duration_hours = int(row['duration_hours']) if pd.notna(row['duration_hours']) else 0
        if duration_hours >= 24:
            days = duration_hours // 24
            hours = duration_hours % 24
            duration_str = f"{days}d {hours}h" if hours > 0 else f"{days}d"
        else:
            duration_str = f"{duration_hours}h"

        # Format return date
        return_date = row['end_time'] if pd.notna(row['end_time']) else 'Unknown'

        # Format planned/unplanned
        outage_type = row['unavailabilityType'] if pd.notna(row['unavailabilityType']) else 'Unknown'
        outage_emoji = '📅' if outage_type == 'Planned' else '⚡'
        outage_display = f"{outage_emoji} {outage_type}"

        outage_data.append([
            asset,  # Column G - Asset Name
            fuel_display,  # Column H - Fuel Type
            int(row['unavail_mw']),  # Column I - Unavail MW
            int(row['normal_mw']) if pd.notna(row['normal_mw']) else '',  # Column J - Normal Capacity
            row['cause'] if pd.notna(row['cause']) else 'Unknown',  # Column K - Cause
            outage_display,  # Column L - Planned/Unplanned
            return_date,  # Column M - Expected Return
            duration_str,  # Column N - Duration
            row['participantName'] if pd.notna(row['participantName']) else '',  # Column O - Operator
            row['affectedArea'] if pd.notna(row['affectedArea']) else '',  # Column P - Area
            row['biddingZone'] if pd.notna(row['biddingZone']) else ''  # Column Q - Bidding Zone
        ])

    print(f"\n✍️  Writing to Live Dashboard v2 sheet...")

    # Calculate summary statistics
    total_outages = len(outages)
    total_unavail_mw = outages['unavail_mw'].sum()
    total_normal_mw = outages['normal_mw'].sum()

    # Clear old outages data using simple clear method
    import time

    # Clear the range
    sheet.batch_clear(['G19:Q54'])
    time.sleep(1)

    # Write title (row 25), summary (row 26), header (row 27), and data (rows 28+)
    title_text = f"⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: {total_outages} units | Offline: {total_unavail_mw:,.0f} MW | Normal Capacity: {total_normal_mw:,.0f} MW"

    sheet.batch_update([
        {'range': 'G25', 'values': [[title_text]]},
    ])
    time.sleep(0.5)
    sheet.batch_update([
        # Row 26 intentionally blank
        {'range': 'G27:Q27', 'values': [['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Normal (MW)', 'Cause', 'Category', 'Expected Return', 'Duration', 'Operator', 'Area', 'Zone']]},
    ])
    time.sleep(0.5)
    sheet.batch_update([
        {'range': f'G28:Q{27 + len(outage_data)}', 'values': outage_data}
    ])

    print(f"   ✅ Outages updated ({len(outage_data)} units, {total_unavail_mw:,.0f} MW offline)")
    print(f"   First: {outage_data[0][0]} | {outage_data[0][1]} - {outage_data[0][2]} MW (Normal: {outage_data[0][3]} MW) | Return: {outage_data[0][6]}")

    # Set column widths for better display
    sheet_id = sheet.id
    requests = [
        # G - Asset Name: 200px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 6, 'endIndex': 7},
                'properties': {'pixelSize': 200},
                'fields': 'pixelSize'
            }
        },
        # H - Fuel Type: 140px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 7, 'endIndex': 8},
                'properties': {'pixelSize': 140},
                'fields': 'pixelSize'
            }
        },
        # I - Unavail MW: 100px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 8, 'endIndex': 9},
                'properties': {'pixelSize': 100},
                'fields': 'pixelSize'
            }
        },
        # J - Normal MW: 100px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 9, 'endIndex': 10},
                'properties': {'pixelSize': 100},
                'fields': 'pixelSize'
            }
        },
        # K - Cause: 150px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 10, 'endIndex': 11},
                'properties': {'pixelSize': 150},
                'fields': 'pixelSize'
            }
        },
        # L - Type (Planned/Unplanned): 130px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 11, 'endIndex': 12},
                'properties': {'pixelSize': 130},
                'fields': 'pixelSize'
            }
        },
        # M - Expected Return: 140px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 12, 'endIndex': 13},
                'properties': {'pixelSize': 140},
                'fields': 'pixelSize'
            }
        },
        # N - Duration: 90px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 13, 'endIndex': 14},
                'properties': {'pixelSize': 90},
                'fields': 'pixelSize'
            }
        },
        # O - Operator: 180px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 14, 'endIndex': 15},
                'properties': {'pixelSize': 180},
                'fields': 'pixelSize'
            }
        },
        # P - Area: 120px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 15, 'endIndex': 16},
                'properties': {'pixelSize': 120},
                'fields': 'pixelSize'
            }
        },
        # Q - Zone: 100px
        {
            'updateDimensionProperties': {
                'range': {'sheetId': sheet_id, 'dimension': 'COLUMNS', 'startIndex': 16, 'endIndex': 17},
                'properties': {'pixelSize': 100},
                'fields': 'pixelSize'
            }
        }
    ]

    spreadsheet.batch_update({'requests': requests})
    print(f"   ✅ Column widths optimized")

    print("\n" + "=" * 80)
    print("✅ OUTAGES UPDATE COMPLETE")
    print("=" * 80)
    print(f"\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=687718775\n")

if __name__ == "__main__":
    try:
        update_outages()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
