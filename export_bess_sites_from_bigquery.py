#!/usr/bin/env python3
"""
export_bess_sites_from_bigquery.py

Extract BESS asset locations from BigQuery bess_asset_config table.
Geocode postcodes if available, otherwise use DNO region centroids.

Usage:
    python3 export_bess_sites_from_bigquery.py

Output:
    btm_sites.csv with columns: asset_id, asset_name, location, dno, latitude, longitude
"""

import csv
import requests
from typing import List, Dict
from google.cloud import bigquery

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
OUTPUT_CSV = "btm_sites.csv"
POSTCODES_API = "https://api.postcodes.io/postcodes/"

# DNO region approximate centroids (fallback if no postcode)
DNO_CENTROIDS = {
    "UKPN-EPN": {"lat": 52.2053, "lon": 0.1218, "region": "Eastern"},  # Norwich
    "UKPN-LPN": {"lat": 51.5074, "lon": -0.1278, "region": "London"},
    "UKPN-SPN": {"lat": 51.4545, "lon": -0.9781, "region": "South East"},  # Reading
    "NGED West Midlands": {"lat": 52.4862, "lon": -1.8904, "region": "West Midlands"},  # Birmingham
    "NGED South West": {"lat": 51.4545, "lon": -2.5879, "region": "South West"},  # Bristol
    "NGED South Wales": {"lat": 51.4816, "lon": -3.1791, "region": "South Wales"},  # Cardiff
    "NGED East Midlands": {"lat": 52.9548, "lon": -1.1581, "region": "East Midlands"},  # Nottingham
    "ENWL": {"lat": 53.4808, "lon": -2.2426, "region": "North West"},  # Manchester
    "SPEN": {"lat": 54.9783, "lon": -1.6178, "region": "North East"},  # Newcastle
    "NPgN": {"lat": 55.8642, "lon": -4.2518, "region": "Central Scotland"},  # Glasgow
    "NPgY": {"lat": 55.9533, "lon": -3.1883, "region": "Southern Scotland"},  # Edinburgh
    "SSEN": {"lat": 57.1497, "lon": -2.0943, "region": "Northern Scotland"},  # Aberdeen
    "SSEH": {"lat": 51.4545, "lon": -2.5879, "region": "Southern"},  # Oxford area
}


def fetch_bess_assets():
    """Fetch BESS assets from BigQuery"""
    print("\n📊 Fetching BESS assets from BigQuery...")
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT
        asset_id,
        asset_name,
        location,
        gsp_group,
        dno,
        p_max_mw,
        e_max_mwh,
        commissioned_date
    FROM `{PROJECT_ID}.{DATASET}.bess_asset_config`
    WHERE asset_id IS NOT NULL
    """

    df = client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} BESS assets")

    return df.to_dict('records')


def geocode_postcode(postcode: str) -> Dict:
    """Geocode UK postcode using postcodes.io API"""
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
    except Exception as e:
        print(f"   ⚠️ Error geocoding {postcode}: {e}")

    return {"latitude": None, "longitude": None, "admin_district": None, "region": None}


def get_dno_centroid(dno: str) -> Dict:
    """Get approximate centroid for DNO region"""
    # Try exact match first
    if dno in DNO_CENTROIDS:
        return DNO_CENTROIDS[dno]

    # Try partial match
    for dno_key, centroid in DNO_CENTROIDS.items():
        if dno.upper() in dno_key.upper() or dno_key.upper() in dno.upper():
            return centroid

    # Default to UK center
    return {"lat": 53.0, "lon": -1.5, "region": "Unknown"}


def geocode_bess_sites(assets: List[Dict]) -> List[Dict]:
    """Geocode BESS sites using postcodes if available, otherwise DNO centroids"""
    print(f"\n📍 Geocoding {len(assets)} BESS sites...")

    geocoded_sites = []

    for i, asset in enumerate(assets, 1):
        site_name = asset.get('asset_name', 'Unknown')
        location = asset.get('location', '')
        dno = asset.get('dno', '')

        print(f"   [{i}/{len(assets)}] {site_name} ({location})...")

        # Try to extract postcode from location field
        # UK postcode pattern: e.g., "SW1A 1AA", "M1 1AE"
        location_clean = location.strip().upper()

        # Check if location looks like a postcode (contains space and numbers)
        if ' ' in location_clean and any(c.isdigit() for c in location_clean):
            # Try geocoding as postcode
            geo = geocode_postcode(location_clean)

            if geo['latitude'] is not None:
                print(f"      ✅ Geocoded via postcode: {geo['latitude']:.4f}, {geo['longitude']:.4f}")
                geocoded_sites.append({
                    'asset_id': asset['asset_id'],
                    'asset_name': site_name,
                    'location': location,
                    'dno': dno,
                    'p_max_mw': asset.get('p_max_mw'),
                    'e_max_mwh': asset.get('e_max_mwh'),
                    'latitude': geo['latitude'],
                    'longitude': geo['longitude'],
                    'geocode_method': 'postcode'
                })
                continue

        # Fallback: Use DNO centroid
        centroid = get_dno_centroid(dno)
        print(f"      ℹ️ Using DNO centroid: {centroid['lat']:.4f}, {centroid['lon']:.4f} ({centroid['region']})")

        geocoded_sites.append({
            'asset_id': asset['asset_id'],
            'asset_name': site_name,
            'location': location if location else centroid['region'],
            'dno': dno,
            'p_max_mw': asset.get('p_max_mw'),
            'e_max_mwh': asset.get('e_max_mwh'),
            'latitude': centroid['lat'],
            'longitude': centroid['lon'],
            'geocode_method': 'dno_centroid'
        })

    return geocoded_sites


def save_to_csv(sites: List[Dict], filename: str):
    """Save geocoded sites to CSV"""
    print(f"\n💾 Saving to {filename}...")

    fieldnames = ['asset_id', 'asset_name', 'location', 'dno', 'p_max_mw', 'e_max_mwh',
                  'latitude', 'longitude', 'geocode_method']

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sites)

    print(f"   ✅ Saved {len(sites)} sites to {filename}")


def main():
    print("🗺️ BESS Sites Export from BigQuery")
    print("=" * 60)

    # Fetch BESS assets from BigQuery
    assets = fetch_bess_assets()

    if not assets:
        print("\n⚠️ No BESS assets found in bess_asset_config table")
        print("   Table exists but is empty or missing data")
        return

    # Geocode sites
    geocoded = geocode_bess_sites(assets)

    # Save to CSV
    save_to_csv(geocoded, OUTPUT_CSV)

    print("\n" + "=" * 60)
    print(f"✅ Pipeline complete! Output: {OUTPUT_CSV}")
    print(f"   Next: python3 create_constraint_geojson_simple.py")


if __name__ == "__main__":
    main()
