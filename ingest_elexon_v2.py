#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Elexon BMRS Data Ingestion Script v2

This script is designed for robust, large-scale historical data ingestion from the Elexon BMRS API
into Google BigQuery. It includes several key enhancements over previous versions:

1.  **Stateful Resumption**: The script maintains a progress log (`ingestion_progress_v2.json`)
    to track completed files. If the script is stopped and restarted, it will skip already
    processed files, preventing duplicate work and allowing for safe resumption of long-running jobs.

2.  **Explicit Schema Enforcement**: Instead of relying on BigQuery's `autodetect`, this script
    defines explicit schemas for each dataset. It performs data type conversions and cleaning
    *before* loading the data, ensuring data integrity and preventing ingestion failures due to
    type mismatches.

3.  **Targeted `_v2` Tables**: All data is loaded into new tables with a `_v2` suffix (e.g., `bmrs_bod_v2`).
    This isolates the new, clean data from the old tables, allowing for a safe and controlled migration.

4.  **Configurable BigQuery Location**: The script explicitly sets the BigQuery dataset location to
    `europe-west2`, ensuring all tables are created in the correct region.

5.  **Detailed Progress Reporting**: The script calculates the total number of files to be processed
    and provides real-time progress updates in the terminal, including percentage complete and
    estimated time remaining.

6.  **Robust Error Handling**: The script includes enhanced error handling to gracefully manage
    API timeouts, bad responses, and data processing errors. It logs failed files to
    `failed_ingestions_v2.log` for later review and reprocessing.

Usage:
    python ingest_elexon_v2.py --start YYYY-MM-DD --end YYYY-MM-DD [--only DATASET1,DATASET2]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd
import requests
from google.api_core.exceptions import BadRequest, Conflict, DeadlineExceeded, NotFound
from google.cloud import bigquery
from tqdm import tqdm

# --- V2 Configuration ---
BQ_LOCATION = "europe-west2"
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"
EUROPE_WEST2_DIR = "europe_west2"
DATA_CACHE_DIR = os.path.join(EUROPE_WEST2_DIR, "raw_data")
PROGRESS_LOG_FILE = os.path.join(EUROPE_WEST2_DIR, "ingestion_progress_v2.json")
FAILED_LOG_FILE = os.path.join(EUROPE_WEST2_DIR, "failed_ingestions_v2.log")
TABLE_SUFFIX = "_v2"

# --- General Configuration ---
BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.5
TIMEOUT = (10, 60)

# --- Per-dataset max window sizes ---
CHUNK_RULES = {
    "BOD": "1h",
    "B1770": "1d",
    "BOALF": "1d",
    "NETBSAD": "1d",
    "DISBSAD": "1d",
    "IMBALNGC": "7d",
    "PN": "1d",
    "QPN": "1d",
    "QAS": "1d",
    "RDRI": "1d",
    "FREQ": "1d",
    "FUELINST": "1d",
    "FUELHH": "1d",
    "TEMP": "7d",
    "B1610": "7d",
    "TSDF": "7d",
    "ITSDO": "7d",
    "MID": "7d",
    "MILS": "1d",
    "MELS": "1d",
}

