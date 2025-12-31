#!/usr/bin/env python3
"""
create_dno_constraint_map.py

Creates a working DNO constraint cost map for Google Sheets.
Uses neso_dno_reference + constraint_costs_by_dno data.

This replaces the non-working constraint_with_postcode_geo_sheets.py approach.
"""

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Constraint Map Data"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def get_dno_constraint_data():
    """
    Query BigQuery for DNO constraint costs (aggregated over all time)
    Returns: List of dicts with DNO region and cost data
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    WITH aggregated_costs AS (
        SELECT
            dno_id,
            dno_full_name,
            area_name,
            MAX(area_sq_km) as area_sq_km,
            SUM(allocated_total_cost) as total_cost_gbp,
            SUM(allocated_voltage_cost) as voltage_cost_gbp,
            SUM(allocated_thermal_cost) as thermal_cost_gbp,
            SUM(allocated_inertia_cost) as inertia_cost_gbp,
            AVG(cost_per_sq_km) as avg_cost_per_sq_km,
            MIN(month_start) as first_month,
            MAX(month_start) as last_month,
            COUNT(*) as num_months
        FROM `{PROJECT_ID}.{DATASET}.constraint_costs_by_dno`
        GROUP BY dno_id, dno_full_name, area_name
    ),
    dno_reference AS (
        SELECT
            mpan_distributor_id,
            dno_name,
            dno_short_code,
            gsp_group_id,
            gsp_group_name,
            primary_coverage_area
        FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
    )
    SELECT
        c.dno_full_name,
        COALESCE(r.dno_short_code, CAST(c.dno_id AS STRING)) as dno_code,
        c.area_name,
        COALESCE(r.gsp_group_name, 'N/A') as gsp_group,
        c.area_sq_km,
        c.total_cost_gbp,
        c.voltage_cost_gbp,
        c.thermal_cost_gbp,
        c.inertia_cost_gbp,
        c.avg_cost_per_sq_km,
        c.num_months,
        c.first_month,
        c.last_month,
        RANK() OVER (ORDER BY c.total_cost_gbp DESC) as cost_rank
    FROM aggregated_costs c
    LEFT JOIN dno_reference r ON c.dno_id = r.mpan_distributor_id
    ORDER BY c.total_cost_gbp DESC
    """

    print("📊 Querying DNO constraint data from BigQuery...")
    results = client.query(query).result()

    data = []
    for row in results:
        data.append({
            'dno_name': row.dno_full_name,
            'dno_code': row.dno_code,
            'coverage_area': row.area_name,
            'gsp_group': row.gsp_group,
            'area_sq_km': float(row.area_sq_km) if row.area_sq_km else 0,
            'total_cost_gbp': float(row.total_cost_gbp) if row.total_cost_gbp else 0,
            'voltage_cost_gbp': float(row.voltage_cost_gbp) if row.voltage_cost_gbp else 0,
            'thermal_cost_gbp': float(row.thermal_cost_gbp) if row.thermal_cost_gbp else 0,
            'inertia_cost_gbp': float(row.inertia_cost_gbp) if row.inertia_cost_gbp else 0,
            'avg_cost_per_sq_km': float(row.avg_cost_per_sq_km) if row.avg_cost_per_sq_km else 0,
            'num_months': int(row.num_months),
            'first_month': str(row.first_month),
            'last_month': str(row.last_month),
            'cost_rank': int(row.cost_rank)
        })

    print(f"   ✓ Retrieved {len(data)} DNO regions")
    print(f"   ✓ Data period: {data[0]['first_month']} to {data[0]['last_month']} ({data[0]['num_months']} months)")
    return data

