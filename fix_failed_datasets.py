#!/usr/bin/env python3
"""
Fix Failed BMRS Datasets
========================

Retry the 30 datasets that failed with PyArrow datetime conversion errors.
Using enhanced datetime handling logic.
"""

import logging
import subprocess
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f'fix_failed_datasets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        ),
        logging.StreamHandler(),
    ],
)

# Failed datasets from the log
FAILED_DATASETS = [
    "DISBSAD",
    "FUELHH",
    "FUELINST",
    "IMBALNGC",
    "INDDEM",
    "INDGEN",
    "INDO",
    "ITSDO",
    "MELNGC",
    "MID",
    "NETBSAD",
    "NDF",
    "NDFD",
    "NDFW",
    "NONBM",
    "OCNMF3Y",
    "OCNMF3Y2",
    "OCNMFD",
    "OCNMFD2",
    "QAS",
    "RDRE",
    "RDRI",
    "RURE",
    "RURI",
    "TEMP",
    "TSDF",
    "TSDFD",
    "TSDFW",
    "WINDFOR",
]

# Also fix MDV which had "BQ final load failed"
FAILED_DATASETS.append("MDV")


def run_single_dataset(dataset: str) -> bool:
    """Run ingestion for a single dataset."""

    cmd = [
        "python",
        "ingest_elexon_fixed.py",
        "--start",
        "2023-01-01",
        "--end",
        "2025-09-11",  # Updated to current date
        "--only",
        dataset,
        "--include-offline",
        "--log-level",
        "INFO",
        "--overwrite",  # Force overwrite to clear any partial data
    ]

    logging.info(f"🔄 Retrying dataset: {dataset}")
    logging.info(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per dataset
        )

        if result.returncode == 0:
            logging.info(f"✅ {dataset}: SUCCESS")
            return True
        else:
            logging.error(f"❌ {dataset}: FAILED")
            logging.error(f"STDOUT: {result.stdout[-1000:]}")  # Last 1000 chars
            logging.error(f"STDERR: {result.stderr[-1000:]}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"⏰ {dataset}: TIMEOUT (1 hour)")
        return False
    except Exception as e:
        logging.error(f"💥 {dataset}: EXCEPTION - {e}")
        return False


def main():
    """Main execution."""

    logging.info("🛠️ Fixing Failed BMRS Datasets")
    logging.info("=" * 50)
    logging.info(f"Datasets to retry: {len(FAILED_DATASETS)}")
    logging.info(f"List: {', '.join(FAILED_DATASETS)}")

    success_count = 0
    failed_datasets = []

    for i, dataset in enumerate(FAILED_DATASETS, 1):
        logging.info(f"\n📊 Progress: {i}/{len(FAILED_DATASETS)} - {dataset}")

        success = run_single_dataset(dataset)

        if success:
            success_count += 1
        else:
            failed_datasets.append(dataset)

        logging.info(f"Running tally: {success_count}/{i} successful")

    # Final summary
    logging.info("\n🎯 FINAL RESULTS")
    logging.info("=" * 30)
    logging.info(f"✅ Successful: {success_count}/{len(FAILED_DATASETS)}")
    logging.info(f"❌ Still failing: {len(failed_datasets)}")

    if failed_datasets:
        logging.info(f"Failed datasets: {', '.join(failed_datasets)}")
    else:
        logging.info("🎉 ALL DATASETS FIXED!")

    return len(failed_datasets) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
