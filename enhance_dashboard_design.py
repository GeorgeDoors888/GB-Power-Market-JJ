#!/usr/bin/env python3
"""
Enhance Dashboard Design
========================
Applies a professional and impactful design to the main Dashboard,
improving visual hierarchy, readability, and consistency.

Features:
- Professional color palette for section headers
- Alternating row colors (banding) for data tables
- Consistent fonts and alignment
- Optimized column widths
- Subtle borders for clarity
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- Configuration ---
DASHBOARD_SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = 'inner-cinema-credentials.json'
SHEET_NAME = 'Dashboard'

# --- Formatting Definitions ---

# Fonts
FONT_FAMILY = "Arial"
FONT_NORMAL = {"fontFamily": FONT_FAMILY, "fontSize": 10}
FONT_BOLD = {"fontFamily": FONT_FAMILY, "fontSize": 10, "bold": True}
FONT_HEADER_LARGE = {"fontFamily": FONT_FAMILY, "fontSize": 12, "bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}

# Colors
COLOR_WHITE = {"red": 1, "green": 1, "blue": 1}
COLOR_BLACK = {"red": 0, "green": 0, "blue": 0}
COLOR_HEADER_BLUE = {"red": 0.2, "green": 0.4, "blue": 0.6} # Darker Blue
COLOR_FUEL_GREEN = {"red": 0.3, "green": 0.7, "blue": 0.3} # Darker Green
COLOR_INTERCONNECTOR_BLUE = {"red": 0.3, "green": 0.5, "blue": 0.8}
COLOR_OUTAGE_RED = {"red": 0.8, "green": 0.3, "blue": 0.3}
COLOR_GSP_HEADER = {"red": 0.4, "green": 0.4, "blue": 0.4} # Grey
COLOR_BANDING_LIGHT = {"red": 0.95, "green": 0.95, "blue": 0.95} # Light Grey
COLOR_BANDING_DARK = {"red": 0.9, "green": 0.9, "blue": 0.9} # Darker Grey

# Borders
BORDER_THIN = {"style": "SOLID", "width": 1, "color": {"red": 0.8, "green": 0.8, "blue": 0.8}}

# --- Cell Formats ---

FORMAT_DEFAULTS = {
    "userEnteredFormat": {
        "textFormat": FONT_NORMAL,
        "verticalAlignment": "MIDDLE",
    }
}

FORMAT_SECTION_HEADER = {
    "userEnteredFormat": {
        "backgroundColor": COLOR_HEADER_BLUE,
        "textFormat": FONT_HEADER_LARGE,
        "horizontalAlignment": "CENTER",
    }
}

FORMAT_SUBHEADER_GREEN = {
    "userEnteredFormat": {
        "backgroundColor": COLOR_FUEL_GREEN,
        "textFormat": {"bold": True, "foregroundColor": COLOR_WHITE},
        "horizontalAlignment": "CENTER",
    }
}

FORMAT_SUBHEADER_BLUE = {
    "userEnteredFormat": {
        "backgroundColor": COLOR_INTERCONNECTOR_BLUE,
        "textFormat": {"bold": True, "foregroundColor": COLOR_WHITE},
        "horizontalAlignment": "CENTER",
    }
}

FORMAT_SUBHEADER_RED = {
    "userEnteredFormat": {
        "backgroundColor": COLOR_OUTAGE_RED,
        "textFormat": {"bold": True, "foregroundColor": COLOR_WHITE},
        "horizontalAlignment": "CENTER",
    }
}

FORMAT_SUBHEADER_GREY = {
    "userEnteredFormat": {
        "backgroundColor": COLOR_GSP_HEADER,
        "textFormat": {"bold": True, "foregroundColor": COLOR_WHITE},
        "horizontalAlignment": "CENTER",
    }
}

FORMAT_BANDING_LIGHT = {
    "userEnteredFormat": {"backgroundColor": COLOR_BANDING_LIGHT}
}

FORMAT_RIGHT_ALIGN = {
    "userEnteredFormat": {"horizontalAlignment": "RIGHT"}
}

def get_sheet():
    """Connects to Google Sheets and returns the specific dashboard worksheet."""
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scope)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(DASHBOARD_SHEET_ID)
    return spreadsheet.worksheet(SHEET_NAME)

def build_requests(sheet_id):
    """Builds a list of batchUpdate requests for all formatting changes."""
    requests = []

    # 0. Unmerge everything first to avoid conflicts
    requests.append({"unmergeCells": {"range": {"sheetId": sheet_id}}})

    # 1. Apply default formatting to the whole sheet
    requests.append({
        "repeatCell": {
            "range": {"sheetId": sheet_id},
            "cell": FORMAT_DEFAULTS,
            "fields": "userEnteredFormat(textFormat,verticalAlignment)"
        }
    })

    # 2. Format main section headers
    headers = [
        (3, 4, 0, 6, "📊 SYSTEM METRICS", FORMAT_SECTION_HEADER), # Row 4
        (31, 32, 0, 6, "⚡ OUTAGES", FORMAT_SUBHEADER_RED), # Row 32
        (54, 55, 0, 12, "📊 GSP ANALYSIS", FORMAT_SUBHEADER_GREY), # Row 55
    ]
    for start_row, end_row, start_col, end_col, text, fmt in headers:
        requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col}, "cell": fmt, "fields": "userEnteredFormat"}})
        requests.append({"updateCells": {"rows": [{"values": [{"userEnteredValue": {"stringValue": text}}]}], "start": {"sheetId": sheet_id, "rowIndex": start_row, "columnIndex": start_col}, "fields": "userEnteredValue"}})
        requests.append({"mergeCells": {"range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col}}})

    # 3. Format Fuel & Interconnector headers
    requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 6, "endRowIndex": 7, "startColumnIndex": 0, "endColumnIndex": 3}, "cell": FORMAT_SUBHEADER_GREEN, "fields": "userEnteredFormat"}})
    requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 6, "endRowIndex": 7, "startColumnIndex": 3, "endColumnIndex": 6}, "cell": FORMAT_SUBHEADER_BLUE, "fields": "userEnteredFormat"}})

    # 4. Apply banding and borders to data tables
    tables = [
        (7, 17, 0, 6),   # Fuel & Interconnectors
        (32, 50, 0, 6),  # Outages
        (57, 77, 0, 5),  # GSP Generation
        (57, 77, 7, 12), # GSP Demand
    ]
    for start_row, end_row, start_col, end_col in tables:
        # Banding
        for i in range(start_row, end_row, 2):
            requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": start_col, "endColumnIndex": end_col}, "cell": FORMAT_BANDING_LIGHT, "fields": "userEnteredFormat(backgroundColor)"}})
        # Borders
        requests.append({"updateBorders": {"range": {"sheetId": sheet_id, "startRowIndex": start_row, "endRowIndex": end_row, "startColumnIndex": start_col, "endColumnIndex": end_col}, "top": BORDER_THIN, "bottom": BORDER_THIN, "left": BORDER_THIN, "right": BORDER_THIN, "innerHorizontal": BORDER_THIN, "innerVertical": BORDER_THIN}})

    # 5. Right-align numerical columns
    num_cols = [1, 2, 4, 5, 9, 10, 11] # B, C, E, F, J, K, L
    for col in num_cols:
        requests.append({"repeatCell": {"range": {"sheetId": sheet_id, "startRowIndex": 7, "startColumnIndex": col, "endColumnIndex": col + 1}, "cell": FORMAT_RIGHT_ALIGN, "fields": "userEnteredFormat(horizontalAlignment)"}})

    # 6. Set column widths
    widths = [
        (0, 220), (1, 120), (2, 120),
        (3, 220), (4, 150), (5, 180),
        (6, 20), # Spacer
        (7, 50), (8, 80), (9, 150), (10, 120), (11, 120)
    ]
    for col, width in widths:
        requests.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": col, "endIndex": col + 1}, "properties": {"pixelSize": width}, "fields": "pixelSize"}})

    return requests

def main():
    """Main function to apply the enhanced design."""
    print("🎨 Applying enhanced design to the Dashboard...")
    try:
        dashboard = get_sheet()
        sheet_id = dashboard.id
        
        print("   1. Building formatting requests...")
        requests = build_requests(sheet_id)
        
        print(f"   2. Executing {len(requests)} batch update requests...")
        dashboard.spreadsheet.batch_update({"requests": requests})
        
        # Final touch: Update timestamp
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        dashboard.update('A2', [[f'🎨 Design Updated: {now} | ✅ Auto-refresh enabled']])

        print("\n✅ Design enhancement complete!")
        print(f"   🔗 View Dashboard: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")

    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
