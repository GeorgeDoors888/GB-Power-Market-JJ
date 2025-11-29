import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
gc = gspread.authorize(creds)
ss = gc.open_by_key('1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc')

print("🔍 DASHBOARD VERIFICATION")
print("=" * 60)

# 1. Check Dashboard sheet
try:
    dash = ss.worksheet('Dashboard')
    print(f"✅ Dashboard sheet: EXISTS (position {dash.index})")
except:
    print("❌ Dashboard sheet: NOT FOUND")
    dash = None

# 2. Check data sheets
data_sheets = ['Chart_Prices', 'Chart_Demand_Gen', 'Chart_IC_Import', 
               'Chart_BM_Costs', 'Chart_Wind_Perf', 'Chart_Frequency', 'Chart_Outages']
print("\n📊 Chart Data Sheets:")
for sheet_name in data_sheets:
    try:
        sheet = ss.worksheet(sheet_name)
        row_count = len(sheet.get_all_values())
        print(f"  ✅ {sheet_name}: {row_count} rows")
    except:
        print(f"  ❌ {sheet_name}: NOT FOUND")

# 3. Check Dashboard content
if dash:
    print("\n📋 Dashboard Content:")
    header = dash.acell('A1').value
    timestamp = dash.acell('A2').value
    print(f"  Header (A1): {header or 'EMPTY'}")
    print(f"  Timestamp (A2): {timestamp or 'EMPTY'}")
    
    kpi = dash.range('A5:D5')
    print(f"  KPI Strip: {'HAS DATA' if any(c.value for c in kpi) else 'EMPTY'}")
