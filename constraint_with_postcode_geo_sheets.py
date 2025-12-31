#!/usr/bin/env python3
"""
constraint_with_postcode_geo_sheets.py

Enhances the BigQuery DNO/constraint model by:
 - Geocoding UK postcodes (using postcodes.io)
 - Aggregating constraint cost/volume trends over time
 - Exporting summary tables to Google Sheets

Per specification in Untitled-1.py
"""

import requests
import pandas as pd
from datetime import datetime
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# -----------------------------------
# CONFIGURATION
# -----------------------------------

# Google Cloud + BigQuery
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
CONSTRAINT_TABLE = "constraint_costs_by_dno"

# Google Sheets
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Constraint Summary"

# UK postcode API (Postcodes.io, free)
POSTCODE_API_BASE = "https://api.postcodes.io/postcodes/"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# DNO region centroids (approximate center points for geocoding)
DNO_CENTROIDS = {
    "UKPN-EPN": {"postcode": "CB1 1BH", "name": "UK Power Networks - Eastern"},
    "UKPN-LPN": {"postcode": "EC1V 1NQ", "name": "UK Power Networks - London"},
    "UKPN-SPN": {"postcode": "BN1 1AL", "name": "UK Power Networks - South Eastern"},
    "ENWL": {"postcode": "M1 1AD", "name": "Electricity North West"},
    "NPgN": {"postcode": "NE1 1AD", "name": "Northern Powergrid - North East"},
    "NPgY": {"postcode": "LS1 1UR", "name": "Northern Powergrid - Yorkshire"},
    "SPEN-SPD": {"postcode": "EH1 1AD", "name": "SP Energy Networks - South Scotland"},
    "SPEN-SPM": {"postcode": "LL57 1DT", "name": "SP Energy Networks - Manweb"},
    "NGED-SWALES": {"postcode": "CF10 1EP", "name": "NGED - South Wales"},
    "NGED-SWEST": {"postcode": "BS1 6LE", "name": "NGED - South West"},
    "NGED-EMID": {"postcode": "NG1 5FS", "name": "NGED - East Midlands"},
    "NGED-WMID": {"postcode": "B1 1AA", "name": "NGED - West Midlands"},
    "SSEH": {"postcode": "AB10 1AD", "name": "SSE - Hydro"},
    "SSEN": {"postcode": "OX1 1AD", "name": "SSE - Southern"}
}

# -----------------------------------
# 1) Postcode geocoder
# -----------------------------------
def geocode_postcode(postcode):
    """Geocode a UK postcode to lat/long"""
    try:
        url = POSTCODE_API_BASE + postcode.replace(" ", "")
        response = requests.get(url, timeout=5)
        data = response.json()

        if data["status"] == 200:
            result = data["result"]
            return {
                "postcode": postcode,
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "region": result.get("region", ""),
                "admin_district": result.get("admin_district", "")
            }
    except:
        pass

    return {"postcode": postcode, "latitude": None, "longitude": None, "region": "", "admin_district": ""}

# -----------------------------------
# 2) Fetch and geocode constraint data
# -----------------------------------
def fetch_geocoded_constraints():
    """
    Fetch constraint costs by DNO and geocode DNO region centroids
    """
    print("\n📊 Fetching constraint costs from BigQuery...")

    query = f"""
    SELECT
        dno_id,
        dno_full_name,
        area_sq_km,
        COUNT(*) as num_months,
        SUM(allocated_total_cost) as total_cost_gbp,
        SUM(allocated_voltage_cost) as voltage_cost_gbp,
        SUM(allocated_thermal_cost) as thermal_cost_gbp,
        AVG(allocated_total_cost) as avg_monthly_cost,
        MIN(year) as earliest_year,
        MAX(year) as latest_year
    FROM `{PROJECT_ID}.{BQ_DATASET}.{CONSTRAINT_TABLE}`
    GROUP BY dno_id, dno_full_name, area_sq_km
    ORDER BY total_cost_gbp DESC
    """

    df = bq_client.query(query).to_dataframe()
    print(f"✅ Retrieved {len(df)} DNO regions")

    # Geocode DNO centroids
    print("\n📍 Geocoding DNO region centroids...")

    geocoded = []
    for _, row in df.iterrows():
        dno_name = row['dno_full_name']

        # Try to match with DNO_CENTROIDS
        dno_key = None
        for key, info in DNO_CENTROIDS.items():
            if info['name'].lower() in dno_name.lower() or dno_name.lower() in info['name'].lower():
                dno_key = key
                break

        if dno_key:
            print(f"   {dno_name[:30]:30} → {DNO_CENTROIDS[dno_key]['postcode']}")
            geo = geocode_postcode(DNO_CENTROIDS[dno_key]['postcode'])
        else:
            print(f"   {dno_name[:30]:30} → No centroid mapping")
            geo = {"postcode": "", "latitude": None, "longitude": None, "region": "", "admin_district": ""}

        geocoded.append({
            **row.to_dict(),
            **geo
        })

    return pd.DataFrame(geocoded)

