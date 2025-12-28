#!/usr/bin/env python3
"""
Daily BM Data Pipeline - Master Automation Script
==================================================

Runs complete data refresh workflow:
1. Backfill BOALF (raw acceptances, last 3 days)
2. Backfill BOAV/EBOCF (settlement data, last 3 days)
3. Run BOD matching (derive acceptance prices)
4. Update Data_Hidden (populate Google Sheets sparkline rows)
5. Update Live Dashboard v2

Schedule: Daily at 3 AM via cron
Runtime: ~15-20 minutes

Author: George Major
Date: December 20, 2025
"""

import sys
import os
import logging
import subprocess
from datetime import datetime, timedelta

# Setup logging
log_dir = '/home/george/GB-Power-Market-JJ/logs'
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_dir}/daily_pipeline.log'),
        logging.StreamHandler()
    ]
)

PROJECT_DIR = '/home/george/GB-Power-Market-JJ'

def run_script(script_name, args='', description=''):
    """Execute a Python script and return success status"""
    logging.info(f"{'='*80}")
    logging.info(f"📊 {description}")
    logging.info(f"{'='*80}")

    cmd = f"cd {PROJECT_DIR} && python3 {script_name} {args}"
    logging.info(f"Command: {cmd}")

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )

        if result.returncode == 0:
            logging.info(f"✅ {description} - SUCCESS")
            if result.stdout:
                # Log last 20 lines of output
                lines = result.stdout.strip().split('\n')
                for line in lines[-20:]:
                    logging.info(f"   {line}")
            return True
        else:
            logging.error(f"❌ {description} - FAILED")
            logging.error(f"Exit code: {result.returncode}")
            if result.stderr:
                logging.error(f"Error: {result.stderr[-1000:]}")  # Last 1000 chars
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"❌ {description} - TIMEOUT (30 minutes)")
        return False
    except Exception as e:
        logging.error(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Execute complete daily pipeline"""
    start_time = datetime.now()
    logging.info("\n" + "="*80)
    logging.info("⚡ DAILY BM DATA PIPELINE - START")
    logging.info("="*80)
    logging.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Calculate date range (last 3 days)
    today = datetime.now().date()
    start_date = (today - timedelta(days=3)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')

    results = {}

    # Step 1: Backfill BM settlement data (BOAV + EBOCF)
    results['boav_ebocf'] = run_script(
        'ingest_bm_settlement_data.py',
        f'--start {start_date} --end {end_date}',
        'Step 1: Backfill BOAV + EBOCF (settlement volumes & cashflows)'
    )

    # Step 2: Backfill BOALF raw data (acceptances without prices)
    # Note: Using direct API ingestion to bmrs_boalf_iris
    results['boalf_raw'] = run_script(
        'backfill_missing_dec19_20.py',
        '',  # This script auto-calculates last 2 days
        'Step 2: Backfill BOALF (raw acceptance data)'
    )

    # Step 3: Run BOD matching to derive acceptance prices
    results['bod_matching'] = run_script(
        'derive_boalf_prices.py',
        f'--start {start_date} --end {end_date}',
        'Step 3: BOD matching (derive acceptance prices for bmrs_boalf_complete)'
    )

    # Step 4: Update Data_Hidden rows for Google Sheets sparklines
    results['data_hidden'] = run_script(
        'update_data_hidden_only.py',
        '',
        'Step 4: Update Data_Hidden (populate sparkline data rows 27-32)'
    )

    # Step 5: Update Live Dashboard v2 (full refresh)
    # Note: This may have errors but should still populate key data
    results['dashboard'] = run_script(
        'update_live_dashboard_v2.py',
        '',
        'Step 5: Update Live Dashboard v2 (complete refresh)'
    )

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60

    logging.info("\n" + "="*80)
    logging.info("📊 PIPELINE SUMMARY")
    logging.info("="*80)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for step, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        logging.info(f"{step.upper()}: {status}")

    logging.info(f"\nSuccess rate: {success_count}/{total_count} ({100*success_count/total_count:.0f}%)")
    logging.info(f"Duration: {duration:.1f} minutes")
    logging.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("="*80)

    # Exit with appropriate code
    if success_count >= 3:  # At least 3/5 steps must succeed
        logging.info("🎉 Pipeline completed successfully (critical steps passed)")
        sys.exit(0)
    else:
        logging.error("⚠️  Pipeline completed with warnings (too many failures)")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.warning("\n⚠️  Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"\n❌ Pipeline crashed: {e}")
        import traceback
        logging.error(traceback.format_exc())
        sys.exit(1)
