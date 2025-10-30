#!/usr/bin/env python
"""
Script to ingest REMIT data from Elexon IRIS service to BigQuery

This standalone script is designed to be run separately or integrated with
the main ingest_elexon_fixed.py process. It handles REMIT data which comes
through the IRIS service rather than the standard BMRS API.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from google.cloud import bigquery

# Import functions from the existing IRIS code
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from elexon_iris.iris_to_bigquery import process_new_files

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DATA_DIR = "./elexon_iris/data"
DEFAULT_PROCESSED_FILE = "./elexon_iris/processed_files.txt"
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
REMIT_TABLE = "bmrs_remit"


def ingest_remit_data(
    data_dir: str = DEFAULT_DATA_DIR,
    processed_file: str = DEFAULT_PROCESSED_FILE,
) -> tuple:
    """
    Process REMIT data from IRIS and load to BigQuery

    Args:
        data_dir: Directory containing IRIS data files
        processed_file: File to track processed files

    Returns:
        tuple: (processed_files, errors)
    """
    logger.info("Starting REMIT data ingestion process")

    # Make sure the data directory exists
    os.makedirs(data_dir, exist_ok=True)

    # Process new files
    processed, errors = process_new_files(data_dir, processed_file)

    if processed:
        logger.info(f"Successfully processed {len(processed)} REMIT files")
    else:
        logger.info("No new REMIT files to process")

    if errors:
        logger.error(f"Encountered errors with {len(errors)} files")

    return processed, errors


def check_remit_table():
    """Check if the REMIT table exists and has data"""
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{REMIT_TABLE}"

    try:
        table = client.get_table(table_id)
        logger.info(f"REMIT table exists with {table.num_rows} rows")

        # Get the latest data
        query = f"""
        SELECT
            COUNT(*) as event_count,
            MIN(eventStartTime) as earliest_start,
            MAX(eventEndTime) as latest_end,
            COUNT(DISTINCT assetId) as unique_assets
        FROM `{table_id}`
        WHERE eventEndTime > CURRENT_TIMESTAMP()
        """

        query_job = client.query(query)
        results = list(query_job)

        if results and results[0].event_count > 0:
            logger.info(f"Current active REMIT events: {results[0].event_count}")
            logger.info(f"Unique assets with active events: {results[0].unique_assets}")
            logger.info(
                f"Event time range: {results[0].earliest_start} to {results[0].latest_end}"
            )
        else:
            logger.info("No active REMIT events found")

        return True

    except Exception as e:
        logger.error(f"Error checking REMIT table: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Ingest REMIT data from IRIS to BigQuery"
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Directory containing IRIS data files",
    )
    parser.add_argument(
        "--processed-file",
        default=DEFAULT_PROCESSED_FILE,
        help="File to track processed files",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check the REMIT table status without ingesting",
    )
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    if args.check_only:
        check_remit_table()
    else:
        # Process REMIT data
        ingest_remit_data(args.data_dir, args.processed_file)

        # Check the status after ingestion
        check_remit_table()


if __name__ == "__main__":
    main()
