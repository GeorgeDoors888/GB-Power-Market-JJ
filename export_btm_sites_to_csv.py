#!/usr/bin/env python3
"""
export_btm_sites_to_csv.py

Extracts BtM site postcodes from Google Sheets, geocodes them via postcodes.io,
and exports to CSV for use in constraint mapping.

Outputs: btm_sites.csv (postcode, lat, lon, site_name, dno_id)

Usage:
    python3 export_btm_sites_to_csv.py
    python3 export_btm_sites_to_csv.py --output btm_sites_custom.csv

Requirements:
    pip3 install --user gspread pandas requests
"""

import argparse
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

# ===== CONFIGURATION =====
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
BTM_SHEET_NAME = "BtM"
POSTCODE_COLUMN = "A"  # Postcode column in BtM sheet
POSTCODE_START_ROW = 6  # First data row (skip headers)

POSTCODE_API_BASE = "https://api.postcodes.io/postcodes/"


def normalize_postcode(postcode):
    """Normalize UK postcode for API lookup (remove spaces, uppercase)."""
    if pd.isna(postcode) or postcode == "":
        return None
    return str(postcode).replace(" ", "").upper()


def geocode_postcode(postcode):
    """
    Geocode a UK postcode using postcodes.io API.

    Returns dict with:
    - latitude
    - longitude
    - admin_district (DNO region hint)
    """
    normalized = normalize_postcode(postcode)
    if not normalized:
        return None

    url = f"{POSTCODE_API_BASE}{normalized}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if data.get("status") == 200 and "result" in data:
            result = data["result"]
            return {
                "postcode": postcode,  # Original format
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "admin_district": result.get("admin_district"),
                "region": result.get("region"),
                "country": result.get("country")
            }
        else:
            print(f"   ⚠️ Geocoding failed for {postcode}: {data.get('error', 'Unknown error')}")
            return None

    except Exception as e:
        print(f"   ❌ Error geocoding {postcode}: {str(e)}")
        return None


def extract_btm_postcodes():
    """
    Extract postcodes from BtM sheet in Google Sheets.

    Returns DataFrame with columns: row_number, postcode
    """

    print("\n🔗 Connecting to Google Sheets...")

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=scopes
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(BTM_SHEET_NAME)

    print(f"✅ Connected to '{BTM_SHEET_NAME}' sheet")

    # Get postcode column (A6 onwards)
    print(f"\n📊 Reading postcodes from column {POSTCODE_COLUMN}...")
    postcode_col = worksheet.col_values(1)  # Column A (1-indexed)

    # Filter to data rows (skip headers, empty cells)
    postcodes = []
    for i, value in enumerate(postcode_col[POSTCODE_START_ROW-1:], start=POSTCODE_START_ROW):
        if value and value.strip():
            postcodes.append({
                "row_number": i,
                "postcode": value.strip()
            })

    df = pd.DataFrame(postcodes)
    print(f"   ✅ Found {len(df)} postcodes")

    return df


def geocode_sites(postcodes_df):
    """
    Geocode all postcodes from DataFrame.

    Returns DataFrame with geocoded results.
    """

    print(f"\n🌍 Geocoding {len(postcodes_df)} postcodes via postcodes.io...")

    results = []
    for i, row in postcodes_df.iterrows():
        postcode = row['postcode']
        print(f"   [{i+1}/{len(postcodes_df)}] Geocoding {postcode}...", end=" ")

        geo_data = geocode_postcode(postcode)

        if geo_data:
            print(f"✅ ({geo_data['latitude']:.4f}, {geo_data['longitude']:.4f})")
            results.append({
                "row_number": row['row_number'],
                "site_name": f"BtM Site {row['row_number']}",  # Placeholder
                "postcode": postcode,
                "latitude": geo_data['latitude'],
                "longitude": geo_data['longitude'],
                "admin_district": geo_data.get('admin_district'),
                "region": geo_data.get('region')
            })
        else:
            print(f"❌ Failed")
            results.append({
                "row_number": row['row_number'],
                "site_name": f"BtM Site {row['row_number']}",
                "postcode": postcode,
                "latitude": None,
                "longitude": None,
                "admin_district": None,
                "region": None
            })

        # Rate limiting (postcodes.io allows 1000 req/min)
        time.sleep(0.1)

    return pd.DataFrame(results)


def save_to_csv(df, output_path):
    """Save geocoded sites to CSV."""
    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved {len(df)} sites to: {output_path}")

    # Show summary
    valid = df['latitude'].notna().sum()
    invalid = df['latitude'].isna().sum()

    print(f"\n📊 Summary:")
    print(f"   Valid geocoded: {valid}")
    print(f"   Failed: {invalid}")

    if invalid > 0:
        print(f"\n⚠️ Failed postcodes:")
        failed = df[df['latitude'].isna()][['postcode', 'row_number']]
        for _, row in failed.iterrows():
            print(f"      Row {row['row_number']}: {row['postcode']}")


def main():
    parser = argparse.ArgumentParser(description='Export BtM sites to CSV with geocoding')
    parser.add_argument('--output', default='btm_sites.csv',
                       help='Output CSV file path (default: btm_sites.csv)')
    args = parser.parse_args()

    print("=" * 70)
    print("📍 BTM SITES EXPORT & GEOCODING")
    print("=" * 70)

    # Step 1: Extract postcodes from Google Sheets
    postcodes_df = extract_btm_postcodes()

    if postcodes_df.empty:
        print("❌ No postcodes found in BtM sheet")
        return

    # Step 2: Geocode all postcodes
    geocoded_df = geocode_sites(postcodes_df)

    # Step 3: Save to CSV
    save_to_csv(geocoded_df, args.output)

    print("\n✅ Export complete!")
    print(f"   Next step: python3 create_constraint_geojson.py")


if __name__ == "__main__":
    main()
