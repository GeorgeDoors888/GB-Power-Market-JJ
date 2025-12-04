from __future__ import annotations
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

def bq_client():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(project=PROJECT_ID, credentials=creds)

def sheets_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    return gspread.authorize(creds)

def query(sql: str) -> pd.DataFrame:
    return bq_client().query(sql).to_dataframe()

def main():
    gc = sheets_client()
    dash = gc.open_by_key(SPREADSHEET_ID).worksheet("Dashboard")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dash.update("A99", [[f"Last Updated (Demo): {ts}"]])

if __name__ == "__main__":
    main()
