#!/usr/bin/env python3
"""
Create test spreadsheet for Upower Dashboard package testing
"""

import gspread
from google.oauth2 import service_account

# Connect
creds = service_account.Credentials.from_service_account_file(
    '../inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
)
gc = gspread.authorize(creds)

# Create new test spreadsheet
print("Creating test spreadsheet...")
sheet = gc.create('Upower Dashboard Test V3')
print(f'✅ Created test spreadsheet')
print(f'ID: {sheet.id}')
print(f'URL: {sheet.url}')

# Share with user
sheet.share('george@upowerenergy.uk', perm_type='user', role='writer')
print(f'✅ Shared with george@upowerenergy.uk')

# Copy basic structure from Dashboard V2
print("\nCopying Dashboard V2 structure...")
source_sheet = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')

# Get Dashboard worksheet from source
source_dashboard = source_sheet.worksheet('Dashboard')

# Rename Sheet1 to Dashboard in new sheet
test_dashboard = sheet.get_worksheet(0)
test_dashboard.update_title('Dashboard')

# Copy first 150 rows (header, KPIs, generation, prices, constraints)
print("Copying Dashboard data...")
data = source_dashboard.get('A1:K150')
test_dashboard.update('A1', data)

print(f'✅ Copied {len(data)} rows to Dashboard')

# Create chart sheets
for chart_name in ['Chart_Prices', 'Chart_Demand_Gen', 'Chart_IC_Import', 'Chart_Frequency']:
    try:
        sheet.add_worksheet(title=chart_name, rows=100, cols=10)
        print(f'✅ Created {chart_name}')
    except:
        print(f'⚠️  {chart_name} already exists')

# Create Daily_Chart_Data sheet
print("Creating Daily_Chart_Data...")
sheet.add_worksheet(title='Daily_Chart_Data', rows=50, cols=10)
daily_chart = sheet.worksheet('Daily_Chart_Data')

# Add headers
headers = [['Settlement Period', 'Date', 'Price (£/MWh)', 'Demand (MW)', 'Generation (MW)', 'IC Import (MW)', 'Frequency (Hz)']]
daily_chart.update('A1', headers)
print('✅ Created Daily_Chart_Data with headers')

print("\n" + "="*80)
print("TEST SPREADSHEET READY!")
print("="*80)
print(f"\n📊 Spreadsheet ID: {sheet.id}")
print(f"🔗 URL: {sheet.url}")
print("\n📝 Next steps:")
print("1. Open URL above")
print("2. Go to Extensions → Apps Script")
print("3. Paste contents of apps_script_code.gs from package")
print("4. Update SPREADSHEET_ID on line 11")
print("5. Save and refresh - menus should appear!")
