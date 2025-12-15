#!/usr/bin/env python3
"""Redesign Dashboard layout - separate settlement periods from outages"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import date
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SA_PATH = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Credentials
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
BQ_SCOPES = ["https://www.googleapis.com/auth/bigquery"]

SHEETS_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=SHEETS_CREDS).spreadsheets()

BQ_CREDS = Credentials.from_service_account_file(SA_PATH, scopes=BQ_SCOPES)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=BQ_CREDS, location="US")

def clear_and_redesign_dashboard():
    """Clear settlement period section and redesign with proper separation"""
    
    print("=" * 80)
    print("🎨 REDESIGNING DASHBOARD LAYOUT")
    print("=" * 80)
    
    # First, clear the problematic area (rows 18-100) to start fresh
    print("\n🧹 Clearing old settlement period and outage sections...")
    
    try:
        # Clear from row 18 onwards
        sheets.values().clear(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A18:H100'
        ).execute()
        
        print("✅ Cleared rows 18-100")
        
    except Exception as e:
        print(f"❌ Error clearing: {e}")
        return False
    
    # Now rebuild with clean design
    print("\n🎨 Building new layout...")
    
    # Read Live Dashboard data for settlement periods
    result = sheets.values().get(
        spreadsheetId=SHEET_ID,
        range='Live Dashboard!A1:E49'
    ).execute()
    live_vals = result.get('values', [])
    
    # Build Settlement Period section with clean 4-column layout
    sp_section = [
        [''],  # Blank row (row 18)
        ['📈 SETTLEMENT PERIOD DATA', '', '', '', '', '', '', ''],  # Header (row 19)
        ['', '', '', '', '', '', '', ''],  # Blank (row 20)
        ['SP', 'Time', 'Generation (GW)', 'Demand (GW)', '', '', '', '']  # Column headers (row 21)
    ]
    
    # Add settlement period data (rows 22-69 for SP01-SP48)
    if len(live_vals) > 0:
        header = live_vals[0]
        try:
            sp_idx = header.index('SP')
            gen_idx = header.index('Generation_MW')
            demand_idx = header.index('Demand_MW')
        except ValueError as e:
            print(f"⚠️ Column not found: {e}")
            sp_idx = 0
            gen_idx = 4
            demand_idx = 3
        
        for i in range(1, 49):  # SP01-SP48
            if i < len(live_vals):
                row = live_vals[i]
                sp_num = i
                
                # Calculate time from SP number
                hour = (sp_num - 1) // 2
                minute = '00' if (sp_num - 1) % 2 == 0 else '30'
                time_str = f"{hour:02d}:{minute}"
                
                # Get generation (convert MW to GW)
                gen_gw = ''
                if len(row) > gen_idx and row[gen_idx]:
                    try:
                        gen_gw = f"{float(row[gen_idx]) / 1000:.1f}"
                    except:
                        gen_gw = ''
                
                # Get demand (convert MW to GW)
                demand_gw = ''
                if len(row) > demand_idx and row[demand_idx]:
                    try:
                        demand_gw = f"{float(row[demand_idx]) / 1000:.1f}"
                    except:
                        demand_gw = ''
                
                # Add row: SP | Time | Gen | Demand
                sp_section.append([
                    f"SP{sp_num:02d}",
                    time_str,
                    gen_gw,
                    demand_gw,
                    '', '', '', ''
                ])
            else:
                # Empty row if no data
                sp_section.append([f"SP{i:02d}", '', '', '', '', '', '', ''])
    
    # Add separator (row 70)
    sp_section.append(['', '', '', '', '', '', '', ''])
    sp_section.append(['', '', '', '', '', '', '', ''])
    
    print(f"✅ Built settlement period section: {len(sp_section)} rows")
    
    # Get outages data
    print("\n⚠️  Querying power station outages...")
    
    today = date.today()
    query = f"""
    WITH latest_revisions AS (
        SELECT 
            affectedUnit,
            MAX(revisionNumber) as max_rev
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE DATE(eventStartTime) <= '{today}'
          AND (DATE(eventEndTime) >= '{today}' OR eventEndTime IS NULL)
        GROUP BY affectedUnit
    )
    SELECT 
        u.affectedUnit as bmu_id,
        u.assetName,
        u.fuelType,
        u.normalCapacity as normal_mw,
        u.unavailableCapacity as unavail_mw,
        u.cause
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability` u
    INNER JOIN latest_revisions lr
        ON u.affectedUnit = lr.affectedUnit
        AND u.revisionNumber = lr.max_rev
    WHERE DATE(u.eventStartTime) <= '{today}'
      AND (DATE(u.eventEndTime) >= '{today}' OR u.eventEndTime IS NULL)
      AND u.unavailableCapacity > 0
    ORDER BY u.unavailableCapacity DESC
    LIMIT 10
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        
        # Build outages section
        outage_section = [
            ['⚠️ POWER STATION OUTAGES', '', '', '', '', '', '', ''],  # Header
            ['', '', '', '', '', '', '', ''],  # Blank
            ['Asset Name', 'Fuel Type', 'Normal (MW)', 'Unavailable (MW)', '% Unavailable', 'Cause', '', '']  # Column headers
        ]
        
        if len(df) > 0:
            print(f"✅ Found {len(df)} active outages")
            
            for _, row in df.iterrows():
                asset_name = row['assetName'] or row['bmu_id']
                fuel = row['fuelType'] or 'Unknown'
                normal = row['normal_mw'] or 0
                unavail = row['unavail_mw'] or 0
                
                # Calculate percentage
                pct = (unavail / normal * 100) if normal > 0 else 0
                
                # Create visual bar
                blocks = int(pct / 10)
                visual = '🟥' * blocks + '⬜' * (10 - blocks)
                
                # Get cause
                cause = row['cause'] or 'Unknown'
                if len(cause) > 35:
                    cause = cause[:32] + '...'
                
                outage_section.append([
                    asset_name[:30],
                    fuel,
                    f"{normal:.0f}",
                    f"{unavail:.0f}",
                    f"{visual} {pct:.1f}%",
                    cause,
                    '', ''
                ])
        else:
            print("✅ No active outages")
            outage_section.append([
                '✅ All systems operational - no active outages',
                '', '', '', '', '', '', ''
            ])
        
        print(f"✅ Built outages section: {len(outage_section)} rows")
        
    except Exception as e:
        print(f"❌ Error querying outages: {e}")
        outage_section = [
            ['⚠️ POWER STATION OUTAGES', '', '', '', '', '', '', ''],
            ['', '', '', '', '', '', '', ''],
            ['Error loading outage data', '', '', '', '', '', '', '']
        ]
    
    # Combine sections
    all_data = sp_section + outage_section
    
    # Write to Dashboard starting at row 18
    print(f"\n💾 Writing {len(all_data)} rows to Dashboard...")
    
    try:
        sheets.values().update(
            spreadsheetId=SHEET_ID,
            range='Dashboard!A18',
            valueInputOption="USER_ENTERED",
            body={"values": all_data}
        ).execute()
        
        print("✅ Dashboard layout updated")
        
        # Apply formatting colors
        print("\n🎨 Applying color formatting...")
        
        # Get spreadsheet to apply formatting
        # Color scheme:
        # - Settlement Period header: Blue background
        # - Outages header: Red background
        # - Column headers: Light gray background
        
        requests = [
            # Settlement Period header (row 19) - Blue
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,  # Dashboard is usually sheet 0
                        "startRowIndex": 18,
                        "endRowIndex": 19,
                        "startColumnIndex": 0,
                        "endColumnIndex": 8
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat)"
                }
            },
            # SP column headers (row 21) - Light gray
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 20,
                        "endRowIndex": 21,
                        "startColumnIndex": 0,
                        "endColumnIndex": 4  # Only 4 columns now (SP, Time, Gen, Demand)
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
        
        print("✅ Color formatting applied")
        
        # Add number formatting to prevent currency display
        print("\n🔢 Applying number formatting...")
        
        format_requests = [
            # Format Generation and Demand columns (C and D) as numbers with 1 decimal
            {
                "repeatCell": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 21,  # Start from data rows (row 22)
                        "endRowIndex": 69,    # Through SP48 (row 69)
                        "startColumnIndex": 2,  # Column C (Generation)
                        "endColumnIndex": 4     # Column D (Demand)
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "numberFormat": {
                                "type": "NUMBER",
                                "pattern": "0.0"
                            }
                        }
                    },
                    "fields": "userEnteredFormat.numberFormat"
                }
            }
        ]
        
        sheets.batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": format_requests}
        ).execute()
        
        print("✅ Number formatting applied")
        
        return True
        
    except Exception as e:
        print(f"❌ Error writing: {e}")
        return False

if __name__ == "__main__":
    success = clear_and_redesign_dashboard()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ DASHBOARD REDESIGN COMPLETE")
        print("=" * 80)
        print("\n📊 New Layout:")
        print("   Rows 18-20: Blank + Settlement Period header")
        print("   Row 21: Column headers (SP | Time | Gen | Demand)")
        print("   Rows 22-69: SP01-SP48 data (clean 4-column layout)")
        print("   Rows 70-71: Separator")
        print("   Rows 72+: Power Station Outages section (separate)")
        print("\n🎨 Color Scheme:")
        print("   📈 Settlement Period header: Blue background, white text")
        print("   ⚠️  Outages header: To be styled")
        print("   Column headers: Light gray background, bold text")
        print("\n🌐 View Dashboard:")
        print("   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
    else:
        print("\n❌ Redesign failed")
