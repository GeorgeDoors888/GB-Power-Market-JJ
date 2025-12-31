#!/usr/bin/env python3
"""
export_btm_sites_mock.py

Bypass Google Sheets connection issues by using mock BtM site data.
Geocodes via postcodes.io API and exports to CSV for map generation.

Usage:
    python3 export_btm_sites_mock.py

Output:
    btm_sites.csv with columns: row_number, site_name, postcode, latitude, longitude, admin_district, region
"""

import time
import requests
import csv
from typing import List, Dict

# Configuration
OUTPUT_CSV = "btm_sites.csv"
POSTCODES_API = "https://api.postcodes.io/postcodes/"

# Mock BtM sites (real UK battery storage locations)
MOCK_BTM_SITES = [
    {"row_number": 1, "site_name": "Drax Battery Storage", "postcode": "YO8 8PH"},
    {"row_number": 2, "site_name": "Cottam BESS", "postcode": "DN22 0HU"},
    {"row_number": 3, "site_name": "Capenhurst BESS", "postcode": "CH1 6ES"},
    {"row_number": 4, "site_name": "Glassenbury BESS", "postcode": "TN17 2PJ"},
    {"row_number": 5, "site_name": "Byers Brae BESS", "postcode": "EH10 7DW"},
    {"row_number": 6, "site_name": "Cleator BESS", "postcode": "CA23 3AX"},
    {"row_number": 7, "site_name": "Enderby BESS", "postcode": "LE19 4AD"},
    {"row_number": 8, "site_name": "Holes Bay BESS", "postcode": "BH15 4AA"},
    {"row_number": 9, "site_name": "Kilmarnock BESS", "postcode": "KA1 3EE"},
    {"row_number": 10, "site_name": "Lister Drive BESS", "postcode": "L14 3NA"},
]


def geocode_postcode(postcode: str) -> Dict:
    """
    Geocode a UK postcode using postcodes.io API.

    Returns:
        dict with latitude, longitude, admin_district, region
    """
    postcode_clean = postcode.replace(" ", "")
    url = f"{POSTCODES_API}{postcode_clean}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("status") == 200 and "result" in data:
            result = data["result"]
            return {
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "admin_district": result.get("admin_district"),
                "region": result.get("region"),
            }
        else:
            print(f"   ⚠️ Failed to geocode {postcode}: {data.get('error', 'Unknown error')}")
            return {"latitude": None, "longitude": None, "admin_district": None, "region": None}

    except Exception as e:
        print(f"   ❌ Error geocoding {postcode}: {e}")
        return {"latitude": None, "longitude": None, "admin_district": None, "region": None}


def geocode_sites(sites: List[Dict]) -> List[Dict]:
    """
    Geocode all sites using postcodes.io API.
    """
    print(f"\n2️⃣ Geocoding {len(sites)} sites via postcodes.io...")

    geocoded_sites = []
    for i, site in enumerate(sites, 1):
        print(f"   [{i}/{len(sites)}] {site['site_name']} ({site['postcode']})...")

        geo = geocode_postcode(site['postcode'])

        geocoded_sites.append({
            **site,
            **geo
        })

        # Rate limiting: postcodes.io allows ~1000 requests/min
        if i < len(sites):
            time.sleep(0.1)

    successful = sum(1 for s in geocoded_sites if s['latitude'] is not None)
    print(f"\n   ✅ Geocoded {successful}/{len(sites)} sites successfully")

    return geocoded_sites


def save_to_csv(sites: List[Dict], filename: str):
    """
    Save geocoded sites to CSV.
    """
    print(f"\n3️⃣ Saving to {filename}...")

    fieldnames = ['row_number', 'site_name', 'postcode', 'latitude', 'longitude', 'admin_district', 'region']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sites)

    print(f"   ✅ Saved {len(sites)} sites to {filename}")


def main():
    print("🗺️ BtM Sites Mock Data Export & Geocoding")
    print("=" * 60)
    print("⚠️  Using mock BtM data (Google Sheets API workaround)")
    print(f"   Mock sites: {len(MOCK_BTM_SITES)}")

    # Geocode mock sites
    geocoded = geocode_sites(MOCK_BTM_SITES)

    # Save to CSV
    save_to_csv(geocoded, OUTPUT_CSV)

    print("\n" + "=" * 60)
    print(f"✅ Pipeline complete! Output: {OUTPUT_CSV}")
    print(f"   Next: python3 create_constraint_geojson.py")


if __name__ == "__main__":
    main()
