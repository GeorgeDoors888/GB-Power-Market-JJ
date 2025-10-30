#!/usr/bin/env python3
"""
Test UKPN with corrected field extraction
"""

import json
import time
from pathlib import Path

import pandas as pd
import requests


def test_ukpn_corrected():
    """Test UKPN with the corrected dataset field extraction"""

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    )

    # Get first 3 datasets from UKPN
    url = "https://ukpowernetworks.opendatasoft.com/api/v2/catalog/datasets"
    params = {"rows": 3}

    response = session.get(url, params=params, timeout=30)
    data = response.json()
    datasets = data.get("datasets", [])

    print(f"🔍 Found {len(datasets)} UKPN datasets")

    successful_downloads = 0
    output_dir = Path("ukpn_test_downloads")
    output_dir.mkdir(exist_ok=True)

    for i, dataset_info in enumerate(datasets, 1):
        # CORRECTED field access
        dataset_data = dataset_info.get("dataset", {})
        dataset_id = dataset_data.get("dataset_id")
        title = (
            dataset_data.get("metas", {}).get("default", {}).get("title", dataset_id)
        )

        print(f"\n📥 Testing UKPN dataset {i}/{len(datasets)}")
        print(f"   ID: {dataset_id}")
        print(f"   Title: {title}")

        if not dataset_id:
            print("   ❌ No dataset ID found")
            continue

        # Try to download CSV
        csv_url = f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"

        try:
            csv_response = session.get(csv_url, timeout=60)
            print(f"   CSV Status: {csv_response.status_code}")

            if csv_response.status_code == 200:
                # Save file
                filename = f"ukpn_{dataset_id}.csv"
                filepath = output_dir / filename

                with open(filepath, "wb") as f:
                    f.write(csv_response.content)

                # Validate
                try:
                    df = pd.read_csv(filepath)
                    print(f"   ✅ SUCCESS: {len(df)} rows, {len(df.columns)} columns")
                    successful_downloads += 1

                    # Show first few columns
                    print(f"   Columns: {list(df.columns[:5])}")

                except Exception as e:
                    print(f"   ⚠️ Saved but couldn't read: {e}")
            else:
                print(f"   ❌ CSV export failed: {csv_response.status_code}")

        except Exception as e:
            print(f"   ❌ Download error: {e}")

        time.sleep(0.5)

    print(f"\n🎯 UKPN TEST RESULTS:")
    print(f"   Successful downloads: {successful_downloads}/{len(datasets)}")
    print(f"   Files saved to: {output_dir}")

    return successful_downloads > 0


if __name__ == "__main__":
    print("🧪 TESTING CORRECTED EXTRACTION ON UKPN")
    print("=" * 50)
    test_ukpn_corrected()
