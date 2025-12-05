#!/usr/bin/env python3
"""
Import bod_boalf_7d_summary view to Google Sheets BOD_SUMMARY tab

This enables Dashboard V3 KPI formulas to work without BigQuery Connected Sheets.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
WORKSHEET_NAME = "BOD_SUMMARY"

def main():
    print("📊 Importing bod_boalf_7d_summary to Google Sheets")
    print("="*80)
    
    # Query BigQuery
    print("\n📥 Querying BigQuery...")
    creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
    client = bigquery.Client(project=PROJECT_ID, credentials=creds, location="US")
    
    query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.bod_boalf_7d_summary`
    ORDER BY 
      CASE breakdown
        WHEN 'GB_total' THEN 1
        WHEN 'selected_dno' THEN 2
        WHEN 'vlp_portfolio' THEN 3
      END,
      dno,
      bm_unit_id
    """
    
    df = client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} rows, {len(df.columns)} columns")
    
    # Show summary
    print("\n📊 Data Summary:")
    print(f"   GB Total rows: {len(df[df['breakdown']=='GB_total'])}")
    print(f"   DNO rows: {len(df[df['breakdown']=='selected_dno'])}")
    print(f"   Portfolio rows: {len(df[df['breakdown']=='vlp_portfolio'])}")
    
    # Connect to Sheets
    print("\n📝 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    sheet_creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
    gc = gspread.authorize(sheet_creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    # Create or clear worksheet
    try:
        sheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"   Found existing '{WORKSHEET_NAME}' sheet - clearing...")
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"   Creating new '{WORKSHEET_NAME}' sheet...")
        sheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
    
    # Prepare data
    print("\n✍️  Writing data to Google Sheets...")
    data = [df.columns.tolist()] + df.values.tolist()
    
    # Calculate column range dynamically
    num_cols = len(df.columns)
    col_letter = chr(64 + num_cols) if num_cols <= 26 else f'A{chr(64 + num_cols - 26)}'
    
    # Write in batches to avoid timeout
    batch_size = 500
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        start_row = i + 1
        end_row = start_row + len(batch) - 1
        range_str = f'A{start_row}:{col_letter}{end_row}'
        sheet.update(range_str, batch, value_input_option='USER_ENTERED')
        print(f"   ✅ Wrote rows {start_row}-{end_row}")
    
    # Format header (dynamic column range)
    print("\n🎨 Formatting header...")
    num_cols = len(df.columns)
    col_letter = chr(64 + num_cols) if num_cols <= 26 else f'A{chr(64 + num_cols - 26)}'
    sheet.format(f'A1:{col_letter}1', {
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    print("\n✅ BOD_SUMMARY imported successfully!")
    print(f"\n📊 Summary:")
    print(f"   - Rows: {len(df)}")
    print(f"   - Worksheet: {WORKSHEET_NAME}")
    print(f"   - Spreadsheet: {SPREADSHEET_ID}")
    print("\n📝 Next step: Run python/task4_update_kpi_formulas.py")

if __name__ == "__main__":
    main()
