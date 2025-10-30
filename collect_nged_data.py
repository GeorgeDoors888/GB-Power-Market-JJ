#!/usr/bin/env python3
"""
NGED Data Collector - National Grid Electricity Distribution
Covers WMID, EMID, SWALES, SWEST license areas
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class NGEDDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        self.base_urls = {
            "open_data": "https://connecteddata.westernpower.co.uk/",
            "charges": "https://www.westernpower.co.uk/connections-landing-page",
            "network_data": "https://www.westernpower.co.uk/network",
        }

        self.areas = ["WMID", "EMID", "SWALES", "SWEST"]

    def discover_nged_data_sources(self):
        """Discover NGED data sources"""
        logger.info("🔍 Discovering NGED data sources...")

        discovered_sources = {}

        # Check open data portal
        try:
            response = self.session.get(self.base_urls["open_data"], timeout=30)
            if response.status_code == 200:
                logger.info("✅ NGED open data portal accessible")

                soup = BeautifulSoup(response.content, "html.parser")
                data_links = []

                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    text = link.get_text(strip=True).lower()

                    if any(
                        keyword in text
                        for keyword in ["data", "download", "csv", "excel"]
                    ) or any(ext in href.lower() for ext in [".csv", ".xlsx", ".json"]):
                        data_links.append(
                            {
                                "url": href,
                                "text": link.get_text(strip=True),
                                "type": "data_source",
                            }
                        )

                discovered_sources["open_data"] = {
                    "status": "accessible",
                    "data_links": data_links[:10],
                }
            else:
                logger.warning(
                    f"⚠️ NGED open data portal returned {response.status_code}"
                )

        except Exception as e:
            logger.error(f"❌ Error accessing NGED open data portal: {e}")
            discovered_sources["open_data"] = {"status": "error", "error": str(e)}

        return discovered_sources

    def collect_nged_data(self):
        """Collect NGED data"""
        logger.info("📊 Collecting NGED data...")

        results = {
            "dno": "NGED",
            "full_name": "National Grid Electricity Distribution",
            "areas": self.areas,
            "collection_timestamp": datetime.now().isoformat(),
            "discovered_sources": self.discover_nged_data_sources(),
            "status": "framework_ready",
        }

        return results


def main():
    collector = NGEDDataCollector()
    results = collector.collect_nged_data()

    # Save results
    with open("nged_collection_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n🎯 NGED DATA COLLECTION SUMMARY")
    print("=" * 50)
    print(f"DNO: {results['dno']} - {results['full_name']}")
    print(f"Areas: {', '.join(results['areas'])}")
    print(f"Status: {results['status']}")

    logger.info("✅ NGED data collection complete!")


if __name__ == "__main__":
    main()
