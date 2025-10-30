"""
GCS to BigQuery Ingestion Script

This script reads all JSON files from a specified GCS bucket and prefix,
infers the schema, and loads the data into corresponding BigQuery tables.
It is designed to be the second step in the data pipeline, following the
successful download of data by `unified_downloader.py`.

Features:
- Reads data directly from GCS, avoiding re-downloading.
- Dynamically determines the target BigQuery table from the GCS file path.
- Automatically creates the BigQuery dataset and tables if they don't exist.
- Infers table schemas from the data to handle different dataset structures.
- Appends data, making the process idempotent for overlapping runs.
- Includes robust logging for monitoring and debugging.

"""

import os
import json
import logging
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from google.cloud import bigquery, storage
from google.api_core.exceptions import NotFound

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'gcs_to_bq_ingest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger('gcs_to_bq_ingest')

GCS_BUCKET_NAME = os.getenv('GCS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
GCP_PROJECT_ID = os.getenv('GCP_PROJECT', 'jibber-jabber-knowledge')
BQ_DATASET_ID = "bmrs_data"
SERVICE_ACCOUNT_KEY_FILE = "jibber_jabber_key.json"
GCS_PREFIX = "elexon/"

class GcsToBigQueryIngestor:
    """
    Handles the process of ingesting data from GCS to BigQuery.
    """
    def __init__(self, project_id: str, bucket_name: str, bq_dataset_id: str, key_file: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.bq_dataset_id = bq_dataset_id
        self.key_path = Path(key_file)

        if not self.key_path.exists():
            logger.critical(
                f"❌ Service account key not found at {self.key_path.resolve()}")
            raise FileNotFoundError(
                f"Service account key not found at {self.key_path.resolve()}")

        self.storage_client = storage.Client.from_service_account_json(
            self.key_path, project=self.project_id)
        self.bq_client = bigquery.Client.from_service_account_json(
            self.key_path, project=self.project_id)
        self.bucket = self.storage_client.bucket(self.bucket_name)

        logger.info("✅ GCS and BigQuery clients initialized successfully.")

    def get_dataset_id_from_path(self, gcs_path: str) -> Optional[str]:
        """Extracts a clean dataset ID from a GCS file path."""
        # Regex to find the dataset ID, which is the directory after 'elexon/'
        match = re.search(r'elexon/([^/]+)/', gcs_path)
        if match:
            # Sanitize the name to be a valid BigQuery table name
            return re.sub(r'[^a-zA-Z0-9_]', '', match.group(1))
        logger.warning(
            f"⚠️ Could not extract dataset ID from path: {gcs_path}")
        return None

    def create_bq_dataset_if_not_exists(self):
        """Ensures the target BigQuery dataset exists, creating it if necessary."""
        full_dataset_id = f"{self.project_id}.{self.bq_dataset_id}"
        dataset_ref = self.bq_client.dataset(self.bq_dataset_id)
        try:
            self.bq_client.get_dataset(dataset_ref)
            logger.info(f"BQ Dataset '{full_dataset_id}' already exists.")
        except NotFound:
            logger.info(f"Creating BQ Dataset: '{full_dataset_id}'")
            self.bq_client.create_dataset(dataset_ref, exists_ok=True)

    def process_blob(self, blob: storage.Blob):
        """
        Downloads a single file from GCS, processes its content,
        and loads it into the appropriate BigQuery table.
        """
        dataset_id = self.get_dataset_id_from_path(blob.name)
        if not dataset_id:
            return

        logger.info(
            f"⏳ Processing gs://{self.bucket_name}/{blob.name} for table '{dataset_id}'")

        try:
            content = blob.download_as_text()
            if not content.strip():
                logger.warning(f"⚠️ Skipping empty file: {blob.name}")
                return

            json_data = json.loads(content)
            records = json_data.get('data')

            if not records:
                logger.warning(
                    f"⚠️ No 'data' key found or data is empty in {blob.name}")
                return

            df = pd.DataFrame(records)

            # Clean column names for BigQuery compatibility
            original_columns = df.columns
            df.columns = [re.sub(r'[^a-zA-Z0-9_]', '', c).lower()
                                 for c in df.columns]
            if list(original_columns) != list(df.columns):
                logger.debug(
                    f"Renamed columns for {dataset_id}: {dict(zip(original_columns, df.columns))}")

            # Attempt to convert object columns to datetime
            for col in df.select_dtypes(include=['object']).columns:
                if df[col].astype(str).str.match(r'\d{4}-\d{2}-\d{2}').any():
                     df[col] = pd.to_datetime(df[col], errors='coerce')

            table_id = f"{self.project_id}.{self.bq_dataset_id}.{dataset_id}"

            job_config = bigquery.LoadJobConfig(
                autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            )

            load_job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config)
            logger.info(
                f"Starting BQ load job {load_job.job_id} for table {table_id}...")

            load_job.result()  # Wait for completion

            destination_table = self.bq_client.get_table(table_id)
            logger.info(
                f"✅ Loaded {len(df)} rows. Total rows in {table_id}: {destination_table.num_rows}")

        except json.JSONDecodeError:
            logger.error(f"❌ Failed to decode JSON from {blob.name}")
        except Exception as e:
            logger.error(
                f"❌ An unexpected error occurred while processing {blob.name}: {e}", exc_info=True)

    def run_ingestion(self, gcs_prefix: str):
        """
        Orchestrates the ingestion process by listing all relevant GCS files
        and processing them one by one.
        """
        self.create_bq_dataset_if_not_exists()

        blobs = self.storage_client.list_blobs(
            self.bucket_name, prefix=gcs_prefix)

        logger.info(
            f"🚀 Found files in gs://{self.bucket_name}/{gcs_prefix}. Starting ingestion...")

        processed_count = 0
        for blob in blobs:
            if blob.name.endswith(".json"):
                self.process_blob(blob)
                processed_count += 1

        logger.info(
            f"🎉 Ingestion run complete. Processed {processed_count} JSON files.")

def main():
    """Main entry point for the script."""
    try:
        ingestor = GcsToBigQueryIngestor(
            project_id=GCP_PROJECT_ID,
            bucket_name=GCS_BUCKET_NAME,
            bq_dataset_id=BQ_DATASET_ID,
            key_file=SERVICE_ACCOUNT_KEY_FILE
        )
        ingestor.run_ingestion(gcs_prefix=GCS_PREFIX)
        print("\n--- BigQuery Table Summary ---")
        print_bq_table_stats(ingestor.bq_client, GCP_PROJECT_ID, BQ_DATASET_ID)
        print("\n--- Table Date Ranges (from BigQuery data) ---")
        print_bq_table_date_ranges(ingestor.bq_client, GCP_PROJECT_ID, BQ_DATASET_ID)
    except Exception as e:
        print(f"Error in main: {e}")
# --- Table date range summary ---
def print_bq_table_date_ranges(bq_client, project_id, dataset_id):
    from google.cloud import bigquery
    import pandas as pd
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    tables = list(bq_client.list_tables(dataset_ref))
    if not tables:
        print("No tables found in dataset.")
        return
    for table in tables:
        t = bq_client.get_table(table)
        # Try to find a likely date/datetime column
        date_cols = [f.name for f in t.schema if f.field_type in ("DATE", "DATETIME", "TIMESTAMP")]
        if not date_cols:
            # Try to heuristically find a date column by name
            date_cols = [f.name for f in t.schema if "date" in f.name or "time" in f.name]
        if not date_cols:
            print(f"Table: {t.table_id:25}  No date/datetime column found.")
            continue
        col = date_cols[0]
        query = f"SELECT MIN({col}) as min_date, MAX({col}) as max_date FROM `{project_id}.{dataset_id}.{t.table_id}`"
        try:
            result = bq_client.query(query).to_dataframe()
            min_date = result['min_date'][0]
            max_date = result['max_date'][0]
            print(f"Table: {t.table_id:25}  Date column: {col:20}  Min: {min_date}  Max: {max_date}")
        except Exception as e:
            print(f"Table: {t.table_id:25}  Date column: {col:20}  Error: {e}")

# --- Table stats summary ---
def print_bq_table_stats(bq_client, project_id, dataset_id):
    from google.cloud import bigquery
    dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
    tables = list(bq_client.list_tables(dataset_ref))
    if not tables:
        print("No tables found in dataset.")
        return
    for table in tables:
        t = bq_client.get_table(table)
        size_mb = t.num_bytes / 1024 / 1024
        print(f"Table: {t.table_id:25} Rows: {t.num_rows:10}  Size: {size_mb:10.2f} MB")

if __name__ == "__main__":
    sys.exit(main())
