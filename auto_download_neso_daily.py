#!/usr/bin/env python3
"""
Automated Daily NESO Data Downloads
Downloads constraint costs, MBSS, and other NESO publications automatically

Schedule: Daily at 3am (after NESO publishes previous day data)
Cron: 0 3 * * * /home/george/GB-Power-Market-JJ/auto_download_neso_daily.py >> /home/george/GB-Power-Market-JJ/logs/neso_daily.log 2>&1
"""

import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from google.cloud import bigquery
import pandas as pd
import json

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"neso_daily_{datetime.now():%Y%m%d}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
DOWNLOAD_DIR = Path(__file__).parent / "neso_downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

# NESO API Configuration
NESO_API_BASE = "https://api.neso.energy/api/3/action"


class NesoDownloader:
    """Automated NESO data downloader"""

    # Key NESO dataset IDs (found via API discovery)
    DATASETS = {
        'constraint_breakdown': {
            'package_id': 'historic-constraint-breakdown',
            'description': 'Monthly Emergency Instructions costs',
            'table': 'neso_constraint_breakdown'
        },
        'mbss': {
            'package_id': 'mbss-mandatory-balancing-services-costs',
            'description': 'Daily emergency service costs',
            'table': 'neso_mbss'
        },
        'constraint_forecast': {
            'package_id': '24-month-constraint-cost-forecast',
            'description': '24-month constraint cost forecast',
            'table': 'neso_constraint_forecast'
        },
        'modelled_costs': {
            'package_id': 'modelled-constraint-costs',
            'description': 'Modelled constraint costs analysis',
            'table': 'neso_modelled_costs'
        },
        'skip_rate': {
            'package_id': 'skip-rate',
            'description': 'Skip rate methodology data',
            'table': 'neso_skip_rates'
        }
    }

    def __init__(self):
        self.session = requests.Session()
        self.bq_client = bigquery.Client(project=PROJECT_ID, location="US")

    def get_dataset_latest_resource(self, package_id):
        """Get the most recent resource URL for a package"""
        url = f"{NESO_API_BASE}/package_show"
        params = {"id": package_id}

        logger.info(f"📦 Fetching metadata for: {package_id}")

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()["result"]

            resources = result.get("resources", [])
            if not resources:
                logger.warning(f"   No resources found for {package_id}")
                return None

            # Get latest CSV resource
            csv_resources = [r for r in resources if r.get('format', '').upper() == 'CSV']
            if not csv_resources:
                logger.warning(f"   No CSV resources found for {package_id}")
                return None

            # Sort by last_modified and get latest
            csv_resources.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
            latest = csv_resources[0]

            logger.info(f"   Latest: {latest['name']} ({latest.get('last_modified', 'unknown date')})")
            return latest

        except Exception as e:
            logger.error(f"   Error fetching metadata: {e}")
            return None

    def download_csv(self, url, output_path):
        """Download CSV file from URL"""
        try:
            logger.info(f"⬇️  Downloading: {url}")
            response = self.session.get(url, timeout=120, stream=True)
            response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = output_path.stat().st_size / 1024 / 1024  # MB
            logger.info(f"   Saved: {output_path} ({file_size:.2f} MB)")
            return True

        except Exception as e:
            logger.error(f"   Download failed: {e}")
            return False

    def load_to_bigquery(self, csv_path, table_name):
        """Load CSV to BigQuery table"""
        try:
            logger.info(f"📊 Loading to BigQuery: {table_name}")

            # Read CSV
            df = pd.read_csv(csv_path)
            logger.info(f"   Rows: {len(df):,}")

            # Clean column names (BigQuery compatible)
            df.columns = [c.strip().replace(' ', '_').replace('-', '_').lower()
                         for c in df.columns]

            # Load to BigQuery (append mode)
            table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND",
                autodetect=True,
                source_format=bigquery.SourceFormat.CSV,
            )

            job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()  # Wait for completion

            logger.info(f"   ✅ Loaded {len(df):,} rows to {table_name}")
            return True

        except Exception as e:
            logger.error(f"   ❌ BigQuery load failed: {e}")
            return False

    def download_and_ingest_dataset(self, dataset_key):
        """Download and ingest a single NESO dataset"""
        dataset_info = self.DATASETS[dataset_key]
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 {dataset_key.upper()}: {dataset_info['description']}")
        logger.info(f"{'='*80}")

        # Get latest resource
        resource = self.get_dataset_latest_resource(dataset_info['package_id'])
        if not resource:
            logger.warning(f"⚠️  Skipping {dataset_key} - no resources found")
            return False

        # Download CSV
        filename = f"{dataset_key}_{datetime.now():%Y%m%d}.csv"
        output_path = DOWNLOAD_DIR / dataset_key / filename

        if not self.download_csv(resource['url'], output_path):
            return False

        # Load to BigQuery
        if not self.load_to_bigquery(output_path, dataset_info['table']):
            return False

        logger.info(f"✅ {dataset_key} complete")
        return True

    def run_daily_update(self):
        """Run daily update for all NESO datasets"""
        logger.info("=" * 80)
        logger.info("🔄 NESO DAILY AUTO-INGESTION")
        logger.info("=" * 80)
        logger.info(f"📅 Date: {datetime.now():%Y-%m-%d %H:%M:%S}")

        results = {}
        for dataset_key in self.DATASETS.keys():
            try:
                results[dataset_key] = self.download_and_ingest_dataset(dataset_key)
            except Exception as e:
                logger.error(f"❌ {dataset_key} failed: {e}")
                results[dataset_key] = False

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("📈 SUMMARY")
        logger.info("=" * 80)

        for dataset_key, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            logger.info(f"{dataset_key:20} {status}")

        success_count = sum(results.values())
        total_count = len(results)
        logger.info(f"\nTotal: {success_count}/{total_count} succeeded")

        return success_count > 0


def main():
    downloader = NesoDownloader()
    success = downloader.run_daily_update()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
