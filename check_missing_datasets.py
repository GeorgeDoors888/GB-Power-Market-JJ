#!/usr/bin/env python3
"""
Check availability of missing BMRS datasets
"""

import json
from datetime import datetime, timedelta

import requests

# BMRS API base URL
BMRS_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


def check_dataset_availability(
    dataset_code, start_date="2024-01-01", end_date="2024-01-02"
):
    """Check if a dataset is available via BMRS API"""
    url = f"{BMRS_BASE_URL}/{dataset_code.lower()}"
    params = {
        "publishDateTimeFrom": start_date,
        "publishDateTimeTo": end_date,
        "format": "json",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return True, f"✅ Available - {len(data.get('data', []))} records found"
        elif response.status_code == 404:
            return False, "❌ Dataset not found (404)"
        else:
            return False, f"❌ Error {response.status_code}: {response.text[:100]}"
    except Exception as e:
        return False, f"❌ Connection error: {str(e)[:100]}"


# Check the missing datasets
missing_datasets = [
    "NETBSAD",  # Adjustment data
    "COSTS",  # System Buy/Sell Prices
    "STOR",  # Short-term operating reserves
    "NDF",  # National Demand Forecast
    "TSDF",  # Transmission System Demand Forecast
    "NDFD",  # National Demand Forecast Day-ahead
    "NDFW",  # National Demand Forecast Week-ahead
    "TSDFD",  # Transmission System Demand Forecast Day-ahead
    "TSDFW",  # Transmission System Demand Forecast Week-ahead
]

print("🔍 Checking availability of missing BMRS datasets...")
print("=" * 60)

for dataset in missing_datasets:
    available, message = check_dataset_availability(dataset)
    print(f"{dataset:10} | {message}")

print("\n" + "=" * 60)
print("Note: Some datasets like Restoration region data and Triad peaks")
print("might be available through different API endpoints or as insights data.")
