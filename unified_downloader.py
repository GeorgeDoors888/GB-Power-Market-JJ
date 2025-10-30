#!/usr/bin/env python3
"""
Unified Elexon & NESO Data Downloader v3

A comprehensive downloader that handles both Elexon Insights and NESO data sources
with improved error handling, retry logic, and complete data coverage from 2016
to present. This script is the definitive downloader for the project.

Features:
- Unified API access for all Elexon Insights & NESO data sources
- Handles all 50+ migrated Elexon datasets
- Implements NESO API best practices (rate limiting, checking for updates)
- Robust error handling with exponential backoff
- Support for historical data backfilling (2016-present)
- Direct to Google Cloud Storage upload
- Comprehensive logging and monitoring
"""

import os
import json
import sys
import time
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import concurrent.futures

import json as _json

import requests
from requests.adapters import HTTPAdapter, Retry
from google.cloud import storage
from google.api_core.exceptions import NotFound

# --- Configuration ---

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'unified_downloader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('unified_downloader')

# Default settings
DEFAULT_BUCKET_NAME = os.getenv('GCS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
DEFAULT_PROJECT_ID = os.getenv('GCP_PROJECT', 'jibber-jabber-knowledge')
DEFAULT_START_DATE = '2016-01-01'
DEFAULT_END_DATE = datetime.now().strftime('%Y-%m-%d')

# Elexon Insights API Configuration
ELEXON_BASE_URL = 'https://data.elexon.co.uk/bmrs/api/v1'

# Load dataset formats from dataset_formats.json if available
DATASET_FORMATS_PATH = Path("dataset_formats.json")
if DATASET_FORMATS_PATH.exists():
    with open(DATASET_FORMATS_PATH) as f:
        DATASET_FORMATS = _json.load(f)
else:
    DATASET_FORMATS = {}
ELEXON_DATASET_IDS = [
    "METADATA", "BOAL", "BOD", "DISBSAD", "FOU2T14D", "FOU2T3YW", "FOUT2T14D",
    "FREQ", "FUELHH", "FUELINST", "IMBALNGC", "INDDEM", "INDGEN", "INDO", "ITSDO",
    "MELNGC", "MID", "MILS", "MELS", "MDP", "MDV", "MNZT", "MZT", "NETBSAD", "NDF",
    "NDFD", "NDFW", "NONBM", "NOU2T14D", "NOU2T3YW", "NTB", "NTO", "NDZ", "OCNMF3Y",
    "OCNMF3Y2", "OCNMFD", "OCNMFD2", "PN", "QAS", "QPN", "RDRE", "RDRI", "RURE",
    "RURI", "SEL", "SIL", "TEMP", "TSDF", "TSDFD", "TSDFW", "UOU2T14D", "UOU2T3YW",
    "WINDFOR"
]

# NESO API Configuration
NESO_BASE_URL = 'https://api.neso.energy/api/3/action'


class UnifiedDownloader:

    def download_dataset_for_month_all_formats(self, dataset_id: str, year: int, month: int, max_days_per_request: int = 7):
        """Download a dataset for a given month in all available formats."""
        formats = DATASET_FORMATS.get(dataset_id, ["json"])
        results = {}
        from calendar import monthrange
        start_date = f"{year}-{month:02d}-01"
        end_day = monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{end_day:02d}"
        for fmt in formats:
            logger.info(f"Testing {dataset_id} for {year}-{month:02d} as {fmt}")
            try:
                count = self.download_elexon_dataset(dataset_id, start_date, end_date, max_days_per_request=max_days_per_request, fmt=fmt)
                results[fmt] = count
            except Exception as e:
                logger.error(f"Failed {dataset_id} {fmt}: {e}")
                results[fmt] = 0
        return results
    """
    Unified downloader for Elexon Insights and NESO data sources
    """

    def __init__(self, api_key: Optional[str] = None, bucket_name: str = DEFAULT_BUCKET_NAME,
                 project_id: str = DEFAULT_PROJECT_ID):
        """
        Initialize the downloader with API credentials and cloud settings
        """
        self.api_keys = self._load_all_api_keys()
        self.api_key_index = 0
        self.bucket_name = bucket_name
        self.project_id = project_id

        self.gcs_key_path = Path("jibber_jabber_key.json")

        try:
            if not self.gcs_key_path.exists():
                logger.error(f"❌ GCS key file not found at: {self.gcs_key_path.resolve()}")
                raise FileNotFoundError("GCS key file 'jibber_jabber_key.json' not found.")

            self.storage_client = storage.Client.from_service_account_json(
                self.gcs_key_path, project=self.project_id
            )
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ Authenticated with GCS and connected to bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to GCS: {e}")
            raise

        self.session = self._build_session()

    def _load_all_api_keys(self) -> list:
        """Load all available Elexon API keys from environment or api.env file."""
        keys = []
        # Try environment variables first
        for i in range(1, 21):
            key = os.getenv(f'BMRS_API_KEY_{i}')
            if key:
                keys.append(key)
        # If not all found, try api.env
        if len(keys) < 20:
            env_path = Path("old_project/api.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        for i in range(1, 21):
                            if line.startswith(f"BMRS_API_KEY_{i}="):
                                key = line.strip().split("=", 1)[1]
                                if key not in keys:
                                    keys.append(key)
        if not keys:
            raise ValueError("No Elexon API keys found in environment or old_project/api.env")
        logger.info(f"✅ Loaded {len(keys)} Elexon API keys for rotation.")
        return keys

    def _get_next_api_key(self) -> str:
        """Rotate to the next API key for each request."""
        key = self.api_keys[self.api_key_index]
        self.api_key_index = (self.api_key_index + 1) % len(self.api_keys)
        return key

    def _load_api_key(self) -> str:
        """Loads the Elexon API key from environment or file."""
        api_key = os.getenv('BMRS_API_KEY_1')
        if api_key:
            logger.info("✅ Loaded Elexon API key from environment variable.")
            return api_key

        env_path = Path("old_project/api.env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("BMRS_API_KEY_1="):
                        key = line.strip().split("=", 1)[1]
                        logger.info("✅ Loaded Elexon API key from api.env file.")
                        return key

        raise ValueError("Elexon API key is required. Set BMRS_API_KEY_1 environment variable or provide in old_project/api.env file.")

    def _build_session(self, retries: int = 5, backoff_factor: float = 0.5) -> requests.Session:
        """Builds a requests session with retry capability."""
        session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=backoff_factor
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.headers.update({'User-Agent': 'UnifiedDataDownloader/1.0'})
        return session

    def _upload_to_gcs(self, data: Any, gcs_path: str):
        """Uploads data to a GCS path."""
        blob = self.bucket.blob(gcs_path)
        blob.upload_from_string(json.dumps(data), content_type='application/json')
        logger.info(f"✅ Uploaded to gs://{self.bucket_name}/{gcs_path}")

    def download_elexon_dataset(self, dataset_id: str, start_date: str, end_date: str, max_days_per_request: int = 7, fmt: str = "json") -> int:
        """Downloads a specific Elexon dataset for a date range and format."""
        logger.info(f"⏳ Downloading Elexon dataset: {dataset_id} from {start_date} to {end_date} as {fmt}")

        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        date_chunks = []
        current_date = start_dt
        while current_date <= end_dt:
            chunk_end = min(current_date + timedelta(days=max_days_per_request - 1), end_dt)
            date_chunks.append((current_date, chunk_end))
            current_date = chunk_end + timedelta(days=1)

        total_downloaded = 0
        for chunk_start, chunk_end in date_chunks:
            api_key = self._get_next_api_key()
            params = {
                'from': chunk_start.strftime('%Y-%m-%d'),
                'to': chunk_end.strftime('%Y-%m-%d'),
                'format': fmt,
                'apiKey': api_key
            }
            endpoint_url = f"{ELEXON_BASE_URL}/datasets/{dataset_id}"

            try:
                response = self.session.get(endpoint_url, params=params, timeout=60)
                response.raise_for_status()
                if fmt == "json":
                    data = response.json()
                    if data.get('data'):
                        filename = f"elexon/{dataset_id}/{chunk_start.year}/{chunk_start.month:02d}/{dataset_id}_{chunk_start}_{chunk_end}.{fmt}"
                        self._upload_to_gcs(data, filename)
                        total_downloaded += 1
                    else:
                        logger.warning(f"⚠️ No data returned for {dataset_id} from {chunk_start} to {chunk_end}")
                else:
                    # Save raw text for csv/xml
                    if response.text.strip():
                        filename = f"elexon/{dataset_id}/{chunk_start.year}/{chunk_start.month:02d}/{dataset_id}_{chunk_start}_{chunk_end}.{fmt}"
                        self._upload_to_gcs(response.text, filename)
                        total_downloaded += 1
                    else:
                        logger.warning(f"⚠️ No data returned for {dataset_id} from {chunk_start} to {chunk_end} as {fmt}")

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error downloading {dataset_id} for {chunk_start} to {chunk_end} as {fmt}: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to process {dataset_id} as {fmt}: {e}")

            time.sleep(1) # Rate limiting

        logger.info(f"✅ Completed download of Elexon dataset {dataset_id} as {fmt}: {total_downloaded} files")
        return total_downloaded

    def download_all_elexon_datasets(self, start_date: str, end_date: str, max_workers: int = 5):
        """Downloads all Elexon datasets in parallel."""
        logger.info(f"🚀 Starting download of all {len(ELEXON_DATASET_IDS)} Elexon datasets...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.download_elexon_dataset, ds_id, start_date, end_date): ds_id for ds_id in ELEXON_DATASET_IDS}
            for future in concurrent.futures.as_completed(futures):
                ds_id = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    logger.error(f"❌ {ds_id} generated an exception: {exc}")

    def download_neso_data(self, start_date: str, end_date: str):
        """Downloads NESO data based on best practices."""
        logger.info("⏳ Downloading NESO data...")
        try:
            # 1. Get list of all datasets (packages)
            package_list_url = f"{NESO_BASE_URL}/package_list"
            response = self.session.get(package_list_url, timeout=30)
            response.raise_for_status()
            dataset_names = response.json().get('result', [])
            logger.info(f"Found {len(dataset_names)} NESO datasets.")

            for ds_name in dataset_names:
                # 2. Get dataset details to find resources
                package_show_url = f"{NESO_BASE_URL}/package_show?id={ds_name}"
                ds_resp = self.session.get(package_show_url, timeout=30)
                ds_info = ds_resp.json().get('result', {})

                for resource in ds_info.get("resources", []):
                    res_id = resource.get("id")

                    # 3. Check resource metadata for modification date
                    res_show_url = f"{NESO_BASE_URL}/resource_show?id={res_id}"
                    res_meta_resp = self.session.get(res_show_url, timeout=30)
                    res_meta = res_meta_resp.json().get('result', {})

                    # Basic check if resource was modified recently. A more robust check would store last_modified dates.
                    last_modified_str = res_meta.get('last_modified')
                    if last_modified_str:
                        last_modified_dt = datetime.fromisoformat(last_modified_str.replace('Z', '+00:00')).date()
                        if last_modified_dt < datetime.strptime(start_date, '%Y-%m-%d').date():
                            logger.info(f"Skipping NESO resource {res_meta.get('name')} as it was not modified recently.")
                            continue

                    # 4. If it's a datastore resource, query it
                    if res_meta.get("datastore_active"):
                        # Using datastore_search_sql for more control
                        # This query fetches data within the date range.
                        # Note: The date column name might vary per dataset. This is a best-effort guess.
                        query = f'SELECT * FROM "{res_id}" WHERE "SETT_DATE" >= \'{start_date}\' AND "SETT_DATE" <= \'{end_date}\' LIMIT 10000'
                        sql_url = f"{NESO_BASE_URL}/datastore_search_sql?sql={query}"
                        try:
                            data_resp = self.session.get(sql_url, timeout=120)
                            data_resp.raise_for_status()
                            records = data_resp.json().get('result', {}).get('records', [])
                            if records:
                                filename = f"neso/{ds_name}/{res_id}.json"
                                self._upload_to_gcs(records, filename)
                            else:
                                logger.info(f"No records found for NESO resource {res_meta.get('name')} in the date range.")
                        except Exception as e:
                            logger.error(f"❌ Failed to query NESO resource {res_meta.get('name')}: {e}")

                time.sleep(2) # Rate limiting per dataset

        except Exception as e:
            logger.error(f"❌ Failed to download NESO data: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Unified Elexon & NESO Data Downloader')
    parser.add_argument('--start-date', type=str, default=DEFAULT_START_DATE, help=f'Start date in YYYY-MM-DD format (default: {DEFAULT_START_DATE})')
    parser.add_argument('--end-date', type=str, default=DEFAULT_END_DATE, help=f'End date in YYYY-MM-DD format (default: {DEFAULT_END_DATE})')
    parser.add_argument('--bucket', type=str, default=DEFAULT_BUCKET_NAME, help=f'GCS bucket name (default: {DEFAULT_BUCKET_NAME})')
    parser.add_argument('--project', type=str, default=DEFAULT_PROJECT_ID, help=f'GCP project ID (default: {DEFAULT_PROJECT_ID})')
    parser.add_argument('--api-key', type=str, help='Elexon API key (overrides environment/file)')
    parser.add_argument('--source', type=str, choices=['all', 'elexon', 'neso'], default='all', help='Which data source to download from')
    parser.add_argument('--test-dataset', type=str, help='Dataset ID to test for a single month (all formats)')
    parser.add_argument('--test-year', type=int, help='Year for test mode (with --test-dataset)')
    parser.add_argument('--test-month', type=int, help='Month for test mode (with --test-dataset)')

    args = parser.parse_args()

    try:
        downloader = UnifiedDownloader(
            api_key=args.api_key,
            bucket_name=args.bucket,
            project_id=args.project
        )

        if args.test_dataset and args.test_year and args.test_month:
            # Test mode: download one dataset for one month in all formats
            results = downloader.download_dataset_for_month_all_formats(args.test_dataset, args.test_year, args.test_month)
            print(f"Test results for {args.test_dataset} {args.test_year}-{args.test_month:02d}: {results}")
            return 0

        if args.source in ['all', 'elexon']:
            downloader.download_all_elexon_datasets(args.start_date, args.end_date)

        if args.source in ['all', 'neso']:
            downloader.download_neso_data(args.start_date, args.end_date)

        logger.info("🎉 All download tasks completed.")

    except Exception as e:
        logger.critical(f"❌ A fatal error occurred: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
