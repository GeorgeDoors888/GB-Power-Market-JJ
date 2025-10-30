#!/usr/bin/env python3
"""
Combined Dashboard Updater - Main Generation + REMIT Unavailability in Sheet1
Updates both real-time generation data and REMIT outage information in the same sheet
"""
import gspread
import pickle
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
FUELINST_TABLE = "bmrs_fuelinst"
REMIT_TABLE = "bmrs_remit_unavailability"
DASHBOARD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"

def get_sheets_client():
    """Initialize Google Sheets client"""
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    return gspread.authorize(creds)

def get_latest_fuelinst_data():
    """Get latest generation data from BigQuery"""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    WITH latest_time AS (
        SELECT MAX(publishTime) as max_time
        FROM `{PROJECT_ID}.{DATASET_ID}.{FUELINST_TABLE}`
        WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
    )
    SELECT 
        f.fuelType,
        f.generation,
        f.publishTime,
        f.settlementDate,
        f.settlementPeriod
    FROM `{PROJECT_ID}.{DATASET_ID}.{FUELINST_TABLE}` f
    CROSS JOIN latest_time
    WHERE f.publishTime = latest_time.max_time
    ORDER BY f.fuelType
    """
    
    results = list(bq_client.query(query).result())
    
    data = {}
    timestamp = None
    settlement_info = {}
    
    for row in results:
        fuel_type = row.fuelType
        generation_mw = float(row.generation) if row.generation else 0.0
        generation_gw = generation_mw / 1000.0
        
        data[fuel_type] = generation_gw
        
        if timestamp is None:
            timestamp = row.publishTime
            settlement_info = {
                'date': row.settlementDate,
                'period': row.settlementPeriod
            }
    
    return data, timestamp, settlement_info

def get_active_remit_events():
    """Get active REMIT unavailability events"""
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT
        assetName,
        affectedUnit,
        fuelType,
        normalCapacity,
        availableCapacity,
        unavailableCapacity,
        CAST(eventStartTime AS STRING) as eventStartTime,
        CAST(eventEndTime AS STRING) as eventEndTime,
        cause,
        eventStatus,
        participantName
    FROM `{PROJECT_ID}.{DATASET_ID}.{REMIT_TABLE}`
    WHERE eventStatus = 'Active'
      AND DATETIME(eventStartTime) <= CURRENT_DATETIME()
      AND DATETIME(eventEndTime) >= CURRENT_DATETIME()
    ORDER BY unavailableCapacity DESC
    LIMIT 20
    """
    
    try:
        results = list(bq_client.query(query).result())
        
        events = []
        for row in results:
            events.append({
                'assetName': row.assetName,
                'affectedUnit': row.affectedUnit,
                'fuelType': row.fuelType,
                'normalCapacity': float(row.normalCapacity) if row.normalCapacity else 0.0,
                'availableCapacity': float(row.availableCapacity) if row.availableCapacity else 0.0,
                'unavailableCapacity': float(row.unavailableCapacity) if row.unavailableCapacity else 0.0,
                'eventStartTime': pd.to_datetime(row.eventStartTime),
                'eventEndTime': pd.to_datetime(row.eventEndTime),
                'cause': row.cause,
                'participantName': row.participantName
            })
        
        return pd.DataFrame(events) if events else pd.DataFrame()
    except Exception as e:
        print(f"⚠️  Could not fetch REMIT data: {e}")
        return pd.DataFrame()

def calculate_system_metrics(data):
    """Calculate system-wide metrics"""
    fuel_mapping = {
        'CCGT': 'Gas', 'NUCLEAR': 'Nuclear', 'WIND': 'Wind',
        'PS': 'Solar', 'BIOMASS': 'Biomass', 'NPSHYD': 'Hydro', 'COAL': 'Coal'
    }
    
    interconnector_mapping = {
        'INTFR': 'IFA', 'INTIFA2': 'IFA2', 'INTNED': 'BritNed',
        'INTNEM': 'Nemo', 'INTNSL': 'NSL', 'INTIRL': 'Moyle'
    }
    
    renewable_types = ['WIND', 'PS', 'BIOMASS', 'NPSHYD']
    
    fuel_data = {}
    interconnector_data = {}
    total_generation = 0.0
    renewable_generation = 0.0
    
    for fuel_type, generation in data.items():
        if fuel_type in fuel_mapping:
            fuel_data[fuel_mapping[fuel_type]] = generation
            total_generation += generation
            if fuel_type in renewable_types:
                renewable_generation += generation
        elif fuel_type in interconnector_mapping:
            interconnector_data[interconnector_mapping[fuel_type]] = generation
    
    total_interconnector = sum(interconnector_data.values())
    total_supply = total_generation + total_interconnector
    renewables_pct = (renewable_generation / total_generation * 100) if total_generation > 0 else 0
    
    return {
        'fuel_data': fuel_data,
        'interconnector_data': interconnector_data,
        'total_generation': total_generation,
        'total_supply': total_supply,
        'renewables_pct': renewables_pct
    }

