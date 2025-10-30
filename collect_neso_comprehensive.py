#!/usr/bin/env python3
"""
NESO Comprehensive Data Collector
=================================

Comprehensive collection from all accessible NESO APIs and datasets.
Focuses on data NOT available in BMRS to complement our energy intelligence platform.

Based on official NESO API documentation and testing results:
- ✅ Carbon Intensity API (fully accessible)
- ✅ NESO Data Portal API (121 datasets available)
- ❌ Authenticated APIs (require special access)
"""

import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from google.cloud import bigquery
from requests.adapters import HTTPAdapter, Retry

# Configuration
OUTPUT_DIR = Path("neso_data_comprehensive")
DB_PATH = OUTPUT_DIR / "neso_comprehensive.sqlite"
BIGQUERY_PROJECT = "jibber-jabber-knowledge"
BIGQUERY_DATASET = "uk_energy_insights"

# Setup logging
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_DIR / "collection.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


# HTTP Session with retry logic
def create_session() -> requests.Session:
    """Create robust HTTP session."""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "NESO-Comprehensive-Collector/1.0 (Energy Research)",
            "Accept": "application/json, text/csv, */*",
        }
    )
    return session


SESSION = create_session()


class NESODataCollector:
    """Main NESO data collection orchestrator."""

    def __init__(self):
        self.session = SESSION
        self.collected_datasets = []
        self.collection_stats = {
            "start_time": datetime.now(),
            "datasets_attempted": 0,
            "datasets_successful": 0,
            "total_records": 0,
            "total_size_mb": 0,
        }

    def save_dataframe(
        self, df: pd.DataFrame, name: str, source: str, metadata: Dict = None
    ):
        """Save DataFrame with metadata."""
        if df.empty:
            logger.warning(f"Empty dataset: {source}/{name}")
            return

        # Create source directory
        source_dir = OUTPUT_DIR / source
        source_dir.mkdir(parents=True, exist_ok=True)

        # Save as Parquet (primary format)
        parquet_path = source_dir / f"{name}.parquet"
        df.to_parquet(parquet_path, index=False)

        # Save as CSV (backup/readable)
        csv_path = source_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)

        # Save metadata
        if metadata:
            metadata_path = source_dir / f"{name}_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2, default=str)

        # Save to SQLite
        table_name = f"{source}__{name}"
        with sqlite3.connect(DB_PATH) as conn:
            df.to_sql(table_name, conn, if_exists="replace", index=False)

        # Update stats
        size_mb = parquet_path.stat().st_size / (1024 * 1024)
        self.collection_stats["total_records"] += len(df)
        self.collection_stats["total_size_mb"] += size_mb

        logger.info(f"✅ Saved {source}/{name}: {len(df):,} records ({size_mb:.2f} MB)")

        # Track for BigQuery upload
        self.collected_datasets.append(
            {
                "name": name,
                "source": source,
                "dataframe": df,
                "metadata": metadata,
                "records": len(df),
                "size_mb": size_mb,
            }
        )

    def upload_to_bigquery(self):
        """Batch upload all collected data to BigQuery."""
        if not self.collected_datasets:
            logger.warning("No datasets to upload to BigQuery")
            return

        try:
            client = bigquery.Client(project=BIGQUERY_PROJECT)

            for dataset in self.collected_datasets:
                table_name = f"neso_{dataset['source']}_{dataset['name']}"
                table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{table_name}"

                # Configure job
                job_config = bigquery.LoadJobConfig(
                    write_disposition="WRITE_TRUNCATE", autodetect=True
                )

                # Upload
                job = client.load_table_from_dataframe(
                    dataset["dataframe"], table_id, job_config=job_config
                )
                job.result()  # Wait for completion

                logger.info(
                    f"✅ BigQuery: {table_name} ({dataset['records']:,} records)"
                )

        except Exception as e:
            logger.error(f"❌ BigQuery upload failed: {e}")


