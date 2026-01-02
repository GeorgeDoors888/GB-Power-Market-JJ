#!/usr/bin/env python3
"""
Apply Data Validations to Search Sheet B8-B16
Links dropdown cells to the populated Dropdowns sheet
"""

from googleapiclient.discovery import build
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Search"
CREDS_FILE = "inner-cinema-credentials.json"

# Initialize clients
sheets_creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets_service = build('sheets', 'v4', credentials=sheets_creds)
gc = gspread.authorize(sheets_creds)
wb = gc.open_by_key(SPREADSHEET_ID)
search_sheet = wb.worksheet('Search')

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 APPLYING DATA VALIDATIONS TO SEARCH SHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

# Get sheet ID
sheet_id = search_sheet.id

# Define validations (row indices are 0-based)
validations = [
    {
        'cell': 'B8',
        'row_index': 7,
        'label': 'Fuel/Technology Type',
        'range': 'Dropdowns!C2:C9'  # 6 fuel types
    },
    {
        'cell': 'B9',
        'row_index': 8,
        'label': 'BM Unit ID',
        'range': 'Dropdowns!A2:A1406'  # 1403 BMU IDs
    },
    {
        'cell': 'B10',
        'row_index': 9,
        'label': 'Organization',
        'range': 'Dropdowns!B2:B734'  # 731 organizations
    },
    {
        'cell': 'B11',
        'row_index': 10,
        'label': 'Capacity Range',
        'range': 'Dropdowns!K2:K10'  # Capacity ranges (need to add to populate script)
    },
    {
        'cell': 'B12',
        'row_index': 11,
        'label': 'TEC Project',
        'range': 'Dropdowns!J2:J4'  # TEC projects placeholder
    },
    {
        'cell': 'B13',
        'row_index': 12,
        'label': 'Connection Site',
        'range': 'Dropdowns!L2:L100'  # Connection sites (need to add)
    },
    {
        'cell': 'B14',
        'row_index': 13,
        'label': 'Project Status',
        'range': 'Dropdowns!M2:M10'  # Status options (need to add)
    },
    {
        'cell': 'B15',
        'row_index': 14,
        'label': 'GSP Region',
        'range': 'Dropdowns!D2:D350'  # 347 GSP locations
    },
    {
        'cell': 'B16',
        'row_index': 15,
        'label': 'DNO Operator',
        'range': 'Dropdowns!E2:E17'  # 14 DNO operators
    }
]

# Build batch request
requests = []

for v in validations:
    print(f"   🔧 Setting validation for {v['cell']} ({v['label']}) → {v['range']}")
    
    requests.append({
        'setDataValidation': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': v['row_index'],
                'endRowIndex': v['row_index'] + 1,
                'startColumnIndex': 1,  # Column B
                'endColumnIndex': 2
            },
            'rule': {
                'condition': {
                    'type': 'ONE_OF_RANGE',
                    'values': [{'userEnteredValue': f'={v["range"]}'}]
                },
                'showCustomUi': True,
                'strict': False
            }
        }
    })

# Apply all validations in one batch
print("\n⚡ Applying batch update...")
result = sheets_service.spreadsheets().batchUpdate(
    spreadsheetId=SPREADSHEET_ID,
    body={'requests': requests}
).execute()

print(f"   ✅ Applied {len(requests)} data validations")

print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ DATA VALIDATIONS APPLIED SUCCESSFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Cells now have dropdowns:
   ✅ B8: Fuel/Technology Type (6 options)
   ✅ B9: BM Unit ID (1,403 options)
   ✅ B10: Organization (731 options)
   ⚠️ B11: Capacity Range (needs data in Dropdowns!K)
   ⚠️ B12: TEC Project (placeholder data)
   ⚠️ B13: Connection Site (needs data in Dropdowns!L)
   ⚠️ B14: Project Status (needs data in Dropdowns!M)
   ✅ B15: GSP Region (347 options)
   ✅ B16: DNO Operator (14 options)

🔧 Note: Some dropdowns (B11, B13, B14) need additional data
   in the Dropdowns sheet. Will populate those next.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
