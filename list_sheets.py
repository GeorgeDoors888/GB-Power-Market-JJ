import gspread
from google.oauth2.service_account import Credentials
import os

SERVICE_ACCOUNT_FILE = r"/home/george/.config/google-cloud/bigquery-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)

print("Sheets available:")
for ws in ss.worksheets():
    print(f"- {ws.title}")
