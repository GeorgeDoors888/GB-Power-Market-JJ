#!/usr/bin/env python3
"""
Targeted DNO Data Collector - Focus on High-Value Sources
Specifically targets Electricity North West and National Grid distribution data
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TargetedDNOCollector:
    """Focused collection from high-priority DNO sources"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )
        self.results = {}

    def collect_electricity_north_west_data(self):
        """Collect data from Electricity North West regulatory page"""
        logger.info("🔍 Collecting Electricity North West data...")

        enw_data = {
            "dno_name": "Electricity North West",
            "mpan_id": "14",
            "main_url": "https://enwl.co.uk/about-us/regulatory-information",
            "collection_time": datetime.now().isoformat(),
            "data_sources": [],
        }

        try:
            # Get the main regulatory page
            response = self.session.get(enw_data["main_url"], timeout=15)
            response.raise_for_status()

            # Look for DUoS-related content and documents
            content = response.text.lower()

            # Search for key terms
            duos_indicators = {
                "duos_mentions": len(
                    re.findall(r"duos|distribution use of system", content)
                ),
                "charge_mentions": len(re.findall(r"charg|tariff|rate", content)),
                "price_mentions": len(re.findall(r"price|cost|£|pence|penny", content)),
                "connection_mentions": len(
                    re.findall(r"connection|network|distribution", content)
                ),
            }

            enw_data["content_analysis"] = duos_indicators

            # Look for downloadable documents
            pdf_pattern = r'href=["\']([^"\']*\.pdf[^"\']*)["\']'
            excel_pattern = r'href=["\']([^"\']*\.xlsx?[^"\']*)["\']'

            pdf_links = re.findall(pdf_pattern, content)
            excel_links = re.findall(excel_pattern, content)

            all_docs = []
            for link in pdf_links + excel_links:
                if any(
                    term in link.lower()
                    for term in ["charge", "tariff", "duos", "regulatory", "price"]
                ):
                    full_url = (
                        link if link.startswith("http") else f"https://enwl.co.uk{link}"
                    )
                    all_docs.append(
                        {
                            "url": full_url,
                            "type": "pdf" if ".pdf" in link else "excel",
                            "relevance": (
                                "high"
                                if any(
                                    term in link.lower()
                                    for term in ["duos", "charge", "tariff"]
                                )
                                else "medium"
                            ),
                        }
                    )

            enw_data["documents_found"] = all_docs
            enw_data["status"] = "success"

            logger.info(f"✅ ENW: Found {len(all_docs)} relevant documents")

        except Exception as e:
            enw_data["status"] = "error"
            enw_data["error"] = str(e)
            logger.error(f"❌ ENW collection error: {e}")

        self.results["electricity_north_west"] = enw_data
        return enw_data

    def collect_national_grid_distribution_data(self):
        """Collect National Grid distribution data (includes former WPD)"""
        logger.info("🔍 Collecting National Grid distribution data...")

        ng_data = {
            "dno_name": "National Grid Distribution (ex-WPD)",
            "mpan_ids": ["21", "22", "23", "24"],
            "search_urls": [
                "https://www.nationalgrid.co.uk/electricity-distribution",
                "https://www.nationalgrid.co.uk/about-us/businesses/uk-electricity-distribution",
                "https://www.nationalgrideso.com/industry-information/codes-and-licences",
                "https://www.nationalgrid.co.uk/document-library",
            ],
            "collection_time": datetime.now().isoformat(),
            "data_sources": [],
        }

        successful_searches = 0

        for url in ng_data["search_urls"]:
            try:
                logger.info(f"  Checking: {url}")
                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    content = response.text.lower()

                    # Look for distribution/DUoS content
                    content_score = (
                        len(re.findall(r"distribution|duos|charge|tariff", content))
                        + len(re.findall(r"wpd|western power", content))
                        * 2  # Bonus for WPD mentions
                    )

                    if content_score > 5:  # Threshold for relevant content
                        ng_data["data_sources"].append(
                            {
                                "url": url,
                                "status": "accessible",
                                "content_score": content_score,
                                "contains_wpd_refs": "wpd" in content
                                or "western power" in content,
                            }
                        )
                        successful_searches += 1
                        logger.info(
                            f"    ✅ Relevant content found (score: {content_score})"
                        )
                    else:
                        logger.info(
                            f"    ⚠️  Limited relevant content (score: {content_score})"
                        )
                else:
                    logger.info(f"    ❌ HTTP {response.status_code}")

            except Exception as e:
                logger.error(f"    ❌ Error: {e}")

        ng_data["successful_searches"] = successful_searches
        ng_data["status"] = "success" if successful_searches > 0 else "limited_success"

        self.results["national_grid_distribution"] = ng_data
        return ng_data

    def search_northern_powergrid_deep(self):
        """Deep search of Northern Powergrid for regulatory data"""
        logger.info("🔍 Deep search Northern Powergrid...")

        npg_data = {
            "dno_name": "Northern Powergrid",
            "mpan_id": "20",
            "base_url": "https://northernpowergrid.com",
            "search_paths": [
                "/about-us/regulatory-information",
                "/connections-and-generation/connection-charges",
                "/about-us/our-performance/regulatory-reporting",
                "/your-power-supply/understanding-your-bill/network-charges",
                "/connections-and-generation/distributed-generation/charges",
            ],
            "collection_time": datetime.now().isoformat(),
            "accessible_pages": [],
        }

        for path in npg_data["search_paths"]:
            url = f"{npg_data['base_url']}{path}"
            try:
                logger.info(f"  Testing: {path}")
                response = self.session.get(url, timeout=10)

                if response.status_code == 200:
                    content = response.text.lower()
                    relevance_score = (
                        len(re.findall(r"duos|distribution use of system", content)) * 5
                        + len(re.findall(r"charg|tariff|rate", content)) * 2
                        + len(re.findall(r"regulatory|ofgem", content)) * 3
                    )

                    if relevance_score > 0:
                        npg_data["accessible_pages"].append(
                            {
                                "path": path,
                                "url": url,
                                "relevance_score": relevance_score,
                                "status": "accessible_with_content",
                            }
                        )
                        logger.info(f"    ✅ Content found (score: {relevance_score})")
                    else:
                        logger.info(f"    ⚠️  Page accessible but no relevant content")
                else:
                    logger.info(f"    ❌ HTTP {response.status_code}")

            except Exception as e:
                logger.info(f"    ❌ Connection error: {str(e)[:50]}...")

        npg_data["status"] = (
            "success" if npg_data["accessible_pages"] else "no_data_found"
        )
        self.results["northern_powergrid"] = npg_data
        return npg_data

    def generate_collection_report(self):
        """Generate comprehensive collection report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Summary statistics
        summary = {
            "collection_time": timestamp,
            "dnos_searched": len(self.results),
            "successful_collections": len(
                [r for r in self.results.values() if r.get("status") == "success"]
            ),
            "total_data_sources": sum(
                len(r.get("data_sources", [])) + len(r.get("accessible_pages", []))
                for r in self.results.values()
            ),
            "priority_findings": [],
        }

        # Analyze each DNO
        for dno_name, data in self.results.items():
            if data.get("status") == "success":
                if dno_name == "electricity_north_west":
                    docs = data.get("documents_found", [])
                    high_relevance_docs = [
                        d for d in docs if d.get("relevance") == "high"
                    ]
                    if high_relevance_docs:
                        summary["priority_findings"].append(
                            f"Electricity North West: {len(high_relevance_docs)} high-relevance documents found"
                        )

                elif dno_name == "national_grid_distribution":
                    sources = data.get("data_sources", [])
                    wpd_sources = [s for s in sources if s.get("contains_wpd_refs")]
                    if wpd_sources:
                        summary["priority_findings"].append(
                            f"National Grid: {len(wpd_sources)} pages with WPD/distribution content"
                        )

                elif dno_name == "northern_powergrid":
                    pages = data.get("accessible_pages", [])
                    high_score_pages = [
                        p for p in pages if p.get("relevance_score", 0) > 5
                    ]
                    if high_score_pages:
                        summary["priority_findings"].append(
                            f"Northern Powergrid: {len(high_score_pages)} high-relevance pages found"
                        )

        # Save detailed results
        detailed_file = f"targeted_dno_collection_{timestamp}.json"
        with open(detailed_file, "w") as f:
            json.dump(self.results, f, indent=2)

        # Save summary
        summary_file = f"dno_collection_summary_{timestamp}.json"
        full_report = {"summary": summary, "detailed_results": self.results}
        with open(summary_file, "w") as f:
            json.dump(full_report, f, indent=2)

        return summary, detailed_file


def main():
    """Main execution"""
    print("🎯 TARGETED DNO DATA COLLECTION")
    print("=" * 50)

    collector = TargetedDNOCollector()

    # Collect from high-priority sources
    collector.collect_electricity_north_west_data()
    collector.collect_national_grid_distribution_data()
    collector.search_northern_powergrid_deep()

    # Generate report
    summary, results_file = collector.generate_collection_report()

    print(f"\n📊 COLLECTION RESULTS")
    print("-" * 30)
    print(f"DNOs searched: {summary['dnos_searched']}")
    print(f"Successful collections: {summary['successful_collections']}")
    print(f"Total data sources found: {summary['total_data_sources']}")

    print(f"\n🎯 KEY FINDINGS")
    print("-" * 30)
    for finding in summary["priority_findings"]:
        print(f"• {finding}")

    print(f"\n💾 Detailed results saved to: {results_file}")


if __name__ == "__main__":
    main()
