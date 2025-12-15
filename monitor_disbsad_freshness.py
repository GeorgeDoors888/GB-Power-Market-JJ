#!/usr/bin/env python3
"""
DISBSAD Data Freshness Monitor
Checks if DISBSAD data is current and triggers backfill if stale
Run every 15 minutes via cron to ensure data quality

Policy Context:
DISBSAD = Settlement-grade data (D+1 to D+2 Working Days)
- NOT real-time (validation required)
- NOT in IRIS (settlement layer, not transparency layer)
- Used for: Imbalance price verification, cost attribution, settlement reconciliation
"""

import sys
import logging
from datetime import date, timedelta, datetime
from google.cloud import bigquery
import subprocess

# Configuration
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TABLE = 'bmrs_disbsad'
BACKFILL_SCRIPT = '/home/george/GB-Power-Market-JJ/backfill_disbsad_simple.py'

# Freshness thresholds
EXPECTED_LAG_WORKING_DAYS = 2  # D+2 WD is normal
MAX_ACCEPTABLE_LAG_DAYS = 4     # Alert if >4 days stale

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/home/george/GB-Power-Market-JJ/logs/disbsad_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_working_days_ago(n):
    """Calculate date N working days ago (excluding weekends)"""
    current = date.today()
    working_days = 0
    
    while working_days < n:
        current -= timedelta(days=1)
        # Skip weekends
        if current.weekday() < 5:  # Mon=0, Fri=4
            working_days += 1
    
    return current


def check_disbsad_freshness():
    """
    Check DISBSAD data freshness
    
    Returns:
        tuple: (is_fresh, latest_date, days_lag, message)
    """
    try:
        client = bigquery.Client(project=PROJECT_ID, location='US')
        
        # Get latest DISBSAD date with actual data
        query = f"""
        SELECT 
            MAX(DATE(settlementDate)) as latest_date,
            COUNT(*) as record_count,
            SUM(ABS(cost)) as total_cost
        FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
        WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
          AND ABS(cost) > 0  -- Ignore zero-cost placeholder records
        """
        
        result = list(client.query(query).result())[0]
        latest_date = result.latest_date
        
        if not latest_date:
            return False, None, 999, "❌ No recent DISBSAD data found"
        
        # Calculate lag
        days_lag = (date.today() - latest_date).days
        
        # Expected freshness: D+2 working days
        expected_date = get_working_days_ago(EXPECTED_LAG_WORKING_DAYS)
        
        # Is data fresh enough?
        is_fresh = latest_date >= expected_date or days_lag <= MAX_ACCEPTABLE_LAG_DAYS
        
        status = "✅" if is_fresh else "⚠️"
        message = f"{status} Latest DISBSAD: {latest_date} ({days_lag} days lag)"
        
        logger.info(message)
        logger.info(f"   Expected minimum: {expected_date} (D+2 WD)")
        logger.info(f"   Records: {result.record_count:,}, Cost: £{result.total_cost:,.0f}")
        
        return is_fresh, latest_date, days_lag, message
        
    except Exception as e:
        logger.error(f"❌ Freshness check failed: {e}")
        return False, None, 999, f"Error: {e}"


def trigger_backfill():
    """
    Trigger DISBSAD backfill script
    
    Returns:
        bool: True if successful
    """
    try:
        logger.info("🔧 Triggering DISBSAD backfill...")
        
        result = subprocess.run(
            ['python3', BACKFILL_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info("✅ Backfill completed successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"❌ Backfill failed with code {result.returncode}")
            logger.error(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Backfill timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"❌ Backfill trigger failed: {e}")
        return False


def get_recent_coverage():
    """Get recent DISBSAD coverage summary"""
    try:
        client = bigquery.Client(project=PROJECT_ID, location='US')
        
        query = f"""
        SELECT 
            DATE(settlementDate) as date,
            COUNT(*) as records,
            COUNT(DISTINCT assetId) as assets,
            SUM(ABS(cost)) as total_cost,
            COUNT(CASE WHEN soFlag = true THEN 1 END) as so_actions,
            COUNT(CASE WHEN storFlag = true THEN 1 END) as stor_actions
        FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        
        logger.info("\n📊 Recent DISBSAD Coverage (Last 7 days):")
        logger.info(f"{'Date':<12} {'Records':<10} {'Assets':<8} {'SO Actions':<12} {'Total Cost':<15}")
        logger.info("=" * 70)
        
        for row in client.query(query).result():
            logger.info(
                f"{str(row.date):<12} {row.records:<10} {row.assets:<8} "
                f"{row.so_actions:<12} £{row.total_cost:>12,.0f}"
            )
        
    except Exception as e:
        logger.warning(f"⚠️  Coverage summary failed: {e}")


def main():
    """Main monitoring logic"""
    logger.info("=" * 80)
    logger.info("🔍 DISBSAD FRESHNESS MONITOR")
    logger.info("=" * 80)
    logger.info("Policy: DISBSAD is settlement-grade data (D+1 to D+2 WD)")
    logger.info("Reason: Requires validation, reconciliation, cost attribution")
    logger.info("=" * 80)
    
    # Check freshness
    is_fresh, latest_date, days_lag, message = check_disbsad_freshness()
    
    # Auto-trigger backfill if stale
    if not is_fresh and days_lag > MAX_ACCEPTABLE_LAG_DAYS:
        logger.warning(f"⚠️  Data is {days_lag} days stale (max acceptable: {MAX_ACCEPTABLE_LAG_DAYS})")
        logger.info("🔧 Auto-triggering backfill...")
        
        success = trigger_backfill()
        
        if success:
            # Re-check freshness
            is_fresh_after, latest_date_after, days_lag_after, message_after = check_disbsad_freshness()
            
            if is_fresh_after or days_lag_after < days_lag:
                logger.info(f"✅ Data freshened: {latest_date} → {latest_date_after}")
            else:
                logger.warning("⚠️  Backfill ran but data still stale (may be weekend/holiday)")
    
    elif is_fresh:
        logger.info("✅ DISBSAD data is current (within acceptable D+2 WD window)")
    
    # Show recent coverage
    get_recent_coverage()
    
    logger.info("=" * 80)
    logger.info("✅ FRESHNESS MONITORING COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.error(f"❌ Monitor failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
