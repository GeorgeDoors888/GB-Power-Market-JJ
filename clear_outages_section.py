#!/usr/bin/env python3
"""
clear_outages_section.py
-------------------------
Temporary: Clear the outages section until proper data source is configured
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
DASHBOARD = 'Dashboard'

print("🧹 Clearing outages section...")

creds = Credentials.from_service_account_file('inner-cinema-credentials.json', 
                                              scopes=['https://www.googleapis.com/auth/spreadsheets'])
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
dash = sh.worksheet(DASHBOARD)

# Clear rows 93-105
dash.batch_clear(["A93:H105"])

# Add placeholder
dash.update([[f"⏳ Outages data source being configured... (Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M')})"]], "A93")

print("✅ Cleared outages section")
