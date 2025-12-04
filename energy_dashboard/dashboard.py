import os
from typing import Dict, Any

import pandas as pd

from bigquery.client import get_bq_client
from bigquery.queries import (
    get_vlp_kpis,
    get_vlp_detail,
    get_wind_deviation,
    get_spreads,
    get_bm_price_history,
    get_bess_kpis,
    get_gsp_headroom,
    get_ic_flows,
    get_turbine_history,
)
from bigquery.geo import (
    get_gsp_geo,
    get_dno_geo,
    get_wind_geo,
    get_ic_geo,
    get_turbine_geo_with_errors,
)
from bigquery.filter_engine import resolve_filters

from ml.wind_deviation import score_wind_deviation
from ml.gsp_forecast import apply_gsp_uncertainty
from ml.predict_constraints import predict_constraint_probability
from ml.bm_price import predict_bm_prices
from ml.turbine_forecast import forecast_turbine_output

from bess.soh_model import estimate_soh
from finance.long_term import project_10_years

from charts.vlp_chart import build_vlp_chart
from charts.bess_chart import build_bess_chart
from charts.wind_chart import build_wind_chart
from charts.spreads_chart import build_spreads_chart
from charts.bm_price_chart import build_bm_price_chart
from charts.projections_chart import build_projections_chart

from maps.map_builder import build_dynamic_map
from sheets.writer import write_dashboard
from utils.logging_utils import get_logger

LOGGER = get_logger(__name__)


def run_dashboard(filters: Dict[str, Any]) -> None:
    """Main orchestration entry point for the GB Energy Dashboard."""
    LOGGER.info("Running dashboard with filters=%s", filters)

    client = get_bq_client()
    resolved = resolve_filters(filters)

    window = filters.get("dateRange", "7D")

    # ---------------- BigQuery pulls ----------------
    vlp_kpis = get_vlp_kpis(client, window)
    vlp_detail = get_vlp_detail(client, window)
    wind = get_wind_deviation(client, window, resolved)
    spreads = get_spreads(client, window, resolved)
    bm_prices_raw = get_bm_price_history(client, window, resolved)
    bess_kpis = get_bess_kpis(client, window)

    gsp_geo = get_gsp_geo(client, resolved)
    dno_geo = get_dno_geo(client)
    wind_geo = get_wind_geo(client, resolved)
    ic_geo = get_ic_geo(client)
    turbine_geo = get_turbine_geo_with_errors(client, window, resolved)

    gsp_headroom = get_gsp_headroom(client, window, resolved)
    ic_flows = get_ic_flows(client, window, resolved)
    turbine_history = get_turbine_history(client, window, resolved)

    # ---------------- ML transforms ----------------
    wind_scored = score_wind_deviation(wind) if not wind.empty else wind

    # Constraint probability & GSP uncertainty (Phase 11 part 1)
    constraints_input = pd.DataFrame()
    if not wind_scored.empty and "timestamp" in wind_scored.columns and "gsp" in wind_scored.columns:
        constraints_input = wind_scored.copy()
        if "system_price" in spreads.columns:
            constraints_input = constraints_input.merge(
                spreads[["timestamp", "system_price"]],
                on="timestamp",
                how="left",
            )

    constraints = (
        predict_constraint_probability(constraints_input)
        if not constraints_input.empty
        else pd.DataFrame()
    )
    constraints = apply_gsp_uncertainty(constraints) if not constraints.empty else constraints

    # BM price ML (Phase 11 part 3 hook)
    bm_prices = predict_bm_prices(bm_prices_raw) if not bm_prices_raw.empty else bm_prices_raw

    # Turbine-level NN forecasting (Phase 11 part 2)
    turbine_forecast = pd.DataFrame()
    if not turbine_history.empty:
        try:
            turbine_forecast = forecast_turbine_output(turbine_history)
        except Exception as e:
            LOGGER.warning("Turbine forecast failed: %s", e)

    # Attach forecast outputs onto turbine_geo by turbine_id where possible
    if not turbine_geo.empty and not turbine_forecast.empty and "turbine_id" in turbine_geo.columns:
        turbine_geo = turbine_geo.merge(
            turbine_forecast[["turbine_id", "forecast_mw", "forecast_err_mw"]],
            on="turbine_id",
            how="left",
        )

    # BESS SoH (simple model)
    bess_soh = None
    try:
        if not vlp_kpis.empty:
            cap_mw = float(vlp_kpis.iloc[0].get("total_capacity_mw", 0.0))
            cycles = 365
            throughput = cycles * cap_mw
            bess_soh = estimate_soh(cycles=cycles, throughput_mwh=throughput)
    except Exception as e:
        LOGGER.warning("SoH calc failed: %s", e)

    # FR + arbitrage high-level KPIs (can be replaced later with detailed calc)
    fr_revenue_annual = float(os.getenv("FR_REVENUE_FALLBACK", "50000"))
    arb_revenue_annual = float(os.getenv("ARB_REVENUE_FALLBACK", "8000"))
    total_vlp_annual = fr_revenue_annual + arb_revenue_annual

    fr_arb_metrics = {
        "fr_revenue_annual": fr_revenue_annual,
        "arb_revenue_annual": arb_revenue_annual,
        "total_vlp_annual": total_vlp_annual,
    }

    # Long-term projections
    capacity_kw = 0.0
    if not vlp_kpis.empty:
        capacity_kw = float(vlp_kpis.iloc[0].get("total_capacity_mw", 0.0)) * 1000.0

    cm_price = float(os.getenv("CM_PRICE", "20"))

    projections = project_10_years(
        start_year=pd.Timestamp.utcnow().year,
        capacity_kw=capacity_kw,
        cm_price=cm_price,
        eso_revenue_year1=fr_revenue_annual,
        fr_arb_year1=arb_revenue_annual,
        bm_year1=0.0,
        network_costs_year1=0.0,
        soh0=bess_soh or 100.0,
    )

    # ---------------- Charts ----------------
    charts = []
    charts.append(build_vlp_chart(vlp_kpis, "out/vlp_chart.png"))
    charts.append(build_bess_chart(bess_kpis, "out/bess_chart.png"))
    charts.append(build_wind_chart(wind_scored, "out/wind_chart.png"))
    charts.append(build_spreads_chart(spreads, "out/spreads_chart.png"))
    charts.append(build_bm_price_chart(bm_prices, "out/bm_price_chart.png"))
    charts.append(build_projections_chart(projections, "out/projections_chart.png"))

    # ---------------- Map (Phase 11: flows + headroom) ----------------
    map_html = build_dynamic_map(
        gsp_geo=gsp_geo,
        dno_geo=dno_geo,
        wind_geo=wind_geo,
        ic_geo=ic_geo,
        constraints_df=constraints,
        gsp_headroom_df=gsp_headroom,
        wind_df=wind_scored,
        turbine_df=turbine_geo,
        ic_flows_df=ic_flows,
        filters=filters,
        html_out="out/map.html",
    )

    # ---------------- Sheets ----------------
    write_dashboard(
        vlp_kpis=vlp_kpis,
        fr_arb_metrics=fr_arb_metrics,
        bess_kpis=bess_kpis,
        wind=wind_scored,
        spreads=spreads,
        bm_prices=bm_prices,
        projections=projections,
        dispatch_results=None,
        map_html=map_html,
        charts=charts,
        bess_soh=bess_soh,
    )

    LOGGER.info("Dashboard run complete.")
