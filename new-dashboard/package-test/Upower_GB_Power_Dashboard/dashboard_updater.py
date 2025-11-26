#!/usr/bin/env python3
"""
Upower GB Energy Dashboard - Auto-Updater
Syncs data from BigQuery to Google Sheets
"""

import sys
import logging
from datetime import datetime
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
import pandas as pd

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration - UPDATE THESE
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = 'your-service-account-credentials.json'

def main():
    logging.info("=" * 80)
    logging.info("🔄 UPOWER DASHBOARD AUTO-UPDATE")
    logging.info("=" * 80)
    
    # Connect to services
    logging.info("🔧 Connecting to Google Sheets and BigQuery...")
    
    sheets_creds = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    bq_creds = service_account.Credentials.from_service_account_file(
        SA_FILE,
        scopes=['https://www.googleapis.com/auth/bigquery']
    )
    
    gc = gspread.authorize(sheets_creds)
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location="US")
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    
    logging.info("✅ Connected successfully")
    
    today = datetime.now().date()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update Dashboard
    dashboard = spreadsheet.worksheet('Dashboard')
    dashboard.update([[f'⏰ Last Updated: {timestamp}']], 'A2')
    
    # Query generation data
    logging.info("📊 Querying generation data...")
    
    gen_query = f"""
    SELECT 
        fuelType,
        ROUND(SUM(generation)/1000, 2) as total_gw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE CAST(settlementDate AS DATE) = '{today}'
    GROUP BY fuelType
    ORDER BY total_gw DESC
    LIMIT 20
    """
    
    gen_df = bq_client.query(gen_query).to_dataframe()
    
    if not gen_df.empty:
        # Emoji mapping
        fuel_emoji = {
            'NUCLEAR': '⚛️', 'CCGT': '🔥', 'WIND': '💨', 
            'SOLAR': '☀️', 'HYDRO': '💧', 'BIOMASS': '🌱'
        }
        
        gen_data = []
        for _, row in gen_df.iterrows():
            fuel = row['fuelType']
            emoji = fuel_emoji.get(fuel.upper(), '⚡')
            gen_data.append([f"{emoji} {fuel}", f"{row['total_gw']:.1f} GW"])
        
        dashboard.update(gen_data, 'A10')
        logging.info(f"✅ Updated {len(gen_data)} fuel types")
    
    logging.info("=" * 80)
    logging.info("✅ UPDATE COMPLETE")
    logging.info("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        logging.exception("Traceback:")
        sys.exit(1)
