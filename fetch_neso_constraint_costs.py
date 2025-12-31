#!/usr/bin/env python3
"""
Fetch NESO Constraint Breakdown Costs from CKAN DataStore API
Source: https://data.nationalgrideso.com/constraint-management/constraint-breakdown-costs-and-volume
"""

import requests
import pandas as pd
from datetime import datetime

# NESO CKAN API endpoint
CKAN_BASE_URL = "https://data.nationalgrideso.com/api/3/action"

def get_constraint_datasets():
    """Get list of constraint breakdown datasets"""
    print("🔍 Finding constraint breakdown datasets...")

    # Search for constraint breakdown datasets
    search_url = f"{CKAN_BASE_URL}/package_search"
    params = {
        'q': 'constraint breakdown',
        'rows': 10
    }

    response = requests.get(search_url, params=params)
    data = response.json()

    if not data['success']:
        print("❌ Failed to search datasets")
        return []

    results = data['result']['results']
    print(f"✅ Found {len(results)} datasets\n")

    for i, dataset in enumerate(results, 1):
        print(f"{i}. {dataset['title']}")
        print(f"   ID: {dataset['name']}")
        print(f"   Resources: {len(dataset.get('resources', []))}")
        print()

    return results

def get_latest_constraint_data():
    """Get latest constraint breakdown data"""
    print("📊 Fetching latest constraint breakdown data...")

    # Known resource ID for 2024-2025 financial year
    # This needs to be updated - let's search for it

    # Get the constraint breakdown package
    package_url = f"{CKAN_BASE_URL}/package_show"
    params = {'id': 'constraint-breakdown-costs-and-volume'}

    response = requests.get(package_url, params=params)
    data = response.json()

    if not data['success']:
        print("❌ Failed to get constraint breakdown package")
        return None

    package = data['result']
    resources = package.get('resources', [])

    print(f"\n📋 Available resources ({len(resources)}):\n")

    # Sort by creation date descending
    resources_sorted = sorted(resources, key=lambda x: x.get('created', ''), reverse=True)

    for i, res in enumerate(resources_sorted[:5], 1):
        print(f"{i}. {res.get('name', 'Unnamed')}")
        print(f"   ID: {res['id']}")
        print(f"   Format: {res.get('format', 'N/A')}")
        print(f"   Created: {res.get('created', 'N/A')}")
        print(f"   Size: {res.get('size', 0) / 1024:.1f} KB")
        print()

    # Get the most recent CSV resource
    csv_resources = [r for r in resources if r.get('format', '').upper() == 'CSV']

    if not csv_resources:
        print("❌ No CSV resources found")
        return None

    latest_resource = csv_resources[0]
    print(f"📥 Using: {latest_resource.get('name', 'Latest data')}")
    print(f"   Resource ID: {latest_resource['id']}\n")

    # Fetch data using datastore_search
    datastore_url = f"{CKAN_BASE_URL}/datastore_search"
    params = {
        'resource_id': latest_resource['id'],
        'limit': 10000  # Get all records
    }

    print("⏳ Downloading data...")
    response = requests.get(datastore_url, params=params)
    data = response.json()

    if not data['success']:
        print("❌ Failed to fetch data")
        return None

    records = data['result']['records']
    print(f"✅ Retrieved {len(records)} records\n")

    # Convert to DataFrame
    df = pd.DataFrame(records)

    # Show columns
    print(f"📋 Columns: {list(df.columns)}\n")

    # Show summary
    print(f"📊 Data summary:")
    print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")

    # Calculate totals
    cost_cols = [c for c in df.columns if 'cost' in c.lower() and c != '_id']

    print(f"\n💰 Total costs:")
    for col in cost_cols:
        try:
            total = pd.to_numeric(df[col], errors='coerce').sum()
            print(f"   {col}: £{total:,.2f}")
        except:
            pass

    return df

def save_to_bigquery(df):
    """Save constraint data to BigQuery"""
    from google.cloud import bigquery

    PROJECT_ID = "inner-cinema-476211-u9"
    DATASET = "uk_energy_prod"
    TABLE = "neso_constraint_breakdown"

    print(f"\n📤 Uploading to BigQuery...")
    print(f"   Project: {PROJECT_ID}")
    print(f"   Dataset: {DATASET}")
    print(f"   Table: {TABLE}")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Clean column names for BigQuery
    df_clean = df.copy()
    df_clean.columns = [c.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').lower() for c in df_clean.columns]

    # Remove _id column if present
    if '_id' in df_clean.columns:
        df_clean = df_clean.drop(columns=['_id'])

    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True
    )

    job = client.load_table_from_dataframe(df_clean, table_id, job_config=job_config)
    job.result()

    print(f"✅ Uploaded {len(df_clean)} rows to {TABLE}")

    return table_id

def main():
    print("🌐 NESO CONSTRAINT BREAKDOWN DATA FETCHER")
    print("=" * 60)
    print()

    # Get datasets
    datasets = get_constraint_datasets()

    if not datasets:
        return

    # Fetch latest data
    df = get_latest_constraint_data()

    if df is None:
        return

    # Save sample to CSV
    csv_file = "neso_constraint_breakdown.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n💾 Saved to {csv_file}")

    # Upload to BigQuery
    try:
        table_id = save_to_bigquery(df)
        print(f"\n✅ Data available in BigQuery: {table_id}")
    except Exception as e:
        print(f"\n⚠️  BigQuery upload failed: {e}")

    print("\n" + "=" * 60)
    print("✅ COMPLETE")

if __name__ == "__main__":
    main()
