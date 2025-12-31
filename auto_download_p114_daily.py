#!/usr/bin/env python3
"""
Automated Daily P114 Settlement Data Ingestion
Fetches latest P114 data (yesterday + today) every day

Schedule: Daily at 2am (after Elexon publishes settlement data)
Cron: 0 2 * * * /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py >> /home/george/GB-Power-Market-JJ/logs/p114_daily.log 2>&1
"""

import subprocess
import sys
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"p114_daily_{datetime.now():%Y%m%d}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_date_range():
    """Get date range for daily update (yesterday + today + tomorrow for safety)"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Return 3-day window to catch any delayed publications
    return yesterday.strftime('%Y-%m-%d'), tomorrow.strftime('%Y-%m-%d')


def ingest_p114_range(start_date, end_date, settlement_run='II'):
    """Run P114 ingestion for date range"""
    cmd = [
        'python3',
        str(Path(__file__).parent / 'ingest_p114_s0142.py'),
        start_date,
        end_date,
        settlement_run
    ]

    logger.info(f"🚀 Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        logger.info(f"✅ Success: {result.stdout}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout after 1 hour")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed: {e.stderr}")
        return False


def main():
    logger.info("=" * 80)
    logger.info("🔄 P114 DAILY AUTO-INGESTION")
    logger.info("=" * 80)

    start_date, end_date = get_date_range()
    logger.info(f"📅 Date Range: {start_date} to {end_date}")

    # Try II run first (Initial Settlement - published T+1)
    logger.info("\n📊 Attempting II run (Initial Settlement)...")
    success_ii = ingest_p114_range(start_date, end_date, 'II')

    # Try SF run (Day After - published T+2)
    logger.info("\n📊 Attempting SF run (Settlement Final)...")
    success_sf = ingest_p114_range(start_date, end_date, 'SF')

    # Try R1 run (5 Working Days After)
    logger.info("\n📊 Attempting R1 run (Reconciliation 1)...")
    success_r1 = ingest_p114_range(start_date, end_date, 'R1')

    logger.info("\n" + "=" * 80)
    logger.info("📈 SUMMARY")
    logger.info("=" * 80)
    logger.info(f"II (Initial):        {'✅ Success' if success_ii else '❌ Failed'}")
    logger.info(f"SF (Final):          {'✅ Success' if success_sf else '❌ Failed'}")
    logger.info(f"R1 (Reconciliation): {'✅ Success' if success_r1 else '❌ Failed'}")

    if success_ii or success_sf or success_r1:
        logger.info("\n✅ At least one settlement run succeeded")
        return 0
    else:
        logger.error("\n❌ All settlement runs failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
