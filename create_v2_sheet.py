import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/home/george/.config/google-cloud/bigquery-credentials.json'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# The sheet ID provided by the user
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'

try:
    sh = client.open_by_key(SHEET_ID)
    print(f"Spreadsheet found: {sh.title}")
    
    worksheets = sh.worksheets()
    print("Existing worksheets:")
    for ws in worksheets:
        print(f"- {ws.title} (ID: {ws.id})")
        
    # Check if 'Live Dashboard v2' exists
    v2_sheet = None
    try:
        v2_sheet = sh.worksheet("Live Dashboard v2")
        print("Live Dashboard v2 already exists.")
    except gspread.WorksheetNotFound:
        print("Creating Live Dashboard v2...")
        v2_sheet = sh.add_worksheet(title="Live Dashboard v2", rows=100, cols=26)
        print("Live Dashboard v2 created.")

except Exception as e:
    print(f"Error: {e}")
