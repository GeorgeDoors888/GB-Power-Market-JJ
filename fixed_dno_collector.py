#!/usr/bin/env python3
"""
Fixed DNO Collector - Using Diagnostic Results
Now with correct API endpoints and pagination
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class FixedDNOCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # Corrected domains and working endpoints
        self.dno_apis = {
            "UKPN": {
                "domain": "https://ukpowernetworks.opendatasoft.com",
                "api_endpoint": "/api/v2/catalog/datasets",
            },
            "SPEN": {
                "domain": "https://spenergynetworks.opendatasoft.com",
                "api_endpoint": "/api/v2/catalog/datasets",
            },
            "NPG": {
                "domain": "https://northernpowergrid.opendatasoft.com",
                "api_endpoint": "/api/v2/catalog/datasets",
            },
            "ENWL": {
                "domain": "https://electricitynorthwest.opendatasoft.com",
                "api_endpoint": "/api/v2/catalog/datasets",
            },
        }

        self.output_dir = Path("dno_data_fixed")
        self.output_dir.mkdir(exist_ok=True)

        self.collection_stats = {
            "start_time": datetime.now().isoformat(),
            "dnos": {},
            "total_datasets": 0,
        }

    def get_all_datasets(self, dno, domain, endpoint):
        """Get all datasets from OpenDataSoft API with proper pagination"""
        logger.info(f"🔍 Collecting all datasets for {dno}")

        url = f"{domain}{endpoint}"
        all_datasets = []
        start = 0
        rows_per_page = 100

        while True:
            try:
                params = {"start": start, "rows": rows_per_page}

                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                datasets = data.get("datasets", [])

                if not datasets:
                    break

                all_datasets.extend(datasets)
                logger.info(
                    f"   Retrieved {len(datasets)} datasets (total: {len(all_datasets)})"
                )

                # Check if we got fewer than requested (last page)
                if len(datasets) < rows_per_page:
                    break

                start += rows_per_page
                time.sleep(0.2)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ Error getting {dno} datasets at start={start}: {e}")
                break

        logger.info(f"✅ {dno} total datasets discovered: {len(all_datasets)}")
        return all_datasets

    def download_dataset(self, dno, dataset_info):
        """Download individual dataset"""
        dataset_id = dataset_info.get("dataset_id")
        title = (
            dataset_info.get("metas", {}).get("default", {}).get("title", dataset_id)
        )

        domain = self.dno_apis[dno]["domain"]

        # Try CSV export first
        csv_url = f"{domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"

        try:
            response = self.session.get(csv_url, timeout=60)
            if response.status_code == 200:
                # Save CSV
                filename = f"{dno}_{dataset_id}.csv"
                filepath = self.output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(response.content)

                # Try to read as DataFrame for validation
                try:
                    df = pd.read_csv(filepath)
                    logger.info(
                        f"✅ {dno}/{dataset_id}: {len(df)} rows saved to {filename}"
                    )

                    return {
                        "dataset_id": dataset_id,
                        "title": title,
                        "filename": filename,
                        "rows": len(df),
                        "columns": len(df.columns),
                        "status": "success",
                    }
                except Exception as e:
                    logger.warning(
                        f"⚠️ {dno}/{dataset_id}: File saved but couldn't read as DataFrame: {e}"
                    )
                    return {
                        "dataset_id": dataset_id,
                        "title": title,
                        "filename": filename,
                        "rows": "unknown",
                        "status": "saved_but_unreadable",
                    }
            else:
                logger.warning(
                    f"⚠️ {dno}/{dataset_id}: CSV export failed ({response.status_code})"
                )

        except Exception as e:
            logger.warning(f"⚠️ {dno}/{dataset_id}: Download failed: {e}")

        return {"dataset_id": dataset_id, "title": title, "status": "failed"}

    def collect_dno_data(self, dno):
        """Collect all data for one DNO"""
        logger.info(f"🚀 Starting {dno} collection")

        api_info = self.dno_apis[dno]
        domain = api_info["domain"]
        endpoint = api_info["api_endpoint"]

        # Get all datasets
        datasets = self.get_all_datasets(dno, domain, endpoint)

        if not datasets:
            logger.warning(f"⚠️ No datasets found for {dno}")
            return {"datasets_found": 0, "downloads": []}

        # Download each dataset
        downloads = []
        successful_downloads = 0

        for i, dataset in enumerate(datasets, 1):
            logger.info(f"📥 Downloading {dno} dataset {i}/{len(datasets)}")
            result = self.download_dataset(dno, dataset)
            downloads.append(result)

            if result.get("status") == "success":
                successful_downloads += 1

            time.sleep(0.3)  # Rate limiting

        logger.info(
            f"✅ {dno} complete: {successful_downloads}/{len(datasets)} successful downloads"
        )

        return {
            "datasets_found": len(datasets),
            "successful_downloads": successful_downloads,
            "downloads": downloads,
        }

    def run_collection(self):
        """Run collection for all DNOs"""
        logger.info("🚀 Starting fixed DNO data collection")

        for dno in self.dno_apis.keys():
            logger.info(f"{'='*60}")
            logger.info(f"Processing {dno}")
            logger.info(f"{'='*60}")

            try:
                results = self.collect_dno_data(dno)
                self.collection_stats["dnos"][dno] = results
                self.collection_stats["total_datasets"] += results[
                    "successful_downloads"
                ]

            except Exception as e:
                logger.error(f"❌ Failed to collect {dno}: {e}")
                self.collection_stats["dnos"][dno] = {"error": str(e)}

        # Save final stats
        self.collection_stats["end_time"] = datetime.now().isoformat()

        with open(self.output_dir / "collection_stats.json", "w") as f:
            json.dump(self.collection_stats, f, indent=2, default=str)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print collection summary"""
        print("\n" + "=" * 70)
        print("🎯 FIXED DNO COLLECTION SUMMARY")
        print("=" * 70)

        total_found = 0
        total_downloaded = 0

        for dno, stats in self.collection_stats["dnos"].items():
            if "error" in stats:
                print(f"{dno:10} | ERROR: {stats['error']}")
            else:
                found = stats.get("datasets_found", 0)
                downloaded = stats.get("successful_downloads", 0)
                total_found += found
                total_downloaded += downloaded
                print(f"{dno:10} | {found:3} found | {downloaded:3} downloaded")

        print("=" * 70)
        print(f"{'TOTAL':10} | {total_found:3} found | {total_downloaded:3} downloaded")
        print(
            f"Success rate: {total_downloaded/total_found*100:.1f}%"
            if total_found > 0
            else "No datasets found"
        )
        print(f"Files saved to: {self.output_dir}")


def main():
    collector = FixedDNOCollector()
    collector.run_collection()


if __name__ == "__main__":
    main()
