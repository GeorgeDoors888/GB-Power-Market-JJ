#!/usr/bin/env python3
"""
UKPN Data Collector - Complete Collection
=========================================

Download all accessible UKPN datasets using the working API key.
"""

import csv
import json
import os
import time
from datetime import datetime

import requests

# UKPN API Key that's working
API_KEY = "d9bf83f6ad2d8960ace2fec0cd5bbc2243f5771144e06abc9acb16bf"

# Known accessible datasets based on our discovery
PRIORITY_DATASETS = [
    {
        "id": "ltds-table-1-circuit-data",
        "name": "LTDS Circuit Data",
        "description": "Long Term Development Statement - Circuit connectivity data",
    },
    {
        "id": "ltds-table-4a-3ph-fault-level",
        "name": "LTDS Fault Levels",
        "description": "Three-phase fault level data",
    },
    {
        "id": "ukpn-secondary-site-transformers",
        "name": "Secondary Transformers",
        "description": "Secondary site transformer information",
    },
    {
        "id": "ukpn-33kv-circuit-operational-data-monthly",
        "name": "33kV Circuit Data",
        "description": "Monthly operational data for 33kV circuits",
    },
    {
        "id": "ukpn-primary-transformer-power-flow-historic-monthly",
        "name": "Primary Transformer Flows",
        "description": "Historical monthly power flow data",
    },
    {
        "id": "ltds-table-7-operational-restrictions",
        "name": "LTDS Operational Restrictions",
        "description": "Network operational restrictions",
    },
    {
        "id": "ukpn-network-losses",
        "name": "Network Losses",
        "description": "Distribution network loss data",
    },
    {
        "id": "ukpn-low-carbon-technologies-lsoa",
        "name": "Low Carbon Technologies",
        "description": "LCT connections by area",
    },
]


class UKPNCollector:
    """Collect all accessible UKPN datasets."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "UK Energy Data Research Tool",
                "Authorization": f"apikey {api_key}",
                "X-API-Key": api_key,
                "apikey": api_key,
            }
        )

        # Create output directory
        self.output_dir = (
            f"ukpn_data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(self.output_dir, exist_ok=True)

        print(f"📁 Output directory: {self.output_dir}")

    def download_dataset(self, dataset_id: str, dataset_name: str) -> dict:
        """Download a specific dataset in multiple formats."""

        print(f"\n📊 Downloading: {dataset_name}")
        print(f"ID: {dataset_id}")
        print("-" * 50)

        result = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "files_created": [],
            "success": False,
            "error": None,
            "file_sizes": {},
            "record_counts": {},
        }

        # Try CSV export (usually most complete)
        csv_url = f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"

        try:
            print(f"🔄 Requesting CSV export...")
            response = self.session.get(csv_url, timeout=60)

            if response.status_code == 200:
                # Save CSV file
                filename = (
                    f"{dataset_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                filepath = os.path.join(self.output_dir, filename)

                with open(filepath, "wb") as f:
                    f.write(response.content)

                result["files_created"].append(filename)
                result["file_sizes"]["csv"] = len(response.content)
                result["success"] = True

                print(f"✅ CSV saved: {filename} ({len(response.content):,} bytes)")

                # Count records
                try:
                    content = response.content.decode("utf-8")
                    lines = content.split("\\n")
                    record_count = len(lines) - 1  # Subtract header
                    result["record_counts"]["csv"] = record_count
                    print(f"📝 Records: {record_count:,}")

                    # Show preview
                    if lines:
                        print(f"📋 Header: {lines[0][:100]}...")
                        if len(lines) > 1 and lines[1].strip():
                            print(f"📋 Sample: {lines[1][:100]}...")

                except Exception as e:
                    print(f"⚠️  Preview error: {e}")

            else:
                print(f"❌ CSV failed: {response.status_code}")
                result["error"] = f"CSV export failed: {response.status_code}"

        except Exception as e:
            print(f"❌ Error: {e}")
            result["error"] = str(e)

        # Also try JSON records format
        json_url = f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset_id}/records/"

        try:
            print(f"🔄 Requesting JSON records...")
            response = self.session.get(json_url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                total_count = data.get("total_count", 0)

                if total_count > 0:
                    # Save JSON metadata
                    json_filename = f"{dataset_id}_metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    json_filepath = os.path.join(self.output_dir, json_filename)

                    with open(json_filepath, "w") as f:
                        json.dump(data, f, indent=2)

                    result["files_created"].append(json_filename)
                    result["file_sizes"]["json"] = len(response.content)
                    result["record_counts"]["json"] = total_count

                    print(f"✅ Metadata saved: {json_filename}")
                    print(f"📊 JSON total count: {total_count:,}")

        except Exception as e:
            print(f"⚠️  JSON metadata error: {e}")

        return result

    def collect_all_priority_datasets(self) -> dict:
        """Download all priority datasets."""

        print("🚀 UKPN Data Collection Starting")
        print("=" * 50)
        print(f"API Key: {self.api_key[:20]}...")
        print(f"Time: {datetime.now()}")
        print(f"Target datasets: {len(PRIORITY_DATASETS)}")
        print()

        results = {
            "collection_time": datetime.now().isoformat(),
            "total_datasets": len(PRIORITY_DATASETS),
            "successful_downloads": 0,
            "failed_downloads": 0,
            "dataset_results": [],
            "summary": {},
        }

        for i, dataset in enumerate(PRIORITY_DATASETS, 1):
            print(f"📊 [{i}/{len(PRIORITY_DATASETS)}] {dataset['name']}")

            result = self.download_dataset(dataset["id"], dataset["name"])
            results["dataset_results"].append(result)

            if result["success"]:
                results["successful_downloads"] += 1
                print(f"✅ SUCCESS")
            else:
                results["failed_downloads"] += 1
                print(f"❌ FAILED: {result['error']}")

            # Small delay between requests
            time.sleep(2)

        # Generate summary
        total_files = sum(len(r["files_created"]) for r in results["dataset_results"])
        total_size = sum(
            sum(r["file_sizes"].values()) for r in results["dataset_results"]
        )
        total_records = sum(
            sum(r["record_counts"].values()) for r in results["dataset_results"]
        )

        results["summary"] = {
            "files_created": total_files,
            "total_size_bytes": total_size,
            "total_records": total_records,
            "success_rate": f"{(results['successful_downloads'] / len(PRIORITY_DATASETS)) * 100:.1f}%",
        }

        # Save collection report
        report_file = os.path.join(self.output_dir, "collection_report.json")
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print("\n🎉 COLLECTION COMPLETE")
        print("=" * 50)
        print(f"✅ Successful: {results['successful_downloads']}")
        print(f"❌ Failed: {results['failed_downloads']}")
        print(f"📁 Files created: {total_files}")
        print(f"💾 Total size: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        print(f"📊 Total records: {total_records:,}")
        print(f"📈 Success rate: {results['summary']['success_rate']}")
        print(f"📄 Report: {report_file}")

        return results


if __name__ == "__main__":
    collector = UKPNCollector(API_KEY)
    results = collector.collect_all_priority_datasets()
