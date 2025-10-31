#!/usr/bin/env python3
"""
Read Entire Dashboard via Google Sheets API
Fetches all data from the Analysis BI Enhanced sheet
"""

from googleapiclient.discovery import build
import pickle
from datetime import datetime
import json

print("=" * 80)
print("📊 DASHBOARD READER - Google Sheets API")
print("=" * 80)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Analysis BI Enhanced'

# Load credentials
print("🔑 Loading credentials...")
try:
    with open('token.pickle', 'rb') as f:
        creds = pickle.load(f)
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        print("🔄 Token expired, refreshing...")
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open('token.pickle', 'wb') as f:
            pickle.dump(creds, f)
    
    print("✅ Credentials loaded")
except Exception as e:
    print(f"❌ Error loading credentials: {e}")
    exit(1)

# Build service
print("🔌 Connecting to Google Sheets API...")
try:
    service = build('sheets', 'v4', credentials=creds)
    print("✅ Connected")
except Exception as e:
    print(f"❌ Error connecting: {e}")
    exit(1)

print()
print("=" * 80)
print("📖 Reading Dashboard Data")
print("=" * 80)

# Get spreadsheet metadata
try:
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    print(f"📄 Spreadsheet: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
    print(f"📍 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print()
    
    # List all sheets
    sheets = spreadsheet.get('sheets', [])
    print(f"📑 Available sheets ({len(sheets)}):")
    for sheet in sheets:
        props = sheet.get('properties', {})
        sheet_title = props.get('title', 'Unknown')
        sheet_id = props.get('sheetId', 'Unknown')
        row_count = props.get('gridProperties', {}).get('rowCount', 0)
        col_count = props.get('gridProperties', {}).get('columnCount', 0)
        print(f"   • {sheet_title} (ID: {sheet_id}, {row_count} rows × {col_count} cols)")
    
except Exception as e:
    print(f"❌ Error reading spreadsheet metadata: {e}")
    exit(1)

print()
print("=" * 80)
print(f"📊 Reading Sheet: {SHEET_NAME}")
print("=" * 80)

# Read all data from the target sheet
try:
    # Read entire sheet (up to 1000 rows)
    range_name = f"{SHEET_NAME}!A1:Z1000"
    
    print(f"📍 Range: {range_name}")
    print(f"⏳ Fetching data...")
    
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name,
        valueRenderOption='FORMATTED_VALUE'  # Get formatted values (with £, %, etc.)
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print("❌ No data found in sheet")
        exit(1)
    
    # Display summary
    print(f"✅ Data retrieved")
    print(f"   Rows: {len(values)}")
    print(f"   Columns: {len(values[0]) if values else 0}")
    print()
    
    # Display first 10 rows
    print("=" * 80)
    print("📋 FIRST 10 ROWS")
    print("=" * 80)
    
    for i, row in enumerate(values[:10]):
        # Pad row to ensure consistent column count
        padded_row = row + [''] * (20 - len(row))
        
        if i == 0:
            # Header row
            print(f"\n{i+1:3d} | HEADERS:")
            for j, cell in enumerate(padded_row[:20]):
                if cell:
                    print(f"      Col {chr(65+j):>2s}: {cell}")
        else:
            # Data rows
            print(f"\n{i+1:3d} | ", end="")
            # Show first 5 columns only
            for j, cell in enumerate(padded_row[:5]):
                if j > 0:
                    print(" | ", end="")
                print(f"{str(cell)[:15]:15s}", end="")
    
    print("\n")
    
    # Analyze data structure
    print("=" * 80)
    print("📊 DATA STRUCTURE ANALYSIS")
    print("=" * 80)
    
    if len(values) > 0:
        headers = values[0]
        print(f"\n📌 Column Headers ({len(headers)} columns):")
        for i, header in enumerate(headers):
            if header:
                col_letter = chr(65 + i) if i < 26 else f"{chr(65 + i//26 - 1)}{chr(65 + i%26)}"
                print(f"   {col_letter}: {header}")
        
        # Check for data in rows
        data_rows = [row for row in values[1:] if any(cell for cell in row)]
        print(f"\n📊 Data Rows: {len(data_rows)}")
        
        # Identify column types
        print(f"\n🔍 Sample Data (Row 2):")
        if len(values) > 1:
            for i, (header, value) in enumerate(zip(headers, values[1])):
                if header and value:
                    col_letter = chr(65 + i) if i < 26 else f"{chr(65 + i//26 - 1)}{chr(65 + i%26)}"
                    print(f"   {col_letter} ({header}): {value}")
    
    # Save to JSON for further analysis
    print()
    print("=" * 80)
    print("💾 SAVING DATA")
    print("=" * 80)
    
    output_file = f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    data_export = {
        "spreadsheet_id": SPREADSHEET_ID,
        "sheet_name": SHEET_NAME,
        "timestamp": datetime.now().isoformat(),
        "rows_count": len(values),
        "columns_count": len(values[0]) if values else 0,
        "headers": values[0] if values else [],
        "data": values[1:] if len(values) > 1 else []
    }
    
    with open(output_file, 'w') as f:
        json.dump(data_export, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Data saved to: {output_file}")
    print(f"   Size: {len(json.dumps(data_export))} bytes")
    
    # Also save as CSV
    import csv
    csv_file = f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(values)
    
    print(f"✅ Data saved to: {csv_file}")
    
    print()
    print("=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully read entire dashboard")
    print(f"   Sheet: {SHEET_NAME}")
    print(f"   Rows: {len(values)}")
    print(f"   Columns: {len(values[0]) if values else 0}")
    print(f"   Headers: {len(headers) if values else 0}")
    print(f"   Data rows: {len(data_rows) if values else 0}")
    print()
    print("📁 Output files:")
    print(f"   • {output_file} (JSON format)")
    print(f"   • {csv_file} (CSV format)")
    print()
    print("💡 You can now:")
    print("   • Analyze data with pandas")
    print("   • Create charts programmatically")
    print("   • Export to other formats")
    print("   • Run statistical analysis")
    
except Exception as e:
    print(f"❌ Error reading sheet: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 80)
print("✅ COMPLETE")
print("=" * 80)
