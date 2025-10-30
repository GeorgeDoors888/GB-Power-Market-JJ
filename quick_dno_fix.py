#!/usr/bin/env python3
"""
Quick Fix for DNO Collector - Correct Field Access
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def quick_test_spen():
    """Quick test to get SPEN data with correct field access"""

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    )

    # Get first few datasets from SPEN
    url = "https://spenergynetworks.opendatasoft.com/api/v2/catalog/datasets"
    params = {"rows": 5}  # Just test 5 datasets

    response = session.get(url, params=params, timeout=30)
    data = response.json()
    datasets = data.get("datasets", [])

    print(f"🔍 Found {len(datasets)} SPEN datasets")

    successful_downloads = 0
    output_dir = Path("spen_test_downloads")
    output_dir.mkdir(exist_ok=True)

    for i, dataset_info in enumerate(datasets, 1):
        # CORRECT field access
        dataset_data = dataset_info.get("dataset", {})
        dataset_id = dataset_data.get("dataset_id")
        title = (
            dataset_data.get("metas", {}).get("default", {}).get("title", dataset_id)
        )

        print(f"\n📥 Testing SPEN dataset {i}/{len(datasets)}")
        print(f"   ID: {dataset_id}")
        print(f"   Title: {title}")

        if not dataset_id:
            print("   ❌ No dataset ID found")
            continue

        # Try to download CSV
        csv_url = f"https://spenergynetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"

        try:
            csv_response = session.get(csv_url, timeout=60)
            print(f"   CSV Status: {csv_response.status_code}")

            if csv_response.status_code == 200:
                # Save file
                filename = f"spen_{dataset_id}.csv"
                filepath = output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(csv_response.content)

                # Validate
                try:
                    df = pd.read_csv(filepath)
                    print(f"   ✅ SUCCESS: {len(df)} rows, {len(df.columns)} columns")
                    successful_downloads += 1
                except Exception as e:
                    print(f"   ⚠️ Saved but couldn't read: {e}")
            else:
                print(f"   ❌ CSV export failed: {csv_response.status_code}")

        except Exception as e:
            print(f"   ❌ Download error: {e}")

        time.sleep(0.5)  # Rate limiting

    print(f"\n🎯 QUICK TEST RESULTS:")
    print(f"   Successful downloads: {successful_downloads}/{len(datasets)}")
    print(f"   Files saved to: {output_dir}")

    return successful_downloads > 0


if __name__ == "__main__":
    print("🧪 QUICK DNO FIX TEST")
    print("=" * 50)

    success = quick_test_spen()

    if success:
        print("\n✅ FIX WORKS! The issue was incorrect field access.")
        print("   dataset_id is in dataset_info['dataset']['dataset_id']")
        print("   not in dataset_info['dataset_id']")
    else:
        print("\n❌ Still having issues - need deeper investigation")
