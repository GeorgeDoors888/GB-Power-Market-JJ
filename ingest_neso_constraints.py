#!/usr/bin/env python3
"""
NESO/ESO Constraint Data Ingestion Pipeline
Scrapes and loads GB transmission constraint data into BigQuery

Datasets ingested:
1. Day-Ahead Constraint Flows & Limits
2. 24-Month Ahead Constraint Limits
3. CMIS (Constraint Management Intertrip Service)
4. CMZ (Constraint Management Zones) Forecasts
5. CMZ Flexibility Trades

Run every 6 hours to capture emergency updates
"""

import datetime as dt
import os
import sys
from typing import Dict, List
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery

# Credentials set via environment variable (GOOGLE_APPLICATION_CREDENTIALS)
# No need to set here - cron job handles it

# --------- CONFIG ---------
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_constraints"
INGEST_LOG_TABLE = f"{PROJECT_ID}.{DATASET_ID}.ingest_log"

# NESO/ESO data source URLs
DATASETS: Dict[str, Dict[str, str]] = {
    "dayahead_constraint_flows": {
        "page_url": "https://www.neso.energy/data-portal/day-ahead-constraint-flows-and-limits",
        "table": f"{PROJECT_ID}.{DATASET_ID}.constraint_flows_da",
    },
    "constraint_limits_24m": {
        "page_url": "https://www.neso.energy/data-portal/24-months-ahead-constraint-limits",
        "table": f"{PROJECT_ID}.{DATASET_ID}.constraint_limits_24m",
    },
    "cmis_arming": {
        "page_url": "https://www.neso.energy/data-portal/constraint-management-intertrip-service-information-cmis",
        "table": f"{PROJECT_ID}.{DATASET_ID}.cmis_arming",
    },
    "flex_forecasts": {
        "page_url": "https://connecteddata.nationalgrid.co.uk/dataset/flexibility-forecasts",
        "table": f"{PROJECT_ID}.{DATASET_ID}.cmz_forecasts",
    },
    # Note: flex_requirements dataset deprecated/removed from NESO portal (404 as of Dec 2025)
}

USER_AGENT = "Upowerenergy-Constraints-Ingest/1.0 (george@upowerenergy.uk)"

# --------- FUNCTIONS ---------

def get_bq_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID, location="US")


def ensure_dataset(client: bigquery.Client) -> None:
    """Create uk_constraints dataset if it doesn't exist"""
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    try:
        client.get_dataset(dataset_ref)
        print(f"✅ Dataset {DATASET_ID} exists")
    except Exception:
        dataset_ref.location = "US"
        client.create_dataset(dataset_ref)
        print(f"✅ Created dataset {DATASET_ID} in US region")


