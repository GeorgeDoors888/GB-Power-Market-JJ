#!/usr/bin/env python3
"""
trigger_dashboard_setup.py
---------------------------
Manually trigger the dashboard setup via direct API calls
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

print("=" * 70)
print("⚡ MANUAL DASHBOARD SETUP TRIGGER")
print("=" * 70)
print()

# Since Apps Script API requires OAuth, we'll do it directly via Sheets API
creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
dash = sh.worksheet('Dashboard')

print("✅ Connected to Dashboard")
print()
print("📋 INSTRUCTIONS TO COMPLETE SETUP:")
print()
print("1. Open the dashboard in your browser:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("2. Look for the menu: ⚡ Dashboard Controls")
print("   (If you don't see it, refresh the page and wait 5 seconds)")
print()
print("3. Click: ⚡ Dashboard Controls → 🎨 Apply Orange Theme")
print()
print("4. Wait for completion message (~3-5 seconds)")
print()
print("=" * 70)
print("✅ This will:")
print("   • Apply orange theme to all elements")
print("   • Position chart zones correctly")
print("   • Set up date pickers (H3, J3)")
print("   • Create Top 12 Outages section")
print("   • Add conditional formatting")
print("   • Remove all conflicting sections")
print("=" * 70)
print()

# Open browser
import subprocess
subprocess.run(['open', f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/'])
print("🌐 Opening dashboard in browser...")
