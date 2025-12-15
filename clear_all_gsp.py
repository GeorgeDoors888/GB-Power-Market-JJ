#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet_obj = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet_obj.worksheet('Dashboard')

# Clear rows 55 and 58 (GSP remnants)
dashboard.batch_clear(['A55:K80'])
print('✅ Cleared all GSP data from rows 55-80')

# Verify
print('\n📋 Verification - rows 30-60:')
for i in range(30, 61):
    row = dashboard.row_values(i)
    if any(row):
        print(f'Row {i}: {row[:8]}')
