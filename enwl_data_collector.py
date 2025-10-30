#!/usr/bin/env python3
"""
ENWL (Electricity North West) Data Collector
Downloads and processes CSV files and regulatory data from ENWL
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ENWLDataCollector:
    """Specialized collector for Electricity North West (ENWL) data"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )
        self.base_url = "https://enwl.co.uk"
        self.collected_files = []
        self.analysis_results = {}

    def discover_enwl_data_sources(self):
        """Discover all ENWL CSV and data sources"""
        logger.info("🔍 Discovering ENWL data sources...")

        sources = {
            "regulatory_information": "https://enwl.co.uk/about-us/regulatory-information",
            "network_data": "https://enwl.co.uk/about-us/our-network",
            "connections": "https://enwl.co.uk/connections-and-generation",
            "tariffs_charges": "https://enwl.co.uk/your-power-supply/understanding-your-bill",
            "performance_data": "https://enwl.co.uk/about-us/our-performance",
        }

        discovered_data = {}

        for section, url in sources.items():
            try:
                logger.info(f"  Checking {section}: {url}")
                response = self.session.get(url, timeout=15)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")

                    # Find all downloadable files
                    files_found = []

                    # Look for direct links to CSV, Excel, PDF files
                    for link in soup.find_all("a", href=True):
                        href = link["href"]
                        if any(
                            ext in href.lower()
                            for ext in [".csv", ".xlsx", ".xls", ".pdf"]
                        ):
                            file_info = {
                                "url": (
                                    href
                                    if href.startswith("http")
                                    else f"{self.base_url}{href}"
                                ),
                                "text": link.get_text(strip=True),
                                "type": href.split(".")[-1].lower(),
                                "relevance_score": self._calculate_relevance(
                                    link.get_text(strip=True) + " " + href
                                ),
                            }
                            files_found.append(file_info)

                    # Look for mentions of DUoS, charges, tariffs
                    content_text = soup.get_text().lower()
                    content_indicators = {
                        "duos_mentions": len(
                            re.findall(r"duos|distribution use of system", content_text)
                        ),
                        "charge_mentions": len(
                            re.findall(r"charg|tariff|rate", content_text)
                        ),
                        "csv_mentions": len(
                            re.findall(r"csv|data|download", content_text)
                        ),
                        "regulatory_mentions": len(
                            re.findall(r"regulatory|ofgem|licence", content_text)
                        ),
                    }

                    discovered_data[section] = {
                        "url": url,
                        "status": "accessible",
                        "files_found": len(files_found),
                        "high_relevance_files": [
                            f for f in files_found if f["relevance_score"] > 3
                        ],
                        "content_indicators": content_indicators,
                        "all_files": files_found,
                    }

                    logger.info(
                        f"    ✅ Found {len(files_found)} files, {len(discovered_data[section]['high_relevance_files'])} high relevance"
                    )
                else:
                    logger.info(f"    ❌ HTTP {response.status_code}")

            except Exception as e:
                logger.error(f"    ❌ Error: {e}")
                discovered_data[section] = {"status": "error", "error": str(e)}

        self.discovered_sources = discovered_data
        return discovered_data

    def _calculate_relevance(self, text):
        """Calculate relevance score for a file based on its name/description"""
        text = text.lower()
        score = 0

        # High value terms
        if any(
            term in text
            for term in ["duos", "distribution use of system", "charges", "tariff"]
        ):
            score += 5

        # Medium value terms
        if any(term in text for term in ["regulatory", "ofgem", "licence", "network"]):
            score += 3

        # File type bonuses
        if any(term in text for term in ["csv", "data", "download"]):
            score += 2

        # ENWL specific terms
        if any(
            term in text for term in ["enwl", "electricity north west", "north west"]
        ):
            score += 2

        return score

    def download_high_priority_files(self, max_files=10):
        """Download the highest priority CSV and data files"""
        logger.info("📥 Downloading high-priority ENWL files...")

        if not hasattr(self, "discovered_sources"):
            self.discover_enwl_data_sources()

        all_files = []
        for section, data in self.discovered_sources.items():
            if data.get("status") == "accessible":
                all_files.extend(data.get("high_relevance_files", []))

        # Sort by relevance score
        all_files.sort(key=lambda x: x["relevance_score"], reverse=True)

        downloaded_files = []

        for i, file_info in enumerate(all_files[:max_files]):
            try:
                logger.info(
                    f"  Downloading {i+1}/{min(max_files, len(all_files))}: {file_info['text'][:50]}..."
                )

                response = self.session.get(file_info["url"], timeout=30)
                response.raise_for_status()

                # Create filename
                filename = f"enwl_{file_info['type']}_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_info['type']}"

                # Save file
                with open(filename, "wb") as f:
                    f.write(response.content)

                file_info["local_filename"] = filename
                file_info["file_size"] = len(response.content)
                file_info["download_status"] = "success"
                downloaded_files.append(file_info)

                logger.info(
                    f"    ✅ Downloaded: {filename} ({file_info['file_size']} bytes)"
                )

            except Exception as e:
                logger.error(f"    ❌ Download failed: {e}")
                file_info["download_status"] = "failed"
                file_info["error"] = str(e)

        self.collected_files = downloaded_files
        return downloaded_files

    def analyze_csv_files(self):
        """Analyze downloaded CSV files for DUoS and charging data"""
        logger.info("📊 Analyzing downloaded CSV files...")

        csv_files = [
            f
            for f in self.collected_files
            if f["type"] == "csv" and f.get("download_status") == "success"
        ]

        analysis_results = {}

        for file_info in csv_files:
            filename = file_info["local_filename"]
            logger.info(f"  Analyzing: {filename}")

            try:
                # Try different encodings
                for encoding in ["utf-8", "latin-1", "cp1252"]:
                    try:
                        df = pd.read_csv(filename, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    logger.error(f"    ❌ Could not read {filename} with any encoding")
                    continue

                # Analyze the CSV structure
                file_analysis = {
                    "filename": filename,
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "data_types": df.dtypes.to_dict(),
                    "sample_data": df.head(3).to_dict("records") if len(df) > 0 else [],
                    "contains_charges": any(
                        "charge" in str(col).lower()
                        or "tariff" in str(col).lower()
                        or "rate" in str(col).lower()
                        for col in df.columns
                    ),
                    "contains_dates": any(
                        "date" in str(col).lower() or "time" in str(col).lower()
                        for col in df.columns
                    ),
                    "contains_mpan": any(
                        "mpan" in str(col).lower() or "distributor" in str(col).lower()
                        for col in df.columns
                    ),
                }

                # Look for numeric columns that might be charges
                numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
                file_analysis["numeric_columns"] = numeric_columns

                # Calculate data quality score
                quality_score = 0
                if file_analysis["contains_charges"]:
                    quality_score += 5
                if file_analysis["contains_dates"]:
                    quality_score += 3
                if file_analysis["contains_mpan"]:
                    quality_score += 4
                if len(numeric_columns) > 0:
                    quality_score += 2
                if file_analysis["rows"] > 100:
                    quality_score += 2

                file_analysis["quality_score"] = quality_score

                analysis_results[filename] = file_analysis

                logger.info(
                    f"    ✅ {filename}: {len(df)} rows, {len(df.columns)} cols, quality score: {quality_score}"
                )

            except Exception as e:
                logger.error(f"    ❌ Analysis failed for {filename}: {e}")
                analysis_results[filename] = {"error": str(e)}

        self.analysis_results = analysis_results
        return analysis_results

    def check_existing_enwl_data(self):
        """Check what ENWL data we already have in the workspace"""
        logger.info("🔍 Checking existing ENWL data in workspace...")

        existing_data = {
            "carbon_intensity_data": None,
            "capacity_market_data": None,
            "other_csv_files": [],
        }

        # Check the carbon intensity file we found earlier
        carbon_file = "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/neso_data_comprehensive/carbon_intensity/regional_intensity.csv"
        if os.path.exists(carbon_file):
            try:
                df = pd.read_csv(carbon_file)
                enwl_data = df[df["dnoregion"] == "Electricity North West"]
                existing_data["carbon_intensity_data"] = {
                    "file": carbon_file,
                    "enwl_records": len(enwl_data),
                    "region_id": 3,
                    "sample_data": (
                        enwl_data.head(2).to_dict("records")
                        if len(enwl_data) > 0
                        else []
                    ),
                }
                logger.info(
                    f"  ✅ Found {len(enwl_data)} ENWL carbon intensity records"
                )
            except Exception as e:
                logger.error(f"  ❌ Error reading carbon intensity data: {e}")

        # Look for other ENWL references in existing CSV files
        search_patterns = ["enwl", "electricity north west", "north west england"]

        for pattern in search_patterns:
            logger.info(f"  Searching for: {pattern}")
            # This would require a more comprehensive search through all CSV files
            # For now, we know about the carbon intensity data

        return existing_data

    def generate_comprehensive_report(self):
        """Generate comprehensive ENWL data collection report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        report = {
            "collection_summary": {
                "timestamp": timestamp,
                "enwl_mpan_id": "14",
                "enwl_region": "North West England",
                "sources_checked": (
                    len(self.discovered_sources)
                    if hasattr(self, "discovered_sources")
                    else 0
                ),
                "files_downloaded": len(self.collected_files),
                "csv_files_analyzed": len(
                    [f for f in self.collected_files if f["type"] == "csv"]
                ),
            },
            "data_discovery": getattr(self, "discovered_sources", {}),
            "downloaded_files": self.collected_files,
            "csv_analysis": getattr(self, "analysis_results", {}),
            "existing_data": self.check_existing_enwl_data(),
            "recommendations": [],
        }

        # Generate recommendations
        if report["csv_analysis"]:
            high_quality_files = [
                name
                for name, analysis in report["csv_analysis"].items()
                if analysis.get("quality_score", 0) > 5
            ]
            if high_quality_files:
                report["recommendations"].append(
                    f"High-quality CSV files found: {high_quality_files}"
                )

        if report["existing_data"]["carbon_intensity_data"]:
            report["recommendations"].append(
                "ENWL carbon intensity data already available - integrate with new DUoS data"
            )

        # Save report
        report_file = f"enwl_comprehensive_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report, report_file


def main():
    """Main execution"""
    print("⚡ ENWL (ELECTRICITY NORTH WEST) DATA COLLECTOR")
    print("=" * 60)

    collector = ENWLDataCollector()

    # Discover data sources
    sources = collector.discover_enwl_data_sources()

    # Download high-priority files
    downloaded = collector.download_high_priority_files(max_files=5)

    # Analyze CSV files
    analysis = collector.analyze_csv_files()

    # Generate comprehensive report
    report, report_file = collector.generate_comprehensive_report()

    # Print summary
    print(f"\n📊 ENWL DATA COLLECTION SUMMARY")
    print("-" * 40)
    print(f"MPAN ID: 14 (North West England)")
    print(f"Sources checked: {len(sources)}")
    print(f"Files downloaded: {len(downloaded)}")
    print(f"CSV files analyzed: {len(analysis)}")

    print(f"\n🎯 HIGH-VALUE DISCOVERIES")
    print("-" * 40)
    for section, data in sources.items():
        if data.get("status") == "accessible":
            high_rel_files = len(data.get("high_relevance_files", []))
            if high_rel_files > 0:
                print(f"✅ {section}: {high_rel_files} high-relevance files")

    print(f"\n📋 CSV ANALYSIS RESULTS")
    print("-" * 40)
    for filename, result in analysis.items():
        if "quality_score" in result:
            print(
                f"✅ {filename}: {result['rows']} rows, quality score {result['quality_score']}"
            )

    print(f"\n💾 Full report saved to: {report_file}")


if __name__ == "__main__":
    main()
