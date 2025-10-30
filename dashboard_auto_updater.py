#!/usr/bin/env python3
"""
Automated Dashboard Updater for UK Power Market Data
Updates Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

This script:
1. Fetches latest data from BigQuery (FUELINST real-time data)
2. Calculates summary metrics
3. Updates specific cells in the Google Sheet dashboard
4. Can run automatically via cron

Usage:
    python dashboard_auto_updater.py
    
Cron setup (every 10 minutes):
    */10 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python dashboard_auto_updater.py >> logs/dashboard_updates.log 2>&1
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import os
from datetime import datetime
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"

# Set up BigQuery client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
bq_client = bigquery.Client(project=PROJECT_ID)

# Set up Google Sheets client
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_sheets_client():
    """Initialize Google Sheets client"""
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"❌ Failed to authenticate with Google Sheets: {e}")
        return None

def get_latest_fuelinst_data():
    """
    Get latest generation data from FUELINST (real-time data)
    Returns data by fuel type including interconnectors
    """
    query = f"""
    WITH latest_time AS (
        SELECT MAX(publishTime) as max_time
        FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst`
        WHERE DATE(settlementDate) >= CURRENT_DATE() - 1
    )
    SELECT 
        f.publishTime,
        f.settlementDate,
        f.settlementPeriod,
        f.fuelType,
        f.generation
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_fuelinst` f
    JOIN latest_time lt ON f.publishTime = lt.max_time
    ORDER BY f.generation DESC
    """
    
    try:
        results = bq_client.query(query).result()
        data = {}
        timestamp = None
        settlement_info = {}
        
        for row in results:
            if timestamp is None:
                timestamp = row.publishTime
                settlement_info = {
                    'date': row.settlementDate,
                    'period': row.settlementPeriod
                }
            
            fuel_type = row.fuelType
            generation_gw = row.generation / 1000  # Convert MW to GW
            data[fuel_type] = generation_gw
        
        return data, timestamp, settlement_info
        
    except Exception as e:
        print(f"❌ Error fetching FUELINST data: {e}")
        return {}, None, {}

def calculate_metrics(data):
    """Calculate summary metrics from raw data"""
    metrics = {
        'timestamp': None,
        'total_generation': 0,
        'total_renewables': 0,
        'total_fossil': 0,
        'total_imports': 0,
        'total_exports': 0,
        'net_import': 0,
        'by_fuel': {}
    }
    
    # Renewable fuel types
    renewables = ['WIND', 'SOLAR', 'BIOMASS', 'NPSHYD', 'PS']
    
    # Fossil fuel types
    fossils = ['CCGT', 'COAL', 'OCGT', 'OIL']
    
    # Interconnector prefix
    interconnector_prefix = 'INT'
    
    for fuel_type, generation in data.items():
        metrics['by_fuel'][fuel_type] = generation
        
        # Check if interconnector
        if fuel_type.startswith(interconnector_prefix):
            if generation > 0:
                metrics['total_imports'] += generation
            else:
                metrics['total_exports'] += abs(generation)
        else:
            # Count towards total generation
            metrics['total_generation'] += generation
            
            # Categorize
            if fuel_type in renewables:
                metrics['total_renewables'] += generation
            elif fuel_type in fossils:
                metrics['total_fossil'] += generation
    
    metrics['net_import'] = metrics['total_imports'] - metrics['total_exports']
    
    # Calculate percentages
    if metrics['total_generation'] > 0:
        metrics['renewables_pct'] = (metrics['total_renewables'] / metrics['total_generation']) * 100
        metrics['fossil_pct'] = (metrics['total_fossil'] / metrics['total_generation']) * 100
    else:
        metrics['renewables_pct'] = 0
        metrics['fossil_pct'] = 0
    
    return metrics

def update_dashboard(sheet_id, metrics, timestamp, settlement_info):
    """
    Update the Google Sheet dashboard with latest data
    
    Note: Cell mapping needs to be configured based on your actual dashboard layout
    """
    try:
        gc = get_sheets_client()
        if not gc:
            return False
        
        sheet = gc.open_by_key(sheet_id)
        
        # Try to find the main data sheet
        # Common names: "Dashboard", "Data", "Summary", "Main", or first sheet
        worksheet = None
        try:
            worksheet = sheet.worksheet("Dashboard")
        except:
            try:
                worksheet = sheet.worksheet("Data")
            except:
                try:
                    worksheet = sheet.worksheet("Summary")
                except:
                    # Use first sheet
                    worksheet = sheet.get_worksheet(0)
        
        if not worksheet:
            print("❌ Could not find worksheet to update")
            return False
        
        print(f"📝 Updating worksheet: {worksheet.title}")
        
        # Update timestamp (adjust cell references as needed)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
        updates = []
        
        # Example cell mappings - ADJUST THESE TO MATCH YOUR DASHBOARD LAYOUT
        # Format: (cell, value, label)
        cell_mappings = [
            # Timestamp
            ('A1', 'Last Updated:', 'label'),
            ('B1', timestamp_str, 'value'),
            
            # Settlement info
            ('A2', 'Settlement Date:', 'label'),
            ('B2', str(settlement_info.get('date', 'N/A')), 'value'),
            ('A3', 'Settlement Period:', 'label'),
            ('B3', str(settlement_info.get('period', 'N/A')), 'value'),
            
            # Summary metrics (Row 5+)
            ('A5', 'Total Generation:', 'label'),
            ('B5', f"{metrics['total_generation']:.2f} GW", 'value'),
            
            ('A6', 'Renewables:', 'label'),
            ('B6', f"{metrics['total_renewables']:.2f} GW ({metrics['renewables_pct']:.1f}%)", 'value'),
            
            ('A7', 'Fossil Fuels:', 'label'),
            ('B7', f"{metrics['total_fossil']:.2f} GW ({metrics['fossil_pct']:.1f}%)", 'value'),
            
            ('A8', 'Net Imports:', 'label'),
            ('B8', f"{metrics['net_import']:.2f} GW", 'value'),
            
            # Individual fuel types (starting row 10)
            ('A10', 'FUEL TYPE', 'header'),
            ('B10', 'GENERATION (GW)', 'header'),
        ]
        
        # Add individual fuel data
        row = 11
        for fuel_type in ['WIND', 'NUCLEAR', 'CCGT', 'BIOMASS', 'SOLAR', 'NPSHYD', 'COAL', 'OCGT', 'OIL', 'OTHER', 'PS']:
            if fuel_type in metrics['by_fuel']:
                cell_mappings.append((f'A{row}', fuel_type, 'label'))
                cell_mappings.append((f'B{row}', f"{metrics['by_fuel'][fuel_type]:.2f}", 'value'))
                row += 1
        
        # Add interconnector data
        row += 2  # Skip a row
        cell_mappings.append((f'A{row}', 'INTERCONNECTORS', 'header'))
        cell_mappings.append((f'B{row}', 'FLOW (GW)', 'header'))
        row += 1
        
        for fuel_type, value in sorted(metrics['by_fuel'].items()):
            if fuel_type.startswith('INT'):
                direction = '→ Import' if value > 0 else '← Export'
                cell_mappings.append((f'A{row}', f"{fuel_type} {direction}", 'label'))
                cell_mappings.append((f'B{row}', f"{abs(value):.2f}", 'value'))
                row += 1
        
        # Batch update all cells
        print(f"📊 Updating {len(cell_mappings)} cells...")
        for cell, value, _ in cell_mappings:
            worksheet.update_acell(cell, value)
        
        print(f"✅ Dashboard updated successfully!")
        print(f"   🔗 View: https://docs.google.com/spreadsheets/d/{sheet_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution function"""
    print("=" * 80)
    print("🔄 UK POWER MARKET DASHBOARD AUTO-UPDATER")
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Fetch data from BigQuery
    print("📥 Fetching latest data from BigQuery...")
    data, timestamp, settlement_info = get_latest_fuelinst_data()
    
    if not data:
        print("❌ No data retrieved. Exiting.")
        return 1
    
    print(f"✅ Retrieved data for {len(data)} fuel types")
    print(f"   Timestamp: {timestamp}")
    print(f"   Settlement: {settlement_info.get('date')} Period {settlement_info.get('period')}")
    print()
    
    # Step 2: Calculate metrics
    print("📊 Calculating metrics...")
    metrics = calculate_metrics(data)
    
    print(f"   Total Generation: {metrics['total_generation']:.2f} GW")
    print(f"   Renewables: {metrics['total_renewables']:.2f} GW ({metrics['renewables_pct']:.1f}%)")
    print(f"   Fossil: {metrics['total_fossil']:.2f} GW ({metrics['fossil_pct']:.1f}%)")
    print(f"   Net Imports: {metrics['net_import']:.2f} GW")
    print()
    
    # Step 3: Update Google Sheet
    print("📝 Updating Google Sheet dashboard...")
    success = update_dashboard(DASHBOARD_SHEET_ID, metrics, timestamp, settlement_info)
    
    if success:
        print()
        print("=" * 80)
        print("✅ DASHBOARD UPDATE COMPLETE!")
        print("=" * 80)
        return 0
    else:
        print()
        print("=" * 80)
        print("❌ DASHBOARD UPDATE FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
