#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet_obj = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet_obj.worksheet('Dashboard')

print('✅ VERIFICATION - Dashboard rows 55-65:')
for i in range(55, 66):
    row = dashboard.row_values(i)
    if any(row):
        row_display = row[:11] if len(row) >= 11 else row
        print(f'Row {i}: {row_display}')
    else:
        print(f'Row {i}: [empty]')
