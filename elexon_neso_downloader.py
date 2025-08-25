"""
Unified Elexon & NESO Data Downloader and BigQuery Ingestor

- Fetches all Elexon (via ElexonDataPortal) and NESO (CKAN/Datastore API) data in parallel
- Uploads directly to BigQuery (no local storage)
- Estimates download time and logs progress
- Uses service account authentication

Requirements:
- pip install ElexonDataPortal google-cloud-bigquery requests tqdm
- Set GOOGLE_APPLICATION_CREDENTIALS to your service account key JSON

Usage:
    python elexon_neso_downloader.py
"""

import concurrent.futures
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List

import requests
from dateutil.relativedelta import relativedelta
from ElexonDataPortal import api
from google.cloud import bigquery
from tqdm import tqdm

# --- CONFIG ---
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "jibber-jabber-knowledge")
BQ_DATASET = os.environ.get("BQ_DATASET", "uk_energy_prod")
ELEXON_TABLE = "elexon_data"  # Change as needed
NESO_TABLE = "neso_data"  # Change as needed

# --- NESO API CONFIG ---
# Official NESO API base URL (see https://www.neso.energy/applications-portals-and-apis)
NESO_BASE_URL = "https://api.neso.energy"  # Update with correct endpoint as needed
# Example endpoints (replace with actual endpoints/resources from NESO API docs)
NESO_RESOURCES = [
    # WARNING: Replace with actual NESO API endpoints or resource IDs
    {"name": "carbon_intensity", "endpoint": "/carbon-intensity"},
    {"name": "demand_forecasts", "endpoint": "/demand-forecast"},
    # Add more as needed
]
START_YEAR = 2016


# --- Load Elexon API Key from api.env ---
def load_api_key(env_path="old_project/api.env"):
    with open(env_path) as f:
        for line in f:
            if line.startswith("BMRS_API_KEY_1="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError("BMRS_API_KEY_1 not found in api.env")


# --- LOGGING ---
LOG_FILE = "elexon_neso_downloader.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    ],
)
logger = logging.getLogger("elexon-neso-downloader")

# --- BIGQUERY CLIENT ---
bq_client = bigquery.Client(project=PROJECT_ID)


def estimate_time(start, end, n_items, label):
    elapsed = time.time() - start
    if n_items == 0:
        return "?"
    rate = elapsed / n_items
    remaining = (end - n_items) * rate
    return f"{remaining/60:.1f} min remaining for {label}"


