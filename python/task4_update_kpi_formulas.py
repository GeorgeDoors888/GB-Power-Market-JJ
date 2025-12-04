#!/usr/bin/env python3
"""
Task 4: Update Dashboard V3 KPI Formulas to use bod_boalf_7d_summary

Updates cells F10, I10, J10, K10, L10 with formulas that query
the bod_boalf_7d_summary view via BOD_SUMMARY imported data tab.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
WORKSHEET_NAME = "Dashboard V3"

def main():
    print("🔧 Task 4: Update Dashboard V3 KPI Formulas")
    print("="*80)
    
    # Connect
    print("\n📝 Connecting to Google Sheets...")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scopes)
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(WORKSHEET_NAME)
    
    # New formulas (assuming BOD_SUMMARY tab with imported data)
    # Column mapping: A=breakdown, B=dno, E=net_balancing_volume_mwh, F=total_revenue_gbp, K=net_margin_gbp_per_mwh
    new_formulas = {
        'F10': '=IFERROR(QUERY(BOD_SUMMARY!A:Q, "SELECT F WHERE A=\'GB_total\' LIMIT 1")/1000, "N/A")',
        'I10': '=IFERROR(QUERY(BOD_SUMMARY!A:Q, "SELECT K WHERE A=\'GB_total\' LIMIT 1"), "N/A")',
        'J10': '=IFERROR(QUERY(BOD_SUMMARY!A:Q, "SELECT K WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1"), "N/A")',
        'K10': '=IFERROR(QUERY(BOD_SUMMARY!A:Q, "SELECT E WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1"), "N/A")',
        'L10': '=IFERROR(QUERY(BOD_SUMMARY!A:Q, "SELECT F WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1")/1000, "N/A")'
    }
    
    print("\n📊 Updating formulas:")
    for cell, formula in new_formulas.items():
        sheet.update(cell, [[formula]], value_input_option='USER_ENTERED')
        print(f"   ✅ {cell}: {formula[:60]}...")
    
    print("\n✅ All formulas updated!")
    print("\n⚠️  NOTE: Formulas require 'BOD_SUMMARY' tab with imported data")
    print("   Run: python/import_bod_summary_to_sheets.py")

if __name__ == "__main__":
    main()
