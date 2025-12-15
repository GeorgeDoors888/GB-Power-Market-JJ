#!/usr/bin/env python3
"""
Read entire Google Sheet and display all data
"""

import pickle
import gspread
import pandas as pd
from datetime import datetime

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Analysis BI Enhanced'

def get_credentials():
    """Load Google Sheets credentials"""
    with open('token.pickle', 'rb') as token:
        return pickle.load(token)

def read_entire_sheet():
    """Read all data from the sheet"""
    print("📖 Reading entire Analysis BI Enhanced sheet...")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to Google Sheets
    creds = get_credentials()
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    # Get all values
    print("🔄 Fetching all data...")
    all_values = sheet.get_all_values()
    
    print(f"✅ Retrieved {len(all_values)} rows\n")
    print("=" * 100)
    
    # Display data by sections
    for i, row in enumerate(all_values, start=1):
        # Skip empty rows
        if not any(cell.strip() for cell in row if cell):
            continue
        
        # Format row
        row_str = f"Row {i:3d}: "
        
        # Show first 8 columns (A-H)
        cells = []
        for j, cell in enumerate(row[:8], start=1):
            if cell.strip():
                col_letter = chr(64 + j)  # A=65, B=66, etc.
                cells.append(f"{col_letter}={cell[:50]}")  # Limit to 50 chars per cell
        
        if cells:
            print(row_str + " | ".join(cells))
        
        # Highlight section headers (rows with formatting)
        first_cell = row[0] if row else ''
        if first_cell and any(keyword in first_cell.upper() for keyword in 
                             ['ANALYSIS', 'CONTROL', 'METRICS', 'GENERATION', 'FREQUENCY', 
                              'PRICE', 'BALANCING', 'ADVANCED', 'CALCULATIONS']):
            print("-" * 100)
    
    print("=" * 100)
    print("\n📊 Summary:")
    print(f"   Total rows: {len(all_values)}")
    print(f"   Total columns: {len(all_values[0]) if all_values else 0}")
    
    # Get sheet properties
    sheet_props = sheet._properties
    print(f"\n📋 Sheet Properties:")
    print(f"   Sheet ID: {sheet_props.get('sheetId', 'N/A')}")
    print(f"   Grid Properties:")
    if 'gridProperties' in sheet_props:
        grid = sheet_props['gridProperties']
        print(f"      Rows: {grid.get('rowCount', 'N/A')}")
        print(f"      Columns: {grid.get('columnCount', 'N/A')}")
    
    # Save to CSV for easier inspection
    csv_path = 'analysis_bi_enhanced_full_export.csv'
    df = pd.DataFrame(all_values)
    df.to_csv(csv_path, index=False, header=False)
    print(f"\n💾 Full data exported to: {csv_path}")
    
    # Show specific sections
    print("\n" + "=" * 100)
    print("🔍 SECTION BREAKDOWN:\n")
    
    sections = {
        'Header': (1, 3),
        'Control Panel': (3, 7),
        'Key Metrics': (7, 15),
        'Generation Mix': (15, 35),
        'System Frequency': (35, 60),
        'Market Prices': (60, 85),
        'Balancing Costs': (85, 110),
        'Advanced Calculations': (112, 140)
    }
    
    for section_name, (start_row, end_row) in sections.items():
        print(f"\n📌 {section_name} (Rows {start_row}-{end_row}):")
        section_data = all_values[start_row-1:end_row] if start_row-1 < len(all_values) else []
        
        if section_data:
            # Show first few non-empty rows of section
            shown = 0
            for row in section_data:
                if any(cell.strip() for cell in row if cell):
                    print(f"   {' | '.join([cell[:40] for cell in row[:6] if cell.strip()])}")
                    shown += 1
                    if shown >= 3:  # Show max 3 rows per section
                        if len(section_data) > 3:
                            print(f"   ... ({len(section_data) - 3} more rows)")
                        break
        else:
            print("   (No data)")
    
    print("\n" + "=" * 100)
    print(f"\n🔗 View online: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")

if __name__ == '__main__':
    read_entire_sheet()
