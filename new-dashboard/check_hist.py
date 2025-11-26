import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'\]
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/georgemajor/GB Power Market JJ/inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

sh = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')
sheet = sh.worksheet('Battery Revenue Analysis')

print('Checking historical data:')
historical = sheet.get('A27:A100')
dates = [row[0] for row in historical if row and row[0]]
print(f'Total dates: {len(dates)}')
if dates:
    print(f'First: {dates[0]}')
    print(f'Last: {dates[-1]}')
