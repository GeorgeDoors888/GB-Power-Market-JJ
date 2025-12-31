#!/usr/bin/env python3
"""
constraint_map_configured.py

CONFIGURED VERSION of constraint geocoding script
Creates DNO constraint cost geographic visualization using existing BigQuery data

Key Changes from user's template:
- Uses actual project/dataset (inner-cinema-476211-u9.uk_energy_prod)
- Maps to actual NESO constraint tables
- Exports to Live Dashboard spreadsheet
- Uses DNO boundaries (no postcodes.io needed - data already in BigQuery)

Data Flow:
1. Query NESO constraint costs from BigQuery (neso_constraint_breakdown_*)
2. Aggregate by DNO region + time period
3. Export summary to Google Sheets for Geo Chart visualization

Requirements:
  pip install google-cloud-bigquery google-auth gspread requests

Environment:
  GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json
"""

import os
import requests
import json
import datetime

from google.cloud import bigquery
from google.oauth2 import service_account
import gspread

# -----------------------------------
# CONFIGURATION (CORRECTED)
# -----------------------------------

# Google Cloud + BigQuery
PROJECT_ID = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"

# NESO Constraint Tables (actual tables in your dataset)
CONSTRAINT_BREAKDOWN_TABLE = "neso_constraint_breakdown_2024"  # Adjust year as needed
DNO_REFERENCE_TABLE = "neso_dno_reference"  # 14 DNO regions with boundaries

# Trend aggregation output
TREND_TABLE = "constraint_trend_by_dno"  # Will be created in uk_energy_prod

# Google Sheets
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # Live Dashboard v2 spreadsheet
SHEET_NAME = "Constraint Map Data"  # New sheet to create

