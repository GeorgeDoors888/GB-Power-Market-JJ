#!/usr/bin/env python3
"""
15-Minute DISBSAD Backfill - Run via cron to keep constraint cost data current
Usage: python3 auto_backfill_disbsad_daily.py
Fetches last 2 days of DISBSAD data to ensure no gaps (runs every 15 minutes)
"""

import logging
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from ingest_elexon_fixed import main as ingest_main

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler('/home/george/GB-Power-Market-JJ/logs/disbsad_15min.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Fetch last 2 days of DISBSAD data (runs every 15 minutes)"""
    today = date.today()
    two_days_ago = today - timedelta(days=2)
    start_date = two_days_ago.strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    logging.info("=" * 80)
    logging.info(f"🔧 15-MIN DISBSAD BACKFILL: {start_date} to {end_date}")
    logging.info("=" * 80)
    
    # Use ingest_elexon_fixed.py with DISBSAD dataset
    sys.argv = [
        'ingest_elexon_fixed.py',
        '--start', start_date,
        '--end', end_date,
        '--only', 'DISBSAD',
        '--overwrite'  # Replace if exists
    ]
    
    try:
        ingest_main()
        logging.info(f"✅ DISBSAD backfill complete for {start_date} to {end_date}")
    except Exception as e:
        logging.error(f"❌ DISBSAD backfill failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
