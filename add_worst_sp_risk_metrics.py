#!/usr/bin/env python3
"""
add_worst_sp_risk_metrics.py

Calculates and displays the worst 5 settlement periods by net cashflow
over 7-day and 30-day windows for VLP/battery trading risk analysis.

Combines:
- BOALF acceptance revenue (acceptances × prices)
- Imbalance charges (position × SSP/SBP from bmrs_costs)

Updates Google Sheets Live Dashboard v2 with worst 5 SP losses.

Usage:
    python3 add_worst_sp_risk_metrics.py
    python3 add_worst_sp_risk_metrics.py --diagnostics-only

Requirements:
    pip3 install --user google-cloud-bigquery gspread pandas
"""

import argparse
from datetime import datetime, timedelta
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# ===== CONFIGURATION =====
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# Dashboard cell locations
WORST_5_LABEL_CELL = "K28"  # "Worst 5 SP Losses (7d)"
WORST_5_7D_START = "L28"    # Start of 7-day worst list
WORST_5_30D_LABEL = "K34"   # "Worst 30d SP"
WORST_5_30D_VALUE = "L34"   # Single worst SP over 30d

# ===== BIGQUERY CLIENT =====
bq_client = bigquery.Client(project=PROJECT_ID, location="US")


def get_worst_sp_cashflows(days=7, limit=5):
    """
    Calculate worst settlement periods by net cashflow.

    Uses boalf_with_prices for acceptance revenue.
    Uses bmrs_costs for imbalance prices.

    Returns DataFrame with columns:
    - settlement_date
    - settlement_period
    - net_cashflow_gbp (negative = loss)
    - acceptance_count
    - sp_time (HH:MM format)
    """

    query = f"""
    WITH acceptance_cashflow AS (
        -- BOALF acceptance revenue (pay-as-bid)
        -- Uses revenue_estimate_gbp (already calculated: acceptancePrice * acceptanceVolume * 0.5)
        SELECT
            settlement_date,
            settlementPeriod as settlement_period,
            SUM(revenue_estimate_gbp) as acceptance_revenue_gbp,
            COUNT(*) as acceptance_count
        FROM `{PROJECT_ID}.{DATASET}.boalf_with_prices`
        WHERE
            settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
            AND acceptancePrice IS NOT NULL
            AND acceptancePrice != 0
            AND revenue_estimate_gbp IS NOT NULL
        GROUP BY settlement_date, settlement_period
    ),

    imbalance_prices AS (
        -- System imbalance prices (SSP/SBP, single price since P305)
        SELECT
            CAST(settlementDate AS DATE) as settlement_date,
            settlementPeriod as settlement_period,
            AVG(systemSellPrice) as ssp,  -- Handles any duplicates
            AVG(systemBuyPrice) as sbp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE
            CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY settlement_date, settlement_period
    ),

    combined AS (
        SELECT
            COALESCE(a.settlement_date, i.settlement_date) as settlement_date,
            COALESCE(a.settlement_period, i.settlement_period) as settlement_period,
            COALESCE(a.acceptance_revenue_gbp, 0) as acceptance_revenue_gbp,
            COALESCE(a.acceptance_count, 0) as acceptance_count,
            i.ssp,
            i.sbp,
            -- Net cashflow: acceptance revenue (simplified - no position modeling yet)
            -- For now, using acceptance revenue as proxy for BM activity profitability
            COALESCE(a.acceptance_revenue_gbp, 0) as net_cashflow_gbp
        FROM acceptance_cashflow a
        FULL OUTER JOIN imbalance_prices i
            ON a.settlement_date = i.settlement_date
            AND a.settlement_period = i.settlement_period
    )

    SELECT
        settlement_date,
        settlement_period,
        net_cashflow_gbp,
        acceptance_count,
        ssp,
        sbp,
        -- Calculate SP time (00:00, 00:30, 01:00, etc.)
        CONCAT(
            LPAD(CAST(CAST((settlement_period - 1) / 2 AS INT64) AS STRING), 2, '0'),
            ':',
            CASE WHEN MOD(settlement_period, 2) = 1 THEN '00' ELSE '30' END
        ) as sp_time
    FROM combined
    WHERE acceptance_count > 0  -- Only SPs with BM activity
    ORDER BY net_cashflow_gbp ASC  -- Most negative (worst losses) first
    LIMIT {limit}
    """

    df = bq_client.query(query).to_dataframe()
    return df


def format_sp_loss_line(row):
    """
    Format a single worst SP line for dashboard display.

    Example: "Dec 28 SP42: -£12,450 (18:30-19:00)"
    """
    date_str = row['settlement_date'].strftime("%b %d")
    sp = int(row['settlement_period'])
    cashflow = row['net_cashflow_gbp']
    sp_time = row['sp_time']

    # Calculate end time (30 min later)
    start_hour, start_min = map(int, sp_time.split(':'))
    end_min = start_min + 30
    end_hour = start_hour
    if end_min >= 60:
        end_min -= 60
        end_hour += 1

    end_time = f"{end_hour:02d}:{end_min:02d}"

    return f"{date_str} SP{sp}: £{cashflow:,.0f} ({sp_time}-{end_time})"


