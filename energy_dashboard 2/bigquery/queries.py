import pandas as pd
from google.cloud import bigquery

def _to_df(job: bigquery.job.QueryJob) -> pd.DataFrame:
    return job.result().to_dataframe()

# ---------------- Core KPI queries ----------------

def get_vlp_kpis(client: bigquery.Client, window: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      COUNT(DISTINCT bmUnit) AS unit_count,
      SUM(total_mw) AS total_capacity_mw
    FROM `{client.project}.uk_energy_prod.vlp_trades_summary`
    WHERE settlementDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    """
    return _to_df(client.query(sql))

def get_vlp_detail(client: bigquery.Client, window: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      timestamp,
      bmUnit,
      service,
      mw_level
    FROM `{client.project}.uk_energy_prod.vlp_trades_detail`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    ORDER BY timestamp DESC
    LIMIT 1000
    """
    return _to_df(client.query(sql))

def get_wind_deviation(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT
      timestamp,
      gsp,
      farm_name,
      forecast_mw,
      actual_mw,
      (actual_mw - forecast_mw) AS delta,
      SAFE_DIVIDE(ABS(actual_mw - forecast_mw), NULLIF(forecast_mw,0)) AS pct_err,
      lat,
      lon
    FROM `{client.project}.uk_energy_prod.wind_deviation`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    """
    return _to_df(client.query(sql))

def get_spreads(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT
      timestamp,
      systemSellPrice AS sbp,
      systemBuyPrice AS ssp,
      (systemSellPrice - systemBuyPrice) AS spread,
      systemSellPrice AS system_price
    FROM `{client.project}.uk_energy_prod.bmrs_costs`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    """
    return _to_df(client.query(sql))

def get_bm_price_history(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT
      timestamp,
      sbp,
      ssp,
      system_imbalance_mw,
      net_ic_flow_mw,
      wind_delta_mw,
      demand_delta_mw,
      reserve_mw
    FROM `{client.project}.uk_energy_prod.bm_price_history`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    """
    return _to_df(client.query(sql))

def get_bess_kpis(client: bigquery.Client, window: str) -> pd.DataFrame:
    sql = f"""
    SELECT
      bmUnit,
      AVG(availability_flag) AS availability_ratio
    FROM `{client.project}.uk_energy_prod.bess_availability`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY bmUnit
    """
    return _to_df(client.query(sql))

# ---------------- Phase 11: Headroom + Flows + Turbines ----------------

def get_gsp_headroom(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    """Real-time GSP headroom metrics.

    Expected columns:
      gsp, timestamp, headroom_mw, demand_mw, gen_mw, rating_mw
    """
    sql = f"""
    SELECT
      timestamp,
      gsp,
      headroom_mw,
      demand_mw,
      gen_mw,
      rating_mw,
      SAFE_DIVIDE(headroom_mw, NULLIF(rating_mw,0)) AS headroom_pct
    FROM `{client.project}.uk_energy_prod.gsp_headroom_rt`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
    """
    return _to_df(client.query(sql))

def get_ic_flows(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    """Interconnector flows for ESO-style arrows."""
    sql = f"""
    SELECT
      timestamp,
      ic_name,
      from_region,
      to_region,
      flow_mw
    FROM `{client.project}.uk_energy_prod.ic_flows_rt`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 HOUR)
    """
    return _to_df(client.query(sql))

def get_turbine_history(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    """Turbine-level time series for ML forecasting."""
    sql = f"""
    SELECT
      timestamp,
      farm_name,
      turbine_id,
      lat,
      lon,
      forecast_mw,
      actual_mw
    FROM `{client.project}.uk_energy_prod.turbine_history`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    """
    return _to_df(client.query(sql))
