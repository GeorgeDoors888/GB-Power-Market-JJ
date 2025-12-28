#!/usr/bin/env python3
"""
NESO Interconnector Flows Ingestion

Downloads interconnector physical flow data from NESO Data Portal.
Tracks import/export flows across 8 GB interconnectors, critical for understanding
UK price volatility and VLP revenue opportunities.

**Interconnectors**:
- IFA (France): 2000 MW
- IFA2 (France): 1000 MW
- ElecLink (France): 1000 MW
- BritNed (Netherlands): 1000 MW
- Nemo Link (Belgium): 1000 MW
- Moyle (Northern Ireland): 500 MW
- EWIC (Ireland): 500 MW
- NSL/Viking Link (Norway): 1400 MW

**Status**: Template - Requires dataset URL identification
**API**: Currently unavailable, requires web scraping or manual download
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
TABLE_NAME = "neso_interconnector_flows"
LOCATION = "US"

# NESO Data Portal
NESO_BASE_URL = "https://data.nationalgrideso.com"
NESO_API_URL = f"{NESO_BASE_URL}/api/3/action"

# ⚠️ PLACEHOLDER - Update with actual dataset/resource ID
INTERCONNECTOR_DATASET = "interconnector-flows"  # Example name
INTERCONNECTOR_RESOURCE_ID = "RESOURCE_ID_PLACEHOLDER"

# Interconnector reference data
INTERCONNECTORS = {
    "IFA": {"country": "France", "capacity_mw": 2000},
    "IFA2": {"country": "France", "capacity_mw": 1000},
    "ELECLINK": {"country": "France", "capacity_mw": 1000},
    "BRITNED": {"country": "Netherlands", "capacity_mw": 1000},
    "NEMOLINK": {"country": "Belgium", "capacity_mw": 1000},
    "MOYLE": {"country": "Northern Ireland", "capacity_mw": 500},
    "EWIC": {"country": "Ireland", "capacity_mw": 500},
    "NSL": {"country": "Norway", "capacity_mw": 1400},
}


def search_interconnector_datasets():
    """Search NESO portal for interconnector datasets"""
    try:
        params = {"q": "interconnector", "rows": 10}
        response = requests.get(f"{NESO_API_URL}/package_search", params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("result", {}).get("results", [])
                print(f"\n📋 Found {len(results)} interconnector datasets:")
                for pkg in results:
                    print(f"   • {pkg.get('name')}: {pkg.get('title', 'N/A')}")
                    print(f"     URL: {NESO_BASE_URL}/dataset/{pkg.get('name')}")
                return results
            else:
                print("⚠️ API returned success=false")
                return []
        else:
            print(f"❌ Search failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Search error: {e}")
        return []


def download_interconnector_csv(resource_url):
    """Download CSV from resource URL"""
    try:
        response = requests.get(resource_url, timeout=60)
        if response.status_code == 200:
            print(f"✅ Downloaded {len(response.content)} bytes")
            return response.content
        else:
            print(f"⚠️ Download failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Download error: {e}")
        return None


def parse_interconnector_data(csv_content):
    """
    Parse interconnector flows CSV

    Expected columns (may vary):
    - timestamp / settlement_date / datetime
    - interconnector_name (IFA, IFA2, etc)
    - flow_mw (positive = import, negative = export)
    - capacity_mw
    - utilization_pct
    """
    try:
        from io import BytesIO
        df = pd.read_csv(BytesIO(csv_content))

        # Standardize column names
        df.columns = df.columns.str.lower().str.replace(' ', '_')

        # Try to identify timestamp column
        time_cols = [col for col in df.columns if any(x in col for x in ['time', 'date', 'period'])]
        if time_cols:
            df['timestamp'] = pd.to_datetime(df[time_cols[0]])

        # Add derived fields
        if 'flow_mw' in df.columns:
            df['flow_direction'] = df['flow_mw'].apply(lambda x: 'IMPORT' if x > 0 else 'EXPORT' if x < 0 else 'ZERO')

        # Enrich with reference data
        if 'interconnector' in df.columns or 'interconnector_name' in df.columns:
            ic_col = 'interconnector' if 'interconnector' in df.columns else 'interconnector_name'
            df['country'] = df[ic_col].str.upper().map(
                {k: v['country'] for k, v in INTERCONNECTORS.items()}
            )

        print(f"✅ Parsed {len(df)} rows")
        print(f"   Columns: {', '.join(df.columns)}")

        # Show sample
        if not df.empty:
            print(f"\n📊 Sample data:")
            print(df.head(3))

        return df
    except Exception as e:
        print(f"❌ Parse error: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_table_if_not_exists(client):
    """Create interconnector flows table"""
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        client.get_table(table_id)
        print(f"✅ Table {TABLE_NAME} already exists")
        return True
    except:
        print(f"📝 Creating table {TABLE_NAME}...")

        schema = [
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("interconnector_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("country", "STRING"),
            bigquery.SchemaField("flow_mw", "FLOAT64"),
            bigquery.SchemaField("flow_direction", "STRING"),
            bigquery.SchemaField("capacity_mw", "FLOAT64"),
            bigquery.SchemaField("utilization_pct", "FLOAT64"),
        ]

        table = bigquery.Table(table_id, schema=schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="timestamp"
        )
        table.clustering_fields = ["interconnector_name", "flow_direction"]

        client.create_table(table)
        print(f"✅ Table {TABLE_NAME} created")
        return True


def upload_to_bigquery(client, df):
    """Upload DataFrame to BigQuery"""
    if df is None or df.empty:
        print("⚠️ No data to upload")
        return False

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE_NAME}"

    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            autodetect=True,
        )

        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        print(f"✅ Uploaded {len(df)} rows to {TABLE_NAME}")
        return True
    except Exception as e:
        print(f"❌ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data(client):
    """Verify ingested data"""
    query = f"""
    SELECT
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(*) as total_rows,
        COUNT(DISTINCT interconnector_name) as distinct_ics,
        AVG(flow_mw) as avg_flow_mw,
        SUM(CASE WHEN flow_direction = 'IMPORT' THEN 1 ELSE 0 END) as imports,
        SUM(CASE WHEN flow_direction = 'EXPORT' THEN 1 ELSE 0 END) as exports
    FROM `{PROJECT_ID}.{DATASET}.{TABLE_NAME}`
    """

    print("\n📊 Data Verification:")
    print("="*80)

    try:
        for row in client.query(query).result():
            print(f"   Time range: {row.earliest} to {row.latest}")
            print(f"   Total rows: {row.total_rows:,}")
            print(f"   Interconnectors: {row.distinct_ics}")
            print(f"   Avg flow: {row.avg_flow_mw:.1f} MW")
            print(f"   Import periods: {row.imports:,}")
            print(f"   Export periods: {row.exports:,}")
    except Exception as e:
        print(f"❌ Verification failed: {e}")


def main_search():
    """Search mode"""
    print("\n🔍 NESO Interconnector Dataset Search")
    print("="*80)

    results = search_interconnector_datasets()

    if not results:
        print("\n⚠️ API search failed. Manual steps:")
        print("   1. Visit: https://data.nationalgrideso.com/")
        print("   2. Search for: 'interconnector'")
        print("   3. Find dataset with physical flows (MW)")
        print("   4. Note dataset name and resource ID")
        print("   5. Update script constants")


def main_ingest():
    """Ingest mode"""
    print("\n🚀 NESO Interconnector Flows Ingestion")
    print("="*80)

    if INTERCONNECTOR_RESOURCE_ID == "RESOURCE_ID_PLACEHOLDER":
        print("❌ Resource ID not configured!")
        print("   Run: python3 ingest_neso_interconnectors.py search")
        return

    # Initialize BigQuery
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    create_table_if_not_exists(client)

    # Download data
    resource_url = f"{NESO_BASE_URL}/dataset/{INTERCONNECTOR_DATASET}/resource/{INTERCONNECTOR_RESOURCE_ID}/download"
    print(f"\n📥 Downloading from: {resource_url}")

    csv_content = download_interconnector_csv(resource_url)
    if csv_content is None:
        return

    # Parse data
    df = parse_interconnector_data(csv_content)
    if df is None:
        return

    # Upload to BigQuery
    if upload_to_bigquery(client, df):
        verify_data(client)

    print("\n✅ Ingestion complete!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ingest_neso_interconnectors.py search")
        print("  python3 ingest_neso_interconnectors.py ingest")
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "search":
        main_search()
    elif mode == "ingest":
        main_ingest()
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
