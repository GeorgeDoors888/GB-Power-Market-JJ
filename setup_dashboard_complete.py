#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

print("🚀 DASHBOARD V3 - COMPLETE SETUP")
print("=" * 60)

# gspread setup
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_gs = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds_gs)
ss = gc.open_by_key(SPREADSHEET_ID)
dash = ss.worksheet('Dashboard')

# Sheets API setup
creds_api = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=creds_api)

print("\n1️⃣ Setting up filter dropdowns...")

# Get sheet ID
sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
dash_id = None
for sheet in sheet_metadata['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        dash_id = sheet['properties']['sheetId']
        break

# Time Range dropdown (B3)
dash.update([['24h']], 'B3')
requests = [{
    "setDataValidation": {
        "range": {"sheetId": dash_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 2},
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in ['1h', '4h', '12h', '24h', '48h', '7d']]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
}]
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
print("   ✅ Time Range dropdown (B3)")

# Region dropdown (D3)
dash.update([['All GB']], 'D3')
requests = [{
    "setDataValidation": {
        "range": {"sheetId": dash_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 3, "endColumnIndex": 4},
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in ['All GB', 'Scotland', 'England', 'Wales', 'N.Ireland']]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
}]
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
print("   ✅ Region dropdown (D3)")

# Alert Type dropdown (F3)
dash.update([['All']], 'F3')
requests = [{
    "setDataValidation": {
        "range": {"sheetId": dash_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 5, "endColumnIndex": 6},
        "rule": {
            "condition": {
                "type": "ONE_OF_LIST",
                "values": [{"userEnteredValue": v} for v in ['All', 'High', 'Medium', 'Low', 'Critical']]
            },
            "showCustomUi": True,
            "strict": True
        }
    }
}]
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
print("   ✅ Alert Type dropdown (F3)")

# Date pickers
today = datetime.now()
week_ago = today - timedelta(days=7)

dash.update([['From:']], 'H3')
dash.update([[week_ago.strftime('%Y-%m-%d')]], 'I3')
dash.update([['To:']], 'J3')
dash.update([[today.strftime('%Y-%m-%d')]], 'K3')

requests = [
    {
        "setDataValidation": {
            "range": {"sheetId": dash_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 8, "endColumnIndex": 9},
            "rule": {"condition": {"type": "DATE_IS_VALID"}, "showCustomUi": True}
        }
    },
    {
        "setDataValidation": {
            "range": {"sheetId": dash_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 10, "endColumnIndex": 11},
            "rule": {"condition": {"type": "DATE_IS_VALID"}, "showCustomUi": True}
        }
    }
]
service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={"requests": requests}).execute()
print("   ✅ Date pickers (I3, K3)")

print("\n2️⃣ Creating chart sheets...")
for sheet_name in ['Chart_Prices', 'Chart_Demand_Gen', 'Chart_IC_Import', 'Chart_BM_Costs', 'Chart_Outages']:
    try:
        ss.worksheet(sheet_name)
        print(f"   ✅ {sheet_name} exists")
    except:
        ss.add_worksheet(title=sheet_name, rows=100, cols=10)
        print(f"   ✅ {sheet_name} created")

print("\n3️⃣ Setting header and labels...")
dash.update([['⚡ GB Power Market Dashboard V3']], 'A1')
dash.update([[f'⚡ Live Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']], 'A2')
dash.update([['🔍 Filters:']], 'A3')
dash.update([['Region:']], 'C3')
dash.update([['Alert:']], 'E3')
print("   ✅ All labels set")

print("\n✅ DASHBOARD SETUP COMPLETE!")
print("   • All dropdowns working")
print("   • Date pickers with calendar UI") 
print("   • All chart sheets created")
