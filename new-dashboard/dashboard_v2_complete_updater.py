#!/usr/bin/env python3
"""
Dashboard V2 Complete Updater
Queries BigQuery and populates all dashboard sections using Google Sheets API
Based on update_analysis_bi_enhanced.py and realtime_dashboard_updater.py patterns

Author: Dashboard V2 System
Date: 2025-11-25
"""

import sys
import logging
from datetime import datetime, timedelta
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
SHEET_NAME = 'Dashboard'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
SA_FILE = Path(__file__).parent.parent / 'inner-cinema-credentials.json'

def update_dashboard_complete():
    """Complete dashboard update with all sections"""
    try:
        logging.info("=" * 80)
        logging.info("🔄 DASHBOARD V2 COMPLETE UPDATE")
        logging.info("=" * 80)
        
        # Initialize clients
        logging.info("🔧 Connecting to Google Sheets and BigQuery...")
        
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        sheets_creds = service_account.Credentials.from_service_account_file(
            str(SA_FILE),
            scopes=SCOPES
        )
        gc = gspread.authorize(sheets_creds)
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)
        
        bq_credentials = service_account.Credentials.from_service_account_file(
            str(SA_FILE),
            scopes=["https://www.googleapis.com/auth/bigquery"]
        )
        bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_credentials)
        
        logging.info("✅ Connected successfully")
        
        # Date range: Today only
        date_today = datetime.now().date()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logging.info(f"📅 Date: {date_today}")
        logging.info(f"⏰ Timestamp: {timestamp}")
        
        # ========================================================================
        # SECTION 1: HEADER & TIMESTAMP (Rows 1-3)
        # ========================================================================
        logging.info("📝 Section 1: Header & Timestamp...")
        sheet.update([[f'⏰ Last Updated: {timestamp} | ✅ Auto-refresh enabled']], 'A2')
        
        # ========================================================================
        # SECTION 2: GENERATION BY FUEL TYPE (Rows 10-40)
        # ========================================================================
        logging.info("📊 Section 2: Generation by Fuel Type...")
        
        gen_query = f"""
        WITH combined_generation AS (
          SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation as total_generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
          WHERE CAST(settlementDate AS DATE) = '{date_today}'
          
          UNION ALL
          
          SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod,
            fuelType,
            generation as total_generation
          FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
          WHERE CAST(settlementDate AS DATE) = '{date_today}'
        )
        SELECT 
          fuelType,
          ROUND(SUM(total_generation), 2) as total_mwh,
          ROUND(AVG(total_generation), 2) as avg_mw,
          ROUND(MAX(total_generation), 2) as max_mw,
          ROUND(MIN(total_generation), 2) as min_mw,
          COUNT(DISTINCT settlementPeriod) as periods
        FROM combined_generation
        GROUP BY fuelType
        ORDER BY total_mwh DESC
        """
        
        gen_df = bq_client.query(gen_query).to_dataframe()
        logging.info(f"  ✅ Retrieved {len(gen_df)} fuel types")
        
        if not gen_df.empty:
            total_generation = gen_df['total_mwh'].sum()
            
            # Map fuel types to emojis
            fuel_emoji = {
                'NUCLEAR': '⚛️',
                'BIOMASS': '🌱',
                'COAL': '⚫',
                'CCGT': '🔥',
                'OCGT': '🔥',
                'GAS': '🔥',
                'WIND': '💨',
                'SOLAR': '☀️',
                'HYDRO': '💧',
                'NPSHYD': '💧',
                'PS': '🔋',
                'OIL': '🛢️',
                'OTHER': '⚡',
                'INTFR': '🇫🇷',
                'INTIRL': '🇮🇪',
                'INTNED': '🇳🇱',
                'INTEW': '🏴󐁧󐁢󐁥󐁮󐁧󐁿',
                'INTELEC': '⚡',
                'INTNEM': '🔌',
                'INTNSL': '🔌'
            }
            
            # Prepare data rows
            gen_data = []
            for idx, row in gen_df.iterrows():
                fuel = row['fuelType']
                emoji = fuel_emoji.get(fuel.upper(), '⚡')
                pct = round((row['total_mwh'] / total_generation * 100), 2) if total_generation > 0 else 0
                
                gen_data.append([
                    f"{emoji} {fuel}",
                    f"{row['total_mwh']:,.0f}",
                    f"{row['avg_mw']:,.0f}",
                    f"{pct}%",
                    f"{row['max_mw']:,.0f}",
                    f"{row['min_mw']:,.0f}",
                    f"SP 1-{int(row['periods'])}"
                ])
            
            # Write to sheet (starting row 10)
            if gen_data:
                sheet.update(gen_data, f'A10:G{9+len(gen_data)}')
                logging.info(f"  ✅ Wrote {len(gen_data)} fuel type rows")
        
        # ========================================================================
        # SECTION 3: SYSTEM PRICES (Rows 80-90)
        # ========================================================================
        logging.info("💷 Section 3: System Prices...")
        
        price_query = f"""
        WITH combined_prices AS (
          SELECT 
            settlementDate,
            settlementPeriod,
            price
          FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
          WHERE CAST(settlementDate AS DATE) = '{date_today}'
            AND dataProvider = 'APXMIDP'
        )
        SELECT 
          ROUND(AVG(price), 2) as avg_price,
          ROUND(MAX(price), 2) as max_price,
          ROUND(MIN(price), 2) as min_price,
          COUNT(*) as periods
        FROM combined_prices
        WHERE price IS NOT NULL
        """
        
        price_df = bq_client.query(price_query).to_dataframe()
        
        if not price_df.empty and len(price_df) > 0:
            row = price_df.iloc[0]
            sheet.update([['Market Prices (mid)']], 'A80')
            sheet.update([
                ['Avg Price:', f'£{row["avg_price"]:.2f}/MWh'],
                ['Max Price:', f'£{row["max_price"]:.2f}/MWh'],
                ['Min Price:', f'£{row["min_price"]:.2f}/MWh'],
                ['Periods:', f'{int(row["periods"])} SP']
            ], 'A81:B84')
            logging.info(f"  ✅ Updated prices (Avg: £{row['avg_price']:.2f}/MWh)")
        
        # ========================================================================
        # SECTION 4: DEMAND DATA - SKIPPED (schema unclear)
        # ========================================================================
        logging.info("⚡ Section 4: Demand (skipped - will add later)")
        
        # ========================================================================
        # SECTION 5: FREQUENCY DATA
        # ========================================================================
        logging.info("📡 Section 5: Frequency...")
        
        freq_query = f"""
        SELECT 
          ROUND(AVG(frequency), 3) as avg_freq,
          ROUND(MAX(frequency), 3) as max_freq,
          ROUND(MIN(frequency), 3) as min_freq,
          COUNTIF(frequency < 49.8 OR frequency > 50.2) as excursions
        FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
        WHERE CAST(measurementTime AS DATE) = '{date_today}'
        """
        
        freq_df = bq_client.query(freq_query).to_dataframe()
        
        if not freq_df.empty:
            row = freq_df.iloc[0]
            sheet.update([
                ['System Frequency:', ''],
                ['Avg:', f'{row["avg_freq"]:.3f} Hz'],
                ['Range:', f'{row["min_freq"]:.3f} - {row["max_freq"]:.3f} Hz'],
                ['Excursions:', f'{int(row["excursions"])} events']
            ], 'A90:B93')
            logging.info(f"  ✅ Updated frequency (Avg: {row['avg_freq']:.3f} Hz)")
        
        # ========================================================================
        # SECTION 6: TRANSMISSION CONSTRAINTS (Rows 116-126) - Keep existing
        # ========================================================================
        logging.info("🔌 Section 6: Transmission Constraints (preserved from copy)")
        # This section was copied from old dashboard, no update needed
        
        # ========================================================================
        # FINAL: Update timestamp in header
        # ========================================================================
        sheet.update([[f'✅ FRESH']], 'H2')
        
        logging.info("=" * 80)
        logging.info("✅ DASHBOARD V2 UPDATE COMPLETE")
        logging.info("=" * 80)
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Update failed: {e}")
        logging.exception("Full traceback:")
        return False

def main():
    """Main entry point"""
    success = update_dashboard_complete()
    
    if success:
        logging.info("✅ Dashboard V2 update completed successfully")
        sys.exit(0)
    else:
        logging.error("❌ Dashboard V2 update failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
