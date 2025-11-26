#!/usr/bin/env python3
"""
Dashboard V2 Auto-Updater - Matches YOUR design layout exactly
Generation: A9:B18 | Interconnectors: C9:D18 | Outages: A30+
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'dashboard_v2_updater.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Manual asset name mappings for units not in bmu_registration_data
MANUAL_ASSET_NAMES = {
    'T_PEHE-1': 'Peterhead Power Station',
    'T_KEAD-1': 'Keadby Power Station Unit 1',
    'T_KEAD-2': 'Keadby Power Station Unit 2',
    'I_IEG-IFA2': 'IFA2 Interconnector (Export)',
    'I_IED-IFA2': 'IFA2 Interconnector (Import)',
    'I_IEG-VKL1': 'Viking Link Interconnector (Export)',
    'I_IED-VKL1': 'Viking Link Interconnector (Import)',
    'RYHPS-1': 'Rye House Power Station'
}
SA_FILE = Path(__file__).parent.parent / 'inner-cinema-credentials.json'

def main():
    logging.info("=" * 80)
    logging.info("🔄 DASHBOARD V2 UPDATE (YOUR DESIGN)")
    logging.info("=" * 80)
    
    # Connect
    logging.info("🔧 Connecting...")
    SCOPES_SHEETS = ['https://www.googleapis.com/auth/spreadsheets']
    SCOPES_BQ = ["https://www.googleapis.com/auth/bigquery"]
    
    sheets_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES_SHEETS
    )
    bq_creds = service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES_BQ
    )
    
    gc = gspread.authorize(sheets_creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    dashboard = spreadsheet.worksheet('Dashboard')
    
    logging.info("✅ Connected")
    
    today = datetime.now().date()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # =======================================================================
    # 1. UPDATE HEADER SECTION (Rows 2, 5, 6)
    # =======================================================================
    logging.info("📋 Updating header...")
    
    # Row 2: Timestamp
    dashboard.update([[f'⏰ Last Updated: {timestamp} | ✅ Auto-refresh enabled']], 'A2')
    
    # Get latest price, demand, generation, frequency
    price_query = f"""
    SELECT price, demand
    FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
    WHERE settlementDate = '{today}'
      AND dataProvider = 'APXMIDP'
    ORDER BY settlementPeriod DESC
    LIMIT 1
    """
    
    try:
        price_df = bq_client.query(price_query).to_dataframe()
        if not price_df.empty:
            current_price = price_df.iloc[0]['price']
            current_demand = price_df.iloc[0]['demand'] / 1000  # Convert to GW
        else:
            current_price = 0
            current_demand = 0
    except:
        current_price = 0
        current_demand = 0
    
    # Get total generation
    gen_query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
    )
    SELECT SUM(generation) as total_gen
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
      AND settlementPeriod = (SELECT max_sp FROM latest_period)
    """
    
    try:
        total_df = bq_client.query(gen_query).to_dataframe()
        total_gen = total_df.iloc[0]['total_gen'] / 1000 if not total_df.empty else 0
    except:
        total_gen = 0
    
    # Get frequency
    freq_query = f"""
    SELECT frequency
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
    ORDER BY measurementTime DESC
    LIMIT 1
    """
    
    try:
        freq_df = bq_client.query(freq_query).to_dataframe()
        frequency = freq_df.iloc[0]['frequency'] if not freq_df.empty else 50.00
    except:
        frequency = 50.00
    
    # Row 6: Current metrics (will update wind% after getting gen breakdown)
    current_row = [[
        '📊 Current:',
        f'Demand: {current_demand:.2f} GW',
        f'Generation: {total_gen:.2f} GW',
        'Wind: 0%',  # Placeholder
        f'Price: £{current_price:.2f}/MWh',
        f'Frequency: {frequency:.2f} Hz',
        'Constraint: 0 MW'
    ]]
    dashboard.update(current_row, 'A6')
    
    logging.info("   ✅ Header updated")
    
    # =======================================================================
    # 2. UPDATE GENERATION (A9:B18) & INTERCONNECTORS (C9:D18)
    # =======================================================================
    logging.info("⚡ Updating generation...")
    
    # Get latest period generation by fuel
    gen_fuel_query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
    )
    SELECT 
        fuelType,
        ROUND(SUM(generation), 1) as total_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
      AND settlementPeriod = (SELECT max_sp FROM latest_period)
    GROUP BY fuelType
    ORDER BY total_mw DESC
    """
    
    gen_df = bq_client.query(gen_fuel_query).to_dataframe()
    
    if not gen_df.empty:
        # Emoji mapping
        fuel_emoji = {
            'CCGT': '🔥', 'WIND': '💨', 'NUCLEAR': '⚛️', 'BIOMASS': '🌱',
            'NPSHYD': '💧', 'PS': '🔋', 'OCGT': '🔥', 'OIL': '🛢️',
            'COAL': '⛏️', 'OTHER': '⚡', 'SOLAR': '☀️'
        }
        
        # Prepare generation data (A9:B18) - 10 rows
        gen_data = []
        wind_mw = 0
        total_mw = 0
        
        for _, row in gen_df.head(10).iterrows():
            fuel = row['fuelType']
            mw = row['total_mw']
            gw = mw / 1000
            
            # Track wind and total for percentage
            if fuel.upper() == 'WIND':
                wind_mw = mw
            if not fuel.upper().startswith('INT'):
                total_mw += mw
            
            emoji = fuel_emoji.get(fuel.upper(), '⚡')
            
            # Generation uses GW, interconnectors use MW
            if fuel.upper().startswith('INT'):
                value_str = f'{mw:,.1f} MW'
            else:
                value_str = f'{gw:.1f} GW'
            
            gen_data.append([f'{emoji} {fuel}', value_str])
        
        # Pad to 10 rows if needed
        while len(gen_data) < 10:
            gen_data.append(['', ''])
        
        # Update generation section
        dashboard.update(gen_data, 'A9')
        
        # Update wind percentage in row 6
        wind_pct = (wind_mw / total_mw * 100) if total_mw > 0 else 0
        dashboard.update([[f'Wind: {wind_pct:.0f}%']], 'D6')
        
        logging.info(f"   ✅ Updated generation (Wind: {wind_pct:.0f}%)")
    
    # =======================================================================
    # 3. UPDATE INTERCONNECTORS (C9:D18)
    # =======================================================================
    logging.info("🌍 Updating interconnectors...")
    
    # Get latest interconnector flows
    ic_query = f"""
    WITH latest_period AS (
        SELECT MAX(settlementPeriod) as max_sp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
        WHERE CAST(settlementDate AS DATE) = '{today}'
    )
    SELECT 
        fuelType,
        ROUND(SUM(generation), 0) as flow_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
      AND settlementPeriod = (SELECT max_sp FROM latest_period)
      AND fuelType LIKE 'INT%'
    GROUP BY fuelType
    ORDER BY ABS(flow_mw) DESC
    """
    
    ic_df = bq_client.query(ic_query).to_dataframe()
    
    if not ic_df.empty:
        # IC name mapping
        ic_names = {
            'INTFR': '🇫🇷 IFA (France)',
            'INTIRL': '🇮🇪 East-West (Ireland)',
            'INTNED': '🇳🇱 BritNed (Netherlands)',
            'INTEW': '🇮🇪 Greenlink (Ireland)',
            'INTELEC': '🇫🇷 ElecLink (France)',
            'INTIFA2': '🇫🇷 IFA2 (France)',
            'INTNEM': '🇧🇪 Nemo (Belgium)',
            'INTNSL': '🇳🇴 NSL (Norway)',
            'INTMOYLE': 'Moyle (N.Ireland)',
            'INTVIK': '🇩🇰 Viking Link (Denmark)'
        }
        
        ic_data = []
        for _, row in ic_df.head(10).iterrows():
            fuel = row['fuelType']
            flow = row['flow_mw']
            
            name = ic_names.get(fuel.upper(), fuel)
            
            if flow > 0:
                direction = 'Import'
            elif flow < 0:
                direction = 'Export'
                flow = abs(flow)
            else:
                direction = 'Balanced'
            
            ic_data.append([name, f'{flow:,.0f} MW {direction}'])
        
        # Pad to 10 rows
        while len(ic_data) < 10:
            ic_data.append(['', ''])
        
        # Update interconnectors section
        dashboard.update(ic_data, 'C9')
        logging.info(f"   ✅ Updated {len(ic_df)} interconnectors")
    
    # =======================================================================
    # 4. UPDATE OUTAGES (A22+ with header at A21)
    # =======================================================================
    logging.info("⚠️  Updating outages...")
    
    # Update header row first
    dashboard.update([['Asset Name', 'BM Unit', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', 'Visual', 'Cause', 'Start Time']], 'A21')
    
    outages_query = f"""
    WITH latest_outages AS (
        SELECT 
            affectedUnit,
            assetName,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            cause,
            eventStartTime,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventStartTime) as start_time,
            ROW_NUMBER() OVER (PARTITION BY affectedUnit ORDER BY revisionNumber DESC) as rn
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE eventStatus = 'Active'
          AND unavailableCapacity >= 50
    )
    SELECT 
        lo.affectedUnit,
        COALESCE(bmu.bmunitname, lo.assetName, lo.affectedUnit) as assetName,
        lo.fuelType,
        lo.normalCapacity,
        lo.unavailableCapacity,
        lo.cause,
        lo.start_time
    FROM latest_outages lo
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON lo.affectedUnit = bmu.nationalgridbmunit
    WHERE lo.rn = 1
    ORDER BY lo.unavailableCapacity DESC
    LIMIT 50
    """
    
    try:
        outages_df = bq_client.query(outages_query).to_dataframe()
        
        if not outages_df.empty:
            # Fuel type emojis
            fuel_emoji_out = {
                'NUCLEAR': '⚛️', 'CCGT': '🔥', 'WIND OFFSHORE': '💨',
                'WIND ONSHORE': '💨', 'HYDRO PUMPED STORAGE': '⚡',
                'BIOMASS': '🌱', 'COAL': '⛏️', 'FOSSIL GAS': '🔥'
            }
            
            outages_data = []
            
            for _, row in outages_df.head(12).iterrows():
                fuel = row['fuelType'] or 'Unknown'
                emoji = fuel_emoji_out.get(fuel.upper(), '🔥')
                mw = row['unavailableCapacity']
                bmu_id = row['affectedUnit']
                
                # Get asset name: use manual mapping first, then database, then BMU ID
                asset_name = MANUAL_ASSET_NAMES.get(bmu_id) or row['assetName'] or bmu_id
                
                pct = (mw / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
                
                # Visual progress bar (10 blocks)
                filled = int(pct / 10)
                bar = '🟥' * filled + '⬜' * (10 - filled) + f' {pct:.1f}%'
                
                outages_data.append([
                    f"{emoji} {asset_name}",
                    bmu_id,
                    fuel,
                    f"{row['normalCapacity']:,.0f}",
                    f"{mw:,.0f}",
                    bar,
                    row['cause'] or 'Unknown',
                    row['start_time']
                ])
            
            # Add section title
            dashboard.update([['LIVE OUTAGES (Top 12)']], 'A20')
            
            # Add header row
            outages_header = [['Asset Name', 'BM Unit', 'Fuel Type', 'Normal (MW)', 'Unavail (MW)', 'Visual', 'Cause', 'Start Time']]
            dashboard.update(outages_header, 'A21')
            
            # Update outages section (starting at row 22)
            dashboard.update(outages_data, 'A22')
            
            # Calculate total
            total_mw = outages_df['unavailableCapacity'].sum()
            total_count = len(outages_df)
            
            # Update total row (row 34)
            dashboard.update([[f'TOTAL UNAVAILABLE CAPACITY: {total_mw:,.0f} MW', '', f'({total_count} outages)']], 'A34')
            
            logging.info(f"   ✅ Updated {len(outages_data)} outages (Total: {total_mw:,.0f} MW, {total_count} active)")
    except Exception as e:
        logging.warning(f"   ⚠️  Outages update failed: {e}")
    
    # =======================================================================
    # FINAL
    # =======================================================================
    logging.info("=" * 80)
    logging.info("✅ DASHBOARD V2 UPDATE COMPLETE")
    logging.info("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
