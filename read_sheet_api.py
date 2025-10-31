"""Read Google Sheet to understand current layout"""
import gspread
from google.oauth2.service_account import Credentials
import json

SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"

def get_sheets_client():
    """Get authenticated Google Sheets client"""
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        # Try service account first
        creds = Credentials.from_service_account_file(
            'service-account-key.json',
            scopes=SCOPES
        )
        return gspread.authorize(creds)
    except:
        # Fall back to token.pickle
        import pickle
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
        return gspread.authorize(creds)

def main():
    print("📖 Reading spreadsheet layout...")
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Read the buffer zone area A18:H28
    print("\n�� Buffer Zone (A18:H28):")
    buffer_data = sheet.get('A18:H28')
    for i, row in enumerate(buffer_data, start=18):
        print(f"Row {i}: {row}")
    
    # Read generation section to see current format
    print("\n⚡ Generation Section (A7:E17):")
    gen_data = sheet.get('A7:E17')
    for i, row in enumerate(gen_data, start=7):
        print(f"Row {i}: {row}")
    
    # Read REMIT section
    print("\n🔴 REMIT Section (A29:H32):")
    remit_data = sheet.get('A29:H32')
    for i, row in enumerate(remit_data, start=29):
        print(f"Row {i}: {row}")

if __name__ == "__main__":
    main()
