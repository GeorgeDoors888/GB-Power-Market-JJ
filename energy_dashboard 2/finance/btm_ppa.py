"""
Behind-the-Meter PPA Revenue Calculations

Calculates BtM PPA revenue streams using BigQuery data:
- Stream 1: Direct Import (when battery not discharging)
- Stream 2: Battery Discharge + VLP revenue
- Curtailment/BM Revenue tracking

Uses real system prices from BigQuery and optimal battery charging strategy.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from google.cloud import bigquery

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

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
VLP_AVG_UPLIFT = 12.0  # £/MWh
VLP_PARTICIPATION_RATE = 0.20

# Dynamic Containment Revenue (separate from BtM PPA)
DC_ANNUAL_REVENUE = 195458  # £/year

# Site configuration
SITE_DEMAND_MW = 2.5  # Constant demand
VLP_BM_UNITS = ["2__FBPGM001", "2__FBPGM002"]  # Flexgen battery units

# Analysis period
ANALYSIS_DAYS = 180


# -------------------------------------------------------------------
# SYSTEM PRICES FROM BIGQUERY
# -------------------------------------------------------------------

def get_system_prices_by_band(client: bigquery.Client, project_id: str, dataset: str) -> Dict[str, float]:
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
      FROM `{project_id}.{dataset}.bmrs_costs`
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
    
    df = client.query(sql).to_dataframe()
    
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
# CURTAILMENT REVENUE (VLP/BM)
# -------------------------------------------------------------------

def get_curtailment_annual(client: bigquery.Client, project_id: str, dataset: str) -> Dict[str, float]:
    """Get curtailment revenue from BM acceptances"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=ANALYSIS_DAYS)
    
    # Try the view first
    sql_view = f"""
    SELECT
      SUM(curtailment_mwh) AS total_curtailment_mwh,
      SUM(curtailment_revenue_gbp) AS total_curtailment_revenue_gbp,
      SUM(generation_add_mwh) AS generation_add_mwh,
      SUM(generation_add_revenue_gbp) AS generation_add_revenue_gbp,
      SUM(total_bm_mwh) AS total_bm_mwh,
      SUM(total_bm_revenue_gbp) AS total_bm_revenue_gbp
    FROM `{project_id}.{dataset}.v_curtailment_revenue_daily`
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
        df = client.query(sql_view, job_config=job_config).to_dataframe()
        
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
    except Exception:
        pass
    
    # Fallback: direct query on bmrs_boalf
    sql_direct = f"""
    SELECT
      SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 ELSE 0 END) AS curtailment_mwh,
      SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 * acceptancePrice ELSE 0 END) AS curtailment_revenue,
      SUM(CASE WHEN bidOfferFlag = 'O' THEN (levelTo - levelFrom) * 0.5 ELSE 0 END) AS generation_add_mwh,
      SUM(CASE WHEN bidOfferFlag = 'O' THEN (levelTo - levelFrom) * 0.5 * acceptancePrice ELSE 0 END) AS generation_add_revenue,
      SUM((levelTo - levelFrom) * 0.5) AS total_bm_mwh,
      SUM((levelTo - levelFrom) * 0.5 * acceptancePrice) AS total_bm_revenue
    FROM `{project_id}.{dataset}.bmrs_boalf`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
      AND bmUnit IN UNNEST(@bmus)
    """
    
    df = client.query(sql_direct, job_config=job_config).to_dataframe()
    
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
# BTM PPA REVENUE CALCULATION
# -------------------------------------------------------------------

def calculate_btm_ppa_revenue(system_prices: Dict[str, float]) -> Dict[str, Any]:
    """Calculate BtM PPA revenue using real system prices"""
    
    # Annual hours by band
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
    
    total_charged_mwh = green_charge_mwh + amber_charge_mwh
    total_discharged_mwh = total_charged_mwh * BESS_EFFICIENCY
    
    # Charging costs
    green_charging_cost = green_charge_mwh * green_cost
    amber_charging_cost = amber_charge_mwh * amber_cost
    total_charging_cost = green_charging_cost + amber_charging_cost
    
    # Battery discharge revenue (assume RED first, then AMBER)
    red_demand_mwh = red_hours * SITE_DEMAND_MW
    amber_demand_mwh = amber_hours * SITE_DEMAND_MW
    green_demand_mwh = green_hours * SITE_DEMAND_MW
    
    # Battery serves RED demand first
    battery_capacity_annual = total_discharged_mwh
    
    if battery_capacity_annual >= red_demand_mwh:
        battery_red_mwh = red_demand_mwh  # 100% coverage
        battery_amber_mwh = min(amber_demand_mwh, battery_capacity_annual - battery_red_mwh)
    else:
        battery_red_mwh = battery_capacity_annual
        battery_amber_mwh = 0
    
    battery_green_mwh = 0  # Never discharge during green
    total_battery_discharge = battery_red_mwh + battery_amber_mwh
    
    # VLP revenue
    vlp_revenue = total_battery_discharge * VLP_PARTICIPATION_RATE * VLP_AVG_UPLIFT
    
    # Stream 2: Battery + VLP
    stream2_ppa_revenue = total_battery_discharge * PPA_PRICE
    stream2_total_revenue = stream2_ppa_revenue + vlp_revenue
    stream2_profit = stream2_total_revenue - total_charging_cost
    
    # Stream 1: Direct import (remaining demand)
    stream1_red_mwh = 0  # Red never profitable (£209 cost vs £150 PPA)
    stream1_amber_mwh = amber_demand_mwh - battery_amber_mwh if amber_cost < PPA_PRICE else 0
    stream1_green_mwh = green_demand_mwh if green_cost < PPA_PRICE else 0
    
    stream1_total_mwh = stream1_red_mwh + stream1_amber_mwh + stream1_green_mwh
    
    stream1_green_revenue = stream1_green_mwh * PPA_PRICE
    stream1_green_cost = stream1_green_mwh * green_cost
    stream1_amber_revenue = stream1_amber_mwh * PPA_PRICE
    stream1_amber_cost = stream1_amber_mwh * amber_cost
    
    stream1_total_revenue = stream1_green_revenue + stream1_amber_revenue
    stream1_total_cost = stream1_green_cost + stream1_amber_cost
    stream1_profit = stream1_total_revenue - stream1_total_cost
    
    # Combined
    btm_ppa_profit = stream1_profit + stream2_profit
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
        },
        "btm_ppa_profit": btm_ppa_profit,
        "total_profit": total_profit,
        "red_coverage": (battery_red_mwh / red_demand_mwh * 100) if red_demand_mwh > 0 else 0,
    }


# -------------------------------------------------------------------
# HIGH-LEVEL API
# -------------------------------------------------------------------

def get_btm_ppa_metrics(client: bigquery.Client, project_id: str = "inner-cinema-476211-u9", 
                        dataset: str = "uk_energy_prod") -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Get complete BtM PPA metrics including revenue breakdown and curtailment.
    
    Returns:
        Tuple of (btm_results, curtailment_results)
    """
    # Get real system prices
    system_prices = get_system_prices_by_band(client, project_id, dataset)
    
    # Calculate BtM PPA revenue
    btm_results = calculate_btm_ppa_revenue(system_prices)
    
    # Get curtailment revenue
    curtailment = get_curtailment_annual(client, project_id, dataset)
    
    return btm_results, curtailment
