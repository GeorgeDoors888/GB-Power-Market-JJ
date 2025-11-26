#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

creds_path = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'
sheet_id = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(sheet_id)
battery = sheet.worksheet('Battery Revenue Analysis')

print('Checking NEW row layout...\n')
print('Row 25 (Historical header):', battery.row_values(25))
print('Row 26 (Historical columns):', battery.row_values(26))
print('Row 27 (First historical day):', battery.row_values(27)[:5])
print('Row 28 (Second historical day):', battery.row_values(28)[:5])
print()
print('Row 80 (Unit Perf header):', battery.row_values(80))
print('Row 81 (Unit Perf columns):', battery.row_values(81))
print('Row 82 (First unit):', battery.row_values(82)[:6])
print('Row 83 (Second unit):', battery.row_values(83)[:6])
print('\nTotal rows:', len([r for r in battery.get_all_values() if any(r)]))
