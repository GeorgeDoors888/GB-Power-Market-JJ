#!/usr/bin/env python3
"""
add_dno_breakdown_to_sheets.py

Adds DNO-level breakdown showing individual constraint costs per DNO
instead of aggregated nationwide totals.

Exports:
 - DNO Summary with TOTAL costs (all-time sum per DNO)
 - DNO Monthly Breakdown (each DNO × each month)
 - Ready for Geo Chart with regional color shading
"""

import os
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "DNO Breakdown"

bq_client = bigquery.Client(project=PROJECT_ID, location="US")

def get_dno_total_costs():
    """
    Get total constraint costs per DNO (all-time sum)
    """
    print("\n📊 Calculating total costs per DNO...")

    query = f"""
    WITH dno_costs AS (
        SELECT
            dno_id,
            dno_full_name,
            SUM(allocated_total_cost) as total_cost,
            SUM(allocated_voltage_cost) as voltage_cost,
            SUM(allocated_thermal_cost) as thermal_cost,
            AVG(area_sq_km) as area_sq_km,
            AVG(cost_per_sq_km) as avg_cost_per_sq_km,
            COUNT(*) as months_of_data
        FROM `{PROJECT_ID}.{BQ_DATASET}.constraint_costs_by_dno`
        GROUP BY dno_id, dno_full_name
    ),
    dno_geo AS (
        SELECT
            dno_id,
            dno_code,
            gsp_group,
            area_name,
            ST_Y(ST_CENTROID(boundary)) as latitude,
            ST_X(ST_CENTROID(boundary)) as longitude
        FROM `{PROJECT_ID}.{BQ_DATASET}.neso_dno_boundaries`
    )
    SELECT
        c.dno_id,
        c.dno_full_name,
        g.dno_code,
        g.gsp_group,
        g.area_name,
        c.total_cost,
        c.voltage_cost,
        c.thermal_cost,
        c.area_sq_km,
        c.avg_cost_per_sq_km,
        c.months_of_data,
        g.latitude,
        g.longitude
    FROM dno_costs c
    LEFT JOIN dno_geo g ON c.dno_id = g.dno_id
    ORDER BY c.total_cost DESC
    """

    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} DNOs")
    print(f"   💰 Total across all DNOs: £{df['total_cost'].sum():,.0f}")
    print(f"\n   Top 3 DNOs by cost:")
    for idx, row in df.head(3).iterrows():
        print(f"      {row['dno_full_name']}: £{row['total_cost']:,.0f}")

    return df

def get_dno_monthly_breakdown():
    """
    Get constraint costs by DNO and month (time series) - Latest 12 months only
    """
    print("\n📈 Fetching DNO monthly breakdown (latest 12 months)...")

    query = f"""
    SELECT
        dno_id,
        dno_full_name,
        year,
        month,
        allocated_total_cost as total_cost,
        allocated_voltage_cost as voltage_cost,
        allocated_thermal_cost as thermal_cost,
        cost_per_sq_km
    FROM `{PROJECT_ID}.{BQ_DATASET}.constraint_costs_by_dno`
    WHERE year >= 2024  -- Latest data only for faster export
    ORDER BY dno_id, year, month
    LIMIT 500
    """

    df = bq_client.query(query).to_dataframe()
    print(f"   ✅ Retrieved {len(df)} DNO-month records")
    if len(df) > 0:
        print(f"   📅 Date range: {df['year'].min()}-{df['month'].min():02d} to {df['year'].max()}-{df['month'].max():02d}")

    return df

def export_to_sheets(total_df, monthly_df):
    """
    Export DNO breakdown to Google Sheets
    """
    print("\n📤 Exporting DNO breakdown to Google Sheets...")

    # Setup Sheets API v4
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=creds)

    # Prepare DNO Summary data
    summary_data = [[
        "DNO ID", "DNO Name", "Code", "GSP Group", "Area",
        "Total Cost (£)", "Voltage (£)", "Thermal (£)",
        "Area (km²)", "Cost/km²", "Months", "Latitude", "Longitude"
    ]]

    for _, row in total_df.iterrows():
        summary_data.append([
            int(row['dno_id']),
            row['dno_full_name'],
            row['dno_code'],
            row['gsp_group'],
            row['area_name'],
            float(row['total_cost']),
            float(row['voltage_cost']),
            float(row['thermal_cost']),
            float(row['area_sq_km']),
            float(row['avg_cost_per_sq_km']),
            int(row['months_of_data']),
            float(row['latitude']),
            float(row['longitude'])
        ])

    # Prepare monthly breakdown data
    monthly_data = [[
        "DNO ID", "DNO Name", "Year", "Month",
        "Total Cost (£)", "Voltage (£)", "Thermal (£)", "Cost/km²"
    ]]

    for _, row in monthly_df.iterrows():
        monthly_data.append([
            int(row['dno_id']),
            row['dno_full_name'],
            int(row['year']),
            int(row['month']),
            float(row['total_cost']),
            float(row['voltage_cost']),
            float(row['thermal_cost']),
            float(row['cost_per_sq_km'])
        ])

    try:
        # Create sheet if doesn't exist
        print(f"   Writing to '{SHEET_NAME}' sheet...")

        # Write DNO Summary (top section)
        body = {"values": summary_data}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",
            valueInputOption="RAW",
            body=body
        ).execute()

        # Write monthly breakdown (below with gap)
        monthly_start_row = len(summary_data) + 3
        body = {"values": monthly_data}
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A{monthly_start_row}",
            valueInputOption="RAW",
            body=body
        ).execute()

        print(f"   ✅ Exported {len(summary_data)-1} DNO summary records")
        print(f"   ✅ Exported {len(monthly_data)-1} monthly breakdown records")

        print(f"\n" + "=" * 70)
        print(f"✅ DNO BREAKDOWN EXPORTED TO GOOGLE SHEETS")
        print(f"=" * 70)
        print(f"\n🔗 Open: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
        print(f"📋 Sheet: '{SHEET_NAME}'")
        print(f"\n📊 Data Layout:")
        print(f"   • Rows 1-{len(summary_data)}: DNO Summary (total costs per DNO)")
        print(f"   • Rows {monthly_start_row}-{monthly_start_row + len(monthly_data) - 1}: Monthly breakdown")
        print(f"\n🗺️ To Create DNO-Level Geo Chart:")
        print(f"   1. Select range A1:F{len(summary_data)} (DNO Name + Total Cost)")
        print(f"   2. Insert → Chart → Geo chart (region shading)")
        print(f"   3. Customize → Geo → Region: United Kingdom")
        print(f"   4. Color axis: Column F (Total Cost)")
        print(f"\n💡 Chart will show:")
        print(f"   - 14 DNO regions color-coded by constraint cost")
        print(f"   - Darker red = Higher costs")
        print(f"   - Lighter yellow = Lower costs")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Note: Sheet '{SHEET_NAME}' may not exist yet")
        print(f"   Solution: Create sheet manually, then re-run")

def main():
    print("🗺️  DNO-LEVEL CONSTRAINT BREAKDOWN")
    print("=" * 70)

    print("\n1️⃣  Calculating total costs per DNO...")
    total_df = get_dno_total_costs()

    print("\n2️⃣  Fetching monthly breakdown...")
    monthly_df = get_dno_monthly_breakdown()

    print("\n3️⃣  Exporting to Google Sheets...")
    export_to_sheets(total_df, monthly_df)

    print("\n✅ Complete!")

if __name__ == "__main__":
    main()
