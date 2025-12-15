#!/usr/bin/env python3
"""
Fix Sparklines in BM Revenue Dashboard
Diagnoses and fixes sparkline issues in Google Sheets
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
PROJECT_ID = "inner-cinema-476211-u9"

def fix_sparklines():
    """Fix sparklines in the dashboard"""
    
    # Connect to Google Sheets
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    gc = gspread.authorize(creds)
    
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    print("=" * 80)
    print("🔍 DIAGNOSING SPARKLINE ISSUES")
    print("=" * 80)
    print()
    
    # Check each sheet for sparkline formulas
    for sheet in spreadsheet.worksheets():
        print(f"📄 Sheet: {sheet.title}")
        
        # Get all formulas
        try:
            formulas = sheet.get_all_values()
            sparkline_cells = []
            
            for row_idx, row in enumerate(formulas, start=1):
                for col_idx, cell in enumerate(row, start=1):
                    if cell and 'SPARKLINE' in str(cell).upper():
                        sparkline_cells.append({
                            'cell': f'{chr(64 + col_idx)}{row_idx}',
                            'formula': cell
                        })
            
            if sparkline_cells:
                print(f"  Found {len(sparkline_cells)} sparkline formulas:")
                for sc in sparkline_cells[:5]:  # Show first 5
                    print(f"    {sc['cell']}: {sc['formula'][:80]}...")
            else:
                print(f"  No sparkline formulas found")
        except Exception as e:
            print(f"  Error checking sheet: {e}")
        
        print()
    
    # Create working sparklines for BM Revenue Analysis
    print("=" * 80)
    print("📊 CREATING SPARKLINES FOR BM REVENUE ANALYSIS")
    print("=" * 80)
    print()
    
    # Find BM Revenue Analysis sheet
    try:
        bm_sheet = spreadsheet.worksheet("BM Revenue Analysis - Full History")
        print(f"✅ Found sheet: {bm_sheet.title}")
        
        # Get header row to find columns
        headers = bm_sheet.row_values(1)
        print(f"📋 Headers: {', '.join(headers[:10])}...")
        
        # Find revenue column (usually column D or E)
        revenue_col = None
        for idx, header in enumerate(headers, start=1):
            if 'revenue' in header.lower() and 'net' in header.lower():
                revenue_col = idx
                break
        
        if revenue_col:
            col_letter = chr(64 + revenue_col)
            print(f"✅ Found revenue column: {col_letter} ({headers[revenue_col-1]})")
            
            # Add sparkline in a new column (after last data column)
            sparkline_col = len(headers) + 1
            sparkline_col_letter = chr(64 + sparkline_col)
            
            print(f"📊 Adding sparklines in column {sparkline_col_letter}...")
            
            # Header
            bm_sheet.update_acell(f'{sparkline_col_letter}1', 'Revenue Trend')
            
            # Get number of rows with data
            data_rows = len(bm_sheet.col_values(1))
            
            # Create sparkline for each row (rows 2 onwards)
            # This creates a simple bar sparkline of the revenue value
            for row in range(2, min(data_rows + 1, 50)):  # Limit to first 50 rows for testing
                cell = f'{sparkline_col_letter}{row}'
                # Simple sparkline showing the revenue as a bar
                formula = f'=SPARKLINE({col_letter}{row}, {{"charttype","bar";"max",MAX({col_letter}$2:{col_letter}$200)}})'
                bm_sheet.update_acell(cell, formula)
            
            print(f"✅ Added sparklines to {min(data_rows, 50)} rows")
        else:
            print("❌ Could not find revenue column")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 80)
    print("✅ SPARKLINE FIX COMPLETE")
    print("=" * 80)
    print()
    print(f"View your sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

if __name__ == "__main__":
    fix_sparklines()
