#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copy existing schema files for historical years.
This script avoids the need for BigQuery authentication.
"""

import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Define the datasets to process
DATASETS = ["BOD", "BOALF", "FREQ", "FUELINST", "MID", "MELS", "MILS", "PN", "QPN"]


def copy_current_schemas_to_year(year: str):
    """Copy current schema files to a year-specific directory."""
    src_dir = "schemas/2025"  # Use 2025 schemas as baseline
    dst_dir = f"schemas/{year}"

    os.makedirs(dst_dir, exist_ok=True)

    # Count how many files were copied
    copied = 0

    for dataset in DATASETS:
        src_file = f"{src_dir}/bmrs_{dataset.lower()}.json"
        dst_file = f"{dst_dir}/bmrs_{dataset.lower()}.json"

        # Skip if destination already exists
        if os.path.exists(dst_file):
            logging.info(f"Schema already exists for {dataset} ({year})")
            continue

        # Skip if source doesn't exist
        if not os.path.exists(src_file):
            logging.warning(f"No schema found for {dataset} in {src_dir}")
            continue

        # Copy the file
        try:
            shutil.copy2(src_file, dst_file)
            copied += 1
            logging.info(f"Copied schema for {dataset} to {year}")
        except Exception as e:
            logging.error(f"Failed to copy schema for {dataset}: {e}")

    return copied


def update_schema_for_year(dataset: str, year: str, add_columns: list = None):
    """Update a specific schema for a year with additional columns."""
    schema_file = f"schemas/{year}/bmrs_{dataset.lower()}.json"

    if not os.path.exists(schema_file):
        logging.error(f"Schema file not found: {schema_file}")
        return False

    try:
        with open(schema_file, "r") as f:
            schema = json.load(f)

        # Get existing column names
        existing_columns = {field["name"] for field in schema}

        # Add new columns if they don't exist
        if add_columns:
            for col in add_columns:
                if col["name"] not in existing_columns:
                    schema.append(col)
                    logging.info(f"Added column {col['name']} to {dataset} ({year})")

        # Write updated schema
        with open(schema_file, "w") as f:
            json.dump(schema, f, indent=2)

        logging.info(f"Updated schema for {dataset} ({year})")
        return True
    except Exception as e:
        logging.error(f"Failed to update schema for {dataset} ({year}): {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Copy schema files for historical years"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        default=["2022", "2023", "2024"],
        help="Years to create schemas for (default: 2022 2023 2024)",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DATASETS,
        help="Datasets to create schemas for (default: all)",
    )
    args = parser.parse_args()

    # Ensure 2025 schemas directory exists
    if not os.path.exists("schemas/2025"):
        logging.error(
            "2025 schemas directory not found. Please run: cp bmrs_*.json schemas/2025/"
        )
        sys.exit(1)

    # Copy schemas to each year
    for year in args.years:
        copied = copy_current_schemas_to_year(year)
        logging.info(f"Copied {copied} schemas to {year}")

    # Update BOD schema for historical years to include additional columns
    for year in args.years:
        # Add metadata columns that are present in 2022-2024 but might be missing in 2025
        metadata_columns = [
            {"mode": "NULLABLE", "name": "_source_columns", "type": "STRING"},
            {"mode": "NULLABLE", "name": "_source_api", "type": "STRING"},
            {"mode": "NULLABLE", "name": "_hash_source_cols", "type": "STRING"},
            {"mode": "NULLABLE", "name": "_hash_key", "type": "STRING"},
        ]

        for dataset in args.datasets:
            update_schema_for_year(dataset, year, add_columns=metadata_columns)

    logging.info("Schema generation complete!")


if __name__ == "__main__":
    main()
