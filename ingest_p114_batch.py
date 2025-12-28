#!/usr/bin/env python3
"""
P114 S0142 Batch Ingestion with Weekly Chunks
Prevents timeout on large date ranges
"""

import subprocess
import sys
from datetime import datetime, timedelta
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_weekly_batches(start_date_str, end_date_str):
    """Generate weekly date ranges"""
    start = datetime.strptime(start_date_str, '%Y-%m-%d')
    end = datetime.strptime(end_date_str, '%Y-%m-%d')

    batches = []
    current = start

    while current <= end:
        batch_end = min(current + timedelta(days=6), end)  # 7 day chunks
        batches.append((
            current.strftime('%Y-%m-%d'),
            batch_end.strftime('%Y-%m-%d')
        ))
        current = batch_end + timedelta(days=1)

    return batches

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 ingest_p114_batch.py START_DATE END_DATE SETTLEMENT_RUN")
        print("Example: python3 ingest_p114_batch.py 2024-10-01 2024-10-31 II")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]
    settlement_run = sys.argv[3]

    batches = generate_weekly_batches(start_date, end_date)

    logger.info(f"🚀 P114 Batch Ingestion: {start_date} to {end_date} ({settlement_run})")
    logger.info(f"📦 Split into {len(batches)} weekly batches")

    total_success = 0
    total_failed = 0

    for i, (batch_start, batch_end) in enumerate(batches, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Batch {i}/{len(batches)}: {batch_start} to {batch_end}")
        logger.info(f"{'='*80}")

        cmd = [
            'python3', 'ingest_p114_s0142.py',
            batch_start, batch_end, settlement_run
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=False)
            if result.returncode == 0:
                total_success += 1
                logger.info(f"✅ Batch {i} completed successfully")
            else:
                total_failed += 1
                logger.error(f"❌ Batch {i} failed with code {result.returncode}")
        except subprocess.CalledProcessError as e:
            total_failed += 1
            logger.error(f"❌ Batch {i} failed: {e}")
        except KeyboardInterrupt:
            logger.warning(f"\n⚠️ Interrupted at batch {i}/{len(batches)}")
            logger.info(f"Resume with: python3 ingest_p114_batch.py {batch_start} {end_date} {settlement_run}")
            sys.exit(1)

    logger.info(f"\n{'='*80}")
    logger.info(f"📊 BATCH INGESTION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Total Batches: {len(batches)}")
    logger.info(f"✅ Successful: {total_success}")
    logger.info(f"❌ Failed: {total_failed}")
    logger.info(f"Success Rate: {total_success*100//len(batches)}%")

if __name__ == '__main__':
    main()
