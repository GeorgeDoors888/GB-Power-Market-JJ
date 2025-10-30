#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate schema files for historical BMRS data.

This script:
1. Samples data from each year (2022, 2023, 2024)
2. Extracts the schema for each dataset
3. Saves schema files in year-specific directories
4. Updates the ingest script to use year-specific schemas
"""

import argparse
import json
import logging
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd
import requests
from google.cloud import bigquery

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Constants
BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
TIMEOUT = (10, 90)  # (connect, read) timeout in seconds

# Define the datasets to process
DATASETS = ["BOD", "BOALF", "FREQ", "FUELINST", "MID", "MELS", "MILS", "PN", "QPN"]

# Sample date ranges for each year
SAMPLE_RANGES = {
    "2022": [
        ("2022-01-15", "2022-01-16"),
        ("2022-06-15", "2022-06-16"),
        ("2022-12-15", "2022-12-16"),
    ],
    "2023": [
        ("2023-01-15", "2023-01-16"),
        ("2023-06-15", "2023-06-16"),
        ("2023-12-15", "2023-12-16"),
    ],
    "2024": [
        ("2024-01-15", "2024-01-16"),
        ("2024-06-15", "2024-06-16"),
        ("2024-08-15", "2024-08-16"),
    ],
}


def _parse_iso_date(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
        # Support YYYY-MM-DD only
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _json_to_df(payload: dict) -> pd.DataFrame:
    """Convert JSON response to DataFrame."""
    if not payload or not isinstance(payload, dict):
        return pd.DataFrame()

    # Handle different API response formats
    data = None
    if "data" in payload and isinstance(payload["data"], list):
        data = payload["data"]
    elif "items" in payload and isinstance(payload["items"], list):
        data = payload["items"]
    elif "results" in payload and isinstance(payload["results"], list):
        data = payload["results"]

    if not data:
        return pd.DataFrame()

    return pd.json_normalize(data)


def _csv_to_df(csv_text: str) -> pd.DataFrame:
    """Convert CSV response to DataFrame."""
    if not csv_text or not csv_text.strip():
        return pd.DataFrame()

    try:
        return pd.read_csv(io.StringIO(csv_text))
    except Exception:
        return pd.DataFrame()


def fetch_sample_data(dataset: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch sample data for a dataset within a date range."""
    from_dt = _parse_iso_date(start_date)
    to_dt = _parse_iso_date(end_date)

    url = f"{BMRS_BASE}/{dataset}"
    params = {
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
    }

    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        if response.status_code == 200:
            try:
                payload = response.json()
                return _json_to_df(payload)
            except:
                return _csv_to_df(response.text)
    except Exception as e:
        logging.warning(f"Error fetching {dataset} for {start_date} to {end_date}: {e}")

    return pd.DataFrame()


def generate_schema_from_df(df: pd.DataFrame) -> List[Dict]:
    """Generate BigQuery schema from DataFrame."""
    schema = []

    if df.empty:
        return schema

    # Map pandas dtypes to BigQuery types
    type_mapping = {
        "object": "STRING",
        "int64": "INTEGER",
        "float64": "FLOAT",
        "bool": "BOOLEAN",
        "datetime64[ns]": "TIMESTAMP",
        "datetime64[ns, UTC]": "TIMESTAMP",
    }

    for col, dtype in df.dtypes.items():
        bq_type = type_mapping.get(str(dtype), "STRING")
        schema.append({"mode": "NULLABLE", "name": col, "type": bq_type})

    return schema


def save_schema(schema: List[Dict], year: str, dataset: str) -> None:
    """Save schema to a JSON file."""
    output_path = f"schemas/{year}/bmrs_{dataset.lower()}.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)
    logging.info(f"Saved schema for {dataset} ({year}) to {output_path}")


