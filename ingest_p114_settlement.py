#!/usr/bin/env python3
"""
P114 Settlement Data Ingestion - c0421 BM Unit Metered Volumes

Downloads and ingests c0421 (BM Unit metered volumes) from Elexon P114 Portal.
This provides actual settlement data for reconciliation with BMRS balancing mechanism revenue.

**IMPORTANT**: Requires valid P114 scripting key from Elexon Portal
To generate key:
1. Login to https://www.elexonportal.co.uk/
2. Go to Account Settings → Scripting
3. Generate new scripting key
4. Update SCRIPTING_KEY variable below

Data: c0421 = BM Unit metered volumes per settlement period
Columns: ~370 fields including actual generation, consumption, prices, settlement volumes
Storage: Estimated 10-20M rows, 20-30GB for 2-3 years of data
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import time
import json
import os
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE_NAME = "elexon_p114_settlement"
LOCATION = "US"

# ⚠️ UPDATE THIS WITH VALID KEY FROM ELEXON PORTAL
SCRIPTING_KEY = "03omen6i9lhv5fa"

# P114 Portal endpoints
PORTAL_LIST_URL = "https://downloads.elexonportal.co.uk/p114/list"
PORTAL_DOWNLOAD_URL = "https://downloads.elexonportal.co.uk/p114/download"

# File filters
FILE_FILTER = "c0421"  # BM Unit metered volumes


def check_key_valid():
    """Test if scripting key is valid"""
    if SCRIPTING_KEY == "PLACEHOLDER_REGENERATE_FROM_PORTAL":
        print("❌ ERROR: P114 scripting key not configured!")
        print("\n📋 To obtain valid key:")
        print("   1. Login to https://www.elexonportal.co.uk/")
        print("   2. Navigate to: Account Settings → Scripting")
        print("   3. Generate new scripting key")
        print("   4. Update SCRIPTING_KEY in this script")
        print("\nNote: Old keys expire. Current account has P114 license (non-BSC party access).")
        return False

    # Test key with simple list request
    test_date = datetime.now().strftime("%Y-%m-%d")
    params = {
        "key": SCRIPTING_KEY,
        "date": test_date,
        "filter": FILE_FILTER
    }

    try:
        response = requests.get(PORTAL_LIST_URL, params=params, timeout=30)
        if response.status_code == 200 and "Scripting Error" not in response.text:
            print("✅ P114 scripting key valid")
            return True
        else:
            print(f"❌ Key validation failed: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Key validation error: {e}")
        return False


def list_available_files(date_str, filter_type="c0421"):
    """
    List available P114 files for a given date

    Args:
        date_str: Date in format YYYY-MM-DD
        filter_type: File type filter (c0421, s0142, etc)

    Returns:
        List of filenames or None if error
    """
    params = {
        "key": SCRIPTING_KEY,
        "date": date_str,
        "filter": filter_type
    }

    try:
        response = requests.get(PORTAL_LIST_URL, params=params, timeout=30)
        if response.status_code == 200:
            # Response is JSON array of filenames
            files = response.json()
            return files if isinstance(files, list) else []
        else:
            print(f"⚠️ List failed for {date_str}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error listing files for {date_str}: {e}")
        return None


def download_file(filename):
    """
    Download specific P114 file

    Args:
        filename: Filename from list endpoint

    Returns:
        File content as bytes or None if error
    """
    params = {
        "key": SCRIPTING_KEY,
        "filename": filename
    }

    try:
        response = requests.get(PORTAL_DOWNLOAD_URL, params=params, timeout=60)
        if response.status_code == 200:
            return response.content
        else:
            print(f"⚠️ Download failed for {filename}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return None


def parse_c0421_file(file_content):
    """
    Parse c0421 CSV file into DataFrame

    c0421 format: BM Unit metered volumes
    Expected columns: ~370 fields including:
    - Settlement Date, Settlement Period
    - BM Unit ID
    - Metered volumes (generation/consumption)
    - Settlement prices and values
    - Various BSC calculation fields

    Returns:
        DataFrame or None if parse error
    """
    try:
        # c0421 is CSV format
        from io import StringIO
        df = pd.read_csv(StringIO(file_content.decode('utf-8')))

        # Standardize column names (lowercase, replace spaces with underscores)
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        # Convert settlement date to datetime
        if 'settlement_date' in df.columns:
            df['settlement_date'] = pd.to_datetime(df['settlement_date'])

        return df
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return None


def create_table_if_not_exists(client):
    """
    Create P114 settlement table in BigQuery

    Schema: Auto-detected from first upload, but key fields:
    - settlement_date: DATE (partition key)
    - settlement_period: INT64
    - bm_unit_id: STRING (cluster key)
    - metered_volume: FLOAT64
    - settlement_price: FLOAT64
    - ... ~365 additional columns from c0421
    """
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        client.get_table(table_id)
        print(f"✅ Table {TABLE_NAME} already exists")
        return True
    except:
        print(f"📝 Creating table {TABLE_NAME}...")

        # Let BigQuery auto-detect schema from first upload
        # Partition by settlement_date, cluster by bm_unit_id
        schema = [
            bigquery.SchemaField("settlement_date", "DATE", mode="REQUIRED"),
            bigquery.SchemaField("settlement_period", "INTEGER"),
            bigquery.SchemaField("bm_unit_id", "STRING"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="settlement_date"
        )
        table.clustering_fields = ["bm_unit_id"]

        client.create_table(table)
        print(f"✅ Table {TABLE_NAME} created")
        return True


def upload_to_bigquery(client, df, date_str):
    """Upload DataFrame to BigQuery"""
    if df is None or df.empty:
        print(f"⚠️ No data to upload for {date_str}")
        return False

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,  # Auto-detect schema from data
        )

        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Wait for completion

        print(f"✅ Uploaded {len(df)} rows for {date_str}")
        return True
    except Exception as e:
        print(f"❌ Upload error for {date_str}: {e}")
        return False


def ingest_date_range(start_date, end_date):
    """
    Ingest P114 c0421 files for date range

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    """
    print(f"\n🚀 P114 Settlement Data Ingestion")
    print(f"📅 Date range: {start_date} to {end_date}")
    print(f"📊 Target: {TABLE_NAME}")
    print("="*80)

    # Validate key first
    if not check_key_valid():
        return

    # Initialize BigQuery client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Create table if needed
    create_table_if_not_exists(client)

    # Process each date
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start

    total_rows = 0
    success_count = 0

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n📅 Processing {date_str}...")

        # List available files
        files = list_available_files(date_str, FILE_FILTER)

        if files is None:
            print(f"⚠️ Skipping {date_str} (list failed)")
            current += timedelta(days=1)
            continue

        if not files:
            print(f"ℹ️ No c0421 files for {date_str}")
            current += timedelta(days=1)
            continue

        print(f"   Found {len(files)} file(s): {files}")

        # Download and process each file
        for filename in files:
            print(f"   📥 Downloading {filename}...")
            content = download_file(filename)

            if content is None:
                print(f"   ⚠️ Skipping {filename}")
                continue

            # Parse CSV
            df = parse_c0421_file(content)
            if df is not None:
                # Upload to BigQuery
                if upload_to_bigquery(client, df, date_str):
                    total_rows += len(df)
                    success_count += 1

            # Rate limiting
            time.sleep(2)

        current += timedelta(days=1)
        time.sleep(1)  # Rate limit between dates

    print("\n" + "="*80)
    print(f"✅ Ingestion complete!")
    print(f"   Total rows uploaded: {total_rows:,}")
    print(f"   Successful dates: {success_count}")
    print(f"   Date range: {start_date} to {end_date}")


def verify_data():
    """Verify ingested data"""
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    query = f"""
    SELECT
        MIN(settlement_date) as earliest_date,
        MAX(settlement_date) as latest_date,
        COUNT(*) as total_rows,
        COUNT(DISTINCT settlement_date) as distinct_dates,
        COUNT(DISTINCT bm_unit_id) as distinct_units
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """

    print("\n📊 Data Verification:")
    print("="*80)

    try:
        for row in client.query(query).result():
            print(f"   Date range: {row.earliest_date} to {row.latest_date}")
            print(f"   Total rows: {row.total_rows:,}")
            print(f"   Distinct dates: {row.distinct_dates}")
            print(f"   Distinct BM Units: {row.distinct_units}")
    except Exception as e:
        print(f"❌ Verification query failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 ingest_p114_settlement.py START_DATE END_DATE")
        print("Example: python3 ingest_p114_settlement.py 2024-01-01 2024-12-31")
        print("\n⚠️ Remember to update SCRIPTING_KEY variable first!")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    ingest_date_range(start_date, end_date)
    verify_data()
