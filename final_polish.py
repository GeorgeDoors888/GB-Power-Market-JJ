#!/usr/bin/env python3
"""
Dashboard Final Polish
======================
A comprehensive script to clean, standardize, and apply a final polished
design to the GB Power Market Dashboard.

This script addresses:
- Inconsistent interconnector names and missing flags.
- Unwanted empty rows and large spaces.
- Messy or inconsistent formatting.

It performs a full reset before applying the final design.
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Configuration ---
DASHBOARD_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_NAME = 'Dashboard'

# --- Standardized Data ---
# Definitive list of interconnectors and their display names
INTERCONNECTOR_MAP = {
    "IFA": "🇫🇷 IFA (France)",
    "IFA2": "🇫🇷 IFA2 (France)",
    "ElecLink": "🇫🇷 ElecLink (France)",
    "BritNed": "🇳🇱 BritNed (Netherlands)",
    "Moyle": "🇮🇪 Moyle (Ireland)",
    "EWIC": "🇮🇪 East-West (Ireland)",
    "Greenlink": "🇮🇪 Greenlink (Ireland)",
    "Nemo Link": "🇧🇪 Nemo Link (Belgium)",
    "North Sea Link": "🇳🇴 NSL (Norway)",
    "Viking Link": "🇩🇰 Viking Link (Denmark)",
}

# --- Formatting Definitions ---
FONT_FAMILY = "Arial"
COLOR_WHITE = {"red": 1, "green": 1, "blue": 1}
COLOR_HEADER_BLUE = {"red": 0.15, "green": 0.3, "blue": 0.5}
COLOR_SECTION_HEADER_BG = {"red": 0.9, "green": 0.9, "blue": 0.9}
BORDER_THIN_GREY = {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}

def get_sheet():
    """Connects to Google Sheets and returns the dashboard worksheet."""
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)

def standardize_interconnectors(dashboard):
    """Reads interconnector data, standardizes names, and applies flags."""
    print("   2. Standardizing interconnector names and flags...")
    try:
        # Read the current data from the interconnector column
        current_names = dashboard.get('D8:D17')
        
        update_requests = []
        for i, row in enumerate(current_names):
            if not row: continue
            cell_value = row[0]
            
            # Find the correct standardized name
            for key, standard_name in INTERCONNECTOR_MAP.items():
                if key.lower() in cell_value.lower():
                    update_requests.append({
                        'range': f'D{8+i}',
                        'values': [[standard_name]],
                    })
                    break
        
        if update_requests:
            dashboard.batch_update(update_requests)
            print(f"      ✅ Standardized {len(update_requests)} interconnector(s).")
        else:
            print("      ℹ️ No interconnectors needed standardization.")
            
    except Exception as e:
        print(f"      ❌ Error standardizing interconnectors: {e}")


def apply_final_polish(dashboard):
    """Applies a clean, uniform, and professional design."""
    sheet_id = dashboard.id
    requests = []

    print("   3. Building final design requests...")

    # --- Step 1: Full Clean-up ---
    # Unmerge all cells to prevent errors
    requests.append({"unmergeCells": {"range": {"sheetId": sheet_id}}})
    # Clear all formatting from a large range
    requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "endRowIndex": 100}, "cell": {"userEnteredFormat": {}}, "fields": "userEnteredFormat"}})
    # Delete empty rows that cause large spaces
    # Note: This is complex via API, manual deletion is better.
    # We will rely on setting uniform row heights instead.

    # --- Step 2: Set Uniform Dimensions ---
    # Set a standard row height for all rows
    requests.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": 0, "endIndex": 100}, "properties": {"pixelSize": 21}, "fields": "pixelSize"}})
    # Set specific column widths
    col_widths = [
        (0, 220), (1, 120), (2, 120), (3, 220), (4, 150), (5, 180),
        (6, 20), # Spacer
        (7, 50), (8, 80), (9, 150), (10, 120), (11, 120)
    ]
    for col, width in col_widths:
        requests.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})

    # --- Step 3: Apply New Formatting ---
    # Main Title Header
    requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1}, "cell": {"userEnteredFormat": {"backgroundColor": COLOR_HEADER_BLUE, "textFormat": {"fontFamily": FONT_FAMILY, "fontSize": 14, "bold": True, "foregroundColor": COLOR_WHITE}}}, "fields": "userEnteredFormat"}})
    requests.append({"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 12}}})

    # Section Headers (System, Outages, GSP)
    section_headers = [(3, "📊 SYSTEM METRICS"), (19, "⚡ OUTAGES"), (35, "📊 GSP ANALYSIS")]
    for row_index, text in section_headers:
        requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": row_index, "endRowIndex": row_index + 1}, "cell": {"userEnteredFormat": {"backgroundColor": COLOR_SECTION_HEADER_BG, "textFormat": {"bold": True}}}, "fields": "userEnteredFormat"}})
        requests.append({"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": row_index, "endRowIndex": row_index + 1, "startColumnIndex": 0, "endColumnIndex": 12}}})

    # Apply borders to data areas
    border_ranges = [
        (5, 16, 0, 6),  # Fuel & Interconnectors
        (20, 31, 0, 6), # Outages
        (37, 55, 0, 4), # GSP Generation
        (37, 55, 7, 11) # GSP Demand
    ]
    for start_row, end_row, start_col, end_col in border_ranges:
        requests.append({"updateBorders": {"range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col}, "top": BORDER_THIN_GREY, "bottom": BORDER_THIN_GREY, "left": BORDER_THIN_GREY, "right": BORDER_THIN_GREY, "innerHorizontal": BORDER_THIN_GREY, "innerVertical": BORDER_THIN_GREY}})

    # --- Step 4: Execute Batch Update ---
    print(f"   4. Executing {len(requests)} batch requests for final design...")
    dashboard.spreadsheet.batch_update({"requests": requests})


def main():
    """Main function to run the final polish process."""
    print("🛁 Applying Final Polish to Dashboard...")
    try:
        dashboard = get_sheet()
        
        print("   1. Reading current sheet state...")
        # This step is implicitly done by the gspread library
        
        # First, standardize the names which is a data operation
        standardize_interconnectors(dashboard)
        
        # Second, apply all formatting changes
        apply_final_polish(dashboard)

        # Final touch: Update title
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dashboard.update('A1', [[f'GB Power Market Dashboard | Last Polished: {now}']])

        print("\n✅ Final polish complete! The design is now clean and uniform.")
        print(f"   🔗 View Dashboard: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")

    except Exception as e:
        print(f"\n❌ An error occurred during the final polish: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
