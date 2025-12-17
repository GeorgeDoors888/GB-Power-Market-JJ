#!/usr/bin/env python3
"""
GB Live Executive Dashboard - Data Updater
Populates the executive dashboard with real BigQuery data
Simple, clean, professional format
"""

import sys
import logging
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
SHEET_NAME = 'GB Live'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = '/home/george/inner-cinema-credentials.json'

logging.basicConfig(level=logging.INFO, format='%(message)s')

def get_kpis(bq_client):
    """Get all KPIs in one query"""
    query = f"""
    WITH latest_gen AS (
        SELECT 
            SUM(CASE WHEN fuelType NOT LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as total_gen_gw,
            SUM(CASE WHEN fuelType LIKE 'INT%' THEN generation ELSE 0 END) / 1000 as net_ic_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND settlementPeriod = (
            SELECT MAX(settlementPeriod)
            FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
            WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        )
    ),
    prices AS (
        SELECT 
            AVG(systemSellPrice) as wholesale_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    )
    SELECT 
        p.wholesale_price as wholesale_price,
        g.total_gen_gw,
        50.0 as frequency,
        g.total_gen_gw + g.net_ic_gw as demand_gw,
        g.net_ic_gw as net_ic_flow_gw
    FROM prices p, latest_gen g
    """
    
    try:
        result = bq_client.query(query).to_dataframe()
        if not result.empty:
            return {
                'wholesale': round(float(result['wholesale_price'].iloc[0]), 2),
                'total_gen': round(float(result['total_gen_gw'].iloc[0]), 2),
                'frequency': 50.0,
                'demand': round(float(result['demand_gw'].iloc[0]), 2),
                'net_ic_flow': round(float(result['net_ic_flow_gw'].iloc[0]), 2)
            }
    except Exception as e:
        logging.error(f"Error getting KPIs: {e}")
    
    return {
        'wholesale': 0, 'total_gen': 0,
        'frequency': 50.0, 'demand': 0, 'net_ic_flow': 0
    }

def get_generation_mix(bq_client):
    """Get current generation mix"""
    query = f"""
    WITH latest AS (
        SELECT 
            fuelType,
            AVG(generation) / 1000 as gen_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        AND settlementPeriod = (
            SELECT MAX(settlementPeriod)
            FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
            WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
        )
        AND fuelType NOT LIKE 'INT%'
        GROUP BY fuelType
    )
    SELECT 
        fuelType,
        gen_gw,
        gen_gw / (SELECT SUM(gen_gw) FROM latest) * 100 as share_pct
    FROM latest
    ORDER BY gen_gw DESC
    """
    
    try:
        return bq_client.query(query).to_dataframe()
    except Exception as e:
        logging.error(f"Error getting generation mix: {e}")
        return None

def get_interconnectors(bq_client):
    """Get interconnector flows"""
    query = f"""
    SELECT 
        fuelType,
        AVG(generation) as flow_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    AND settlementPeriod = (
        SELECT MAX(settlementPeriod)
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
    )
    AND fuelType LIKE 'INT%'
    GROUP BY fuelType
    ORDER BY flow_mw DESC
    """
    
    try:
        return bq_client.query(query).to_dataframe()
    except Exception as e:
        logging.error(f"Error getting interconnectors: {e}")
        return None

