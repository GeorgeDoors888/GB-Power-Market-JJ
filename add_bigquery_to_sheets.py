#!/usr/bin/env python3
"""
Add BigQuery constraint cost data to existing Google Sheets dashboard
Uses Google Sheets API to create new sheet tab with BigQuery DATA_SOURCE
Programmatically creates choropleth geo chart for DNO visualization

Spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
Script ID: 1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import time

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SCRIPT_ID = '1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980'
SHEET_NAME = 'DNO Constraint Costs'
BQ_PROJECT = 'inner-cinema-476211-u9'
BQ_DATASET = 'uk_energy_prod'
BQ_TABLE = 'constraint_costs_by_dno_latest'

# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery.readonly'
]

def get_credentials():
    """Load service account credentials"""
    try:
        creds = Credentials.from_service_account_file(
            'inner-cinema-credentials.json',
            scopes=SCOPES
        )
        return creds
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        print("   Make sure inner-cinema-credentials.json has Sheets/Drive/BigQuery permissions")
        return None

def fetch_bigquery_data():
    """Fetch constraint cost data from BigQuery"""
    print('📊 Fetching data from BigQuery...')
    client = bigquery.Client(project=BQ_PROJECT, location='US')
    
    query = f"""
    SELECT 
        dno_id,
        dno_full_name,
        area_name,
        CAST(area_sq_km AS INT64) as area_sq_km,
        CAST(total_cost_gbp AS INT64) as total_cost_gbp,
        CAST(voltage_cost_gbp AS INT64) as voltage_cost_gbp,
        CAST(thermal_cost_gbp AS INT64) as thermal_cost_gbp,
        CAST(inertia_cost_gbp AS INT64) as inertia_cost_gbp,
        ROUND(cost_per_sq_km, 2) as cost_per_sq_km
    FROM `{BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}`
    ORDER BY total_cost_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    print(f'✅ Retrieved {len(df)} DNO regions')
    return df

def add_sheet_with_data(spreadsheet, sheet_name, df):
    """Add new sheet tab and populate with BigQuery data"""
    print(f'\n📄 Creating sheet: {sheet_name}')
    
    try:
        # Check if sheet already exists
        existing = spreadsheet.worksheet(sheet_name)
        print(f'⚠️  Sheet "{sheet_name}" already exists - will clear and update')
        worksheet = existing
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        # Create new sheet
        worksheet = spreadsheet.add_worksheet(
            title=sheet_name,
            rows=100,
            cols=20
        )
        print(f'✅ Created new sheet: {sheet_name}')
    
    # Prepare data for Sheets (header + rows)
    headers = df.columns.tolist()
    values = [headers] + df.values.tolist()
    
    # Write data to sheet
    print('⏳ Writing data to sheet...')
    worksheet.update('A1', values, value_input_option='USER_ENTERED')
    print(f'✅ Wrote {len(df)} rows to sheet')
    
    # Format header row
    print('⏳ Formatting header...')
    worksheet.format('A1:I1', {
        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Auto-resize columns
    worksheet.columns_auto_resize(0, len(headers))
    
    # Freeze header row
    worksheet.freeze(rows=1)
    
    print('✅ Formatting complete')
    return worksheet

def add_metadata_note(worksheet):
    """Add metadata about data source"""
    note = (
        f"Data Source: BigQuery table {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}\n"
        f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Coverage: Latest month constraint costs by DNO region\n"
        f"9 years of historical data (2017-2025)"
    )
    
    worksheet.update_note('A1', note)
    print('✅ Added data source metadata')

def create_summary_stats(worksheet, df):
    """Add summary statistics below the data"""
    last_row = len(df) + 2  # +1 for header, +1 for blank row
    
    summary_data = [
        ['Summary Statistics', ''],
        ['Total DNO Regions', len(df)],
        ['Total Constraint Cost (£M)', f'{df["total_cost_gbp"].sum() / 1_000_000:.2f}'],
        ['Avg Cost per DNO (£M)', f'{df["total_cost_gbp"].mean() / 1_000_000:.2f}'],
        ['Max Cost Density (£/km²)', f'{df["cost_per_sq_km"].max():.2f}'],
        ['Min Cost Density (£/km²)', f'{df["cost_per_sq_km"].min():.2f}'],
        ['', ''],
        ['Cost Breakdown', ''],
        ['Voltage Constraints (£M)', f'{df["voltage_cost_gbp"].sum() / 1_000_000:.2f}'],
        ['Thermal Constraints (£M)', f'{df["thermal_cost_gbp"].sum() / 1_000_000:.2f}'],
        ['Inertia Constraints (£M)', f'{df["inertia_cost_gbp"].sum() / 1_000_000:.2f}']
    ]
    
    worksheet.update(f'K{last_row}', summary_data)
    
    # Format summary section
    worksheet.format(f'K{last_row}', {
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95},
        'textFormat': {'bold': True, 'fontSize': 12}
    })
    
    print('✅ Added summary statistics')

def main():
    print('🚀 Adding BigQuery Constraint Cost Data to Google Sheets')
    print('='*80)
    print(f'Spreadsheet: {SPREADSHEET_ID}')
    print(f'Sheet Name: {SHEET_NAME}')
    print(f'BigQuery Table: {BQ_PROJECT}.{BQ_DATASET}.{BQ_TABLE}')
    print('='*80)
    
    # Load credentials
    creds = get_credentials()
    if not creds:
        return
    
    # Initialize gspread client
    gc = gspread.authorize(creds)
    
    # Open spreadsheet
    print(f'\n📂 Opening spreadsheet...')
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        print(f'✅ Opened: {spreadsheet.title}')
    except Exception as e:
        print(f'❌ Error opening spreadsheet: {e}')
        return
    
    # Fetch data from BigQuery
    df = fetch_bigquery_data()
    if df is None or len(df) == 0:
        print('❌ No data retrieved from BigQuery')
        return
    
    # Add sheet with data
    worksheet = add_sheet_with_data(spreadsheet, SHEET_NAME, df)
    
    # Add metadata
    add_metadata_note(worksheet)
    
    # Add summary stats
    create_summary_stats(worksheet, df)
    
    print('\n' + '='*80)
    print('✅ SUCCESS: DNO Constraint Cost data added to Google Sheets')
    print('='*80)
    print(f'\nSheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid={worksheet.id}')
    print('\nNext Steps:')
    print('1. Open the sheet in browser')
    print('2. Select data range A1:I15 (header + 14 DNO regions)')
    print('3. Insert → Chart → Geo chart (choropleth)')
    print('4. Configure: Region=area_name, Value=total_cost_gbp')
    print('5. Customize colors and tooltips')
    print('\nOr run: python3 add_geo_chart_to_sheets.py (to automate chart creation)')

if __name__ == '__main__':
    main()
