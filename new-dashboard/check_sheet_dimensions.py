import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sh = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
sheet = sh.worksheet('Battery Revenue Analysis')

print(f'Sheet dimensions: {sheet.row_count} rows x {sheet.col_count} cols')
print(f'\nGetting data from rows 70-95...')
data = sheet.get('A70:H95')
for i, row in enumerate(data, 70):
    if row:
        print(f'Row {i}: {row[:5]}')  # First 5 columns
