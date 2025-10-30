#!/usr/bin/env python3
"""
Enhanced DNO Data Collector with Fallback Strategies
===================================================

This improved version handles API access issues and provides multiple strategies
for collecting GB Distribution Network Operator data.

Features:
- Robust error handling for API issues
- Alternative data discovery methods
- UKPN focus with working endpoints
- Direct CSV discovery from known sources
- BigQuery integration for your existing pipeline

Run with: python fetch_dno_enhanced.py
"""

import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

# Configuration
OUT_DIR = Path("./dno_data_enhanced").resolve()
LOG_PATH = OUT_DIR / "enhanced_run.log"
DB_PATH = OUT_DIR / "dno_enhanced.sqlite"

# Setup logging
OUT_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)

# Known working DNO data sources
KNOWN_SOURCES = {
    "UKPN": {
        "base_url": "https://ukpowernetworks.opendatasoft.com",
        "known_datasets": [
            "monthly-electricity-consumption-per-customer-by-location",
            "ukpn-network-faults",
            "uk-power-networks-outages",
            "power-cut-data",
            "distribution-connections-queue",
        ],
    },
    "NGED": {
        "base_url": "https://connecteddata.nationalgrid.co.uk",
        "known_datasets": [
            "duos-availability-capacity-mapping",
            "distributed-flexibility-procurement",
            "enhanced-capacity-assessment",
        ],
    },
}


# Create session with retry strategy
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": "Energy-Research-Tool/1.0"})
    return session


