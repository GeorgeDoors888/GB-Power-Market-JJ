#!/usr/bin/env python3
"""
Check if service account has access to Dashboard V2
"""
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SERVICE_ACCOUNT = 'all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com'

print(f"🔍 Checking access for: {SERVICE_ACCOUNT}")
print(f"📊 Spreadsheet: {SPREADSHEET_ID}")
print()

try:
    # Authenticate
    creds = Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive']
    )
    client = gspread.authorize(creds)
    
    # Try to open spreadsheet
    print("🔑 Attempting to open spreadsheet...")
    sheet = client.open_by_key(SPREADSHEET_ID)
    
    print(f"✅ SUCCESS! Service account has access")
    print(f"   Title: {sheet.title}")
    print(f"   Sheets: {[s.title for s in sheet.worksheets()]}")
    
    # Try to read Dashboard sheet
    dashboard = sheet.worksheet('Dashboard')
    print(f"   Dashboard rows: {dashboard.row_count}")
    print(f"   Dashboard cols: {dashboard.col_count}")
    
except gspread.exceptions.SpreadsheetNotFound:
    print("❌ FAILED: Spreadsheet not found or no access")
    print()
    print("📋 TO FIX:")
    print("1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc")
    print("2. Click Share button (top right)")
    print(f"3. Add: {SERVICE_ACCOUNT}")
    print("4. Set role: Editor")
    print("5. Click Share")
    
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
