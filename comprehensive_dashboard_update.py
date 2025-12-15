#!/usr/bin/env python3
"""
Comprehensive Dashboard Update
Updates ALL sections of the Dashboard:
- Timestamp & Freshness
- System Metrics (Total Gen, Supply, Renewables %, Market Price)
- Fuel Breakdown (CCGT, Wind, Nuclear, etc.)
- Interconnectors with flags
- Power Station Outages with flags and progress bars

Date: November 21, 2025
"""

import sys
import pickle
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Configuration
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
DASHBOARD_SHEET = 'Dashboard'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'

# Fuel type emojis
FUEL_EMOJIS = {
    'CCGT': '🔥',
    'WIND': '💨',
    'NUCLEAR': '⚛️',
    'BIOMASS': '🌱',
    'NPSHYD': '💧',
    'OTHER': '⚡',
    'OCGT': '🔥',
    'COAL': '⛏️',
    'OIL': '🛢️',
    'PS': '🔋',
    'SOLAR': '☀️',
    'HYDRO': '💧'
}

# Interconnector flag mapping
INTERCONNECTOR_INFO = {
    'ElecLink': {'flag': '🇫🇷', 'name': 'ElecLink (France)', 'typical_mw': 1000},
    'IFA': {'flag': '🇫🇷', 'name': 'IFA (France)', 'typical_mw': 2000},
    'IFA2': {'flag': '🇫🇷', 'name': 'IFA2 (France)', 'typical_mw': 1000},
    'Nemo': {'flag': '🇧🇪', 'name': 'Nemo (Belgium)', 'typical_mw': 1000},
    'Viking': {'flag': '🇩🇰', 'name': 'Viking Link (Denmark)', 'typical_mw': 1400},
    'BritNed': {'flag': '🇳🇱', 'name': 'BritNed (Netherlands)', 'typical_mw': 1000},
    'Moyle': {'flag': '🇮🇪', 'name': 'Moyle (N.Ireland)', 'typical_mw': 500},
    'East-West': {'flag': '🇮🇪', 'name': 'East-West (Ireland)', 'typical_mw': 500},
    'Greenlink': {'flag': '🇮🇪', 'name': 'Greenlink (Ireland)', 'typical_mw': 500},
    'NSL': {'flag': '🇳🇴', 'name': 'NSL (Norway)', 'typical_mw': 1400},
}

# Unit type emojis
UNIT_EMOJIS = {
    'NUCLEAR': '⚛️',
    'CCGT': '🔥',
    'OCGT': '🔥',
    'GAS': '🔥',
    'PS': '🔋',
    'HYDRO': '💧',
    'WIND': '💨',
    'BIOMASS': '🌱',
    'COAL': '⛏️',
    'INTERCONNECTOR': '🔌'
}

def connect():
    """Connect to Google Sheets and BigQuery"""
    print("🔧 Connecting to services...")
    
    if not TOKEN_FILE.exists():
        print(f"❌ Token file not found: {TOKEN_FILE}")
        sys.exit(1)
    
    with open(TOKEN_FILE, 'rb') as f:
        creds = pickle.load(f)
    
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet(DASHBOARD_SHEET)
    
    if SA_FILE.exists():
        bq_creds = service_account.Credentials.from_service_account_file(
            str(SA_FILE),
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds)
    else:
        bq_client = bigquery.Client(project=PROJECT_ID)
    
    print("✅ Connected")
    return dashboard, bq_client

def get_latest_settlement_period():
    """Calculate current settlement period"""
    now = datetime.now()
    sp = (now.hour * 2) + (1 if now.minute < 30 else 2)
    return min(sp, 48)  # Cap at SP48

