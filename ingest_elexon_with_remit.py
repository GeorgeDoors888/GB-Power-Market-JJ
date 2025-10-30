#!/usr/bin/env python
"""
Add REMIT dataset support to ingest_elexon_fixed.py

This script integrates the REMIT ingestor with the main Elexon BMRS
ingestion process to allow for a unified command-line interface.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Set up path to find the existing modules
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

# Import from the main ingest script
from ingest_elexon_fixed import main as elexon_main

# Import the REMIT ingestion logic
from ingest_remit import check_remit_table, ingest_remit_data


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced Elexon BMRS + REMIT ingestion pipeline"
    )

    # Standard arguments from ingest_elexon_fixed.py
    parser.add_argument("--start", help="ISO date (YYYY-MM-DD) or full ISO8601")
    parser.add_argument(
        "--end",
        help="ISO date (YYYY-MM-DD) or full ISO8601 (exclusive upper bound is fine)",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated dataset codes, e.g. BOD,BOAL,DISBSAD,REMIT",
    )
    parser.add_argument(
        "--include-remit",
        action="store_true",
        help="Include REMIT data in the ingestion process",
    )
    parser.add_argument(
        "--remit-only",
        action="store_true",
        help="Only ingest REMIT data (skip standard BMRS datasets)",
    )
    parser.add_argument(
        "--remit-data-dir",
        default="./elexon_iris/data",
        help="Directory containing IRIS data files for REMIT",
    )
    parser.add_argument(
        "--remit-processed-file",
        default="./elexon_iris/processed_files.txt",
        help="File to track processed REMIT files",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level",
    )

    args, remaining_args = parser.parse_known_args()

    # Set up logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Process REMIT data if requested
    process_remit = (
        args.include_remit or args.remit_only or "REMIT" in args.only.upper().split(",")
    )

    if process_remit:
        logging.info("Processing REMIT data...")
        processed, errors = ingest_remit_data(
            data_dir=args.remit_data_dir,
            processed_file=args.remit_processed_file,
        )
        check_remit_table()

        if errors:
            logging.warning(f"Encountered {len(errors)} errors during REMIT ingestion")

    # Process standard BMRS data if not in REMIT-only mode
    if not args.remit_only:
        logging.info("Processing standard BMRS datasets...")

        # Build sys.argv for the elexon_main function
        sys.argv = [sys.argv[0]] + remaining_args

        # If we've already included REMIT through the dedicated ingestion,
        # remove it from the --only parameter if it's there
        if process_remit and args.only and "REMIT" in args.only.upper().split(","):
            only_datasets = [ds for ds in args.only.split(",") if ds.upper() != "REMIT"]
            for i, arg in enumerate(sys.argv):
                if arg == "--only" and i + 1 < len(sys.argv):
                    sys.argv[i + 1] = ",".join(only_datasets)

        # Call the main function from ingest_elexon_fixed.py
        elexon_main()

    logging.info("All ingestion processes completed")


if __name__ == "__main__":
    main()