# Credentials
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Initialize BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# -----------------------------------
# 1) Query DNO constraint costs (no geocoding needed)
# -----------------------------------
def query_dno_constraint_costs():
    """
    Query NESO constraint breakdown data and aggregate by DNO region
    Uses existing DNO reference table (no postcodes.io API needed)
    """
    print("📊 Querying DNO constraint costs from BigQuery...")

    # Check which constraint tables exist
    query = f"""
    SELECT table_name
    FROM `{PROJECT_ID}.{BQ_DATASET}.INFORMATION_SCHEMA.TABLES`
    WHERE table_name LIKE 'neso_constraint%'
    ORDER BY table_name
    """

    tables = [row.table_name for row in bq_client.query(query).result()]
    print(f"✅ Found {len(tables)} NESO constraint tables:")
    for table in tables:
        print(f"   • {table}")

    if not tables:
        print("❌ No NESO constraint tables found")
        return None

    # Use the most recent constraint breakdown table
    constraint_table = None
    for table in reversed(tables):
        if 'breakdown' in table:
            constraint_table = table
            break

    if not constraint_table:
        print("⚠️  No constraint_breakdown table found, using first available")
        constraint_table = tables[0]

    print(f"\n🎯 Using table: {constraint_table}")

    # Sample query to understand structure
    sample_query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{BQ_DATASET}.{constraint_table}`
    LIMIT 5
    """

    print("\n📝 Sample data structure:")
    sample_rows = bq_client.query(sample_query).result()
    for row in sample_rows:
        print(f"   {dict(row)}")
        break  # Just show first row structure

    return constraint_table

# -----------------------------------
# 2) Create DNO constraint trend summary
# -----------------------------------
def create_dno_constraint_trend_summary(constraint_table):
    """
    Creates BigQuery aggregated constraint cost/volume trend by DNO over time
    """
    print(f"\n📊 Creating DNO constraint trend summary...")

    query = f"""
    CREATE OR REPLACE TABLE `{PROJECT_ID}.{BQ_DATASET}.{TREND_TABLE}` AS
    WITH constraint_data AS (
      SELECT
        EXTRACT(YEAR FROM startTime) AS year,
        EXTRACT(MONTH FROM startTime) AS month,
        boundary,
        reasonCode,
        CAST(totalCost AS FLOAT64) AS total_cost_gbp,
        CAST(volume AS FLOAT64) AS volume_mw
      FROM `{PROJECT_ID}.{BQ_DATASET}.{constraint_table}`
      WHERE startTime IS NOT NULL
    )
    SELECT
      year,
      month,
      boundary,
      reasonCode,
      COUNT(*) AS event_count,
      SUM(total_cost_gbp) AS total_cost_gbp,
      SUM(volume_mw) AS total_volume_mw,
      AVG(total_cost_gbp) AS avg_cost_per_event,
      MAX(total_cost_gbp) AS max_cost_event
    FROM constraint_data
    GROUP BY year, month, boundary, reasonCode
    ORDER BY year DESC, month DESC, total_cost_gbp DESC;
    """

    try:
        job = bq_client.query(query)
        job.result()  # Wait for completion
        print(f"✅ Created aggregated trend table: {BQ_DATASET}.{TREND_TABLE}")

        # Show sample results
        sample_query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{BQ_DATASET}.{TREND_TABLE}`
        LIMIT 10
        """
        print("\n📊 Sample trend data:")
        for row in bq_client.query(sample_query).result():
            print(f"   {row.year}-{row.month:02d} | {row.boundary} | £{row.total_cost_gbp:,.0f} | {row.event_count} events")

        return True

    except Exception as e:
        print(f"❌ Error creating trend table: {e}")
        return False

# -----------------------------------
# 3) Export to Google Sheets (for Geo Chart)
# -----------------------------------
def export_summary_to_sheets():
    """
    Reads the constraint trend summary and exports to Google Sheets
    Creates a format suitable for Google Sheets Geo Chart
    """
    print(f"\n📤 Exporting to Google Sheets...")

    # Query summary data
    query = f"""
    SELECT
      CONCAT(year, '-', LPAD(CAST(month AS STRING), 2, '0')) AS period,
      boundary,
      reasonCode,
      event_count,
      total_cost_gbp,
      total_volume_mw,
      avg_cost_per_event
    FROM `{PROJECT_ID}.{BQ_DATASET}.{TREND_TABLE}`
    ORDER BY year DESC, month DESC, total_cost_gbp DESC
    LIMIT 500
    """

    rows = bq_client.query(query).result()

    # Build data for Google Sheets
    sheet_data = [[
        "Period", "Boundary", "Reason", "Events", "Total Cost (£)",
        "Total Volume (MW)", "Avg Cost/Event (£)"
    ]]

    for r in rows:
        sheet_data.append([
            r.period,
            r.boundary or "Unknown",
            r.reasonCode or "Unknown",
            r.event_count,
            round(r.total_cost_gbp, 2) if r.total_cost_gbp else 0,
            round(r.total_volume_mw, 2) if r.total_volume_mw else 0,
            round(r.avg_cost_per_event, 2) if r.avg_cost_per_event else 0
        ])

    print(f"✅ Prepared {len(sheet_data)-1} rows for export")

    # Connect to Google Sheets
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)

        # Try to get existing sheet or create new
        try:
            worksheet = spreadsheet.worksheet(SHEET_NAME)
            print(f"✅ Found existing sheet '{SHEET_NAME}'")
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            print(f"📝 Creating new sheet '{SHEET_NAME}'")
            worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=len(sheet_data)+10, cols=10)

        # Write data
        worksheet.update('A1', sheet_data)
        print(f"✅ Exported to Google Sheet '{SHEET_NAME}' (ID: {SHEET_ID})")
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{SHEET_ID}")

        # Instructions for Geo Chart
        print("\n📊 To create Geo Chart in Google Sheets:")
        print("   1. Select the data range (columns: Boundary, Total Cost)")
        print("   2. Insert → Chart")
        print("   3. Chart type → Geo chart")
        print("   4. Customize → Set region to 'United Kingdom'")
        print("   5. Color scale: min=green, max=red")

        return True

    except Exception as e:
        print(f"❌ Error exporting to Sheets: {e}")
        return False

# -----------------------------------
# 4) DNO Boundary Reference
# -----------------------------------
def show_dno_reference():
    """
    Display DNO reference data (14 regions with boundaries)
    """
    print("\n🗺️  Querying DNO reference data...")

    query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{BQ_DATASET}.{DNO_REFERENCE_TABLE}`
    ORDER BY dno_name
    """

    try:
        rows = bq_client.query(query).result()
        print(f"\n✅ DNO Reference (14 regions):")
        for row in rows:
            print(f"   • {row.dno_name} (ID: {row.dno_id})")
        return True
    except Exception as e:
        print(f"⚠️  Could not query DNO reference: {e}")
        return False

# -----------------------------------
# Main entry
# -----------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("🗺️  GB POWER CONSTRAINT MAP - CONFIGURED VERSION")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Dataset: {BQ_DATASET}")
    print(f"Output: {SHEET_NAME} in spreadsheet {SHEET_ID}")

    try:
        # Step 1: Show DNO reference
        print("\n" + "=" * 70)
        print("STEP 1: DNO Reference Data")
        print("=" * 70)
        show_dno_reference()

        # Step 2: Query constraint tables
        print("\n" + "=" * 70)
        print("STEP 2: Query Constraint Data")
        print("=" * 70)
        constraint_table = query_dno_constraint_costs()

        if not constraint_table:
            print("\n❌ No constraint data available - exiting")
            exit(1)

        # Step 3: Create trend summary
        print("\n" + "=" * 70)
        print("STEP 3: Create DNO Trend Summary")
        print("=" * 70)
        if not create_dno_constraint_trend_summary(constraint_table):
            print("\n⚠️  Could not create trend summary - continuing to export")

        # Step 4: Export to Sheets
        print("\n" + "=" * 70)
        print("STEP 4: Export to Google Sheets")
        print("=" * 70)
        if export_summary_to_sheets():
            print("\n" + "=" * 70)
            print("✅ ALL TASKS COMPLETED SUCCESSFULLY")
            print("=" * 70)
        else:
            print("\n⚠️  Export to Sheets failed - data in BigQuery only")

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
