#!/usr/bin/env python3
"""
Manual DNO Data Collector
=========================

Collects publicly available DNO data from direct CSV links and
documented download URLs that don't require API authentication.

This bypasses the API restrictions we encountered and focuses on
datasets that are openly available for download.
"""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUT_DIR = Path("./dno_manual_data").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)


class ManualDNOCollector:
    """Collect DNO data from publicly available sources."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    def download_file(self, url: str, filename: str, description: str = "") -> bool:
        """Download a file from URL."""

        try:
            logger.info(f"Downloading: {description or filename}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            file_path = OUT_DIR / filename
            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded: {filename} ({len(response.content):,} bytes)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download {filename}: {e}")
            return False

    def collect_ukpn_data(self):
        """Collect UKPN data from known public URLs."""

        logger.info("🔌 Collecting UKPN data...")

        # Known public UKPN datasets (these might work without API)
        ukpn_datasets = [
            {
                "url": "https://ukpowernetworks.opendatasoft.com/api/records/1.0/download/?dataset=long-term-development-statement-forecast-data&format=csv",
                "filename": "ukpn_ltds_forecast.csv",
                "description": "UKPN Long Term Development Statement Forecast",
            },
            {
                "url": "https://ukpowernetworks.opendatasoft.com/api/records/1.0/download/?dataset=network-capacity-map&format=csv",
                "filename": "ukpn_network_capacity.csv",
                "description": "UKPN Network Capacity Data",
            },
        ]

        successful = 0
        for dataset in ukpn_datasets:
            if self.download_file(
                dataset["url"], dataset["filename"], dataset["description"]
            ):
                successful += 1
            time.sleep(1)  # Be polite

        logger.info(f"UKPN: {successful}/{len(ukpn_datasets)} datasets collected")

    def collect_nged_data(self):
        """Collect National Grid ED data from public sources."""

        logger.info("⚡ Collecting NGED data...")

        # Known public NGED datasets
        nged_datasets = [
            {
                "url": "https://connecteddata.nationalgrid.co.uk/dataset/2593158a-353f-4b86-8c6d-5c6e9f8ad4e3/resource/177f6fa4-ae49-44f5-94ca-76d8c0831b6a/download/dfesdata2023.csv",
                "filename": "nged_dfes_2023.csv",
                "description": "NGED Distribution Future Energy Scenarios 2023",
            },
            {
                "url": "https://connecteddata.nationalgrid.co.uk/dataset/95e8b955-3640-4932-8db6-3d0e0e84be48/resource/cf7a0ab8-88c1-4334-9d83-b7e0d23dc3c9/download/network-capacity-heatmap-connections-in-flight.csv",
                "filename": "nged_network_capacity_heatmap.csv",
                "description": "NGED Network Capacity Heatmap",
            },
        ]

        successful = 0
        for dataset in nged_datasets:
            if self.download_file(
                dataset["url"], dataset["filename"], dataset["description"]
            ):
                successful += 1
            time.sleep(1)

        logger.info(f"NGED: {successful}/{len(nged_datasets)} datasets collected")

    def collect_northern_powergrid_data(self):
        """Collect Northern Powergrid data."""

        logger.info("⚡ Collecting Northern Powergrid data...")

        # Try direct CSV downloads
        npg_datasets = [
            {
                "url": "https://www.northernpowergrid.com/asset/0/document/3855.csv",
                "filename": "npg_generation_availability.csv",
                "description": "Northern Powergrid Generation Availability",
            }
        ]

        successful = 0
        for dataset in npg_datasets:
            if self.download_file(
                dataset["url"], dataset["filename"], dataset["description"]
            ):
                successful += 1
            time.sleep(1)

        logger.info(
            f"Northern Powergrid: {successful}/{len(npg_datasets)} datasets collected"
        )

    def collect_ssen_data(self):
        """Collect SSE Networks data."""

        logger.info("🔌 Collecting SSEN data...")

        ssen_datasets = [
            {
                "url": "https://data.ssen.co.uk/OpenData/NetworkData.csv",
                "filename": "ssen_network_data.csv",
                "description": "SSEN Network Data",
            }
        ]

        successful = 0
        for dataset in ssen_datasets:
            if self.download_file(
                dataset["url"], dataset["filename"], dataset["description"]
            ):
                successful += 1
            time.sleep(1)

        logger.info(f"SSEN: {successful}/{len(ssen_datasets)} datasets collected")

    def analyze_collected_data(self):
        """Analyze what data we've successfully collected."""

        logger.info("📊 Analyzing collected data...")

        analysis = {"files_collected": [], "total_size": 0, "data_summary": {}}

        for file_path in OUT_DIR.glob("*.csv"):
            try:
                # Get file info
                file_size = file_path.stat().st_size
                analysis["files_collected"].append(file_path.name)
                analysis["total_size"] += file_size

                # Try to read and analyze CSV
                df = pd.read_csv(file_path, nrows=1000)  # Sample first 1000 rows

                analysis["data_summary"][file_path.name] = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "size_mb": round(file_size / 1024 / 1024, 2),
                    "sample_columns": list(df.columns[:10]),  # First 10 columns
                }

                logger.info(
                    f"📄 {file_path.name}: {len(df)} rows, {len(df.columns)} columns"
                )

            except Exception as e:
                logger.warning(f"Could not analyze {file_path.name}: {e}")

        return analysis

    def create_integration_script(self, analysis):
        """Create script to integrate collected data with BigQuery."""

        integration_script = f'''#!/usr/bin/env python3
"""
DNO Manual Data Integration
===========================

Integrate manually collected DNO data with your BMRS BigQuery dataset.
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Files collected: {len(analysis["files_collected"])}
Total size: {analysis["total_size"] / 1024 / 1024:.1f} MB
"""

import pandas as pd
from google.cloud import bigquery
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DNOManualIntegrator:
    """Integrate manually collected DNO data."""

    def __init__(self):
        self.client = bigquery.Client(project="jibber-jabber-knowledge")
        self.dataset = "uk_energy_insights"
        self.data_dir = Path("./dno_manual_data")

    def process_collected_files(self):
        """Process all collected DNO files."""

        file_processors = {{
'''

        # Add specific processors for each file
        for filename, info in analysis["data_summary"].items():
            dno_name = filename.split("_")[0].upper()
            integration_script += f"""
            "{filename}": self.process_{filename.replace('.csv', '').replace('-', '_')},"""

        integration_script += '''
        }

        for csv_file in self.data_dir.glob("*.csv"):
            processor = file_processors.get(csv_file.name)
            if processor:
                try:
                    processor(csv_file)
                except Exception as e:
                    logger.error(f"Failed to process {csv_file.name}: {e}")
            else:
                logger.warning(f"No processor for {csv_file.name}")

    def load_to_bigquery(self, df: pd.DataFrame, table_name: str, dno_id: str):
        """Load DataFrame to BigQuery."""

        # Add metadata
        df['dno_id'] = dno_id
        df['data_source'] = f"{dno_id}_MANUAL"
        df['ingested_at'] = pd.Timestamp.now()

        table_id = f"{self.client.project}.{self.dataset}.{table_name}"

        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            autodetect=True
        )

        job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()

        logger.info(f"✅ Loaded {len(df)} rows to {table_name}")
'''

        # Add specific processors for each successful download
        for filename, info in analysis["data_summary"].items():
            method_name = filename.replace(".csv", "").replace("-", "_")
            dno_name = filename.split("_")[0].upper()

            integration_script += f'''

    def process_{method_name}(self, file_path):
        """Process {filename}."""

        df = pd.read_csv(file_path)

        # Clean column names
        df.columns = [col.lower().replace(' ', '_').replace('(', '').replace(')', '')
                      for col in df.columns]

        # Determine appropriate table based on content
        # You may need to customize this based on actual data structure
        if 'capacity' in file_path.name.lower():
            table_name = 'dno_capacity_data'
        elif 'forecast' in file_path.name.lower() or 'dfes' in file_path.name.lower():
            table_name = 'dno_forecast_data'
        elif 'network' in file_path.name.lower():
            table_name = 'dno_network_data'
        else:
            table_name = 'dno_misc_data'

        self.load_to_bigquery(df, table_name, "{dno_name}")
'''

        integration_script += """

if __name__ == "__main__":
    integrator = DNOManualIntegrator()
    integrator.process_collected_files()
    print("✅ Manual DNO data integration complete!")
"""

        script_path = OUT_DIR / "integrate_manual_dno_data.py"
        with open(script_path, "w") as f:
            f.write(integration_script)

        logger.info(f"✅ Created integration script: {script_path}")


