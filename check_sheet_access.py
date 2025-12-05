
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os

SERVICE_ACCOUNT_FILE = "workspace-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def check_spreadsheet(spreadsheet_id):
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=creds)
        
        print(f"Checking spreadsheet: {spreadsheet_id}")
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        print(f"✅ Success! Spreadsheet title: {spreadsheet['properties']['title']}")
        print(f"URL: {spreadsheet['spreadsheetUrl']}")
        return True
    except Exception as e:
        print(f"❌ Error accessing spreadsheet {spreadsheet_id}: {e}")
        return False

# Check the ID we've been using
check_spreadsheet("1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc")

# Check the other ID found in grep
check_spreadsheet("12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
