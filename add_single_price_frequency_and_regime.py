#!/usr/bin/env python3
"""
add_single_price_frequency_and_regime.py

Adds two critical trader KPIs to Live Dashboard v2:
1. Single-Price Frequency (% SPs where SSP=SBP over 30d)
2. Price Regime Classification (Low/Normal/High/Scarcity)

Addresses diagnostic findings from COMPREHENSIVE_FUNCTIONALITY_DIAGNOSTIC.py

Created: December 29, 2025
"""

import gspread
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

def get_single_price_frequency():
    """
    Calculate % of settlement periods where SSP = SBP (single pricing)
    Since Nov 2015 P305: SSP=SBP for ALL periods (single imbalance price)

    Returns: (frequency_pct, periods_checked, notes)
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    SELECT
        COUNT(*) as total_periods,
        COUNT(CASE WHEN systemSellPrice = systemBuyPrice THEN 1 END) as single_price_periods,
        MIN(settlementDate) as earliest_date,
        MAX(settlementDate) as latest_date
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        AND settlementDate < CURRENT_DATE()  -- Exclude today (incomplete)
        AND systemSellPrice IS NOT NULL
        AND systemBuyPrice IS NOT NULL
    """

    try:
        df = client.query(query).to_dataframe()

        if df.empty or df.iloc[0]['total_periods'] == 0:
            return 100.0, 0, "No data available (P305: single pricing since Nov 2015)"

        row = df.iloc[0]
        frequency_pct = (row['single_price_periods'] / row['total_periods']) * 100

        # Note: Since P305 (Nov 2015), SSP=SBP for all periods
        # Frequency should be ~100%, but historical data may have dual pricing
        if frequency_pct > 99.5:
            note = "Single pricing (P305 since Nov 2015)"
        elif frequency_pct > 95:
            note = f"Mostly single pricing ({frequency_pct:.1f}%)"
        else:
            note = f"Mixed pricing detected ({frequency_pct:.1f}%)"

        return frequency_pct, int(row['total_periods']), note

    except Exception as e:
        return 100.0, 0, f"Query error: {str(e)[:50]}"


def get_current_price_regime():
    """
    Classify current imbalance price into regime bands:
    - Low: < £20/MWh
    - Normal: £20-80/MWh
    - High: £80-150/MWh
    - Scarcity: > £150/MWh

    Returns: (regime_name, price, color_code)
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Get most recent imbalance price
    query = f"""
    SELECT
        systemSellPrice as price,
        settlementDate,
        settlementPeriod
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
    """

    try:
        df = client.query(query).to_dataframe()

        if df.empty:
            return "Unknown", 0.0, "#808080"

        price = float(df.iloc[0]['price'])

        # Classify regime
        if price < 20:
            regime = "Low"
            color = "#90EE90"  # Light green
        elif price < 80:
            regime = "Normal"
            color = "#87CEEB"  # Sky blue
        elif price < 150:
            regime = "High"
            color = "#FFD700"  # Gold
        else:
            regime = "Scarcity"
            color = "#FF6347"  # Tomato red

        return regime, price, color

    except Exception as e:
        return "Error", 0.0, "#808080"


def get_regime_distribution_30d():
    """
    Calculate % of time in each regime over last 30 days
    Returns: dict with regime: percentage
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")

    query = f"""
    WITH regimes AS (
        SELECT
            CASE
                WHEN systemSellPrice < 20 THEN 'Low'
                WHEN systemSellPrice < 80 THEN 'Normal'
                WHEN systemSellPrice < 150 THEN 'High'
                ELSE 'Scarcity'
            END as regime,
            COUNT(*) as count
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            AND settlementDate < CURRENT_DATE()
            AND systemSellPrice IS NOT NULL
        GROUP BY regime
    )
    SELECT
        regime,
        count,
        count * 100.0 / SUM(count) OVER () as percentage
    FROM regimes
    ORDER BY
        CASE regime
            WHEN 'Low' THEN 1
            WHEN 'Normal' THEN 2
            WHEN 'High' THEN 3
            WHEN 'Scarcity' THEN 4
        END
    """

    try:
        df = client.query(query).to_dataframe()

        if df.empty:
            return {"Low": 0, "Normal": 0, "High": 0, "Scarcity": 0}

        distribution = {row['regime']: row['percentage'] for _, row in df.iterrows()}

        # Ensure all regimes present
        for regime in ['Low', 'Normal', 'High', 'Scarcity']:
            if regime not in distribution:
                distribution[regime] = 0.0

        return distribution

    except Exception as e:
        return {"Low": 0, "Normal": 0, "High": 0, "Scarcity": 0}