def update_dashboard(worst_7d, worst_30d):
    """
    Update Google Sheets with worst 5 SP metrics.

    Args:
        worst_7d: DataFrame with 5 worst SPs over 7 days
        worst_30d: DataFrame with 5 worst SPs over 30 days (we'll use #1)
    """

    print("\n🔗 Connecting to Google Sheets...")

    # Google Sheets authentication
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
    worksheet = spreadsheet.worksheet(SHEET_NAME)

    print(f"✅ Connected to '{SHEET_NAME}'")

    # Prepare update data
    updates = []

    # 7-day worst 5 SP section
    updates.append({
        'range': WORST_5_LABEL_CELL,
        'values': [["Worst 5 SP Losses (7d):"]]
    })

    # Format 7d worst list (5 rows)
    worst_7d_lines = []
    for i, row in worst_7d.iterrows():
        if i < 5:  # Ensure only 5 lines
            worst_7d_lines.append([format_sp_loss_line(row)])
        else:
            break

    # Pad to 5 rows if fewer results
    while len(worst_7d_lines) < 5:
        worst_7d_lines.append(["No data"])

    # Write 7d worst list starting at L28
    start_row = int(WORST_5_7D_START[1:])  # Extract row number
    for i, line in enumerate(worst_7d_lines):
        updates.append({
            'range': f"L{start_row + i}",
            'values': [line]
        })

    # 30-day worst single SP
    if not worst_30d.empty:
        worst_30d_single = worst_30d.iloc[0]
        worst_30d_text = format_sp_loss_line(worst_30d_single)
    else:
        worst_30d_text = "No data"

    updates.append({
        'range': WORST_5_30D_LABEL,
        'values': [["Worst 30d SP:"]]
    })
    updates.append({
        'range': WORST_5_30D_VALUE,
        'values': [[worst_30d_text]]
    })

    # Batch update
    print(f"\n📝 Updating dashboard cells...")
    for update in updates:
        worksheet.update(update['range'], update['values'])
        print(f"   ✅ {update['range']}: {update['values'][0][0][:50]}...")

    print(f"\n✅ Dashboard updated successfully!")
    print(f"   7d worst: K28:L32")
    print(f"   30d worst: K34:L34")


def run_diagnostics_only():
    """
    Run diagnostics without updating dashboard.
    Shows worst SPs for analysis.
    """

    print("=" * 70)
    print("🔍 WORST SP RISK METRICS - DIAGNOSTICS")
    print("=" * 70)

    print("\n1️⃣ Fetching worst 5 SPs (7-day window)...")
    worst_7d = get_worst_sp_cashflows(days=7, limit=5)

    if worst_7d.empty:
        print("   ⚠️ No BM activity data found for last 7 days")
    else:
        print(f"   ✅ Found {len(worst_7d)} settlement periods with losses")
        print("\n   Worst 5 SP Losses (7d):")
        for i, row in worst_7d.iterrows():
            print(f"      {i+1}. {format_sp_loss_line(row)}")
            print(f"         Acceptances: {int(row['acceptance_count'])}, SSP: £{row['ssp']:.2f}/MWh")

    print("\n2️⃣ Fetching worst 5 SPs (30-day window)...")
    worst_30d = get_worst_sp_cashflows(days=30, limit=5)

    if worst_30d.empty:
        print("   ⚠️ No BM activity data found for last 30 days")
    else:
        print(f"   ✅ Found {len(worst_30d)} settlement periods with losses")
        print("\n   Worst 5 SP Losses (30d):")
        for i, row in worst_30d.iterrows():
            print(f"      {i+1}. {format_sp_loss_line(row)}")
            print(f"         Acceptances: {int(row['acceptance_count'])}, SSP: £{row['ssp']:.2f}/MWh")

        print(f"\n   📊 30-day worst single SP: {format_sp_loss_line(worst_30d.iloc[0])}")

    print("\n" + "=" * 70)
    print("💡 NOTES:")
    print("   - Net cashflow currently = acceptance revenue only")
    print("   - Imbalance charges not yet included (requires position modeling)")
    print("   - Negative values indicate BM activity cost > revenue")
    print("   - Use '--diagnostics-only' flag to run without updating sheets")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Add worst 5 SP risk metrics to dashboard')
    parser.add_argument('--diagnostics-only', action='store_true',
                       help='Run diagnostics without updating Google Sheets')
    args = parser.parse_args()

    if args.diagnostics_only:
        run_diagnostics_only()
    else:
        print("⚡ ADDING WORST 5 SP RISK METRICS TO DASHBOARD")
        print("=" * 70)

        print("\n📊 Calculating worst SPs...")
        worst_7d = get_worst_sp_cashflows(days=7, limit=5)
        worst_30d = get_worst_sp_cashflows(days=30, limit=5)

        if worst_7d.empty and worst_30d.empty:
            print("❌ No BM activity data found. Cannot update dashboard.")
            return

        print(f"   ✅ 7d: {len(worst_7d)} worst SPs")
        print(f"   ✅ 30d: {len(worst_30d)} worst SPs")

        update_dashboard(worst_7d, worst_30d)

        print("\n✅ Complete. Run with --diagnostics-only for detailed analysis.")


if __name__ == "__main__":
    main()
