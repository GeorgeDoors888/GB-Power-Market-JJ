#!/usr/bin/env python3
"""
GB Live Executive Dashboard - Clean Professional Layout
Creates a proper executive KPI dashboard with clear sections
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SHEET_NAME = 'GB Live'
CREDS_FILE = '/home/george/inner-cinema-credentials.json'

def create_executive_dashboard():
    """Create a clean, professional executive dashboard layout"""
    
    # Connect
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    
    print("🎨 BUILDING EXECUTIVE DASHBOARD LAYOUT...")
    
    # Clear entire sheet first
    print("  🧹 Clearing sheet...")
    sheet.clear()
    time.sleep(2)
    
    # Build layout in batches
    updates = []
    
    # ===== HEADER SECTION (Rows 1-3) =====
    updates.append({
        'range': 'A1:L1',
        'values': [['⚡ GB LIVE DASHBOARD — Executive Overview', '', '', '', '', '', '', '', '', '', '', '']]
    })
    
    updates.append({
        'range': 'A2:L2',
        'values': [[f'✅ Live Data | Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '', '', '', '', '', '', '', '', '', '', '']]
    })
    
    # ===== KEY PERFORMANCE INDICATORS (Row 5) =====
    updates.append({
        'range': 'A5:L5',
        'values': [['📊 KEY PERFORMANCE INDICATORS', '', '', '', '', '', '', '', '', '', '', '']]
    })
    
    # KPI Headers (Row 6)
    updates.append({
        'range': 'A6:E6',
        'values': [['Wholesale Price', 'Generation', 'Grid Frequency', 'Demand', 'Net IC Flow']]
    })
    
    # KPI Values (Row 7) - will be populated by data script
    updates.append({
        'range': 'A7:E7',
        'values': [['£0/MWh', '0 GW', '50.0 Hz', '0 GW', '+0.00 GW']]
    })
    
    # ===== GENERATION MIX SECTION (Row 9) =====
    updates.append({
        'range': 'A9:L9',
        'values': [['⚡ GENERATION MIX — Live Breakdown', '', '', '', '', '', '', '', '', '', '', '']]
    })
    
    # Generation table headers (Row 10)
    updates.append({
        'range': 'A10:E10',
        'values': [['Fuel Type', 'Generation (GW)', 'Share (%)', 'Trend', 'Status']]
    })
    
    # Placeholder rows for fuel types (Rows 11-20)
    fuel_placeholders = [
        ['Loading...', '0.00', '0%', '→', 'Pending']
        for _ in range(10)
    ]
    updates.append({
        'range': 'A11:E20',
        'values': fuel_placeholders
    })
    
    # ===== INTERCONNECTORS SECTION =====
    updates.append({
        'range': 'G10:J10',
        'values': [['Interconnector', 'Flow (MW)', 'Direction', 'Status']]
    })
    
    ic_placeholders = [
        ['Loading...', '0', '—', 'Pending']
        for _ in range(10)
    ]
    updates.append({
        'range': 'G11:J20',
        'values': ic_placeholders
    })
    
    # ===== TREND CHARTS SECTION (Row 22) =====
    updates.append({
        'range': 'A22:L22',
        'values': [['📈 INTRADAY TRENDS — Last 24 Hours', '', '', '', '', '', '', '', '', '', '', '']]
    })
    
    updates.append({
        'range': 'A23:C23',
        'values': [['Wind Generation', 'System Demand', 'Wholesale Price']]
    })
    
    # Sparkline placeholders (Row 24)
    updates.append({
        'range': 'A24:C24',
        'values': [['[Chart]', '[Chart]', '[Chart]']]
    })
    
    # Apply all updates
    print("  📝 Writing layout to sheet...")
    sheet.batch_update(updates)
    time.sleep(2)
    
    # Format the sheet
    print("  🎨 Applying formatting...")
    
    # Set column widths
    requests = [
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet.id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,  # Column A
                    'endIndex': 12    # Column L
                },
                'properties': {
                    'pixelSize': 150
                },
                'fields': 'pixelSize'
            }
        },
        # Freeze header rows
        {
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet.id,
                    'gridProperties': {
                        'frozenRowCount': 3
                    }
                },
                'fields': 'gridProperties.frozenRowCount'
            }
        }
    ]
    
    sheet.spreadsheet.batch_update({'requests': requests})
    
    print("\n✅ EXECUTIVE DASHBOARD LAYOUT CREATED!")
    print("\n📋 Layout Structure:")
    print("  • Rows 1-2: Header with live status")
    print("  • Rows 5-7: 5 Key Performance Indicators")
    print("  • Rows 9-20: Generation Mix (10 fuel types)")
    print("  • Rows 10-20: Interconnectors (9 connections)")
    print("  • Rows 22-24: Trend charts (Wind, Demand, Price)")
    print("\n🔄 Run update_gb_live_executive.py to populate with real data")

if __name__ == '__main__':
    create_executive_dashboard()