def update_dashboard():
    """
    Update Live Dashboard v2 with single-price frequency and price regime
    """
    print("\n" + "=" * 80)
    print("⚡ ADDING SINGLE-PRICE FREQUENCY & PRICE REGIME TO DASHBOARD")
    print("=" * 80)

    # Calculate metrics
    print("\n📊 Calculating metrics...")

    sp_freq, periods, sp_note = get_single_price_frequency()
    print(f"   Single-Price Frequency: {sp_freq:.1f}% ({periods:,} periods, {sp_note})")

    regime_name, price, color = get_current_price_regime()
    print(f"   Current Price Regime: {regime_name} (£{price:.2f}/MWh)")

    distribution = get_regime_distribution_30d()
    print(f"\n   30-Day Regime Distribution:")
    for regime, pct in distribution.items():
        print(f"      {regime:10}: {pct:>5.1f}%")

    # Connect to Google Sheets
    print("\n🔗 Connecting to Google Sheets...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    gc = gspread.authorize(creds)

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)

    # Insert new KPI rows after K23 (Price Regime row from conversation)
    # New rows: K24-K26 for single-price freq and regime distribution

    print("\n📝 Updating dashboard cells...")

    updates = [
        # Single-Price Frequency (new row K24)
        {
            'range': 'K24',
            'values': [['Single-Price Frequency']]
        },
        {
            'range': 'L24',
            'values': [[f'{sp_freq:.1f}%']]
        },
        {
            'range': 'M24',
            'values': [[sp_note]]
        },

        # Price Regime Distribution (new row K25)
        {
            'range': 'K25',
            'values': [['Regime Distribution (30d)']]
        },
        {
            'range': 'L25',
            'values': [[f"Low: {distribution['Low']:.0f}% | Normal: {distribution['Normal']:.0f}% | High: {distribution['High']:.0f}% | Scarcity: {distribution['Scarcity']:.0f}%"]]
        },
        {
            'range': 'M25',
            'values': [['30-day breakdown']]
        },

        # Update existing Price Regime row (K23) with current value
        {
            'range': 'L23',
            'values': [[f'{regime_name} (£{price:.2f}/MWh)']]
        }
    ]

    sheet.batch_update(updates)

    # Apply conditional formatting to regime cell (L23) based on color
    # Note: Color formatting requires more complex API calls, documented separately

    print("\n✅ Dashboard updated successfully!")
    print(f"   K24: Single-Price Frequency: {sp_freq:.1f}%")
    print(f"   K25: Regime Distribution added")
    print(f"   L23: Current Regime: {regime_name} (£{price:.2f}/MWh)")

    print("\n💡 Next Steps:")
    print("   1. Apply conditional formatting to L23 cell:")
    print(f"      - Format → Conditional formatting → Custom formula")
    print(f"      - Use color: {color} for {regime_name} regime")
    print("   2. Add sparkline to M24 showing 30d single-price trend (optional)")
    print("   3. Consider adding regime heatmap (hour × day grid)")

    return sp_freq, regime_name, distribution


if __name__ == "__main__":
    update_dashboard()
    print("\n✅ Complete!")
