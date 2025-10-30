#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Analyze BigQuery tables to generate year-specific schemas.

This script:
1. Queries BigQuery to get samples of data for each year (2022, 2023, 2024)
2. Analyzes the schema structure
3. Generates year-specific schema files
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from google.cloud import bigquery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# List of datasets to analyze
DEFAULT_DATASETS = [
    "BOD",
    "BOALF",
    "FREQ",
    "FUELINST",
    "MID",
    "MELS",
    "MILS",
    "PN",
    "QPN",
]


def ensure_schema_dirs(years: List[str]):
    """Create schema directories for each year."""
    # Create base schemas directory
    if not os.path.exists("schemas"):
        os.makedirs("schemas")
        logging.info("Created schemas directory")

    # Create year-specific directories
    for year in years:
        year_dir = os.path.join("schemas", year)
        if not os.path.exists(year_dir):
            os.makedirs(year_dir)
            logging.info(f"Created schema directory for {year}")


def get_current_schema(project: str, dataset: str, table: str) -> List[Dict]:
    """Get the current schema for a BigQuery table."""
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{table}"

    try:
        table_obj = client.get_table(table_ref)
        schema = []

        for field in table_obj.schema:
            schema.append(
                {"name": field.name, "type": field.field_type, "mode": field.mode}
            )

        return schema
    except Exception as e:
        logging.error(f"Failed to get schema for {table_ref}: {e}")
        return []


def generate_year_schema(
    project: str, dataset: str, table: str, year: str, copy_if_no_data: bool = True
) -> bool:
    """Generate schema for a specific year."""
    client = bigquery.Client(project=project)
    table_ref = f"{project}.{dataset}.{table}"
    dataset_code = table.replace("bmrs_", "").upper()

    logging.info(f"Generating schema for {dataset_code} ({year})...")

    # First, get a sample of data for the specific year
    query = f"""
    SELECT *
    FROM `{table_ref}`
    WHERE EXTRACT(YEAR FROM TIMESTAMP(
        COALESCE(
            _window_from_utc,
            settlementDate,
            timeFrom,
            CAST(_ingested_utc AS STRING)
        )
    )) = {year}
    LIMIT 100
    """

    try:
        # Run the query
        query_job = client.query(query)
        results = list(query_job.result())

        if not results:
            logging.warning(f"No data found for {dataset_code} in {year}")
            if copy_if_no_data:
                # Copy the current schema as fallback
                current_schema = get_current_schema(project, dataset, table)
                if current_schema:
                    schema_path = os.path.join("schemas", year, f"{table}.json")
                    with open(schema_path, "w") as f:
                        json.dump(current_schema, f, indent=2)
                    logging.info(
                        f"Copied current schema for {dataset_code} ({year}) as fallback"
                    )
                    return True
            return False

        # Get the schema from the query results
        schema = []
        for field in query_job.schema:
            schema.append(
                {"name": field.name, "type": field.field_type, "mode": field.mode}
            )

        # Save the schema
        schema_path = os.path.join("schemas", year, f"{table}.json")
        with open(schema_path, "w") as f:
            json.dump(schema, f, indent=2)

        logging.info(
            f"Saved schema for {dataset_code} ({year}) with {len(schema)} fields"
        )
        return True

    except Exception as e:
        logging.error(f"Failed to generate schema for {dataset_code} ({year}): {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate year-specific schemas from BigQuery data"
    )
    parser.add_argument("--project", required=True, help="BigQuery project ID")
    parser.add_argument("--dataset", required=True, help="BigQuery dataset ID")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DEFAULT_DATASETS,
        help="Specific datasets to process (e.g., BOD FREQ FUELINST)",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        default=["2022", "2023", "2024"],
        help="Years to generate schemas for (default: 2022 2023 2024)",
    )
    parser.add_argument(
        "--copy-current",
        action="store_true",
        help="Copy current schema as fallback for years with no data",
    )

    args = parser.parse_args()

    # Create schema directories
    ensure_schema_dirs(args.years)

    # Process each dataset for each year
    for dataset_code in args.datasets:
        table_name = f"bmrs_{dataset_code.lower()}"
        for year in args.years:
            generate_year_schema(
                args.project,
                args.dataset,
                table_name,
                year,
                copy_if_no_data=args.copy_current,
            )

    logging.info("Schema generation complete!")


if __name__ == "__main__":
    main()
