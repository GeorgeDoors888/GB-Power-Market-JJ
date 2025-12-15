#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet.worksheet('Dashboard')

print('📋 DASHBOARD ROWS 1-10 FULL VIEW:')
print('=' * 100)

for i in range(1, 11):
    row_data = dashboard.row_values(i)
    if any(row_data):
        print(f'\nRow {i}:')
        for col_idx, value in enumerate(row_data[:8], start=1):
            if value:
                col_letter = chr(64 + col_idx)
                print(f'  {col_letter}{i}: {value}')
