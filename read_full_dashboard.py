#!/usr/bin/env python3
"""
Read entire Dashboard sheet to diagnose layout issues
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

def read_dashboard():
    """Read entire Dashboard sheet"""
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    dashboard = sh.worksheet('Dashboard')
    
    print("=" * 100)
    print("READING FULL DASHBOARD SHEET")
    print("=" * 100)
    
    # Get all data
    all_data = dashboard.get_all_values()
    
    print(f"\nTotal rows: {len(all_data)}")
    print(f"First row columns: {len(all_data[0]) if all_data else 0}")
    
    # Show first 50 rows with column indicators
    print("\n" + "=" * 100)
    print("FIRST 50 ROWS (with column positions)")
    print("=" * 100)
    
    for i, row in enumerate(all_data[:50], start=1):
        # Pad row to at least 15 columns
        padded = row + [''] * (15 - len(row))
        
        # Show non-empty cells with their column letter
        cells = []
        for col_idx, val in enumerate(padded[:15]):
            if val and val.strip():
                col_letter = chr(65 + col_idx)  # A, B, C, etc.
                # Truncate long values
                display_val = val[:40] + "..." if len(val) > 40 else val
                cells.append(f"{col_letter}{i}:{display_val}")
        
        if cells:
            print(f"Row {i:2d}: {' | '.join(cells)}")
    
    # Show rows 20-40 (outages section)
    print("\n" + "=" * 100)
    print("ROWS 20-40 (OUTAGES SECTION)")
    print("=" * 100)
    
    for i in range(19, min(40, len(all_data))):
        row = all_data[i]
        if any(row):
            padded = row + [''] * (10 - len(row))
            # Show first 10 columns
            row_str = ' | '.join([f"Col{j+1}:{padded[j][:30]}" if padded[j] else '' 
                                  for j in range(10)])
            print(f"Row {i+1}: {row_str}")

if __name__ == "__main__":
    read_dashboard()
