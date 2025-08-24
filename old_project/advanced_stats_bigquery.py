"""
Advanced Statistical Analysis Suite for BigQuery UK Energy Data
===============================================================

REQUIREMENTS (install once):
    pip install google-cloud-bigquery pandas numpy scipy statsmodels matplotlib pandas-gbq pyarrow

OPTIONAL (GCS upload of plots):
    pip install google-cloud-storage

USAGE:
    - Update CONFIG below (PROJECT_ID, DATASETs).
    - Run: python advanced_stats_bigquery.py

DATA MODEL (this version, aligned to your platform):
    Sources (uk_energy.*):
      - elexon_bid_offer_acceptances (BOD)        -> price proxies (SSP/SBP) + BOA volumes
      - elexon_demand_outturn                     -> demand (MW) -> volume proxy (MWh per SP)
      - elexon_generation_outturn                 -> contextual generation mix (optional in joins)
      - elexon_system_warnings                    -> grid/system event flag
      - neso_demand_forecasts                     -> temperature_forecast (°C)
      - neso_wind_forecasts                       -> actual_output_mw OR forecast_output_mw
      - neso_balancing_services                   -> cost/volume, BSUoS-like metrics

    Price sourcing precedence:
      1) If uk_energy.prices exists and has SSP/SBP -> use it
      2) Else derive:
         - SBP_proxy = VWAP of accepted offer_price where accepted_offer_volume > 0
         - SSP_proxy = VWAP of accepted bid_price   where accepted_bid_volume   > 0
         per (settlement_date, settlement_period)
      Spread = SBP - SSP.

OUTPUTS:
    BigQuery tables (written to DATASET_ANALYTICS):
        * ttest_results
        * anova_results
        * correlation_matrix
        * regression_temperature_ssp
        * regression_volume_price
        * arima_forecast_ssp
        * seasonal_decomposition_stats
        * outage_impact_results
        * neso_behavior_results
    Plots: ./output/ or gs://<GCS_BUCKET>/output/ if GCS_BUCKET set

NOTES:
    - ARIMA uses SARIMAX with weekly seasonality for 30-min data (period=48*7).
    - Timestamp per SP = TIMESTAMP(DATETIME(settlement_date) + (SP-1)*30 minutes), UTC.
"""

# =========================
# ======== CONFIG =========
# =========================
PROJECT_ID = "jibber-jabber-knowledge"
LOCATION = "europe-west2"  # London region recommended for uk grid data
DATASET_SOURCE = "uk_energy_prod"        # Raw/curated source dataset as per your setup
DATASET_ANALYTICS = "uk_energy_analysis" # Analytics outputs (create or let to_gbq create)

# ---- Optional: upload plots to GCS (recommended for your platform) ----
GCS_BUCKET = "jibber-jabber-knowledge-bmrs-data"  # set "" to save locally

# ---- Date range for analysis ----
DATE_START = "2024-12-01"
DATE_END = "2024-12-31"  # exclusive upper bound

# =========================
# ======== IMPORTS ========
# =========================
import pathlib
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX

from google.cloud import bigquery
from pandas_gbq import to_gbq

# Optional: GCS upload for plots
try:
    from google.cloud import storage as gcs_storage  # noqa
    HAS_GCS = True
except Exception:
    HAS_GCS = False

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

# =========================
# ====== UTILITIES ========
# =========================
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

def save_plot(fig, fname: str):
    """Save plot locally or to GCS if configured."""
    local_path = OUTDIR / fname
    fig.savefig(local_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    if GCS_BUCKET:
        if not HAS_GCS:
            print("[WARN] GCS_BUCKET set but google-cloud-storage not installed; saved locally.")
            return str(local_path)
        client = gcs_storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"output/{fname}")
        with open(local_path, "rb") as f:
            blob.upload_from_file(f)
        print(f"[GCS] Uploaded gs://{GCS_BUCKET}/output/{fname}")
        return f"gs://{GCS_BUCKET}/output/{fname}"
    return str(local_path)

