#!/usr/bin/env python3
"""
Write SPARKLINE formulas using raw Google Sheets API v4
Bypasses gspread limitations with cross-sheet references
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SHEET_NAME = 'GB Live'

# Sparkline definitions (fuel types in Column C)
FUEL_SPARKLINES = [
    (11, 1, '#4ECDC4', 20, '💨 Wind'),      # Green
    (12, 2, '#FF6B6B', 10, '🔥 CCGT'),      # Red
    (13, 3, '#FFA07A', 5, '⚛️ Nuclear'),    # Orange
    (14, 4, '#98D8C8', 5, '🌱 Biomass'),    # Teal
    (15, 5, '#F7DC6F', 2, '❓ Other'),      # Yellow
    (16, 6, '#85C1E9', 2, '💧 Pumped'),     # Blue
    (17, 7, '#52B788', 1, '🌊 Hydro'),      # Forest green
    (18, 8, '#E76F51', 1, '🔥 OCGT'),       # Burnt orange
    (19, 9, '#666666', 1, '⚫ Coal'),        # Gray
    (20, 10, '#8B4513', 1, '🛢️ Oil'),       # Brown
]

# Sparkline definitions (interconnectors in Column F)
IC_SPARKLINES = [
    (11, 11, '#0055A4', 2, '🇫🇷 France'),
    (12, 12, '#169B62', 1, '🇮🇪 Ireland'),
    (13, 13, '#FF9B00', 1, '🇳🇱 Netherlands'),
    (14, 14, '#00843D', 1, '🏴 East-West'),
    (15, 15, '#FDDA24', 1, '🇧🇪 Belgium (Nemo)'),
    (16, 16, '#EF3340', 1, '🇧🇪 Belgium (Elec)'),
    (17, 17, '#0055A4', 2, '🇫🇷 IFA2'),
    (18, 18, '#BA0C2F', 2, '🇳🇴 Norway (NSL)'),
    (19, 19, '#C8102E', 2, '🇩🇰 Viking Link'),
    (20, 20, '#169B62', 1, '🇮🇪 Greenlink'),
]


def write_sparklines_v4_api():
    """Write sparkline formulas using raw Sheets API v4"""
    
    # Authenticate
    logging.info("🔐 Authenticating with Google Sheets API v4...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    
    # Prepare batch update request
    requests = []
    
    # Column C - Fuel sparklines
    logging.info("📝 Preparing Column C sparkline formulas (fuel types)...")
    for row, data_row, color, max_val, label in FUEL_SPARKLINES:
        sparkline_formula = (
            f'=SPARKLINE(Data_Hidden!A{data_row}:X{data_row},'
            f'{{"charttype","line";"linewidth",2;"color","{color}";"max",{max_val};"ymin",0}})'
        )
        
        requests.append({
            'updateCells': {
                'range': {
                    'sheetId': 1535990597,  # GB Live sheet ID
                    'startRowIndex': row - 1,
                    'endRowIndex': row,
                    'startColumnIndex': 2,  # Column C (0-indexed)
                    'endColumnIndex': 3
                },
                'rows': [{
                    'values': [{
                        'userEnteredValue': {
                            'formulaValue': sparkline_formula
                        }
                    }]
                }],
                'fields': 'userEnteredValue'
            }
        })
        logging.info(f"   Row {row} ({label}): {sparkline_formula[:80]}...")
    
    # Column F - Interconnector sparklines
    logging.info("📝 Preparing Column F sparkline formulas (interconnectors)...")
    for row, data_row, color, max_val, label in IC_SPARKLINES:
        sparkline_formula = (
            f'=SPARKLINE(Data_Hidden!A{data_row}:X{data_row},'
            f'{{"charttype","line";"linewidth",2;"color","{color}";"max",{max_val};"ymin",0}})'
        )
        
        requests.append({
            'updateCells': {
                'range': {
                    'sheetId': 1535990597,  # GB Live sheet ID
                    'startRowIndex': row - 1,
                    'endRowIndex': row,
                    'startColumnIndex': 5,  # Column F (0-indexed)
                    'endColumnIndex': 6
                },
                'rows': [{
                    'values': [{
                        'userEnteredValue': {
                            'formulaValue': sparkline_formula
                        }
                    }]
                }],
                'fields': 'userEnteredValue'
            }
        })
        logging.info(f"   Row {row} ({label}): {sparkline_formula[:80]}...")
    
    # Execute batch update
    logging.info(f"📤 Sending {len(requests)} sparkline formulas via API v4...")
    body = {'requests': requests}
    
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()
        
        logging.info(f"✅ SUCCESS! Written {len(requests)} sparkline formulas")
        logging.info(f"   Replies: {len(response.get('replies', []))}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ FAILED: {e}")
        return False


def verify_sparklines():
    """Verify sparklines were written correctly using gspread"""
    import gspread
    
    logging.info("\n🔍 VERIFYING SPARKLINES...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    
    # Check Column C (fuel types)
    logging.info("\n📊 Column C (Fuel Types):")
    for row, _, _, _, label in FUEL_SPARKLINES:
        c_val = sheet.cell(row, 3).value
        if c_val and '=SPARKLINE' in str(c_val):
            logging.info(f"   ✅ Row {row} ({label}): Formula present")
        else:
            logging.info(f"   ❌ Row {row} ({label}): {c_val}")
    
    # Check Column F (interconnectors)
    logging.info("\n📊 Column F (Interconnectors):")
    for row, _, _, _, label in IC_SPARKLINES:
        f_val = sheet.cell(row, 6).value
        if f_val and '=SPARKLINE' in str(f_val):
            logging.info(f"   ✅ Row {row} ({label}): Formula present")
        else:
            logging.info(f"   ❌ Row {row} ({label}): {f_val}")


if __name__ == '__main__':
    logging.info("=" * 70)
    logging.info("🚀 WRITING SPARKLINES VIA GOOGLE SHEETS API V4")
    logging.info("=" * 70)
    
    success = write_sparklines_v4_api()
    
    if success:
        logging.info("\n⏳ Waiting 3 seconds for Google Sheets to process...")
        import time
        time.sleep(3)
        
        verify_sparklines()
        
        logging.info("\n" + "=" * 70)
        logging.info("✅ SPARKLINE DEPLOYMENT COMPLETE!")
        logging.info("=" * 70)
        logging.info("\n📋 Next steps:")
        logging.info("   1. Open Google Sheet in browser")
        logging.info("   2. Verify sparklines display in columns C and F")
        logging.info("   3. If successful, integrate into update_bg_live_dashboard.py")
    else:
        logging.error("\n❌ Sparkline deployment FAILED - check errors above")
