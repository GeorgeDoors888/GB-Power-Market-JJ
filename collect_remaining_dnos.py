#!/usr/bin/env python3
"""
Multi-DNO Data Collector - Collect data from all remaining DNOs
ENWL, NPG, SPD collectors in one script
"""

import json
import logging
from datetime import datetime

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class MultiDNOCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        self.dnos = {
            "ENWL": {
                "name": "Electricity North West",
                "areas": ["ENWL"],
                "urls": {
                    "charges": "https://www.enwl.co.uk/get-connected/charges-and-agreements/",
                    "regulatory": "https://www.enwl.co.uk/about-us/regulatory-and-governance/",
                    "innovation": "https://www.enwl.co.uk/innovation/",
                },
            },
            "NPG": {
                "name": "Northern Powergrid",
                "areas": ["NEEB", "YOREB"],
                "urls": {
                    "charges": "https://www.northernpowergrid.com/charges-and-agreements",
                    "network": "https://www.northernpowergrid.com/network-information",
                    "smart_grid": "https://www.northernpowergrid.com/smart-grid",
                },
            },
            "SPD": {
                "name": "SP Distribution",
                "areas": ["SPDS", "SPMW"],
                "urls": {
                    "charges": "https://www.spenergynetworks.co.uk/pages/charges_and_agreements.aspx",
                    "network": "https://www.spenergynetworks.co.uk/pages/distribution_network_data.aspx",
                    "connections": "https://www.spenergynetworks.co.uk/pages/network_information.aspx",
                },
            },
        }

    def test_dno_accessibility(self, dno_code):
        """Test if DNO websites are accessible"""
        logger.info(f"🔍 Testing {dno_code} accessibility...")

        dno_info = self.dnos[dno_code]
        accessibility_results = {}

        for url_type, url in dno_info["urls"].items():
            try:
                response = self.session.get(url, timeout=15)
                accessibility_results[url_type] = {
                    "url": url,
                    "status_code": response.status_code,
                    "accessible": response.status_code == 200,
                    "content_length": (
                        len(response.content) if response.status_code == 200 else 0
                    ),
                }

                if response.status_code == 200:
                    logger.info(
                        f"✅ {dno_code} {url_type} accessible ({response.status_code})"
                    )
                else:
                    logger.warning(
                        f"⚠️ {dno_code} {url_type} returned {response.status_code}"
                    )

            except Exception as e:
                logger.error(f"❌ {dno_code} {url_type} error: {e}")
                accessibility_results[url_type] = {
                    "url": url,
                    "accessible": False,
                    "error": str(e),
                }

        return accessibility_results

    def collect_dno_data(self, dno_code):
        """Collect data for a specific DNO"""
        logger.info(f"📊 Collecting {dno_code} data...")

        dno_info = self.dnos[dno_code]

        results = {
            "dno": dno_code,
            "full_name": dno_info["name"],
            "areas": dno_info["areas"],
            "collection_timestamp": datetime.now().isoformat(),
            "accessibility_test": self.test_dno_accessibility(dno_code),
            "expected_data_types": [
                "duos_charges",
                "network_capacity",
                "connection_data",
                "performance_statistics",
            ],
            "status": "accessibility_tested",
        }

        return results

    def collect_all_remaining_dnos(self):
        """Collect data from all remaining DNOs"""
        logger.info("🚀 Starting collection for all remaining DNOs...")

        all_results = {
            "collection_timestamp": datetime.now().isoformat(),
            "dnos_collected": [],
            "summary": {},
        }

        for dno_code in ["ENWL", "NPG", "SPD"]:
            try:
                results = self.collect_dno_data(dno_code)
                all_results["dnos_collected"].append(results)

                # Count accessible URLs
                accessible_count = sum(
                    1
                    for test in results["accessibility_test"].values()
                    if test.get("accessible", False)
                )
                total_urls = len(results["accessibility_test"])

                all_results["summary"][dno_code] = {
                    "accessible_urls": f"{accessible_count}/{total_urls}",
                    "status": (
                        "ready_for_data_extraction"
                        if accessible_count > 0
                        else "access_issues"
                    ),
                }

                logger.info(f"✅ {dno_code} collection complete")

            except Exception as e:
                logger.error(f"❌ Failed to collect {dno_code}: {e}")
                all_results["summary"][dno_code] = {"status": "failed", "error": str(e)}

        return all_results


def main():
    """Execute multi-DNO collection"""
    logger.info("🚀 Starting multi-DNO data collection...")

    collector = MultiDNOCollector()
    results = collector.collect_all_remaining_dnos()

    # Save results
    with open("multi_dno_collection_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\n🎯 MULTI-DNO COLLECTION SUMMARY")
    print("=" * 60)

    for dno_code, summary in results["summary"].items():
        print(f"\n📋 {dno_code}")
        print(f"   Accessible URLs: {summary.get('accessible_urls', 'N/A')}")
        print(f"   Status: {summary.get('status', 'Unknown')}")

    total_dnos = len(results["summary"])
    successful_dnos = sum(
        1
        for s in results["summary"].values()
        if s.get("status") == "ready_for_data_extraction"
    )

    print(f"\n📊 OVERALL RESULTS:")
    print(f"   DNOs tested: {total_dnos}")
    print(f"   Ready for extraction: {successful_dnos}")
    print(f"   Success rate: {successful_dnos/total_dnos*100:.1f}%")

    logger.info("✅ Multi-DNO collection complete!")


if __name__ == "__main__":
    main()
