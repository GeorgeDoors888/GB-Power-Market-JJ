#!/usr/bin/env python

import logging

from google.cloud import bigquery

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

# Constants
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
TABLE_NAME = "test_table"


def main():
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID)
    logging.info(f"Client project: {client.project}")

    # Print how table_id would be constructed
    table_id = f"{client.project}.{DATASET_ID}.{TABLE_NAME}"
    logging.info(f"Full table_id: {table_id}")

    # Check if dataset exists
    dataset_ref = f"{client.project}.{DATASET_ID}"
    logging.info(f"Full dataset reference: {dataset_ref}")

    try:
        dataset = client.get_dataset(dataset_ref)
        logging.info(f"Dataset exists: {dataset.dataset_id}")
        logging.info(f"Dataset full path: {dataset.full_dataset_id}")
        logging.info(f"Dataset project: {dataset.project}")
    except Exception as e:
        logging.error(f"Error getting dataset: {e}")

    # Test dataset().table() method
    table_ref = client.dataset(DATASET_ID).table(TABLE_NAME)
    logging.info(
        f"Table reference from dataset().table(): {table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}"
    )

    # Log environment variables that might affect client behavior
    import os

    logging.info(
        f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}"
    )
    logging.info(
        f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}"
    )


if __name__ == "__main__":
    main()
