#!/usr/bin/env python3
"""
Example script to query your BigQuery data locally
"""

import os

import pandas as pd
from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables
load_dotenv()


def main():
    # Initialize client
    client = bigquery.Client(project="jibber-jabber-knowledge")

    print(f"✅ Connected to BigQuery project: {client.project}")

    # List all BMRS tables
    dataset_id = "uk_energy_insights"
    dataset_ref = client.dataset(dataset_id)

    print(f"\n📋 BMRS Tables in {dataset_id}:")
    tables = client.list_tables(dataset_ref)
    bmrs_tables = [table for table in tables if table.table_id.startswith("bmrs_")]

    for table in bmrs_tables:
        table_ref = dataset_ref.table(table.table_id)
        table_obj = client.get_table(table_ref)
        size_mb = (table_obj.num_bytes / 1024 / 1024) if table_obj.num_bytes else 0
        print(f"  • {table.table_id}: {table_obj.num_rows:,} rows ({size_mb:.1f} MB)")

    # Example query - modify as needed
    if bmrs_tables:
        sample_table = bmrs_tables[0].table_id
        query = f"""
        SELECT
            *
        FROM `jibber-jabber-knowledge.uk_energy_insights.{sample_table}`
        LIMIT 5
        """

        print(f"\n🔍 Sample data from {sample_table}:")
        try:
            query_job = client.query(query)
            results = query_job.result()
            df = results.to_dataframe()
            print(df.head())
        except Exception as e:
            print(f"⚠️  Query failed: {e}")

    # Check ingestion progress
    progress_query = """
    SELECT
        table_name,
        row_count,
        ROUND(size_bytes / 1024 / 1024, 2) as size_mb
    FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE 'bmrs_%'
    AND row_count > 0
    ORDER BY row_count DESC
    """

    print(f"\n📊 Ingestion Progress (tables with data):")
    try:
        query_job = client.query(progress_query)
        results = query_job.result()
        progress_df = results.to_dataframe()
        if not progress_df.empty:
            print(progress_df.to_string(index=False))
        else:
            print("  No tables with data yet (ingestion still in progress)")
    except Exception as e:
        print(f"⚠️  Progress query failed: {e}")


if __name__ == "__main__":
    main()