class CarbonIntensityCollector:
    """Carbon Intensity API collector."""

    def __init__(self, collector: NESODataCollector):
        self.collector = collector
        self.base_url = "https://api.carbonintensity.org.uk"

    def collect_all(self):
        """Collect all carbon intensity data."""
        logger.info("🌱 Collecting Carbon Intensity Data")

        # Current intensity
        self._collect_current_intensity()

        # Generation mix
        self._collect_generation_mix()

        # Regional data
        self._collect_regional_data()

        # Intensity factors
        self._collect_intensity_factors()

        # Historical data (7 days)
        self._collect_historical_data(days=7)

        # Statistics
        self._collect_statistics()

    def _collect_current_intensity(self):
        """Current carbon intensity."""
        try:
            response = self.collector.session.get(
                f"{self.base_url}/intensity", timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data["data"])
                metadata = {"source": "Carbon Intensity API", "endpoint": "/intensity"}
                self.collector.save_dataframe(
                    df, "current_intensity", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.error(f"❌ Current intensity failed: {e}")

    def _collect_generation_mix(self):
        """Current generation mix."""
        try:
            response = self.collector.session.get(
                f"{self.base_url}/generation", timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # Flatten generation mix
                records = []
                for entry in data["data"]:
                    for fuel in entry["generationmix"]:
                        record = {
                            "from": entry["from"],
                            "to": entry["to"],
                            "fuel": fuel["fuel"],
                            "percentage": fuel["perc"],
                        }
                        records.append(record)

                df = pd.DataFrame(records)
                metadata = {"source": "Carbon Intensity API", "endpoint": "/generation"}
                self.collector.save_dataframe(
                    df, "generation_mix", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.error(f"❌ Generation mix failed: {e}")

    def _collect_regional_data(self):
        """Regional carbon intensity."""
        try:
            response = self.collector.session.get(
                f"{self.base_url}/regional", timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                # Flatten regional data
                records = []
                for entry in data["data"]:
                    for region in entry["regions"]:
                        record = {
                            "from": entry["from"],
                            "to": entry["to"],
                            "regionid": region["regionid"],
                            "dnoregion": region["dnoregion"],
                            "shortname": region["shortname"],
                            "intensity_forecast": region["intensity"]["forecast"],
                            "intensity_index": region["intensity"]["index"],
                        }

                        # Add generation mix if available
                        if "generationmix" in region:
                            for fuel in region["generationmix"]:
                                record[f"gen_{fuel['fuel']}"] = fuel["perc"]

                        records.append(record)

                df = pd.DataFrame(records)
                metadata = {"source": "Carbon Intensity API", "endpoint": "/regional"}
                self.collector.save_dataframe(
                    df, "regional_intensity", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.error(f"❌ Regional data failed: {e}")

    def _collect_intensity_factors(self):
        """Intensity factors by fuel type."""
        try:
            response = self.collector.session.get(
                f"{self.base_url}/intensity/factors", timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data["data"])
                metadata = {
                    "source": "Carbon Intensity API",
                    "endpoint": "/intensity/factors",
                }
                self.collector.save_dataframe(
                    df, "intensity_factors", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.error(f"❌ Intensity factors failed: {e}")

    def _collect_historical_data(self, days: int = 7):
        """Historical carbon intensity."""
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            # Format for API
            start_str = start_time.strftime("%Y-%m-%dT%H:%MZ")
            end_str = end_time.strftime("%Y-%m-%dT%H:%MZ")

            url = f"{self.base_url}/intensity/{start_str}/{end_str}"
            response = self.collector.session.get(url, timeout=60)

            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data["data"])
                metadata = {
                    "source": "Carbon Intensity API",
                    "endpoint": f"/intensity/{start_str}/{end_str}",
                    "days": days,
                }
                self.collector.save_dataframe(
                    df, f"historical_{days}d", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.error(f"❌ Historical data failed: {e}")

    def _collect_statistics(self):
        """Statistics endpoint if available."""
        try:
            response = self.collector.session.get(
                f"{self.base_url}/intensity/stats", timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                df = pd.json_normalize(data["data"])
                metadata = {
                    "source": "Carbon Intensity API",
                    "endpoint": "/intensity/stats",
                }
                self.collector.save_dataframe(
                    df, "statistics", "carbon_intensity", metadata
                )
        except Exception as e:
            logger.debug(f"Statistics endpoint not available: {e}")


class NESODataPortalCollector:
    """NESO Data Portal collector."""

    def __init__(self, collector: NESODataCollector):
        self.collector = collector
        self.base_url = "https://api.neso.energy/api/3/action"

    def collect_all(self):
        """Collect priority NESO Data Portal datasets."""
        logger.info("📊 Collecting NESO Data Portal Datasets")

        # First get catalog information
        self._collect_catalog_info()

        # Collect priority datasets (unique from BMRS)
        priority_datasets = [
            "embedded-wind-and-solar-forecasts",
            "1-day-ahead-demand-forecast",
            "2-day-ahead-demand-forecast",
            "7-day-ahead-national-forecast",
            "2-14-days-ahead-national-demand-forecast",
            "balancing-services-use-of-system-bsuos-daily-forecast",
            "bsuos-monthly-forecast",
            "bsuos-fixed-tariffs",
            "carbon-intensity-of-balancing-actions",
            "capacity-market-register",
            "constraint-management-pathfinder-results",
            "24-months-ahead-constraint-cost-forecast",
            "demand-flexibility-service-dfs",
            "system-warnings",
            "frequency-risk-control-report",
            "monthly-balancing-services-summary",
            "transmission-losses-multipliers",
        ]

        for dataset_id in priority_datasets:
            self._collect_dataset(dataset_id)
            time.sleep(1)  # Respect rate limits

    def _collect_catalog_info(self):
        """Collect catalog metadata."""
        try:
            # Organizations
            response = self.collector.session.get(f"{self.base_url}/organization_list")
            if response.status_code == 200:
                orgs = response.json()["result"]
                df = pd.DataFrame([{"organization": org} for org in orgs])
                self.collector.save_dataframe(
                    df,
                    "organizations",
                    "catalog",
                    {"source": "NESO Data Portal", "endpoint": "/organization_list"},
                )

            # All packages
            response = self.collector.session.get(f"{self.base_url}/package_list")
            if response.status_code == 200:
                packages = response.json()["result"]
                df = pd.DataFrame([{"package_id": pkg} for pkg in packages])
                self.collector.save_dataframe(
                    df,
                    "available_datasets",
                    "catalog",
                    {
                        "source": "NESO Data Portal",
                        "endpoint": "/package_list",
                        "total_datasets": len(packages),
                    },
                )

            # Tags
            response = self.collector.session.get(f"{self.base_url}/tag_list")
            if response.status_code == 200:
                tags = response.json()["result"]
                df = pd.DataFrame([{"tag": tag} for tag in tags])
                self.collector.save_dataframe(
                    df,
                    "tags",
                    "catalog",
                    {"source": "NESO Data Portal", "endpoint": "/tag_list"},
                )

        except Exception as e:
            logger.error(f"❌ Catalog collection failed: {e}")

    def _collect_dataset(self, dataset_id: str):
        """Collect specific dataset."""
        try:
            self.collector.collection_stats["datasets_attempted"] += 1

            # Get dataset metadata
            response = self.collector.session.get(
                f"{self.base_url}/package_show?id={dataset_id}"
            )
            if response.status_code != 200:
                logger.warning(f"❌ Dataset {dataset_id} not accessible")
                return

            package_data = response.json()["result"]
            resources = package_data.get("resources", [])

            if not resources:
                logger.warning(f"⚠️ No resources in {dataset_id}")
                return

            # Collect data from resources
            dataset_collected = False
            for resource in resources:
                if self._collect_resource(dataset_id, resource, package_data):
                    dataset_collected = True

            if dataset_collected:
                self.collector.collection_stats["datasets_successful"] += 1
                logger.info(f"✅ Completed dataset: {dataset_id}")

        except Exception as e:
            logger.error(f"❌ Dataset {dataset_id} failed: {e}")

    def _collect_resource(
        self, dataset_id: str, resource: Dict, package_data: Dict
    ) -> bool:
        """Collect individual resource (data file)."""
        try:
            resource_id = resource.get("id")
            resource_name = resource.get("name", "unnamed")
            resource_format = resource.get("format", "").lower()

            # Skip non-data formats
            if resource_format not in ["csv", "json", "xlsx", "xls"]:
                logger.debug(f"Skipping {resource_name} (format: {resource_format})")
                return False

            # Try datastore API first (most efficient)
            df = self._try_datastore_api(resource_id)

            # Fallback to direct download
            if df is None:
                df = self._try_direct_download(resource)

            if df is not None:
                # Clean name for filesystem
                clean_name = f"{dataset_id}_{resource_name}".replace(" ", "_").replace(
                    "/", "_"
                )
                clean_name = "".join(
                    c for c in clean_name if c.isalnum() or c in "_-."
                )[:100]

                metadata = {
                    "source": "NESO Data Portal",
                    "dataset_id": dataset_id,
                    "dataset_title": package_data.get("title", ""),
                    "resource_id": resource_id,
                    "resource_name": resource_name,
                    "resource_format": resource_format,
                    "last_modified": resource.get("last_modified"),
                    "size": resource.get("size"),
                    "description": package_data.get("notes", ""),
                }

                self.collector.save_dataframe(df, clean_name, "neso_portal", metadata)
                return True

            return False

        except Exception as e:
            logger.debug(
                f"Resource collection failed for {resource.get('name', 'unknown')}: {e}"
            )
            return False

    def _try_datastore_api(self, resource_id: str) -> Optional[pd.DataFrame]:
        """Try NESO datastore API."""
        try:
            # Use datastore_search with limit
            url = f"{self.base_url}/datastore_search"
            params = {
                "resource_id": resource_id,
                "limit": 10000,  # Start with reasonable limit
            }

            response = self.collector.session.get(url, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "records" in data["result"]:
                    records = data["result"]["records"]
                    if records:
                        df = pd.DataFrame(records)
                        # Remove CKAN metadata columns
                        df = df.drop(columns=["_id"], errors="ignore")
                        return df
        except Exception as e:
            logger.debug(f"Datastore API failed for {resource_id}: {e}")

        return None

    def _try_direct_download(self, resource: Dict) -> Optional[pd.DataFrame]:
        """Try direct download of resource."""
        try:
            url = resource.get("url")
            if not url:
                return None

            response = self.collector.session.get(url, timeout=120)
            if response.status_code != 200:
                return None

            format_type = resource.get("format", "").lower()

            if format_type == "csv":
                # Try different encodings
                for encoding in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        content = response.content.decode(encoding)
                        from io import StringIO

                        return pd.read_csv(StringIO(content))
                    except:
                        continue

            elif format_type in ["xlsx", "xls"]:
                from io import BytesIO

                return pd.read_excel(BytesIO(response.content))

            elif format_type == "json":
                data = response.json()
                if isinstance(data, list):
                    return pd.DataFrame(data)
                elif isinstance(data, dict):
                    return pd.json_normalize(data)

        except Exception as e:
            logger.debug(f"Direct download failed: {e}")

        return None


def create_collection_summary(collector: NESODataCollector):
    """Create comprehensive collection summary."""
    logger.info("📋 Creating Collection Summary")

    stats = collector.collection_stats
    duration = datetime.now() - stats["start_time"]

    summary = {
        "collection_timestamp": datetime.now(),
        "duration_minutes": duration.total_seconds() / 60,
        "datasets_attempted": stats["datasets_attempted"],
        "datasets_successful": stats["datasets_successful"],
        "success_rate": (
            (stats["datasets_successful"] / stats["datasets_attempted"] * 100)
            if stats["datasets_attempted"] > 0
            else 0
        ),
        "total_records": stats["total_records"],
        "total_size_mb": stats["total_size_mb"],
        "datasets_collected": len(collector.collected_datasets),
    }

    # Save summary
    summary_df = pd.DataFrame([summary])
    collector.save_dataframe(summary_df, "collection_summary", "meta", summary)

    # Log summary
    logger.info("📊 COLLECTION SUMMARY")
    logger.info("=" * 30)
    logger.info(f"Duration: {summary['duration_minutes']:.1f} minutes")
    logger.info(
        f"Datasets: {summary['datasets_successful']}/{summary['datasets_attempted']} ({summary['success_rate']:.1f}%)"
    )
    logger.info(f"Records: {summary['total_records']:,}")
    logger.info(f"Size: {summary['total_size_mb']:.2f} MB")

    # Dataset breakdown
    logger.info("\n📈 Datasets by Source:")
    source_stats = {}
    for dataset in collector.collected_datasets:
        source = dataset["source"]
        if source not in source_stats:
            source_stats[source] = {"count": 0, "records": 0, "size_mb": 0}
        source_stats[source]["count"] += 1
        source_stats[source]["records"] += dataset["records"]
        source_stats[source]["size_mb"] += dataset["size_mb"]

    for source, stats in source_stats.items():
        logger.info(
            f"  {source}: {stats['count']} datasets, {stats['records']:,} records, {stats['size_mb']:.2f} MB"
        )


def main():
    """Main collection pipeline."""
    logger.info("🚀 NESO Comprehensive Data Collection")
    logger.info("=" * 50)
    logger.info(f"Output: {OUTPUT_DIR}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"BigQuery: {BIGQUERY_PROJECT}.{BIGQUERY_DATASET}")

    try:
        # Initialize collector
        collector = NESODataCollector()

        # Collect Carbon Intensity data
        carbon_collector = CarbonIntensityCollector(collector)
        carbon_collector.collect_all()

        # Collect NESO Data Portal datasets
        portal_collector = NESODataPortalCollector(collector)
        portal_collector.collect_all()

        # Create summary
        create_collection_summary(collector)

        # Upload to BigQuery
        collector.upload_to_bigquery()

        logger.info("✅ NESO data collection completed successfully!")

    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
