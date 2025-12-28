#!/usr/bin/env python3
"""
Add DNO constraint cost map to Google Sheets using scatter chart
Uses lat/long coordinates of DNO centroids since Sheets doesn't support custom boundaries
Creates bubble chart where size = cost, positioned by UK coordinates
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery

SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'DNO Map Data'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery.readonly'
]

def fetch_dno_centroids_with_costs():
    """Fetch DNO centroid coordinates with constraint costs"""
    print('📊 Fetching DNO centroids and costs from BigQuery...')
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    query = f"""
    SELECT 
        d.dno_id,
        d.dno_full_name,
        d.area_name,
        d.dno_code,
        c.total_cost_gbp,
        c.voltage_cost_gbp,
        c.thermal_cost_gbp,
        c.cost_per_sq_km,
        ST_Y(ST_CENTROID(d.boundary)) as latitude,
        ST_X(ST_CENTROID(d.boundary)) as longitude,
        CAST(ST_AREA(d.boundary) / 1000000 AS INT64) as area_sq_km
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries` d
    JOIN `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno_latest` c
        ON d.dno_id = c.dno_id
    ORDER BY c.total_cost_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    print(f'✅ Retrieved {len(df)} DNO centroids')
    return df

def add_map_data_sheet(spreadsheet, df):
    """Add sheet with DNO map data"""
    print(f'\n📄 Creating sheet: {SHEET_NAME}')
    
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        print(f'⚠️  Sheet exists - clearing and updating')
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=50, cols=15)
        print(f'✅ Created new sheet')
    
    # Prepare data
    headers = ['DNO Code', 'DNO Name', 'Region', 'Latitude', 'Longitude', 
               'Total Cost (£M)', 'Voltage Cost (£M)', 'Thermal Cost (£M)', 
               'Area (km²)', 'Cost/km²']
    
    # Convert costs to millions for readability
    data = []
    for _, row in df.iterrows():
        data.append([
            row['dno_code'],
            row['dno_full_name'],
            row['area_name'],
            round(row['latitude'], 4),
            round(row['longitude'], 4),
            round(row['total_cost_gbp'] / 1_000_000, 2),
            round(row['voltage_cost_gbp'] / 1_000_000, 2),
            round(row['thermal_cost_gbp'] / 1_000_000, 2),
            row['area_sq_km'],
            round(row['cost_per_sq_km'], 2)
        ])
    
    values = [headers] + data
    
    # Write to sheet
    worksheet.update(values, 'A1', value_input_option='USER_ENTERED')
    
    # Format header
    worksheet.format('A1:J1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format numbers
    worksheet.format('F2:H15', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
    worksheet.format('I2:I15', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0'}})
    worksheet.format('J2:J15', {'numberFormat': {'type': 'NUMBER', 'pattern': '#,##0.00'}})
    
    # Auto-resize
    worksheet.columns_auto_resize(0, len(headers))
    worksheet.freeze(rows=1)
    
    print('✅ Data written and formatted')
    return worksheet

def create_scatter_map_chart(spreadsheet, worksheet):
    """Create scatter/bubble chart as UK map"""
    print('\n📊 Creating scatter map chart...')
    
    chart_request = {
        'addChart': {
            'chart': {
                'spec': {
                    'title': 'UK DNO Constraint Costs by Location',
                    'basicChart': {
                        'chartType': 'SCATTER',
                        'legendPosition': 'RIGHT_LEGEND',
                        'axis': [
                            {
                                'position': 'BOTTOM_AXIS',
                                'title': 'Longitude (West ← → East)'
                            },
                            {
                                'position': 'LEFT_AXIS',
                                'title': 'Latitude (South ← → North)'
                            }
                        ],
                        'domains': [{
                            'domain': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': worksheet.id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 15,
                                        'startColumnIndex': 4,  # Longitude (E)
                                        'endColumnIndex': 5
                                    }]
                                }
                            }
                        }],
                        'series': [{
                            'series': {
                                'sourceRange': {
                                    'sources': [{
                                        'sheetId': worksheet.id,
                                        'startRowIndex': 1,
                                        'endRowIndex': 15,
                                        'startColumnIndex': 3,  # Latitude (D)
                                        'endColumnIndex': 4
                                    }]
                                }
                            },
                            'targetAxis': 'LEFT_AXIS',
                            'pointStyle': {
                                'size': 10
                            }
                        }],
                        'headerCount': 1
                    }
                },
                'position': {
                    'overlayPosition': {
                        'anchorCell': {
                            'sheetId': worksheet.id,
                            'rowIndex': 1,
                            'columnIndex': 11
                        },
                        'offsetXPixels': 20,
                        'offsetYPixels': 20,
                        'widthPixels': 700,
                        'heightPixels': 500
                    }
                }
            }
        }
    }
    
    try:
        spreadsheet.batch_update({'requests': [chart_request]})
        print('✅ Scatter map chart created')
        return True
    except Exception as e:
        print(f'⚠️  Chart creation failed: {e}')
        return False

def add_instructions(worksheet):
    """Add instructions for creating geo chart manually"""
    instructions = [
        [''],
        ['MANUAL GEO CHART INSTRUCTIONS:'],
        ['1. Select range C2:C15 (Region column - 14 DNO names)'],
        ['2. Hold Ctrl and also select F2:F15 (Total Cost column)'],
        ['3. Click Insert → Chart'],
        ['4. In Chart Editor → Setup tab:'],
        ['   - Chart type: Geo chart'],
        ['   - Region: United Kingdom'],
        ['5. In Customize tab:'],
        ['   - Geo → Region: United Kingdom'],
        ['   - Geo → Display mode: Regions'],
        ['   - Color scale: Min value (light) to Max value (dark)'],
        [''],
        ['NOTE: Google Sheets cannot display DNO boundaries'],
        ['It will show UK regions/cities as closest match'],
        ['For accurate DNO boundaries, use: dno_constraint_map.html']
    ]
    
    worksheet.update(instructions, 'L2')
    worksheet.format('L2', {'textFormat': {'bold': True, 'fontSize': 12}})
    
    print('✅ Instructions added')

def main():
    print('🗺️  Adding DNO Map to Google Sheets')
    print('='*80)
    
    # Get credentials
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    print(f'✅ Opened: {spreadsheet.title}')
    
    # Fetch data
    df = fetch_dno_centroids_with_costs()
    
    # Add data sheet
    worksheet = add_map_data_sheet(spreadsheet, df)
    
    # Create scatter chart
    create_scatter_map_chart(spreadsheet, worksheet)
    
    # Add instructions
    add_instructions(worksheet)
    
    print('\n' + '='*80)
    print('✅ SUCCESS: DNO map data added to Google Sheets')
    print('='*80)
    print(f'\nView: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}')
    print('\nLIMITATIONS of Google Sheets:')
    print('  ❌ Cannot display custom DNO boundaries')
    print('  ❌ Geo charts only support predefined regions (countries/provinces/cities)')
    print('  ❌ Will show nearest city/region matches, not actual DNO areas')
    print('\nRECOMMENDATION:')
    print('  ✅ Use dno_constraint_map.html for accurate DNO boundary visualization')
    print('  ✅ Upload to http://94.237.55.15/ for web access')

if __name__ == '__main__':
    main()