class EnhancedDNOCollector:
    def __init__(self):
        self.session = create_session()
        self.collected_datasets = []

    def safe_request(self, url: str, timeout: int = 30) -> Optional[requests.Response]:
        """Make a safe HTTP request with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Request failed for {url}: {e}")
            return None

    def try_ukpn_direct(self):
        """Try direct access to known UKPN datasets."""
        logging.info("🔍 Attempting direct UKPN dataset access...")

        base_url = "https://ukpowernetworks.opendatasoft.com"

        # Try to get dataset list without search
        catalog_url = f"{base_url}/api/v2/catalog/datasets"
        response = self.safe_request(catalog_url)

        if response:
            try:
                data = response.json()
                datasets = data.get("datasets", [])

                logging.info(f"✅ Found {len(datasets)} UKPN datasets")

                for dataset in datasets[:10]:  # Limit to first 10 for demo
                    dataset_info = dataset.get("dataset", {})
                    dataset_id = dataset_info.get("dataset_id")
                    title = dataset_info.get("metas", {}).get("title", "")

                    if dataset_id:
                        csv_url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"
                        self.try_download_csv(csv_url, "UKPN", dataset_id, title)
                        time.sleep(0.5)  # Be respectful

            except Exception as e:
                logging.error(f"Failed to parse UKPN catalog: {e}")

    def try_download_csv(self, url: str, dno: str, dataset_id: str, title: str):
        """Attempt to download and process a CSV dataset."""
        logging.info(f"📥 Attempting download: {dataset_id}")

        response = self.safe_request(url, timeout=60)
        if not response:
            return False

        try:
            # Try to parse as CSV
            df = pd.read_csv(url, low_memory=False)

            if df.empty:
                logging.warning(f"Empty dataset: {dataset_id}")
                return False

            # Clean column names
            df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

            # Store the data
            self.store_dataset(df, dno, dataset_id, title)

            # Add to collected datasets
            self.collected_datasets.append(
                {
                    "dno": dno,
                    "dataset_id": dataset_id,
                    "title": title,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logging.info(f"✅ Successfully stored {len(df)} rows for {dataset_id}")
            return True

        except Exception as e:
            logging.error(f"Failed to process {dataset_id}: {e}")
            return False

    def store_dataset(self, df: pd.DataFrame, dno: str, dataset_id: str, title: str):
        """Store dataset in both Parquet and SQLite formats."""

        # Create safe filename
        safe_id = "".join(c for c in dataset_id if c.isalnum() or c in "._-")[:100]

        # Store as Parquet
        parquet_dir = OUT_DIR / "parquet" / dno
        parquet_dir.mkdir(parents=True, exist_ok=True)
        parquet_path = parquet_dir / f"{safe_id}.parquet"
        df.to_parquet(parquet_path, index=False)

        # Store in SQLite
        table_name = f"{dno.lower()}_{safe_id}"
        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)

    def try_alternative_sources(self):
        """Try alternative data sources and discovery methods."""
        logging.info("🔍 Trying alternative data discovery methods...")

        # Known direct CSV links (these change over time, but are examples)
        direct_links = [
            "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/ukpn-electricity-consumption-postcode/exports/csv",
            "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/power-cut-data/exports/csv",
        ]

        for url in direct_links:
            try:
                df = pd.read_csv(url, low_memory=False)
                if not df.empty:
                    # Extract dataset ID from URL
                    dataset_id = url.split("/")[-3] if "/" in url else "unknown"
                    self.store_dataset(
                        df, "UKPN_DIRECT", dataset_id, f"Direct: {dataset_id}"
                    )

                    self.collected_datasets.append(
                        {
                            "dno": "UKPN_DIRECT",
                            "dataset_id": dataset_id,
                            "title": f"Direct: {dataset_id}",
                            "rows": len(df),
                            "columns": len(df.columns),
                            "url": url,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    logging.info(
                        f"✅ Successfully collected direct dataset: {dataset_id}"
                    )
                    time.sleep(1)

            except Exception as e:
                logging.warning(f"Direct link failed {url}: {e}")

    def create_summary_report(self):
        """Create a comprehensive summary of collected data."""

        if not self.collected_datasets:
            logging.warning("No datasets were successfully collected")
            return

        # Create summary DataFrame
        summary_df = pd.DataFrame(self.collected_datasets)

        # Store summary
        summary_path = OUT_DIR / "collection_summary.parquet"
        summary_df.to_parquet(summary_path, index=False)

        with sqlite3.connect(DB_PATH) as conn:
            summary_df.to_sql(
                "collection_summary", conn, if_exists="replace", index=False
            )

        # Print summary
        logging.info("📊 COLLECTION SUMMARY")
        logging.info("=" * 50)
        logging.info(f"Total datasets collected: {len(self.collected_datasets)}")
        logging.info(f"Total rows across all datasets: {summary_df['rows'].sum():,}")
        logging.info(f"DNOs covered: {', '.join(summary_df['dno'].unique())}")

        # Top datasets by size
        top_datasets = summary_df.nlargest(5, "rows")[["dataset_id", "rows", "dno"]]
        logging.info("\n🏆 Largest datasets:")
        for _, row in top_datasets.iterrows():
            logging.info(
                f"  • {row['dataset_id']} ({row['dno']}): {row['rows']:,} rows"
            )

        logging.info(f"\n💾 Data stored in:")
        logging.info(f"  • Parquet files: {OUT_DIR}/parquet/")
        logging.info(f"  • SQLite database: {DB_PATH}")
        logging.info(f"  • Summary report: {summary_path}")

    def run_collection(self):
        """Run the complete data collection process."""
        logging.info("🚀 Starting Enhanced DNO Data Collection")
        logging.info("=" * 60)

        # Try UKPN direct access
        self.try_ukpn_direct()

        # Try alternative sources
        self.try_alternative_sources()

        # Create summary
        self.create_summary_report()

        logging.info("✅ DNO data collection completed!")


def create_bigquery_integration():
    """Create a script to load DNO data into BigQuery."""

    integration_script = '''#!/usr/bin/env python3
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
'''

    script_path = OUT_DIR / "load_to_bigquery.py"
    with open(script_path, "w") as f:
        f.write(integration_script)

    logging.info(f"📝 Created BigQuery integration script: {script_path}")


def main():
    """Main execution function."""

    collector = EnhancedDNOCollector()
    collector.run_collection()

    # Create BigQuery integration
    create_bigquery_integration()

    print("\n🎯 NEXT STEPS:")
    print("1. Review collected data in ./dno_data_enhanced/")
    print("2. Run: python dno_data_enhanced/load_to_bigquery.py")
    print("3. Query DNO + BMRS data together in BigQuery")
    print("4. For NGED data: Get API token from connecteddata.nationalgrid.co.uk")


if __name__ == "__main__":
    main()
