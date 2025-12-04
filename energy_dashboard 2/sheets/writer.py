import os
from datetime import datetime
from typing import List, Dict, Any

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

DASHBOARD_SPREADSHEET_ID = os.getenv("DASHBOARD_SPREADSHEET_ID")
DASHBOARD_SHEET_NAME = os.getenv("DASHBOARD_SHEET_NAME", "Dashboard")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def _get_sheet():
    if not DASHBOARD_SPREADSHEET_ID:
        raise RuntimeError("DASHBOARD_SPREADSHEET_ID not set in environment")
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(DASHBOARD_SPREADSHEET_ID)
    return ss.worksheet(DASHBOARD_SHEET_NAME)

def _safe_number(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default

def _write_vlp_kpi_row(ws, vlp_kpis: pd.DataFrame, fr_arb_metrics: Dict[str, Any]) -> None:
    if vlp_kpis is None or vlp_kpis.empty:
        row = [
            "💰 VLP FLEXIBILITY",
            "Units", "-", "Capacity", "-", "FR Revenue", "-", "Arbitrage", "-", "Total", "-",
        ]
    else:
        row0 = vlp_kpis.iloc[0]
        units = int(row0.get("unit_count", 0))
        cap = _safe_number(row0.get("total_capacity_mw", 0.0))
        fr_rev = _safe_number(fr_arb_metrics.get("fr_revenue_annual", 0.0))
        arb_rev = _safe_number(fr_arb_metrics.get("arb_revenue_annual", 0.0))
        total = _safe_number(fr_arb_metrics.get("total_vlp_annual", fr_rev + arb_rev))
        row = [
            "💰 VLP FLEXIBILITY",
            "⚡ Units", f"{units}",
            "⚡ Capacity", f"{cap:,.0f} MW",
            "📊 FR Revenue", f"£{fr_rev:,.0f}/yr",
            "⚡ Arbitrage", f"£{arb_rev:,.0f}/yr",
            "💷 Total", f"£{total:,.0f}/yr",
        ]
    ws.update("A6:K6", [row])

def _write_bess_kpi_row(ws, bess_kpis: pd.DataFrame, bess_soh: float | None) -> None:
    if bess_kpis is None or bess_kpis.empty:
        row = [
            "🔋 BESS PORTFOLIO",
            "Availability", "-",
            "Top unit", "-",
            "SoH", "-" if bess_soh is None else f"{bess_soh:.1f}%",
            "Note", "No BESS data",
        ]
    else:
        df = bess_kpis.copy()
        if "availability_ratio" in df.columns:
            top = df.sort_values("availability_ratio", ascending=False).iloc[0]
            avg_av = df["availability_ratio"].mean() * 100.0
            top_name = top.get("bmUnit", "N/A")
            row = [
                "🔋 BESS PORTFOLIO",
                "Avg availability", f"{avg_av:.1f}%",
                "Top unit", f"{top_name}",
                "SoH", "-" if bess_soh is None else f"{bess_soh:.1f}%",
                "Units", f"{len(df)}",
            ]
        else:
            row = [
                "🔋 BESS PORTFOLIO",
                "Availability", "-",
                "Top unit", "-",
                "SoH", "-" if bess_soh is None else f"{bess_soh:.1f}%",
                "Units", "-",
            ]
    ws.update("A7:H7", [row])

def _write_insight_bullets(ws,
                           vlp_kpis: pd.DataFrame,
                           fr_arb_metrics: Dict[str, Any],
                           wind: pd.DataFrame,
                           spreads: pd.DataFrame,
                           btm_results: Dict[str, Any] = None,
                           curtailment: Dict[str, float] = None) -> None:
    lines: List[List[str]] = []
    if vlp_kpis is not None and not vlp_kpis.empty:
        row0 = vlp_kpis.iloc[0]
        units = int(row0.get("unit_count", 0))
        cap = _safe_number(row0.get("total_capacity_mw", 0.0))
        fr_rev = _safe_number(fr_arb_metrics.get("fr_revenue_annual", 0.0))
        arb_rev = _safe_number(fr_arb_metrics.get("arb_revenue_annual", 0.0))
        total = _safe_number(fr_arb_metrics.get("total_vlp_annual", fr_rev + arb_rev))
        text = (
            f"📈 VLP FR revenue annualised at £{fr_rev:,.0f}/yr, "
            f"arbitrage at £{arb_rev:,.0f}/yr, total VLP value about £{total/1e3:,.1f}k/yr "
            f"from {units} units ({cap:,.0f} MW)."
        )
        lines.append([text])
    
    # BtM PPA insights
    if btm_results is not None:
        s2 = btm_results.get("stream2", {})
        total_profit = btm_results.get("total_profit", 0)
        red_coverage = btm_results.get("red_coverage", 0)
        cycles = s2.get("cycles", 0)
        text = (
            f"💰 BtM PPA total profit: £{total_profit:,.0f}/yr "
            f"({red_coverage:.0f}% RED coverage, {cycles:.0f} battery cycles/yr)."
        )
        lines.append([text])
    
    if curtailment is not None:
        curtail_rev = curtailment.get("curtailment_revenue", 0)
        if curtail_rev > 0:
            text = f"⚡ Curtailment revenue: £{curtail_rev:,.0f}/yr from BM acceptances."
            lines.append([text])
    
    if wind is not None and not wind.empty and "pct_err" in wind.columns:
        mean_err = (wind["pct_err"].abs().mean() or 0) * 100.0
        text = f"🌬 Offshore wind forecast mean absolute error over the selected window is {mean_err:.1f}%."
        lines.append([text])
    if spreads is not None and not spreads.empty and "spread" in spreads.columns:
        avg_spread = spreads["spread"].mean()
        max_spread = spreads["spread"].max()
        text = (
            f"💹 Average SSP–SBP spread is £{avg_spread:,.1f}/MWh, "
            f"with peaks up to £{max_spread:,.1f}/MWh in the period."
        )
        lines.append([text])
    if not lines:
        lines = [["No insights available yet – run the dashboard backend to populate data."]]
    ws.update("A10:A" + str(9 + len(lines)), lines)

def write_dashboard(
    vlp_kpis: pd.DataFrame,
    fr_arb_metrics: Dict[str, Any],
    bess_kpis: pd.DataFrame,
    wind: pd.DataFrame,
    spreads: pd.DataFrame,
    bm_prices: pd.DataFrame,
    projections,
    dispatch_results,
    map_html: str,
    charts: list,
    bess_soh: float | None = None,
    btm_results: Dict[str, Any] = None,
    curtailment: Dict[str, float] = None,
) -> None:
    ws = _get_sheet()
    
    # Add BtM PPA row if data available
    if btm_results is not None:
        s1 = btm_results.get("stream1", {})
        s2 = btm_results.get("stream2", {})
        total_revenue = s1.get("total_revenue", 0) + s2.get("total_revenue", 0)
        total_cost = s1.get("total_cost", 0) + s2.get("charging_cost", 0)
        total_profit = btm_results.get("total_profit", 0)
        red_coverage = btm_results.get("red_coverage", 0)
        
        btm_row = [
            "💰 BtM PPA PROFIT",
            "Total Revenue", f"£{total_revenue:,.0f}",
            "Total Costs", f"£{total_cost:,.0f}",
            "Net Profit", f"£{total_profit:,.0f}",
            "RED Coverage", f"{red_coverage:.0f}%"
        ]
        ws.update("A8:H8", [btm_row])
        ws.batch_clear(["A6:K7", "A10:A15", "A99:A100"])
    else:
        ws.batch_clear(["A6:K8", "A10:A15", "A99:A100"])
    
    _write_vlp_kpi_row(ws, vlp_kpis, fr_arb_metrics)
    _write_bess_kpi_row(ws, bess_kpis, bess_soh)
    _write_insight_bullets(ws, vlp_kpis, fr_arb_metrics, wind, spreads, btm_results, curtailment)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    note = f"Last updated by backend: {ts}"
    ws.update("A99", [[note]])