def main():
    """Main execution."""

    logger.info("📥 Manual DNO Data Collection")
    logger.info("=" * 40)

    collector = ManualDNOCollector()

    # Try to collect from each DNO
    collector.collect_ukpn_data()
    collector.collect_nged_data()
    collector.collect_northern_powergrid_data()
    collector.collect_ssen_data()

    # Analyze what we got
    analysis = collector.analyze_collected_data()

    # Create integration script
    collector.create_integration_script(analysis)

    print("\n🎯 MANUAL COLLECTION COMPLETE!")
    print("=" * 35)
    print(f"📁 Data saved to: {OUT_DIR}")
    print(f"📊 Files collected: {len(analysis['files_collected'])}")
    print(f"💾 Total size: {analysis['total_size'] / 1024 / 1024:.1f} MB")

    if analysis["files_collected"]:
        print("\n📋 Successfully collected:")
        for filename in analysis["files_collected"]:
            info = analysis["data_summary"].get(filename, {})
            print(
                f"  • {filename} ({info.get('size_mb', 0):.1f} MB, {info.get('rows', 0):,} rows)"
            )

        print(
            f"\n🔧 Integration script created: {OUT_DIR}/integrate_manual_dno_data.py"
        )
        print("   Run this to load data into BigQuery!")
    else:
        print("\n⚠️  No files collected - all URLs may be restricted")
        print("   Consider contacting DNOs directly for data access")


if __name__ == "__main__":
    main()
