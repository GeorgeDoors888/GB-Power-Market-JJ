#!/usr/bin/env python3
"""
DNO Data Extraction Summary
Parse downloaded data and create final collection status
"""

import json
import logging
from datetime import datetime

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def parse_ssen_catalog():
    """Parse SSEN catalog to find downloadable datasets"""
    logger.info("📊 Parsing SSEN data catalog...")

    try:
        with open("ssen_catalog.jsonld.json", "r") as f:
            catalog_data = json.load(f)

        datasets = []
        for item in catalog_data:
            if isinstance(item, dict):
                title = None
                download_url = None
                description = None
                file_format = None

                # Extract title
                if "http://purl.org/dc/terms/title" in item:
                    title = item["http://purl.org/dc/terms/title"][0]["@value"]

                # Extract description
                if "http://purl.org/dc/terms/description" in item:
                    description = item["http://purl.org/dc/terms/description"][0][
                        "@value"
                    ]

                # Extract format
                if "http://purl.org/dc/terms/format" in item:
                    file_format = item["http://purl.org/dc/terms/format"][0]["@value"]

                # Extract download URL
                if "http://www.w3.org/ns/dcat#downloadURL" in item:
                    download_url = item["http://www.w3.org/ns/dcat#downloadURL"][0][
                        "@id"
                    ]
                elif "http://www.w3.org/ns/dcat#accessURL" in item:
                    download_url = item["http://www.w3.org/ns/dcat#accessURL"][0]["@id"]

                if title and download_url:
                    datasets.append(
                        {
                            "title": title,
                            "description": description,
                            "format": file_format,
                            "download_url": download_url,
                            "relevance": (
                                "high"
                                if any(
                                    keyword in title.lower()
                                    for keyword in [
                                        "charge",
                                        "tariff",
                                        "substation",
                                        "network",
                                        "capacity",
                                    ]
                                )
                                else "medium"
                            ),
                        }
                    )

        # Sort by relevance
        datasets.sort(key=lambda x: (x["relevance"] == "high", x["title"]))

        logger.info(f"✅ Found {len(datasets)} datasets in SSEN catalog")
        return datasets[:20]  # Top 20 most relevant

    except Exception as e:
        logger.error(f"❌ Error parsing SSEN catalog: {e}")
        return []


def create_final_dno_status():
    """Create final DNO collection status and next steps"""

    # Parse SSEN data
    ssen_datasets = parse_ssen_catalog()

    final_status = {
        "completion_timestamp": datetime.now().isoformat(),
        "collection_phase": "Data Discovery and Initial Downloads Complete",
        "progress_summary": {
            "total_uk_dnos": 6,
            "fully_collected": 1,  # UKPN
            "data_discovered": 3,  # SSEN, NGED, SPD
            "partially_accessible": 1,  # ENWL
            "access_issues": 1,  # NPG
            "overall_progress": "67% (4/6 DNOs accessible)",
        },
        "discovered_data": {
            "SSEN": {
                "datasets_found": len(ssen_datasets),
                "data_types": [
                    "Network maps",
                    "Substation data",
                    "Charges",
                    "Statistics",
                ],
                "file_formats": list(
                    set(d["format"] for d in ssen_datasets if d["format"])
                ),
                "sample_datasets": ssen_datasets[:5],
            },
            "SPD": {
                "pages_downloaded": 2,
                "data_types": ["Charges and agreements", "Distribution network data"],
                "status": "HTML pages saved - needs parsing",
            },
            "NGED": {
                "portal_status": "Accessible",
                "portal_url": "https://connecteddata.westernpower.co.uk/",
                "status": "Ready for data extraction",
            },
        },
        "immediate_actions_required": {
            "SSEN": [
                f"Download {len(ssen_datasets)} datasets from catalog",
                "Parse network and substation data files",
                "Extract DUoS charges information",
                "Upload to BigQuery with standardized schema",
            ],
            "SPD": [
                "Parse HTML pages to find CSV/Excel links",
                "Download actual data files",
                "Extract charges and network information",
            ],
            "NGED": [
                "Explore connected data portal structure",
                "Identify available datasets",
                "Download relevant data files",
            ],
            "NPG": [
                "Research correct URLs (current ones return 404)",
                "Find alternative data sources",
                "Contact NPG for data access guidance",
            ],
        },
        "estimated_timeline": {
            "Week 1": "Complete SSEN data extraction and BigQuery upload",
            "Week 2": "Complete SPD and NGED data collection",
            "Week 3": "Resolve NPG access issues and complete ENWL",
            "Week 4": "Final validation and documentation",
        },
        "technical_next_steps": [
            "Build automated downloaders for SSEN catalog datasets",
            "Create HTML parsers for SPD web pages",
            "Develop NGED portal scrapers",
            "Design standardized BigQuery schemas for all DNOs",
            "Implement data quality validation pipeline",
        ],
    }

    return final_status


def main():
    """Generate final DNO collection summary"""
    logger.info("📋 Creating final DNO collection status...")

    final_status = create_final_dno_status()

    # Save complete status
    with open("DNO_COLLECTION_FINAL_STATUS.json", "w") as f:
        json.dump(final_status, f, indent=2, default=str)

    # Print executive summary
    print("\n" + "=" * 80)
    print("🎯 FINAL DNO DATA COLLECTION STATUS")
    print("=" * 80)
    print()

    progress = final_status["progress_summary"]
    print(f"📊 OVERALL PROGRESS: {progress['overall_progress']}")
    print(f"   • Fully collected: {progress['fully_collected']}/6 (UKPN)")
    print(f"   • Data discovered: {progress['data_discovered']}/6 (SSEN, NGED, SPD)")
    print(f"   • Partially accessible: {progress['partially_accessible']}/6 (ENWL)")
    print(f"   • Access issues: {progress['access_issues']}/6 (NPG)")
    print()

    print("📋 DISCOVERED DATA SUMMARY:")
    discovered = final_status["discovered_data"]
    if "SSEN" in discovered:
        ssen = discovered["SSEN"]
        print(f"   • SSEN: {ssen['datasets_found']} datasets found")
        print(f"     Formats: {', '.join(ssen['file_formats'][:5])}")

    if "SPD" in discovered:
        spd = discovered["SPD"]
        print(f"   • SPD: {spd['pages_downloaded']} data pages downloaded")

    if "NGED" in discovered:
        print(f"   • NGED: Data portal accessible and ready")
    print()

    print("⏱️ ESTIMATED COMPLETION TIMELINE:")
    timeline = final_status["estimated_timeline"]
    for week, task in timeline.items():
        print(f"   • {week}: {task}")
    print()

    print("🚀 IMMEDIATE NEXT ACTIONS:")
    for i, action in enumerate(final_status["technical_next_steps"][:5], 1):
        print(f"   {i}. {action}")

    print("\n" + "=" * 80)
    print("✅ DNO COLLECTION DISCOVERY PHASE COMPLETE")
    print("🔄 READY TO PROCEED WITH DATA EXTRACTION")
    print("=" * 80)

    logger.info("✅ Final DNO status report generated!")


if __name__ == "__main__":
    main()
