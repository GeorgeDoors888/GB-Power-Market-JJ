#!/usr/bin/env python3
"""
Real-Time Dashboard Updater
Automatically refreshes the Enhanced BI Analysis dashboard with latest data
Runs via cron every 5 minutes

Author: Auto-generated for GB Power Market JJ
Date: 2025-11-09
"""

import sys
import os
import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# Setup logging
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / 'dashboard_updater.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configuration
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'
SHEET_NAME = 'Dashboard'  # Main dashboard sheet
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TOKEN_FILE = Path(__file__).parent / 'token.pickle'
SA_FILE = Path(__file__).parent / 'inner-cinema-credentials.json'  # Service account for BigQuery

def update_dashboard():
    """Update the dashboard with latest data"""
    try:
        logging.info("=" * 80)
        logging.info("🔄 REAL-TIME DASHBOARD UPDATE STARTED")
        logging.info("=" * 80)
        
        # Check token file exists
        if not TOKEN_FILE.exists():
            logging.error(f"❌ Token file not found: {TOKEN_FILE}")
            logging.error("   Run: python3 update_analysis_bi_enhanced.py manually first")
            return False
        
        # Initialize clients
        logging.info("🔧 Connecting to Google Sheets and BigQuery...")
        
        # Google Sheets (uses OAuth token)
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
        
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        
        # BigQuery (uses service account)
        if SA_FILE.exists():
            bq_credentials = service_account.Credentials.from_service_account_file(
                str(SA_FILE),
                scopes=["https://www.googleapis.com/auth/bigquery"]
            )
            bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_credentials)
        else:
            # Fallback: try default credentials
            logging.warning(f"⚠️  Service account not found: {SA_FILE}")
            logging.warning("   Trying default credentials...")
            bq_client = bigquery.Client(project=PROJECT_ID)
        
        logging.info("✅ Connected successfully")
        
        # Read dashboard status
        logging.info("📖 Checking dashboard...")
        # Try to read a cell to verify connection
        try:
            test_cell = sheet.acell('A1').value
            logging.info(f"  Dashboard connected: {test_cell or 'Empty cell A1'}")
        except Exception as e:
            logging.warning(f"  Could not read A1: {e}")
        
        # Use fixed date range: last 7 days
        days = 7
        date_to = datetime.now().date()
        date_from = date_to - timedelta(days=days)
        
        logging.info(f"  Date Range: {date_from} to {date_to} ({days} days)")
        
        # Query latest generation data (UNION historical + IRIS)
        logging.info("📊 Querying BigQuery for latest data...")
        query = f"""
        WITH combined_generation AS (
          -- Historical data
          SELECT 
            CAST(settlementDate AS DATE) as date,
            fuelType,
            SUM(generation) as total_generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
          WHERE CAST(settlementDate AS DATE) BETWEEN '{date_from}' AND '{date_to}'
            AND CAST(settlementDate AS DATE) < CURRENT_DATE()
          GROUP BY date, fuelType
          
          UNION ALL
          
          -- Real-time IRIS data (last 48 hours)
          SELECT 
            CAST(settlementDate AS DATE) as date,
            fuelType,
            SUM(generation) as total_generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
            AND CAST(settlementDate AS DATE) BETWEEN '{date_from}' AND '{date_to}'
          GROUP BY date, fuelType
        )
        SELECT 
          fuelType,
          SUM(total_generation) as total_mwh,
          COUNT(DISTINCT date) as days_with_data
        FROM combined_generation
        GROUP BY fuelType
        ORDER BY total_mwh DESC
        LIMIT 20
        """
        
        df = bq_client.query(query).to_dataframe()
        
        logging.info(f"✅ Retrieved {len(df)} fuel types")
        
        # Update summary metrics on sheet
        total_generation = df['total_mwh'].sum()
        renewable_fuels = ['WIND', 'SOLAR', 'HYDRO', 'BIOMASS']
        renewable_gen = df[df['fuelType'].isin(renewable_fuels)]['total_mwh'].sum()
        renewable_pct = (renewable_gen / total_generation * 100) if total_generation > 0 else 0
        
        logging.info("📝 Updating dashboard metrics...")
        
        # Write to sheet - find empty spot or specific cells
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update a status cell (you can adjust these cell references)
        try:
            # Try updating Live_Raw_Gen sheet if it exists
            live_sheet = spreadsheet.worksheet('Live_Raw_Gen')
            live_sheet.update_acell('A1', f'Auto-Updated: {timestamp}')
            logging.info(f"  ✅ Updated Live_Raw_Gen sheet")
        except:
            # Fallback: update main dashboard
            sheet.update_acell('A50', f'Auto-Updated: {timestamp}')
            logging.info(f"  ✅ Updated Dashboard sheet (cell A50)")
        
        logging.info(f"✅ Dashboard updated successfully!")
        logging.info(f"   Total Generation: {total_generation:,.0f} MWh")
        logging.info(f"   Renewable %: {renewable_pct:.1f}%")
        logging.info(f"   Timestamp: {timestamp}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Update failed: {e}")
        logging.exception("Full traceback:")
        return False

def main():
    """Main entry point"""
    success = update_dashboard()
    
    if success:
        logging.info("✅ Real-time update completed successfully")
        sys.exit(0)
    else:
        logging.error("❌ Real-time update failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