def ensure_ingest_log(client: bigquery.Client) -> None:
    """Create ingest_log table to track processed files"""
    try:
        client.get_table(INGEST_LOG_TABLE)
        print("✅ ingest_log table exists")
        return
    except Exception:
        schema = [
            bigquery.SchemaField("dataset_key", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("resource_url", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("first_seen", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("last_ingested", "TIMESTAMP", mode="REQUIRED"),
        ]
        table = bigquery.Table(INGEST_LOG_TABLE, schema=schema)
        client.create_table(table)
        print(f"✅ Created ingest_log table: {INGEST_LOG_TABLE}")


def get_already_processed_urls(client: bigquery.Client, dataset_key: str) -> List[str]:
    """Get list of URLs we've already processed"""
    query = f"""
        SELECT resource_url
        FROM `{INGEST_LOG_TABLE}`
        WHERE dataset_key = @dataset_key
        GROUP BY resource_url
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("dataset_key", "STRING", dataset_key)
            ]
        ),
    )
    return [row["resource_url"] for row in job.result()]


def mark_processed_url(client: bigquery.Client, dataset_key: str, resource_url: str) -> None:
    """Mark a URL as processed in ingest_log"""
    table = client.get_table(INGEST_LOG_TABLE)
    now = dt.datetime.utcnow().isoformat("T") + "Z"
    rows_to_insert = [
        {
            "dataset_key": dataset_key,
            "resource_url": resource_url,
            "first_seen": now,
            "last_ingested": now,
        }
    ]
    errors = client.insert_rows_json(table, rows_to_insert)
    if errors:
        print(f"⚠️  Failed to write ingest_log: {errors}")


def find_csv_links(page_url: str) -> List[str]:
    """Scrape CSV download links from NESO/NG portal pages"""
    print(f"📥 Fetching: {page_url}")
    try:
        resp = requests.get(page_url, headers={"User-Agent": USER_AGENT}, timeout=60)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if ".csv" in href.lower():
                if href.startswith("http://") or href.startswith("https://"):
                    links.append(href)
                else:
                    from urllib.parse import urljoin
                    links.append(urljoin(page_url, href))
        
        unique_links = sorted(set(links))
        print(f"   Found {len(unique_links)} CSV links")
        return unique_links
    except Exception as e:
        print(f"   ❌ Error scraping page: {e}")
        return []


def download_and_parse_csv(csv_url: str) -> pd.DataFrame:
    """Download CSV and return as DataFrame"""
    print(f"📥 Downloading: {csv_url}")
    # Try UTF-8 first, fall back to latin-1 for files with £ symbol or other special chars
    try:
        df = pd.read_csv(csv_url, encoding='utf-8')
    except UnicodeDecodeError:
        print(f"   ⚠️  UTF-8 failed, using latin-1 encoding...")
        df = pd.read_csv(csv_url, encoding='latin-1')
    print(f"   Loaded {len(df):,} rows")
    return df


def ensure_table_exists(client: bigquery.Client, table_id: str, sample_df: pd.DataFrame) -> None:
    """Create table if it doesn't exist"""
    try:
        client.get_table(table_id)
        print(f"✅ Table {table_id} exists")
        return
    except Exception:
        print(f"🔨 Creating table {table_id}")
        job_config = bigquery.LoadJobConfig(
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_EMPTY,
        )
        load_job = client.load_table_from_dataframe(sample_df.head(0), table_id, job_config=job_config)
        load_job.result()
        print(f"✅ Table {table_id} created")


def load_dataframe_to_bq(client: bigquery.Client, df: pd.DataFrame, table_id: str) -> None:
    """Load DataFrame to BigQuery table"""
    if df.empty:
        print(f"⚠️  DataFrame empty, skipping {table_id}")
        return

    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        autodetect=True,
    )
    print(f"⬆️  Loading {len(df):,} rows into {table_id}")
    load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()
    print(f"✅ Load complete")


def process_dataset(client: bigquery.Client, dataset_key: str, cfg: Dict[str, str]) -> None:
    """Process one constraint dataset"""
    page_url = cfg["page_url"]
    table_id = cfg["table"]
    print(f"\n{'='*70}")
    print(f"📊 DATASET: {dataset_key}")
    print(f"   Page:  {page_url}")
    print(f"   Table: {table_id}")
    print(f"{'='*70}")

    csv_links = find_csv_links(page_url)
    if not csv_links:
        print("⚠️  No CSV links found")
        return

    already = set(get_already_processed_urls(client, dataset_key))
    new_links = [u for u in csv_links if u not in already]
    
    if not new_links:
        print("✅ No new CSV files to process")
        return

    print(f"📥 {len(new_links)} new CSV file(s) to ingest")

    for csv_url in new_links:
        try:
            df = download_and_parse_csv(csv_url)

            # Normalize column names - BigQuery column name rules:
            # - Only letters, numbers, underscores
            # - Max 300 chars
            # - Must start with letter or underscore
            import re
            new_columns = []
            for c in df.columns:
                # Convert to lowercase, strip whitespace
                col = c.strip().lower()
                # Replace spaces, brackets, slashes, and other special chars with underscore
                col = re.sub(r'[^a-z0-9_]', '_', col)
                # Remove consecutive underscores
                col = re.sub(r'_+', '_', col)
                # Remove leading/trailing underscores
                col = col.strip('_')
                # Ensure starts with letter or underscore
                if col and col[0].isdigit():
                    col = 'col_' + col
                # Truncate to 300 chars
                col = col[:300]
                new_columns.append(col)
            
            df.columns = new_columns

            # Ensure table exists (first time only)
            ensure_table_exists(client, table_id, df)

            # Load to BigQuery
            load_dataframe_to_bq(client, df, table_id)

            # Mark as processed
            mark_processed_url(client, dataset_key, csv_url)

        except Exception as e:
            print(f"❌ Failed to process {csv_url}: {e}")


def main():
    print("🔌 NESO/ESO Constraint Data Ingestion Pipeline")
    print("="*70)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}")
    print(f"Time: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    client = get_bq_client()
    ensure_dataset(client)
    ensure_ingest_log(client)

    for dataset_key, cfg in DATASETS.items():
        try:
            process_dataset(client, dataset_key, cfg)
        except Exception as e:
            print(f"❌ Dataset {dataset_key} failed: {e}")

    print("\n" + "="*70)
    print("✅ CONSTRAINT INGESTION COMPLETE")
    print("="*70)


if __name__ == "__main__":
    sys.exit(main())
