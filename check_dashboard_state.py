#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet.worksheet('Dashboard')

print('📋 DASHBOARD CURRENT STATE:')
print('=' * 80)

print('\n🔹 Row 5 (A5):')
a5 = dashboard.acell('A5').value
print(f'  {a5}')

print('\n🔹 Row 6 (A6:G6):')
row6 = dashboard.range('A6:G6')
for cell in row6:
    if cell.value:
        print(f'  {cell.address}: {cell.value}')

print('\n🔹 Rows 56-60 (checking for GSP data):')
for i in range(56, 61):
    cell_value = dashboard.acell(f'A{i}').value
    if cell_value:
        print(f'  A{i}: {cell_value}')
