#!/usr/bin/env python3
"""
Read Live Dashboard v2 - Find Wind Forecast Section
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

print("🔍 READING LIVE DASHBOARD v2")
print("=" * 80)
print()

try:
    sh = client.open_by_key(SPREADSHEET_ID)
    ws = sh.worksheet("Live Dashboard v2")
    
    print(f"📊 Sheet: {ws.title}")
    print(f"   Size: {ws.row_count} rows × {ws.col_count} cols")
    print()
    
    # Read first 50 rows to find Wind Data section
    all_values = ws.get_all_values()
    
    print("🔍 Searching for 'Wind' section...")
    print("-" * 80)
    
    wind_section_start = None
    for i, row in enumerate(all_values[:100], 1):
        row_text = ' '.join(str(cell) for cell in row).lower()
        if 'wind' in row_text and ('forecast' in row_text or 'data' in row_text):
            print(f"✅ Found at Row {i}: {' | '.join(row[:8])}")
            wind_section_start = i
            break
    
    if wind_section_start:
        print()
        print("=" * 80)
        print(f"📊 WIND FORECAST SECTION (Starting at Row {wind_section_start})")
        print("=" * 80)
        print()
        
        # Display 30 rows from wind section
        for i in range(wind_section_start - 1, min(wind_section_start + 29, len(all_values))):
            row = all_values[i]
            # Show first 12 columns
            row_display = '\t'.join(str(cell)[:15] for cell in row[:12])
            print(f"Row {i+1:3d}: {row_display}")
        
        print()
        print("=" * 80)
        print("🔍 CHECKING FOR #ERROR! VALUES")
        print("=" * 80)
        print()
        
        errors_found = []
        for row_idx in range(wind_section_start - 1, min(wind_section_start + 49, len(all_values))):
            row = all_values[row_idx]
            for col_idx, cell in enumerate(row[:20], 1):  # Check first 20 columns
                cell_str = str(cell)
                if '#ERROR!' in cell_str or '#N/A' in cell_str or '#REF!' in cell_str or '#VALUE!' in cell_str:
                    col_letter = chr(64 + col_idx) if col_idx <= 26 else f"A{chr(64 + col_idx - 26)}"
                    errors_found.append({
                        'Cell': f"{col_letter}{row_idx + 1}",
                        'Row': row_idx + 1,
                        'Col': col_idx,
                        'Error': cell_str,
                        'Label': row[0] if row else '',
                        'Context': ' | '.join(str(c)[:15] for c in row[max(0, col_idx-2):min(len(row), col_idx+3)])
                    })
        
        if errors_found:
            print(f"🔴 Found {len(errors_found)} errors in Wind section:")
            print("-" * 80)
            for err in errors_found:
                print(f"\n  Cell {err['Cell']} (Row {err['Row']}, Col {err['Col']}):")
                print(f"    Label: {err['Label']}")
                print(f"    Error: {err['Error']}")
                print(f"    Context: {err['Context']}")
        else:
            print("✅ No errors found in Wind section")
        
        # Try to read specific cells based on your layout
        print()
        print("=" * 80)
        print("📊 KEY METRICS")
        print("=" * 80)
        print()
        
        # Assuming Wind section starts at the row we found
        # Try reading cells in a grid pattern
        for offset in range(30):
            row_num = wind_section_start + offset
            if row_num <= len(all_values):
                row = all_values[row_num - 1]
                if any(cell for cell in row[:8]):  # If row has data
                    print(f"Row {row_num}: {' | '.join(str(c)[:20] for c in row[:8])}")
    
    else:
        print("⚠️  'Wind' section not found in first 100 rows")
        print()
        print("Showing first 50 rows:")
        print("-" * 80)
        for i, row in enumerate(all_values[:50], 1):
            row_display = ' | '.join(str(cell)[:15] for cell in row[:8])
            if row_display.strip():
                print(f"Row {i:3d}: {row_display}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
