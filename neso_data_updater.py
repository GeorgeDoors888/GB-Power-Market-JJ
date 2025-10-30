#!/usr/bin/env python3
"""
NESO Data Integration Module
Handles incremental updates for NESO (National Energy System Operator) data
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

from automated_data_tracker import DataTracker

logger = logging.getLogger(__name__)


class NESODataUpdater:
    """Handles NESO data updates with Google Sheets tracking"""

    def __init__(self):
        self.tracker = DataTracker()
        self.base_url = "https://data.nationalgrideso.com/api/3/action"

    def get_available_datasets(self) -> List[Dict]:
        """Get list of available NESO datasets"""
        try:
            response = requests.get(f"{self.base_url}/package_list")
            response.raise_for_status()

            datasets = []
            package_list = response.json()["result"]

            # Get details for each dataset
            for package_id in package_list[:10]:  # Limit to first 10 for now
                try:
                    detail_response = requests.get(
                        f"{self.base_url}/package_show", params={"id": package_id}
                    )
                    detail_response.raise_for_status()
                    datasets.append(detail_response.json()["result"])
                except Exception as e:
                    logger.warning(f"Could not get details for {package_id}: {e}")

            return datasets

        except Exception as e:
            logger.error(f"Failed to get NESO datasets: {e}")
            return []

    def check_for_updates(self, dataset_id: str, last_check: datetime) -> bool:
        """Check if a NESO dataset has been updated since last check"""
        try:
            response = requests.get(
                f"{self.base_url}/package_show", params={"id": dataset_id}
            )
            response.raise_for_status()

            dataset_info = response.json()["result"]

            # Check metadata_modified timestamp
            if "metadata_modified" in dataset_info:
                modified_str = dataset_info["metadata_modified"]
                modified_time = datetime.fromisoformat(
                    modified_str.replace("Z", "+00:00")
                )

                return modified_time > last_check

            return True  # If no timestamp, assume it needs updating

        except Exception as e:
            logger.error(f"Failed to check updates for {dataset_id}: {e}")
            return False

    def download_dataset(
        self, dataset_id: str, output_dir: str = "neso_data"
    ) -> Optional[str]:
        """Download a NESO dataset"""
        try:
            os.makedirs(output_dir, exist_ok=True)

            response = requests.get(
                f"{self.base_url}/package_show", params={"id": dataset_id}
            )
            response.raise_for_status()

            dataset_info = response.json()["result"]

            if not dataset_info.get("resources"):
                logger.warning(f"No resources found for dataset {dataset_id}")
                return None

            # Download the first CSV resource
            for resource in dataset_info["resources"]:
                if resource.get("format", "").upper() == "CSV":
                    download_url = resource["url"]
                    filename = (
                        f"{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    )
                    filepath = os.path.join(output_dir, filename)

                    logger.info(f"Downloading {dataset_id} from {download_url}")

                    download_response = requests.get(download_url, stream=True)
                    download_response.raise_for_status()

                    with open(filepath, "wb") as f:
                        for chunk in download_response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    logger.info(f"Downloaded {dataset_id} to {filepath}")
                    return filepath

            logger.warning(f"No CSV resources found for dataset {dataset_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to download dataset {dataset_id}: {e}")
            return None

    def update_neso_data(self) -> Dict:
        """Main function to update NESO data"""
        logger.info("🔄 Starting NESO data update...")

        try:
            # Get last update time from Google Sheets
            last_times = self.tracker.get_last_ingestion_times()
            neso_last = last_times.get(
                "NESO_ALL", datetime.now(timezone.utc) - timedelta(hours=24)
            )

            current_time = datetime.now(timezone.utc)
            time_since_neso = current_time - neso_last

            logger.info(
                f"Last NESO update: {neso_last} ({time_since_neso.total_seconds()/60:.1f} minutes ago)"
            )

            # Only update if it's been more than 1 hour (NESO data updates less frequently)
            if time_since_neso.total_seconds() < 3600:  # 1 hour
                logger.info("⏭️  NESO data is recent enough, skipping update")
                return {
                    "action": "skip",
                    "reason": "neso_too_recent",
                    "time_since_last": time_since_neso.total_seconds() / 60,
                }

            # Get available datasets
            datasets = self.get_available_datasets()
            if not datasets:
                logger.warning("No NESO datasets found")
                return {"action": "error", "error": "no_datasets_found"}

            # Update tracking
            self.tracker.update_ingestion_time("NESO", "ALL", current_time, "STARTED")

            updated_count = 0
            for dataset in datasets:
                dataset_id = dataset.get("name", "unknown")

                if self.check_for_updates(dataset_id, neso_last):
                    logger.info(f"Updating dataset: {dataset_id}")

                    # Download the dataset
                    filepath = self.download_dataset(dataset_id)
                    if filepath:
                        updated_count += 1
                        logger.info(f"✅ Updated {dataset_id}")
                    else:
                        logger.warning(f"⚠️  Failed to download {dataset_id}")
                else:
                    logger.info(f"⏭️  No updates needed for {dataset_id}")

            # Update tracking with success
            self.tracker.update_ingestion_time("NESO", "ALL", current_time, "SUCCESS")

            logger.info(f"✅ NESO update completed. Updated {updated_count} datasets.")

            return {
                "action": "neso_update",
                "updated_count": updated_count,
                "total_datasets": len(datasets),
            }

        except Exception as e:
            logger.error(f"NESO update failed: {e}")

            # Update tracking with failure
            try:
                self.tracker.update_ingestion_time(
                    "NESO", "ALL", datetime.now(timezone.utc), "FAILED"
                )
            except:
                pass

            return {"action": "error", "error": str(e)}


def main():
    """Main function for NESO data updates"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    updater = NESODataUpdater()
    result = updater.update_neso_data()

    print(f"NESO update result: {result}")
    return result


if __name__ == "__main__":
    main()
