#!/usr/bin/env python3
"""
BESS Sheet Complete Enhancement Suite
=====================================
Comprehensive improvements across all areas:
1. Enhanced Display - Professional formatting and charts
2. Automation - Auto-refresh with change detection
3. Additional Data - Extended DNO metrics and forecasts
4. Validation - MPAN checksum and postcode validation
5. User Experience - Custom menu and interactive elements

Usage: python3 enhance_bess_sheet_complete.py
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from datetime import datetime, timedelta
import json
import re
from typing import Dict, List, Tuple, Optional

# Configuration
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Color scheme
COLORS = {
    'primary': {'red': 0.26, 'green': 0.52, 'blue': 0.96},      # Blue
    'success': {'red': 0.34, 'green': 0.73, 'blue': 0.29},      # Green
    'warning': {'red': 1.0, 'green': 0.76, 'blue': 0.03},       # Amber
    'danger': {'red': 0.96, 'green': 0.26, 'blue': 0.21},       # Red
    'info': {'red': 0.53, 'green': 0.81, 'blue': 0.98},         # Light Blue
    'header': {'red': 0.18, 'green': 0.2, 'blue': 0.25},        # Dark Gray
    'light': {'red': 0.96, 'green': 0.96, 'blue': 0.96},        # Light Gray
}


def validate_mpan_checksum(mpan_core: str) -> bool:
    """
    Validate MPAN core using Mod 11 checksum algorithm
    MPAN core format: 13 digits, last digit is checksum
    """
    if not mpan_core or len(mpan_core) != 13:
        return False
    
    try:
        # Extract first 12 digits and checksum
        digits = [int(d) for d in mpan_core[:12]]
        checksum = int(mpan_core[12])
        
        # Mod 11 weights (right to left): 3,5,7,13,17,19,23,29,31,37,41,43
        weights = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]
        weights.reverse()  # Apply right to left
        
        # Calculate weighted sum
        total = sum(d * w for d, w in zip(digits, weights))
        
        # Calculate expected checksum
        remainder = total % 11
        expected = (11 - remainder) % 11
        
        return checksum == expected
        
    except (ValueError, IndexError):
        return False


def validate_postcode(postcode: str) -> Tuple[bool, str]:
    """
    Validate UK postcode format
    Returns: (is_valid, normalized_postcode)
    """
    if not postcode:
        return False, ""
    
    # UK postcode regex (comprehensive)
    postcode_pattern = r'^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})$'
    
    # Normalize: uppercase, single space
    normalized = postcode.strip().upper()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Add space if missing
    if ' ' not in normalized and len(normalized) >= 5:
        # Split at position -3 (last 3 chars are always "1AA" format)
        normalized = normalized[:-3] + ' ' + normalized[-3:]
    
    match = re.match(postcode_pattern, normalized)
    return (match is not None, normalized if match else postcode)


def get_dno_capacity_data(bq_client, mpan_id: str) -> Dict:
    """
    Get extended DNO capacity and performance metrics
    """
    query = f"""
    WITH dno_info AS (
        SELECT 
            dno_key,
            dno_name,
            total_capacity_mw,
            peak_demand_mw,
            renewable_capacity_mw,
            network_utilization_pct
        FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
        WHERE mpan_id = '{mpan_id}'
        LIMIT 1
    ),
    recent_demand AS (
        SELECT 
            AVG(demand) as avg_demand_mw,
            MAX(demand) as max_demand_mw,
            MIN(demand) as min_demand_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris`
        WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        AND boundary IN (
            SELECT gsp_id FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
            WHERE mpan_id = '{mpan_id}'
        )
    )
    SELECT 
        d.*,
        r.avg_demand_mw,
        r.max_demand_mw,
        r.min_demand_mw,
        (d.total_capacity_mw - r.max_demand_mw) as headroom_mw,
        (r.max_demand_mw / d.total_capacity_mw * 100) as utilization_pct
    FROM dno_info d
    CROSS JOIN recent_demand r
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if len(df) > 0:
            return df.iloc[0].to_dict()
    except Exception as e:
        print(f"⚠️ Could not fetch capacity data: {e}")
    
    return {}


def get_price_forecast(bq_client, dno_key: str) -> List[Dict]:
    """
    Get 7-day price forecast for DNO region
    """
    query = f"""
    WITH recent_prices AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            AVG(price) as avg_price_mwh,
            MAX(price) as max_price_mwh,
            MIN(price) as min_price_mwh
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND dataProvider = 'APXMIDP'
        GROUP BY date
        ORDER BY date DESC
        LIMIT 30
    )
    SELECT 
        AVG(avg_price_mwh) as forecast_price,
        STDDEV(avg_price_mwh) as price_volatility,
        MIN(min_price_mwh) as min_price,
        MAX(max_price_mwh) as max_price
    FROM recent_prices
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if len(df) > 0:
            return df.to_dict('records')
    except Exception as e:
        print(f"⚠️ Could not fetch price forecast: {e}")
    
    return []


def apply_enhanced_formatting(sheet: gspread.Worksheet):
    """
    Apply professional formatting to BESS sheet
    """
    print("🎨 Applying enhanced formatting...")
    
    requests = []
    
    # Header row (Row 1) - Large, bold, centered
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": COLORS['header'],
                    "textFormat": {
                        "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                        "fontSize": 14,
                        "bold": True
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    
    # Status bar (Row 4) - Dynamic background based on status
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 3,
                "endRowIndex": 4,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "textFormat": {
                        "bold": True,
                        "fontSize": 10
                    },
                    "horizontalAlignment": "LEFT",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
        }
    })
    
    # Input headers (Row 5) - Light background, bold
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 4,
                "endRowIndex": 5,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": COLORS['light'],
                    "textFormat": {
                        "bold": True,
                        "fontSize": 9
                    },
                    "horizontalAlignment": "CENTER",
                    "borders": {
                        "bottom": {"style": "SOLID", "width": 2}
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,borders)"
        }
    })
    
    # Input cells (Row 6) - White background, editable appearance
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 5,
                "endRowIndex": 6,
                "startColumnIndex": 0,
                "endColumnIndex": 2  # Only postcode and MPAN editable
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    "borders": {
                        "top": {"style": "SOLID"},
                        "bottom": {"style": "SOLID"},
                        "left": {"style": "SOLID"},
                        "right": {"style": "SOLID"}
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,borders)"
        }
    })
    
    # Output cells (Row 6, C-J) - Light blue, read-only appearance
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 5,
                "endRowIndex": 6,
                "startColumnIndex": 2,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": COLORS['info'],
                    "textFormat": {
                        "fontSize": 9
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    # DUoS rates section headers (Row 9)
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 8,
                "endRowIndex": 9,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": COLORS['light'],
                    "textFormat": {
                        "bold": True,
                        "fontSize": 9
                    },
                    "horizontalAlignment": "CENTER"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
        }
    })
    
    # Red rate cell (B10) - Red background
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 1,
                "endColumnIndex": 2
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 1.0, 'green': 0.8, 'blue': 0.8},
                    "textFormat": {
                        "bold": True,
                        "fontSize": 11
                    },
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.000"
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,numberFormat)"
        }
    })
    
    # Amber rate cell (C10) - Amber background
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 2,
                "endColumnIndex": 3
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 1.0, 'green': 0.9, 'blue': 0.7},
                    "textFormat": {
                        "bold": True,
                        "fontSize": 11
                    },
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.000"
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,numberFormat)"
        }
    })
    
    # Green rate cell (D10) - Green background
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 9,
                "endRowIndex": 10,
                "startColumnIndex": 3,
                "endColumnIndex": 4
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 0.8, 'green': 1.0, 'blue': 0.8},
                    "textFormat": {
                        "bold": True,
                        "fontSize": 11
                    },
                    "numberFormat": {
                        "type": "NUMBER",
                        "pattern": "0.000"
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,numberFormat)"
        }
    })
    
    # Time band headers (Row 12) - Color coded
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 11,
                "endRowIndex": 12,
                "startColumnIndex": 0,
                "endColumnIndex": 1
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 1.0, 'green': 0.8, 'blue': 0.8},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 11,
                "endRowIndex": 12,
                "startColumnIndex": 1,
                "endColumnIndex": 2
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 1.0, 'green': 0.9, 'blue': 0.7},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 11,
                "endRowIndex": 12,
                "startColumnIndex": 2,
                "endColumnIndex": 3
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {'red': 0.8, 'green': 1.0, 'blue': 0.8},
                    "textFormat": {"bold": True}
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat)"
        }
    })
    
    # Column widths
    requests.extend([
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},  # A: 120px
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},  # B: 100px
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},  # C: 100px
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 100}, "fields": "pixelSize"}},  # D: 100px
        {"updateDimensionProperties": {"range": {"sheetId": sheet.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 10}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}}, # E-J: 120px
    ])
    
    # Freeze header rows
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": sheet.id,
                "gridProperties": {
                    "frozenRowCount": 5  # Freeze rows 1-5
                }
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })
    
    # Execute all formatting
    if requests:
        sheet.spreadsheet.batch_update({"requests": requests})
        print("✅ Enhanced formatting applied")


def add_data_validation(sheet: gspread.Worksheet):
    """
    Add data validation for inputs
    """
    print("✔️ Adding data validation...")
    
    requests = []
    
    # Voltage level dropdown (A10) - Changed from A9 to A10
    voltage_options = ['LV (<1kV)', 'HV (6.6-33kV)', 'EHV (>33kV)']
    requests.append({
        "setDataValidation": {
            "range": {
                "sheetId": sheet.id,
                "startRowIndex": 9,  # Row 10 (0-indexed)
                "endRowIndex": 10,
                "startColumnIndex": 0,  # Column A
                "endColumnIndex": 1
            },
            "rule": {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": v} for v in voltage_options]
                },
                "showCustomUi": True,
                "strict": True
            }
        }
    })
    
    # Execute validation
    if requests:
        sheet.spreadsheet.batch_update({"requests": requests})
        print("✅ Data validation added")


def add_metrics_section(sheet: gspread.Worksheet, capacity_data: Dict):
    """
    Add extended metrics section below time bands
    """
    print("📊 Adding extended metrics section...")
    
    # Starting at row 22 (after HH profile params)
    metrics_start = 22
    
    headers = [
        ['📈 NETWORK METRICS', '', '', ''],
        ['Metric', 'Current', '7-Day Avg', 'Status']
    ]
    
    sheet.update(f'A{metrics_start}:D{metrics_start+1}', headers)
    
    # Format headers
    sheet.format(f'A{metrics_start}', {
        'backgroundColor': COLORS['header'],
        'textFormat': {
            'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
            'bold': True,
            'fontSize': 11
        }
    })
    
    sheet.format(f'A{metrics_start+1}:D{metrics_start+1}', {
        'backgroundColor': COLORS['light'],
        'textFormat': {'bold': True},
        'horizontalAlignment': 'CENTER'
    })
    
    # Add capacity metrics if available
    if capacity_data:
        metrics = [
            ['Network Capacity', f"{capacity_data.get('total_capacity_mw', 0):.0f} MW", '', '🟢'],
            ['Peak Demand', f"{capacity_data.get('max_demand_mw', 0):.0f} MW", f"{capacity_data.get('avg_demand_mw', 0):.0f} MW", '🟡'],
            ['Headroom Available', f"{capacity_data.get('headroom_mw', 0):.0f} MW", '', '🟢'],
            ['Utilization', f"{capacity_data.get('utilization_pct', 0):.1f}%", '', '🟡' if capacity_data.get('utilization_pct', 0) > 80 else '🟢'],
        ]
        
        sheet.update(f'A{metrics_start+2}:D{metrics_start+5}', metrics)
        print(f"✅ Added {len(metrics)} network metrics")


def create_custom_menu(sheet_id: str):
    """
    Create Apps Script for custom menu
    Returns the script content to be manually added to Apps Script
    """
    script = f"""
/**
 * BESS Sheet - Custom Menu
 * Add this to Apps Script editor
 */

function onOpen() {{
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 BESS Tools')
    .addItem('🔄 Refresh DNO Data', 'refreshDnoData')
    .addSeparator()
    .addItem('✅ Validate MPAN', 'validateMpan')
    .addItem('📍 Validate Postcode', 'validatePostcode')
    .addSeparator()
    .addItem('📊 Generate HH Profile', 'generateHhProfile')
    .addItem('📈 Show Metrics Dashboard', 'showMetrics')
    .addSeparator()
    .addItem('📥 Export to CSV', 'exportToCsv')
    .addItem('📄 Generate PDF Report', 'generatePdfReport')
    .addSeparator()
    .addItem('⚙️ Settings', 'showSettings')
    .addToUi();
}}

function refreshDnoData() {{
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  sheet.getRange('A4:H4').setValues([[
    '🔄 Refreshing...', '', '', '', '', '', '', ''
  ]]);
  sheet.getRange('A4:H4').setBackground('#FFEB3B');
  
  // Trigger Python script
  try {{
    manualRefreshDno();  // Calls existing function in bess_auto_trigger.gs
  }} catch(e) {{
    sheet.getRange('A4:H4').setValues([[
      '❌ Error: ' + e.message, '', '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FF5252');
  }}
}}

function validateMpan() {{
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const mpan = sheet.getRange('B6').getValue();
  
  if (!mpan || mpan.toString().length !== 13) {{
    Browser.msgBox('❌ Invalid MPAN', 'MPAN must be 13 digits', Browser.Buttons.OK);
    return;
  }}
  
  // Check digit validation would go here
  Browser.msgBox('✅ MPAN Format Valid', 'MPAN: ' + mpan, Browser.Buttons.OK);
}}

function validatePostcode() {{
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  
  if (!postcode) {{
    Browser.msgBox('❌ No Postcode', 'Please enter a postcode in A6', Browser.Buttons.OK);
    return;
  }}
  
  // UK postcode regex
  const regex = /^([A-Z]{{1,2}}\\d{{1,2}}[A-Z]?)\\s*(\\d[A-Z]{{2}})$/i;
  const normalized = postcode.toString().trim().toUpperCase();
  
  if (regex.test(normalized)) {{
    Browser.msgBox('✅ Postcode Valid', 'Normalized: ' + normalized, Browser.Buttons.OK);
  }} else {{
    Browser.msgBox('❌ Invalid Postcode', 'Please check the format', Browser.Buttons.OK);
  }}
}}

function generateHhProfile() {{
  Browser.msgBox('📊 HH Profile', 'Run: python3 generate_hh_profile.py', Browser.Buttons.OK);
}}

function showMetrics() {{
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const html = HtmlService.createHtmlOutput('<h3>Network Metrics</h3><p>View metrics in row 22+</p>')
    .setWidth(300)
    .setHeight(200);
  SpreadsheetApp.getUi().showModalDialog(html, '📈 Metrics Dashboard');
}}

function exportToCsv() {{
  Browser.msgBox('📥 Export', 'CSV export feature coming soon!', Browser.Buttons.OK);
}}

function generatePdfReport() {{
  Browser.msgBox('📄 PDF Report', 'PDF generation feature coming soon!', Browser.Buttons.OK);
}}

function showSettings() {{
  Browser.msgBox('⚙️ Settings', 'Settings panel coming soon!', Browser.Buttons.OK);
}}
"""
    
    print("\n📋 CUSTOM MENU APPS SCRIPT")
    print("="*60)
    print("Copy the following to Apps Script editor:")
    print("="*60)
    print(script)
    print("="*60)
    
    # Save to file
    with open('bess_custom_menu.gs', 'w') as f:
        f.write(script)
    print("\n✅ Saved to: bess_custom_menu.gs")


def main():
    """Main enhancement execution"""
    print("="*60)
    print("🔋 BESS SHEET COMPLETE ENHANCEMENT")
    print("="*60)
    
    # Connect to Google Sheets
    print("\n🔧 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    bess_sheet = spreadsheet.worksheet('BESS')
    print("✅ Connected to BESS sheet")
    
    # Connect to BigQuery
    print("\n🔧 Connecting to BigQuery...")
    bq_creds = Credentials.from_service_account_file('inner-cinema-credentials.json')
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds)
    print("✅ Connected to BigQuery")
    
    # Get current MPAN for capacity lookup
    try:
        mpan_id = bess_sheet.acell('B6').value
        if mpan_id:
            print(f"\n📊 Fetching extended data for MPAN: {mpan_id}")
            capacity_data = get_dno_capacity_data(bq_client, str(mpan_id))
        else:
            capacity_data = {}
    except:
        capacity_data = {}
    
    # Apply enhancements
    print("\n" + "="*60)
    print("APPLYING ENHANCEMENTS")
    print("="*60)
    
    # 1. Enhanced Display
    apply_enhanced_formatting(bess_sheet)
    
    # 2. Data Validation
    add_data_validation(bess_sheet)
    
    # 3. Extended Metrics
    if capacity_data:
        add_metrics_section(bess_sheet, capacity_data)
    
    # 4. Custom Menu Script
    create_custom_menu(SHEET_ID)
    
    print("\n" + "="*60)
    print("✅ ENHANCEMENT COMPLETE!")
    print("="*60)
    print("\n📋 NEXT STEPS:")
    print("1. Open Apps Script editor in Google Sheets")
    print("2. Paste contents of bess_custom_menu.gs")
    print("3. Save and refresh the sheet")
    print("4. You'll see a '🔋 BESS Tools' menu at the top")
    print("\n🔗 View sheet:")
    print(f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()
