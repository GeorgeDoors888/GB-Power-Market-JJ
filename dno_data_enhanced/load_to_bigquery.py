#!/usr/bin/env python3
"""
Load DNO data into BigQuery to complement BMRS data
"""

from google.cloud import bigquery
import pandas as pd
from pathlib import Path

def load_dno_to_bigquery():
    """Load collected DNO data into BigQuery."""

    client = bigquery.Client(project="jibber-jabber-knowledge")
    dataset_id = "uk_energy_insights"

    # Find all parquet files
    parquet_dir = Path("./dno_data_enhanced/parquet")

    for dno_dir in parquet_dir.iterdir():
        if dno_dir.is_dir():
            dno_name = dno_dir.name.lower()

            for parquet_file in dno_dir.glob("*.parquet"):
                try:
                    df = pd.read_parquet(parquet_file)

                    table_name = f"dno_{dno_name}_{parquet_file.stem}"
                    table_id = f"{client.project}.{dataset_id}.{table_name}"

                    job_config = bigquery.LoadJobConfig(
                        write_disposition="WRITE_TRUNCATE",
                        autodetect=True
                    )

                    job = client.load_table_from_dataframe(
                        df, table_id, job_config=job_config
                    )
                    job.result()  # Wait for job to complete

                    print(f"✅ Loaded {len(df)} rows to {table_name}")

                except Exception as e:
                    print(f"❌ Failed to load {parquet_file}: {e}")

if __name__ == "__main__":
    load_dno_to_bigquery()
