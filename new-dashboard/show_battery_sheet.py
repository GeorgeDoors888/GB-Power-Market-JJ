#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(
    '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', 
    scope
)
client = gspread.authorize(creds)
sheet = client.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')

print('='*70)
print('DASHBOARD V2 - ALL SHEETS')
print('='*70)
for i, ws in enumerate(sheet.worksheets(), start=1):
    print(f'{i}. {ws.title} (ID: {ws.id})')

battery_sheet = sheet.worksheet('Battery Revenue Analysis')
print()
print('='*70)
print('BATTERY REVENUE ANALYSIS LOCATION')
print('='*70)
print(f'Spreadsheet: Dashboard V2')
print(f'Sheet Name: Battery Revenue Analysis')
print(f'Sheet ID: {battery_sheet.id}')
print(f'Direct Link: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit#gid={battery_sheet.id}')
print()
print('KPIs:', battery_sheet.row_values(2)[:4])
print('Headers:', battery_sheet.row_values(4)[:12])
print()
print('Sample data (Row 5):', battery_sheet.row_values(5)[:8])
