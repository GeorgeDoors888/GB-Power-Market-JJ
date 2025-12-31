#!/usr/bin/env python3
"""
Export NESO Constraint Cost Data to Google Sheets
Creates 'Constraint Costs' sheet in GB Live 2 dashboard with daily timeline and summaries
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # GB Live 2
SHEET_NAME = "Constraint Costs"

# BigQuery client
bq_client = bigquery.Client(project=PROJECT_ID, location="US")

# Google Sheets client
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
sheets_client = gspread.authorize(creds)

def fetch_daily_data(days=90):
    """Fetch last N days of daily constraint data"""
    print(f"\nFetching last {days} days of constraint data...")

    sql = f"""
    SELECT
      constraint_date,
      ROUND(thermal_cost_gbp, 0) as thermal_gbp,
      ROUND(voltage_cost_gbp, 0) as voltage_gbp,
      ROUND(largest_loss_cost_gbp, 0) as loss_gbp,
      ROUND(inertia_cost_gbp, 0) as inertia_gbp,
      ROUND(total_cost_gbp, 0) as total_gbp,
      ROUND(total_volume_mwh, 0) as volume_mwh,
      ROUND(avg_price_per_mwh, 2) as price_per_mwh,
      ROUND(cost_7d_avg, 0) as cost_7d_avg,
      dominant_constraint
    FROM `{PROJECT_ID}.{DATASET}.constraint_trend_summary`
    WHERE constraint_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY constraint_date DESC
    LIMIT {days}
    """

    df = bq_client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} days")
    return df

def fetch_monthly_data():
    """Fetch monthly aggregations (last 24 months)"""
    print("\nFetching monthly aggregations...")

    sql = f"""
    SELECT
      year_month,
      ROUND(thermal_cost_gbp, 0) as thermal_gbp,
      ROUND(voltage_cost_gbp, 0) as voltage_gbp,
      ROUND(largest_loss_cost_gbp, 0) as loss_gbp,
      ROUND(inertia_cost_gbp, 0) as inertia_gbp,
      ROUND(total_cost_gbp, 0) as total_gbp,
      days_in_period
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_monthly`
    ORDER BY year_month DESC
    LIMIT 24
    """

    df = bq_client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} months")
    return df

def fetch_annual_data():
    """Fetch annual aggregations (all available FYs)"""
    print("\nFetching annual aggregations...")

    sql = f"""
    SELECT
      financial_year,
      CONCAT('FY', CAST(financial_year AS STRING), '-', SUBSTR(CAST(financial_year + 1 AS STRING), 3, 2)) as fy_label,
      ROUND(thermal_cost_gbp / 1000000, 1) as thermal_millions,
      ROUND(voltage_cost_gbp / 1000000, 1) as voltage_millions,
      ROUND(largest_loss_cost_gbp / 1000000, 1) as loss_millions,
      ROUND(inertia_cost_gbp / 1000000, 1) as inertia_millions,
      ROUND(total_cost_gbp / 1000000, 1) as total_millions,
      ROUND(thermal_pct, 1) as thermal_pct,
      ROUND(voltage_pct, 1) as voltage_pct,
      days_in_period
    FROM `{PROJECT_ID}.{DATASET}.constraint_costs_annual`
    ORDER BY financial_year DESC
    """

    df = bq_client.query(sql).to_dataframe()
    print(f"✅ Retrieved {len(df)} financial years")
    return df

def create_or_clear_sheet(spreadsheet):
    """Create or clear the Constraint Costs sheet"""
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
        print(f"Sheet '{SHEET_NAME}' exists, clearing...")
        sheet.clear()
    except gspread.WorksheetNotFound:
        print(f"Creating sheet '{SHEET_NAME}'...")
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows=1000, cols=20)

    return sheet

def write_headers_and_data(sheet):
    """Write all data to sheet with formatting"""

    # Fetch data
    daily_df = fetch_daily_data(90)
    monthly_df = fetch_monthly_data()
    annual_df = fetch_annual_data()

    # Build output rows
    rows = []

    # Title
    rows.append([f"NESO Constraint Costs - Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
    rows.append([])

    # Section 1: Annual Summary
    rows.append(["FINANCIAL YEAR TOTALS (£M)"])
    rows.append(["Financial Year", "Total £M", "Thermal £M", "Voltage £M", "Loss £M", "Inertia £M", "Thermal %", "Voltage %", "Days"])

    for _, row in annual_df.iterrows():
        rows.append([
            row['fy_label'],
            row['total_millions'],
            row['thermal_millions'],
            row['voltage_millions'],
            row['loss_millions'],
            row['inertia_millions'],
            f"{row['thermal_pct']}%",
            f"{row['voltage_pct']}%",
            row['days_in_period']
        ])

    rows.append([])
    rows.append([])

    # Section 2: Monthly Summary
    rows.append(["MONTHLY TOTALS (Last 24 Months)"])
    rows.append(["Year-Month", "Total £", "Thermal £", "Voltage £", "Loss £", "Inertia £", "Days"])

    for _, row in monthly_df.iterrows():
        rows.append([
            row['year_month'],
            f"£{row['total_gbp']:,.0f}",
            f"£{row['thermal_gbp']:,.0f}",
            f"£{row['voltage_gbp']:,.0f}",
            f"£{row['loss_gbp']:,.0f}",
            f"£{row['inertia_gbp']:,.0f}",
            row['days_in_period']
        ])

    rows.append([])
    rows.append([])

    # Section 3: Daily Timeline
    rows.append(["DAILY TIMELINE (Last 90 Days)"])
    rows.append(["Date", "Total £", "Thermal £", "Voltage £", "Loss £", "Inertia £", "Volume MWh", "£/MWh", "7d Avg £", "Dominant Type"])

    for _, row in daily_df.iterrows():
        rows.append([
            str(row['constraint_date']),
            f"£{row['total_gbp']:,.0f}",
            f"£{row['thermal_gbp']:,.0f}",
            f"£{row['voltage_gbp']:,.0f}",
            f"£{row['loss_gbp']:,.0f}",
            f"£{row['inertia_gbp']:,.0f}",
            f"{row['volume_mwh']:,.0f}",
            f"£{row['price_per_mwh']:.2f}",
            f"£{row['cost_7d_avg']:,.0f}",
            row['dominant_constraint']
        ])

    # Write all rows
    print(f"\nWriting {len(rows)} rows to sheet...")
    sheet.update('A1', rows, value_input_option='USER_ENTERED')

    # Apply formatting
    print("Applying formatting...")

    # Bold headers
    header_rows = [1, 3, 4, 4 + len(annual_df) + 3, 4 + len(annual_df) + 4,
                   4 + len(annual_df) + len(monthly_df) + 7, 4 + len(annual_df) + len(monthly_df) + 8]

    for row_num in header_rows:
        sheet.format(f'A{row_num}:Z{row_num}', {
            'textFormat': {'bold': True, 'fontSize': 11},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

    # Title row
    sheet.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 14},
        'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.0}
    })

    # Freeze header rows
    sheet.freeze(rows=1, cols=0)

    # Auto-resize columns
    sheet.columns_auto_resize(0, 10)

    print("✅ Formatting applied")

def main():
    try:
        print(f"Connecting to spreadsheet: {SPREADSHEET_ID}")
        spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)

        # Create or clear sheet
        sheet = create_or_clear_sheet(spreadsheet)

        # Write data
        write_headers_and_data(sheet)

        print(f"\n✅ SUCCESSFULLY EXPORTED CONSTRAINT DATA TO SHEETS")
        print(f"   Sheet: {SHEET_NAME}")
        print(f"   URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
