#!/usr/bin/env python3
"""
Verify PS (Pumped Storage) sparkline now uses symmetric LET formula.
"""
import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
WORKSHEET_NAME = "Live Dashboard v2"
PS_CELL = "D22"  # PS sparkline location

def main():
    # Authenticate
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    
    print("=" * 80)
    print("🔍 CHECKING PS (PUMPED STORAGE) SPARKLINE FORMULA")
    print("=" * 80)
    
    # Get formula from D22
    formula = sheet.acell(PS_CELL, value_render_option='FORMULA').value
    
    print(f"\n📊 PS Sparkline Cell: {PS_CELL}")
    print(f"Formula Length: {len(formula)} characters\n")
    
    # Check for key elements of symmetric LET formula
    checks = {
        "Uses LET formula": "=LET(" in formula,
        "Has MAX(ABS(x)) for symmetric range": "MAX(ABS(x))" in formula or "MAX(ABS" in formula,
        "Has symmetric ymin (-m-pad)": "-m-pad" in formula,
        "Has symmetric ymax (m+pad)": "m+pad" in formula,
        "Has 8% padding": "*0.08" in formula,
        "Has purple color": "#8A2BE2" in formula,
        "Has red negcolor": "#DC143C" in formula,
        "Has axis enabled": '"axis",TRUE' in formula or '"axis",true' in formula,
        "Uses column chart": '"charttype","column"' in formula
    }
    
    print("✅ Verification Checks:")
    print("-" * 80)
    all_pass = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check}")
        if not result:
            all_pass = False
    
    print("\n" + "=" * 80)
    if all_pass:
        print("🎉 SUCCESS: PS sparkline using symmetric LET formula!")
    else:
        print("⚠️  INCOMPLETE: Some checks failed")
    
    print("\n📝 Full Formula Preview (first 200 chars):")
    print(formula[:200] + "..." if len(formula) > 200 else formula)
    
    # Extract data preview
    if "=LET(r,{" in formula:
        data_start = formula.find("{") + 1
        data_end = formula.find("}", data_start)
        data_str = formula[data_start:data_end]
        values = data_str.split(",")[:5]
        print(f"\n📊 First 5 Data Points: {', '.join(values)}")

if __name__ == "__main__":
    main()
