#!/usr/bin/env python3
"""
upload_code_to_sheets.py

Uploads Python scripts and documentation to Google Sheets "Code_Repository" tab
so ChatGPT can read them via Railway Sheets API.

Usage:
    python3 upload_code_to_sheets.py
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

# Configuration
SERVICE_ACCOUNT = 'inner-cinema-credentials.json'
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # BESS Dashboard
SHEET_NAME = 'Code_Repository'

# Files to upload for ChatGPT access
FILES_TO_UPLOAD = [
    # BESS & Revenue Optimization
    'bess_revenue_engine.py',
    'fr_revenue_optimiser.py',
    'chatgptnextsteps.py',
    
    # Dashboard Scripts
    'update_analysis_bi_enhanced.py',
    'realtime_dashboard_updater.py',
    'format_dashboard.py',
    'enhance_dashboard_layout.py',
    
    # Statistical Analysis
    'advanced_statistical_analysis_enhanced.py',
    
    # DNO Lookup
    'dno_lookup_python.py',
    'dno_webhook_server.py',
    
    # Documentation
    'PROJECT_INDEX.md',
    'BESS_ENGINE_DEPLOYMENT.md',
    'PROJECT_CONFIGURATION.md',
    'STOP_DATA_ARCHITECTURE_REFERENCE.md',
    'CHATGPT_GITHUB_ACCESS.md',
    
    # Apps Script
    'bess_auto_trigger.gs',
    'apps_script_code.gs',
    'bess_dno_lookup.gs',
]

def main():
    print("⚡ Uploading code files to Google Sheets for ChatGPT access...")
    
    # Authenticate
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    sh = client.open_by_key(SPREADSHEET_ID)
    
    # Create or clear Code_Repository sheet
    try:
        ws = sh.worksheet(SHEET_NAME)
        ws.clear()
        print(f"✅ Cleared existing {SHEET_NAME} sheet")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(SHEET_NAME, rows=5000, cols=5)
        print(f"✅ Created new {SHEET_NAME} sheet")
    
    # Add header
    ws.update(range_name='A1:D1', values=[[
        'Filename', 'Content', 'Lines', 'Last Updated'
    ]])
    
    # Format header
    ws.format('A1:D1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Upload files
    rows = []
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for filename in FILES_TO_UPLOAD:
        if not os.path.exists(filename):
            print(f"⚠️  Skipping {filename} (not found)")
            continue
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                line_count = len(content.split('\n'))
                
                rows.append([
                    filename,
                    content,
                    line_count,
                    timestamp
                ])
                
                print(f"✅ Uploaded {filename} ({line_count} lines)")
        
        except Exception as e:
            print(f"❌ Error uploading {filename}: {e}")
    
    # Batch upload all rows
    if rows:
        ws.append_rows(rows, value_input_option='RAW')
        print(f"\n✅ Successfully uploaded {len(rows)} files to Google Sheets")
        print(f"\n📊 ChatGPT can now access these files via Railway API:")
        print(f"   POST https://jibber-jabber-production.up.railway.app/sheets_read")
        print(f"   Body: {{\"sheet\":\"{SHEET_NAME}\",\"range\":\"A2:D1000\"}}")
        
        print(f"\n🔍 Example ChatGPT query:")
        print(f'   "Read the Code_Repository sheet from my Google Sheets and show me')
        print(f'    the bess_revenue_engine.py implementation"')
    else:
        print("\n❌ No files were uploaded")
    
    # Add summary sheet
    summary_ws_name = 'Code_Repository_Index'
    try:
        summary_ws = sh.worksheet(summary_ws_name)
        summary_ws.clear()
    except gspread.WorksheetNotFound:
        summary_ws = sh.add_worksheet(summary_ws_name, rows=100, cols=4)
    
    summary_ws.update(range_name='A1:D1', values=[[
        'Category', 'Files', 'Total Lines', 'Description'
    ]])
    
    summary_data = [
        ['BESS Revenue', 
         'bess_revenue_engine.py, fr_revenue_optimiser.py', 
         '2055', 
         'Revenue optimization engines'],
        ['Dashboard', 
         'update_analysis_bi_enhanced.py, realtime_dashboard_updater.py', 
         '~800', 
         'Dashboard refresh scripts'],
        ['Analysis', 
         'advanced_statistical_analysis_enhanced.py', 
         '~500', 
         'Statistical analysis suite'],
        ['DNO Lookup', 
         'dno_lookup_python.py, dno_webhook_server.py', 
         '~400', 
         'DNO lookup system'],
        ['Documentation', 
         'PROJECT_INDEX.md, BESS_ENGINE_DEPLOYMENT.md', 
         '~2000', 
         'Project documentation'],
        ['Apps Script', 
         'bess_auto_trigger.gs, apps_script_code.gs', 
         '~600', 
         'Google Sheets automation'],
    ]
    
    summary_ws.update(range_name='A2:D7', values=summary_data)
    print(f"\n✅ Created index sheet: {summary_ws_name}")

if __name__ == '__main__':
    main()
