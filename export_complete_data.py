#!/usr/bin/env python3
"""
Complete Data Export to Google Sheets
Exports all available fields for BM Units, BSC Parties, Balancing Revenue, Network Details
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def get_bigquery_client():
    """Initialize BigQuery client"""
    return bigquery.Client(project=PROJECT_ID, location="US")

def get_sheets_client():
    """Initialize Google Sheets client"""
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    return gspread.authorize(creds)

def export_bm_units_detail():
    """Export complete BM Unit details"""
    print("📊 Exporting BM Units Detail...")
    
    bq_client = get_bigquery_client()
    sheets_client = get_sheets_client()
    
    query = f"""
    SELECT 
        bmu_id,
        bmu_name,
        fuel_type_category,
        max_capacity_mw,
        lead_party_name,
        party_classification,
        gsp_group,
        is_active,
        effective_from,
        effective_to,
        bmu_type,
        fpn_flag,
        CAST(NULL AS BOOL) as interconnector_flag,
        CAST(NULL AS STRING) as voltage_level
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = TRUE
    ORDER BY bmu_name
    """
    
    results = bq_client.query(query).result()
    
    # Prepare data
    data = [['BMU ID', 'Name', 'Fuel Type', 'Capacity (MW)', 'Lead Party', 
             'Classification', 'GSP Group', 'Active', 'Effective From', 'Effective To',
             'Unit Type', 'FPN Flag', 'Interconnector', 'Voltage']]
    
    for row in results:
        data.append([
            row.bmu_id or '',
            row.bmu_name or '',
            row.fuel_type_category or '',
            row.max_capacity_mw or 0,
            row.lead_party_name or '',
            row.party_classification or '',
            row.gsp_group or '',
            'Yes' if row.is_active else 'No',
            str(row.effective_from) if row.effective_from else '',
            str(row.effective_to) if row.effective_to else '',
            row.bmu_type or '',
            row.fpn_flag or '',
            'No',  # interconnector_flag placeholder
            ''     # voltage_level placeholder
        ])
    
    # Write to sheet
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    
    # Create or get sheet
    try:
        sheet = spreadsheet.worksheet('BM Units Detail')
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet('BM Units Detail', rows=2000, cols=15)
    
    # Write data
    sheet.update('A1', data)
    
    # Format header
    sheet.format('A1:N1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86}
    })
    
    print(f"   ✅ Exported {len(data)-1} BM Units to 'BM Units Detail' sheet")
    return len(data) - 1

def export_balancing_revenue():
    """Export recent balancing activity with revenue estimates"""
    print("💰 Exporting Balancing Revenue...")
    
    bq_client = get_bigquery_client()
    sheets_client = get_sheets_client()
    
    # Last 30 days of validated acceptances
    query = f"""
    WITH recent_activity AS (
        SELECT 
            bmUnit,
            COUNT(*) as acceptance_count,
            SUM(acceptanceVolume) as total_volume_mw,
            AVG(acceptancePrice) as avg_price_mwh,
            MIN(acceptancePrice) as min_price_mwh,
            MAX(acceptancePrice) as max_price_mwh,
            SUM(acceptanceVolume * acceptancePrice / 2) as revenue_estimate_gbp,
            MAX(acceptanceTime) as latest_acceptance
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf_complete`
        WHERE acceptanceTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        AND validation_flag = 'Valid'
        GROUP BY bmUnit
    )
    SELECT 
        ra.*,
        rg.bmu_name,
        rg.fuel_type_category,
        rg.lead_party_name,
        rg.max_capacity_mw
    FROM recent_activity ra
    LEFT JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_generators` rg
        ON ra.bmUnit = rg.bmu_id
    ORDER BY ra.revenue_estimate_gbp DESC
    LIMIT 500
    """
    
    results = bq_client.query(query).result()
    
    # Prepare data
    data = [['BMU ID', 'Name', 'Fuel Type', 'Lead Party', 'Capacity (MW)',
             'Acceptances (30d)', 'Total Volume (MWh)', 'Avg Price (£/MWh)', 
             'Min Price', 'Max Price', 'Revenue Est. (£)', 'Latest Activity']]
    
    for row in results:
        data.append([
            row.bmUnit or '',
            row.bmu_name or '',
            row.fuel_type_category or '',
            row.lead_party_name or '',
            row.max_capacity_mw or 0,
            row.acceptance_count or 0,
            f"{row.total_volume_mw:.1f}" if row.total_volume_mw else '0',
            f"{row.avg_price_mwh:.2f}" if row.avg_price_mwh else '0',
            f"{row.min_price_mwh:.2f}" if row.min_price_mwh else '0',
            f"{row.max_price_mwh:.2f}" if row.max_price_mwh else '0',
            f"{row.revenue_estimate_gbp:.0f}" if row.revenue_estimate_gbp else '0',
            str(row.latest_acceptance) if row.latest_acceptance else ''
        ])
    
    # Write to sheet
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    
    try:
        sheet = spreadsheet.worksheet('Balancing Revenue')
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet('Balancing Revenue', rows=600, cols=12)
    
    sheet.update('A1', data)
    
    # Format header
    sheet.format('A1:L1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.3, 'green': 0.7, 'blue': 0.3}
    })
    
    print(f"   ✅ Exported {len(data)-1} units with balancing revenue to 'Balancing Revenue' sheet")
    return len(data) - 1

def export_network_locations():
    """Export DNO and GSP network details"""
    print("📍 Exporting Network Locations...")
    
    bq_client = get_bigquery_client()
    sheets_client = get_sheets_client()
    
    query = f"""
    SELECT 
        dno_name,
        dno_short_code,
        gsp_group_id,
        gsp_group_name,
        mpan_distributor_id,
        market_participant_id
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
    WHERE dno_name IS NOT NULL
    ORDER BY gsp_group_name, dno_name
    """
    
    results = bq_client.query(query).result()
    
    # Prepare data
    data = [['DNO Name', 'Short Code', 'GSP Group ID', 'GSP Group Name', 
             'MPAN Distributor ID', 'Market Participant ID']]
    
    for row in results:
        data.append([
            row.dno_name or '',
            row.dno_short_code or '',
            row.gsp_group_id or '',
            row.gsp_group_name or '',
            row.mpan_distributor_id or '',
            row.market_participant_id or ''
        ])
    
    # Write to sheet
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    
    try:
        sheet = spreadsheet.worksheet('Network Locations')
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet('Network Locations', rows=100, cols=6)
    
    sheet.update('A1', data)
    
    # Format header
    sheet.format('A1:F1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.95, 'green': 0.6, 'blue': 0.2}
    })
    
    print(f"   ✅ Exported {len(data)-1} DNO/GSP mappings to 'Network Locations' sheet")
    return len(data) - 1

def export_bsc_parties():
    """Export BSC registered parties"""
    print("🏢 Exporting BSC Parties...")
    
    bq_client = get_bigquery_client()
    sheets_client = get_sheets_client()
    
    query = f"""
    SELECT 
        party_id,
        party_name,
        is_vlp,
        is_vtp,
        bmu_count,
        data_source
    FROM `{PROJECT_ID}.{DATASET}.dim_party`
    ORDER BY party_name
    """
    
    results = bq_client.query(query).result()
    
    # Prepare data
    data = [['Party ID', 'Party Name', 'VLP Status', 'VTP Status', 'BMU Count', 'Data Source']]
    
    for row in results:
        data.append([
            row.party_id or '',
            row.party_name or '',
            'Yes' if row.is_vlp else 'No',
            'Yes' if row.is_vtp else 'No',
            row.bmu_count or 0,
            row.data_source or ''
        ])
    
    # Write to sheet
    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    
    try:
        sheet = spreadsheet.worksheet('BSC Parties Detail')
        sheet.clear()
    except:
        sheet = spreadsheet.add_worksheet('BSC Parties Detail', rows=500, cols=5)
    
    sheet.update('A1', data)
    
    # Format header
    sheet.format('A1:E1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.6, 'green': 0.4, 'blue': 0.8}
    })
    
    print(f"   ✅ Exported {len(data)-1} BSC parties to 'BSC Parties Detail' sheet")
    return len(data) - 1

def main():
    """Export all data"""
    print("🚀 Starting Complete Data Export\n")
    print(f"Target Spreadsheet: {SPREADSHEET_ID}\n")
    
    try:
        count_bmu = export_bm_units_detail()
        count_revenue = export_balancing_revenue()
        count_network = export_network_locations()
        count_parties = export_bsc_parties()
        
        print(f"\n✅ EXPORT COMPLETE!")
        print(f"   - {count_bmu} BM Units")
        print(f"   - {count_revenue} Units with balancing revenue")
        print(f"   - {count_network} DNO/GSP mappings")
        print(f"   - {count_parties} BSC Parties")
        print(f"\n📊 View at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
        
    except Exception as e:
        print(f"\n❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
