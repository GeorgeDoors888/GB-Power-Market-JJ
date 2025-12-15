#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet_obj = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
dashboard = sheet_obj.worksheet('Dashboard')

print('🔍 Checking Dashboard for GSP data...')

# Check H57:K75 range (where GSP data typically appears)
gsp_data = dashboard.get('H57:K80')
if gsp_data:
    print(f'\n📍 Found data in H57:K80:')
    for idx, row in enumerate(gsp_data, start=57):
        if any(row):
            print(f'Row {idx}: {row}')
else:
    print('No data found in H57:K80')

# Now clear it completely
print('\n🧹 Clearing H56:K80 (GSP data area)...')
dashboard.batch_clear(['H56:K80'])
print('✅ Cleared GSP data from Dashboard')
