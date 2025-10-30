import os
from dotenv import load_dotenv
from pathlib import Path
import json
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List
import time
import pandas as pd
import requests
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Conflict
from io import StringIO

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets/{datasetCode}/data"
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"

# -----------------------------------------------------------------------------
# EMBEDDED DATASETS CONFIGURATION (60 datasets)
# -----------------------------------------------------------------------------
DATASETS = {
    "Insights": [
        {"code": "METADATA", "name": "Metadata (METADATA)"},
        {"code": "BOAL", "name": "BOAL (BOAL)"},
        {"code": "BOD", "name": "BOD (BOD)"},
        {"code": "DISBSAD", "name": "Balancing Services Adjustment Actions (DISBSAD)"},
        {"code": "FOU2T14D", "name": "FOU2T14D (FOU2T14D)"},
        {"code": "FOU2T3YW", "name": "FOU2T3YW (FOU2T3YW)"},
        {"code": "FOUT2T14D", "name": "FOUT2T14D (FOUT2T14D)"},
        {"code": "FREQ", "name": "Frequency (FREQ)"},
        {"code": "FUELHH", "name": "Generation by Fuel Type Half Hourly (FUELHH)"},
        {"code": "FUELINST", "name": "Generation by Fuel Type (FUELINST)"},
        {"code": "IMBALNGC", "name": "IMBALNGC (IMBALNGC)"},
        {"code": "INDDEM", "name": "Industrial Demand (INDDEM)"},
        {"code": "INDGEN", "name": "INDGEN (INDGEN)"},
        {"code": "INDO", "name": "Interconnectors Data (INDO)"},
        {"code": "ITSDO", "name": "ITSDO (ITSDO)"},
        {"code": "MELNGC", "name": "MELNGC (MELNGC)"},
        {"code": "MID", "name": "MID (MID)"},
        {"code": "MILS", "name": "MILS (MILS)"},
        {"code": "MELS", "name": "MELS (MELS)"},
        {"code": "MDP", "name": "MDP (MDP)"},
        {"code": "MDV", "name": "MDV (MDV)"},
        {"code": "MNZT", "name": "MNZT (MNZT)"},
        {"code": "MZT", "name": "MZT (MZT)"},
        {"code": "NETBSAD", "name": "NETBSAD (NETBSAD)"},
        {"code": "NDF", "name": "NDF (NDF)"},
        {"code": "NDFD", "name": "NDFD (NDFD)"},
        {"code": "NDFW", "name": "NDFW (NDFW)"},
        {"code": "NONBM", "name": "NONBM (NONBM)"},
        {"code": "NOU2T14D", "name": "NOU2T14D (NOU2T14D)"},
        {"code": "NOU2T3YW", "name": "NOU2T3YW (NOU2T3YW)"},
        {"code": "NTB", "name": "NTB (NTB)"},
        {"code": "NTO", "name": "NTO (NTO)"},
        {"code": "NDZ", "name": "NDZ (NDZ)"},
        {"code": "OCNMF3Y", "name": "OCNMF3Y (OCNMF3Y)"},
        {"code": "OCNMF3Y2", "name": "OCNMF3Y2 (OCNMF3Y2)"},
        {"code": "OCNMFD", "name": "OCNMFD (OCNMFD)"},
        {"code": "OCNMFD2", "name": "OCNMFD2 (OCNMFD2)"},
        {"code": "PN", "name": "PN (PN)"},
        {"code": "QAS", "name": "Quarterly Aggregated Supply (QAS)"},
        {"code": "QPN", "name": "QPN (QPN)"},
        {"code": "RDRE", "name": "RDRE (RDRE)"},
        {"code": "RDRI", "name": "RDRI (RDRI)"},
        {"code": "RURE", "name": "RURE (RURE)"},
        {"code": "RURI", "name": "RURI (RURI)"},
        {"code": "SEL", "name": "SEL (SEL)"},
        {"code": "SIL", "name": "SIL (SIL)"},
        {"code": "TEMP", "name": "Temperature (TEMP)"},
        {"code": "TSDF", "name": "TSDF (TSDF)"},
        {"code": "TSDFD", "name": "TSDFD (TSDFD)"},
        {"code": "TSDFW", "name": "TSDFW (TSDFW)"},
        {"code": "UOU2T14D", "name": "UOU2T14D (UOU2T14D)"},
        {"code": "UOU2T3YW", "name": "UOU2T3YW (UOU2T3YW)"},
        {"code": "WINDFOR", "name": "Wind Forecast (WINDFOR)"},
        {"code": "GENFUEL", "name": "Generation by Fuel Type Summary (GENFUEL)"},
        {"code": "DEMAND", "name": "Demand Summary (DEMAND)"},
        {"code": "INTERCON", "name": "Interconnector Flows Summary (INTERCON)"},
        {"code": "PRICES", "name": "Price Data (PRICES)"},
        {"code": "SYSTEM", "name": "System Data (SYSTEM)"},
        {"code": "EMISSIONS", "name": "Emissions Data (EMISSIONS)"},
        {"code": "GENINST", "name": "Generation by Fuel Type Instantaneous (GENINST)"},
        {"code": "BMRSFUEL", "name": "BMRS Fuel Type Data (BMRSFUEL)"},
        {"code": "FUELDAILY", "name": "Daily Fuel Mix (FUELDAILY)"},
        {"code": "GENDAILY", "name": "Daily Generation (GENDAILY)"},
        {"code": "GENMONTHLY", "name": "Monthly Generation (GENMONTHLY)"},
        {"code": "GENYEARLY", "name": "Yearly Generation (GENYEARLY)"},
        {"code": "PRICEHIST", "name": "Historical Prices (PRICEHIST)"},
        {"code": "DEMANDHIST", "name": "Historical Demand (DEMANDHIST)"},
        {"code": "INTERCONHIST", "name": "Historical Interconnector Flows (INTERCONHIST)"},
        {"code": "GENFUELHIST", "name": "Historical Fuel Mix (GENFUELHIST)"},
        {"code": "EMISSIONSHIST", "name": "Historical Emissions (EMISSIONSHIST)"},
    ]
}

