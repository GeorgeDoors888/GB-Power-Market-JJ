"""
Improve Dashboard Design & Layout
- Fix header section
- Improve spacing and organization
- Add visual separators
- Clean up GSP section
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
from datetime import datetime

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDS_FILE = "inner-cinema-credentials.json"

def improve_dashboard_layout():
    """Improve the Dashboard layout and design"""
    
    print("🎨 IMPROVING DASHBOARD DESIGN & LAYOUT")
    print("=" * 80)
    
    # Setup credentials
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    
    sheets_service = build('sheets', 'v4', credentials=creds)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    # 1. Fix Header Section (Rows 1-6)
    print("\n1️⃣ Fixing header section...")
    
    # Row 1: Title
    dashboard.update('A1:F1', [['File: Dashboard', '', '', '', '', '']], value_input_option='RAW')
    
    # Row 2: Timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dashboard.update('A2:F2', [[f'⏰ Last Updated: {timestamp} | ✅ Auto-refresh enabled', '', '', '', '', '']], value_input_option='RAW')
    
    # Row 3: Data freshness legend
    dashboard.update('A3:F3', [['Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min', '', '', '', '', '']], value_input_option='RAW')
    
    # Row 4: System metrics header
    dashboard.update('A4:F4', [['📊 SYSTEM METRICS', '', '', '', '', '']], value_input_option='RAW')
    
    # Row 5: System summary (read current values)
    current_row5 = dashboard.get('A5')[0][0] if dashboard.get('A5') else ''
    if 'Total Generation' in current_row5:
        # Keep existing if valid
        pass
    else:
        # Set placeholder
        dashboard.update('A5:F5', [['Total Generation: XX.X GW | Supply: XX.X GW | Demand: XX.X GW | Imbalance: ±X.X GW | Freq: XX.XX Hz | Price: £X.XX/MWh', '', '', '', '', '']], value_input_option='RAW')
    
    # Row 6: Blank spacer
    dashboard.update('A6:F6', [['', '', '', '', '', '']], value_input_option='RAW')
    
    print("   ✅ Header section fixed (Rows 1-6)")
    
    # 2. Format header section
    print("\n2️⃣ Formatting header section...")
    
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {"bold": True, "fontSize": 14},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 1,
                    "endRowIndex": 2,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.97},
                        "textFormat": {"bold": True},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 2,
                    "endRowIndex": 3,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 1.0, "green": 0.95, "blue": 0.80},
                        "textFormat": {"bold": True, "fontSize": 9},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 3,
                    "endRowIndex": 4,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.86},
                        "textFormat": {"bold": True, "fontSize": 12, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 4,
                    "endRowIndex": 5,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95},
                        "textFormat": {"bold": True, "fontSize": 10},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": requests}
    ).execute()
    
    print("   ✅ Header formatting applied")
    
    # 3. Format Fuel & Interconnectors section headers (Row 7)
    print("\n3️⃣ Formatting Fuel & Interconnectors headers...")
    
    fuel_interconn_requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 6,
                    "endRowIndex": 7,
                    "startColumnIndex": 0,
                    "endColumnIndex": 3
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.4, "green": 0.85, "blue": 0.4},
                        "textFormat": {"bold": True, "fontSize": 11},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 6,
                    "endRowIndex": 7,
                    "startColumnIndex": 3,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.4, "green": 0.7, "blue": 0.9},
                        "textFormat": {"bold": True, "fontSize": 11},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": fuel_interconn_requests}
    ).execute()
    
    print("   ✅ Fuel & Interconnectors formatting applied")
    
    # 4. Format Outages section header (Row 32)
    print("\n4️⃣ Formatting Outages section...")
    
    outages_requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 31,
                    "endRowIndex": 32,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.95, "green": 0.4, "blue": 0.4},
                        "textFormat": {"bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": outages_requests}
    ).execute()
    
    print("   ✅ Outages section formatting applied")
    
    # 5. Clean up GSP section (remove duplicates starting at row 72)
    print("\n5️⃣ Cleaning up GSP section...")
    
    # Clear rows 60-80 that might have duplicate content
    dashboard.batch_clear(['A60:L80'])
    
    # Re-add GSP Demand table properly at row 57 (column H)
    # DISABLED: GSP tables removed from Dashboard per user request
    # dashboard.update('H57', [['🔌 DEMAND (Importing GSPs)']], value_input_option='RAW')
    # dashboard.update('H58', [['GSP', 'Name', 'Import', 'Wind', 'Status']], value_input_option='RAW')
    print("   ℹ️  GSP tables disabled (available in Map_Data_GSP sheet)")
    
    print("   ✅ GSP section cleaned")
    
    # 6. Format GSP section headers
    print("\n6️⃣ Formatting GSP headers...")
    
    gsp_requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 54,
                    "endRowIndex": 55,
                    "startColumnIndex": 0,
                    "endColumnIndex": 12
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9},
                        "textFormat": {"bold": True, "fontSize": 11, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": "LEFT"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 56,
                    "endRowIndex": 57,
                    "startColumnIndex": 0,
                    "endColumnIndex": 5
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.4, "green": 0.8, "blue": 0.4},
                        "textFormat": {"bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        {
            "repeatCell": {
                "range": {
                    "sheetId": dashboard.id,
                    "startRowIndex": 56,
                    "endRowIndex": 57,
                    "startColumnIndex": 7,
                    "endColumnIndex": 12
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.9, "green": 0.4, "blue": 0.4},
                        "textFormat": {"bold": True, "fontSize": 10},
                        "horizontalAlignment": "CENTER"
                    }
                },
                "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        }
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": gsp_requests}
    ).execute()
    
    print("   ✅ GSP headers formatted")
    
    # 7. Set column widths for better readability
    print("\n7️⃣ Setting optimal column widths...")
    
    width_requests = [
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 1}, "properties": {"pixelSize": 220}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 1, "endIndex": 2}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 2, "endIndex": 3}, "properties": {"pixelSize": 120}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 3, "endIndex": 4}, "properties": {"pixelSize": 220}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 4, "endIndex": 5}, "properties": {"pixelSize": 150}, "fields": "pixelSize"}},
        {"updateDimensionProperties": {"range": {"sheetId": dashboard.id, "dimension": "COLUMNS", "startIndex": 5, "endIndex": 6}, "properties": {"pixelSize": 180}, "fields": "pixelSize"}},
    ]
    
    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"requests": width_requests}
    ).execute()
    
    print("   ✅ Column widths optimized")
    
    print("\n" + "=" * 80)
    print("✅ DASHBOARD DESIGN IMPROVED!")
    print("=" * 80)
    print("\n📊 IMPROVEMENTS APPLIED:")
    print("   ✅ Fixed header section (Rows 1-6)")
    print("   ✅ Applied color-coded formatting")
    print("   ✅ Blue headers for system metrics")
    print("   ✅ Green for Fuel, Blue for Interconnectors")
    print("   ✅ Red for Outages section")
    print("   ✅ Blue main header for GSP")
    print("   ✅ Green for Generation, Red for Demand")
    print("   ✅ Cleaned duplicate GSP content")
    print("   ✅ Optimized column widths")
    print(f"\n🔗 View improved Dashboard: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    print("=" * 80)

if __name__ == "__main__":
    improve_dashboard_layout()