def export_to_sheets(data):
    """
    Export DNO constraint data to Google Sheets
    """
    print(f"\n📤 Exporting to Google Sheets...")

    # Authenticate
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    # Open spreadsheet
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    # Create or clear sheet
    try:
        worksheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"   ✓ Found existing '{SHEET_NAME}' sheet")
        worksheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        print(f"   Creating new '{SHEET_NAME}' sheet...")
        worksheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=100, cols=20)

    # Prepare data for Sheets
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    headers = [
        'DNO Region',
        'Code',
        'Coverage Area',
        'GSP Group',
        'Area (km²)',
        'Total Cost (£M)',
        'Voltage (£M)',
        'Thermal (£M)',
        'Inertia (£M)',
        'Cost/km² (£)',
        'Months',
        'Cost Rank'
    ]

    rows = [headers]
    for item in data:
        rows.append([
            item['dno_name'],
            item['dno_code'],
            item['coverage_area'],
            item['gsp_group'],
            round(item['area_sq_km'], 0),
            round(item['total_cost_gbp'] / 1_000_000, 2),  # Convert to millions
            round(item['voltage_cost_gbp'] / 1_000_000, 2),
            round(item['thermal_cost_gbp'] / 1_000_000, 2),
            round(item['inertia_cost_gbp'] / 1_000_000, 2),
            round(item['avg_cost_per_sq_km'], 2),
            item['num_months'],
            item['cost_rank']
        ])

    # Add metadata rows
    rows.append([])
    rows.append(['Data updated:', timestamp])
    rows.append(['Source:', f'{PROJECT_ID}.{DATASET}.constraint_costs_by_dno'])
    rows.append(['Data period:', f"{data[0]['first_month']} to {data[0]['last_month']}"])
    rows.append(['Total months:', data[0]['num_months']])

    # Write to sheet
    print(f"   Writing {len(rows)} rows...")
    worksheet.update('A1', rows)

    # Format header row
    print(f"   Applying formatting...")
    worksheet.format('A1:L1', {
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.6},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })

    # Freeze header row
    worksheet.freeze(rows=1)

    # Auto-resize columns
    worksheet.columns_auto_resize(0, 11)

    print(f"   ✓ Export complete!")
    return worksheet

def create_instructions():
    """
    Return instructions for creating Geo Chart in Google Sheets
    """
    return """
╔══════════════════════════════════════════════════════════════════════════════╗
║                   📍 HOW TO CREATE CONSTRAINT MAP IN SHEETS                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

Data has been exported to: "{SHEET_NAME}"

TO CREATE GEO CHART:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Open the Google Sheet:
   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}

2. Select data range:
   Highlight cells A1:E15 (DNO Region + Coverage Area + Total Cost)

3. Insert Chart:
   Click: Insert → Chart

4. Change Chart Type:
   In Chart Editor → Setup tab:
   - Chart type → scroll to "Map" section
   - Select "Geo chart"

5. Configure Chart:
   In Chart Editor → Setup:
   - Location: Column A (DNO Region) or Column C (Coverage Area)
   - Color: Column E (Total Cost £M)
   - (Optional) Size: Column F (Total Volume MWh)

6. Customize Appearance:
   In Chart Editor → Customize:
   - Geo → Region: "United Kingdom"
   - Colors → Min color: Green (#34A853)
   - Colors → Max color: Red (#EA4335)
   - Background color: Light gray (#F5F5F5)

7. Position Chart:
   - Drag chart to desired location (e.g., cell K1)
   - Resize as needed

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 TIPS:
  • Use "Coverage Area" (Column C) for better geographic matching
  • Higher cost = darker/redder color
  • Chart updates automatically when data is refreshed

📊 DATA INTERPRETATION:
  • Cost Rank 1 = Highest constraint costs
  • Avg Cost £/MWh shows price intensity
  • Total Volume shows constraint frequency

🔄 TO UPDATE DATA:
   Run this script again: python3 create_dno_constraint_map.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""".format(SHEET_NAME=SHEET_NAME, SPREADSHEET_ID=SPREADSHEET_ID)

def main():
    print("╔══════════════════════════════════════════════════════════════════════════════╗")
    print("║           DNO Constraint Cost Map Creator - GB Power Market JJ              ║")
    print("╚══════════════════════════════════════════════════════════════════════════════╝\n")

    try:
        # Step 1: Get data from BigQuery
        data = get_dno_constraint_data()

        if not data:
            print("⚠️  No constraint data found in BigQuery")
            return

        # Step 2: Export to Google Sheets
        worksheet = export_to_sheets(data)

        # Step 3: Display summary
        print(f"\n✅ SUCCESS!")
        print(f"\n📊 Summary:")
        print(f"   - {len(data)} DNO regions exported")
        print(f"   - Total constraint cost: £{sum(d['total_cost_gbp'] for d in data) / 1_000_000:.1f}M")
        print(f"   - Sheet: '{SHEET_NAME}'")
        print(f"   - URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

        # Step 4: Show top 3 most expensive regions
        print(f"\n🔥 Top 3 Costliest DNO Regions:")
        for i, item in enumerate(data[:3], 1):
            print(f"   {i}. {item['dno_name']:30} £{item['total_cost_gbp'] / 1_000_000:>6.1f}M")

        # Step 5: Display instructions
        print(create_instructions())

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