# -----------------------------------------------------------------------------
# SETUP LOGGING
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# -----------------------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES AND API KEYS
# -----------------------------------------------------------------------------
env_path = Path(__file__).parent / "api.env"
if not env_path.exists():
    logging.error(f"api.env file not found at {env_path}")
    raise FileNotFoundError(f"api.env file not found at {env_path}")
load_dotenv(dotenv_path=env_path)

API_KEYS = []
for i in range(1, 21):
    key = os.getenv(f"BMRS_API_KEY_{i}")
    if key:
        API_KEYS.append(key)
if not API_KEYS:
    logging.error("No BMRS_API_KEY_* entries found in api.env. Please ensure it exists and is populated with up to 20 keys.")
    raise FileNotFoundError("api.env file missing or contains no API keys.")

api_index = 0

# -----------------------------------------------------------------------------
# BIGQUERY CLIENT INITIALIZATION
# -----------------------------------------------------------------------------
bq_client = bigquery.Client(project=PROJECT_ID)

def ensure_dataset():
    try:
        bq_client.get_dataset(DATASET_ID)
        logging.info(f"BigQuery dataset {DATASET_ID} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
        dataset.location = "europe-west2"
        try:
            bq_client.create_dataset(dataset)
            logging.info(f"Created BigQuery dataset: {DATASET_ID}")
        except Conflict:
            logging.info(f"BigQuery dataset {DATASET_ID} already exists (conflict).")

def ensure_table(table_name: str, schema: List[bigquery.SchemaField]):
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    try:
        bq_client.get_table(table_id)
        logging.info(f"BigQuery table {table_id} already exists.")
    except NotFound:
        table = bigquery.Table(table_id, schema=schema)
        # Partition on settlementDate if present
        if any(field.name == "settlementDate" for field in schema):
            table.time_partitioning = bigquery.TimePartitioning(field="settlementDate")
        try:
            bq_client.create_table(table)
            logging.info(f"Created BigQuery table: {table_id}")
        except Conflict:
            logging.info(f"BigQuery table {table_id} already exists (conflict).")

# -----------------------------------------------------------------------------
# DOWNLOAD DATA FROM API WITH RETRIES AND KEY ROTATION
# -----------------------------------------------------------------------------
def fetch_dataset(dataset_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    global api_index, API_KEYS
    url = BASE_URL.format(datasetCode=dataset_code)
    params = {
        "start": start_date,
        "end": end_date,
        "api_key": API_KEYS[api_index],
        "format": "json",
        "pageSize": 1000
    }

    all_data = []
    max_retries = 5
    backoff_base = 2.0

    while True:
        retries = 0
        while retries < max_retries:
            try:
                logging.info(f"Requesting URL: {url} | Params: {params}")
                r = requests.get(url, params=params, timeout=30)
                logging.debug(f"Response [{r.status_code}]: {r.text[:200]}")
                if r.status_code == 403:
                    # Rotate API key if possible
                    if api_index + 1 < len(API_KEYS):
                        api_index += 1
                        params["api_key"] = API_KEYS[api_index]
                        logging.warning(f"403 Forbidden: Switching to API key {api_index+1} due to rate limit.")
                        retries = 0
                        time.sleep(1)  # brief pause before retrying with new key
                        continue
                    else:
                        logging.error("403 Forbidden and no more API keys to rotate. Aborting.")
                        r.raise_for_status()
                if r.status_code == 404:
                    logging.error(f"Dataset {dataset_code} returned 404. URL: {r.url}")
                    logging.error(f"Response: {r.text}")
                    return pd.DataFrame()
                elif r.status_code >= 400 and r.status_code < 600:
                    # Retry for 4xx or 5xx except 403 and 404 handled above
                    retries += 1
                    wait_time = backoff_base ** retries
                    logging.warning(f"HTTP {r.status_code} error on dataset {dataset_code}. Retrying in {wait_time:.1f}s ({retries}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                r.raise_for_status()
                break
            except requests.RequestException as e:
                retries += 1
                wait_time = backoff_base ** retries
                logging.warning(f"Request exception on dataset {dataset_code}: {e}. Retrying in {wait_time:.1f}s ({retries}/{max_retries})")
                time.sleep(wait_time)
        else:
            logging.error(f"Failed to fetch dataset {dataset_code} after {max_retries} retries. Skipping.")
            return pd.DataFrame()

        payload = r.json()
        items = payload.get("data", [])
        if not items:
            # No data in this page, end pagination
            break

        all_data.extend(items)
        if not payload.get("nextPage"):
            break
        url = payload["nextPage"]
        params = {}  # nextPage URL already contains all params

        # To avoid overwhelming the API, pause briefly between page requests
        time.sleep(0.5)

    return pd.DataFrame(all_data)

# -----------------------------------------------------------------------------
# WRITE DATA TO BIGQUERY
# -----------------------------------------------------------------------------
def write_to_bigquery(df: pd.DataFrame, table_name: str):
    if df.empty:
        logging.warning(f"No data for {table_name}. Skipping upload.")
        return

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    logging.info(f"Uploading {len(df)} rows to {table_id}")
    bq_client.load_table_from_file(csv_buffer, table_id, job_config=job_config).result()

# -----------------------------------------------------------------------------
# MAIN INGESTION PIPELINE
# -----------------------------------------------------------------------------
def ingest_datasets(dataset: str, start: str, end: str):
    ensure_dataset()
    for group, entries in DATASETS.items():
        for ds in entries:
            if dataset != "ALL" and ds["code"] != dataset:
                continue
            logging.info(f"Starting ingestion for dataset {ds['code']} ({ds['name']})")

            df = fetch_dataset(ds["code"], start, end)
            if df.empty:
                logging.info(f"No data returned for dataset {ds['code']}. Skipping upload.")
                continue

            # Define schema dynamically from DataFrame columns, infer types as STRING for simplicity
            schema = []
            for col in df.columns:
                schema.append(bigquery.SchemaField(col, "STRING"))
            ensure_table(ds["code"], schema)

            try:
                write_to_bigquery(df, ds["code"])
                logging.info(f"Successfully ingested dataset {ds['code']}.")
            except Exception as e:
                logging.error(f"Failed to upload dataset {ds['code']} to BigQuery: {e}")

            # Pause between datasets to avoid overwhelming the API and rate limits
            time.sleep(2)

# -----------------------------------------------------------------------------
# ARGPARSE ENTRY POINT
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest Elexon Insights API datasets into BigQuery")
    parser.add_argument("--dataset", type=str, default="ALL", help="Dataset code or ALL (default: ALL)")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    ingest_datasets(args.dataset, args.start, args.end)
    logging.info("Pipeline finished successfully.")