def update_combined_dashboard(sheet_id, gen_data, metrics, timestamp, settlement_info, remit_df):
    """Update Sheet1 with both generation and REMIT data"""
    
    gc = get_sheets_client()
    spreadsheet = gc.open_by_key(sheet_id)
    sheet = spreadsheet.worksheet(SHEET_NAME)
    
    fuel_data = metrics['fuel_data']
    interconnector_data = metrics['interconnector_data']
    
    # Build updates list
    updates = []
    
    # Row 1: Title (keep existing)
    # Row 2: Last Updated
    updates.append({
        'range': 'A2',
        'values': [[f"⏰ Last Updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} (Period {settlement_info.get('period', 'N/A')})"]]
    })
    
    # Row 3: Settlement info (optional)
    
    # Row 4: System metrics
    updates.append({
        'range': 'A4',
        'values': [[f"⚡ Total Generation: {metrics['total_generation']:.1f} GW"]]
    })
    updates.append({
        'range': 'B4',
        'values': [[f"📊 Total Supply: {metrics['total_supply']:.1f} GW"]]
    })
    updates.append({
        'range': 'C4',
        'values': [[f"🌱 Renewables: {metrics['renewables_pct']:.1f}%"]]
    })
    
    # Rows 5-11: Generation by fuel type
    updates.append({'range': 'A5', 'values': [[f"🔥 Gas: {fuel_data.get('Gas', 0):.1f} GW"]]})
    updates.append({'range': 'A6', 'values': [[f"⚛️ Nuclear: {fuel_data.get('Nuclear', 0):.1f} GW"]]})
    updates.append({'range': 'A7', 'values': [[f"💨 Wind: {fuel_data.get('Wind', 0):.1f} GW"]]})
    updates.append({'range': 'A8', 'values': [[f"☀️ Solar: {fuel_data.get('Solar', 0):.1f} GW"]]})
    updates.append({'range': 'A9', 'values': [[f"🌿 Biomass: {fuel_data.get('Biomass', 0):.1f} GW"]]})
    updates.append({'range': 'A10', 'values': [[f"💧 Hydro: {fuel_data.get('Hydro', 0):.1f} GW | 💷 NOOD POOL: £0.00/MWh"]]})
    updates.append({'range': 'A11', 'values': [[f"⚫ Coal: {fuel_data.get('Coal', 0):.1f} GW | 💶 EPEX SPOT: £76.33/MWh"]]})
    
    # Interconnectors (Column E)
    updates.append({'range': 'E5', 'values': [[f"🇫🇷 IFA: {interconnector_data.get('IFA', 0):.1f} GW"]]})
    updates.append({'range': 'E6', 'values': [[f"🇫🇷 IFA2: {interconnector_data.get('IFA2', 0):.1f} GW"]]})
    updates.append({'range': 'E7', 'values': [[f"🇳🇱 BritNed: {interconnector_data.get('BritNed', 0):.1f} GW"]]})
    updates.append({'range': 'E8', 'values': [[f"🇧🇪 Nemo: {interconnector_data.get('Nemo', 0):.1f} GW"]]})
    updates.append({'range': 'E9', 'values': [[f"🇳🇴 NSL: {interconnector_data.get('NSL', 0):.1f} GW"]]})
    updates.append({'range': 'E10', 'values': [[f"🇮🇪 Moyle: {interconnector_data.get('Moyle', 0):.1f} GW"]]})
    
    print(f"  ✓ Updated generation data (31 cells)")
    
    # Now add REMIT section starting at row 13
    remit_start_row = 13
    
    if not remit_df.empty:
        total_unavailable = remit_df['unavailableCapacity'].sum()
        num_events = len(remit_df)
        
        # REMIT Header
        updates.append({
            'range': f'A{remit_start_row}',
            'values': [['']]  # Empty row
        })
        
        updates.append({
            'range': f'A{remit_start_row + 1}',
            'values': [['🔴 REMIT UNAVAILABILITY - ACTIVE OUTAGES']]
        })
        
        updates.append({
            'range': f'A{remit_start_row + 2}',
            'values': [[f'Active Events: {num_events} | Total Unavailable: {total_unavailable:.0f} MW']]
        })
        
        updates.append({
            'range': f'A{remit_start_row + 3}',
            'values': [['']]  # Empty row
        })
        
        # Table header
        header_row = remit_start_row + 4
        updates.append({
            'range': f'A{header_row}:F{header_row}',
            'values': [['Asset Name', 'BM Unit', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', 'Cause']]
        })
        
        # Event rows
        data_start_row = header_row + 1
        for idx, row in remit_df.iterrows():
            row_num = data_start_row + idx
            duration_hours = (row['eventEndTime'] - row['eventStartTime']).total_seconds() / 3600
            cause_short = row['cause'][:40] if pd.notna(row['cause']) else ""
            
            updates.append({
                'range': f'A{row_num}:F{row_num}',
                'values': [[
                    row['assetName'],
                    row['affectedUnit'],
                    row['fuelType'],
                    f"{row['normalCapacity']:.0f}",
                    f"{row['unavailableCapacity']:.0f}",
                    cause_short
                ]]
            })
        
        print(f"  ✓ Added REMIT data ({num_events} outages, {total_unavailable:.0f} MW)")
    else:
        # No active events
        updates.append({
            'range': f'A{remit_start_row + 1}',
            'values': [['🔴 REMIT UNAVAILABILITY']]
        })
        updates.append({
            'range': f'A{remit_start_row + 2}',
            'values': [['✅ No active unplanned outages at this time']]
        })
        print(f"  ✓ No active REMIT events")
    
    # Batch update
    print(f"📊 Batch updating {len(updates)} ranges...")
    sheet.batch_update(updates)
    
    return True

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 COMBINED DASHBOARD UPDATER (Generation + REMIT)")
    print("=" * 80)
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Get generation data
    print("📥 Fetching generation data from BigQuery...")
    gen_data, timestamp, settlement_info = get_latest_fuelinst_data()
    
    if not gen_data:
        print("❌ No generation data retrieved. Exiting.")
        return 1
    
    print(f"✅ Retrieved data for {len(gen_data)} fuel types")
    print(f"   Timestamp: {timestamp}")
    print(f"   Settlement: {settlement_info.get('date')} Period {settlement_info.get('period')}\n")
    
    # Calculate metrics
    print("📊 Calculating system metrics...")
    metrics = calculate_system_metrics(gen_data)
    print(f"   Total Generation: {metrics['total_generation']:.1f} GW")
    print(f"   Total Supply: {metrics['total_supply']:.1f} GW")
    print(f"   Renewables: {metrics['renewables_pct']:.1f}%\n")
    
    # Get REMIT data
    print("📥 Fetching REMIT unavailability data...")
    remit_df = get_active_remit_events()
    
    if not remit_df.empty:
        print(f"✅ Retrieved {len(remit_df)} active outage events")
        print(f"   Total Unavailable: {remit_df['unavailableCapacity'].sum():.0f} MW\n")
    else:
        print("ℹ️  No active outages found\n")
    
    # Update dashboard
    print("📝 Updating Google Sheet...")
    success = update_combined_dashboard(
        DASHBOARD_SHEET_ID, 
        gen_data, 
        metrics, 
        timestamp, 
        settlement_info,
        remit_df
    )
    
    if success:
        print("\n" + "=" * 80)
        print("✅ COMBINED DASHBOARD UPDATE COMPLETE!")
        print(f"🔗 View: https://docs.google.com/spreadsheets/d/{DASHBOARD_SHEET_ID}")
        print("=" * 80)
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ DASHBOARD UPDATE FAILED")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
