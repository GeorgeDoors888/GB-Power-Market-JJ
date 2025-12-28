import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
ss = gc.open_by_key(SPREADSHEET_ID)
dash = ss.worksheet('Dashboard')

print("🔧 FINAL DASHBOARD SETUP")
print("=" * 60)

# Set default date values
from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
to_date = datetime.now().strftime('%Y-%m-%d')

print("\n1️⃣ Setting filter defaults...")
dash.update('B3', [['24h']])
dash.update('D3', [['All GB']])
dash.update('F3', [['All']])
dash.update('I3', [[from_date]])
dash.update('K3', [[to_date]])
print(f"   ✅ Filters set: 24h, All GB, All, {from_date} to {to_date}")

print("\n✅ Dashboard ready!")
print("\n📋 Next Steps:")
print("  1. Go to Apps Script editor")
print("  2. Paste PASTE_INTO_APPS_SCRIPT.js code")
print("  3. Run buildAllCharts()")
print("  4. Create button → Assign RefreshDashboard")
