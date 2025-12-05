#!/usr/bin/env python3
"""
Load VLP Documents from CSV to Google Sheets
Uses vlp_documents_complete.csv (1,391 documents)
"""

import os
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"  # Sheet 2 (Dashboard V3)
SHEET_NAME = "VLP Documents"
CSV_FILE = "vlp_documents_complete.csv"
CREDENTIALS_PATH = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")

def main():
    """Load CSV data into Google Sheets with status analysis"""
    
    # Load CSV
    print(f"📂 Loading {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE)
    
    print(f"✅ Loaded {len(df)} documents")
    
    # Add Status column based on chunk_count
    def determine_status(chunk_count):
        if chunk_count >= 100:
            return "Complete"
        elif chunk_count >= 20:
            return "Partial"
        else:
            return "Missing"
    
    df['status'] = df['chunk_count'].apply(determine_status)
    
    # Prepare data for Sheets (exclude doc_id for cleaner view, keep for reference)
    df_sheets = df[['doc_id', 'title', 'source', 'doc_type', 'scraped_date', 'chunk_count', 'url', 'status']].copy()
    
    # Add empty column for sparkline (will be inserted by Apps Script)
    df_sheets.insert(7, 'trend', '')
    
    # Reorder columns: doc_id, title, source, doc_type, scraped_date, chunk_count, url_link, trend, status
    df_sheets = df_sheets[['doc_id', 'title', 'source', 'doc_type', 'scraped_date', 'chunk_count', 'url', 'trend', 'status']]
    
    # Convert to list of lists for Sheets API
    values = df_sheets.values.tolist()
    
    # Authenticate with Google Sheets API
    print("🔐 Authenticating with Google Sheets...")
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    service = build('sheets', 'v4', credentials=credentials)
    
    # Check if sheet exists, create if not
    print(f"🔍 Checking if '{SHEET_NAME}' sheet exists...")
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheet_exists = any(sheet['properties']['title'] == SHEET_NAME for sheet in spreadsheet['sheets'])
    
    if not sheet_exists:
        print(f"📄 Creating '{SHEET_NAME}' sheet...")
        request_body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': SHEET_NAME
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=request_body
        ).execute()
        print(f"✅ Sheet '{SHEET_NAME}' created")
        
        # Add headers
        headers = [["Document ID", "Title", "Source", "Document Type", "Scraped Date", "Chunk Count", "URL", "Trend", "Status"]]
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()
    else:
        # Clear existing data (keep headers)
        print(f"🧹 Clearing existing data in '{SHEET_NAME}'...")
        range_to_clear = f"{SHEET_NAME}!A2:Z10000"
        service.spreadsheets().values().clear(
            spreadsheetId=SPREADSHEET_ID,
            range=range_to_clear
        ).execute()
    
    # Write data
    print(f"📝 Writing {len(values)} rows to Google Sheets...")
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2",
        valueInputOption='RAW',
        body=body
    ).execute()
    
    print(f"✅ Updated {result.get('updatedCells')} cells")
    
    # Summary statistics
    print("\n📊 Summary:")
    print(f"  Total documents: {len(df)}")
    print(f"  Complete (≥100 chunks): {len(df[df['status'] == 'Complete'])}")
    print(f"  Partial (20-99 chunks): {len(df[df['status'] == 'Partial'])}")
    print(f"  Missing (<20 chunks): {len(df[df['status'] == 'Missing'])}")
    print(f"\n  Total chunks: {df['chunk_count'].sum():,}")
    print(f"  Avg chunks/doc: {df['chunk_count'].mean():.1f}")
    print(f"\n  By source:")
    for source, count in df['source'].value_counts().head(5).items():
        print(f"    {source}: {count}")
    
    print(f"\n✅ Data loaded successfully!")
    print(f"🔗 Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    print(f"\n📋 Next steps:")
    print(f"  1. Open the spreadsheet")
    print(f"  2. Click: 📄 VLP Documents → 🎨 Format Dashboard")
    print(f"  3. Click: 📄 VLP Documents → 📊 Insert Sparklines")
    print(f"  4. Click: 📄 VLP Documents → ✅ Apply Conditional Formatting")
    print(f"  5. Click: 📄 VLP Documents → 📈 Generate Summary Report")

if __name__ == "__main__":
    main()
