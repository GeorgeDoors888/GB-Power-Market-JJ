#!/usr/bin/env python3
import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
RANGE_NAME = "Live Dashboard v2!A12:C25"
SA_PATH = "/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def verify_sheet():
    print(f"🔍 Checking Sheet: {SHEET_ID}")
    print(f"🎯 Range: {RANGE_NAME}")
    
    if not os.path.exists(SA_PATH):
        print(f"❌ Error: Credentials file not found at {SA_PATH}")
        return

    try:
        creds = Credentials.from_service_account_file(SA_PATH, scopes=SCOPES)
        service = build("sheets", "v4", credentials=creds)
        
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('⚠️ No data found.')
        else:
            print("\n✅ Current Data on Sheet:")
            for row in values:
                print(row)
                
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    verify_sheet()
