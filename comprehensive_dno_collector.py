#!/usr/bin/env python3
"""
Comprehensive Hybrid DNO Data Collection Framework
==================================================

This script implements a multi-strategy approach to collect data from all 6 UK DNOs:

Strategy 1: Working OpenDataSoft APIs (SPEN, ENWL)
Strategy 2: Manual Portal Scraping (SSEN)
Strategy 3: CKAN API Integration (NGED)
Strategy 4: Archive/Manual Downloads (UKPN, NPG)
Strategy 5: Alternative Sources (Government data, FOI requests)

Updated: September 12, 2025
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class ComprehensiveDNOCollector:
    """Unified DNO data collection using multiple strategies"""

    def __init__(self, output_dir: str = "dno_comprehensive_collection"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # DNO configuration with collection strategies
        self.dno_config = {
            "SPEN": {
                "name": "SP Energy Networks",
                "license_areas": ["SPD", "SPM"],
                "strategy": "opendatasoft_working",
                "base_url": "https://spenergynetworks.opendatasoft.com",
                "working_endpoint": "/api/v2/catalog/datasets/{}/exports",
            },
            "ENWL": {
                "name": "Electricity North West",
                "license_areas": ["ENWL"],
                "strategy": "opendatasoft_working",
                "base_url": "https://electricitynorthwest.opendatasoft.com",
                "working_endpoint": "/api/v2/catalog/datasets/{}/exports",
            },
            "SSEN": {
                "name": "Scottish and Southern Electricity Networks",
                "license_areas": ["SSEN-SHE", "SSEN-SEPD"],
                "strategy": "manual_scraping",
                "portal_url": "https://www.ssen.co.uk/our-services/tools-and-data/",
                "data_patterns": [".csv", ".xlsx", ".json"],
            },
            "NGED": {
                "name": "National Grid Electricity Distribution",
                "license_areas": ["WMID", "EMID", "SWALES", "SWEST"],
                "strategy": "ckan_api",
                "ckan_url": "https://connecteddata.nationalgrid.co.uk",
                "requires_token": True,
            },
            "UKPN": {
                "name": "UK Power Networks",
                "license_areas": ["EPN", "LPN", "SPN"],
                "strategy": "archive_manual",
                "status": "Previously collected 8 datasets on 2025-09-11",
                "archive_path": "ukpn_data_collection_20250911_134928/",
            },
            "NPG": {
                "name": "Northern Powergrid",
                "license_areas": ["NPG-NE", "NPG-YS"],
                "strategy": "restricted_manual",
                "portal_url": "https://northernpowergrid.opendatasoft.com",
                "status": "Requires authentication or alternative sources",
            },
        }

        self.collection_results = {
            "timestamp": datetime.now().isoformat(),
            "total_dnos": len(self.dno_config),
            "strategies_used": {},
            "datasets_collected": {},
            "errors": [],
            "summary": {},
        }

    def collect_opendatasoft_working(self, dno_id: str, config: dict) -> dict:
        """Collect from working OpenDataSoft APIs (SPEN, ENWL)"""

        logger.info(f"🔄 Collecting {dno_id} using working OpenDataSoft API")

        results = {
            "dno_id": dno_id,
            "strategy": "opendatasoft_working",
            "datasets_found": 0,
            "datasets_downloaded": 0,
            "files_created": [],
            "errors": [],
        }

        try:
            # Get catalog
            catalog_url = f"{config['base_url']}/api/v2/catalog/datasets"
            response = self.session.get(catalog_url, params={"rows": 100}, timeout=30)

            if response.status_code == 200:
                data = response.json()
                datasets = data.get("datasets", [])
                results["datasets_found"] = len(datasets)

                logger.info(f"📊 Found {len(datasets)} datasets for {dno_id}")

                # Process each dataset
                for i, dataset_info in enumerate(datasets, 1):
                    dataset_data = dataset_info.get("dataset", {})
                    dataset_id = dataset_data.get("dataset_id")

                    if not dataset_id:
                        continue

                    title = (
                        dataset_data.get("metas", {})
                        .get("default", {})
                        .get("title", dataset_id)
                    )
                    logger.info(
                        f"📥 Processing {dno_id} dataset {i}/{len(datasets)}: {dataset_id}"
                    )

                    # Try the working v2.0 exports endpoint
                    exports_url = f"{config['base_url']}/api/v2/catalog/datasets/{dataset_id}/exports"

                    try:
                        exports_response = self.session.get(exports_url, timeout=30)

                        if exports_response.status_code == 200:
                            # Parse available export formats
                            exports_data = exports_response.json()

                            # Save metadata
                            metadata_file = (
                                self.output_dir / f"{dno_id}_{dataset_id}_metadata.json"
                            )
                            metadata = {
                                "dataset_id": dataset_id,
                                "title": title,
                                "dno": dno_id,
                                "exports_available": exports_data,
                                "collection_timestamp": datetime.now().isoformat(),
                            }

                            with open(metadata_file, "w") as f:
                                json.dump(metadata, f, indent=2)

                            results["files_created"].append(str(metadata_file))
                            results["datasets_downloaded"] += 1

                            logger.info(f"✅ {dno_id}/{dataset_id}: Metadata saved")

                        else:
                            logger.warning(
                                f"⚠️ {dno_id}/{dataset_id}: Exports endpoint failed ({exports_response.status_code})"
                            )

                    except Exception as e:
                        error_msg = f"Error processing {dataset_id}: {e}"
                        results["errors"].append(error_msg)
                        logger.error(f"❌ {error_msg}")

                    time.sleep(0.5)  # Rate limiting

            else:
                error_msg = (
                    f"Catalog access failed for {dno_id}: {response.status_code}"
                )
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")

        except Exception as e:
            error_msg = f"Failed to collect {dno_id}: {e}"
            results["errors"].append(error_msg)
            logger.error(f"💥 {error_msg}")

        return results

    def collect_manual_scraping(self, dno_id: str, config: dict) -> dict:
        """Collect using manual portal scraping (SSEN)"""

        logger.info(f"🔄 Collecting {dno_id} using manual portal scraping")

        results = {
            "dno_id": dno_id,
            "strategy": "manual_scraping",
            "datasets_found": 0,
            "datasets_downloaded": 0,
            "files_created": [],
            "errors": [],
        }

        try:
            # Scrape SSEN portal for data links
            response = self.session.get(config["portal_url"], timeout=30)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")

                # Find data download links
                data_links = []
                for pattern in config["data_patterns"]:
                    links = soup.find_all(
                        "a", href=lambda x: x and pattern in x.lower()
                    )
                    data_links.extend(links)

                results["datasets_found"] = len(data_links)
                logger.info(
                    f"📊 Found {len(data_links)} potential data links for {dno_id}"
                )

                # Process each link
                for i, link in enumerate(data_links, 1):
                    href = link.get("href")
                    text = link.get_text(strip=True)

                    if href:
                        # Make URL absolute
                        if href.startswith("/"):
                            href = urljoin(config["portal_url"], href)

                        logger.info(
                            f"📥 Processing {dno_id} link {i}/{len(data_links)}: {text}"
                        )

                        try:
                            # Download the file
                            file_response = self.session.get(href, timeout=60)

                            if file_response.status_code == 200:
                                # Determine filename
                                filename = href.split("/")[-1]
                                if not filename or "." not in filename:
                                    filename = f"{dno_id}_dataset_{i}.csv"

                                output_file = self.output_dir / f"{dno_id}_{filename}"

                                with open(output_file, "wb") as f:
                                    f.write(file_response.content)

                                results["files_created"].append(str(output_file))
                                results["datasets_downloaded"] += 1

                                logger.info(f"✅ {dno_id}: Downloaded {filename}")
                            else:
                                logger.warning(
                                    f"⚠️ {dno_id}: Failed to download {href} ({file_response.status_code})"
                                )

                        except Exception as e:
                            error_msg = f"Error downloading {href}: {e}"
                            results["errors"].append(error_msg)
                            logger.error(f"❌ {error_msg}")

                    time.sleep(1)  # Rate limiting for scraping

            else:
                error_msg = f"Portal access failed for {dno_id}: {response.status_code}"
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")

        except Exception as e:
            error_msg = f"Failed to scrape {dno_id}: {e}"
            results["errors"].append(error_msg)
            logger.error(f"💥 {error_msg}")

        return results

    def collect_ckan_api(self, dno_id: str, config: dict) -> dict:
        """Collect using CKAN API (NGED)"""

        logger.info(f"🔄 Collecting {dno_id} using CKAN API")

        results = {
            "dno_id": dno_id,
            "strategy": "ckan_api",
            "datasets_found": 0,
            "datasets_downloaded": 0,
            "files_created": [],
            "errors": [],
        }

        # Check for API token
        api_token = os.environ.get("NGED_API_TOKEN")
        if not api_token:
            error_msg = "NGED_API_TOKEN environment variable not set"
            results["errors"].append(error_msg)
            logger.warning(f"⚠️ {error_msg}")
            return results

        try:
            # Search for datasets
            search_url = f"{config['ckan_url']}/api/3/action/package_search"
            search_params = {"q": "*", "rows": 100}

            headers = {"Authorization": api_token}
            response = self.session.get(
                search_url, params=search_params, headers=headers, timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                datasets = data.get("result", {}).get("results", [])
                results["datasets_found"] = len(datasets)

                logger.info(f"📊 Found {len(datasets)} datasets for {dno_id}")

                # Process each dataset
                for i, dataset in enumerate(datasets, 1):
                    dataset_id = dataset.get("id")
                    title = dataset.get("title", dataset_id)

                    logger.info(
                        f"📥 Processing {dno_id} dataset {i}/{len(datasets)}: {title}"
                    )

                    # Save metadata
                    metadata_file = (
                        self.output_dir / f"{dno_id}_{dataset_id}_metadata.json"
                    )
                    metadata = {
                        "dataset_id": dataset_id,
                        "title": title,
                        "dno": dno_id,
                        "ckan_data": dataset,
                        "collection_timestamp": datetime.now().isoformat(),
                    }

                    with open(metadata_file, "w") as f:
                        json.dump(metadata, f, indent=2)

                    results["files_created"].append(str(metadata_file))
                    results["datasets_downloaded"] += 1

                    # Try to download resources if available
                    resources = dataset.get("resources", [])
                    for resource in resources:
                        resource_url = resource.get("url")
                        if resource_url:
                            try:
                                resource_response = self.session.get(
                                    resource_url, timeout=60
                                )
                                if resource_response.status_code == 200:
                                    resource_filename = f"{dno_id}_{dataset_id}_{resource.get('id', 'resource')}.csv"
                                    resource_file = self.output_dir / resource_filename

                                    with open(resource_file, "wb") as f:
                                        f.write(resource_response.content)

                                    results["files_created"].append(str(resource_file))
                                    logger.info(
                                        f"✅ {dno_id}: Downloaded resource {resource_filename}"
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"⚠️ Failed to download resource {resource_url}: {e}"
                                )

                    time.sleep(0.5)

            else:
                error_msg = f"CKAN API failed for {dno_id}: {response.status_code}"
                results["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")

        except Exception as e:
            error_msg = f"Failed to collect from CKAN for {dno_id}: {e}"
            results["errors"].append(error_msg)
            logger.error(f"💥 {error_msg}")

        return results

    def collect_archive_manual(self, dno_id: str, config: dict) -> dict:
        """Handle previously collected data (UKPN)"""

        logger.info(f"🔄 Processing archived data for {dno_id}")

        results = {
            "dno_id": dno_id,
            "strategy": "archive_manual",
            "datasets_found": 0,
            "datasets_downloaded": 0,
            "files_created": [],
            "errors": [],
            "status": config.get("status", "Unknown archive status"),
        }

        # Check if archive directory exists
        archive_path = Path(config.get("archive_path", ""))

        if archive_path.exists():
            # Count existing files
            csv_files = list(archive_path.glob("*.csv"))
            json_files = list(archive_path.glob("*.json"))

            results["datasets_found"] = len(csv_files)
            results["datasets_downloaded"] = len(csv_files)
            results["files_created"] = [str(f) for f in csv_files + json_files]

            logger.info(
                f"✅ {dno_id}: Found {len(csv_files)} CSV files and {len(json_files)} metadata files in archive"
            )
        else:
            error_msg = f"Archive path not found: {archive_path}"
            results["errors"].append(error_msg)
            logger.warning(f"⚠️ {error_msg}")

        return results

    def collect_restricted_manual(self, dno_id: str, config: dict) -> dict:
        """Handle restricted access DNOs (NPG)"""

        logger.info(f"🔄 Attempting restricted collection for {dno_id}")

        results = {
            "dno_id": dno_id,
            "strategy": "restricted_manual",
            "datasets_found": 0,
            "datasets_downloaded": 0,
            "files_created": [],
            "errors": [],
            "recommendations": [],
        }

        # Document alternative approaches
        recommendations = [
            "Contact DNO directly for data access permissions",
            "Check for government open data portals",
            "Look for FOI (Freedom of Information) request datasets",
            "Monitor for API access policy changes",
            "Check third-party energy data aggregators",
        ]

        results["recommendations"] = recommendations

        # Save a strategy document
        strategy_file = self.output_dir / f"{dno_id}_collection_strategy.json"
        strategy_doc = {
            "dno_id": dno_id,
            "name": config["name"],
            "status": "Restricted access - requires alternative approaches",
            "portal_url": config.get("portal_url"),
            "recommendations": recommendations,
            "last_checked": datetime.now().isoformat(),
        }

        with open(strategy_file, "w") as f:
            json.dump(strategy_doc, f, indent=2)

        results["files_created"].append(str(strategy_file))

        logger.info(f"📝 {dno_id}: Strategy document created with recommendations")

        return results

    def run_comprehensive_collection(self) -> dict:
        """Execute collection for all DNOs using appropriate strategies"""

        logger.info("🚀 Starting Comprehensive DNO Data Collection")
        logger.info("=" * 60)

        start_time = datetime.now()

        for dno_id, config in self.dno_config.items():
            logger.info(f"\n📋 Processing {dno_id} ({config['name']})")
            logger.info(f"Strategy: {config['strategy']}")

            # Route to appropriate collection method
            if config["strategy"] == "opendatasoft_working":
                result = self.collect_opendatasoft_working(dno_id, config)
            elif config["strategy"] == "manual_scraping":
                result = self.collect_manual_scraping(dno_id, config)
            elif config["strategy"] == "ckan_api":
                result = self.collect_ckan_api(dno_id, config)
            elif config["strategy"] == "archive_manual":
                result = self.collect_archive_manual(dno_id, config)
            elif config["strategy"] == "restricted_manual":
                result = self.collect_restricted_manual(dno_id, config)
            else:
                result = {
                    "dno_id": dno_id,
                    "strategy": config["strategy"],
                    "error": "Unknown strategy",
                }

            # Store results
            self.collection_results["datasets_collected"][dno_id] = result

            if config["strategy"] not in self.collection_results["strategies_used"]:
                self.collection_results["strategies_used"][config["strategy"]] = []
            self.collection_results["strategies_used"][config["strategy"]].append(
                dno_id
            )

            # Log summary for this DNO
            datasets_collected = result.get("datasets_downloaded", 0)
            files_created = len(result.get("files_created", []))
            errors_count = len(result.get("errors", []))

            logger.info(
                f"📊 {dno_id} Summary: {datasets_collected} datasets, {files_created} files, {errors_count} errors"
            )

            time.sleep(1)  # Brief pause between DNOs

        # Generate final summary
        end_time = datetime.now()
        duration = end_time - start_time

        total_datasets = sum(
            result.get("datasets_downloaded", 0)
            for result in self.collection_results["datasets_collected"].values()
        )
        total_files = sum(
            len(result.get("files_created", []))
            for result in self.collection_results["datasets_collected"].values()
        )
        total_errors = sum(
            len(result.get("errors", []))
            for result in self.collection_results["datasets_collected"].values()
        )

        self.collection_results["summary"] = {
            "duration_seconds": duration.total_seconds(),
            "total_datasets_collected": total_datasets,
            "total_files_created": total_files,
            "total_errors": total_errors,
            "dnos_processed": len(self.dno_config),
            "strategies_used_count": len(self.collection_results["strategies_used"]),
        }

        # Save comprehensive results
        results_file = self.output_dir / "comprehensive_collection_results.json"
        with open(results_file, "w") as f:
            json.dump(self.collection_results, f, indent=2)

        logger.info(f"\n🎯 COMPREHENSIVE COLLECTION COMPLETE")
        logger.info("=" * 50)
        logger.info(f"📊 Total datasets collected: {total_datasets}")
        logger.info(f"📁 Total files created: {total_files}")
        logger.info(f"⚠️ Total errors: {total_errors}")
        logger.info(f"⏱️ Duration: {duration}")
        logger.info(f"💾 Results saved to: {results_file}")

        return self.collection_results


def main():
    """Run the comprehensive DNO collection"""

    collector = ComprehensiveDNOCollector()
    results = collector.run_comprehensive_collection()

    return results


if __name__ == "__main__":
    main()
