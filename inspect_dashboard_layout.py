
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import os
import json

SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
SHEET_NAME = "Dashboard V3"

def inspect_dashboard():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("sheets", "v4", credentials=creds)
    
    # Get sheet metadata (row heights, merges)
    spreadsheet = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        ranges=[SHEET_NAME],
        includeGridData=True
    ).execute()
    
    sheet = spreadsheet['sheets'][0]
    
    print(f"Sheet ID: {sheet['properties']['sheetId']}")
    
    # Check Row Heights
    row_metadata = sheet['data'][0].get('rowMetadata', [])
    print("\n--- Row Heights (Indices 8-15) ---")
    for i in range(8, 16):
        if i < len(row_metadata):
            meta = row_metadata[i]
            print(f"Row {i+1}: {meta.get('pixelSize', 'default')}px")
            
    # Check Merges
    merges = sheet.get('merges', [])
    print("\n--- Merged Regions ---")
    for merge in merges:
        start_row = merge['startRowIndex']
        end_row = merge['endRowIndex']
        start_col = merge['startColumnIndex']
        end_col = merge['endColumnIndex']
        # Only show merges relevant to the sparkline area (approx rows 9-15, cols F-L)
        if start_row < 20 and start_col > 4:
            print(f"Merge: R{start_row+1}:R{end_row} x C{start_col+1}:C{end_col}")

    # Check Cell Formats (Colors) for KPI Header (Row 9, Index 8)
    print("\n--- KPI Header Colors (Row 9) ---")
    row_data = sheet['data'][0].get('rowData', [])
    if len(row_data) > 8:
        cells = row_data[8].get('values', [])
        for i, cell in enumerate(cells):
            if i >= 5 and i <= 11: # F to L
                bg = cell.get('userEnteredFormat', {}).get('backgroundColor', {})
                print(f"Col {chr(65+i)}: {bg}")

if __name__ == "__main__":
    inspect_dashboard()
