#!/usr/bin/env python3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
summary = sheet.worksheet('Summary')

all_data = summary.get_all_values()
latest = all_data[-1]

time_str = latest[0]
demand = latest[1]
generation = latest[2]
wind = latest[3]
price = latest[4]

now = datetime.now()
sp = (now.hour * 2) + (1 if now.minute < 30 else 2)

summary_text = f'Total Generation: {generation} GW | Demand: {demand} GW | Wind: {wind}% | 💰 Market Price: £{price}/MWh (SP{sp}, {now.strftime("%H:%M")})'

dashboard = sheet.worksheet('Dashboard')
dashboard.update_acell('A5', summary_text)

print(f'✅ Updated Dashboard row 5:')
print(f'   {summary_text}')
