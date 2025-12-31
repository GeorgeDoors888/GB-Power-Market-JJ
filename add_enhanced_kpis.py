#!/usr/bin/env python3
"""
Enhanced KPIs for Live Dashboard v2
Adds Battery, CHP, and Risk metrics for trader decision-making
"""

from google.cloud import bigquery
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import numpy as np

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

def get_battery_kpis(bq_client):
    """Calculate battery-specific KPIs"""

    print("\n🔋 Calculating Battery KPIs...")

    # Arbitrage Capture % (last 24h)
    sql = f"""
    WITH prices AS (
      SELECT
        settlementDate,
        settlementPeriod,
        systemSellPrice as sip
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    ),
    arbitrage AS (
      SELECT
        MAX(sip) - MIN(sip) as max_spread,
        AVG(sip) as avg_price
      FROM prices
    )
    SELECT
      max_spread,
      avg_price,
      max_spread / NULLIF(avg_price, 0) * 100 as capture_potential_pct
    FROM arbitrage
    """

    result = list(bq_client.query(sql).result())
    if result:
        row = result[0]
        capture_pct = min(row.capture_potential_pct or 0, 100)  # Cap at 100%
    else:
        capture_pct = 0

    # Marginal Value (value of next MWh discharge at current price)
    sql = f"""
    SELECT
      systemSellPrice as current_sip,
      systemSellPrice * 1.0 as marginal_value_gbp
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    ORDER BY settlementDate DESC, settlementPeriod DESC
    LIMIT 1
    """

    result = list(bq_client.query(sql).result())
    marginal_value = result[0].marginal_value_gbp if result else 0

    # Cycle Value (£/MWh accounting for degradation - simplified)
    # Assume 0.02% degradation per cycle, 10-year lifespan, £150k/MWh battery cost
    degradation_cost_per_mwh = 150000 * 0.0002  # £30/MWh
    cycle_value = marginal_value - degradation_cost_per_mwh if marginal_value > 0 else 0

    return {
        'arbitrage_capture_pct': round(capture_pct, 1),
        'marginal_value_gbp': round(marginal_value, 2),
        'cycle_value_gbp_mwh': round(cycle_value, 2)
    }

def get_chp_kpis(bq_client):
    """Calculate CHP (Combined Heat & Power) KPIs"""

    print("\n🔥 Calculating CHP KPIs...")

    # Spark Spread (power price - gas price - carbon cost)
    # Simplified: assume gas at £80/MWh, carbon at £30/tonne, 0.4 tonnes CO2/MWh
    sql = f"""
    SELECT
      AVG(systemSellPrice) as avg_power_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    """

    result = list(bq_client.query(sql).result())
    power_price = result[0].avg_power_price if result else 0

    gas_price = 80  # £/MWh (example)
    carbon_cost = 30 * 0.4  # £30/tonne * 0.4 tonnes/MWh = £12/MWh
    spark_spread = power_price - gas_price - carbon_cost

    # Heat Constraint Index (simplified - would need heat demand data)
    # Placeholder: assume 20% of time heat-limited in winter
    heat_constraint_index = 20.0  # %

    return {
        'spark_spread_gbp_mwh': round(spark_spread, 2),
        'heat_constraint_index_pct': round(heat_constraint_index, 1)
    }

def get_risk_kpis(bq_client):
    """Calculate risk management KPIs"""

    print("\n⚠️  Calculating Risk KPIs...")

    # Worst 5 Settlement Periods (today)
    sql = f"""
    SELECT
      settlementPeriod,
      systemSellPrice as sip,
      RANK() OVER (ORDER BY systemSellPrice DESC) as price_rank
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate = CURRENT_DATE()
    ORDER BY systemSellPrice DESC
    LIMIT 5
    """

    result = list(bq_client.query(sql).result())
    worst_5_periods = [f"SP{row.settlementPeriod}:£{row.sip:.0f}" for row in result]
    worst_5_str = ", ".join(worst_5_periods) if worst_5_periods else "N/A"

    # Imbalance Tail Exposure (VaR 99% - 99th percentile price)
    sql = f"""
    SELECT
      APPROX_QUANTILES(systemSellPrice, 100)[OFFSET(99)] as var_99,
      APPROX_QUANTILES(systemSellPrice, 100)[OFFSET(95)] as var_95,
      AVG(systemSellPrice) as avg_price
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
    """

    result = list(bq_client.query(sql).result())
    if result:
        var_99 = result[0].var_99 or 0
        var_95 = result[0].var_95 or 0
    else:
        var_99 = 0
        var_95 = 0

    # Missed Delivery Count (MEL/MIL violations - placeholder)
    # Would need to compare FPN vs actual generation
    missed_delivery_count = 0  # Placeholder

    return {
        'worst_5_periods': worst_5_str,
        'tail_risk_var99_gbp_mwh': round(var_99, 2),
        'tail_risk_var95_gbp_mwh': round(var_95, 2),
        'missed_delivery_count': missed_delivery_count
    }