# --- ELEXON DOWNLOADER ---
def fetch_elexon_data(row_limit=None):
    logger.info("Fetching all Elexon datasets (2016–present) from Insights API...")
    import httpx
    api_key = load_api_key()
    base_url = os.environ.get("INSIGHTS_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1/")
    headers = {"x-api-key": api_key}
    datasets = [
        {"name": "demand_outturn", "endpoint": "demand/outturn"},
        {"name": "generation_outturn", "endpoint": "generation/outturn"},
        {"name": "system_warnings", "endpoint": "datasets/SYSWARN"},
        {"name": "system_frequency", "endpoint": "system/frequency"},
        {"name": "rolling_demand", "endpoint": "demand/rollingSystemDemand"},
    ]
    start_date = f"{START_YEAR}-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")
    all_results = {}
    with httpx.Client(timeout=60) as client:
        for ds in tqdm(datasets, desc="Elexon Insights datasets"):
            url = f"{base_url.rstrip('/')}/{ds['endpoint']}"
            params = {"from": start_date, "to": end_date, "format": "json", "apiKey": api_key}
            try:
                logger.info(f"Fetching {ds['name']} from {url}")
                resp = client.get(url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                records = data.get("data") or data.get("result", {}).get("records", [])
                if records:
                    if row_limit:
                        records = records[:row_limit]
                    all_results[ds["name"]] = records
                    logger.info(f"Fetched {len(records)} rows for {ds['name']}")
                else:
                    logger.info(f"No data for {ds['name']}")
            except Exception as e:
                logger.error(f"Failed to fetch {ds['name']}: {e}", exc_info=True)
            logger.info(f"Progress: {len(all_results)}/{len(datasets)} datasets complete.")
    logger.info(f"Fetched data for {len(all_results)} Elexon datasets.")
    return all_results


# --- NESO DOWNLOADER ---
def fetch_neso_data():
    logger.info("Smoke test: Fetching all NESO datasets and up to 100 records from each resource for the last month...")
    CKAN_BASE = "https://api.neso.energy/api/3/action"
    all_rows = []
    try:
        # Step 1: List all datasets
        pkg_list_url = f"{CKAN_BASE}/package_list"
        resp = requests.get(pkg_list_url, timeout=30)
        resp.raise_for_status()
        dataset_names = resp.json()["result"]
        logger.info(f"Found {len(dataset_names)} NESO datasets.")
        # Step 2: For each dataset, get metadata and resources
        for ds_name in tqdm(dataset_names, desc="NESO datasets"):
            pkg_show_url = f"{CKAN_BASE}/package_show?id={ds_name}"
            try:
                ds_resp = requests.get(pkg_show_url, timeout=30)
                ds_resp.raise_for_status()
                ds_info = ds_resp.json()["result"]
                for resource in ds_info.get("resources", []):
                    res_id = resource.get("id")
                    res_name = resource.get("name", res_id)
                    # Step 3: Check if resource is a CKAN datastore (datastore_active)
                    try:
                        res_show_url = f"{CKAN_BASE}/resource_show?id={res_id}"
                        res_show_resp = requests.get(res_show_url, timeout=15)
                        res_show_resp.raise_for_status()
                        res_meta = res_show_resp.json()["result"]
                        if res_meta.get("datastore_active"):
                            ds_url = f"{CKAN_BASE}/datastore_search?resource_id={res_id}&limit=100"
                            try:
                                r = requests.get(ds_url, timeout=30)
                                r.raise_for_status()
                                data = r.json()
                                records = data.get("result", {}).get("records", [])
                                if records:
                                    logger.info(f"Fetched {len(records)} rows for NESO resource {res_name}")
                                    all_rows.extend(records)
                                else:
                                    logger.info(f"No data for NESO resource {res_name}")
                            except Exception as e:
                                logger.warning(f"Failed to fetch records for NESO resource {res_name}: {e}")
                        else:
                            # Not a datastore resource, try to fetch file (CSV, XLSX, etc.)
                            url = res_meta.get("url")
                            if url:
                                try:
                                    file_resp = requests.get(url, timeout=30)
                                    if file_resp.status_code == 404:
                                        logger.info(f"File resource 404 for {res_name} ({url})")
                                    elif file_resp.ok:
                                        logger.info(f"File resource available for {res_name} ({url}), skipping ingest.")
                                    else:
                                        logger.warning(f"File resource error for {res_name} ({url}): {file_resp.status_code}")
                                except Exception as e:
                                    logger.warning(f"Failed to fetch file resource for {res_name}: {e}")
                            else:
                                logger.info(f"Resource {res_name} has no url and is not a datastore.")
                    except Exception as e:
                        logger.warning(f"Failed to check resource_show for {res_name}: {e}")
            except Exception as e:
                logger.warning(f"Failed to get metadata for NESO dataset {ds_name}: {e}")
    except Exception as e:
        logger.error(f"Failed to list NESO datasets: {e}", exc_info=True)
    logger.info(f"Fetched {len(all_rows)} NESO records (smoke test).")
    return all_rows


# --- BIGQUERY UPLOAD ---
def upload_to_bigquery(table_name: str, rows: List[dict]):
    if not rows:
        logger.warning(f"No data to upload for {table_name}")
        return
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{table_name}"
    logger.info(f"Uploading {len(rows)} rows to {table_id}...")
    try:
        errors = bq_client.insert_rows_json(table_id, rows)
        if errors:
            logger.error(f"BigQuery upload errors: {errors}")
        else:
            logger.info(f"Upload to {table_id} complete.")
    except Exception as e:
        logger.error(f"Failed to upload to BigQuery table {table_name}: {e}", exc_info=True)


# --- MAIN ---
def main():
    start_time = time.time()
    try:
        # Set row_limit to a small number (e.g. 100) for fast testing, or None for full run
        row_limit = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            fut_elexon = executor.submit(fetch_elexon_data, row_limit)
            fut_neso = executor.submit(fetch_neso_data)
            # Elexon: upload each dataset to its own table
            logger.info("Waiting for Elexon download...")
            elexon_results = fut_elexon.result()
            for method_name, rows in elexon_results.items():
                table = method_name.lower()
                logger.info(f"Uploading Elexon dataset {method_name} to table {table}...")
                upload_start = time.time()
                upload_to_bigquery(table, rows)
                logger.info(f"Elexon {method_name} upload took {time.time() - upload_start:.1f}s")
            # NESO: upload all to one table as before
            logger.info("Waiting for NESO download...")
            neso_rows = fut_neso.result()
            logger.info("Uploading NESO data...")
            upload_start = time.time()
            upload_to_bigquery(NESO_TABLE, neso_rows)
            logger.info(f"NESO upload took {time.time() - upload_start:.1f}s")
        logger.info(f"All done in {time.time() - start_time:.1f}s")
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()
