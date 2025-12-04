import pandas as pd
from google.cloud import bigquery

def _to_df(job: bigquery.job.QueryJob) -> pd.DataFrame:
    return job.result().to_dataframe()

def get_gsp_geo(client: bigquery.Client, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT gsp, dno, geojson
    FROM `{client.project}.uk_energy_prod.geo_gsp`
    """
    return _to_df(client.query(sql))

def get_dno_geo(client: bigquery.Client) -> pd.DataFrame:
    sql = f"""
    SELECT dno, geojson
    FROM `{client.project}.uk_energy_prod.geo_dno`
    """
    return _to_df(client.query(sql))

def get_wind_geo(client: bigquery.Client, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT farm_name, capacity_mw, geojson
    FROM `{client.project}.uk_energy_prod.geo_wind_farms`
    """
    return _to_df(client.query(sql))

def get_ic_geo(client: bigquery.Client) -> pd.DataFrame:
    sql = f"""
    SELECT name, geojson
    FROM `{client.project}.uk_energy_prod.geo_interconnectors`
    """
    return _to_df(client.query(sql))

def get_turbine_geo_with_errors(client: bigquery.Client, window: str, resolved) -> pd.DataFrame:
    sql = f"""
    SELECT
      timestamp,
      farm_name,
      turbine_id,
      lat,
      lon,
      turbine_error_mw
    FROM `{client.project}.uk_energy_prod.turbine_errors`
    WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
    """
    return _to_df(client.query(sql))
