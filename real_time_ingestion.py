"""
Real-Time Ingestion with Elexon API

This script fetches real-time data from the Elexon API and ingests it into BigQuery.
"""

import json
import os
import time

import requests
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()

# Elexon API credentials
ELEXON_API_KEY = os.getenv("ELEXON_API_KEY")

# BigQuery credentials
BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE")

# Validate required environment variables
if not ELEXON_API_KEY:
    raise ValueError(
        "ELEXON_API_KEY environment variable is not set. Please specify the API key."
    )

if not BIGQUERY_PROJECT_ID or not BIGQUERY_DATASET or not BIGQUERY_TABLE:
    raise ValueError(
        "BigQuery configuration (BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, BIGQUERY_TABLE) is not fully set."
    )

# Initialize BigQuery client
bq_client = bigquery.Client(project=BIGQUERY_PROJECT_ID)


def upload_to_bigquery(data):
    """Uploads data to BigQuery."""
    table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")

    # Convert data to BigQuery-compatible format
    def flatten_and_decode(data):
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary.")

        # Ensure all keys and values are strings, decode bytes if necessary
        return {
            str(key): (
                value.decode("utf-8")
                if isinstance(value, bytes)
                else (
                    str(value)
                    if not isinstance(value, (dict, list))
                    else json.dumps(value)
                )
            )
            for key, value in data.items()
        }

    rows_to_insert = [flatten_and_decode(data)]

    errors = bq_client.insert_rows_json(table_id, rows_to_insert)

    if errors:
        print(f"Error uploading to BigQuery: {errors}")
    else:
        print("Data uploaded successfully to BigQuery.")


def fetch_data_from_elexon():
    """Fetches data from the Elexon API."""
    url = "https://api.bmreports.com/BMRS/ROLSYSDEM/v1"
    params = {"APIKey": ELEXON_API_KEY, "ServiceType": "json"}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        print("Data fetched successfully from Elexon API.")
        # Ensure the response content is decoded to a string
        return response.json()
    else:
        print(
            f"Error fetching data from Elexon API: {response.status_code}, {response.text}"
        )
        return None


def main():
    """Main function to fetch data from Elexon API and ingest into BigQuery."""
    while True:
        data = fetch_data_from_elexon()
        if data:
            try:
                upload_to_bigquery(data)
            except Exception as e:
                print(f"Error uploading data to BigQuery: {e}")
        time.sleep(300)  # Fetch data every 5 minutes


if __name__ == "__main__":
    main()
