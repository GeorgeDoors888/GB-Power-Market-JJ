
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os

SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

def check_sparklines():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range="Dashboard V3!F11:I11",
        valueRenderOption="FORMULA"
    ).execute()
    
    formulas = result.get('values', [])
    print("Sparkline Formulas:")
    for row in formulas:
        print(row)

if __name__ == "__main__":
    check_sparklines()
