#!/usr/bin/env python3
"""
NESO Data Portal API Ingestion Script
Replaces manual CSV downloads with automated API calls

NESO API Documentation: https://api.neso.energy/api/3/action/
Rate Limits: 1 req/sec for CKAN, 2 req/min for Datastore queries
"""

import requests
import time
import json
import argparse
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
from typing import Dict, List, Optional

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
API_BASE = "https://api.neso.energy/api/3/action"

# Rate limiting
CKAN_DELAY = 1.0  # 1 second between CKAN calls
DATASTORE_DELAY = 30.0  # 30 seconds between Datastore queries (2/min)


class NesoApiClient:
    """Client for NESO Data Portal CKAN API"""
    
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
        self.last_ckan_call = 0
        self.last_datastore_call = 0
    
    def _rate_limit_ckan(self):
        """Enforce 1 req/sec for CKAN endpoints"""
        elapsed = time.time() - self.last_ckan_call
        if elapsed < CKAN_DELAY:
            time.sleep(CKAN_DELAY - elapsed)
        self.last_ckan_call = time.time()
    
    def _rate_limit_datastore(self):
        """Enforce 2 req/min for Datastore queries"""
        elapsed = time.time() - self.last_datastore_call
        if elapsed < DATASTORE_DELAY:
            time.sleep(DATASTORE_DELAY - elapsed)
        self.last_datastore_call = time.time()
    
    def search_datasets(self, query: str, rows: int = 10) -> Dict:
        """Search for datasets by keyword"""
        self._rate_limit_ckan()
        url = f"{self.base_url}/package_search"
        params = {"q": query, "rows": rows}
        
        print(f"🔍 Searching for: '{query}'")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()["result"]
        print(f"   Found {result['count']} datasets")
        return result
    
    def get_dataset_metadata(self, dataset_id: str) -> Dict:
        """Get detailed metadata for a dataset (package)"""
        self._rate_limit_ckan()
        url = f"{self.base_url}/package_show"
        params = {"id": dataset_id}
        
        print(f"📦 Fetching metadata for: {dataset_id}")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()["result"]
        print(f"   Title: {result.get('title', 'N/A')}")
        print(f"   Resources: {len(result.get('resources', []))}")
        return result
    
    def get_resource_info(self, resource_id: str) -> Dict:
        """Get metadata for a specific resource (checks last_modified)"""
        self._rate_limit_ckan()
        url = f"{self.base_url}/resource_show"
        params = {"id": resource_id}
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()["result"]
        return result
    
    def query_datastore(self, resource_id: str, limit: int = 100, offset: int = 0) -> Dict:
        """Query datastore for a resource (paginated)"""
        self._rate_limit_datastore()
        url = f"{self.base_url}/datastore_search"
        params = {
            "resource_id": resource_id,
            "limit": limit,
            "offset": offset
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response.json()["result"]
    
    def query_datastore_sql(self, sql: str) -> Dict:
        """Query datastore using SQL (most powerful)"""
        self._rate_limit_datastore()
        url = f"{self.base_url}/datastore_search_sql"
        params = {"sql": sql}
        
        print(f"📊 Executing SQL query...")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        result = response.json()["result"]
        print(f"   Retrieved {len(result.get('records', []))} rows")
        return result


def find_constraint_cost_datasets(client: NesoApiClient) -> List[Dict]:
    """Find constraint cost related datasets"""
    search_terms = [
        "constraint cost",
        "historic constraint breakdown",
        "MBSS",
        "mandatory balancing services",
        "skip rate",
        "balancing services cost"
    ]
    
    datasets = []
    for term in search_terms:
        result = client.search_datasets(term, rows=20)
        for package in result.get("results", []):
            datasets.append({
                "id": package["id"],
                "name": package["name"],
                "title": package.get("title", ""),
                "search_term": term
            })
        time.sleep(1)  # Respect rate limits
    
    return datasets


def download_resource_to_bigquery(
    client: NesoApiClient,
    bq_client: bigquery.Client,
    resource_id: str,
    table_name: str,
    batch_size: int = 10000,
    test_mode: bool = False
) -> int:
    """Download resource data and upload to BigQuery"""
    
    # Get resource metadata first
    resource_info = client.get_resource_info(resource_id)
    print(f"\n📥 Downloading: {resource_info.get('name', resource_id)}")
    print(f"   Format: {resource_info.get('format', 'unknown')}")
    print(f"   Last Modified: {resource_info.get('last_modified', 'unknown')}")
    
    if test_mode:
        print("   🧪 TEST MODE: Fetching sample only")
        result = client.query_datastore(resource_id, limit=10)
        df = pd.DataFrame(result["records"])
        print(f"   Sample data preview:\n{df.head()}")
        return len(df)
    
    # Full download with pagination
    all_records = []
    offset = 0
    total_fetched = 0
    
    while True:
        result = client.query_datastore(resource_id, limit=batch_size, offset=offset)
        records = result.get("records", [])
        
        if not records:
            break
        
        all_records.extend(records)
        total_fetched += len(records)
        offset += batch_size
        
        print(f"   Progress: {total_fetched:,} rows downloaded...")
        
        # Stop if we've fetched all available data
        if len(records) < batch_size:
            break
    
    if not all_records:
        print("   ⚠️  No data retrieved")
        return 0
    
    # Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    # Remove CKAN internal fields
    internal_cols = ['_id', '_full_text']
    df = df.drop(columns=[col for col in internal_cols if col in df.columns])
    
    print(f"   📊 Total rows: {len(df):,}")
    print(f"   📋 Columns: {list(df.columns)}")
    
    # Upload to BigQuery
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
    
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Replace table
        autodetect=True,  # Auto-detect schema
    )
    
    print(f"   ⬆️  Uploading to {table_id}...")
    job = bq_client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # Wait for completion
    
    print(f"   ✅ Uploaded {len(df):,} rows to BigQuery")
    return len(df)