def write_bq(df: pd.DataFrame, table_name: str, if_exists="replace"):
    """Write a DataFrame to BigQuery."""
    full_table = f"{PROJECT_ID}.{DATASET_ANALYTICS}.{table_name}"
    if df.empty:
        print(f"[INFO] {table_name}: DataFrame is empty; skipping write.")
        return
    to_gbq(df, full_table, project_id=PROJECT_ID, if_exists=if_exists, location=LOCATION)
    print(f"[BQ] Wrote {len(df):,} rows to {full_table} (if_exists={if_exists})")

def add_calendar_fields(df: pd.DataFrame, ts_col: str):
    ts = pd.to_datetime(df[ts_col])
    df["date"] = ts.dt.date
    df["month"] = ts.dt.month
    df["dow"] = ts.dt.dayofweek
    df["is_weekend"] = df["dow"] >= 5
    def season(m):
        return "Winter" if m in (12,1,2) else "Spring" if m in (3,4,5) else "Summer" if m in (6,7,8) else "Autumn"
    df["season"] = df["month"].apply(season)
    return df

# =========================
# ======== LOADING ========
# =========================
def _table_exists(client: bigquery.Client, fq_table: str) -> bool:
    try:
        client.get_table(fq_table)
        return True
    except Exception:
        return False

