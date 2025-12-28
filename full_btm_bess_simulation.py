#!/usr/bin/env python3
"""
GB Power Market - Full BTM BESS Simulation

Complete Behind-the-Meter battery simulation with:
- BigQuery data integration (v_btm_bess_inputs view)
- Forward-looking optimization (48-period horizon)
- SoC time-series simulation
- All revenue streams (PPA + BM + DC + CM)
- All costs (SSP + DUoS + Levies)
- EBITDA calculation
- Google Sheets export (BESS + Dashboard tabs)

Usage:
    python3 full_btm_bess_simulation.py
"""

import os
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
import gspread

# Import optimization engine
from optimised_bess_engine import optimize_bess, simulate_soc_optimized, compute_metrics

# ====================================================
# CONFIGURATION
# ====================================================

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW_NAME = "v_btm_bess_inputs"
SERVICE_ACCOUNT_FILE = "../inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

# Battery parameters
INITIAL_SOC = 2.5  # MWh starting charge
BATTERY_ENERGY_MWH = 5.0

# OpEx
FIXED_OPEX_ANNUAL = 100_000  # £/year
VARIABLE_OPEX_PER_MWH = 3.0  # £/MWh discharged

# Analysis period (default: last 30 days)
DAYS_TO_ANALYZE = 30


# ====================================================
# BIGQUERY CONNECTION
# ====================================================

