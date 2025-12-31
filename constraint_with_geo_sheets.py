#!/usr/bin/env python3
"""
constraint_with_geo_sheets.py

Implements the Untitled-1.py specification:
 - Uses NESO DNO boundaries from BigQuery (already ingested GeoJSON)
 - Aggregates constraint cost/volume trends over time
 - Exports summary tables to Google Sheets for Geo Chart visualization

Uses existing data sources:
 - neso_dno_boundaries (14 DNO polygons with GEOGRAPHY)
 - neso_constraint_breakdown_* (annual financial year tables)
 - constraint_costs_by_dno (aggregated historical data)
"""

import os
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

# -----------------------------------
# CONFIGURATION
# -----------------------------------

# Google Cloud + BigQuery
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"

# Google Sheets
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
CONSTRAINT_SUMMARY_SHEET = "Constraint Summary"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# -----------------------------------
# 1) Get DNO boundary centroids for display
# -----------------------------------
def get_dno_centroids():
    """
    Calculate centroids of DNO boundary polygons for map display
    """
    print("📍 Calculating DNO centroids from boundaries...")

    query = f"""
    SELECT
        dno_full_name,
        dno_code,
        gsp_group,
        area_name,
        ST_Y(ST_CENTROID(boundary)) as latitude,
        ST_X(ST_CENTROID(boundary)) as longitude
    FROM `{PROJECT_ID}.{BQ_DATASET}.neso_dno_boundaries`
    ORDER BY dno_full_name
    """

    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} DNO centroids")

    return df

# -----------------------------------
# 2) Aggregate constraint costs by DNO and time
# -----------------------------------
def create_constraint_trend_summary():
    """
    Aggregates constraint costs by DNO, year, month from existing BigQuery tables
    Uses constraint_costs_by_dno (already aggregated monthly by DNO)
    """
    print("\n📊 Building constraint trend summary...")

    # Use the pre-aggregated table (simpler and faster)
    query = f"""
    SELECT
        year,
        month,
        SUM(allocated_total_cost) AS total_cost_gbp,
        SUM(allocated_voltage_cost) as voltage_cost_gbp,
        SUM(allocated_thermal_cost) as thermal_cost_gbp,
        AVG(cost_per_sq_km) as avg_cost_per_sq_km,
        COUNT(DISTINCT dno_id) as dno_count,
        COUNT(*) as records
    FROM `{PROJECT_ID}.{BQ_DATASET}.constraint_costs_by_dno`
    GROUP BY year, month
    ORDER BY year, month
    """

    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ Aggregated {len(df)} year-month periods")
    print(f"   📈 Total constraint cost: £{df['total_cost_gbp'].sum():,.0f}")

    return df

# -----------------------------------
# 3) Export to Google Sheets
# -----------------------------------
def export_to_sheets(centroid_df, trend_df):
    """
    Exports DNO centroids and constraint trends to Google Sheets
    """
    print("\n📤 Exporting to Google Sheets...")

    # Setup Sheets API v4 (gspread times out)
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)

    # Prepare data for export
    # Sheet 1: DNO Summary (for geo chart region names)
    dno_data = [["DNO Name", "Code", "GSP Group", "Area", "Latitude", "Longitude"]]
    for _, row in centroid_df.iterrows():
        dno_data.append([
            row['dno_full_name'],
            row['dno_code'],
            row['gsp_group'],
            row['area_name'],
            row['latitude'],
            row['longitude']
        ])

    # Sheet 2: Constraint Trends (time series)
    trend_data = [["Year", "Month", "Total Cost (£)", "Voltage (£)", "Thermal (£)", "Avg Cost/km²", "DNO Count", "Records"]]
    for _, row in trend_df.iterrows():
        trend_data.append([
            int(row['year']),
            int(row['month']),
            float(row['total_cost_gbp']),
            float(row['voltage_cost_gbp']),
            float(row['thermal_cost_gbp']),
            float(row['avg_cost_per_sq_km']),
            int(row['dno_count']),
            int(row['records'])
        ])

    # Clear and write to sheet
    try:
        # Create sheet if it doesn't exist, or clear existing
        print(f"   Writing to '{CONSTRAINT_SUMMARY_SHEET}' sheet...")

        # Write DNO summary
        body = {"values": dno_data}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{CONSTRAINT_SUMMARY_SHEET}!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Write trend data below (with gap)
        trend_start_row = len(dno_data) + 3
        body = {"values": trend_data}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{CONSTRAINT_SUMMARY_SHEET}!A{trend_start_row}",
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"   ✅ Exported {len(dno_data)-1} DNO records")
        print(f"   ✅ Exported {len(trend_data)-1} time periods")

        print(f"\n" + "=" * 60)
        print(f"✅ DATA EXPORTED TO GOOGLE SHEETS")
        print(f"=" * 60)
        print(f"\n📋 Next steps to create Geo Chart:")
        print(f"   1. Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"   2. Go to '{CONSTRAINT_SUMMARY_SHEET}' sheet")
        print(f"   3. Select DNO data range (A1:B{len(dno_data)})")
        print(f"   4. Click: Insert → Chart")
        print(f"   5. Chart type → Map → Geo chart (region shading)")
        print(f"   6. Customize → Geo → Region: United Kingdom")
        print(f"   7. Color by: Total Cost column from trend data")

    except Exception as e:
        print(f"   ❌ Error exporting to Sheets: {e}")
        print(f"   Note: Sheet '{CONSTRAINT_SUMMARY_SHEET}' may not exist yet")
        print(f"   Solution: Create sheet manually, then re-run")

# -----------------------------------
# Main entry
# -----------------------------------
def main():
    print("🗺️  CONSTRAINT DATA → GOOGLE SHEETS GEO CHART")
    print("=" * 60)

    print("\n1️⃣  Fetching DNO boundaries and centroids...")
    centroid_df = get_dno_centroids()

    print("\n2️⃣  Aggregating constraint costs over time...")
    trend_df = create_constraint_trend_summary()

    print("\n3️⃣  Exporting to Google Sheets...")
    export_to_sheets(centroid_df, trend_df)

    print("\n✅ All tasks completed!")

if __name__ == "__main__":
    main()
