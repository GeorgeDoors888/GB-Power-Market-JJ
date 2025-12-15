import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = '/home/george/.config/google-cloud/bigquery-credentials.json'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

sheet_ids = [
    '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA', # User provided
    '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'  # From root .clasp.json
]

for sid in sheet_ids:
    try:
        sh = client.open_by_key(sid)
        print(f"ID: {sid} -> Title: {sh.title}")
    except Exception as e:
        print(f"ID: {sid} -> Error: {e}")
