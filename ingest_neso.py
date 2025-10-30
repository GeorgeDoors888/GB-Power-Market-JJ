#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NESO Data Discoverability and Ingestion Script

- Discovers all available datasets from the NESO CKAN API.
- For each dataset, checks its resources to see if they are available via the machine-readable Datastore API.
- Fetches a small sample from each available Datastore resource to confirm access.
- Logs a summary of which datasets are available, which are file-only, and which failed.
- This script is designed to replace the NESO portion of `elexon_neso_downloader.py` with a more robust, auto-discovery approach.

Requirements:
- pip install requests tqdm pandas google-cloud-bigquery

Usage:
    # Discover and sample all NESO datasets
    python ingest_neso.py

    # Discover, sample, and ingest the first 1000 rows of specified datasets to BigQuery
    python ingest_neso.py --only "Real-Time Wind-Solar Data,System Frequency Data" --ingest --limit 1000
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd
import requests
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
from tqdm import tqdm

# --- CONFIG ---
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_prod"
NESO_CKAN_BASE = "https://api.neso.energy/api/3/action"
TIMEOUT = (10, 60)  # (connect, read) timeout

# --- LOGGING ---
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)

def _setup_logger(log_level: str):
    log = logging.getLogger()
    log.setLevel(getattr(logging, log_level.upper()))
    if not log.handlers:
        handler = TqdmLoggingHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        log.addHandler(handler)

# --- HELPERS ---
def _safe_table_name(name: str) -> str:
    """Converts a dataset name to a BQ-safe table name."""
    return f"neso_{name.lower().replace('-', '_').replace(' ', '_')}"

def _load_dataframe(client: bigquery.Client, df: pd.DataFrame, table_id: str):
    if df is None or df.empty:
        return
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Overwrite table with fresh data
        autodetect=True,
    )
    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        logging.info(f"✅ Loaded {len(df)} rows to {table_id}")
    except Exception as e:
        logging.error(f"❌ BQ load failed for {table_id}: {e}")
        raise

@dataclass
class NesoResource:
    id: str
    name: str
    dataset_name: str
    is_datastore: bool = False
    url: str | None = None
    error: str | None = None

def discover_neso_datasets() -> list[NesoResource]:
    """Discovers all datasets and their resources from the NESO CKAN API."""
    resources = []
    logging.info("Discovering NESO datasets from CKAN API...")
    try:
        # 1. Get list of all dataset names
        pkg_list_url = f"{NESO_CKAN_BASE}/package_list"
        resp = requests.get(pkg_list_url, timeout=TIMEOUT)
        resp.raise_for_status()
        dataset_names = resp.json()["result"]
        logging.info(f"Found {len(dataset_names)} NESO datasets.")

        # 2. Get details for each dataset
        for name in tqdm(dataset_names, desc="Discovering Resources", unit="dataset"):
            pkg_show_url = f"{NESO_CKAN_BASE}/package_show?id={name}"
            try:
                ds_resp = requests.get(pkg_show_url, timeout=TIMEOUT)
                ds_resp.raise_for_status()
                ds_info = ds_resp.json()["result"]
                for res_meta in ds_info.get("resources", []):
                    res = NesoResource(
                        id=res_meta.get("id"),
                        name=res_meta.get("name", res_meta.get("id")),
                        dataset_name=name,
                        is_datastore=res_meta.get("datastore_active", False),
                        url=res_meta.get("url")
                    )
                    resources.append(res)
            except Exception as e:
                logging.error(f"Failed to get metadata for dataset '{name}': {e}")
                resources.append(NesoResource(id=name, name=name, dataset_name=name, error=str(e)))

    except Exception as e:
        logging.critical(f"Failed to list NESO datasets, cannot proceed: {e}")
    return resources

def sample_and_ingest_resources(resources: list[NesoResource], bq_client: bigquery.Client | None, limit: int):
    """Samples or ingests data from datastore-enabled resources."""
    datastore_resources = [r for r in resources if r.is_datastore and not r.error]
    logging.info(f"Found {len(datastore_resources)} machine-readable (Datastore) resources to process.")

    for res in tqdm(datastore_resources, desc="Processing Datastore Resources", unit="resource"):
        url = f"{NESO_CKAN_BASE}/datastore_search?resource_id={res.id}&limit={limit}"
        try:
            resp = requests.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json().get("result", {}).get("records", [])
            if not data:
                logging.info(f"  - {res.dataset_name} / {res.name}: No records returned.")
                continue

            df = pd.json_normalize(data)
            logging.info(f"  - {res.dataset_name} / {res.name}: Fetched {len(df)} rows.")

            if bq_client:
                table_name = _safe_table_name(res.dataset_name)
                table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"
                _load_dataframe(bq_client, df, table_id)

        except Exception as e:
            logging.error(f"  - {res.dataset_name} / {res.name}: Failed to fetch/ingest: {e}")

def main():
    parser = argparse.ArgumentParser(description="NESO Data Discoverability and Ingestion Tool")
    parser.add_argument("--only", help="Comma-separated list of dataset names to process (e.g. 'System Frequency Data').")
    parser.add_argument("--ingest", action="store_true", help="If set, ingest data to BigQuery. Otherwise, just sample.")
    parser.add_argument("--limit", type=int, default=5, help="Number of rows to fetch per resource.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    _setup_logger(args.log_level)

    all_resources = discover_neso_datasets()

    # Filter resources if --only is provided
    resources_to_process = all_resources
    if args.only:
        only_set = {s.strip() for s in args.only.split(",")}
        resources_to_process = [r for r in all_resources if r.dataset_name in only_set]
        logging.info(f"Filtered to {len(resources_to_process)} resources based on --only flag.")

    # Initialize BQ client only if ingesting
    bq_client = None
    if args.ingest:
        gac = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not gac or not os.path.exists(gac):
            logging.error("GOOGLE_APPLICATION_CREDENTIALS must be set to an existing file for ingestion.")
            sys.exit(1)
        bq_client = bigquery.Client(project=BQ_PROJECT)
        logging.info(f"BigQuery client initialized for project {BQ_PROJECT}. Ingestion is ENABLED.")
    else:
        logging.info("Running in discovery-only mode. No data will be written to BigQuery.")

    sample_and_ingest_resources(resources_to_process, bq_client, args.limit)

    # Final summary
    logging.info("\n--- Discovery Summary ---")
    datastore_count = sum(1 for r in all_resources if r.is_datastore)
    file_count = sum(1 for r in all_resources if not r.is_datastore and r.url)
    error_count = sum(1 for r in all_resources if r.error)
    logging.info(f"Total Datasets Found: {len(set(r.dataset_name for r in all_resources))}")
    logging.info(f"Total Resources Found: {len(all_resources)}")
    logging.info(f"  - Machine-Readable (Datastore): {datastore_count}")
    logging.info(f"  - File-Only: {file_count}")
    logging.info(f"  - Errors: {error_count}")
    logging.info("-------------------------\n")

if __name__ == "__main__":
    main()
