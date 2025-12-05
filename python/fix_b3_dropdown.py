#!/usr/bin/env python3
"""
Fix B3 dropdown on Dashboard V3 - standalone fix for the dropdown issue
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET_NAME = "Dashboard V3"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main():
    # Authenticate
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    
    # Get Dashboard V3 sheet ID
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    dashboard_id = None
    for sheet in meta["sheets"]:
        if sheet["properties"]["title"] == DASHBOARD_SHEET_NAME:
            dashboard_id = sheet["properties"]["sheetId"]
            break
    
    if not dashboard_id:
        print(f"❌ Sheet '{DASHBOARD_SHEET_NAME}' not found")
        return
    
    print(f"📍 Dashboard V3 Sheet ID: {dashboard_id}")
    
    # Build request to add dropdown to B3
    values = [
        "Today – Auto Refresh",
        "Today – Manual",
        "Last 7 Days",
        "Last 30 Days",
        "Year to Date",
    ]
    
    request = {
        "setDataValidation": {
            "range": {
                "sheetId": dashboard_id,
                "startRowIndex": 2,   # row 3 (0-based = 2)
                "endRowIndex": 3,
                "startColumnIndex": 1,  # col B (0-based = 1)
                "endColumnIndex": 2,
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in values],
                },
                "strict": True,
                "showCustomUi": True,
            },
        }
    }
    
    # Execute
    print("🔧 Adding dropdown to B3...")
    body = {"requests": [request]}
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    
    print("✅ B3 dropdown added successfully!")
    print(f"   Options: {', '.join(values)}")
    print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={dashboard_id}")


if __name__ == "__main__":
    main()
