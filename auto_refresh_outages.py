#!/usr/bin/env python3
"""Auto-refresh outage data at bottom of Dashboard - delete old, add new"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, date
from flag_utils import verify_and_fix_flags
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

SHEETS_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=SHEETS_CREDS).spreadsheets()

BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

def auto_refresh_outages():
    """Get LIVE outage data from BigQuery and refresh Dashboard bottom section"""
    
    print("=" * 80)
    print("⚡ AUTO-REFRESHING LIVE OUTAGE DATA")
    print("=" * 80)
    
    # Step 1: Delete old outage data (rows 70+)
    print("\n🗑️  Deleting old outage data (rows 70-100)...")
    
    try:
        sheets.values().clear(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A70:H100'
        ).execute()
        print("✅ Old data deleted")
    except Exception as e:
        print(f"⚠️  Error clearing: {e}")
    
    # Step 2: Query LIVE outage data from BigQuery
    print("\n📡 Querying LIVE outage data from BigQuery...")
    
    today = date.today()
    
    query = f"""
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE DATE(eventStartTime) <= '{today}'
          AND (DATE(eventEndTime) >= '{today}' OR eventEndTime IS NULL)
          AND eventStatus = 'Active'
        GROUP BY affectedUnit
    )
    SELECT 
        u.affectedUnit as bmu_id,
        u.assetName,
        u.fuelType,
        u.normalCapacity as normal_mw,
        u.unavailableCapacity as unavail_mw,
        u.cause,
        u.eventStartTime,
        u.eventEndTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE DATE(u.eventStartTime) <= '{today}'
      AND (DATE(u.eventEndTime) >= '{today}' OR u.eventEndTime IS NULL)
      AND u.eventStatus = 'Active'
      AND u.unavailableCapacity > 0
    ORDER BY u.unavailableCapacity DESC
    LIMIT 15
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        print(f"✅ Retrieved {len(df)} LIVE active outages")
        
        # Step 3: Build new outage section with LIVE data
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        outage_section = [
            ['', '', '', '', '', '', '', ''],  # Blank separator (row 70)
            ['', '', '', '', '', '', '', ''],  # Blank separator (row 71)
            ['⚠️ LIVE POWER STATION OUTAGES', '', '', '', '', '', '', ''],  # Header (row 72)
            [f'🔄 Auto-refreshed: {now}', '', '', '', '', '', '', ''],  # Timestamp (row 73)
            ['', '', '', '', '', '', '', ''],  # Blank (row 74)
            ['Asset Name', 'BMU ID', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', '% Unavailable', 'Cause', 'Start Time']  # Headers (row 75)
        ]
        
        if len(df) > 0:
            for _, row in df.iterrows():
                asset_name = str(row['assetName'])[:30] if row['assetName'] else str(row['bmu_id'])[:30]
                bmu_id = str(row['bmu_id'])[:15]
                fuel = str(row['fuelType'])[:20] if row['fuelType'] else 'Unknown'
                normal = int(row['normal_mw']) if row['normal_mw'] else 0
                unavail = int(row['unavail_mw']) if row['unavail_mw'] else 0
                
                # Calculate percentage and visual bar
                pct = (unavail / normal * 100) if normal > 0 else 0
                blocks = int(pct / 10)
                visual = '🟥' * blocks + '⬜' * (10 - blocks)
                pct_display = f"{visual} {pct:.1f}%"
                
                # Get cause and start time
                cause = str(row['cause'])[:35] if row['cause'] else 'Unknown'
                start_time = str(row['eventStartTime'])[:16] if row['eventStartTime'] else 'Unknown'
                
                outage_section.append([
                    asset_name,
                    bmu_id,
                    fuel,
                    str(normal),
                    str(unavail),
                    pct_display,
                    cause,
                    start_time
                ])
            
            # Add summary row
            total_unavail = df['unavail_mw'].sum()
            outage_section.append(['', '', '', '', '', '', '', ''])
            outage_section.append([
                f'TOTAL UNAVAILABLE CAPACITY: {total_unavail:.0f} MW',
                '',
                f'({len(df)} outages)',
                '',
                '',
                '',
                '',
                ''
            ])
            
        else:
            outage_section.append([
                '✅ All systems operational - no active outages',
                '', '', '', '', '', '', ''
            ])
        
        print(f"✅ Built outage section with {len(outage_section)} rows")
        
        # Step 4: Write LIVE data to Dashboard bottom
        print(f"\n💾 Writing LIVE outage data to Dashboard (rows 70+)...")
        
        sheets.values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A70',
            valueInputOption="USER_ENTERED",
            body={"values": outage_section}
        ).execute()
        
        print("✅ LIVE outage data written")
        
        # Step 5: Apply formatting
        print("\n🎨 Applying formatting...")
        
        requests = [
            # Format outage header (row 72) - Red/warning background
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 71,  # Row 72
                        "endRowIndex": 72,
                        "startColumnIndex": 0,
                        "endColumnIndex": 8
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.9, "green": 0.3, "blue": 0.3},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}, "fontSize": 12}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            },
            # Format column headers (row 75) - Light gray
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 74,  # Row 75
                        "endRowIndex": 75,
                        "startColumnIndex": 0,
                        "endColumnIndex": 8
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9},
                            "textFormat": {"bold": True}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            }
        ]
        
        sheets.batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": requests}
        ).execute()
        
        print("✅ Formatting applied")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = auto_refresh_outages()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ LIVE OUTAGE DATA AUTO-REFRESH COMPLETE")
        print("=" * 80)
        print("\n📊 Outage section updated:")
        print("   • Old data deleted from rows 70-100")
        print("   • LIVE data from BigQuery inserted")
        print("   • Auto-refresh timestamp added")
        print("   • Total unavailable capacity calculated")
        
        # Auto-verify flags after update
        print("\n🔧 Verifying interconnector flags...")
        service = build("sheets", "v4", credentials=SHEETS_CREDS)
        all_complete, num_fixed = verify_and_fix_flags(service, SHEET_ID, verbose=False)
        if num_fixed > 0:
            print(f"   ✅ Fixed {num_fixed} broken flags")
        else:
            print("   ✅ All flags complete")
        
        print("\n🔄 To auto-refresh, run this script periodically:")
        print("   python3 auto_refresh_outages.py")
        print("\n🌐 View Dashboard:")
        print("   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
    else:
        print("\n❌ Auto-refresh failed")
