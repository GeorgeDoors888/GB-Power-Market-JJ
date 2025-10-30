#!/usr/bin/env python3
"""
STOR Data Ingestion from NESO Portal to BigQuery

Ingests Short-Term Operating Reserve (STOR) data from NESO Portal CKAN API
to BigQuery, filling the gap identified in BMRS data coverage.
"""

import os
from datetime import datetime

import pandas as pd
import requests
from google.cloud import bigquery

# Configuration
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"
NESO_CKAN_BASE = "https://api.neso.energy/api/3/action"

# STOR datasets to ingest
STOR_DATASETS = {
    "stor_auction_results": {
        "dataset_id": "short-term-operating-reserve-stor-day-ahead-auction-results",
        "table_name": "neso_stor_auction_results",
        "description": "STOR Day Ahead Auction Results",
    },
    "stor_buy_curve": {
        "dataset_id": "short-term-operating-reserve-stor-day-ahead-buy-curve",
        "table_name": "neso_stor_buy_curve",
        "description": "STOR Day Ahead Buy Curve",
    },
    "stor_windows": {
        "dataset_id": "stor-windows",
        "table_name": "neso_stor_windows",
        "description": "STOR Service Windows",
    },
}


def fetch_neso_dataset(dataset_id: str, limit: int = 10000):
    """Fetch data from NESO CKAN dataset"""
    try:
        # Get dataset metadata
        pkg_show_url = f"{NESO_CKAN_BASE}/package_show?id={dataset_id}"
        resp = requests.get(pkg_show_url, timeout=30)
        resp.raise_for_status()
        ds_info = resp.json()["result"]

        print(f"Dataset: {ds_info['title']}")
        print(f"Resources: {len(ds_info.get('resources', []))}")

        all_data = []

        # Process each resource
        for res in ds_info.get("resources", []):
            res_id = res.get("id")
            res_name = res.get("name", res_id)

            if res.get("datastore_active"):
                print(f"  Fetching resource: {res_name}")

                # Fetch data from datastore
                ds_url = f"{NESO_CKAN_BASE}/datastore_search?resource_id={res_id}&limit={limit}"
                data_resp = requests.get(ds_url, timeout=30)
                data_resp.raise_for_status()

                records = data_resp.json().get("result", {}).get("records", [])
                if records:
                    df = pd.DataFrame(records)

                    # Clean column names for BigQuery compatibility
                    df.columns = [
                        col.replace("/", "_")
                        .replace("(", "")
                        .replace(")", "")
                        .replace("£", "GBP")
                        .replace(" ", "_")
                        .replace(":", "")
                        .replace("-", "_")
                        .strip()
                        for col in df.columns
                    ]

                    # Add metadata
                    df["_resource_name"] = res_name
                    df["_dataset_id"] = dataset_id
                    df["_ingested_utc"] = datetime.utcnow()
                    all_data.append(df)
                    print(f"    Fetched {len(records)} records")
                else:
                    print(f"    No records found")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error fetching {dataset_id}: {e}")
        return pd.DataFrame()


def upload_to_bigquery(df: pd.DataFrame, table_name: str):
    """Upload DataFrame to BigQuery"""
    if df.empty:
        print(f"No data to upload for {table_name}")
        return

    try:
        client = bigquery.Client(project=BQ_PROJECT)
        table_id = f"{BQ_PROJECT}.{BQ_DATASET}.{table_name}"

        # Configure load job
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Overwrite existing data
            autodetect=True,
        )

        # Load data
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for job to complete

        print(f"✅ Loaded {len(df)} rows to {table_id}")

    except Exception as e:
        print(f"❌ Failed to upload {table_name}: {e}")


def main():
    print("STOR Data Ingestion from NESO Portal")
    print("====================================\\n")

    for dataset_key, config in STOR_DATASETS.items():
        print(f"Processing {config['description']}...")

        # Fetch data
        df = fetch_neso_dataset(config["dataset_id"], limit=50000)

        if not df.empty:
            print(f"Dataset shape: {df.shape}")
            print(f"Columns: {list(df.columns)[:10]}...")  # Show first 10 columns

            # Upload to BigQuery
            upload_to_bigquery(df, config["table_name"])
        else:
            print("No data fetched")

        print()

    print("STOR data ingestion complete!")


if __name__ == "__main__":
    main()