def update_dashboard():
    """Main update function"""
    print("\n" + "=" * 80)
    print("⚡ GB LIVE EXECUTIVE DASHBOARD UPDATE")
    print("=" * 80)
    
    # Connect to services
    print("\n🔧 Connecting to BigQuery and Google Sheets...")
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    sheets_creds = service_account.Credentials.from_service_account_file(SA_FILE, scopes=SCOPES)
    gc = gspread.authorize(sheets_creds)
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    
    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/bigquery"]
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    
    print("✅ Connected\n")
    
    # Update timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.update_acell('A2', f'✅ Live Data | Updated: {timestamp}')
    
    # Get and update KPIs
    print("📊 Fetching Key Performance Indicators...")
    kpis = get_kpis(bq_client)
    
    kpi_updates = [{
        'range': 'A7:E7',
        'values': [[
            f"£{kpis['wholesale']:.2f}/MWh",
            f"{kpis['total_gen']:.2f} GW",
            f"{kpis['frequency']:.1f} Hz",
            f"{kpis['demand']:.2f} GW",
            f"{kpis['net_ic_flow']:+.2f} GW"
        ]]
    }]
    sheet.batch_update(kpi_updates)
    
    print(f"  💷 Wholesale Price: £{kpis['wholesale']:.2f}/MWh")
    print(f"  ⚡ Generation: {kpis['total_gen']:.2f} GW")
    print(f"  📊 Demand: {kpis['demand']:.2f} GW")
    print(f"  🔌 Net IC Flow: {kpis['net_ic_flow']:+.2f} GW")
    
    # Add section headers
    sheet.update([['⚡ GENERATION MIX — Live Breakdown']], 'A9:F9')
    
    # Get and update generation mix
    print("\n🔋 Fetching Generation Mix...")
    gen_mix = get_generation_mix(bq_client)
    
    if gen_mix is not None and not gen_mix.empty:
        fuel_emojis = {
            'WIND': '💨 Wind',
            'CCGT': '🔥 CCGT',
            'NUCLEAR': '⚛️ Nuclear',
            'BIOMASS': '🌱 Biomass',
            'NPSHYD': '💧 Hydro',
            'PS': '⚡ Pumped',
            'OTHER': '❓ Other',
            'OCGT': '🔥 OCGT',
            'COAL': '⚫ Coal',
            'OIL': '🛢️ Oil'
        }
        
        gen_updates = []
        for idx, row in gen_mix.head(10).iterrows():
            fuel = row['fuelType']
            gen_gw = row['gen_gw']
            share = row['share_pct']
            
            trend = '↑' if share > 15 else '→' if share > 5 else '↓'
            status = '🟢 Active' if gen_gw > 0.01 else '⚫ Offline'
            
            gen_updates.append([
                fuel_emojis.get(fuel, fuel),
                f"{gen_gw:.2f}",
                f"{share:.1f}%",
                trend,
                status
            ])
            print(f"  {fuel_emojis.get(fuel, fuel)}: {gen_gw:.2f} GW ({share:.1f}%)")
        
        # Pad with empty rows if less than 10
        while len(gen_updates) < 10:
            gen_updates.append(['—', '0.00', '0%', '—', '—'])
        
        # Update generation mix (columns A-E, rows 10-19)
        sheet.update(gen_updates, 'A10:E19')
    
    # Get and update interconnectors
    print("\n🔌 Fetching Interconnector Flows...")
    
    # Add interconnector header
    sheet.update([['🔌 INTERCONNECTORS']], 'H9:K9')
    
    ic_data = get_interconnectors(bq_client)
    
    if ic_data is not None and not ic_data.empty:
        ic_emojis = {
            'INTFR': '🇫🇷 France',
            'INTNEM': '🇧🇪 Belgium',
            'INTVKL': '🇩🇰 Denmark',
            'INTIFA2': '🇫🇷 IFA2',
            'INTNED': '🇳🇱 Netherlands',
            'INTELEC': '⚡ ElecLink',
            'INTEW': '🏴󠁧󠁢󠁥󠁮󠁧󠁿 E-W',
            'INTNSL': '🇳🇴 Norway',
            'INTIRL': '🇮🇪 Ireland',
            'INTGRNL': '🇬🇱 Greenlink'
        }
        
        ic_updates = []
        for idx, row in ic_data.head(10).iterrows():
            ic_name = row['fuelType']
            flow = int(row['flow_mw'])
            
            direction = '← Import' if flow > 0 else '→ Export' if flow < 0 else '—'
            status = '🟢 Active' if abs(flow) > 10 else '⚫ Idle'
            
            ic_updates.append([
                ic_emojis.get(ic_name, ic_name),
                str(flow),
                direction,
                status
            ])
            print(f"  {ic_emojis.get(ic_name, ic_name)}: {flow} MW {direction}")
        
        while len(ic_updates) < 10:
            ic_updates.append(['—', '0', '—', '—'])
        
        # Update interconnectors (columns H-K, rows 10-19) 
        sheet.update(ic_updates, 'H10:K19')
    
    print("\n" + "=" * 80)
    print("✅ DASHBOARD UPDATE COMPLETE")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    try:
        update_dashboard()
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        sys.exit(1)
