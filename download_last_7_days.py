#!/usr/bin/env python3
"""
Download last 7 days of Elexon data from Insights API to BigQuery
Uses the insights_manifest.json configuration file
"""

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from typing import Any, Dict

import httpx
import pandas as pd
from google.cloud import bigquery
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from tqdm import tqdm

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
INSIGHTS_API_KEY = os.getenv("BMRS_API_KEY_1", "")  # Optional

def load_manifest(path="insights_manifest.json"):
    """Load the dataset manifest"""
    with open(path) as f:
        return json.load(f)

def ensure_bq_table(client: bigquery.Client, table_id: str, df_sample: pd.DataFrame):
    """Ensure BigQuery table exists with proper schema"""
    # Parse table ID - handle both formats: "project.dataset.table" or "dataset.table"
    parts = table_id.split(".")
    if len(parts) == 3:
        proj, dataset, table = parts
    elif len(parts) == 2:
        proj = PROJECT_ID
        dataset, table = parts
        table_id = f"{proj}.{dataset}.{table}"
    else:
        raise ValueError(f"Invalid table_id format: {table_id}")
    
    ds_ref = bigquery.Dataset(f"{proj}.{dataset}")
    try:
        client.get_dataset(ds_ref)
    except Exception:
        ds = bigquery.Dataset(ds_ref)
        ds.location = "EU"
        client.create_dataset(ds, exists_ok=True)
        print(f"✅ Created dataset: {dataset}")
    
    try:
        client.get_table(table_id)
        print(f"📋 Table exists: {table_id}")
    except Exception:
        schema = []
        for col, dtype in df_sample.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                field_type = "INT64"
            elif pd.api.types.is_float_dtype(dtype):
                field_type = "FLOAT64"
            elif pd.api.types.is_bool_dtype(dtype):
                field_type = "BOOL"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                field_type = "TIMESTAMP"
            else:
                field_type = "STRING"
            schema.append(bigquery.SchemaField(col, field_type))
        tbl = bigquery.Table(table_id, schema=schema)
        client.create_table(tbl)
        print(f"✅ Created table: {table_id}")

def upload_bq(client: bigquery.Client, table_id: str, df: pd.DataFrame):
    """Upload dataframe to BigQuery"""
    if df.empty:
        print(f"⚠️  No data to upload for {table_id}")
        return
    
    ensure_bq_table(client, table_id, df.head(100).copy())
    
    # Use load_table_from_dataframe for more reliable uploads
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for the job to complete
    
    print(f"✅ Uploaded {len(df)} rows to {table_id}")

@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=60),
    retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError))
)
def fetch_insights_data(code: str, route: str, start: date, end: date) -> list:
    """Fetch data from Insights API with retry logic"""
    params = {
        "from": start.isoformat(),
        "to": end.isoformat(),
        "format": "json"
    }
    if INSIGHTS_API_KEY:
        params["apiKey"] = INSIGHTS_API_KEY
    
    with httpx.Client(timeout=httpx.Timeout(60.0, connect=30.0)) as client:
        url = f"{INSIGHTS_BASE}{route}"
        print(f"  📥 Fetching: {url}")
        r = client.get(url, params=params, follow_redirects=True)
        r.raise_for_status()
        js = r.json()
        
        # Handle different response formats
        if isinstance(js, list):
            return js
        elif isinstance(js, dict):
            data = js.get("data", js)
            if isinstance(data, list):
                return data
            return [data] if data else []
        return []

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Download Elexon data to BigQuery")
    parser.add_argument("--manifest", default="insights_manifest_complete.json", 
                       help="Path to manifest file (default: insights_manifest_complete.json)")
    parser.add_argument("--days", type=int, default=7,
                       help="Number of days to download (default: 7)")
    parser.add_argument("--datasets", nargs="+",
                       help="Specific datasets to download (default: all)")
    args = parser.parse_args()
    
    # Date range
    end_date = date.today()
    start_date = end_date - timedelta(days=args.days)
    
    print("=" * 70)
    print(f"📅 Elexon Data Downloader - Last {args.days} Days")
    print("=" * 70)
    print(f"Start Date: {start_date}")
    print(f"End Date:   {end_date}")
    print(f"Project:    {PROJECT_ID}")
    print(f"Dataset:    {BQ_DATASET}")
    print(f"Manifest:   {args.manifest}")
    print("=" * 70)
    print()
    
    # Load manifest
    try:
        manifest = load_manifest(args.manifest)
    except FileNotFoundError:
        print(f"❌ Manifest file not found: {args.manifest}")
        print("Run: python discover_all_datasets.py to generate it")
        sys.exit(1)
    
    datasets = manifest.get("datasets", {})
    
    # Filter datasets if specified
    if args.datasets:
        datasets = {k: v for k, v in datasets.items() if k in args.datasets}
        if not datasets:
            print(f"❌ No matching datasets found: {args.datasets}")
            sys.exit(1)
    
    if not datasets:
        print("❌ No datasets found in manifest")
        sys.exit(1)
    
    print(f"📊 Found {len(datasets)} datasets to download")
    print()
    
    # Initialize BigQuery client
    bq_client = bigquery.Client(project=PROJECT_ID)
    
    # Track statistics
    stats = {
        "total_datasets": len(datasets),
        "successful": 0,
        "failed": 0,
        "total_rows": 0
    }
    
    # Download each dataset
    for code, config in tqdm(datasets.items(), desc="Downloading datasets"):
        print(f"\n🔄 Processing: {code} - {config.get('name', 'N/A')}")
        route = config.get("route")
        bq_table = config.get("bq_table", f"{PROJECT_ID}.{BQ_DATASET}.{code.lower()}")
        
        if not route:
            print(f"  ⚠️  No route specified, skipping")
            stats["failed"] += 1
            continue
        
        try:
            # Fetch data
            data = fetch_insights_data(code, route, start_date, end_date)
            
            if not data:
                print(f"  ℹ️  No data returned for {code}")
                stats["successful"] += 1
                continue
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            print(f"  📊 Retrieved {len(df)} rows")
            
            # Upload to BigQuery
            upload_bq(bq_client, bq_table, df)
            stats["successful"] += 1
            stats["total_rows"] += len(df)
            
        except httpx.HTTPStatusError as e:
            print(f"  ❌ HTTP Error {e.response.status_code}: {e}")
            stats["failed"] += 1
        except Exception as e:
            print(f"  ❌ Error: {e}")
            stats["failed"] += 1
    
    print()
    print("=" * 70)
    print("✅ Download complete!")
    print("=" * 70)
    print(f"📊 Statistics:")
    print(f"   Total datasets: {stats['total_datasets']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total rows uploaded: {stats['total_rows']:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()
