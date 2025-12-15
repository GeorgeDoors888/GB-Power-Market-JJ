#!/usr/bin/env python3
"""
Check which Apps Script projects are bound to GB Live spreadsheet
"""

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

try:
    spreadsheet = gc.open_by_key(SHEET_ID)
    
    print("=" * 70)
    print("📊 GB LIVE SPREADSHEET INFO")
    print("=" * 70)
    print(f"Title: {spreadsheet.title}")
    print(f"ID: {spreadsheet.id}")
    print(f"URL: {spreadsheet.url}")
    
    print("\n📑 SHEETS:")
    for sheet in spreadsheet.worksheets():
        print(f"   - {sheet.title} (ID: {sheet.id})")
    
    print("\n⚠️  NOTE: To check Apps Script projects:")
    print("   1. Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/")
    print("   2. Extensions → Apps Script")
    print("   3. If you see 'DNO Map' code, delete it")
    print("   4. Deploy new code: cd bg-sparklines-clasp && ./deploy.sh")
    print("\n✅ The correct menu name is: '⚡ GB Live Dashboard'")
    
except Exception as e:
    print(f"❌ Error: {e}")