def process_dataset(dataset: str, year: str) -> None:
    """Process a dataset for a specific year."""
    logging.info(f"Processing {dataset} for {year}...")

    # Get sample ranges for the year
    date_ranges = SAMPLE_RANGES.get(year, [])
    if not date_ranges:
        logging.warning(f"No sample date ranges defined for {year}")
        return

    # Try each date range until we get data
    all_dfs = []
    for start_date, end_date in date_ranges:
        df = fetch_sample_data(dataset, start_date, end_date)
        if not df.empty:
            all_dfs.append(df)
            logging.info(
                f"Got {len(df)} rows for {dataset} from {start_date} to {end_date}"
            )

        # If we have enough data, stop fetching
        if sum(len(df) for df in all_dfs) >= 100:
            break

    # Combine all dataframes
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        # Generate and save schema
        schema = generate_schema_from_df(combined_df)
        if schema:
            save_schema(schema, year, dataset)
        else:
            logging.warning(f"Could not generate schema for {dataset} ({year})")
    else:
        logging.warning(f"No data found for {dataset} in {year}")


def check_existing_schemas(years: List[str], datasets: List[str]) -> None:
    """Check which schemas already exist."""
    for year in years:
        for dataset in datasets:
            path = f"schemas/{year}/bmrs_{dataset.lower()}.json"
            if os.path.exists(path):
                with open(path, "r") as f:
                    try:
                        schema = json.load(f)
                        logging.info(
                            f"Existing schema for {dataset} ({year}): {len(schema)} columns"
                        )
                    except json.JSONDecodeError:
                        logging.warning(f"Invalid schema file for {dataset} ({year})")


def generate_schema_loader_script() -> None:
    """Generate a helper script to load the appropriate schema based on year."""
    script_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

\"\"\"
Schema loader for year-specific BMRS schemas.
This module provides functions to load the appropriate schema for a dataset based on the year.
\"\"\"

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Base directory for schema files
SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")

def get_schema_for_year(dataset: str, year: int) -> Optional[List[Dict]]:
    \"\"\"
    Load the schema for a dataset for a specific year.
    Falls back to the most recent available schema if the exact year is not available.
    \"\"\"
    dataset = dataset.lower()

    # Try to load schema for the specific year
    year_dir = os.path.join(SCHEMA_DIR, str(year))
    schema_path = os.path.join(year_dir, f"bmrs_{dataset}.json")

    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            return json.load(f)

    # If not found, try to find the closest year
    available_years = []
    for y in os.listdir(SCHEMA_DIR):
        if y.isdigit() and os.path.isdir(os.path.join(SCHEMA_DIR, y)):
            y_int = int(y)
            schema_path = os.path.join(SCHEMA_DIR, y, f"bmrs_{dataset}.json")
            if os.path.exists(schema_path):
                available_years.append(y_int)

    if not available_years:
        return None

    # Find the closest year (prefer older schemas for older data)
    closest_year = None
    min_diff = float('inf')
    for y in available_years:
        diff = abs(y - year)
        if diff < min_diff or (diff == min_diff and y < closest_year):
            min_diff = diff
            closest_year = y

    if closest_year:
        schema_path = os.path.join(SCHEMA_DIR, str(closest_year), f"bmrs_{dataset}.json")
        with open(schema_path, "r") as f:
            return json.load(f)

    return None

def get_schema_for_date_range(dataset: str, start_date: datetime, end_date: datetime) -> Optional[List[Dict]]:
    \"\"\"
    Load the appropriate schema for a dataset based on a date range.
    Uses the schema for the year at the start of the range.
    \"\"\"
    year = start_date.year
    return get_schema_for_year(dataset, year)
"""

    with open("schema_loader.py", "w") as f:
        f.write(script_content)

    logging.info("Generated schema_loader.py")


def main():
    parser = argparse.ArgumentParser(
        description="Generate schema files for historical BMRS data"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        default=["2022", "2023", "2024"],
        help="Years to generate schemas for",
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=DATASETS,
        help="Datasets to generate schemas for",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Check existing schemas without generating new ones",
    )
    args = parser.parse_args()

    # Ensure schema directories exist
    for year in args.years:
        os.makedirs(f"schemas/{year}", exist_ok=True)

    if args.check_existing:
        check_existing_schemas(args.years, args.datasets)
        return

    # Process each dataset for each year
    for year in args.years:
        for dataset in args.datasets:
            process_dataset(dataset, year)

    # Generate helper script for loading schemas
    generate_schema_loader_script()

    logging.info("Schema generation complete")


if __name__ == "__main__":
    main()
