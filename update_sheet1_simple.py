#!/usr/bin/env python3
"""
Simple Sheet1 Update - Add Navigation Links to Analysis Sheets
"""

from googleapiclient.discovery import build
import pickle

print("📊 Updating Sheet1 with Analysis Navigation")
print("=" * 60)

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

# Load credentials
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
service = build('sheets', 'v4', credentials=creds)

# Get sheet IDs
spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
sheet_ids = {}
for sheet in spreadsheet.get('sheets', []):
    title = sheet['properties']['title']
    sheet_ids[title] = sheet['properties']['sheetId']

print("\n✅ Found sheets:")
for title, sid in sheet_ids.items():
    print(f"   • {title} (ID: {sid})")

# Create navigation section for Sheet1
navigation_data = [
    [''],
    ['═══════════════════════════════════════════════════'],
    ['📊 UK POWER MARKET ANALYSIS DASHBOARD'],
    ['═══════════════════════════════════════════════════'],
    [''],
    ['📈 ANALYSIS TOOLS:'],
    [''],
    ['1️⃣  Latest Day Chart', '→ See chart below at Row 18'],
    [''],
    ['2️⃣  Latest Day Data', f'=HYPERLINK("#gid={sheet_ids.get("Latest Day Data", 0)}", "View Settlement Period Data →")'],
    [''],
    ['3️⃣  Analysis BI Enhanced', f'=HYPERLINK("#gid={sheet_ids.get("Analysis BI Enhanced", 0)}", "View Enhanced BI Analysis →")'],
    [''],
    ['═══════════════════════════════════════════════════'],
    [''],
    ['⚠️  DATA STATUS:'],
    ['• Data currently 3 days old (bmrs_indo table lag)'],
    ['• IRIS real-time pipeline deployment in progress'],
    ['• Once deployed: 30s-2min latency vs current 3-6 days'],
    [''],
]

# Write to Sheet1
try:
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'Sheet1!A1:C{len(navigation_data)}',
        valueInputOption='USER_ENTERED',  # Process formulas
        body={'values': navigation_data}
    ).execute()
    print(f"\n✅ Updated Sheet1 with navigation (rows 1-{len(navigation_data)})")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n🔗 View spreadsheet:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0")
print("\n✅ Complete!")