def load_data() -> pd.DataFrame:
    """
    Load and harmonize series from uk_energy dataset.
    - Price: uk_energy.prices(SSP/SBP) if present, else derive from BOD VWAPs.
    - Volume proxy: Demand Outturn national_demand (MW) -> MWh per 30min (MW*0.5).
    - Temperature: NESO demand_forecasts.temperature_forecast.
    - Wind: NESO wind actual_output_mw (fallback: forecast_output_mw).
    - Outages/events: elexon_system_warnings -> boolean flag per SP window.
    - Balancing metrics: neso_balancing_services -> cost/volume per SP.
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    prices_table = f"{PROJECT_ID}.{DATASET_SOURCE}.prices"
    has_prices = _table_exists(client, prices_table)

    # Build price CTE: either native prices(SSP/SBP) or derived VWAPs from BOD
    price_cte = f"""
    -- Build half-hourly timestamp per Elexon SP (SP 1 = 00:00–00:30)
    WITH sp_clock AS (
      SELECT
        settlement_date,
        settlement_period,
        TIMESTAMP(DATETIME(settlement_date)) AS midnight_utc,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_bid_offer_acceptances`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    {(
      # Native price table path
      f"""
      prices_raw AS (
        SELECT
          TIMESTAMP(ts) AS ts,
          CAST(SSP AS FLOAT64) AS SSP,
          CAST(SBP AS FLOAT64) AS SBP
        FROM `{prices_table}`
        WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
      ),
      prices AS (
        SELECT ts, SSP, SBP FROM prices_raw
      )
      """
      if has_prices else
      # Derive SSP/SBP from BOD (VWAP per SP)
      """
      bod AS (
        SELECT
          settlement_date,
          settlement_period,
          SUM(CASE WHEN accepted_offer_volume > 0 THEN offer_price * accepted_offer_volume END) / NULLIF(SUM(CASE WHEN accepted_offer_volume > 0 THEN accepted_offer_volume END),0) AS SBP,
          SUM(CASE WHEN accepted_bid_volume   > 0 THEN  bid_price * accepted_bid_volume   END) / NULLIF(SUM(CASE WHEN accepted_bid_volume   > 0 THEN   accepted_bid_volume END),0) AS SSP
        FROM `""" + f"{PROJECT_ID}.{DATASET_SOURCE}.elexon_bid_offer_acceptances" + """`
        WHERE settlement_date BETWEEN DATE('""" + DATE_START + """') AND DATE('""" + DATE_END + """')
        GROUP BY settlement_date, settlement_period
      ),
      prices AS (
        SELECT s.ts, b.SSP, b.SBP
        FROM sp_clock s
        LEFT JOIN bod b
          USING (settlement_date, settlement_period)
      )
      """
    )}
    SELECT * FROM prices
    """

    # Temperature (NESO demand forecasts)
    temp_cte = f"""
    WITH f AS (
      SELECT
        settlement_date,
        settlement_period,
        AVG(temperature_forecast) AS temperature
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    clk AS (
      SELECT
        settlement_date, settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT c.ts, f.temperature
    FROM clk c LEFT JOIN f USING (settlement_date, settlement_period)
    """

    # Wind (NESO wind forecasts/actuals)
    wind_cte = f"""
    WITH w AS (
      SELECT
        settlement_date,
        settlement_period,
        AVG(COALESCE(actual_output_mw, forecast_output_mw)) AS wind_generation
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    clk AS (
      SELECT
        settlement_date, settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT c.ts, w.wind_generation
    FROM clk c LEFT JOIN w USING (settlement_date, settlement_period)
    """

    # Demand Outturn -> volume proxy (MWh per 30-min = MW * 0.5)
    volume_cte = f"""
    WITH d AS (
      SELECT
        settlement_date,
        settlement_period,
        AVG(national_demand) AS demand_mw
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_demand_outturn`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    clk AS (
      SELECT
        settlement_date, settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_demand_outturn`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT c.ts, d.demand_mw * 0.5 AS volume_mwh
    FROM clk c LEFT JOIN d USING (settlement_date, settlement_period)
    """

    # System warnings -> event flag per timestamp (coarse: mark SPs overlapping any warning window)
    warnings_cte = f"""
    WITH w AS (
      SELECT
        TIMESTAMP(timestamp) AS ts_start,
        TIMESTAMP(COALESCE(end_time, timestamp)) AS ts_end,
        COALESCE(severity, 'UNKNOWN') AS severity
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_system_warnings`
      WHERE DATE(timestamp) BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
    )
    -- Build a 30-minute grid and mark if it intersects any window
    , grid AS (
      SELECT ts
      FROM UNNEST(GENERATE_TIMESTAMP_ARRAY(TIMESTAMP('{DATE_START}'), TIMESTAMP('{DATE_END}'), INTERVAL 30 MINUTE)) AS ts
    )
    , flagged AS (
      SELECT g.ts,
             MAX(CASE WHEN g.ts BETWEEN w.ts_start AND w.ts_end THEN 1 ELSE 0 END) AS system_event,
             ANY_VALUE(MAX(CASE WHEN g.ts BETWEEN w.ts_start AND w.ts_end AND w.severity='HIGH' THEN 1 ELSE 0 END)) AS severe_event
      FROM grid g
      LEFT JOIN w
      ON g.ts BETWEEN w.ts_start AND w.ts_end
      GROUP BY g.ts
    )
    SELECT ts, CAST(system_event AS BOOL) AS system_event, CAST(severe_event AS BOOL) AS severe_event
    FROM flagged
    """

    # NESO balancing services (cost/volume per SP)
    balancing_cte = f"""
    WITH b AS (
      SELECT
        charge_date AS settlement_date,
        settlement_period,
        SUM(cost_pounds) AS total_balancing_cost,
        SUM(volume_mwh) AS total_volume_mwh,
        SAFE_DIVIDE(SUM(cost_pounds), NULLIF(SUM(volume_mwh),0)) AS cost_per_mwh
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services`
      WHERE charge_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    clk AS (
      SELECT
        settlement_date, settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services`
      WHERE charge_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT c.ts, b.total_balancing_cost, b.total_volume_mwh, b.cost_per_mwh
    FROM clk c LEFT JOIN b USING (settlement_date, settlement_period)
    """

    # Final join (on ts)
    sql = f"""
    WITH prices AS ({price_cte}),
         temp AS ({temp_cte}),
         wind AS ({wind_cte}),
         vol  AS ({volume_cte}),
         warn AS ({warnings_cte}),
         bal  AS ({balancing_cte})
    SELECT
      p.ts,
      p.SSP,
      p.SBP,
      (p.SBP - p.SSP) AS spread,
      vol.volume_mwh AS volume,
      temp.temperature,
      wind.wind_generation,
      warn.system_event AS unplanned_event,
      warn.severe_event AS severe_event,
      bal.total_balancing_cost AS balancing_cost,
      bal.cost_per_mwh      AS balancing_cost_per_mwh
    FROM prices p
    LEFT JOIN vol  USING (ts)
    LEFT JOIN temp USING (ts)
    LEFT JOIN wind USING (ts)
    LEFT JOIN warn USING (ts)
    LEFT JOIN bal  USING (ts)
    WHERE p.ts >= TIMESTAMP('{DATE_START}') AND p.ts < TIMESTAMP('{DATE_END}')
    ORDER BY p.ts
    """

    df = client.query(sql).to_dataframe(create_bqstorage_client=True)
    if df.empty:
        raise RuntimeError("No data returned from BigQuery for the specified date range.")
    # drop rows missing both SSP and SBP (protect downstream calcs)
    if "SSP" in df.columns and "SBP" in df.columns:
        df = df.dropna(subset=["SSP", "SBP"], how="all")
    df = add_calendar_fields(df, "ts")
    return df

# =========================
# ====== STATISTICS =======
# =========================
def ttest_ssp_sbp(df: pd.DataFrame):
    if not {"SSP","SBP"}.issubset(df.columns):
        return pd.DataFrame()
    a = df["SSP"].astype(float).values
    b = df["SBP"].astype(float).values
    # Only keep finite values
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 3 or len(b) < 3:
        return pd.DataFrame()
    tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    n1, n2 = len(a), len(b)
    m1, m2 = np.nanmean(a), np.nanmean(b)
    s1, s2 = np.nanstd(a, ddof=1), np.nanstd(b, ddof=1)
    # Welch-Satterthwaite df
    df_denom = (s1**2/n1 + s2**2/n2)**2
    df_num = (s1**2/n1)**2/(n1-1) + (s2**2/n2)**2/(n2-1)
    dof = df_denom/df_num if df_num > 0 else np.nan
    mean_diff = m2 - m1
    se = np.sqrt(s1**2/n1 + s2**2/n2)
    ci_lo = mean_diff - 1.96*se
    ci_hi = mean_diff + 1.96*se
    return pd.DataFrame([{
        "metric": "SSP_vs_SBP",
        "t_stat": tstat,
        "p_value": pval,
        "mean_SSP": m1,
        "mean_SBP": m2,
        "mean_diff": mean_diff,
        "ci_95_lo": ci_lo,
        "ci_95_hi": ci_hi,
        "dof": dof,
        "n_SSP": n1,
        "n_SBP": n2
    }])

def anova_by_season(df: pd.DataFrame, price_col: str = "SSP"):
    if price_col not in df.columns:
        return pd.DataFrame()
    groups = [g[price_col].dropna().values for _, g in df.groupby("season")]
    groups = [x for x in groups if len(x) > 1]
    if len(groups) < 2:
        return pd.DataFrame()
    fstat, pval = stats.f_oneway(*groups)
    out = pd.DataFrame([{
        "price_col": price_col,
        "f_stat": fstat,
        "p_value": pval,
        "n_groups": len(groups),
        "group_names": list(df.groupby("season").groups.keys()),
        "group_sizes": [len(x) for x in groups],
        "group_means": [float(np.nanmean(x)) for x in groups],
    }])
    return out

def correlation_matrix(df: pd.DataFrame):
    cols = [c for c in [
        "SSP","SBP","spread","volume","temperature","wind_generation",
        "balancing_cost","balancing_cost_per_mwh"
    ] if c in df.columns]
    if not cols:
        return pd.DataFrame()
    cm = df[cols].corr(method="pearson")
    cm = cm.reset_index().rename(columns={"index": "variable"})
    return cm

def regression_temperature_ssp(df: pd.DataFrame):
    if not {"SSP","temperature"}.issubset(df.columns):
        return pd.DataFrame()
    d = df[["SSP", "temperature"]].dropna()
    if len(d) < 10:
        return pd.DataFrame()
    X = sm.add_constant(d["temperature"].astype(float))
    y = d["SSP"].astype(float)
    model = sm.OLS(y, X).fit()
    summary = {
        "model": "OLS_SSP_on_Temperature",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "intercept": float(model.params.get("const", np.nan)),
        "slope_temperature": float(model.params.get("temperature", np.nan)),
        "p_intercept": float(model.pvalues.get("const", np.nan)),
        "p_temperature": float(model.pvalues.get("temperature", np.nan))
    }
    # Plot
    fig, ax = plt.subplots(figsize=(7,5))
    ax.scatter(d["temperature"], d["SSP"], s=8, alpha=0.5)
    xgrid = np.linspace(d["temperature"].min(), d["temperature"].max(), 200)
    yhat = summary["intercept"] + summary["slope_temperature"] * xgrid
    ax.plot(xgrid, yhat, linewidth=2)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("SSP (£/MWh)")
    ax.set_title("Temperature vs SSP (OLS)")
    path = save_plot(fig, "reg_temperature_ssp.png")
    summary["plot_path"] = path
    return pd.DataFrame([summary])

def regression_volume_price(df: pd.DataFrame):
    # Price elasticity proxy: SSP ~ log(volume) + wind + temperature
    need = {"SSP","volume"}
    if not need.issubset(df.columns):
        return pd.DataFrame()
    d = df[["SSP","volume","wind_generation","temperature"]].dropna()
    d = d[d["volume"] > 0]
    if len(d) < 50:
        return pd.DataFrame()
    d = d.copy()
    d["log_volume"] = np.log(d["volume"])
    X = sm.add_constant(d[["log_volume","wind_generation","temperature"]].astype(float))
    y = d["SSP"].astype(float)
    model = sm.OLS(y, X).fit()
    return pd.DataFrame([{
        "model": "OLS_SSP_on_logVolume_controls",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "intercept": float(model.params.get("const", np.nan)),
        "beta_log_volume": float(model.params.get("log_volume", np.nan)),
        "beta_wind": float(model.params.get("wind_generation", np.nan)),
        "beta_temp": float(model.params.get("temperature", np.nan)),
        "p_log_volume": float(model.pvalues.get("log_volume", np.nan)),
        "p_wind": float(model.pvalues.get("wind_generation", np.nan)),
        "p_temp": float(model.pvalues.get("temperature", np.nan)),
    }])

def arima_ssp(df: pd.DataFrame):
    if "SSP" not in df.columns:
        return pd.DataFrame()
    d = df[["ts","SSP"]].dropna().copy()
    if d.empty:
        return pd.DataFrame()
    d["ts"] = pd.to_datetime(d["ts"])
    d = d.set_index("ts").sort_index()
    y = d["SSP"].asfreq("30min").interpolate(limit_direction="both")
    if y.size < 48*14:  # at least 2 weeks of 30-min data for stable weekly seasonality
        return pd.DataFrame()
    season = 48 * 7
    order = (1,1,1)
    seasonal_order = (1,1,1,season)
    try:
        model = SARIMAX(y, order=order, seasonal_order=seasonal_order,
                        enforce_stationarity=False, enforce_invertibility=False)
        res = model.fit(disp=False)
    except Exception as e:
        print(f"[WARN] ARIMA failed: {e}")
        return pd.DataFrame()
    steps = 48  # 24h ahead
    fc = res.get_forecast(steps=steps)
    pred = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    out = pd.DataFrame({
        "ts": pred.index,
        "forecast_ssp": pred.values,
        "ci_lo": ci.iloc[:,0].values,
        "ci_hi": ci.iloc[:,1].values
    }).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9,5))
    y.tail(48*7).plot(ax=ax, label="History")
    pred.plot(ax=ax, label="Forecast")
    ax.fill_between(out["ts"], out["ci_lo"], out["ci_hi"], alpha=0.2, label="95% CI")
    ax.set_title("SSP ARIMA Forecast (next 24h, 30-min steps)")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("SSP (£/MWh)")
    ax.legend()
    path = save_plot(fig, "arima_ssp_forecast.png")
    out["plot_path"] = path
    out["aic"] = res.aic
    out["bic"] = res.bic
    out["order"] = str(order)
    out["seasonal_order"] = str(seasonal_order)
    return out

def seasonal_decomp(df: pd.DataFrame):
    if "SSP" not in df.columns:
        return pd.DataFrame()
    d = df[["ts","SSP"]].dropna().copy()
    d["ts"] = pd.to_datetime(d["ts"])
    d = d.set_index("ts").sort_index()
    y = d["SSP"].asfreq("30min").interpolate(limit_direction="both")
    period = 48 * 7
    try:
        decomp = seasonal_decompose(y, model="additive", period=period, two_sided=False, extrapolate_trend="freq")
    except Exception as e:
        print(f"[WARN] Seasonal decomposition failed: {e}")
        return pd.DataFrame()
    fig, axes = plt.subplots(4, 1, figsize=(10,8))
    axes[0].plot(y.index, y.values); axes[0].set_title("Observed"); axes[0].set_ylabel("SSP")
    axes[1].plot(decomp.trend.index, decomp.trend.values); axes[1].set_title("Trend")
    axes[2].plot(decomp.seasonal.index, decomp.seasonal.values); axes[2].set_title("Seasonal")
    axes[3].plot(decomp.resid.index, decomp.resid.values); axes[3].set_title("Residual")
    for ax in axes: ax.set_xlabel("Time (UTC)")
    path = save_plot(fig, "seasonal_decomposition_ssp.png")
    stats_out = pd.DataFrame([{
        "period": int(period),
        "obs_count": int(len(y)),
        "trend_var": float(np.nanvar(decomp.trend.values)),
        "seasonal_var": float(np.nanvar(decomp.seasonal.values)),
        "resid_var": float(np.nanvar(decomp.resid.values)),
        "plot_path": path
    }])
    return stats_out

def outage_impact(df: pd.DataFrame):
    """Spread during system events vs non-events (proxy for outage/stress periods)."""
    if "spread" not in df.columns or "unplanned_event" not in df.columns:
        return pd.DataFrame()
    d = df[["spread","unplanned_event"]].dropna()
    if d.empty:
        return pd.DataFrame()
    a = d.loc[d["unplanned_event"] == True,  "spread"].values
    b = d.loc[d["unplanned_event"] == False, "spread"].values
    if len(a) < 5 or len(b) < 5:
        return pd.DataFrame()
    tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    return pd.DataFrame([{
        "metric": "spread_during_system_events",
        "mean_with_event": float(np.nanmean(a)),
        "mean_without_event": float(np.nanmean(b)),
        "mean_diff": float(np.nanmean(a) - np.nanmean(b)),
        "t_stat": float(tstat),
        "p_value": float(pval),
        "n_with": int(np.isfinite(a).sum()),
        "n_without": int(np.isfinite(b).sum())
    }])

def neso_behavior(df: pd.DataFrame):
    """Spread ~ NESO balancing cost intensity (and optional per-MWh rate)."""
    need_any = {"spread","balancing_cost","balancing_cost_per_mwh"}
    if not ({"spread","balancing_cost"}.issubset(df.columns)):
        return pd.DataFrame()
    cols = ["spread","balancing_cost"]
    if "balancing_cost_per_mwh" in df.columns:
        cols.append("balancing_cost_per_mwh")
    d = df[cols].dropna()
    if len(d) < 50:
        return pd.DataFrame()
    X = sm.add_constant(d[[c for c in cols if c != "spread"]].astype(float))
    y = d["spread"].astype(float)
    model = sm.OLS(y, X).fit()
    out = {
        "model": "Spread_on_BalancingCosts",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "beta_balancing_cost": float(model.params.get("balancing_cost", np.nan)),
        "p_balancing_cost": float(model.pvalues.get("balancing_cost", np.nan)),
    }
    if "balancing_cost_per_mwh" in X.columns:
        out.update({
            "beta_cost_per_mwh": float(model.params.get("balancing_cost_per_mwh", np.nan)),
            "p_cost_per_mwh": float(model.pvalues.get("balancing_cost_per_mwh", np.nan)),
        })
    return pd.DataFrame([out])

# =========================
# ======== PLOTS ==========
# =========================
def correlation_heatmap(df_corr: pd.DataFrame):
    """Save a correlation heatmap (matplotlib)."""
    if df_corr.empty:
        return ""
    cols = [c for c in df_corr.columns if c != "variable"]
    mat = df_corr.set_index("variable")[cols]
    fig, ax = plt.subplots(figsize=(7.5,6))
    im = ax.imshow(mat.values, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticks(range(len(mat.index))); ax.set_yticklabels(mat.index)
    ax.set_title("Correlation Matrix (Pearson)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    path = save_plot(fig, "correlation_matrix.png")
    return path

# =========================
# ========= MAIN ==========
# =========================
def main():
    print(f"[{datetime.utcnow().isoformat()}] Loading harmonized data from BigQuery uk_energy…")
    df = load_data()
    print(f"[INFO] Loaded {len(df):,} rows")

    # ===== Comparative Statistics =====
    print("[RUN] T-tests (SSP vs SBP)")
    ttest_df = ttest_ssp_sbp(df)
    write_bq(ttest_df, "ttest_results")

    print("[RUN] ANOVA by Season (SSP & SBP)")
    anova_ssp = anova_by_season(df, "SSP")
    anova_sbp = anova_by_season(df, "SBP")
    anova_all = pd.concat([anova_ssp, anova_sbp], ignore_index=True) if not anova_ssp.empty or not anova_sbp.empty else pd.DataFrame()
    write_bq(anova_all, "anova_results")

    # ===== Correlations =====
    print("[RUN] Correlation Matrix")
    corr_df = correlation_matrix(df)
    write_bq(corr_df, "correlation_matrix")
    try:
        heatmap_path = correlation_heatmap(corr_df)
        if heatmap_path:
            print(f"[PLOT] Correlation heatmap -> {heatmap_path}")
    except Exception as e:
        print(f"[WARN] Heatmap failed: {e}")

    # ===== Regression =====
    print("[RUN] OLS: Temperature -> SSP")
    reg_temp = regression_temperature_ssp(df)
    write_bq(reg_temp, "regression_temperature_ssp")

    print("[RUN] OLS: SSP vs log(Volume) + Wind + Temp")
    reg_vol = regression_volume_price(df)
    write_bq(reg_vol, "regression_volume_price")

    # ===== Time Series =====
    print("[RUN] ARIMA (SARIMAX) for SSP")
    arima_df = arima_ssp(df)
    write_bq(arima_df, "arima_forecast_ssp")

    print("[RUN] Seasonal Decomposition for SSP")
    decomp_df = seasonal_decomp(df)
    write_bq(decomp_df, "seasonal_decomposition_stats")

    # ===== External / Event Effects =====
    print("[RUN] System Warning (Outage/Event) impact on spread")
    out_outage = outage_impact(df)
    write_bq(out_outage, "outage_impact_results")

    print("[RUN] NESO balancing cost relationships")
    out_neso = neso_behavior(df)
    write_bq(out_neso, "neso_behavior_results")

    print("[DONE] All analyses complete.")

if __name__ == "__main__":
    main()
