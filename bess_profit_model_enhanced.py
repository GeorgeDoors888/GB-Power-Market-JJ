#!/usr/bin/env python3
"""
Enhanced BESS Profit Model - Integrated with Dashboard Pipeline
Calculates per-SP and annual revenue across all streams:
- FR (DC/DR/DM availability + utilization)
- Wholesale arbitrage
- BM/BOA revenues
- VLP flexibility (with P444 compensation)
- Behind-the-meter savings (DUoS/levies/BSUoS)
- Capacity Market
- Degradation costs

Wires into Google Sheets BESS tab via dashboard_pipeline.py
"""

from google.cloud import bigquery
import pandas as pd
from typing import Dict, Tuple
from dataclasses import dataclass

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Constants
BESS_DEG_COST_PER_MWH = 10.0  # £/MWh throughput
VLP_FEE_SHARE = 0.15          # 15% aggregator fee
ROUND_TRIP_EFF = 0.9
CM_PRICE_PER_KW_YR = 30.59    # £/kW/year (2025 estimate)
CM_DERATE_FACTOR = 0.895      # 2-hour battery derating

@dataclass
class BESSAsset:
    asset_id: str
    power_mw: float
    energy_mwh: float
    efficiency: float = 0.9
    location: str = 'GB'

def compute_bess_profit_detailed(
    asset: BESSAsset,
    year: int,
    scenario: str = "central",
    client: bigquery.Client = None
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Returns:
        - DataFrame: Per-SP cashflow with all revenue/cost components
        - Dict: Annual summary KPIs by revenue stream
    """
    if client is None:
        client = bigquery.Client(project=PROJECT_ID)
    
    # Load per-SP cashflow inputs from unified view
    q = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.v_bess_cashflow_inputs`
    WHERE asset_id = @asset_id 
      AND year = @year
    ORDER BY settlement_datetime
    """
    
    job = client.query(
        q,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("asset_id", "STRING", asset.asset_id),
                bigquery.ScalarQueryParameter("year", "INT64", year),
            ]
        ),
    )
    df = job.to_dataframe()
    
    if df.empty:
        print(f"⚠️  No data for {asset.asset_id} in {year}")
        return pd.DataFrame(), {}
    
    # ====== REVENUE CALCULATIONS ======
    
    # 1. FR Revenue (availability + utilization - penalties)
    df["fr_revenue_gbp"] = (
        df["fr_availability_gbp"] + 
        df["fr_utilisation_gbp"] - 
        df["fr_penalty_gbp"]
    )
    
    # 2. BM/BOA Revenue
    df["bm_revenue_gbp"] = df["boa_revenue_gbp"]
    
    # 3. VLP Flexibility Revenue (net of aggregator fee)
    df["vlp_gross_revenue_gbp"] = df["vlp_payment_gbp"] + df["vlp_compensation_gbp"]
    df["vlp_fee_gbp"] = df["vlp_gross_revenue_gbp"] * VLP_FEE_SHARE
    df["vlp_net_revenue_gbp"] = df["vlp_gross_revenue_gbp"] - df["vlp_fee_gbp"]
    
    # 4. Wholesale Arbitrage
    # Discharge revenue - charge cost (using mid/system prices)
    df["discharge_mwh"] = df["bess_mwh"].clip(lower=0)
    df["charge_mwh"] = df["bess_mwh"].clip(upper=0).abs()
    
    df["arbitrage_revenue_gbp"] = df["discharge_mwh"] * df["mid_price_gbp_mwh"]
    df["arbitrage_cost_gbp"] = df["charge_mwh"] * df["import_price_gbp_mwh"]
    df["arbitrage_net_gbp"] = df["arbitrage_revenue_gbp"] - df["arbitrage_cost_gbp"]
    
    # 5. Behind-the-Meter Savings
    # Avoided import when discharging = discharge * (import_price - wholesale_price)
    df["btm_avoided_import_mwh"] = df["discharge_mwh"]
    df["btm_savings_gbp"] = df["btm_avoided_import_mwh"] * (
        df["levies_gbp_mwh"] + df["duos_rate_gbp_mwh"] + 5.0  # BSUoS ~£5/MWh
    )
    
    # ====== COST CALCULATIONS ======
    
    # 6. Charging Cost
    df["charging_cost_gbp"] = df["charge_mwh"] * df["import_price_gbp_mwh"]
    
    # 7. Degradation Cost (throughput-based)
    df["throughput_mwh"] = df["bess_mwh"].abs()
    df["degradation_cost_gbp"] = df["throughput_mwh"] * BESS_DEG_COST_PER_MWH
    
    # 8. VLP Fixed Costs (spread across year)
    vlp_fixed_annual = 12 * (250 + 150)  # £250 Elexon + £150 other/month
    vlp_fixed_per_sp = vlp_fixed_annual / (365 * 48)
    df["vlp_fixed_cost_gbp"] = vlp_fixed_per_sp
    
    # ====== TOTALS PER SP ======
    
    df["total_revenue_gbp"] = (
        df["fr_revenue_gbp"] +
        df["bm_revenue_gbp"] +
        df["vlp_net_revenue_gbp"] +
        df["arbitrage_net_gbp"] +
        df["btm_savings_gbp"]
    )
    
    df["total_cost_gbp"] = (
        df["charging_cost_gbp"] +
        df["degradation_cost_gbp"] +
        df["vlp_fixed_cost_gbp"]
    )
    
    df["net_profit_gbp"] = df["total_revenue_gbp"] - df["total_cost_gbp"]
    df["cum_profit_gbp"] = df["net_profit_gbp"].cumsum()
    
    # ====== ANNUAL SUMMARY ======
    
    annual_summary = {
        "asset_id": asset.asset_id,
        "year": year,
        "scenario": scenario,
        
        # Energy throughput
        "total_charged_mwh": df["charge_mwh"].sum(),
        "total_discharged_mwh": df["discharge_mwh"].sum(),
        "total_throughput_mwh": df["throughput_mwh"].sum(),
        "cycles_per_year": df["throughput_mwh"].sum() / (2 * asset.energy_mwh),
        
        # Revenue by stream
        "fr_revenue_gbp": df["fr_revenue_gbp"].sum(),
        "bm_revenue_gbp": df["bm_revenue_gbp"].sum(),
        "vlp_revenue_gbp": df["vlp_net_revenue_gbp"].sum(),
        "arbitrage_revenue_gbp": df["arbitrage_net_gbp"].sum(),
        "btm_savings_gbp": df["btm_savings_gbp"].sum(),
        
        # Capacity Market (annual)
        "cm_revenue_gbp": asset.power_mw * 1000 * CM_PRICE_PER_KW_YR * CM_DERATE_FACTOR,
        
        # Costs
        "charging_cost_gbp": df["charging_cost_gbp"].sum(),
        "degradation_cost_gbp": df["degradation_cost_gbp"].sum(),
        "vlp_fixed_cost_gbp": vlp_fixed_annual,
        "total_cost_gbp": df["total_cost_gbp"].sum() + vlp_fixed_annual,
        
        # Bottom line
        "total_revenue_gbp": df["total_revenue_gbp"].sum() + (asset.power_mw * 1000 * CM_PRICE_PER_KW_YR * CM_DERATE_FACTOR),
        "net_profit_gbp": df["net_profit_gbp"].sum() + (asset.power_mw * 1000 * CM_PRICE_PER_KW_YR * CM_DERATE_FACTOR),
        
        # Metrics
        "net_profit_gbp_per_kw_yr": (df["net_profit_gbp"].sum() + (asset.power_mw * 1000 * CM_PRICE_PER_KW_YR * CM_DERATE_FACTOR)) / (asset.power_mw * 1000),
        "avg_revenue_gbp_per_mwh": df["total_revenue_gbp"].sum() / max(df["discharge_mwh"].sum(), 1),
    }
    
    # Add revenue percentages
    total_rev = annual_summary["total_revenue_gbp"]
    if total_rev > 0:
        annual_summary["fr_revenue_pct"] = 100 * annual_summary["fr_revenue_gbp"] / total_rev
        annual_summary["bm_revenue_pct"] = 100 * annual_summary["bm_revenue_gbp"] / total_rev
        annual_summary["vlp_revenue_pct"] = 100 * annual_summary["vlp_revenue_gbp"] / total_rev
        annual_summary["arbitrage_revenue_pct"] = 100 * annual_summary["arbitrage_revenue_gbp"] / total_rev
        annual_summary["btm_savings_pct"] = 100 * annual_summary["btm_savings_gbp"] / total_rev
        annual_summary["cm_revenue_pct"] = 100 * annual_summary["cm_revenue_gbp"] / total_rev
    
    return df, annual_summary


