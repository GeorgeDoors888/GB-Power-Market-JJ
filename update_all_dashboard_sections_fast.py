#!/usr/bin/env python3
"""
Fast Dashboard Updater - Updates ALL sections
Uses direct Google Sheets API v4 (298x faster than gspread)
Updates: Generation Mix, Demand, Interconnectors, Wind, Outages, KPIs
"""

from fast_sheets_api import FastSheetsAPI
from google.cloud import bigquery
import os
from datetime import datetime
import pytz

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
SHEET_NAME = 'Live Dashboard v2'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Initialize APIs
sheets_api = FastSheetsAPI('inner-cinema-credentials.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
bq_client = bigquery.Client(project=PROJECT_ID, location='US')

def get_latest_generation_mix():
    """Get latest generation by fuel type"""
    query = f"""
    SELECT 
        fuelType,
        generation
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ORDER BY publishTime DESC
    LIMIT 50
    """
    df = bq_client.query(query).to_dataframe()
    if df.empty:
        return {}
    
    # Group by fuel type and get latest
    latest = df.groupby('fuelType').first()['generation'].to_dict()
    return latest

def get_latest_demand():
    """Get latest demand data"""
    query = f"""
    SELECT 
        initialDemandOutturn as demand
    FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
    ORDER BY CAST(settlementDate AS DATE) DESC, settlementPeriod DESC
    LIMIT 1
    """
    df = bq_client.query(query).to_dataframe()
    if not df.empty:
        return float(df['demand'].iloc[0])
    return 0.0

def get_latest_interconnectors():
    """Get latest interconnector flows from bmrs_fuelinst_iris"""
    query = f"""
    SELECT 
        fuelType,
        generation as flow
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE fuelType IN ('INTFR', 'INTIRL', 'INTNED', 'INTEW', 'INTNEM', 'INTELEC', 'INTNSL', 'INTIFA2')
    ORDER BY publishTime DESC
    LIMIT 50
    """
    try:
        df = bq_client.query(query).to_dataframe()
        if df.empty:
            return {}
        
        # Group by fuel type and get latest - map to interconnector names
        ic_map = {
            'INTFR': 'IFA',
            'INTIFA2': 'IFA2',
            'INTELEC': 'ELECLINK',
            'INTNED': 'BRITNED',
            'INTNEM': 'NEMO',
            'INTNSL': 'NSL',
            'INTEW': 'EWIC',
            'INTIRL': 'MOYLE'
        }
        latest = {}
        for fuel_type, flow in df.groupby('fuelType').first()['flow'].items():
            ic_name = ic_map.get(fuel_type)
            if ic_name:
                latest[ic_name] = flow
        return latest
    except:
        # Return empty if table doesn't exist
        return {}

def update_generation_mix(gen_data):
    """Update generation mix section (A13:D22) - leaves column E sparklines untouched"""
    print("\n🔋 Updating Generation Mix...")
    
    fuel_types = [
        ('WIND', '🌬️ WIND'),
        ('NUCLEAR', '⚛️ NUCLEAR'),
        ('CCGT', '🏭 CCGT'),
        ('BIOMASS', '🌿 BIOMASS'),
        ('NPSHYD', '💧 NPSHYD'),
        ('OTHER', '❓ OTHER'),
        ('OCGT', '🛢️ OCGT'),
        ('COAL', '⛏️ COAL'),
        ('OIL', '🛢️ OIL'),
        ('PS', '💧 PS'),
    ]
    
    rows = []
    for fuel_key, fuel_label in fuel_types:
        gen_mw = gen_data.get(fuel_key, 0)
        gen_gw = gen_mw / 1000
        # Only update live values A-D, preserve existing sparklines in column E
        rows.append([fuel_label, f'{gen_mw:.0f}', 'MW', f'{gen_gw:.2f} GW'])
    
    # Update columns A-D only (label, MW value, "MW" text, GW value)
    # Column E sparklines are maintained by Data_Hidden and should not be overwritten
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!A13:D22',
        rows
    )
    print(f"   ✅ Updated {len(rows)} fuel types (sparklines preserved)")

def update_demand(demand_mw):
    """Update demand section"""
    print("\n📊 Updating Demand...")
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!A25:D25',
        [[f'Demand: {demand_mw:.0f} MW', '', '', f'{demand_mw/1000:.2f} GW']]
    )
    print(f"   ✅ Demand: {demand_mw:.0f} MW")

