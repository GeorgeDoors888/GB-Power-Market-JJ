#!/usr/bin/env python3
"""
Live Outages Sheet Auto-Updater
Refreshes all active outages from BigQuery
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_formatting import *

# Configuration
SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Manual asset name mappings
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

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'live_outages_updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    logging.info("=" * 80)
    logging.info("🔄 LIVE OUTAGES REFRESH")
    logging.info("=" * 80)
    
    # Connect to Google Sheets
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    logging.info("✅ Connected to Google Sheets")
    
    # Connect to BigQuery
    bq_creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json'
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location='US')
    
    logging.info("✅ Connected to BigQuery")
    
    # Update timestamp
    sheet.update([[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']], 'A2')
    
    # Fetch all outages
    logging.info("📊 Fetching all outages...")
    
    query = f"""
    WITH latest_outages AS (
        SELECT 
            affectedUnit,
            assetName,
            fuelType,
            normalCapacity,
            unavailableCapacity,
            cause,
            eventStartTime,
            eventEndTime,
            eventStatus,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventStartTime) as start_time,
            FORMAT_TIMESTAMP('%Y-%m-%d %H:%M', eventEndTime) as end_time,
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
        lo.start_time,
        lo.end_time,
        lo.eventStatus
    FROM latest_outages lo
    LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_registration_data` bmu
        ON lo.affectedUnit = bmu.nationalgridbmunit
    WHERE lo.rn = 1
    ORDER BY lo.unavailableCapacity DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    if df.empty:
        logging.warning("⚠️ No outages data found")
        return False
    
    logging.info(f"✅ Retrieved {len(df)} outages")
    
    # Update summary stats
    total_outages = len(df)
    total_mw = df['unavailableCapacity'].sum()
    avg_mw = df['unavailableCapacity'].mean()
    
    sheet.update([[total_outages]], 'K6')
    sheet.update([[f'{total_mw:,.0f}']], 'K7')
    sheet.update([[f'{avg_mw:,.0f}']], 'K8')
    
    logging.info(f"   Total: {total_mw:,.0f} MW ({total_outages} outages)")
    
    # Build outages data
    fuel_emoji = {
        'NUCLEAR': '⚛️', 'CCGT': '🔥', 'WIND OFFSHORE': '💨',
        'WIND ONSHORE': '💨', 'HYDRO PUMPED STORAGE': '⚡',
        'BIOMASS': '🌱', 'COAL': '⛏️', 'FOSSIL GAS': '🔥'
    }
    
    data_rows = []
    for _, row in df.iterrows():
        bmu_id = row['affectedUnit']
        asset_name = MANUAL_ASSET_NAMES.get(bmu_id) or row['assetName'] or bmu_id
        fuel = row['fuelType'] or 'Unknown'
        emoji = fuel_emoji.get(fuel.upper(), '🔥')
        mw = row['unavailableCapacity']
        
        pct = (mw / row['normalCapacity'] * 100) if row['normalCapacity'] > 0 else 0
        filled = int(pct / 10)
        bar = '🟥' * filled + '⬜' * (10 - filled) + f' {pct:.1f}%'
        
        data_rows.append([
            f"{emoji} {asset_name}",
            bmu_id,
            fuel,
            f"{row['normalCapacity']:,.0f}",
            f"{mw:,.0f}",
            bar,
            row['cause'] or 'Unknown',
            row['start_time'] or 'N/A',
            row['end_time'] or 'Ongoing',
            row['eventStatus']
        ])
    
    # Clear old data (rows 11+)
    last_row = sheet.row_count
    if last_row > 11:
        sheet.batch_clear(['A11:J' + str(last_row)])
    
    # Update new data
    if data_rows:
        sheet.update(data_rows, 'A11')
        logging.info(f"✅ Updated {len(data_rows)} outage records")
    
    logging.info("=" * 80)
    logging.info("✅ LIVE OUTAGES REFRESH COMPLETE")
    logging.info("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
