#!/usr/bin/env python3
"""Quick test to read Data_Hidden rows 22-25 to verify sparkline data availability"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

# Setup
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_PATH = os.path.expanduser('~/inner-cinema-credentials.json')

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
gc = gspread.authorize(creds)

try:
    ss = gc.open_by_key(SPREADSHEET_ID)
    data_hidden = ss.worksheet('Data_Hidden')
    
    print("📊 Checking Data_Hidden for KPI sparkline data (rows 22-25, columns B-AW):\n")
    
    rows = {
        22: 'Wholesale Price',
        23: 'Frequency',
        24: 'Total Generation',
        25: 'Wind Output'
    }
    
    for row_num, label in rows.items():
        # Read B to AW (columns 2-49 = 48 periods)
        values = data_hidden.row_values(row_num)[1:49]  # Skip column A, get B-AW
        
        # Check if we have data
        non_empty = [v for v in values if v and v != '']
        numeric_count = sum(1 for v in non_empty if v.replace('.', '').replace('-', '').isdigit())
        
        print(f"Row {row_num} ({label}):")
        print(f"  Total cells: {len(values)}")
        print(f"  Non-empty: {len(non_empty)}")
        print(f"  Numeric: {numeric_count}")
        print(f"  First 5 values: {values[:5]}")
        print(f"  Last 5 values: {values[-5:]}")
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")
