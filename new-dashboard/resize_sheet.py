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

print(f'Current sheet size: {battery.row_count} rows x {battery.col_count} cols')

all_data = battery.get_all_values()
data_rows = len([r for r in all_data if any(r)])
print(f'Data ends at row: {data_rows}')

# Resize to 150 rows to fit all data
print('\n🔧 Resizing sheet to 150 rows...')
battery.resize(rows=150)
print(f'✅ Resized to: {battery.row_count} rows x {battery.col_count} cols')
