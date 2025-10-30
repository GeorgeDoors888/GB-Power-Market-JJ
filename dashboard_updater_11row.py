#!/usr/bin/env python3
"""
Dashboard Updater for 11-row format
Updates numeric values while preserving emoji labels
"""
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import os
from datetime import datetime
import sys
import re

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

def update_value_in_cell(cell_value, new_number):
    """
    Update just the numeric value in a cell, preserving emoji and label
    Example: '💨 Gas: 15.2 GW' -> '💨 Gas: 18.5 GW'
    """
    # Use regex to find the number and replace it
    pattern = r'(\d+\.?\d*)\s*GW'
    replacement = f'{new_number:.1f} GW'
    
    if re.search(pattern, cell_value):
        return re.sub(pattern, replacement, cell_value)
    else:
        # If no existing GW value, just append it
        return f'{cell_value} {replacement}'

def update_dashboard_11row_format(sheet_id, data, timestamp, settlement_info):
    """
    Update the 11-row dashboard format
    Preserves all emoji labels and formatting, updates only numbers
    """
    try:
        gc = get_sheets_client()
        if not gc:
            return False
        
        sheet = gc.open_by_key(sheet_id)
        worksheet = sheet.worksheet("Sheet1")
        
        print(f"📝 Updating dashboard: {worksheet.title}")
        
        # Read current values
        all_values = worksheet.get_all_values()
        
        # Map fuel types to their BMRS codes
        fuel_mapping = {
            'Gas': 'CCGT',      # Combined Cycle Gas Turbine
            'Nuclear': 'NUCLEAR',
            'Wind': 'WIND',
            'Solar': 'SOLAR',
            'Biomass': 'BIOMASS',
            'Hydro': 'NPSHYD',  # Non-Pumped Storage Hydro
            'Coal': 'COAL'
        }
        
        # Interconnector mapping
        ic_mapping = {
            'IFA (France)': 'INTFR',
            'IFA2 (France)': 'INTIFA2',
            'BritNed (Netherlands)': 'INTNED',
            'Nemo (Belgium)': 'INTNEM',
            'NSL (Norway)': 'INTNSL',
            'Moyle (N. Ireland)': 'INTIRL'
        }
        
        # Prepare batch updates
        updates = []
        
        # Update timestamp in row 2
        timestamp_str = f"📅 Last Updated: {timestamp.strftime('%d %B %Y at %H:%M')}"
        if len(all_values) > 1:
            current_a2 = all_values[1][0]
            updates.append({
                'range': 'A2',
                'values': [[timestamp_str]]
            })
        
        # Update fuel values in column B (rows 5-11)
        for i, row in enumerate(all_values):
            row_num = i + 1
            if row_num >= 5 and row_num <= 11 and len(row) > 1:
                cell_b = row[1]  # Column B
                
                # Find which fuel type this is
                for fuel_label, fuel_code in fuel_mapping.items():
                    if fuel_label in cell_b or fuel_label.lower() in cell_b.lower():
                        if fuel_code in data:
                            new_value = update_value_in_cell(cell_b, data[fuel_code])
                            updates.append({
                                'range': f'B{row_num}',
                                'values': [[new_value]]
                            })
                            print(f"  ✓ Row {row_num} ({fuel_label}): {data[fuel_code]:.1f} GW")
                        break
            
            # Update interconnectors in column C
            if row_num >= 5 and row_num <= 10 and len(row) > 2:
                cell_c = row[2]  # Column C
                
                for ic_label, ic_code in ic_mapping.items():
                    if ic_label in cell_c:
                        if ic_code in data:
                            new_value = update_value_in_cell(cell_c, abs(data[ic_code]))
                            updates.append({
                                'range': f'C{row_num}',
                                'values': [[new_value]]
                            })
                            print(f"  ✓ Row {row_num} ({ic_label}): {abs(data[ic_code]):.1f} GW")
                        break
        
        # Batch update
        if updates:
            print(f"\n📊 Batch updating {len(updates)} cells...")
            worksheet.batch_update(updates)
            print(f"✅ Updated {len(updates)} cells successfully!")
        else:
            print("⚠️ No cells to update")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 UK POWER DASHBOARD UPDATER (11-Row Format)")
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
    
    # Update sheet
    print("📝 Updating Google Sheet...")
    success = update_dashboard_11row_format(DASHBOARD_SHEET_ID, data, timestamp, settlement_info)
    
    if success:
        print()
        print("=" * 80)
        print("✅ DASHBOARD UPDATE COMPLETE!")
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")
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