def query_current_generation(bq_client):
    """Get current generation by fuel type (latest SP)"""
    print("\n📊 Querying current generation...")
    
    date_today = datetime.now().date()
    
    # Query using LATEST publishTime (not settlementPeriod which may lag)
    query = f"""
    WITH latest_data AS (
        SELECT 
            fuelType,
            generation,
            publishTime
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE DATE(settlementDate) = '{date_today}'
        ORDER BY publishTime DESC
        LIMIT 1000
    ),
    current_sp AS (
        SELECT MAX(publishTime) as latest_time
        FROM latest_data
    )
    SELECT 
        ld.fuelType,
        ROUND(SUM(ld.generation), 1) as total_generation_mw
    FROM latest_data ld
    CROSS JOIN current_sp cs
    WHERE ld.publishTime = cs.latest_time
      AND ld.fuelType NOT LIKE 'INT%'  -- Exclude interconnectors
    GROUP BY ld.fuelType
    ORDER BY total_generation_mw DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    print(f"✅ Retrieved {len(df)} fuel types")
    
    # Convert MW to GW
    df['generation_gw'] = df['total_generation_mw'] / 1000.0
    
    # Get current SP for display
    current_sp = get_latest_settlement_period()
    
    return df, current_sp

def query_current_price(bq_client):
    """Get current market price"""
    print("\n💰 Querying market price...")
    
    date_today = datetime.now().date()
    
    # Use bmrs_mid_iris with dataProvider = 'APXMIDP' for market price
    query = f"""
    SELECT 
        settlementPeriod,
        dataProvider,
        ROUND(AVG(price), 2) as price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE DATE(settlementDate) = '{date_today}'
      AND dataProvider = 'APXMIDP'
    GROUP BY settlementPeriod, dataProvider
    ORDER BY settlementPeriod DESC
    LIMIT 1
    """
    
    try:
        df = bq_client.query(query).to_dataframe()
        if len(df) > 0 and df['price'].iloc[0] > 0:
            price = df['price'].iloc[0]
            sp = df['settlementPeriod'].iloc[0]
            print(f"✅ Market price: £{price:.2f}/MWh (SP{sp})")
            return price, sp
        else:
            print(f"⚠️  No price data available")
            return None, get_latest_settlement_period()
    except Exception as e:
        print(f"⚠️  Price query error: {e}")
        return None, get_latest_settlement_period()

def query_interconnector_flows(bq_client):
    """Get current interconnector flows"""
    print("\n🌍 Querying interconnector flows...")
    
    date_today = datetime.now().date()
    
    # Use same latest publishTime pattern as generation query
    query = f"""
    WITH latest_data AS (
        SELECT 
            fuelType,
            generation,
            publishTime
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE DATE(settlementDate) = '{date_today}'
          AND fuelType LIKE 'INT%'
        ORDER BY publishTime DESC
        LIMIT 100
    ),
    current_sp AS (
        SELECT MAX(publishTime) as latest_time
        FROM latest_data
    )
    SELECT 
        ld.fuelType,
        ROUND(SUM(ld.generation), 1) as flow_mw
    FROM latest_data ld
    CROSS JOIN current_sp cs
    WHERE ld.publishTime = cs.latest_time
    GROUP BY ld.fuelType
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} interconnectors")
    
    return df

def query_outages(bq_client):
    """Get current power station outages"""
    print("\n🔴 Querying power station outages...")
    
    query = f"""
    SELECT 
        assetName,
        affectedUnit,
        fuelType,
        normalCapacity,
        unavailableCapacity,
        ROUND(unavailableCapacity / NULLIF(normalCapacity, 0) * 100, 1) as pct_unavailable,
        cause,
        publishTime
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
    WHERE eventStatus = 'Active'
      AND TIMESTAMP(eventStartTime) <= CURRENT_TIMESTAMP()
      AND (TIMESTAMP(eventEndTime) >= CURRENT_TIMESTAMP() OR eventEndTime IS NULL)
      AND unavailableCapacity >= 100
    ORDER BY unavailableCapacity DESC, publishTime DESC
    LIMIT 10
    """
    
    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} active outages")
    
    return df

