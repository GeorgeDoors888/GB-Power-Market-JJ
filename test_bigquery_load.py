#!/usr/bin/env python3
import logging
import os
from datetime import datetime, timezone

import pandas as pd
from google.api_core import retry
from google.cloud import bigquery

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_bigquery_load():
    """Test BigQuery loading with a small test dataset"""

    # Create test data
    test_data = pd.DataFrame(
        {
            "dataset": ["FREQ"] * 5,
            "measurementTime": [datetime.now(timezone.utc)] * 5,
            "frequency": [50.0, 50.1, 50.2, 50.3, 50.4],
            "_dataset": ["FREQ"] * 5,
            "_window_from_utc": [datetime.now(timezone.utc)] * 5,
            "_window_to_utc": [datetime.now(timezone.utc)] * 5,
            "_ingested_utc": [datetime.now(timezone.utc)] * 5,
            "_source_columns": ["frequency,measurementTime"] * 5,
            "_source_api": ["v1"] * 5,
            "_hash_source_cols": ["test_hash"] * 5,
            "_hash_key": ["test_key"] * 5,
        }
    )

    logger.info("Test data created")

    # Initialize BigQuery client
    client = bigquery.Client()
    logger.info(f"BigQuery client initialized for project: {client.project}")

    # Create test table schema
    schema = [
        bigquery.SchemaField("dataset", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("measurementTime", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("frequency", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("_dataset", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("_window_from_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_window_to_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_ingested_utc", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("_source_columns", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_source_api", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_hash_source_cols", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("_hash_key", "STRING", mode="NULLABLE"),
    ]

    # Set up test table
    dataset_id = "uk_energy_insights"
    table_id = f"{client.project}.{dataset_id}.test_freq_load"

    try:
        # Create the test table
        table = bigquery.Table(table_id, schema=schema)
        table = client.create_table(table, exists_ok=True)
        logger.info(f"Test table created: {table_id}")

        # Configure the load job
        job_config = bigquery.LoadJobConfig(
            schema=schema,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        )

        # Load the data with retry
        load_job = client.load_table_from_dataframe(
            test_data, table_id, job_config=job_config, retry=retry.Retry(deadline=300)
        )

        # Wait for the job to complete
        load_job.result()
        logger.info(f"✅ Loaded {len(test_data)} rows to {table_id}")

        # Verify the loaded data
        table = client.get_table(table_id)
        logger.info(f"Table now has {table.num_rows} rows")

        # Query the loaded data
        query = f"""
        SELECT COUNT(*) as count
        FROM `{table_id}`
        WHERE _ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 MINUTE)
        """
        query_job = client.query(query)
        rows = query_job.result()
        for row in rows:
            logger.info(f"Found {row.count} recently loaded rows")

    except Exception as e:
        logger.error(f"Error during BigQuery operations: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    test_bigquery_load()