# -----------------------------------
# 3) Export to Google Sheets
# -----------------------------------
def export_to_sheets(df):
    """
    Export geocoded constraint data to Google Sheets
    """
    print(f"\n📤 Exporting to Google Sheets...")
    print(f"   Spreadsheet ID: {SPREADSHEET_ID}")
    print(f"   Sheet name: {SHEET_NAME}")

    # Prepare data for Sheets
    # Format numbers nicely
    df_export = df.copy()
    df_export['total_cost_gbp'] = df_export['total_cost_gbp'].apply(lambda x: f"£{x:,.2f}")
    df_export['voltage_cost_gbp'] = df_export['voltage_cost_gbp'].apply(lambda x: f"£{x:,.2f}")
    df_export['thermal_cost_gbp'] = df_export['thermal_cost_gbp'].apply(lambda x: f"£{x:,.2f}")
    df_export['avg_monthly_cost'] = df_export['avg_monthly_cost'].apply(lambda x: f"£{x:,.2f}")
    df_export['area_sq_km'] = df_export['area_sq_km'].apply(lambda x: f"{x:,.0f}")

    # Reorder columns
    cols_order = [
        'dno_full_name', 'postcode', 'latitude', 'longitude',
        'total_cost_gbp', 'voltage_cost_gbp', 'thermal_cost_gbp',
        'avg_monthly_cost', 'num_months', 'area_sq_km',
        'earliest_year', 'latest_year', 'region', 'admin_district'
    ]
    df_export = df_export[[c for c in cols_order if c in df_export.columns]]

    # Convert to values
    values = [df_export.columns.tolist()] + df_export.values.tolist()

    # Setup Sheets API
    credentials = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=credentials)

    # Check if sheet exists
    try:
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_names = [s['properties']['title'] for s in sheets]

        if SHEET_NAME not in sheet_names:
            # Create new sheet
            print(f"   Creating new sheet '{SHEET_NAME}'...")
            request = {
                'addSheet': {
                    'properties': {
                        'title': SHEET_NAME
                    }
                }
            }
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': [request]}
            ).execute()
    except Exception as e:
        print(f"   ⚠️  Error checking/creating sheet: {e}")

    # Write data
    sheet_body = {"values": values}

    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A1",
        valueInputOption="RAW",
        body=sheet_body
    ).execute()

    print(f"✅ Exported {len(df)} rows to Google Sheet '{SHEET_NAME}'")
    print(f"\n📊 Summary:")
    print(f"   Total DNO regions: {len(df)}")
    print(f"   Total constraint costs: £{df['total_cost_gbp'].sum():,.2f}")
    print(f"   Date range: {df['earliest_year'].min()}-{df['latest_year'].max()}")

    return True

# -----------------------------------
# Main entry
# -----------------------------------
def main():
    print("🗺️  CONSTRAINT DATA WITH POSTCODE GEOCODING")
    print("=" * 60)

    # Fetch and geocode constraint data
    df = fetch_geocoded_constraints()

    # Export to Google Sheets
    success = export_to_sheets(df)

    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TASKS COMPLETED!")
        print("\n📋 Next steps:")
        print("   1. Open Google Sheets: https://docs.google.com/spreadsheets/d/" + SPREADSHEET_ID)
        print("   2. Go to 'Constraint Summary' sheet")
        print("   3. Select data range (A1:N15)")
        print("   4. Click: Insert → Chart")
        print("   5. Choose: Geo chart → Region shading")
        print("   6. Customize: Set region to 'United Kingdom'")
        print("   7. Set color scale: Min=Green, Max=Red for total_cost_gbp")

if __name__ == "__main__":
    main()
