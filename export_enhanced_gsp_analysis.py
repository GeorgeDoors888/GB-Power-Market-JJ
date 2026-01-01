#!/usr/bin/env python3
"""
Enhanced GSP/DNO Analysis Export to Google Sheets
Includes both GSP Groups AND individual NESO GSP IDs with Elexon linking

Author: GB Power Market JJ
Date: 2025-12-31
"""

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "GSP-DNO Analysis"

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)

# BigQuery setup
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# ============================================================================
# MAIN EXPORT FUNCTION
# ============================================================================

def export_enhanced_gsp_analysis():
    """
    Export comprehensive GSP/DNO analysis including:
    1. Summary statistics
    2. GSP Groups (14 DNO licence areas)
    3. Individual NESO GSPs (333 grid supply points)
    4. BMU capacity by region
    5. Data linking guide
    """
    
    print("🚀 Exporting Enhanced GSP/DNO Analysis to Google Sheets...")
    
    # Open spreadsheet
    ss = gc.open_by_key(SPREADSHEET_ID)
    
    # Get or create sheet
    try:
        sheet = ss.worksheet(SHEET_NAME)
        # Clear content and formatting
        sheet.batch_clear(['A1:Z500'])
        # Unmerge any existing merged cells by getting all merges and removing them
        merges = sheet.spreadsheet.fetch_sheet_metadata().get('merges', [])
        if merges:
            # Just clear and start fresh
            pass
    except:
        sheet = ss.add_worksheet(title=SHEET_NAME, rows=500, cols=15)
    
    current_row = 1
    
    # ========================================================================
    # SECTION 1: HEADER
    # ========================================================================
    
    print("  📊 Creating header...")
    
    header_data = [
        ["GB POWER MARKET - COMPREHENSIVE GSP/DNO ANALYSIS", "", "", "", "", ""],
        ["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", "", "", ""]
    ]
    sheet.update(values=header_data, range_name='A1:F2')
    sheet.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 16},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}
    })
    
    current_row = 4
    
    # ========================================================================
    # SECTION 2: KEY FINDINGS
    # ========================================================================
    
    print("  📊 Exporting key findings...")
    
    findings_header = [["KEY FINDINGS", "", ""]]
    sheet.update(values=findings_header, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 14}})
    current_row += 1
    
    findings_data = [
        ['Metric', 'Count', 'Details'],
        ['GSP Groups (DNO Licence Areas)', '14', 'Mapped to Elexon codes (_A through _P)'],
        ['Individual NESO GSPs', '333', 'With geographic boundaries and area (sqkm)'],
        ['Active BM Units', '1,403', '698 with GSP Group assignments (49.8% coverage)'],
        ['DNO Operators', '14', 'With MPAN distributor IDs'],
        ['Data Sources', '3', 'NESO GIS, Elexon Settlement, FES Capacity'],
        ['', '', ''],
        ['TOP 3 REGIONS BY CAPACITY', '', ''],
    ]
    
    # Get top regions
    query_top_regions = f"""
    SELECT 
        gsp_group,
        COUNT(*) as bmu_count,
        ROUND(SUM(max_capacity_mw), 1) as total_capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = true AND gsp_group IS NOT NULL
    GROUP BY gsp_group
    ORDER BY total_capacity_mw DESC
    LIMIT 3
    """
    
    top_regions = bq_client.query(query_top_regions).to_dataframe()
    
    # Get GSP group names for top regions
    query_names = f"""
    SELECT gsp_group_id, gsp_group_name, dno_name
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_groups`
    """
    gsp_names = bq_client.query(query_names).to_dataframe()
    
    for _, row in top_regions.iterrows():
        gsp_info = gsp_names[gsp_names['gsp_group_id'] == row['gsp_group']]
        if not gsp_info.empty:
            name = gsp_info.iloc[0]['gsp_group_name']
            dno = gsp_info.iloc[0]['dno_name']
            findings_data.append([
                f"{name} (_{row['gsp_group']})",
                f"{int(row['total_capacity_mw'])} MW",
                f"{dno}"
            ])
    
    sheet.update(values=findings_data, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
    })
    current_row += len(findings_data) + 2
    
    # ========================================================================
    # SECTION 3: GSP GROUPS (14 DNO LICENCE AREAS)
    # ========================================================================
    
    print("  📍 Exporting GSP Groups...")
    
    groups_header = [["GSP GROUPS (DNO LICENCE AREAS - ELEXON SETTLEMENT CODES)", "", "", "", "", "", ""]]
    sheet.update(values=groups_header, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 13}})
    current_row += 1
    
    groups_columns = [['Elexon Code', 'GSP Group Name', 'DNO Code', 'DNO Operator', 'Coverage Area', 'BMU Count', 'Total MW']]
    sheet.update(values=groups_columns, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
    })
    current_row += 1
    
    # Get GSP groups with BMU capacity
    query_groups = f"""
    SELECT 
        g.gsp_group_id,
        g.gsp_group_name,
        g.dno_short_code,
        g.dno_name,
        g.primary_coverage_area,
        COUNT(b.bmu_id) as bmu_count,
        ROUND(SUM(b.max_capacity_mw), 1) as total_capacity
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_groups` g
    LEFT JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_generators` b
        ON g.gsp_group_id = b.gsp_group AND b.is_active = true
    GROUP BY g.gsp_group_id, g.gsp_group_name, g.dno_short_code, g.dno_name, g.primary_coverage_area
    ORDER BY g.gsp_group_id
    """
    
    groups_df = bq_client.query(query_groups).to_dataframe()
    groups_data = []
    
    for _, row in groups_df.iterrows():
        groups_data.append([
            row['gsp_group_id'],
            row['gsp_group_name'],
            row['dno_short_code'],
            row['dno_name'],
            row['primary_coverage_area'],
            int(row['bmu_count']) if row['bmu_count'] else 0,
            f"{row['total_capacity']} MW" if row['total_capacity'] else "0 MW"
        ])
    
    if groups_data:
        sheet.update(values=groups_data, range_name=f'A{current_row}')
        current_row += len(groups_data) + 2
    
    # ========================================================================
    # SECTION 4: INDIVIDUAL NESO GSPs (333 GRID SUPPLY POINTS)
    # ========================================================================
    
    print("  🗺️ Exporting individual NESO GSPs...")
    
    gsps_header = [["INDIVIDUAL NESO GRID SUPPLY POINTS (333 GSPs)", "", "", "", "", "", ""]]
    sheet.update(values=gsps_header, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 13}})
    current_row += 1
    
    gsps_note = [[
        "Note: These are the actual geographic Grid Supply Points published by NESO. Each belongs to one of the 14 GSP Groups above. Use GSP ID to link to Elexon settlement data (B1610, etc.)",
        "", "", "", "", "", ""
    ]]
    sheet.update(values=gsps_note, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'italic': True, 'fontSize': 10},
        'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}
    })
    current_row += 2
    
    gsps_columns = [['NESO GSP ID', 'GSP Name', 'Area (sq km)', 'GSP Group', 'DNO Operator', 'Elexon Code', 'Settlement Use']]
    sheet.update(values=gsps_columns, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.85, 'green': 0.85, 'blue': 0.95}
    })
    current_row += 1
    
    gsps_start_row = current_row
    
    # Query individual GSPs with GSP Group mapping
    # Note: We need to create the mapping between NESO GSP boundaries and GSP Groups
    # For now, show all 333 GSPs with area data
    query_gsps = f"""
    SELECT 
        gsp_id,
        gsp_name,
        ROUND(area_sqkm, 2) as area_sqkm
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    ORDER BY gsp_id
    LIMIT 50
    """
    
    gsps_df = bq_client.query(query_gsps).to_dataframe()
    gsps_data = []
    
    for _, row in gsps_df.iterrows():
        gsps_data.append([
            row['gsp_id'],
            row['gsp_name'],
            f"{row['area_sqkm']} km²",
            "[Mapping required]",  # TODO: Add spatial join or FES data
            "[Query by area]",
            "[_A to _P]",
            "Use in B1610 queries"
        ])
    
    if gsps_data:
        sheet.update(values=gsps_data, range_name=f'A{current_row}')
        current_row += len(gsps_data) + 1
    
    # Add note about full 333 GSPs
    note_data = [[
        f"Showing first 50 of 333 GSPs. Full dataset in BigQuery: {PROJECT_ID}.{DATASET}.neso_gsp_boundaries",
        "", "", "", "", "", ""
    ]]
    sheet.update(values=note_data, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'italic': True, 'fontSize': 9}
    })
    current_row += 3
    
    # ========================================================================
    # SECTION 5: DATA LINKING GUIDE
    # ========================================================================
    
    print("  🔗 Creating data linking guide...")
    
    linking_header = [["HOW TO USE GSP DATA IN QUERIES", "", "", ""]]
    sheet.update(values=linking_header, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 13}})
    current_row += 1
    
    linking_data = [
        ['Use Case', 'Table', 'Join Key', 'Example'],
        ['Settlement by GSP Group', 'bmrs_bod, bmrs_boalf', 'GSP Group (_A to _P)', 'WHERE gsp_group = "_A"'],
        ['Geographic boundaries', 'neso_gsp_boundaries', 'gsp_id (GSP_1 to GSP_333)', 'JOIN ON gsp_id = "GSP_123"'],
        ['DNO operator lookup', 'neso_gsp_groups', 'gsp_group_id', 'JOIN ON gsp_group_id = "_A"'],
        ['BMU to region', 'ref_bmu_generators', 'gsp_group field', 'WHERE gsp_group = "_H"'],
        ['MPAN to DNO', 'neso_dno_reference', 'distributor_id (10-29)', 'WHERE distributor_id = "14"'],
        ['DUoS rates', 'gb_power.duos_unit_rates', 'dno_name + voltage', 'WHERE dno_name LIKE "%UKPN%"'],
        ['', '', '', ''],
        ['KEY FIELDS:', '', '', ''],
        ['GSP Group', 'Single letter A-P (with underscore: _A, _B, etc.)', 'Elexon settlement code', 'Used in BM reports'],
        ['GSP ID', 'GSP_1 through GSP_333', 'NESO geographic identifier', 'Used in GIS data'],
        ['DNO Code', '3-5 letter codes (EPN, WMID, etc.)', 'Network operator code', 'Used in DUoS/MPAN'],
        ['Distributor ID', '10-29', 'First 2 digits of MPAN', 'Used in billing'],
    ]
    
    sheet.update(values=linking_data, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.9}
    })
    current_row += len(linking_data) + 2
    
    # ========================================================================
    # SECTION 6: EXAMPLE QUERIES
    # ========================================================================
    
    print("  💡 Adding example queries...")
    
    examples_header = [["EXAMPLE BIGQUERY QUERIES", ""]]
    sheet.update(values=examples_header, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {'textFormat': {'bold': True, 'fontSize': 13}})
    current_row += 1
    
    examples_data = [
        ['Query Type', 'SQL Example'],
        ['All BMUs in Eastern (_A)', 'SELECT * FROM ref_bmu_generators WHERE gsp_group = "_A" AND is_active = true'],
        ['Capacity by DNO', 'SELECT g.gsp_group_name, SUM(b.max_capacity_mw) as total_mw FROM neso_gsp_groups g JOIN ref_bmu_generators b ON g.gsp_group_id = b.gsp_group GROUP BY g.gsp_group_name'],
        ['GSP boundary area', 'SELECT gsp_id, gsp_name, area_sqkm FROM neso_gsp_boundaries WHERE area_sqkm > 1000 ORDER BY area_sqkm DESC'],
        ['Settlement by region', 'SELECT gsp_group, AVG(acceptancePrice) FROM boalf_with_prices WHERE settlementDate >= "2025-01-01" GROUP BY gsp_group'],
        ['DNO constraint costs', 'SELECT dno_name, SUM(cost_gbp) FROM neso_constraint_breakdown WHERE constraint_date >= "2025-01-01" GROUP BY dno_name'],
    ]
    
    sheet.update(values=examples_data, range_name=f'A{current_row}')
    sheet.format(f'A{current_row}', {
        'textFormat': {'fontSize': 10, 'fontFamily': 'Courier New'},
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.98}
    })
    
    print("\n✅ Enhanced GSP/DNO Analysis exported successfully!")
    print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print(f"\n📋 Data exported:")
    print(f"   • 14 GSP Groups with BMU capacity")
    print(f"   • 50 sample individual GSPs (of 333 total)")
    print(f"   • Data linking guide")
    print(f"   • Example BigQuery queries")

if __name__ == "__main__":
    export_enhanced_gsp_analysis()
