#!/usr/bin/env python3
from google.oauth2 import service_account
import gspread

SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SA_FILE = '/home/george/inner-cinema-credentials.json'

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
wb = gc.open_by_key(SPREADSHEET_ID)

print("📋 AVAILABLE SHEETS:")
print("=" * 80)
for idx, sheet in enumerate(wb.worksheets()):
    print(f"{idx}: '{sheet.title}' (ID: {sheet.id})")
    # Check first cell
    try:
        a1 = sheet.acell('A1').value
        a2 = sheet.acell('A2').value
        print(f"   A1: '{a1}'")
        print(f"   A2: '{a2}'")
    except:
        print("   (Unable to read)")
    print()

print("\n🎯 Looking for 'GB LIVE DASHBOARD' sheet...")
for sheet in wb.worksheets():
    a1 = sheet.acell('A1').value or ''
    if 'LIVE' in a1.upper() or 'DASHBOARD' in a1.upper():
        print(f"\n✅ FOUND: '{sheet.title}'")
        print(f"   A1: {a1}")
        print(f"   A2: {sheet.acell('A2').value}")
        print(f"   Reading first 10 rows...")
        for row in range(1, 11):
            cells = sheet.range(f'A{row}:F{row}')
            values = [c.value for c in cells if c.value]
            if values:
                print(f"   Row {row}: {' | '.join(str(v)[:30] for v in values)}")
