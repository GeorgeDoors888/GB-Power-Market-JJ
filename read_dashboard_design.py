from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread
import json

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# Connect
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)
sheets_service = build('sheets', 'v4', credentials=creds)

print("="*80)
print("📊 READING DASHBOARD CURRENT DESIGN")
print("="*80)

# Get spreadsheet with full formatting
result = sheets_service.spreadsheets().get(
    spreadsheetId=SPREADSHEET_ID,
    includeGridData=True,
    ranges=['Dashboard!A1:K80']
).execute()

dashboard_sheet = None
for sheet in result['sheets']:
    if sheet['properties']['title'] == 'Dashboard':
        dashboard_sheet = sheet
        break

if not dashboard_sheet:
    print("❌ Dashboard sheet not found")
    exit(1)

print("\n📋 DASHBOARD LAYOUT & FORMATTING\n")

grid_data = dashboard_sheet['data'][0]
row_data = grid_data.get('rowData', [])

# Store design information
design = {
    'title': '',
    'rows': [],
    'colors': {},
    'fonts': {},
    'charts': []
}

# Read each row with formatting
for row_idx, row in enumerate(row_data[:80], 1):
    values = row.get('values', [])
    if not values:
        continue
    
    row_info = {
        'row_number': row_idx,
        'cells': []
    }
    
    has_content = False
    for col_idx, cell in enumerate(values[:11], 0):  # A-K columns
        col_letter = chr(65 + col_idx)
        
        user_value = cell.get('formattedValue', '')
        if user_value:
            has_content = True
        
        cell_format = cell.get('effectiveFormat', {})
        bg_color = cell_format.get('backgroundColor', {})
        text_format = cell_format.get('textFormat', {})
        fg_color = text_format.get('foregroundColor', {})
        
        cell_info = {
            'column': col_letter,
            'value': user_value,
            'background': {
                'red': bg_color.get('red', 1),
                'green': bg_color.get('green', 1),
                'blue': bg_color.get('blue', 1)
            },
            'text_color': {
                'red': fg_color.get('red', 0),
                'green': fg_color.get('green', 0),
                'blue': fg_color.get('blue', 0)
            },
            'font_size': text_format.get('fontSize', 10),
            'bold': text_format.get('bold', False),
            'italic': text_format.get('italic', False),
            'font_family': text_format.get('fontFamily', 'Arial'),
            'horizontal_align': cell_format.get('horizontalAlignment', 'LEFT'),
            'vertical_align': cell_format.get('verticalAlignment', 'BOTTOM')
        }
        
        row_info['cells'].append(cell_info)
    
    if has_content:
        design['rows'].append(row_info)

# Get chart information
if 'charts' in dashboard_sheet:
    for chart in dashboard_sheet['charts']:
        chart_spec = chart.get('spec', {})
        position = chart.get('position', {}).get('overlayPosition', {}).get('anchorCell', {})
        
        chart_info = {
            'title': chart_spec.get('title', ''),
            'subtitle': chart_spec.get('subtitle', ''),
            'chart_id': chart.get('chartId'),
            'position': {
                'row': position.get('rowIndex', 0) + 1,
                'column': chr(65 + position.get('columnIndex', 0))
            },
            'type': 'UNKNOWN'
        }
        
        # Determine chart type
        if 'basicChart' in chart_spec:
            basic_chart = chart_spec['basicChart']
            chart_info['type'] = basic_chart.get('chartType', 'UNKNOWN')
            chart_info['legend_position'] = basic_chart.get('legendPosition', 'NONE')
        elif 'pieChart' in chart_spec:
            chart_info['type'] = 'PIE'
        
        design['charts'].append(chart_info)

# Print summary
print(f"�� Total rows with data: {len(design['rows'])}")
print(f"📊 Total charts: {len(design['charts'])}")

# Print detailed layout
print("\n" + "="*80)
print("DETAILED LAYOUT")
print("="*80)

for row_info in design['rows'][:30]:  # First 30 rows
    row_num = row_info['row_number']
    cells_with_data = [c for c in row_info['cells'] if c['value']]
    
    if not cells_with_data:
        continue
    
    print(f"\n📍 Row {row_num}:")
    for cell in cells_with_data:
        bg = cell['background']
        text_col = cell['text_color']
        
        # Convert to hex
        bg_hex = f"#{int(bg['red']*255):02x}{int(bg['green']*255):02x}{int(bg['blue']*255):02x}"
        text_hex = f"#{int(text_col['red']*255):02x}{int(text_col['green']*255):02x}{int(text_col['blue']*255):02x}"
        
        formatting = []
        if cell['bold']:
            formatting.append('BOLD')
        if cell['italic']:
            formatting.append('ITALIC')
        if cell['font_size'] != 10:
            formatting.append(f"{cell['font_size']}pt")
        
        format_str = f" [{', '.join(formatting)}]" if formatting else ""
        
        value_preview = cell['value'][:50]
        print(f"  {cell['column']}: \"{value_preview}\"")
        print(f"      BG: {bg_hex}, Text: {text_hex}, Align: {cell['horizontal_align']}{format_str}")

# Print charts
if design['charts']:
    print("\n" + "="*80)
    print("CHARTS")
    print("="*80)
    for idx, chart in enumerate(design['charts'], 1):
        print(f"\n📊 Chart {idx}: {chart['title']}")
        print(f"   Type: {chart['type']}")
        print(f"   Position: {chart['position']['column']}{chart['position']['row']}")
        if chart.get('subtitle'):
            print(f"   Subtitle: {chart['subtitle']}")

# Save to JSON
with open('dashboard_current_design.json', 'w') as f:
    json.dump(design, f, indent=2)

print("\n" + "="*80)
print("✅ Design exported to dashboard_current_design.json")
print("="*80)
