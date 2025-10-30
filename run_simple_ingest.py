#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple runner for Elexon ingestion with no staging tables for historical data.
This script avoids schema issues entirely by using direct loading.
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def run_quarter(year, quarter, datasets="", batch_size=10):
    """Run ingestion for a specific quarter of a year."""
    quarters = {
        1: (f"{year}-01-01", f"{year}-04-01"),
        2: (f"{year}-04-01", f"{year}-07-01"),
        3: (f"{year}-07-01", f"{year}-10-01"),
        4: (f"{year}-10-01", f"{year+1}-01-01"),
    }

    if quarter not in quarters:
        logging.error(f"Invalid quarter: {quarter}. Must be 1, 2, 3, or 4.")
        return False

    start_date, end_date = quarters[quarter]
    log_file = f"ingest_{year}_Q{quarter}_{datasets.replace(',', '_') if datasets else 'all'}.log"

    cmd = [
        "python",
        "ingest_elexon_fixed.py",
        "--start",
        start_date,
        "--end",
        end_date,
        "--batch-size",
        str(batch_size),
        "--log-level",
        "INFO",
        "--log-file",
        log_file,
        "--skip-existing",  # Skip datasets that already have data
    ]

    # Add dataset filter if specified
    if datasets:
        cmd.extend(["--only", datasets])

    # Run the command
    logging.info(f"Running ingestion for {year} Q{quarter}")
    logging.info(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Ingestion completed successfully. Log file: {log_file}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ingestion failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Simple runner for Elexon ingestion")
    parser.add_argument("--year", type=int, required=True, help="Year to process")
    parser.add_argument(
        "--quarter",
        type=int,
        required=True,
        choices=[1, 2, 3, 4],
        help="Quarter to process (1-4)",
    )
    parser.add_argument(
        "--datasets",
        default="",
        help="Comma-separated list of datasets to process (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for ingestion (default: 10)",
    )

    args = parser.parse_args()

    run_quarter(args.year, args.quarter, args.datasets, args.batch_size)


if __name__ == "__main__":
    main()
