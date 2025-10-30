#!/usr/bin/env python3
"""
Automated DNO Data Collection from Discovered Sources
Collects DUoS charges and distribution data from missing DNO providers
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DNODataCollector:
    """Automated DNO data collection from discovered web sources"""

    def __init__(self, sources_file: Optional[str] = None):
        """Initialize the collector with discovered sources"""
        self.sources_file = sources_file or "dno_website_sources_20250913_121252.json"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )
        self.collected_data = {}

    def load_sources(self) -> Dict:
        """Load discovered DNO sources from JSON file"""
        try:
            with open(self.sources_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Sources file not found: {self.sources_file}")
            return {}

    def extract_data_from_page(self, url: str, dno_name: str) -> Dict:
        """Extract DUoS and charging data from a webpage"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Look for common data indicators
            data_indicators = {
                "duos_mentions": len(
                    soup.find_all(
                        text=re.compile(r"DUoS|Distribution Use of System", re.I)
                    )
                ),
                "charge_mentions": len(
                    soup.find_all(text=re.compile(r"charge|tariff|rate", re.I))
                ),
                "price_mentions": len(
                    soup.find_all(text=re.compile(r"price|cost|£|pence", re.I))
                ),
                "regulatory_mentions": len(
                    soup.find_all(text=re.compile(r"regulatory|ofgem", re.I))
                ),
            }

            # Look for downloadable files (PDFs, Excel, CSV)
            file_links = []
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if any(
                    ext in href.lower() for ext in [".pdf", ".xlsx", ".xls", ".csv"]
                ):
                    file_links.append(
                        {
                            "url": (
                                href
                                if href.startswith("http")
                                else f"{url.split('/')[0]}//{url.split('/')[2]}{href}"
                            ),
                            "text": link.get_text(strip=True),
                            "type": href.split(".")[-1].lower(),
                        }
                    )

            # Look for data tables
            tables = soup.find_all("table")
            table_data = []
            for i, table in enumerate(tables[:3]):  # Limit to first 3 tables
                rows = table.find_all("tr")
                if len(rows) > 1:  # Has header and data
                    table_info = {
                        "table_index": i,
                        "rows": len(rows),
                        "columns": len(rows[0].find_all(["th", "td"])) if rows else 0,
                        "headers": (
                            [
                                th.get_text(strip=True)
                                for th in rows[0].find_all(["th", "td"])
                            ]
                            if rows
                            else []
                        ),
                    }
                    table_data.append(table_info)

            return {
                "url": url,
                "dno": dno_name,
                "collection_time": datetime.now().isoformat(),
                "page_title": (
                    soup.title.get_text(strip=True) if soup.title else "No title"
                ),
                "data_indicators": data_indicators,
                "downloadable_files": file_links,
                "tables_found": table_data,
                "total_data_score": sum(data_indicators.values())
                + len(file_links) * 5
                + len(table_data) * 3,
            }

        except Exception as e:
            logger.error(f"Error extracting data from {url}: {e}")
            return {
                "url": url,
                "dno": dno_name,
                "error": str(e),
                "collection_time": datetime.now().isoformat(),
            }

    def collect_all_data(self) -> Dict:
        """Collect data from all discovered sources"""
        sources = self.load_sources()

        logger.info(f"Starting data collection from {len(sources)} DNO sources")

        for dno_name, dno_sources in sources.items():
            logger.info(f"Collecting data for {dno_name}...")

            dno_data = []

            for source in dno_sources:
                if source.get("type") == "potential_data_page":
                    logger.info(f"  Analyzing: {source['url']}")
                    data = self.extract_data_from_page(source["url"], dno_name)
                    dno_data.append(data)

                    # Rate limiting
                    time.sleep(2)

            self.collected_data[dno_name] = dno_data
            logger.info(f"  Completed {dno_name}: {len(dno_data)} sources analyzed")

        return self.collected_data

    def analyze_results(self) -> Dict:
        """Analyze collected data and generate insights"""
        analysis = {
            "collection_summary": {
                "dnos_analyzed": len(self.collected_data),
                "total_sources": sum(
                    len(sources) for sources in self.collected_data.values()
                ),
                "collection_time": datetime.now().isoformat(),
            },
            "dno_analysis": {},
            "top_sources": [],
            "recommendations": [],
        }

        # Analyze each DNO
        for dno_name, sources in self.collected_data.items():
            dno_analysis = {
                "sources_checked": len(sources),
                "successful_extractions": len([s for s in sources if "error" not in s]),
                "total_data_score": sum(s.get("total_data_score", 0) for s in sources),
                "downloadable_files": sum(
                    len(s.get("downloadable_files", [])) for s in sources
                ),
                "tables_found": sum(len(s.get("tables_found", [])) for s in sources),
            }

            # Find best source for this DNO
            best_source = (
                max(sources, key=lambda x: x.get("total_data_score", 0))
                if sources
                else None
            )
            if best_source and best_source.get("total_data_score", 0) > 0:
                dno_analysis["best_source"] = {
                    "url": best_source["url"],
                    "score": best_source["total_data_score"],
                    "files": len(best_source.get("downloadable_files", [])),
                    "tables": len(best_source.get("tables_found", [])),
                }

            analysis["dno_analysis"][dno_name] = dno_analysis

        # Generate recommendations
        high_score_dnos = [
            (dno, data["total_data_score"])
            for dno, data in analysis["dno_analysis"].items()
            if data["total_data_score"] > 10
        ]

        if high_score_dnos:
            analysis["recommendations"].append(
                f"High-priority DNOs for manual data collection: {[dno for dno, score in high_score_dnos]}"
            )

        file_rich_dnos = [
            (dno, data["downloadable_files"])
            for dno, data in analysis["dno_analysis"].items()
            if data["downloadable_files"] > 0
        ]

        if file_rich_dnos:
            analysis["recommendations"].append(
                f"DNOs with downloadable data files: {[dno for dno, files in file_rich_dnos]}"
            )

        return analysis

    def save_results(self, filename: Optional[str] = None) -> str:
        """Save collected data and analysis to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save raw collected data
        data_file = filename or f"dno_collected_data_{timestamp}.json"
        with open(data_file, "w") as f:
            json.dump(self.collected_data, f, indent=2)

        # Save analysis
        analysis = self.analyze_results()
        analysis_file = f"dno_data_analysis_{timestamp}.json"
        with open(analysis_file, "w") as f:
            json.dump(analysis, f, indent=2)

        logger.info(f"Results saved to {data_file} and {analysis_file}")
        return data_file


def main():
    """Main execution function"""
    print("🤖 AUTOMATED DNO DATA COLLECTION")
    print("=" * 50)

    collector = DNODataCollector()

    # Collect data from all sources
    collected_data = collector.collect_all_data()

    # Analyze and save results
    results_file = collector.save_results()
    analysis = collector.analyze_results()

    # Print summary
    print(f"\n📊 COLLECTION SUMMARY")
    print("-" * 30)
    print(f"DNOs analyzed: {analysis['collection_summary']['dnos_analyzed']}")
    print(f"Sources checked: {analysis['collection_summary']['total_sources']}")

    print(f"\n🎯 TOP FINDINGS")
    print("-" * 30)
    for dno, data in analysis["dno_analysis"].items():
        if data["total_data_score"] > 5:
            print(
                f"✅ {dno}: Score {data['total_data_score']}, "
                f"{data['downloadable_files']} files, {data['tables_found']} tables"
            )

    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 30)
    for rec in analysis["recommendations"]:
        print(f"• {rec}")

    print(f"\n💾 Results saved to: {results_file}")


if __name__ == "__main__":
    main()
