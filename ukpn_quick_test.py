#!/usr/bin/env python3
"""
Quick UKPN API Test - Download One Dataset
==========================================

Quickly test the UKPN API key by downloading the LTDS Circuit Data.
"""

import csv
import json
from datetime import datetime

import requests

# UKPN API Key from user
API_KEY = "d9bf83f6ad2d8960ace2fec0cd5bbc2243f5771144e06abc9acb16bf"


def test_ukpn_ltds_download():
    """Test downloading LTDS Circuit Data - this was working in the previous test."""

    print("🔑 UKPN API Key Quick Test")
    print("=" * 30)
    print(f"Testing LTDS Circuit Data download...")

    # The URL that was working in the previous test
    url = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/ltds-table-1-circuit-data/exports/csv"

    headers = {
        "User-Agent": "UK Energy Data Research Tool",
        "Authorization": f"apikey {API_KEY}",
        "X-API-Key": API_KEY,
        "apikey": API_KEY,
    }

    try:
        print(f"📥 Downloading: {url}")
        response = requests.get(url, headers=headers, timeout=30)

        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("✅ SUCCESS! API Key is working.")

            # Save the data
            output_file = (
                f"ukpn_ltds_circuit_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"📄 Data saved to: {output_file}")

            # Quick preview
            try:
                content = response.content.decode("utf-8")
                lines = content.split("\n")
                print(f"\n📊 Data Preview:")
                print(f"Total lines: {len(lines)}")
                print(f"Header: {lines[0][:100]}...")
                if len(lines) > 1:
                    print(f"First data row: {lines[1][:100]}...")

                # Parse CSV to count records
                reader = csv.DictReader(content.split("\n"))
                row_count = sum(1 for row in reader)
                print(f"Records: {row_count}")

            except Exception as e:
                print(f"Preview error: {e}")

            return True

        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_api_catalog():
    """Test basic API catalog access."""

    print("\n🔍 Testing API Catalog Access...")

    url = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/"

    headers = {
        "User-Agent": "UK Energy Data Research Tool",
        "Authorization": f"apikey {API_KEY}",
        "X-API-Key": API_KEY,
        "apikey": API_KEY,
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            datasets = data.get("datasets", [])
            print(f"✅ Found {len(datasets)} datasets available")

            print("\n📋 Available Datasets:")
            for i, dataset in enumerate(datasets[:10]):  # Show first 10
                dataset_id = dataset.get("dataset_id", "unknown")
                title = (
                    dataset.get("metas", {}).get("default", {}).get("title", "No title")
                )
                print(f"{i+1:2d}. {dataset_id} - {title}")

            if len(datasets) > 10:
                print(f"    ... and {len(datasets) - 10} more")

            return datasets
        else:
            print(f"❌ Catalog access failed: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Catalog error: {e}")
        return []


if __name__ == "__main__":
    print("🚀 Starting UKPN API Quick Test\n")

    # Test 1: Download known working dataset
    success = test_ukpn_ltds_download()

    # Test 2: Get available datasets
    datasets = test_api_catalog()

    if success:
        print("\n🎉 CONCLUSION:")
        print("✅ UKPN API Key is working!")
        print("✅ Data download successful")
        print(f"✅ {len(datasets)} datasets available")
        print("\n🚀 Next Steps:")
        print("1. Update DNO collector to use this API key")
        print("2. Download all available UKPN datasets")
        print("3. Integrate with BigQuery pipeline")
    else:
        print("\n❌ API Key test failed")
        print("Need to troubleshoot authentication")