# --- BigQuery Schemas (v2) ---
# Add explicit schemas here as needed. This is a sample for 'BOD'.
# The full implementation would have a schema for each dataset.
SCHEMAS = {
    "BOD": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE", "REQUIRED"),
        bigquery.SchemaField("settlementPeriod", "INT64", "REQUIRED"),
        bigquery.SchemaField("timeFrom", "TIMESTAMP"),
        bigquery.SchemaField("timeTo", "TIMESTAMP"),
        bigquery.SchemaField("levelFrom", "INT64"),
        bigquery.SchemaField("levelTo", "INT64"),
        bigquery.SchemaField("bidPrice", "NUMERIC"),
        bigquery.SchemaField("offerPrice", "NUMERIC"),
        bigquery.SchemaField("nationalGridBmUnit", "STRING"),
        bigquery.SchemaField("bmUnit", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "B1770": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("resourceName", "STRING"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("imbalanceQuantity", "NUMERIC"),
        bigquery.SchemaField("imbalancePrice", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "BOALF": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("bmUnit", "STRING"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("timeFrom", "TIMESTAMP"),
        bigquery.SchemaField("timeTo", "TIMESTAMP"),
        bigquery.SchemaField("acceptanceNumber", "INT64"),
        bigquery.SchemaField("acceptanceTime", "TIMESTAMP"),
        bigquery.SchemaField("deemedBoFlag", "STRING"),
        bigquery.SchemaField("soFlag", "STRING"),
        bigquery.SchemaField("storFlag", "STRING"),
        bigquery.SchemaField("rrFlag", "STRING"),
        bigquery.SchemaField("levelFrom", "NUMERIC"),
        bigquery.SchemaField("levelTo", "NUMERIC"),
        bigquery.SchemaField("nationalGridBmUnit", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "NETBSAD": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("netImbalanceVolume", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "DISBSAD": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE", "REQUIRED"),
        bigquery.SchemaField("settlementPeriod", "INT64", "REQUIRED"),
        bigquery.SchemaField("systemSellPrice", "NUMERIC"),
        bigquery.SchemaField("systemBuyPrice", "NUMERIC"),
        bigquery.SchemaField("priceDerivationCode", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "IMBALNGC": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("totalSystemImbalance", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "PN": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("bmUnitID", "STRING"),
        bigquery.SchemaField("pnLevel", "NUMERIC"),
        bigquery.SchemaField("timeFrom", "TIMESTAMP"),
        bigquery.SchemaField("timeTo", "TIMESTAMP"),
        bigquery.SchemaField("nationalGridBmUnit", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "QPN": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("bmUnitID", "STRING"),
        bigquery.SchemaField("timeFrom", "TIMESTAMP"),
        bigquery.SchemaField("timeTo", "TIMESTAMP"),
        bigquery.SchemaField("level", "NUMERIC"),
        bigquery.SchemaField("nationalGridBmUnit", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "QAS": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("bmUnit", "STRING"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("quantity", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "RDRI": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("bmUnitId", "STRING"),
        bigquery.SchemaField("dataType", "STRING"),
        bigquery.SchemaField("data", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "FREQ": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("reportSnapshotTime", "TIMESTAMP"),
        bigquery.SchemaField("spotTime", "TIMESTAMP"),
        bigquery.SchemaField("frequency", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "FUELINST": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("ccgt", "INT64"),
        bigquery.SchemaField("oil", "INT64"),
        bigquery.SchemaField("coal", "INT64"),
        bigquery.SchemaField("nuclear", "INT64"),
        bigquery.SchemaField("wind", "INT64"),
        bigquery.SchemaField("ps", "INT64"),
        bigquery.SchemaField("npshyd", "INT64"),
        bigquery.SchemaField("ocgt", "INT64"),
        bigquery.SchemaField("other", "INT64"),
        bigquery.SchemaField("intfr", "INT64"),
        bigquery.SchemaField("intirl", "INT64"),
        bigquery.SchemaField("intned", "INT64"),
        bigquery.SchemaField("intew", "INT64"),
        bigquery.SchemaField("intnem", "INT64"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "FUELHH": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("ccgt", "INT64"),
        bigquery.SchemaField("oil", "INT64"),
        bigquery.SchemaField("coal", "INT64"),
        bigquery.SchemaField("nuclear", "INT64"),
        bigquery.SchemaField("wind", "INT64"),
        bigquery.SchemaField("ps", "INT64"),
        bigquery.SchemaField("npshyd", "INT64"),
        bigquery.SchemaField("ocgt", "INT64"),
        bigquery.SchemaField("other", "INT64"),
        bigquery.SchemaField("intfr", "INT64"),
        bigquery.SchemaField("intirl", "INT64"),
        bigquery.SchemaField("intned", "INT64"),
        bigquery.SchemaField("intew", "INT64"),
        bigquery.SchemaField("intnem", "INT64"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "TEMP": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("publishTime", "TIMESTAMP"),
        bigquery.SchemaField("temperature", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "B1610": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("quantity", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "TSDF": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("systemTotal", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "ITSDO": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("systemDemand", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "MID": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("marketIndexPrice", "NUMERIC"),
        bigquery.SchemaField("marketIndexVolume", "NUMERIC"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "MILS": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("systemSellPrice", "NUMERIC"),
        bigquery.SchemaField("systemBuyPrice", "NUMERIC"),
        bigquery.SchemaField("priceDerivationCode", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
    "MELS": [
        bigquery.SchemaField("dataset", "STRING", "REQUIRED"),
        bigquery.SchemaField("settlementDate", "DATE"),
        bigquery.SchemaField("settlementPeriod", "INT64"),
        bigquery.SchemaField("systemSellPrice", "NUMERIC"),
        bigquery.SchemaField("systemBuyPrice", "NUMERIC"),
        bigquery.SchemaField("priceDerivationCode", "STRING"),
        bigquery.SchemaField("ingested_utc", "TIMESTAMP", "REQUIRED"),
        bigquery.SchemaField("file_hash", "STRING", "REQUIRED"),
    ],
}

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
tqdm_handler = logging.StreamHandler(sys.stdout)
tqdm_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger().addHandler(tqdm_handler)


# --- State Management ---
def load_progress() -> dict:
    if not os.path.exists(PROGRESS_LOG_FILE):
        return {}
    with open(PROGRESS_LOG_FILE, "r") as f:
        return json.load(f)


def save_progress(progress: dict):
    with open(PROGRESS_LOG_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def log_failed_ingestion(dataset: str, window_start: str, reason: str):
    with open(FAILED_LOG_FILE, "a") as f:
        f.write(
            f"{datetime.now(timezone.utc).isoformat()},{dataset},{window_start},{reason}\n"
        )


def save_raw_data(dataset: str, from_dt: datetime, content: bytes):
    """Saves the raw API response to a local file."""
    cache_path = os.path.join(DATA_CACHE_DIR, dataset)
    os.makedirs(cache_path, exist_ok=True)
    file_name = f"{from_dt.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    file_path = os.path.join(cache_path, file_name)
    with open(file_path, "wb") as f:
        f.write(content)
    logging.info(f"Saved raw data to {file_path}")


# --- BigQuery Helpers ---
def get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=BQ_PROJECT)


def ensure_bq_dataset(client: bigquery.Client):
    dataset_id = f"{client.project}.{BQ_DATASET}"
    try:
        client.get_dataset(dataset_id)
    except NotFound:
        dataset = bigquery.Dataset(dataset_id)
        dataset.location = BQ_LOCATION
        client.create_dataset(dataset, exists_ok=True)
        logging.info(f"Created BigQuery dataset {dataset_id} in {BQ_LOCATION}")


def get_table_id(dataset: str) -> str:
    return f"{BQ_PROJECT}.{BQ_DATASET}.bmrs_{dataset.lower()}{TABLE_SUFFIX}"


def transform_and_load_to_bq(
    client: bigquery.Client, df: pd.DataFrame, dataset: str, file_hash: str
):
    table_id = get_table_id(dataset)
    schema = SCHEMAS.get(dataset)
    if not schema:
        logging.error(f"No schema defined for dataset {dataset}. Skipping load.")
        return

    # --- Data Transformation Step ---
    # This is where you apply the logic from BIGQUERY_SCHEMA_UPDATE_GUIDE.md
    for field in schema:
        if field.name not in df.columns:
            continue

        # Handle Timestamps and Dates
        if field.field_type in ("TIMESTAMP", "DATETIME"):
            df[field.name] = pd.to_datetime(df[field.name], errors="coerce", utc=True)
        elif field.field_type == "DATE":
            df[field.name] = pd.to_datetime(df[field.name], errors="coerce").dt.date

        # Handle Numerics
        elif field.field_type in ("NUMERIC", "FLOAT64", "INT64"):
            df[field.name] = pd.to_numeric(df[field.name], errors="coerce")
            if field.field_type == "INT64":
                # Coerce to nullable integer type before filling NA
                df[field.name] = df[field.name].astype("Int64")

    # Add metadata
    df["ingested_utc"] = datetime.now(timezone.utc)
    df["file_hash"] = file_hash

    # Ensure all columns exist, fill missing with None
    for field in schema:
        if field.name not in df.columns:
            df[field.name] = None

    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(schema=schema, write_disposition="WRITE_APPEND")
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logging.info(f"Successfully loaded {len(df)} rows to {table_id}")
    except Exception as e:
        logging.error(f"Failed to load data to {table_id}: {e}")
        log_failed_ingestion(dataset, "batch_load", str(e))


# --- Main Ingestion Logic ---
def fetch_bmrs_data(
    dataset: str, from_dt: datetime, to_dt: datetime
) -> Optional[Tuple[pd.DataFrame, str]]:
    url = f"{BMRS_BASE}/{dataset}"
    params = {
        "from": from_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": to_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json",
    }
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()

        # Save raw data before processing
        save_raw_data(dataset, from_dt, response.content)

        # Memory-efficient hashing
        file_hash = hashlib.sha256(response.content).hexdigest()

        data = response.json()
        df = pd.json_normalize(data.get("data", []))
        return df, file_hash

    except requests.RequestException as e:
        logging.error(f"API request failed for {dataset} ({from_dt}): {e}")
        log_failed_ingestion(dataset, from_dt.isoformat(), str(e))
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON for {dataset} ({from_dt}): {e}")
        log_failed_ingestion(dataset, from_dt.isoformat(), "JSONDecodeError")
        return None


def main(args):
    start_date = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end_date = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    datasets_to_ingest = args.only.split(",") if args.only else list(CHUNK_RULES.keys())

    client = get_bq_client()
    ensure_bq_dataset(client)
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    progress = load_progress()

    # --- Calculate Total Work ---
    tasks = []
    for dataset in datasets_to_ingest:
        max_window = pd.to_timedelta(CHUNK_RULES.get(dataset, "7d"))
        current = end_date
        while current > start_date:
            window_start = max(current - max_window, start_date)
            tasks.append((dataset, window_start, current))
            current = window_start

    logging.info(f"Planning to process {len(tasks)} total files.")
    tasks.reverse()

    # --- Execute Ingestion ---
    with tqdm(total=len(tasks), desc="Overall Progress") as pbar:
        for dataset, window_start, window_end in tasks:
            pbar.set_description(f"Processing {dataset} {window_start.date()}")

            # Check progress log
            task_id = f"{dataset}_{window_start.isoformat()}"
            if progress.get(task_id) == "completed":
                logging.info(f"Skipping already completed task: {task_id}")
                pbar.update(1)
                continue

            # Fetch data
            fetch_result = fetch_bmrs_data(dataset, window_start, window_end)
            if not fetch_result:
                pbar.update(1)
                continue

            df, file_hash = fetch_result

            if df.empty:
                logging.info(f"No data for {task_id}, marking as complete.")
                progress[task_id] = "completed"
                save_progress(progress)
                pbar.update(1)
                continue

            # Transform and load
            transform_and_load_to_bq(client, df, dataset, file_hash)

            # Update progress
            progress[task_id] = "completed"
            save_progress(progress)
            pbar.update(1)

    logging.info("Ingestion run completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Elexon BMRS Ingestion Script v2")
    parser.add_argument(
        "--start", required=True, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument("--only", help="Comma-separated list of datasets to ingest")

    args = parser.parse_args()
    main(args)