def main():
    parser = argparse.ArgumentParser(description="Ingest NESO data via API")
    parser.add_argument("--search", help="Search for datasets by keyword")
    parser.add_argument("--dataset-id", help="Download specific dataset by ID")
    parser.add_argument("--resource-id", help="Download specific resource by ID")
    parser.add_argument("--table-name", help="BigQuery table name (required with --resource-id)")
    parser.add_argument("--test", action="store_true", help="Test mode (sample data only)")
    parser.add_argument("--discover", action="store_true", help="Discover constraint cost datasets")
    
    args = parser.parse_args()
    
    # Initialize clients
    neso = NesoApiClient()
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Discovery mode
    if args.discover:
        print("🔍 DISCOVERING NESO CONSTRAINT COST DATASETS")
        print("=" * 80)
        datasets = find_constraint_cost_datasets(neso)
        
        print(f"\n📊 Found {len(datasets)} relevant datasets:")
        for ds in datasets:
            print(f"\n  ID: {ds['id']}")
            print(f"  Name: {ds['name']}")
            print(f"  Title: {ds['title']}")
            print(f"  Search term: {ds['search_term']}")
        
        # Save to file
        with open("neso_discovered_datasets.json", "w") as f:
            json.dump(datasets, f, indent=2)
        print(f"\n✅ Saved to: neso_discovered_datasets.json")
        return
    
    # Search mode
    if args.search:
        result = neso.search_datasets(args.search)
        print(f"\n📊 Results for '{args.search}':")
        for package in result["results"]:
            print(f"\n  Name: {package['name']}")
            print(f"  Title: {package.get('title', 'N/A')}")
            print(f"  ID: {package['id']}")
        return
    
    # Dataset metadata mode
    if args.dataset_id:
        metadata = neso.get_dataset_metadata(args.dataset_id)
        print(f"\n📦 Dataset: {metadata['title']}")
        print(f"   Description: {metadata.get('notes', 'N/A')[:200]}...")
        print(f"\n   Resources ({len(metadata['resources'])}):")
        for i, res in enumerate(metadata['resources'], 1):
            print(f"\n   {i}. {res.get('name', 'unnamed')}")
            print(f"      ID: {res['id']}")
            print(f"      Format: {res.get('format', 'unknown')}")
            print(f"      Size: {res.get('size', 'unknown')}")
            print(f"      Last Modified: {res.get('last_modified', 'unknown')}")
        return
    
    # Download mode
    if args.resource_id:
        if not args.table_name:
            print("❌ Error: --table-name required with --resource-id")
            return
        
        total_rows = download_resource_to_bigquery(
            neso, bq_client,
            args.resource_id,
            args.table_name,
            test_mode=args.test
        )
        
        print(f"\n✅ Complete: {total_rows:,} rows ingested")
        return
    
    # No arguments - show help
    parser.print_help()
    print("\n💡 Examples:")
    print("  python3 ingest_neso_api.py --discover")
    print("  python3 ingest_neso_api.py --search 'constraint cost'")
    print("  python3 ingest_neso_api.py --dataset-id historic-constraint-breakdown")
    print("  python3 ingest_neso_api.py --resource-id <UUID> --table-name neso_constraints --test")


if __name__ == "__main__":
    main()