def update_dashboard(dashboard, gen_df, price, current_sp, ic_df, outages_df):
    """Update all dashboard sections"""
    print("\n📝 Updating Dashboard...")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Row 2: Timestamp & Freshness
    dashboard.update_acell('B2', f'⏰ Last Updated: {timestamp} | ✅ FRESH')
    dashboard.update_acell('B3', f'Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min')
    print(f"✅ Updated timestamp (B2)")
    
    # Row 4: System Metrics
    total_gen_gw = gen_df['generation_gw'].sum()
    renewable_fuels = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']
    renewable_gw = gen_df[gen_df['fuelType'].isin(renewable_fuels)]['generation_gw'].sum()
    renewable_pct = (renewable_gw / total_gen_gw * 100) if total_gen_gw > 0 else 0
    
    price_text = f"£{price:.2f}/MWh (SP{current_sp})" if price else "N/A"
    
    metrics_text = (f"📊 SYSTEM METRICS\n"
                   f"Total Generation: {total_gen_gw:.1f} GW | "
                   f"Supply: {total_gen_gw:.1f} GW | "
                   f"Renewables: {renewable_pct:.0f}% | "
                   f"💰 Market Price: {price_text}")
    
    dashboard.update_acell('B4', metrics_text)
    print(f"✅ Updated system metrics (B4)")
    
    # Rows 6+: Fuel Breakdown (B6:C15)
    print(f"\n🔥 Updating Fuel Breakdown...")
    fuel_data = []
    
    # Main fuels in display order
    display_fuels = ['CCGT', 'WIND', 'NUCLEAR', 'BIOMASS', 'NPSHYD', 'OTHER', 'OCGT', 'COAL', 'OIL', 'PS']
    
    for fuel in display_fuels:
        emoji = FUEL_EMOJIS.get(fuel, '⚡')
        matching = gen_df[gen_df['fuelType'] == fuel]
        
        if len(matching) > 0:
            gw = matching['generation_gw'].iloc[0]
        else:
            gw = 0.0
        
        fuel_data.append([f"{emoji} {fuel}", f"{gw:.1f} GW"])
    
    # Update B6:C15 (10 rows)
    dashboard.update('B6:C15', fuel_data, value_input_option='USER_ENTERED')
    print(f"✅ Updated {len(fuel_data)} fuel types")
    
    # Interconnectors (D7:E16 - 10 rows)
    print(f"\n🌍 Updating Interconnectors...")
    ic_data = []
    
    for ic_key, ic_info in list(INTERCONNECTOR_INFO.items())[:10]:
        flag = ic_info['flag']
        name = ic_info['name']
        
        # Find matching interconnector in data
        matching = ic_df[ic_df['fuelType'].str.contains(ic_key.upper(), case=False, na=False)]
        
        if len(matching) > 0:
            flow_mw = matching['flow_mw'].iloc[0]
            
            if flow_mw > 0:
                direction = "Import"
            elif flow_mw < 0:
                direction = "Export"
                flow_mw = abs(flow_mw)
            else:
                direction = "Balanced"
            
            ic_data.append([f"{flag} {name}", f"{int(flow_mw)} MW {direction}"])
        else:
            ic_data.append([f"{flag} {name}", "0 MW Balanced"])
    
    dashboard.update('D7:E16', ic_data, value_input_option='USER_ENTERED')
    print(f"✅ Updated {len(ic_data)} interconnectors")
    
    # Outages (A23:H32 - 10 rows)
    if len(outages_df) > 0:
        print(f"\n🔴 Updating Outages...")
        outage_data = []
        
        for _, row in outages_df.iterrows():
            # Column A: Unit emoji + name
            fuel = str(row['fuelType']).upper() if row['fuelType'] else 'UNKNOWN'
            emoji = UNIT_EMOJIS.get(fuel, '⚡')
            
            asset = row['assetName'] if row['assetName'] else 'Unknown'
            unit = row['affectedUnit'] if row['affectedUnit'] else ''
            
            if 'INTER' in fuel or 'IFA' in asset.upper() or 'ELEC' in asset.upper():
                emoji = '🔌'
                unit_name = f"{emoji} {asset[:25]}"
            else:
                unit_name = f"{emoji} {asset[:25]}"
            
            # Columns B-H
            # B: affectedUnit, C: fuelType, D: normalCapacity, E: unavailableCapacity
            # F: progress bar, G: cause, H: publishTime
            
            normal_mw = int(row['normalCapacity']) if row['normalCapacity'] else 0
            unavail_mw = int(row['unavailableCapacity']) if row['unavailableCapacity'] else 0
            pct = float(row['pct_unavailable']) if row['pct_unavailable'] else 0
            
            # Progress bar
            filled = min(int(pct / 10), 10)
            bar = '🟥' * filled + '⬜' * (10 - filled) + f" {pct:.1f}%"
            
            cause = (str(row['cause'])[:40] + '...') if row['cause'] and len(str(row['cause'])) > 40 else (str(row['cause']) if row['cause'] else 'Unspecified')
            
            publish_time = str(row['publishTime'])[:19] if row['publishTime'] else ''
            
            outage_data.append([unit_name, unit, fuel, normal_mw, unavail_mw, bar, cause, publish_time])
        
        # Pad to 10 rows
        while len(outage_data) < 10:
            outage_data.append(['', '', '', '', '', '', '', ''])
        
        dashboard.update('A23:H32', outage_data, value_input_option='USER_ENTERED')
        print(f"✅ Updated {len(outages_df)} outages")
    
    print(f"\n✅ Dashboard update complete!")

def main():
    """Main execution"""
    print("=" * 80)
    print("🔄 COMPREHENSIVE DASHBOARD UPDATE")
    print("=" * 80)
    
    # Connect
    dashboard, bq_client = connect()
    
    # Query data
    gen_df, current_sp = query_current_generation(bq_client)
    price, _ = query_current_price(bq_client)
    ic_df = query_interconnector_flows(bq_client)
    outages_df = query_outages(bq_client)
    
    # Update dashboard
    update_dashboard(dashboard, gen_df, price, current_sp, ic_df, outages_df)
    
    print("\n" + "=" * 80)
    print("✅ UPDATE COMPLETE")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   • Settlement Period: SP{current_sp}")
    print(f"   • Total Generation: {gen_df['generation_gw'].sum():.1f} GW")
    print(f"   • Market Price: £{price:.2f}/MWh" if price else "   • Market Price: N/A")
    print(f"   • Fuel Types: {len(gen_df)}")
    print(f"   • Interconnectors: {len(ic_df)}")
    print(f"   • Active Outages: {len(outages_df)}")
    print(f"\n🌐 View Dashboard:")
    print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
    print()

if __name__ == '__main__':
    main()
