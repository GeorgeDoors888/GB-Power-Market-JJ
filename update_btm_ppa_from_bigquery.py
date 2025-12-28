#!/usr/bin/env python3
"""
Update BtM PPA + BM/VLP revenue KPIs in Google Sheets from BigQuery.

Uses BigQuery views:
    - v_bm_system_direction_classified
    - v_curtailment_revenue_daily
    - v_system_prices_sp
    - bmrs_costs (for real system prices)
    - bmrs_boalf (for BM acceptances)

Writes to:
    - 'BESS' sheet (detailed breakdown)
    - 'Dashboard' sheet (headline KPIs)
"""

import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"

# BMU(s) for your VLP/BESS unit(s)
VLP_BM_UNITS = ["2__FBPGM001", "2__FBPGM002"]  # Flexgen battery units
SITE_DEMAND_MW = 2.5  # Constant 2.5 MW assumption

# BESS Configuration
BESS_CAPACITY_MWH = 5.0
BESS_POWER_MW = 2.5
BESS_EFFICIENCY = 0.85
MAX_CYCLES_PER_DAY = 4

# PPA Price
PPA_PRICE = 150.0  # £/MWh

# Fixed Levy Rates (£/MWh)
TNUOS_RATE = 12.50
BSUOS_RATE = 4.50
CCL_RATE = 7.75
RO_RATE = 61.90
FIT_RATE = 11.50
TOTAL_LEVIES = TNUOS_RATE + BSUOS_RATE + CCL_RATE + RO_RATE + FIT_RATE  # £98.15/MWh

# DUoS Rates (£/MWh)
DUOS_RED = 17.64
DUOS_AMBER = 2.05
DUOS_GREEN = 0.11

# VLP Revenue (realistic)
VLP_AVG_UPLIFT = 12.0  # £/MWh (reduced from £15)
VLP_PARTICIPATION_RATE = 0.20

# Dynamic Containment Revenue (separate from BtM PPA)
DC_ANNUAL_REVENUE = 195458  # £/year from frequency response services

# Analysis period (last 6 months)
ANALYSIS_DAYS = 180

# -------------------------------------------------------------------
# AUTH
# -------------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES,
)

gc = gspread.authorize(creds)

bq_creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/bigquery"],
)
bq_client = bigquery.Client(
    project=PROJECT_ID,
    credentials=bq_creds,
    location="US",
)

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def query_bigquery(sql: str) -> pd.DataFrame:
    """Execute BigQuery SQL and return DataFrame"""
    job = bq_client.query(sql)
    return job.to_dataframe()


def format_gbp(value: float) -> str:
    """Format as £X,XXX"""
    return f"£{value:,.0f}"


def format_mwh(value: float) -> str:
    """Format as X,XXX MWh"""
    return f"{value:,.0f} MWh"


def get_duos_band(sp: int, is_weekday: bool) -> tuple:
    """Return DUoS band and rate for given settlement period"""
    # RED: SP 33-39 (16:00-19:30) weekdays only
    if is_weekday and 33 <= sp <= 39:
        return 'red', DUOS_RED
    # AMBER: SP 17-32, 40-44 (08:00-16:00, 19:30-22:00) weekdays only
    elif is_weekday and ((17 <= sp <= 32) or (40 <= sp <= 44)):
        return 'amber', DUOS_AMBER
    # GREEN: All other times
    else:
        return 'green', DUOS_GREEN


# -------------------------------------------------------------------
# 1. GET REAL SYSTEM PRICES FROM BIGQUERY
# -------------------------------------------------------------------