def write_bess_to_sheets(
    df: pd.DataFrame,
    summary: Dict[str, float],
    sheet_id: str,
    credentials_path: str,
    start_row: int = 60
) -> None:
    """
    Write BESS cashflow and summary to Google Sheets
    - Per-SP data starting at specified row (default 60 to preserve existing DNO/HH/BtM PPA)
    - Annual KPIs to side panel (T column)
    - Revenue stack to W column
    
    Args:
        start_row: Starting row for enhanced analysis (default 60 preserves rows 1-50)
    """
    import gspread
    from google.oauth2.service_account import Credentials
    
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    gc = gspread.authorize(creds)
    
    ss = gc.open_by_key(sheet_id)
    
    try:
        bess_sheet = ss.worksheet('BESS')
    except gspread.WorksheetNotFound:
        bess_sheet = ss.add_worksheet(title='BESS', rows=10000, cols=30)
    
    # Write section divider and title
    divider_row = start_row - 2
    title_row = start_row - 1
    bess_sheet.update([['']], f'A{divider_row}')
    bess_sheet.update([['─── Enhanced Revenue Analysis (6-Stream Model) ───']], f'A{title_row}:Q{title_row}', value_input_option='USER_ENTERED')
    bess_sheet.format(f'A{title_row}:Q{title_row}', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 1.0, 'green': 0.4, 'blue': 0.0},
        'horizontalAlignment': 'CENTER'
    })
    
    # 1. Write headers at start_row
    headers = [
        'Timestamp', '', '', '', '', '', '', '', '', '',  # A-J (placeholders)
        'Charge (MWh)', 'Discharge (MWh)', 'SoC (MWh)', 
        'Total Cost (£)', 'Total Revenue (£)', 'Net Profit (£)', 'Cumulative Profit (£)'
    ]
    bess_sheet.update([headers], f'A{start_row}:Q{start_row}')
    
    # 2. Write per-SP data (A2:Q...)
    values = []
    for _, r in df.iterrows():
        values.append([
            r["settlement_datetime"].strftime('%Y-%m-%d %H:%M'),
            '', '', '', '', '', '', '', '', '',  # B-J placeholders
            float(r["charge_mwh"]),
            float(r["discharge_mwh"]),
            float(r["soc_mwh"]),
            float(r["total_cost_gbp"]),
            float(r["total_revenue_gbp"]),
            float(r["net_profit_gbp"]),
            float(r["cum_profit_gbp"]),
        ])
    
    if values:
        data_start_row = start_row + 1
        bess_sheet.update(values, f'A{data_start_row}:Q{data_start_row + len(values) - 1}')
    
    # 3. Write annual KPIs to side panel (T column to avoid conflicts with existing B3:B10)
    kpi_start = start_row
    kpi_labels = [
        ['📊 Enhanced Revenue KPIs'],
        ['Charged (MWh)'],
        ['Discharged (MWh)'],
        ['Revenue (£)'],
        ['Cost (£)'],
        ['Net Profit (£)'],
        ['£/kW/year'],
        ['Cycles/year']
    ]
    kpi_values = [
        [''],  # Header
        [summary["total_charged_mwh"]],
        [summary["total_discharged_mwh"]],
        [summary["total_revenue_gbp"]],
        [summary["total_cost_gbp"]],
        [summary["net_profit_gbp"]],
        [summary["net_profit_gbp_per_kw_yr"]],
        [summary.get("cycles_per_year", 0)]
    ]
    # Merge labels and values
    kpi_combined = [[label[0], value[0]] for label, value in zip(kpi_labels, kpi_values)]
    bess_sheet.update(kpi_combined, f'T{kpi_start}:U{kpi_start + len(kpi_combined) - 1}')
    
    # 4. Write revenue stack to W column (avoids conflict with existing F3:H9)
    stack_start = start_row
    stack_data = [
        ["Revenue Stream", "£/year", "%"],
        ["FR Revenue (ESO)", summary["fr_revenue_gbp"], summary.get("fr_revenue_pct", 0)],
        ["Wholesale Arbitrage", summary["arbitrage_revenue_gbp"], summary.get("arbitrage_revenue_pct", 0)],
        ["BM / BOA Revenue", summary["bm_revenue_gbp"], summary.get("bm_revenue_pct", 0)],
        ["VLP Flex Revenue", summary["vlp_revenue_gbp"], summary.get("vlp_revenue_pct", 0)],
        ["BTM Savings", summary["btm_savings_gbp"], summary.get("btm_savings_pct", 0)],
        ["Capacity Market", summary["cm_revenue_gbp"], summary.get("cm_revenue_pct", 0)],
        ["TOTAL", summary["total_revenue_gbp"], 100.0],
    ]
    bess_sheet.update(stack_data, f'W{stack_start}:Y{stack_start + len(stack_data) - 1}')
    
    print(f"✅ Enhanced BESS data written to sheet starting row {start_row}: {len(values)} rows, £{summary['net_profit_gbp']:,.0f} annual profit")


if __name__ == "__main__":
    # Example usage
    asset = BESSAsset(
        asset_id="BESS_2P5MW_5MWH",
        power_mw=2.5,
        energy_mwh=5.0,
        efficiency=0.9
    )
    
    client = bigquery.Client(project=PROJECT_ID)
    df, summary = compute_bess_profit_detailed(asset, year=2025, client=client)
    
    print(f"\n🔋 BESS Revenue Summary for {asset.asset_id} ({2025})")
    print("=" * 60)
    for key, val in summary.items():
        if 'gbp' in key.lower() and isinstance(val, (int, float)):
            print(f"  {key:30s}: £{val:>12,.0f}")
        elif 'pct' in key.lower():
            print(f"  {key:30s}: {val:>12.1f}%")
        elif isinstance(val, (int, float)):
            print(f"  {key:30s}: {val:>12.2f}")
    
    # Uncomment to write to Sheets:
    # write_bess_to_sheets(df, summary, "YOUR_SHEET_ID", "inner-cinema-credentials.json")
