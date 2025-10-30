#!/usr/bin/env python3
"""
Real-time Power Generation Data Updater
Fetches latest FUELINST, WIND_SOLAR_GEN, and MID data from Elexon BMRS API every 5 minutes
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import argparse
from google.cloud import bigquery

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/realtime_updates.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def fetch_latest_data(minutes_back=15):
    """
    Fetch data from the last N minutes.
    
    Args:
        minutes_back: How many minutes back to fetch (default: 15)
    """
    try:
        # Calculate time window
        now = datetime.utcnow()
        start = now - timedelta(minutes=minutes_back)
        
        # Format as dates for the ingestion script
        start_date = start.strftime('%Y-%m-%d')
        # IMPORTANT: end_date must be TOMORROW to create a valid window for today's data
        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        logger.info(f"🔄 Fetching data from {start.strftime('%Y-%m-%d %H:%M')} to {now.strftime('%Y-%m-%d %H:%M')} UTC")
        logger.info(f"   Date range: {start_date} to {end_date}")
        
        # Import the ingestion script
        import subprocess
        
        cmd = [
            sys.executable,  # Use the same Python interpreter
            'ingest_elexon_fixed.py',
            '--start', start_date,
            '--end', end_date,
            '--only', 'FUELINST,WIND_SOLAR_GEN,MID'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            logger.info("✅ Real-time update completed successfully")
            logger.info(f"   Output: {result.stdout.splitlines()[-5:]}")  # Last 5 lines
            return True
        else:
            logger.error(f"❌ Real-time update failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error in real-time update: {str(e)}")
        return False


def check_data_freshness():
    """Check how old the latest data is."""
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
        client = bigquery.Client(project='inner-cinema-476211-u9')
        
        # Check FUELINST
        query_fuelinst = """
        SELECT 
            MAX(DATE(settlementDate)) as latest_date,
            MAX(settlementPeriod) as latest_period,
            MAX(publishTime) as latest_publish,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(publishTime) AS TIMESTAMP), MINUTE) as minutes_old
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
        """
        
        result = list(client.query(query_fuelinst).result())[0]
        
        logger.info(f"📊 FUELINST data status:")
        logger.info(f"   Latest date: {result.latest_date}")
        logger.info(f"   Latest period: {result.latest_period}")
        logger.info(f"   Data age: {result.minutes_old} minutes")
        
        fuelinst_fresh = result.minutes_old <= 30
        
        if result.minutes_old > 30:
            logger.warning(f"⚠️  FUELINST data is {result.minutes_old} minutes old (expected < 30)")
        else:
            logger.info(f"✅ FUELINST data is fresh ({result.minutes_old} minutes old)")
        
        # Check WIND_SOLAR_GEN
        query_solar = """
        SELECT 
            MAX(DATE(settlementDate)) as latest_date,
            MAX(settlementPeriod) as latest_period,
            MAX(publishTime) as latest_publish,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(publishTime) AS TIMESTAMP), MINUTE) as minutes_old
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_wind_solar_gen`
        """
        
        try:
            result_solar = list(client.query(query_solar).result())[0]
            
            logger.info(f"📊 WIND_SOLAR_GEN data status:")
            logger.info(f"   Latest date: {result_solar.latest_date}")
            logger.info(f"   Latest period: {result_solar.latest_period}")
            logger.info(f"   Data age: {result_solar.minutes_old} minutes")
            
            solar_fresh = result_solar.minutes_old <= 30
            
            if result_solar.minutes_old > 30:
                logger.warning(f"⚠️  WIND_SOLAR_GEN data is {result_solar.minutes_old} minutes old (expected < 30)")
            else:
                logger.info(f"✅ WIND_SOLAR_GEN data is fresh ({result_solar.minutes_old} minutes old)")
            
            return fuelinst_fresh and solar_fresh
        except Exception as e:
            logger.warning(f"⚠️  Could not check WIND_SOLAR_GEN: {str(e)}")
            return fuelinst_fresh
        
    except Exception as e:
        logger.error(f"❌ Error checking data freshness: {str(e)}")
        return False

def check_mid_data():
    """Check MID (Market Index Data) freshness"""
    try:
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
        client = bigquery.Client(project='inner-cinema-476211-u9')
        
        query_mid = """
        SELECT 
            MAX(DATE(settlementDate)) as latest_date,
            MAX(settlementPeriod) as latest_period,
            dataProvider,
            MAX(price) as latest_price,
            MAX(volume) as latest_volume
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
        WHERE settlementDate >= CURRENT_DATE() - 2
        GROUP BY dataProvider
        ORDER BY dataProvider
        """
        
        results = list(client.query(query_mid).result())
        
        logger.info(f"💷 MID (Market Index Data) status:")
        for row in results:
            logger.info(f"   {row.dataProvider}: £{row.latest_price:.2f}/MWh ({row.latest_volume:.0f} MWh)")
            logger.info(f"      Latest: {row.latest_date} Period {row.latest_period}")
        
        return True
        
    except Exception as e:
        logger.warning(f"⚠️  Could not check MID data: {str(e)}")
        return False
            
    except Exception as e:
        logger.error(f"❌ Error checking data freshness: {str(e)}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Real-time power generation data updater (FUELINST + WIND_SOLAR_GEN + MID)')
    parser.add_argument('--minutes-back', type=int, default=15,
                       help='How many minutes back to fetch (default: 15)')
    parser.add_argument('--check-only', action='store_true',
                       help='Only check data freshness, do not fetch')
    
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("🔄 REAL-TIME POWER DATA UPDATER (FUELINST + WIND_SOLAR_GEN + MID)")
    logger.info("=" * 80)
    
    if args.check_only:
        check_data_freshness()
        check_mid_data()
    else:
        # Check current status
        check_data_freshness()
        check_mid_data()
        
        # Fetch latest data
        success = fetch_latest_data(minutes_back=args.minutes_back)
        
        if success:
            logger.info("✅ Update cycle completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Update cycle failed")
            sys.exit(1)


if __name__ == '__main__':
    main()
