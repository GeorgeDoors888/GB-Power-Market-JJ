#!/usr/bin/env python3
"""
Dashboard Updater - Preserves Formatting
Updates only DATA cells in the existing dashboard layout

This script updates ONLY the data values, preserving all:
- Formatting (colors, fonts, borders)
- Layout (merged cells, column widths)
- Formulas
- Headers and labels

Updates:
- B1: Last updated timestamp
- B2: Settlement date
- B3: Settlement period  
- B5-B8: Summary metrics
- B9: Grid status & biomass value
- B11-B20: Fuel type generation values
- B24-B33: Interconnector flow values
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

# Set up BigQuery
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
bq_client = bigquery.Client(project=PROJECT_ID)

# Set up Google Sheets
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
        print(f"❌ Failed to authenticate: {e}")
        return None

def get_latest_fuelinst_data():
    """Get latest generation data from FUELINST"""
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
                    'date': row.settlementDate.strftime('%Y-%m-%d'),
                    'period': row.settlementPeriod
                }
            
            fuel_type = row.fuelType
            generation_gw = row.generation / 1000  # MW to GW
            data[fuel_type] = generation_gw
        
        return data, timestamp, settlement_info
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return {}, None, {}

def calculate_metrics(data):
    """Calculate summary metrics"""
    metrics = {
        'total_generation': 0,
        'total_renewables': 0,
        'total_fossil': 0,
        'total_imports': 0,
        'total_exports': 0,
    }
    
    renewables = ['WIND', 'SOLAR', 'BIOMASS', 'NPSHYD', 'PS']
    fossils = ['CCGT', 'COAL', 'OCGT', 'OIL']
    
    for fuel_type, generation in data.items():
        if fuel_type.startswith('INT'):
            if generation > 0:
                metrics['total_imports'] += generation
            else:
                metrics['total_exports'] += abs(generation)
        else:
            metrics['total_generation'] += generation
            if fuel_type in renewables:
                metrics['total_renewables'] += generation
            elif fuel_type in fossils:
                metrics['total_fossil'] += generation
    
    metrics['net_import'] = metrics['total_imports'] - metrics['total_exports']
    
    if metrics['total_generation'] > 0:
        metrics['renewables_pct'] = (metrics['total_renewables'] / metrics['total_generation']) * 100
        metrics['fossil_pct'] = (metrics['total_fossil'] / metrics['total_generation']) * 100
    else:
        metrics['renewables_pct'] = 0
        metrics['fossil_pct'] = 0
    
    return metrics

def update_dashboard_data_only(sheet_id, data, metrics, timestamp, settlement_info):
    """
    Update ONLY data values, preserving all formatting
    Uses batch_update for efficiency
    """
    try:
        gc = get_sheets_client()
        if not gc:
            return False
        
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet("Sheet1")
        
        print(f"📝 Updating data values in: {worksheet.title}")
        
        # Prepare all updates as a list of cell updates
        # Format: list of {'range': 'A1', 'values': [['value']]}
        updates = []
        
        # === TOP SECTION ===
        # B1: Timestamp
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
        updates.append({
            'range': 'B1',
            'values': [[timestamp_str]]
        })
        
        # B2: Settlement Date
        updates.append({
            'range': 'B2',
            'values': [[settlement_info.get('date', 'N/A')]]
        })
        
        # B3: Settlement Period
        updates.append({
            'range': 'B3',
            'values': [[str(settlement_info.get('period', 'N/A'))]]
        })
        
        # === SUMMARY METRICS (Column B, Rows 5-8) ===
        # B5: Total Generation
        updates.append({
            'range': 'B5',
            'values': [[f"{metrics['total_generation']:.2f} GW"]]
        })
        
        # B6: Renewables
        updates.append({
            'range': 'B6',
            'values': [[f"{metrics['total_renewables']:.2f} GW ({metrics['renewables_pct']:.1f}%)"]]
        })
        
        # B7: Fossil Fuels
        updates.append({
            'range': 'B7',
            'values': [[f"{metrics['total_fossil']:.2f} GW ({metrics['fossil_pct']:.1f}%)"]]
        })
        
        # B8: Net Imports
        updates.append({
            'range': 'B8',
            'values': [[f"{metrics['net_import']:.2f} GW"]]
        })
        
        # === ROW 9: Biomass value (in B9) ===
        biomass_val = data.get('BIOMASS', 0)
        updates.append({
            'range': 'B9',
            'values': [[f"🌿 Biomass: {biomass_val:.1f} GW"]]
        })
        
        # === FUEL TYPE SECTION (B11-B20) ===
        # Map fuel types to their rows
        fuel_row_mapping = {
            'WIND': 11,
            'NUCLEAR': 12,
            'CCGT': 13,
            'BIOMASS': 14,
            'NPSHYD': 15,
            'COAL': 16,
            'OCGT': 17,
            'OIL': 18,
            'OTHER': 19,
            'PS': 20
        }
        
        for fuel_type, row_num in fuel_row_mapping.items():
            value = data.get(fuel_type, 0)
            updates.append({
                'range': f'B{row_num}',
                'values': [[f"{value:.2f}"]]
            })
        
        # === INTERCONNECTORS SECTION ===
        # Get all interconnectors from data
        interconnectors = {k: v for k, v in data.items() if k.startswith('INT')}
        
        # Sort by absolute value (descending)
        sorted_ics = sorted(interconnectors.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Update starting from row 24
        ic_start_row = 24
        for idx, (ic_code, value) in enumerate(sorted_ics):
            row_num = ic_start_row + idx
            if row_num > 35:  # Safety limit
                break
            
            # Determine direction
            if value > 0:
                direction = "→ Import"
            else:
                direction = "← Export"
            
            # Update Column A (interconnector name with direction)
            updates.append({
                'range': f'A{row_num}',
                'values': [[f"{ic_code} {direction}"]]
            })
            
            # Update Column B (absolute value)
            updates.append({
                'range': f'B{row_num}',
                'values': [[f"{abs(value):.2f}"]]
            })
        
        # Clear any remaining interconnector rows if we have fewer than before
        for row_num in range(ic_start_row + len(sorted_ics), 36):
            updates.append({
                'range': f'A{row_num}',
                'values': [['']]
            })
            updates.append({
                'range': f'B{row_num}',
                'values': [['']]
            })
        
        # === BATCH UPDATE ALL CELLS ===
        print(f"📊 Batch updating {len(updates)} cells...")
        
        # gspread batch_update expects a list of dicts
        worksheet.batch_update(updates)
        
        print(f"✅ Dashboard updated successfully!")
        print(f"   Updated {len(updates)} cells")
        print(f"   🔗 View: https://docs.google.com/spreadsheets/d/{sheet_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 UK POWER MARKET DASHBOARD UPDATER (Preserves Formatting)")
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Fetch data
    print("📥 Fetching latest data from BigQuery...")
    data, timestamp, settlement_info = get_latest_fuelinst_data()
    
    if not data:
        print("❌ No data retrieved. Exiting.")
        return 1
    
    print(f"✅ Retrieved data for {len(data)} fuel types")
    print(f"   Timestamp: {timestamp}")
    print(f"   Settlement: {settlement_info.get('date')} Period {settlement_info.get('period')}")
    print()
    
    # Calculate metrics
    print("📊 Calculating metrics...")
    metrics = calculate_metrics(data)
    
    print(f"   Total Generation: {metrics['total_generation']:.2f} GW")
    print(f"   Renewables: {metrics['total_renewables']:.2f} GW ({metrics['renewables_pct']:.1f}%)")
    print(f"   Fossil: {metrics['total_fossil']:.2f} GW ({metrics['fossil_pct']:.1f}%)")
    print(f"   Net Imports: {metrics['net_import']:.2f} GW")
    print()
    
    # Update sheet
    print("📝 Updating Google Sheet (data only, preserving formatting)...")
    success = update_dashboard_data_only(DASHBOARD_SHEET_ID, data, metrics, timestamp, settlement_info)
    
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