def get_bq_client():
    """Create BigQuery client with service account credentials."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/bigquery"],
    )
    return bigquery.Client(project=PROJECT_ID, credentials=creds)


def fetch_bess_inputs(client, days=DAYS_TO_ANALYZE) -> pd.DataFrame:
    """
    Fetch battery optimization inputs from BigQuery view.
    
    Args:
        client: BigQuery client
        days: Number of days to fetch (from today backwards)
    
    Returns:
        DataFrame with all cost/revenue components per half-hour
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT
        ts_halfhour,
        settlementDate,
        settlementPeriod,
        hour_of_day,
        day_of_week,
        month,
        duos_band,
        ssp_charge,
        duos_charge,
        levies_per_mwh,
        ppa_price,
        bm_revenue_per_mwh,
        dc_revenue_per_mwh,
        cm_revenue_per_mwh,
        other_revenue_per_mwh,
        total_cost_per_mwh,
        total_revenue_per_mwh,
        net_margin_per_mwh
    FROM `{PROJECT_ID}.{DATASET}.{VIEW_NAME}`
    WHERE settlementDate >= '{start_date}'
      AND settlementDate <= '{end_date}'
    ORDER BY ts_halfhour
    """
    
    print(f"Fetching data from {start_date} to {end_date}...")
    df = client.query(query).to_dataframe()
    print(f"✅ Fetched {len(df)} settlement periods ({len(df)/48:.1f} days)")
    
    return df


# ====================================================
# GOOGLE SHEETS CONNECTION
# ====================================================

def get_sheets_client():
    """Create Google Sheets client with service account credentials."""
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ],
    )
    return gspread.authorize(creds)


def write_to_sheets(df: pd.DataFrame, kpis: dict):
    """
    Write simulation results to Google Sheets.
    
    Args:
        df: Full time-series DataFrame
        kpis: Dictionary of summary metrics
    """
    print("\nWriting to Google Sheets...")
    
    gc = get_sheets_client()
    ss = gc.open_by_key(SPREADSHEET_ID)

    # ------------------------------------------------
    # WRITE BESS TAB (FULL TIME-SERIES)
    # ------------------------------------------------
    try:
        bess = ss.worksheet("BESS")
    except:
        print("Creating BESS sheet...")
        bess = ss.add_worksheet("BESS", rows=20000, cols=25)

    bess.clear()
    
    # Prepare data for export
    export_df = df[[
        'ts_halfhour', 'settlementDate', 'settlementPeriod',
        'duos_band', 'ssp_charge', 'duos_charge', 'levies_per_mwh',
        'ppa_price', 'bm_revenue_per_mwh', 'dc_revenue_per_mwh',
        'charge_mwh', 'discharge_mwh', 'soc_end',
        'sp_cost', 'sp_revenue', 'sp_net', 'action'
    ]].copy()
    
    # Convert timestamp to string for Sheets
    export_df['ts_halfhour'] = export_df['ts_halfhour'].astype(str)
    export_df['settlementDate'] = export_df['settlementDate'].astype(str)
    
    # Write headers
    headers = list(export_df.columns)
    bess.append_row(headers)
    
    # Write data (in batches for performance)
    rows = export_df.values.tolist()
    print(f"  Writing {len(rows)} rows to BESS sheet...")
    
    # Batch write (1000 rows at a time)
    batch_size = 1000
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        start_row = i + 2  # +2 because row 1 is headers, and sheets are 1-indexed
        bess.update(f'A{start_row}', batch)
        print(f"    Wrote rows {i+1} to {min(i+batch_size, len(rows))}")
    
    # Write KPI summary (rows 3-7, column B)
    bess.update('A3:B7', [
        ['Charged (MWh)', kpis['charged_mwh']],
        ['Discharged (MWh)', kpis['discharged_mwh']],
        ['Revenue (£)', kpis['total_revenue']],
        ['Cost (£)', kpis['total_cost']],
        ['EBITDA (£)', kpis['ebitda']]
    ])
    
    print("  ✅ BESS sheet updated")

    # ------------------------------------------------
    # WRITE DASHBOARD KPIs
    # ------------------------------------------------
    try:
        dash = ss.worksheet("Dashboard")
    except:
        print("Creating Dashboard sheet...")
        dash = ss.add_worksheet("Dashboard", rows=100, cols=20)
    
    # Write KPI values (Row 2)
    dash.update('B2:F2', [[
        kpis['charged_mwh'],
        kpis['discharged_mwh'],
        kpis['total_revenue'],
        kpis['total_cost'],
        kpis['ebitda']
    ]])
    
    # Write last updated timestamp
    dash.update('A99', f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("  ✅ Dashboard sheet updated")


# ====================================================
# EBITDA CALCULATION
# ====================================================

def compute_ebitda(df: pd.DataFrame, metrics: dict) -> dict:
    """
    Compute EBITDA with all costs and revenues.
    
    Args:
        df: Simulation DataFrame
        metrics: Metrics from compute_metrics()
    
    Returns:
        Enhanced metrics dict with EBITDA components
    """
    total_revenue = metrics['total_revenue']
    total_cost_energy = metrics['total_cost']
    total_discharged = metrics['discharged_mwh']
    
    # Calculate OpEx
    variable_opex = VARIABLE_OPEX_PER_MWH * total_discharged
    
    # Annualize if analyzing < 1 year
    days_analyzed = len(df) / 48  # 48 half-hours per day
    annualization_factor = 365 / days_analyzed if days_analyzed < 365 else 1
    
    fixed_opex = FIXED_OPEX_ANNUAL * (days_analyzed / 365)
    
    # EBITDA = Revenue - Energy Costs - OpEx (excludes interest, tax, D&A)
    ebitda = total_revenue - total_cost_energy - variable_opex - fixed_opex
    ebitda_annualized = ebitda * annualization_factor
    
    metrics.update({
        'total_revenue': total_revenue,
        'total_cost_energy': total_cost_energy,
        'opex_variable': variable_opex,
        'opex_fixed': fixed_opex,
        'ebitda': ebitda,
        'ebitda_annualized': ebitda_annualized,
        'days_analyzed': days_analyzed,
        'annualization_factor': annualization_factor
    })
    
    return metrics


# ====================================================
# REPORTING
# ====================================================

def print_summary(metrics: dict):
    """Print comprehensive performance summary."""
    print("\n" + "=" * 80)
    print("BATTERY PERFORMANCE SUMMARY")
    print("=" * 80)
    
    print(f"\n⚡ Energy Performance:")
    print(f"  Charged:         {metrics['charged_mwh']:>10,.1f} MWh")
    print(f"  Discharged:      {metrics['discharged_mwh']:>10,.1f} MWh")
    print(f"  Cycles:          {metrics['cycles']:>10,.1f} cycles")
    print(f"  Efficiency:      {metrics['avg_efficiency']*100:>10,.1f}%")
    print(f"  Utilization:     {metrics['utilization_pct']:>10,.1f}%")
    
    print(f"\n💰 Financial Performance:")
    print(f"  Revenue:         £{metrics['total_revenue']:>10,.0f}")
    print(f"  Energy Cost:     £{metrics['total_cost']:>10,.0f}")
    print(f"  Gross Profit:    £{metrics['gross_profit']:>10,.0f}")
    print(f"  Variable OpEx:   £{metrics['opex_variable']:>10,.0f}")
    print(f"  Fixed OpEx:      £{metrics['opex_fixed']:>10,.0f}")
    print(f"  EBITDA:          £{metrics['ebitda']:>10,.0f}")
    
    if metrics.get('annualization_factor', 1) > 1:
        print(f"\n📊 Annualized Performance ({metrics['days_analyzed']:.0f} days analyzed):")
        print(f"  Annual EBITDA:   £{metrics['ebitda_annualized']:>10,.0f}")
    
    print(f"\n📈 Per-Cycle Metrics:")
    print(f"  Profit/Cycle:    £{metrics['avg_profit_per_cycle']:>10,.2f}")
    print(f"  Charge Periods:  {metrics['charge_periods']:>10,}")
    print(f"  Discharge Periods: {metrics['discharge_periods']:>10,}")
    
    print("\n" + "=" * 80)


# ====================================================
# MAIN EXECUTION
# ====================================================

def main():
    """Execute full simulation pipeline."""
    print("=" * 80)
    print("GB POWER MARKET - FULL BTM BESS SIMULATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Fetch data from BigQuery
    client = get_bq_client()
    df_raw = fetch_bess_inputs(client, days=DAYS_TO_ANALYZE)
    
    if df_raw.empty:
        print("❌ No data retrieved from BigQuery")
        return
    
    # 2. Apply optimization
    print("\nApplying forward-looking optimization...")
    df_optimized = optimize_bess(df_raw)
    print("✅ Optimization complete")
    
    # 3. Run SoC simulation
    print("\nRunning SoC simulation...")
    df_simulated = simulate_soc_optimized(df_optimized, initial_soc=INITIAL_SOC)
    print("✅ Simulation complete")
    
    # 4. Compute metrics
    print("\nComputing performance metrics...")
    metrics = compute_metrics(df_simulated)
    metrics = compute_ebitda(df_simulated, metrics)
    print("✅ Metrics computed")
    
    # 5. Display results
    print_summary(metrics)
    
    # 6. Export to Google Sheets
    write_to_sheets(df_simulated, metrics)
    
    print(f"\n✅ SIMULATION COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