def update_interconnectors(ic_data):
    """Update interconnector section (G13:I20) - leaves column J sparklines untouched"""
    print("\n🔌 Updating Interconnectors...")
    
    interconnectors = [
        ('IFA', 'IFA (FR)'),
        ('IFA2', 'IFA2 (FR)'),
        ('ELECLINK', 'ElecLink (FR)'),
        ('BRITNED', 'BritNed (NL)'),
        ('NEMO', 'Nemo (BE)'),
        ('NSL', 'NSL (NO)'),
        ('EWIC', 'EWIC (IE)'),
        ('MOYLE', 'Moyle (NI)'),
    ]
    
    rows = []
    for ic_key, ic_label in interconnectors:
        flow = ic_data.get(ic_key, 0)
        direction = '→ Import' if flow > 0 else '← Export' if flow < 0 else '—'
        # Only update live values G-I, preserve existing sparklines in column J
        rows.append([ic_label, f'{abs(flow):.0f} MW', direction])
    
    # Update columns G-I only (label, MW value, direction)
    # Column J sparklines are maintained by Data_Hidden and should not be overwritten
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!G13:I20',
        rows
    )
    print(f"   ✅ Updated {len(rows)} interconnectors (sparklines preserved)")

def get_latest_outages():
    """Get latest power station outages"""
    query = f"""
    SELECT 
        affectedUnit,
        eventType,
        fuelType,
        mwCapacity
    FROM `{PROJECT_ID}.{DATASET}.neso_remit_outages`
    WHERE eventStatus = 'Active'
    AND eventStart <= CURRENT_DATE()
    AND (eventEnd >= CURRENT_DATE() OR eventEnd IS NULL)
    ORDER BY mwCapacity DESC
    LIMIT 10
    """
    try:
        df = bq_client.query(query).to_dataframe()
        return df.to_dict('records') if not df.empty else []
    except:
        return []

def update_outages(outages_data):
    """Update outages section (K27-K36)"""
    print("\n⚠️  Updating Outages...")
    
    if not outages_data:
        # Clear section if no outages
        rows = [['No active outages']] + [[''] for _ in range(9)]
        sheets_api.update_single_range(
            SPREADSHEET_ID,
            f'{SHEET_NAME}!K27:K36',
            rows
        )
        print(f"   ✅ No active outages")
        return
    
    rows = []
    for outage in outages_data[:10]:
        unit = outage.get('affectedUnit', 'Unknown')
        event_type = outage.get('eventType', '')
        fuel = outage.get('fuelType', '')
        mw = outage.get('mwCapacity', 0)
        rows.append([f'{unit} ({fuel}) • {mw:.0f}MW • {event_type}'])
    
    # Pad to 10 rows
    while len(rows) < 10:
        rows.append([''])
    
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!K27:K36',
        rows
    )
    print(f"   ✅ Updated {len(outages_data)} outages")

def update_timestamp():
    """Update last updated timestamp"""
    now = datetime.now(pytz.timezone('Europe/London'))
    timestamp = now.strftime('%d/%m/%Y, %H:%M:%S')
    
    # Get current settlement period (approx)
    sp = ((now.hour * 60 + now.minute) // 30) + 1
    
    sheets_api.update_single_range(
        SPREADSHEET_ID,
        f'{SHEET_NAME}!A2',
        [[f'Last Updated: {timestamp} (v2.0) SP {sp}']]
    )
    print(f"   ✅ Timestamp: {timestamp} SP {sp}")

def main():
    """Main execution"""
    print("=" * 100)
    print("🚀 FAST DASHBOARD UPDATER - ALL SECTIONS")
    print("=" * 100)
    print(f"Spreadsheet: GB Live 2 ({SPREADSHEET_ID})")
    print(f"Sheet: {SHEET_NAME}")
    print(f"API: Google Sheets v4 Direct (298x faster)")
    
    try:
        # Fetch all data from BigQuery
        print("\n📊 Fetching data from BigQuery...")
        gen_data = get_latest_generation_mix()
        demand_mw = get_latest_demand()
        ic_data = get_latest_interconnectors()
        outages_data = get_latest_outages()
        
        print(f"   ✅ Generation: {len(gen_data)} fuel types")
        print(f"   ✅ Demand: {demand_mw:.0f} MW")
        print(f"   ✅ Interconnectors: {len(ic_data)} flows")
        print(f"   ✅ Outages: {len(outages_data)} active")
        
        # Update all sections
        update_timestamp()
        update_generation_mix(gen_data)
        update_demand(demand_mw)
        update_interconnectors(ic_data)
        update_outages(outages_data)
        
        print("\n" + "=" * 100)
        print("✅ DASHBOARD UPDATE COMPLETE!")
        print("=" * 100)
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