def get_system_prices_by_band():
    """Get average system buy prices by DUoS band from last 6 months"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=ANALYSIS_DAYS)
    
    sql = f"""
    WITH prices_with_band AS (
      SELECT
        settlementDate,
        settlementPeriod,
        systemBuyPrice,
        EXTRACT(DAYOFWEEK FROM settlementDate) AS dow,
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) BETWEEN 2 AND 6
               AND settlementPeriod BETWEEN 33 AND 39
            THEN 'red'
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) BETWEEN 2 AND 6
               AND ((settlementPeriod BETWEEN 17 AND 32) OR (settlementPeriod BETWEEN 40 AND 44))
            THEN 'amber'
          ELSE 'green'
        END AS duos_band
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      WHERE settlementDate >= '{start_date}'
        AND settlementDate <= '{end_date}'
        AND systemBuyPrice IS NOT NULL
    )
    SELECT
      duos_band,
      AVG(systemBuyPrice) AS avg_sbp,
      MIN(systemBuyPrice) AS min_sbp,
      MAX(systemBuyPrice) AS max_sbp,
      COUNT(*) AS periods
    FROM prices_with_band
    GROUP BY duos_band
    ORDER BY duos_band
    """
    
    df = query_bigquery(sql)
    
    if df.empty:
        # Fallback to defaults
        return {
            'green': 40.0,
            'amber': 50.0,
            'red': 80.0
        }
    
    prices = {}
    for _, row in df.iterrows():
        prices[row['duos_band']] = row['avg_sbp']
    
    return prices


# -------------------------------------------------------------------
# 2. GET CURTAILMENT REVENUE (VLP/BM)
# -------------------------------------------------------------------

def get_curtailment_annual():
    """Get curtailment revenue from BM acceptances"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=ANALYSIS_DAYS)
    
    # First try the view
    sql_view = f"""
    SELECT
      SUM(curtailment_mwh) AS total_curtailment_mwh,
      SUM(curtailment_revenue_gbp) AS total_curtailment_revenue_gbp,
      SUM(generation_add_mwh) AS generation_add_mwh,
      SUM(generation_add_revenue_gbp) AS generation_add_revenue_gbp,
      SUM(total_bm_mwh) AS total_bm_mwh,
      SUM(total_bm_revenue_gbp) AS total_bm_revenue_gbp
    FROM `{PROJECT_ID}.{DATASET}.v_curtailment_revenue_daily`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
      AND bmUnit IN UNNEST(@bmus)
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("bmus", "STRING", VLP_BM_UNITS)
        ]
    )
    
    try:
        df = bq_client.query(sql_view, job_config=job_config).to_dataframe()
        
        if not df.empty:
            row = df.iloc[0]
            # Annualize from analysis period
            factor = 365.25 / ANALYSIS_DAYS
            return {
                "curtailment_mwh": row["total_curtailment_mwh"] * factor if pd.notna(row["total_curtailment_mwh"]) else 0,
                "curtailment_revenue": row["total_curtailment_revenue_gbp"] * factor if pd.notna(row["total_curtailment_revenue_gbp"]) else 0,
                "generation_add_mwh": row["generation_add_mwh"] * factor if pd.notna(row["generation_add_mwh"]) else 0,
                "generation_add_revenue": row["generation_add_revenue_gbp"] * factor if pd.notna(row["generation_add_revenue_gbp"]) else 0,
                "total_bm_mwh": row["total_bm_mwh"] * factor if pd.notna(row["total_bm_mwh"]) else 0,
                "total_bm_revenue": row["total_bm_revenue_gbp"] * factor if pd.notna(row["total_bm_revenue_gbp"]) else 0,
            }
    except Exception as e:
        print(f"⚠️  View query failed: {e}")
    
    # Fallback: direct query on bmrs_boalf
    sql_direct = f"""
    SELECT
      SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 ELSE 0 END) AS curtailment_mwh,
      SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 * acceptancePrice ELSE 0 END) AS curtailment_revenue,
      SUM(CASE WHEN bidOfferFlag = 'O' THEN (levelTo - levelFrom) * 0.5 ELSE 0 END) AS generation_add_mwh,
      SUM(CASE WHEN bidOfferFlag = 'O' THEN (levelTo - levelFrom) * 0.5 * acceptancePrice ELSE 0 END) AS generation_add_revenue,
      SUM((levelTo - levelFrom) * 0.5) AS total_bm_mwh,
      SUM((levelTo - levelFrom) * 0.5 * acceptancePrice) AS total_bm_revenue
    FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
      AND bmUnit IN UNNEST(@bmus)
    """
    
    df = bq_client.query(sql_direct, job_config=job_config).to_dataframe()
    
    if df.empty:
        return {
            "curtailment_mwh": 0,
            "curtailment_revenue": 0,
            "generation_add_mwh": 0,
            "generation_add_revenue": 0,
            "total_bm_mwh": 0,
            "total_bm_revenue": 0,
        }
    
    row = df.iloc[0]
    factor = 365.25 / ANALYSIS_DAYS
    return {
        "curtailment_mwh": row["curtailment_mwh"] * factor if pd.notna(row["curtailment_mwh"]) else 0,
        "curtailment_revenue": row["curtailment_revenue"] * factor if pd.notna(row["curtailment_revenue"]) else 0,
        "generation_add_mwh": row["generation_add_mwh"] * factor if pd.notna(row["generation_add_mwh"]) else 0,
        "generation_add_revenue": row["generation_add_revenue"] * factor if pd.notna(row["generation_add_revenue"]) else 0,
        "total_bm_mwh": row["total_bm_mwh"] * factor if pd.notna(row["total_bm_mwh"]) else 0,
        "total_bm_revenue": row["total_bm_revenue"] * factor if pd.notna(row["total_bm_revenue"]) else 0,
    }


# -------------------------------------------------------------------
# 3. CALCULATE BTM PPA REVENUE (WITH REAL PRICES)
# -------------------------------------------------------------------

def calculate_btm_ppa_revenue(system_prices):
    """Calculate BtM PPA revenue using real system prices"""
    
    # Annual hours by band
    # Weekdays: 260, Weekends: 105 (approximate)
    weekday_hours = 260 * 24
    weekend_hours = 105 * 24
    
    # RED: SP 33-39 = 7 SPs × 0.5h = 3.5h/day × 260 weekdays
    red_periods = 7 * 260
    red_hours = red_periods * 0.5
    
    # AMBER: SP 17-32 (16 SPs) + SP 40-44 (5 SPs) = 21 SPs × 0.5h × 260 weekdays
    amber_periods = 21 * 260
    amber_hours = amber_periods * 0.5
    
    # GREEN: All remaining
    total_periods = 365.25 * 48
    green_periods = total_periods - red_periods - amber_periods
    green_hours = green_periods * 0.5
    
    # Get real prices
    green_sbp = system_prices.get('green', 40.0)
    amber_sbp = system_prices.get('amber', 50.0)
    red_sbp = system_prices.get('red', 80.0)
    
    print(f"\n📊 System Buy Prices (from BigQuery, last {ANALYSIS_DAYS} days):")
    print(f"   🟢 Green: £{green_sbp:.2f}/MWh")
    print(f"   🟡 Amber: £{amber_sbp:.2f}/MWh")
    print(f"   🔴 Red:   £{red_sbp:.2f}/MWh")
    
    # Calculate costs per band
    green_cost = green_sbp + DUOS_GREEN + TOTAL_LEVIES
    amber_cost = amber_sbp + DUOS_AMBER + TOTAL_LEVIES
    red_cost = red_sbp + DUOS_RED + TOTAL_LEVIES
    
    # Battery charging strategy: charge during GREEN (cheapest)
    charging_threshold = PPA_PRICE - 30  # £120/MWh threshold
    
    # Determine charging volumes
    can_charge_green = green_cost < charging_threshold
    can_charge_amber = amber_cost < charging_threshold
    
    # Max annual charging cycles
    max_cycles_year = MAX_CYCLES_PER_DAY * 365.25
    max_charge_mwh_year = max_cycles_year * BESS_CAPACITY_MWH
    
    # Prioritize GREEN charging
    if can_charge_green:
        green_available_mwh = green_hours * BESS_POWER_MW
        green_charge_mwh = min(green_available_mwh, max_charge_mwh_year)
        remaining_capacity = max_charge_mwh_year - green_charge_mwh
    else:
        green_charge_mwh = 0
        remaining_capacity = max_charge_mwh_year
    
    # Then AMBER if needed and economic
    if can_charge_amber and remaining_capacity > 0:
        amber_available_mwh = amber_hours * BESS_POWER_MW
        amber_charge_mwh = min(amber_available_mwh, remaining_capacity)
    else:
        amber_charge_mwh = 0
    
    # Never charge during RED
    red_charge_mwh = 0
    
    total_charged_mwh = green_charge_mwh + amber_charge_mwh + red_charge_mwh
    total_discharged_mwh = total_charged_mwh * BESS_EFFICIENCY
    
    # Charging costs
    green_charging_cost = green_charge_mwh * green_cost
    amber_charging_cost = amber_charge_mwh * amber_cost
    total_charging_cost = green_charging_cost + amber_charging_cost
    
    # Battery discharge revenue (assume RED first, then AMBER)
    red_demand_mwh = red_hours * SITE_DEMAND_MW
    amber_demand_mwh = amber_hours * SITE_DEMAND_MW
    green_demand_mwh = green_hours * SITE_DEMAND_MW
    
    # Battery can serve 100% of RED demand (corrected)
    battery_capacity_annual = total_discharged_mwh
    
    if battery_capacity_annual >= red_demand_mwh:
        battery_red_mwh = red_demand_mwh  # 100% coverage
        battery_amber_mwh = min(amber_demand_mwh, battery_capacity_annual - battery_red_mwh)
    else:
        battery_red_mwh = battery_capacity_annual  # Less than 100%
        battery_amber_mwh = 0
    
    battery_green_mwh = 0  # Never discharge during green (import is profitable)
    
    total_battery_discharge = battery_red_mwh + battery_amber_mwh
    
    # VLP revenue (realistic £12/MWh)
    vlp_revenue = total_battery_discharge * VLP_PARTICIPATION_RATE * VLP_AVG_UPLIFT
    
    # Stream 2: Battery + VLP
    stream2_ppa_revenue = total_battery_discharge * PPA_PRICE
    stream2_total_revenue = stream2_ppa_revenue + vlp_revenue
    stream2_profit = stream2_total_revenue - total_charging_cost
    
    # Stream 1: Direct import (ONLY when cost < PPA price of £150)
    stream1_red_mwh = red_demand_mwh - battery_red_mwh
    stream1_amber_mwh = amber_demand_mwh - battery_amber_mwh
    stream1_green_mwh = green_demand_mwh  # All green is direct import
    
    # Only count profitable imports (cost < £150)
    stream1_red_profitable = red_cost < PPA_PRICE
    stream1_amber_profitable = amber_cost < PPA_PRICE
    stream1_green_profitable = green_cost < PPA_PRICE
    
    # Calculate revenue only for profitable periods
    if stream1_green_profitable:
        stream1_green_revenue = stream1_green_mwh * PPA_PRICE
        stream1_green_cost = stream1_green_mwh * green_cost
        stream1_green_profit = stream1_green_revenue - stream1_green_cost
    else:
        stream1_green_mwh = 0
        stream1_green_revenue = 0
        stream1_green_cost = 0
        stream1_green_profit = 0
    
    if stream1_amber_profitable:
        stream1_amber_revenue = stream1_amber_mwh * PPA_PRICE
        stream1_amber_cost = stream1_amber_mwh * amber_cost
        stream1_amber_profit = stream1_amber_revenue - stream1_amber_cost
    else:
        stream1_amber_mwh = 0
        stream1_amber_revenue = 0
        stream1_amber_cost = 0
        stream1_amber_profit = 0
    
    # Red is NEVER profitable at £209/MWh cost vs £150 PPA
    stream1_red_mwh = 0
    stream1_red_revenue = 0
    stream1_red_cost = 0
    stream1_red_profit = 0
    
    stream1_total_mwh = stream1_red_mwh + stream1_amber_mwh + stream1_green_mwh
    stream1_total_revenue = stream1_red_revenue + stream1_amber_revenue + stream1_green_revenue
    stream1_total_cost = stream1_red_cost + stream1_amber_cost + stream1_green_cost
    stream1_profit = stream1_total_revenue - stream1_total_cost
    
    # Combined (BtM PPA only)
    btm_ppa_profit = stream1_profit + stream2_profit
    
    # Add Dynamic Containment revenue (separate service)
    total_profit = btm_ppa_profit + DC_ANNUAL_REVENUE
    
    # Cycles
    actual_cycles = total_charged_mwh / BESS_CAPACITY_MWH if BESS_CAPACITY_MWH > 0 else 0
    
    return {
        "system_prices": {
            "green": green_sbp,
            "amber": amber_sbp,
            "red": red_sbp,
        },
        "costs_per_band": {
            "green": green_cost,
            "amber": amber_cost,
            "red": red_cost,
        },
        "stream2": {
            "charged_mwh": total_charged_mwh,
            "green_charge": green_charge_mwh,
            "amber_charge": amber_charge_mwh,
            "red_charge": red_charge_mwh,
            "discharged_mwh": total_battery_discharge,
            "red_discharge": battery_red_mwh,
            "amber_discharge": battery_amber_mwh,
            "charging_cost": total_charging_cost,
            "ppa_revenue": stream2_ppa_revenue,
            "vlp_revenue": vlp_revenue,
            "total_revenue": stream2_total_revenue,
            "profit": stream2_profit,
            "cycles": actual_cycles,
        },
        "stream1": {
            "total_mwh": stream1_total_mwh,
            "red_mwh": stream1_red_mwh,
            "amber_mwh": stream1_amber_mwh,
            "green_mwh": stream1_green_mwh,
            "total_revenue": stream1_total_revenue,
            "total_cost": stream1_total_cost,
            "profit": stream1_profit,
            "red_profit": stream1_red_profit,
            "amber_profit": stream1_amber_profit,
            "green_profit": stream1_green_profit,
        },
        "btm_ppa_profit": btm_ppa_profit,
        "total_profit": total_profit,
        "red_coverage": (battery_red_mwh / red_demand_mwh * 100) if red_demand_mwh > 0 else 0,
    }


# -------------------------------------------------------------------
# 4. UPDATE SHEETS
# -------------------------------------------------------------------

def update_bess_sheet(btm_results, curtail):
    """Write detailed results to BESS sheet"""
    ss = gc.open_by_key(SPREADSHEET_ID)
    bess_ws = ss.worksheet("BESS")
    
    s2 = btm_results["stream2"]
    s1 = btm_results["stream1"]
    
    # Battery charging breakdown (E28-H30)
    charging_data = [
        [s2["red_charge"], f"£{s2['red_charge'] * btm_results['costs_per_band']['red']:,.2f}"],
        [s2["amber_charge"], f"£{s2['amber_charge'] * btm_results['costs_per_band']['amber']:,.2f}"],
        [s2["green_charge"], f"£{s2['green_charge'] * btm_results['costs_per_band']['green']:,.2f}"],
    ]
    bess_ws.update("E28:F30", charging_data)
    
    # Discharge summary (F45-H45)
    discharge_summary = [[
        s2["discharged_mwh"],
        f"£{s2['ppa_revenue']:,.0f}",
        f"£{s2['vlp_revenue']:,.0f}"
    ]]
    bess_ws.update("F45:H45", discharge_summary)
    
    # Curtailment summary (A60-B67)
    curtail_data = [
        ["Curtailment Summary (ESO Taking Generation Off)", ""],
        ["Total Curtailment MWh", format_mwh(curtail["curtailment_mwh"])],
        ["Total Curtailment Revenue", format_gbp(curtail["curtailment_revenue"])],
        ["Generation Addition MWh", format_mwh(curtail["generation_add_mwh"])],
        ["Generation Addition Revenue", format_gbp(curtail["generation_add_revenue"])],
        ["Total BM MWh", format_mwh(curtail["total_bm_mwh"])],
        ["Total BM Revenue", format_gbp(curtail["total_bm_revenue"])]
    ]
    bess_ws.update("A60:B66", curtail_data)
    
    print("✅ BESS sheet updated")


def update_dashboard_sheet(btm_results, curtail):
    """Write KPIs to Dashboard sheet"""
    ss = gc.open_by_key(SPREADSHEET_ID)
    dash = ss.worksheet("Dashboard")
    
    # Row 7: BtM PPA Profit KPI
    total_profit = btm_results["total_profit"]
    s1 = btm_results["stream1"]
    s2 = btm_results["stream2"]
    
    ppa_kpi = [[
        "💰 BtM PPA PROFIT",
        "Total Revenue",
        format_gbp(s1["total_revenue"] + s2["total_revenue"]),
        "Total Costs",
        format_gbp(s1["total_cost"] + s2["charging_cost"]),
        "Net Profit",
        format_gbp(total_profit),
        "RED Coverage",
        f"{btm_results['red_coverage']:.0f}%"
    ]]
    dash.update("A7:I7", ppa_kpi)
    
    # Row 8: Curtailment Revenue KPI
    curtail_kpi = [[
        "⚡ CURTAILMENT REVENUE",
        "Curtailment MWh",
        format_mwh(curtail["curtailment_mwh"]),
        "Curtailment Revenue",
        format_gbp(curtail["curtailment_revenue"]),
        "Gen Add Revenue",
        format_gbp(curtail["generation_add_revenue"]),
        "Total BM Revenue",
        format_gbp(curtail["total_bm_revenue"])
    ]]
    dash.update("A8:I8", curtail_kpi)
    
    # Timestamp
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dash.update("A99", [[f"Last Updated (BtM PPA + BM from BigQuery): {ts}"]])
    
    print("✅ Dashboard sheet updated")


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------

def main():
    print("=" * 70)
    print("BtM PPA + BM/VLP Revenue Update (BigQuery → Sheets)")
    print("=" * 70)
    
    # 1) Get real system prices from BigQuery
    print("\n🔍 Querying system prices from BigQuery...")
    system_prices = get_system_prices_by_band()
    
    # 2) Calculate BtM PPA revenue with real prices
    print("\n💰 Calculating BtM PPA revenue...")
    btm_results = calculate_btm_ppa_revenue(system_prices)
    
    print(f"\n📊 Results:")
    print(f"   Stream 1 (Direct Import): {btm_results['stream1']['profit']:,.0f} GBP")
    print(f"   Stream 2 (Battery + VLP): {btm_results['stream2']['profit']:,.0f} GBP")
    print(f"   BtM PPA Subtotal: {btm_results['btm_ppa_profit']:,.0f} GBP")
    print(f"   Dynamic Containment: {DC_ANNUAL_REVENUE:,.0f} GBP")
    print(f"   TOTAL PROFIT: {btm_results['total_profit']:,.0f} GBP")
    print(f"   Battery cycles/year: {btm_results['stream2']['cycles']:.1f}")
    print(f"   RED coverage: {btm_results['red_coverage']:.1f}%")
    
    # 3) Get curtailment revenue
    print("\n⚡ Querying curtailment revenue...")
    curtail = get_curtailment_annual()
    print(f"   Curtailment MWh: {curtail['curtailment_mwh']:,.0f}")
    print(f"   Curtailment Revenue: {curtail['curtailment_revenue']:,.0f} GBP")
    print(f"   Total BM Revenue: {curtail['total_bm_revenue']:,.0f} GBP")
    
    # 4) Update sheets
    print("\n📝 Updating Google Sheets...")
    update_bess_sheet(btm_results, curtail)
    update_dashboard_sheet(btm_results, curtail)
    
    print("\n✅ Complete!")


if __name__ == "__main__":
    main()
