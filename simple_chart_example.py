#!/usr/bin/env python3
"""
Simple Chart Creation Example
Demonstrates how to create a basic chart in Google Sheets
Based on your example but adapted for OAuth authentication
"""

from googleapiclient.discovery import build
import pickle

# --- Configuration ---
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_ID = 0  # Usually 0 for first sheet, or get from API

print("📊 Simple Chart Creator")
print("=" * 50)

# --- 1. Authenticate (OAuth, not service account) ---
print("🔑 Loading credentials...")
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)

# Refresh if needed
if creds.expired and creds.refresh_token:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
    print("   Token refreshed")

service = build("sheets", "v4", credentials=creds)
print("✅ Connected to Google Sheets API")
print()

# --- 2. Build chart request ---
print("📈 Creating SSP vs Date chart...")

chart_request = {
    "requests": [{
        "addChart": {
            "chart": {
                "spec": {
                    "title": "SSP vs Date - GB Power Market",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {
                                "position": "BOTTOM_AXIS",
                                "title": "Date"
                            },
                            {
                                "position": "LEFT_AXIS",
                                "title": "SSP (£/MWh)"
                            }
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": SHEET_ID,
                                        "startRowIndex": 9,    # Row 10 (0-indexed)
                                        "endRowIndex": 109,    # Row 110
                                        "startColumnIndex": 0,  # Column A
                                        "endColumnIndex": 1     # Column A only
                                    }]
                                }
                            }
                        }],
                        "series": [{
                            "series": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": SHEET_ID,
                                        "startRowIndex": 9,    # Row 10
                                        "endRowIndex": 109,    # Row 110
                                        "startColumnIndex": 9,  # Column J (SSP)
                                        "endColumnIndex": 10    # Column J only
                                    }]
                                }
                            },
                            "targetAxis": "LEFT_AXIS"
                        }]
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": SHEET_ID,
                            "rowIndex": 2,      # Row 3
                            "columnIndex": 12   # Column M
                        },
                        "widthPixels": 600,
                        "heightPixels": 400
                    }
                }
            }
        }
    }]
}

# --- 3. Send chart creation request ---
try:
    response = service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=chart_request
    ).execute()
    
    print("✅ Chart created successfully!")
    print()
    print(f"📄 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
    print()
    print("💡 Chart location: Row 3, Column M (600x400 pixels)")
    print("💡 Data range: Rows 10-110, Columns A (dates) and J (SSP)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting:")
    print("  1. Check SHEET_ID matches your target sheet")
    print("  2. Verify data exists in rows 10-110, columns A and J")
    print("  3. Ensure token.pickle is valid (run refresh_token.py)")
    print("  4. Check column J contains numeric SSP values")
