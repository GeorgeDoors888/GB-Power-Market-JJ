#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Run Elexon ingestion with year-specific schemas.

This script helps run the ingestion script for different years
with appropriate parameters, using year-specific schemas.
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


def run_ingestion(
    start_date: str,
    end_date: str,
    datasets: str = "",
    batch_size: int = 20,
    use_staging: bool = True,
    skip_existing: bool = True,
    log_file: str = "",
    include_offline: bool = False,
):
    """Run the ingestion script with specified parameters."""

    # Determine year from start date for log file naming
    year = start_date.split("-")[0]

    # Generate a log file name if not provided
    if not log_file:
        start_str = start_date.replace("-", "")
        end_str = end_date.replace("-", "")
        dataset_str = datasets.replace(",", "_") if datasets else "all"
        log_file = f"ingest_{year}_{start_str}_to_{end_str}_{dataset_str}.log"

    # Build the command
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
    ]

    # Add optional parameters
    if datasets:
        cmd.extend(["--only", datasets])

    if use_staging:
        cmd.append("--use-staging-table")

    if skip_existing:
        cmd.append("--skip-existing")

    if include_offline:
        cmd.append("--include-offline")

    # Run the command
    logging.info(f"Running ingestion for {start_date} to {end_date}")
    logging.info(f"Command: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        logging.info(f"Ingestion completed successfully. Log file: {log_file}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Ingestion failed with exit code {e.returncode}")
        return False


def run_quarterly(
    year: int,
    datasets: str = "",
    batch_size: int = 20,
    use_staging: bool = True,
    skip_existing: bool = True,
    include_offline: bool = False,
):
    """Run ingestion for each quarter of a year."""
    quarters = [
        (f"{year}-01-01", f"{year}-04-01"),
        (f"{year}-04-01", f"{year}-07-01"),
        (f"{year}-07-01", f"{year}-10-01"),
        (f"{year}-10-01", f"{year+1}-01-01"),
    ]

    for i, (start, end) in enumerate(quarters):
        q_num = i + 1
        log_file = f"ingest_{year}_Q{q_num}_{datasets.replace(',', '_') if datasets else 'all'}.log"

        success = run_ingestion(
            start,
            end,
            datasets=datasets,
            batch_size=batch_size,
            use_staging=use_staging,
            skip_existing=skip_existing,
            log_file=log_file,
            include_offline=include_offline,
        )

        if not success:
            logging.error(f"Failed during Q{q_num} {year}. Stopping.")
            return False

        logging.info(f"Completed Q{q_num} {year}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run Elexon ingestion with year-specific schemas"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2022, 2023, 2024],
        help="Years to process (default: 2022 2023 2024)",
    )
    parser.add_argument(
        "--datasets",
        default="",
        help="Comma-separated list of datasets to process (default: all)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Batch size for ingestion (default: 20)",
    )
    parser.add_argument(
        "--no-staging",
        action="store_true",
        help="Disable staging tables (use direct loading)",
    )
    parser.add_argument(
        "--no-skip", action="store_true", help="Don't skip existing data"
    )
    parser.add_argument(
        "--include-offline",
        action="store_true",
        help="Include offline datasets (MILS, MELS)",
    )
    parser.add_argument(
        "--mode",
        choices=["quarterly", "yearly", "custom"],
        default="quarterly",
        help="Processing mode: quarterly, yearly, or custom date range",
    )
    parser.add_argument("--start", help="Custom start date (required for custom mode)")
    parser.add_argument("--end", help="Custom end date (required for custom mode)")

    args = parser.parse_args()

    # Check if schemas directory exists
    if not os.path.exists("schemas"):
        logging.error(
            "Schemas directory not found. Please run generate_schemas_from_bigquery.py first."
        )
        sys.exit(1)

    # Process based on selected mode
    if args.mode == "custom":
        if not args.start or not args.end:
            logging.error("Custom mode requires --start and --end parameters")
            sys.exit(1)

        run_ingestion(
            args.start,
            args.end,
            datasets=args.datasets,
            batch_size=args.batch_size,
            use_staging=not args.no_staging,
            skip_existing=not args.no_skip,
            include_offline=args.include_offline,
        )

    elif args.mode == "yearly":
        for year in args.years:
            logging.info(f"Processing year {year}")
            run_ingestion(
                f"{year}-01-01",
                f"{year+1}-01-01",
                datasets=args.datasets,
                batch_size=args.batch_size,
                use_staging=not args.no_staging,
                skip_existing=not args.no_skip,
                include_offline=args.include_offline,
            )

    else:  # quarterly
        for year in args.years:
            logging.info(f"Processing year {year} by quarter")
            run_quarterly(
                year,
                datasets=args.datasets,
                batch_size=args.batch_size,
                use_staging=not args.no_staging,
                skip_existing=not args.no_skip,
                include_offline=args.include_offline,
            )

    logging.info("All ingestion tasks completed!")


if __name__ == "__main__":
    main()
