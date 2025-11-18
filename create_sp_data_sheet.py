#!/usr/bin/env python3
"""Move settlement period data to separate 'SP_Data' sheet for graphing"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

def create_sp_data_sheet():
    """Create separate sheet for settlement period data"""
    
    print("=" * 80)
    print("📊 CREATING SETTLEMENT PERIOD DATA SHEET")
    print("=" * 80)
    
    # Step 1: Check if 'SP_Data' sheet exists, create if not
    print("\n🔍 Checking for SP_Data sheet...")
    
    try:
        spreadsheet = sheets.get(spreadsheetId=SHEET_ID).execute()
        sheet_names = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        if 'SP_Data' in sheet_names:
            print("✅ SP_Data sheet already exists")
        else:
            print("📝 Creating SP_Data sheet...")
            
            requests = [{
                "addSheet": {
                    "properties": {
                        "title": "SP_Data",
                        "gridProperties": {
                            "rowCount": 100,
                            "columnCount": 10
                        }
                    }
                }
            }]
            
            sheets.batchUpdate(
                spreadsheetId=SHEET_ID,
                body={"requests": requests}
            ).execute()
            
            print("✅ SP_Data sheet created")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Step 2: Read settlement period data from Live Dashboard
    print("\n📡 Reading Live Dashboard data...")
    
    try:
        result = sheets.values().get(
            spreadsheetId=SHEET_ID,
            range='Live Dashboard!A1:J49'
        ).execute()
        
        live_vals = result.get('values', [])
        
        if not live_vals:
            print("❌ No data in Live Dashboard")
            return False
        
        header = live_vals[0]
        
        # Find column indices
        try:
            sp_idx = header.index('SP')
            gen_idx = header.index('Generation_MW')
            demand_idx = header.index('Demand_MW')
        except ValueError as e:
            print(f"❌ Column not found: {e}")
            return False
        
        print(f"✅ Found {len(live_vals)-1} settlement periods")
        
    except Exception as e:
        print(f"❌ Error reading data: {e}")
        return False
    
    # Step 3: Build SP_Data sheet with clean structure
    print("\n🏗️ Building SP_Data sheet...")
    
    sp_data = [
        ['Settlement Period', 'Time', 'Generation (GW)', 'Demand (GW)', 'Net Export (GW)', 'Date'],
    ]
    
    for i in range(1, 49):
        if i < len(live_vals):
            row = live_vals[i]
            
            # SP number
            sp_num = f"SP{i:02d}"
            
            # Time
            hour = (i - 1) // 2
            minute = '00' if (i - 1) % 2 == 0 else '30'
            time_str = f"{hour:02d}:{minute}"
            
            # Generation (MW to GW)
            gen_gw = ''
            if len(row) > gen_idx and row[gen_idx]:
                try:
                    gen_gw = float(row[gen_idx]) / 1000
                except:
                    gen_gw = ''
            
            # Demand (MW to GW)
            demand_gw = ''
            if len(row) > demand_idx and row[demand_idx]:
                try:
                    demand_gw = float(row[demand_idx]) / 1000
                except:
                    demand_gw = ''
            
            # Net Export (Generation - Demand)
            net_export = ''
            if gen_gw and demand_gw:
                net_export = gen_gw - demand_gw
            
            # Date (today)
            from datetime import date
            today = date.today().strftime('%Y-%m-%d')
            
            sp_data.append([
                sp_num,
                time_str,
                gen_gw if gen_gw else '',
                demand_gw if demand_gw else '',
                net_export if net_export else '',
                today
            ])
    
    print(f"✅ Built {len(sp_data)} rows (header + 48 SPs)")
    
    # Step 4: Write to SP_Data sheet
    print("\n💾 Writing to SP_Data sheet...")
    
    try:
        sheets.values().update(
            spreadsheetId=SHEET_ID,
            range='SP_Data!A1',
            valueInputOption="USER_ENTERED",
            body={"values": sp_data}
        ).execute()
        
        print("✅ Data written to SP_Data sheet")
        
    except Exception as e:
        print(f"❌ Error writing: {e}")
        return False
    
    # Step 5: Apply formatting
    print("\n🎨 Applying formatting...")
    
    try:
        # Get sheet ID
        spreadsheet = sheets.get(spreadsheetId=SHEET_ID).execute()
        sp_data_sheet_id = None
        for sheet in spreadsheet.get('sheets', []):
            if sheet['properties']['title'] == 'SP_Data':
                sp_data_sheet_id = sheet['properties']['sheetId']
                break
        
        if sp_data_sheet_id is None:
            print("⚠️ Could not find SP_Data sheet ID")
            return True
        
        requests = [
            # Format header row - blue background
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sp_data_sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": 0,
                        "endColumnIndex": 6
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
            # Freeze header row
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sp_data_sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            },
            # Format number columns
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sp_data_sheet_id,
                        "startRowIndex": 1,
                        "endRowIndex": 49,
                        "startColumnIndex": 2,
                        "endColumnIndex": 5
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
            body={"requests": requests}
        ).execute()
        
        print("✅ Formatting applied")
        
    except Exception as e:
        print(f"⚠️ Formatting error (non-critical): {e}")
    
    return True

if __name__ == "__main__":
    success = create_sp_data_sheet()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ SP_DATA SHEET CREATED")
        print("=" * 80)
        print("\n📊 New 'SP_Data' sheet contains:")
        print("   • Settlement Period (SP01-SP48)")
        print("   • Time (00:00-23:30)")
        print("   • Generation (GW)")
        print("   • Demand (GW)")
        print("   • Net Export (GW) - calculated column")
        print("   • Date")
        print("\n📈 Ready for graphing!")
        print("   Use this sheet as data source for charts")
        print("\n🌐 View Dashboard:")
        print("   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
    else:
        print("\n❌ Failed to create SP_Data sheet")
