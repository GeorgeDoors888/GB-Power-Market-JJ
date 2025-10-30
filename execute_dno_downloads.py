#!/usr/bin/env python3
"""
DNO Data Download Executor
Actually downloads data from accessible DNO portals
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from google.cloud import bigquery

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class DNODataDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        # DNO download priorities based on accessibility test
        self.priority_dnos = {
            "SSEN": {
                "status": "ready",
                "data_urls": [
                    "https://ckan-prod.sse.datopian.com/dataset/ssen-substation-data.jsonld",
                    "https://ckan-prod.sse.datopian.com/catalog.jsonld",
                ],
                "areas": ["SSES", "SHEPD"],
            },
            "NGED": {
                "status": "ready",
                "data_portal": "https://connecteddata.westernpower.co.uk/",
                "areas": ["WMID", "EMID", "SWALES", "SWEST"],
            },
            "SPD": {
                "status": "ready",
                "data_urls": [
                    "https://www.spenergynetworks.co.uk/pages/charges_and_agreements.aspx",
                    "https://www.spenergynetworks.co.uk/pages/distribution_network_data.aspx",
                ],
                "areas": ["SPDS", "SPMW"],
            },
            "ENWL": {
                "status": "partial",
                "data_urls": ["https://www.enwl.co.uk/innovation/"],
                "areas": ["ENWL"],
            },
        }

    def download_ssen_data(self):
        """Download actual SSEN data files"""
        logger.info("📥 Downloading SSEN data...")

        downloaded_files = []

        for url in self.priority_dnos["SSEN"]["data_urls"]:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    # Extract filename from URL
                    filename = url.split("/")[-1]
                    if not filename.endswith((".json", ".csv", ".xlsx")):
                        filename += ".json"

                    filepath = Path(f"ssen_{filename}")

                    # Save the file
                    with open(filepath, "wb") as f:
                        f.write(response.content)

                    downloaded_files.append(
                        {
                            "url": url,
                            "filename": str(filepath),
                            "size_bytes": len(response.content),
                            "download_time": datetime.now().isoformat(),
                        }
                    )

                    logger.info(
                        f"✅ Downloaded {filepath} ({len(response.content)} bytes)"
                    )
                else:
                    logger.warning(
                        f"⚠️ Failed to download {url}: {response.status_code}"
                    )

            except Exception as e:
                logger.error(f"❌ Error downloading {url}: {e}")

        return downloaded_files

    def download_spd_data(self):
        """Download SPD data (web scraping approach)"""
        logger.info("📥 Downloading SPD data...")

        downloaded_files = []

        # SPD requires web scraping to find actual data files
        for url in self.priority_dnos["SPD"]["data_urls"]:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    # Save the HTML page for manual inspection
                    filename = f"spd_{url.split('/')[-1]}.html"
                    filepath = Path(filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(response.text)

                    downloaded_files.append(
                        {
                            "url": url,
                            "filename": str(filepath),
                            "size_bytes": len(response.content),
                            "download_time": datetime.now().isoformat(),
                            "type": "html_page",
                        }
                    )

                    logger.info(f"✅ Downloaded SPD page {filepath}")

            except Exception as e:
                logger.error(f"❌ Error downloading SPD {url}: {e}")

        return downloaded_files

    def create_dno_summary_report(self):
        """Create comprehensive DNO collection status report"""

        report = {
            "report_timestamp": datetime.now().isoformat(),
            "total_uk_dnos": 6,
            "collected_dnos": 1,  # UKPN already collected
            "in_progress_dnos": 4,  # SSEN, NGED, SPD, ENWL
            "problematic_dnos": 1,  # NPG
            "detailed_status": {
                "UKPN": {
                    "status": "✅ COMPLETE",
                    "tables_collected": 10,
                    "areas": ["LPN", "SPN", "EPN"],
                    "data_types": ["DUoS charges", "network data", "connections"],
                },
                "SSEN": {
                    "status": "🔄 DATA AVAILABLE",
                    "accessibility": "Good - data portal accessible",
                    "areas": ["SSES", "SHEPD"],
                    "data_found": "Substation data, JSON catalog",
                },
                "NGED": {
                    "status": "🔄 PORTAL ACCESSIBLE",
                    "accessibility": "Good - open data portal accessible",
                    "areas": ["WMID", "EMID", "SWALES", "SWEST"],
                    "data_found": "Open data portal with multiple datasets",
                },
                "SPD": {
                    "status": "🔄 WEBSITES ACCESSIBLE",
                    "accessibility": "Excellent - all 3 URLs accessible",
                    "areas": ["SPDS", "SPMW"],
                    "data_found": "Charges and network data pages",
                },
                "ENWL": {
                    "status": "⚠️ LIMITED ACCESS",
                    "accessibility": "Partial - only innovation page accessible",
                    "areas": ["ENWL"],
                    "data_found": "Innovation projects data only",
                },
                "NPG": {
                    "status": "❌ ACCESS ISSUES",
                    "accessibility": "Poor - all URLs returned 404",
                    "areas": ["NEEB", "YOREB"],
                    "data_found": "None - URL issues need investigation",
                },
            },
            "next_steps": {
                "immediate": [
                    "Extract actual data from SSEN JSON files",
                    "Scrape data from SPD web pages",
                    "Explore NGED open data portal",
                    "Research correct NPG URLs",
                ],
                "this_week": [
                    "Complete SSEN data extraction and BigQuery upload",
                    "Implement SPD data parser",
                    "Build NGED portal scraper",
                    "Find working NPG data sources",
                ],
                "next_week": [
                    "Complete all DNO data collection",
                    "Standardize schemas across all DNOs",
                    "Implement automated collection pipeline",
                    "Validate data quality and completeness",
                ],
            },
            "estimated_completion": {
                "SSEN": "2-3 days",
                "SPD": "3-4 days",
                "NGED": "4-5 days",
                "ENWL": "5-6 days",
                "NPG": "7-10 days (pending URL research)",
            },
        }

        return report

    def execute_immediate_downloads(self):
        """Execute downloads for immediately available data"""
        logger.info("🚀 Executing immediate DNO data downloads...")

        download_results = {
            "execution_timestamp": datetime.now().isoformat(),
            "downloads": {},
        }

        # Download SSEN data
        download_results["downloads"]["SSEN"] = self.download_ssen_data()

        # Download SPD data
        download_results["downloads"]["SPD"] = self.download_spd_data()

        # Summary
        total_files = sum(
            len(files) for files in download_results["downloads"].values()
        )
        total_size = sum(
            file["size_bytes"]
            for files in download_results["downloads"].values()
            for file in files
        )

        download_results["summary"] = {
            "total_files_downloaded": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "dnos_with_downloads": len(
                [k for k, v in download_results["downloads"].items() if v]
            ),
        }

        return download_results


def main():
    """Execute DNO data downloads"""
    logger.info("🚀 Starting DNO data download execution...")

    downloader = DNODataDownloader()

    # Create status report
    report = downloader.create_dno_summary_report()

    # Save status report
    with open("dno_collection_status_report.json", "w") as f:
        json.dump(report, f, indent=2)

    # Execute downloads
    download_results = downloader.execute_immediate_downloads()

    # Save download results
    with open("dno_download_results.json", "w") as f:
        json.dump(download_results, f, indent=2, default=str)

    # Print summary
    print("\n🎯 DNO COLLECTION EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Report generated: {report['report_timestamp']}")
    print(f"Total UK DNOs: {report['total_uk_dnos']}")
    print(f"Completed: {report['collected_dnos']}/6 (UKPN)")
    print(f"In progress: {report['in_progress_dnos']}/6")
    print()

    print("📊 IMMEDIATE DOWNLOAD RESULTS:")
    summary = download_results["summary"]
    print(f"Files downloaded: {summary['total_files_downloaded']}")
    print(f"Total size: {summary['total_size_mb']} MB")
    print(f"DNOs with data: {summary['dnos_with_downloads']}")
    print()

    print("📋 DETAILED STATUS:")
    for dno, status in report["detailed_status"].items():
        print(f"  {dno}: {status['status']}")

    print("\n💡 IMMEDIATE NEXT STEPS:")
    for step in report["next_steps"]["immediate"]:
        print(f"  • {step}")

    logger.info("✅ DNO download execution complete!")


if __name__ == "__main__":
    main()