def add_kpis_to_dashboard(sheets_client, battery_kpis, chp_kpis, risk_kpis):
    """Add new KPIs to dashboard"""

    print("\n📊 Adding KPIs to dashboard...")

    spreadsheet = sheets_client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(SHEET_NAME)

    # Add new KPIs starting at row 31 (after existing KPIs and notes)
    new_kpis = [
        [""],  # Spacing
        ["🔋 BATTERY METRICS"],
        ["📈 Arbitrage Capture %", f"{battery_kpis['arbitrage_capture_pct']}%"],
        ["💰 Marginal Value (£/MWh)", f"£{battery_kpis['marginal_value_gbp']:.2f}"],
        ["🔄 Cycle Value (£/MWh)", f"£{battery_kpis['cycle_value_gbp_mwh']:.2f}"],
        [""],
        ["🔥 CHP METRICS"],
        ["⚡ Spark Spread (£/MWh)", f"£{chp_kpis['spark_spread_gbp_mwh']:.2f}"],
        ["🌡️ Heat Constraint Index", f"{chp_kpis['heat_constraint_index_pct']}%"],
        [""],
        ["⚠️ RISK METRICS"],
        ["🔺 Worst 5 Periods Today", risk_kpis['worst_5_periods']],
        ["📊 Tail Risk (VaR 99%)", f"£{risk_kpis['tail_risk_var99_gbp_mwh']:.2f}/MWh"],
        ["📉 Tail Risk (VaR 95%)", f"£{risk_kpis['tail_risk_var95_gbp_mwh']:.2f}/MWh"],
        ["❌ Missed Deliveries", risk_kpis['missed_delivery_count']],
    ]

    # Write to sheet
    sheet.update('K31:L45', new_kpis, value_input_option='USER_ENTERED')

    # Format section headers
    sheet.format('K32', {  # Battery header
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.0}
    })

    sheet.format('K38', {  # CHP header
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 1.0, 'green': 0.6, 'blue': 0.2}
    })

    sheet.format('K42', {  # Risk header
        'textFormat': {'bold': True, 'fontSize': 11},
        'backgroundColor': {'red': 1.0, 'green': 0.3, 'blue': 0.3}
    })

    print(f"✅ Added {len(new_kpis)} rows of KPIs")

def main():
    print("="*80)
    print("ENHANCED KPIs: BATTERY, CHP, AND RISK METRICS")
    print("="*80)

    # Connect to BigQuery
    print(f"\n🔗 Connecting to BigQuery: {PROJECT_ID}.{DATASET}")
    bq_client = bigquery.Client(project=PROJECT_ID, location="US")

    # Calculate KPIs
    battery_kpis = get_battery_kpis(bq_client)
    chp_kpis = get_chp_kpis(bq_client)
    risk_kpis = get_risk_kpis(bq_client)

    # Display results
    print("\n" + "="*80)
    print("CALCULATED KPIs")
    print("="*80)

    print("\n🔋 Battery Metrics:")
    print(f"  Arbitrage Capture: {battery_kpis['arbitrage_capture_pct']}%")
    print(f"  Marginal Value: £{battery_kpis['marginal_value_gbp']:.2f}/MWh")
    print(f"  Cycle Value: £{battery_kpis['cycle_value_gbp_mwh']:.2f}/MWh")

    print("\n🔥 CHP Metrics:")
    print(f"  Spark Spread: £{chp_kpis['spark_spread_gbp_mwh']:.2f}/MWh")
    print(f"  Heat Constraint Index: {chp_kpis['heat_constraint_index_pct']}%")

    print("\n⚠️ Risk Metrics:")
    print(f"  Worst 5 Periods: {risk_kpis['worst_5_periods']}")
    print(f"  Tail Risk (VaR 99%): £{risk_kpis['tail_risk_var99_gbp_mwh']:.2f}/MWh")
    print(f"  Tail Risk (VaR 95%): £{risk_kpis['tail_risk_var95_gbp_mwh']:.2f}/MWh")
    print(f"  Missed Deliveries: {risk_kpis['missed_delivery_count']}")

    # Connect to Google Sheets
    print(f"\n🔗 Connecting to Google Sheets: {SPREADSHEET_ID}")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    sheets_client = gspread.authorize(creds)

    # Add to dashboard
    add_kpis_to_dashboard(sheets_client, battery_kpis, chp_kpis, risk_kpis)

    print("\n" + "="*80)
    print("✅ ENHANCED KPIs ADDED TO DASHBOARD")
    print("="*80)
    print(f"Dashboard URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

if __name__ == "__main__":
    main()
