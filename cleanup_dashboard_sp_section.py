#!/usr/bin/env python3
"""Remove settlement period table from Dashboard - it's now in SP_Data sheet"""

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SA_PATH = "inner-cinema-credentials.json"
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_file(SA_PATH, scopes=SHEETS_SCOPES)
sheets = build("sheets", "v4", credentials=creds).spreadsheets()

print("=" * 80)
print("🧹 CLEANING UP DASHBOARD - REMOVING SP TABLE")
print("=" * 80)

# Remove settlement period section (rows 18-69)
print("\n🗑️  Removing settlement period table from Dashboard...")
print("   (Data is now in SP_Data sheet for graphing)")

try:
    sheets.values().clear(
        spreadsheetId=SHEET_ID,
        range='Dashboard!A18:H69'
    ).execute()
    
    print("✅ Settlement period table removed from Dashboard")
    
    # Add a note pointing to SP_Data sheet
    note_section = [
        [''],
        ['📊 SETTLEMENT PERIOD DATA', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['Data has been moved to the "SP_Data" sheet for cleaner graphing and analysis.', '', '', '', '', '', '', ''],
        ['', '', '', '', '', '', '', ''],
        ['👉 View settlement period data: Go to SP_Data sheet', '', '', '', '', '', '', ''],
        ['📈 Create charts: Insert → Chart, select data from SP_Data sheet', '', '', '', '', '', '', ''],
    ]
    
    sheets.values().update(
        spreadsheetId=SHEET_ID,
        range='Dashboard!A18',
        valueInputOption="USER_ENTERED",
        body={"values": note_section}
    ).execute()
    
    print("✅ Added note pointing to SP_Data sheet")
    
    # Format the note
    print("\n🎨 Formatting note section...")
    
    requests = [
        # Format header
        {
            "repeatCell": {
                "range": {
                    "sheetId": 0,
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
        }
    ]
    
    sheets.batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": requests}
    ).execute()
    
    print("✅ Formatting applied")
    
    print("\n" + "=" * 80)
    print("✅ DASHBOARD CLEANED UP")
    print("=" * 80)
    print("\n📊 Dashboard now shows:")
    print("   • Header with metrics (rows 1-6)")
    print("   • Fuel breakdown + Interconnectors (rows 7-17)")
    print("   • Note pointing to SP_Data sheet (rows 18-24)")
    print("   • Live outage data (rows 70+)")
    print("\n📈 Settlement period data:")
    print("   • Located in SP_Data sheet")
    print("   • Clean format for graphing")
    print("   • Ready for charts/analysis")
    print("\n🌐 View Dashboard:")
    print("   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")

except Exception as e:
    print(f"❌ Error: {e}")
