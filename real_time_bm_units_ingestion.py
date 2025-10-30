"""
Real-Time Ingestion for BM Units from Elexon API

This script fetches real-time data for all BM units from the Elexon API and ingests it into BigQuery.
"""

import csv
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
BIGQUERY_TABLE = "elexon_bm_units_raw"  # New table for BM unit data

# Validate required environment variables
if not ELEXON_API_KEY:
    raise ValueError(
        "ELEXON_API_KEY environment variable is not set. Please specify the API key."
    )

if not BIGQUERY_PROJECT_ID or not BIGQUERY_DATASET:
    raise ValueError(
        "BigQuery configuration (BIGQUERY_PROJECT_ID, BIGQUERY_DATASET) is not fully set."
    )

# Initialize BigQuery client
bq_client = bigquery.Client(project=BIGQUERY_PROJECT_ID)


def get_bm_units():
    """Reads BM units from bm_units.tsv."""
    bm_units = []
    with open("bm_units.tsv", "r") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)  # Skip header
        for row in reader:
            bm_units.append(row[0])
    return bm_units


def upload_to_bigquery(data):
    """Uploads data to BigQuery."""
    table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        autodetect=True,  # Autodetect schema
    )

    # Convert data to BigQuery-compatible format
    def flatten_and_decode(item):
        if not isinstance(item, dict):
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
            for key, value in item.items()
        }

    # The API returns a list of records, so we process each one
    if isinstance(data, list):
        rows_to_insert = [flatten_and_decode(item) for item in data]
    else:
        rows_to_insert = [flatten_and_decode(data)]

    if not rows_to_insert:
        print("No data to upload.")
        return

    errors = bq_client.insert_rows_json(table_id, rows_to_insert)

    if errors:
        print(f"Error uploading to BigQuery: {errors}")
    else:
        print(
            f"Data uploaded successfully to BigQuery for {len(rows_to_insert)} records."
        )


def fetch_data_for_bm_unit(bm_unit):
    """Fetches physical data for a specific BM unit from the Elexon API."""
    url = "https://api.bmreports.com/BMRS/PHYBMDATA/v1"
    params = {
        "APIKey": ELEXON_API_KEY,
        "SettlementDate": time.strftime("%Y-%m-%d"),
        "SettlementPeriod": "*",
        "BMUnitId": bm_unit,
        "ServiceType": "json",
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        response_data = response.json()
        # The actual data is in a nested key, check for its presence
        if "responseBody" in response_data and "data" in response_data["responseBody"]:
            print(f"Data fetched successfully for BM Unit {bm_unit}.")
            return response_data["responseBody"]["data"]
        else:
            print(f"No data in response for BM Unit {bm_unit}.")
            return None
    else:
        print(
            f"Error fetching data for BM Unit {bm_unit}: {response.status_code}, {response.text}"
        )
        return None


def main():
    """Main function to fetch data for all BM units and ingest into BigQuery."""
    bm_units = get_bm_units()
    print(f"Found {len(bm_units)} BM units to process.")

    while True:
        for bm_unit in bm_units:
            data = fetch_data_for_bm_unit(bm_unit)
            if data:
                try:
                    upload_to_bigquery(data)
                except Exception as e:
                    print(f"Error uploading data to BigQuery for {bm_unit}: {e}")
            # Add a small delay to avoid hitting API rate limits
            time.sleep(1)
        print(
            "Completed a cycle of fetching data for all BM units. Waiting for the next cycle."
        )
        time.sleep(300)  # Wait for 5 minutes before the next full cycle


if __name__ == "__main__":
    main()
