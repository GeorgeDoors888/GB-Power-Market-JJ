#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_PATH = '/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json'
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
client = gspread.authorize(creds)

sheet = client.open_by_key(SPREADSHEET_ID)
battery_sheet = sheet.worksheet('Battery Revenue Analysis')

all_data = battery_sheet.get_all_values()

print(f'Total rows: {len(all_data)}')
print(f'Rows with data: {len([r for r in all_data if any(r)])}')

print('\n🔍 Scanning all rows for section headers...')
for i, row in enumerate(all_data[:100], 1):
    if row and row[0]:
        text = str(row[0]).strip()
        if any(keyword in text.upper() for keyword in ['HISTORICAL', 'UNIT PERFORMANCE', 'DAILY', 'SUMMARY', '7 WEEK', '49 DAY']):
            print(f'\n📍 Row {i}: "{text}"')
            # Show next 3 rows
            for j in range(i, min(i+3, len(all_data))):
                if all_data[j]:
                    print(f'   Row {j+1}: {all_data[j][:6]}')
