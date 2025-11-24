from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread

SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# Connect
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
sheets_service = build('sheets', 'v4', credentials=creds)

# Get spreadsheet
sh = gc.open_by_key(SPREADSHEET_ID)
dashboard = sh.worksheet('Dashboard')

print("=" * 70)
print("📊 CURRENT DASHBOARD STATE")
print("=" * 70)

# Check H57:K75 for GSP data
print("\n🔍 Checking H57:K75 for GSP data...")
gsp_range = dashboard.get('H57:K75')
if gsp_range and any(any(cell for cell in row) for row in gsp_range):
    print("❌ GSP DATA STILL EXISTS:")
    for i, row in enumerate(gsp_range, 57):
        if any(cell for cell in row):
            print(f"  Row {i}: {row}")
else:
    print("✅ No GSP data found in H57:K75")

# Get spreadsheet metadata including charts
print("\n📊 Checking embedded charts...")
result = sheets_service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    includeGridData=False
).execute()

dashboard_sheet_id = None
for sheet in result['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        dashboard_sheet_id = sheet['properties']['sheetId']
        if 'charts' in sheet:
            print(f"\n✅ Found {len(sheet['charts'])} embedded charts:")
            for idx, chart in enumerate(sheet['charts'], 1):
                spec = chart.get('spec', {})
                title = spec.get('title', 'Untitled')
                pos = chart.get('position', {}).get('overlayPosition', {}).get('anchorCell', {})
                row = pos.get('rowIndex', 0) + 1
                col_idx = pos.get('columnIndex', 0)
                col = chr(65 + col_idx) if col_idx < 26 else f"{chr(65 + col_idx // 26 - 1)}{chr(65 + col_idx % 26)}"
                print(f"  Chart {idx}: '{title}'")
                print(f"    Position: {col}{row}")
                print(f"    Chart ID: {chart.get('chartId')}")
        else:
            print("❌ No charts found on Dashboard")
        break

# Check data extent
all_data = dashboard.get_all_values()
print(f"\n📏 Dashboard dimensions:")
print(f"  Total rows with data: {len(all_data)}")
print(f"  Total columns: {len(all_data[0]) if all_data else 0}")

# Show rows 1-20 structure
print(f"\n📋 Current layout (rows 1-20):")
for i in range(min(20, len(all_data))):
    row_preview = ' | '.join(str(cell)[:30] for cell in all_data[i][:8])
    print(f"  Row {i+1}: {row_preview}")

# Check where fuel/IC data ends
print(f"\n🔍 Looking for where data sections are...")
for i, row in enumerate(all_data, 1):
    row_text = ' '.join(str(cell) for cell in row).strip()
    if 'Outage' in row_text or 'Asset Name' in row_text:
        print(f"  📍 Outage section starts at row {i}")
        break
    if i == 50:
        break

print("\n" + "=" * 70)
