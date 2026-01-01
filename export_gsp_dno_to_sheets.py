#!/usr/bin/env python3
"""
Export GSP/DNO Analysis to Google Sheets
Creates a comprehensive dashboard showing regional capacity, DNO operators, and report capabilities
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def export_gsp_dno_dashboard():
    """Export GSP/DNO analysis to Google Sheets dashboard"""
    print("\n🚀 Exporting GSP/DNO Analysis to Google Sheets...")
    
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    sheets_client = get_sheets_client()
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    
    # Create or get sheet
    try:
        sheet = spreadsheet.worksheet('GSP-DNO Analysis')
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet('GSP-DNO Analysis', rows=200, cols=20)
    
    # Section 1: Header
    sheet.update('A1', [['GB POWER MARKET - GSP/DNO REGIONAL ANALYSIS']])
    sheet.merge_cells('A1:T1')
    sheet.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 16},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
        'horizontalAlignment': 'CENTER'
    })
    
    sheet.update('A2', [[f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    sheet.merge_cells('A2:T2')
    
    # Section 2: Key Findings
    print("  📊 Exporting key findings...")
    findings_data = [
        ['KEY FINDINGS', '', ''],
        ['Metric', 'Count', 'Details'],
        ['GSP Groups (DNO Licence Areas)', '14', 'Mapped to Elexon codes (_A through _P)'],
        ['Individual GSPs', '333', 'With geographic boundaries from NESO'],
        ['Active BM Units', '1,403', '698 with GSP assignments (49.8% coverage)'],
        ['DNO Operators', '14', 'With MPAN distributor IDs'],
        ['Report Types Available', '12', 'Heatmaps, charts, geographic visualizations'],
        ['', '', ''],
        ['TOP 3 REGIONS BY CAPACITY', '', ''],
        ['Eastern (_A)', '2,213 MW', 'UK Power Networks - Eastern'],
        ['North Scotland (_P)', '1,934 MW', 'Scottish Hydro Electric Power Distribution'],
        ['Southern (_H)', '1,906 MW', 'Southern Electric Power Distribution']
    ]
    
    sheet.update('A4', findings_data)
    sheet.format('A4:C4', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    sheet.format('A5:C5', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
    sheet.format('A12:C12', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    
    # Section 3: GSP Groups Detail
    print("  📍 Exporting GSP Groups...")
    query = f"""
    SELECT 
        gsp_group_id,
        gsp_group_name,
        dno_short_code,
        dno_name,
        primary_coverage_area
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_groups`
    ORDER BY gsp_group_id
    """
    df_groups = bq_client.query(query).to_dataframe()
    
    gsp_data = [['', '', '', '', ''], ['GSP GROUPS (DNO LICENCE AREAS)', '', '', '', ''], 
                ['Elexon Code', 'GSP Group Name', 'DNO Code', 'DNO Operator', 'Coverage Area']]
    for _, row in df_groups.iterrows():
        gsp_data.append([
            row['gsp_group_id'], row['gsp_group_name'], row['dno_short_code'],
            row['dno_name'], row['primary_coverage_area']
        ])
    
    sheet.update('A18', gsp_data)
    sheet.format('A19:E19', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    sheet.format('A20:E20', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}})
    
    # Section 4: BM Units by GSP Region
    print("  🔋 Exporting BMU capacity by region...")
    query = f"""
    SELECT 
        gsp_group,
        COUNT(DISTINCT bmu_id) as bmu_count,
        COUNT(DISTINCT lead_party_name) as party_count,
        ROUND(SUM(max_capacity_mw), 0) as total_capacity_mw,
        STRING_AGG(DISTINCT fuel_type_category, ', ' ORDER BY fuel_type_category) as fuel_types
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = TRUE AND gsp_group IS NOT NULL
    GROUP BY gsp_group
    ORDER BY total_capacity_mw DESC
    """
    df_bmu = bq_client.query(query).to_dataframe()
    
    bmu_data = [['', '', '', '', ''], ['BM UNITS BY GSP REGION', '', '', '', ''],
                ['GSP Group', 'BMU Count', 'Party Count', 'Total Capacity (MW)', 'Fuel Types']]
    for _, row in df_bmu.iterrows():
        bmu_data.append([
            row['gsp_group'], int(row['bmu_count']), int(row['party_count']),
            int(row['total_capacity_mw']), row['fuel_types']
        ])
    
    start_row = len(gsp_data) + 21
    sheet.update(f'A{start_row}', bmu_data)
    sheet.format(f'A{start_row+1}:E{start_row+1}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    sheet.format(f'A{start_row+2}:E{start_row+2}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}})
    
    # Section 5: Available Report Types
    print("  📈 Exporting report capabilities...")
    reports = [
        ('GSP Regional Generation Capacity', 'Stacked bar chart by fuel type per GSP Group'),
        ('DNO Network Load vs Generation', 'Bubble chart: capacity vs demand by DNO'),
        ('VLP Revenue by GSP Region', 'Heatmap showing £/MWh earnings per region'),
        ('Battery Storage Deployment Map', 'Geographic map colored by storage capacity'),
        ('Wind Farm Locations', 'Scatter plot with lat/long from NESO boundaries'),
        ('DNO Constraint Cost Analysis', 'Time series line chart by licence area'),
        ('GSP Group Settlement Volumes', 'Daily/monthly settlement data trends'),
        ('Technology Mix by Region', 'Pie charts per GSP Group'),
        ('Connection Queue by DNO', 'Bar chart of pending projects'),
        ('Voltage Level Distribution', 'Histogram of HV/LV/EHV connections per DNO'),
        ('Capacity Factor Analysis', 'Box plot by fuel type and region'),
        ('Geographic Coverage Heatmap', 'Area_sqkm vs generation density')
    ]
    
    report_data = [['', ''], ['AVAILABLE REPORT TYPES (12)', ''],
                   ['Report Name', 'Description']]
    for name, desc in reports:
        report_data.append([name, desc])
    
    start_row = start_row + len(bmu_data) + 3
    sheet.update(f'G{start_row}', report_data)
    sheet.format(f'G{start_row+1}:H{start_row+1}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    sheet.format(f'G{start_row+2}:H{start_row+2}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}})
    
    # Section 6: Elexon Code Mapping
    print("  🗺️ Exporting Elexon code mapping...")
    elexon_mapping = [
        ('_A', 'Eastern', 'UKPN-EPN'),
        ('_B', 'East Midlands', 'NGED-EMID'),
        ('_C', 'London', 'UKPN-LPN'),
        ('_D', 'Merseyside & North Wales', 'SP Energy Networks (SPM)'),
        ('_E', 'West Midlands', 'NGED-WMID'),
        ('_F', 'North East', 'Northern Powergrid (NE)'),
        ('_G', 'North West', 'Electricity North West (ENWL)'),
        ('_H', 'Southern', 'Scottish & Southern - SEPD'),
        ('_J', 'South Eastern', 'UKPN-SPN'),
        ('_K', 'South Wales', 'NGED-SWALES'),
        ('_L', 'South Western', 'NGED-SWEST'),
        ('_M', 'Yorkshire', 'Northern Powergrid (Y)'),
        ('_N', 'South Scotland', 'SP Energy Networks (SPD)'),
        ('_P', 'North Scotland', 'Scottish & Southern - SHEPD')
    ]
    
    elexon_data = [['', '', ''], ['ELEXON GSP GROUP CODES', '', ''],
                   ['Code', 'Region', 'DNO Operator']]
    for code, region, dno in elexon_mapping:
        elexon_data.append([code, region, dno])
    
    sheet.update(f'A{start_row}', elexon_data)
    sheet.format(f'A{start_row+1}:C{start_row+1}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
    sheet.format(f'A{start_row+2}:C{start_row+2}', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.85}})
    
    # Auto-resize columns
    sheet.format('A:T', {'wrapStrategy': 'WRAP'})
    
    print(f"\n✅ GSP/DNO Analysis exported to 'GSP-DNO Analysis' sheet!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")

def get_sheets_client():
    """Initialize Google Sheets client"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    return gspread.authorize(creds)

def main():
    try:
        export_gsp_dno_dashboard()
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
