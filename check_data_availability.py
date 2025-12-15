#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')

sheet = spreadsheet.worksheet('Data Availability')
data = sheet.get_all_values()[:30]

print('📊 Data Availability Sheet:')
print('=' * 100)
for idx, row in enumerate(data, 1):
    if any(row):
        print(f'Row {idx}: {" | ".join(str(x) for x in row[:6] if x)}')
