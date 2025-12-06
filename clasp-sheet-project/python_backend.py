#!/usr/bin/env python3
"""
Python Backend for Google Sheets Apps Script Integration
Handles all data processing, BigQuery queries, and calculations

Apps Script calls this via webhook, Python updates the sheet directly
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
import pandas as pd
from datetime import datetime
import json

# Configuration
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def authenticate_sheets():
    """Authenticate with Google Sheets API"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    return gspread.authorize(creds)

def authenticate_bigquery():
    """Authenticate with BigQuery"""
    return bigquery.Client(project=PROJECT_ID, location='US')

def refresh_data():
    """
    Main data refresh function
    This is where all your Python logic lives
    """
    print("🔄 Starting data refresh...")
    
    # Authenticate
    sheets_client = authenticate_sheets()
    bq_client = authenticate_bigquery()
    
    # Open spreadsheet
    sheet = sheets_client.open_by_key(SHEET_ID)
    
    # Example: Query BigQuery
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        AVG(systemSellPrice) as avg_price,
        COUNT(*) as periods
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= CURRENT_DATE() - 7
    GROUP BY date
    ORDER BY date DESC
    LIMIT 10
    """
    
    print("📊 Querying BigQuery...")
    df = bq_client.query(query).to_dataframe()
    
    # Process data (add your logic here)
    print(f"✅ Retrieved {len(df)} rows")
    
    # Update sheet
    try:
        ws = sheet.worksheet('Data')
    except:
        ws = sheet.add_worksheet(title='Data', rows=100, cols=20)
    
    # Clear existing data
    ws.clear()
    
    # Write headers
    headers = df.columns.tolist()
    ws.update(range_name='A1:Z1', values=[headers])
    
    # Write data
    data = df.values.tolist()
    if data:
        ws.update(range_name=f'A2:Z{len(data)+1}', values=data)
    
    print(f"✅ Updated sheet with {len(data)} rows")
    
    # Add timestamp
    try:
        meta = sheet.worksheet('Metadata')
    except:
        meta = sheet.add_worksheet(title='Metadata', rows=10, cols=5)
    
    meta.update(range_name='A1:B2', values=[
        ['Last Updated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ['Rows', len(data)]
    ])
    
    return {
        'success': True,
        'message': f'Updated {len(data)} rows at {datetime.now().strftime("%H:%M:%S")}',
        'rows': len(data)
    }

def apply_formatting(sheet_name):
    """
    Advanced formatting that's easier in Python than Apps Script
    """
    sheets_client = authenticate_sheets()
    sheet = sheets_client.open_by_key(SHEET_ID)
    ws = sheet.worksheet(sheet_name)
    
    # Example: Conditional formatting rules
    # Add your formatting logic here
    
    return {'success': True, 'message': 'Formatting applied'}

if __name__ == '__main__':
    # Test the refresh function
    result = refresh_data()
    print(json.dumps(result, indent=2))
