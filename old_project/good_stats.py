"""
Advanced Statistical Analysis Suite for BigQuery Energy Market Data
==================================================================

REQUIREMENTS (install once):
    pip install google-cloud-bigquery pandas numpy scipy statsmodels matplotlib pandas-gbq pyarrow

OPTIONAL (GCS upload of plots):
    pip install google-cloud-storage

USAGE:
    - Update CONFIG below.
    - Run: python advanced_stats_bigquery.py

OUTPUTS:
    - BigQuery tables (written to DATASET_ANALYTICS):
        * ttest_results
        * anova_results
        * correlation_matrix
        * regression_temperature_ssp
        * regression_volume_price
        * arima_forecast_ssp
        * seasonal_decomposition_stats
        * outage_impact_results
        * neso_behavior_results
    - Plots saved under ./output/ (or gs://YOUR_BUCKET/output/ if GCS_BUCKET set)

NOTES:
    - Column names are configurable in CONFIG -> COLUMN_MAP.
    - ARIMA uses SARIMAX with weekly seasonality on half-hourly data (period=48*7). Adjust if your granularity differs.
"""

# =========================
# ======== CONFIG =========
# =========================
PROJECT_ID = "your-gcp-project"
LOCATION = "EU"  # or "US"
DATASET_SOURCE = "market_source"           # BigQuery dataset with raw tables
DATASET_ANALYTICS = "market_analytics"     # BigQuery dataset to write results

# ---- Source tables (fully qualified or dataset-local) ----
TABLE_PRICES = f"{PROJECT_ID}.{DATASET_SOURCE}.prices"       # columns: ts, region, SSP, SBP, volume
TABLE_WEATHER = f"{PROJECT_ID}.{DATASET_SOURCE}.weather"     # columns: ts, region, temperature
TABLE_WIND = f"{PROJECT_ID}.{DATASET_SOURCE}.wind"           # columns: ts, region, wind_generation
TABLE_OUTAGES = f"{PROJECT_ID}.{DATASET_SOURCE}.outages"     # columns: ts, region, outage_mw, unplanned
TABLE_NESO = f"{PROJECT_ID}.{DATASET_SOURCE}.neso"           # columns: ts, bid_acceptance, offer_acceptance, balancing_cost

# ---- Date range for analysis ----
DATE_START = "2019-01-01"
DATE_END = "2025-08-01"  # exclusive upper bound

# ---- Optional: upload plots to GCS. Leave empty to save locally. ----
GCS_BUCKET = ""  # e.g. "upowerenergy-analysis-artifacts"

# ---- Column map (edit to match your schema) ----
COLUMN_MAP = {
    "timestamp": "ts",
    "region": "region",
    "ssp": "SSP",
    "sbp": "SBP",
    "volume": "volume",
    "temperature": "temperature",
    "wind_generation": "wind_generation",
    "outage_mw": "outage_mw",
    "unplanned": "unplanned",
    "bid_accept": "bid_acceptance",
    "offer_accept": "offer_acceptance",
    "balancing_cost": "balancing_cost",
}

# =========================
# ======== IMPORTS ========
# =========================
import os
import io
import math
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
    df["date"] = pd.to_datetime(df[ts_col]).dt.date
    df["month"] = pd.to_datetime(df[ts_col]).dt.month
    df["dow"] = pd.to_datetime(df[ts_col]).dt.dayofweek
    df["is_weekend"] = df["dow"] >= 5
    # Seasons: Winter(12-2), Spring(3-5), Summer(6-8), Autumn(9-11)
    def season(m):
        return (
            "Winter" if m in (12, 1, 2) else
            "Spring" if m in (3, 4, 5) else
            "Summer" if m in (6, 7, 8) else
            "Autumn"
        )
    df["season"] = df["month"].apply(season)
    return df

# =========================
# ======== LOADING ========
# =========================
def load_data() -> pd.DataFrame:
    """Load and join source data from BigQuery within date range."""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Base SQL: pull relevant fields and left join external factors on timestamp + region
    sql = f"""
    WITH prices AS (
      SELECT
        {COLUMN_MAP['timestamp']} AS ts,
        {COLUMN_MAP['region']} AS region,
        {COLUMN_MAP['ssp']} AS SSP,
        {COLUMN_MAP['sbp']} AS SBP,
        {COLUMN_MAP['volume']} AS volume
      FROM `{TABLE_PRICES}`
      WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
    ),
    weather AS (
      SELECT
        {COLUMN_MAP['timestamp']} AS ts,
        {COLUMN_MAP['region']} AS region,
        {COLUMN_MAP['temperature']} AS temperature
      FROM `{TABLE_WEATHER}`
      WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
    ),
    wind AS (
      SELECT
        {COLUMN_MAP['timestamp']} AS ts,
        {COLUMN_MAP['region']} AS region,
        {COLUMN_MAP['wind_generation']} AS wind_generation
      FROM `{TABLE_WIND}`
      WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
    ),
    outages AS (
      SELECT
        {COLUMN_MAP['timestamp']} AS ts,
        {COLUMN_MAP['region']} AS region,
        {COLUMN_MAP['outage_mw']} AS outage_mw,
        CAST({COLUMN_MAP['unplanned']} AS BOOL) AS unplanned
      FROM `{TABLE_OUTAGES}`
      WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
    ),
    neso AS (
      SELECT
        {COLUMN_MAP['timestamp']} AS ts,
        {COLUMN_MAP['bid_accept']} AS bid_acceptance,
        {COLUMN_MAP['offer_accept']} AS offer_acceptance,
        {COLUMN_MAP['balancing_cost']} AS balancing_cost
      FROM `{TABLE_NESO}`
      WHERE ts >= TIMESTAMP('{DATE_START}') AND ts < TIMESTAMP('{DATE_END}')
    )
    SELECT
      p.ts, p.region, p.SSP, p.SBP, p.volume,
      w.temperature,
      g.wind_generation,
      o.outage_mw, o.unplanned,
      n.bid_acceptance, n.offer_acceptance, n.balancing_cost
    FROM prices p
    LEFT JOIN weather w USING (ts, region)
    LEFT JOIN wind g USING (ts, region)
    LEFT JOIN outages o USING (ts, region)
    LEFT JOIN neso n USING (ts)
    ORDER BY ts
    """
    df = client.query(sql).to_dataframe(create_bqstorage_client=True)
    if df.empty:
        raise RuntimeError("No data returned from BigQuery for the specified date range.")
    df = df.dropna(subset=["SSP", "SBP"])
    df = add_calendar_fields(df, "ts")
    df["spread"] = df["SBP"] - df["SSP"]
    return df

# =========================
# ====== STATISTICS =======
# =========================
def ttest_ssp_sbp(df: pd.DataFrame):
    a = df["SSP"].astype(float).values
    b = df["SBP"].astype(float).values
    tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    n1, n2 = np.isfinite(a).sum(), np.isfinite(b).sum()
    m1, m2 = np.nanmean(a), np.nanmean(b)
    s1, s2 = np.nanstd(a, ddof=1), np.nanstd(b, ddof=1)

    # Welch-Satterthwaite df
    df_denom = (s1**2/n1 + s2**2/n2)**2
    df_num = (s1**2/n1)**2/(n1-1) + (s2**2/n2)**2/(n2-1)
    dof = df_denom/df_num if df_num > 0 else np.nan

    # 95% CI for difference in means
    mean_diff = m2 - m1
    se = np.sqrt(s1**2/n1 + s2**2/n2)
    ci_lo = mean_diff - 1.96*se
    ci_hi = mean_diff + 1.96*se

    out = pd.DataFrame([{
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
    return out

def anova_by_season(df: pd.DataFrame, price_col: str = "SSP"):
    groups = [g[price_col].dropna().values for _, g in df.groupby("season")]
    if len(groups) < 2:
        return pd.DataFrame()
    fstat, pval = stats.f_oneway(*groups)
    out = pd.DataFrame([{
        "price_col": price_col,
        "f_stat": fstat,
        "p_value": pval,
        "n_groups": len(groups),
        "group_sizes": [len(x) for x in groups],
        "group_means": [np.nanmean(x) for x in groups],
        "group_names": list(df.groupby("season").groups.keys())
    }])
    return out

def correlation_matrix(df: pd.DataFrame):
    cols = ["SSP", "SBP", "volume", "temperature", "wind_generation", "spread", "bid_acceptance", "offer_acceptance", "balancing_cost"]
    cols = [c for c in cols if c in df.columns]
    cm = df[cols].corr(method="pearson")
    cm = cm.reset_index().rename(columns={"index": "variable"})
    return cm

def regression_temperature_ssp(df: pd.DataFrame):
    d = df[["SSP", "temperature"]].dropna()
    if d.empty:
        return pd.DataFrame()
    X = sm.add_constant(d["temperature"].astype(float))
    y = d["SSP"].astype(float)
    model = sm.OLS(y, X).fit()
    summary = {
        "model": "OLS_SSP_on_Temperature",
        "n_obs": int(model.nobs),
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "intercept": model.params.get("const", np.nan),
        "slope_temperature": model.params.get("temperature", np.nan),
        "p_intercept": model.pvalues.get("const", np.nan),
        "p_temperature": model.pvalues.get("temperature", np.nan)
    }

    # Scatter + fitted line
    fig, ax = plt.subplots(figsize=(7,5))
    ax.scatter(d["temperature"], d["SSP"], s=8, alpha=0.5)
    xgrid = np.linspace(d["temperature"].min(), d["temperature"].max(), 200)
    yhat = summary["intercept"] + summary["slope_temperature"] * xgrid
    ax.plot(xgrid, yhat, linewidth=2)
    ax.set_xlabel("Temperature")
    ax.set_ylabel("SSP")
    ax.set_title("Temperature vs SSP (OLS)")
    path = save_plot(fig, "reg_temperature_ssp.png")
    summary["plot_path"] = path

    return pd.DataFrame([summary])

def regression_volume_price(df: pd.DataFrame):
    # Price elasticity proxy: regress SSP on log(volume) and wind + temperature controls
    d = df[["SSP", "volume", "wind_generation", "temperature"]].dropna()
    if d.empty:
        return pd.DataFrame()
    d = d[(d["volume"] > 0)]
    d["log_volume"] = np.log(d["volume"])
    X = sm.add_constant(d[["log_volume", "wind_generation", "temperature"]].astype(float))
    y = d["SSP"].astype(float)
    model = sm.OLS(y, X).fit()
    return pd.DataFrame([{
        "model": "OLS_SSP_on_logVolume_controls",
        "n_obs": int(model.nobs),
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "intercept": model.params.get("const", np.nan),
        "beta_log_volume": model.params.get("log_volume", np.nan),
        "beta_wind": model.params.get("wind_generation", np.nan),
        "beta_temp": model.params.get("temperature", np.nan),
        "p_log_volume": model.pvalues.get("log_volume", np.nan),
        "p_wind": model.pvalues.get("wind_generation", np.nan),
        "p_temp": model.pvalues.get("temperature", np.nan),
    }])

def arima_ssp(df: pd.DataFrame):
    # Aggregate to hourly to reduce runtime (adjust if your data is daily/half-hourly)
    d = df[["ts", "SSP"]].dropna().copy()
    d["ts"] = pd.to_datetime(d["ts"])
    d = d.set_index("ts").sort_index()
    # Resample half-hourly (if your data is already half-hourly, this keeps it)
    y = d["SSP"].asfreq("30min").interpolate(limit_direction="both")

    # SARIMAX with weekly seasonality for half-hourly: 48 * 7 = 336
    season = 48 * 7
    order = (1,1,1)
    seasonal_order = (1,1,1,season)
    try:
        model = SARIMAX(y, order=order, seasonal_order=seasonal_order, enforce_stationarity=False, enforce_invertibility=False)
        res = model.fit(disp=False)
    except Exception as e:
        print(f"[WARN] ARIMA failed: {e}")
        return pd.DataFrame()

    steps = 48  # 1 day ahead at 30-min intervals
    fc = res.get_forecast(steps=steps)
    pred = fc.predicted_mean
    ci = fc.conf_int(alpha=0.05)
    out = pd.DataFrame({
        "ts": pred.index,
        "forecast_ssp": pred.values,
        "ci_lo": ci.iloc[:,0].values,
        "ci_hi": ci.iloc[:,1].values
    }).reset_index(drop=True)

    # Plot
    fig, ax = plt.subplots(figsize=(9,5))
    y.tail(48*7).plot(ax=ax)  # last week for context
    pred.plot(ax=ax)
    ax.fill_between(out["ts"], out["ci_lo"], out["ci_hi"], alpha=0.2)
    ax.set_title("SSP ARIMA Forecast (next 24h, 30-min steps)")
    ax.set_xlabel("Time")
    ax.set_ylabel("SSP")
    path = save_plot(fig, "arima_ssp_forecast.png")
    out["plot_path"] = path
    out["aic"] = res.aic
    out["bic"] = res.bic
    out["order"] = str(order)
    out["seasonal_order"] = str(seasonal_order)
    return out

def seasonal_decomp(df: pd.DataFrame):
    d = df[["ts", "SSP"]].dropna().copy()
    d["ts"] = pd.to_datetime(d["ts"])
    d = d.set_index("ts").sort_index()
    y = d["SSP"].asfreq("30min").interpolate(limit_direction="both")
    period = 48 * 7  # weekly seasonal period for 30-min data
    try:
        decomp = seasonal_decompose(y, model="additive", period=period, two_sided=False, extrapolate_trend="freq")
    except Exception as e:
        print(f"[WARN] Seasonal decomposition failed: {e}")
        return pd.DataFrame()

    # Plot components
    fig, axes = plt.subplots(4, 1, figsize=(10,8))
    axes[0].plot(y.index, y.values); axes[0].set_title("Observed")
    axes[1].plot(decomp.trend.index, decomp.trend.values); axes[1].set_title("Trend")
    axes[2].plot(decomp.seasonal.index, decomp.seasonal.values); axes[2].set_title("Seasonal")
    axes[3].plot(decomp.resid.index, decomp.resid.values); axes[3].set_title("Residual")
    for ax in axes: ax.set_xlabel("Time")
    axes[0].set_ylabel("SSP")
    path = save_plot(fig, "seasonal_decomposition_ssp.png")

    stats_out = pd.DataFrame([{
        "period": period,
        "obs_count": len(y),
        "trend_var": np.nanvar(decomp.trend.values),
        "seasonal_var": np.nanvar(decomp.seasonal.values),
        "resid_var": np.nanvar(decomp.resid.values),
        "plot_path": path
    }])
    return stats_out

def outage_impact(df: pd.DataFrame):
    """Quantify unplanned outage effects on spread."""
    d = df[["spread", "outage_mw", "unplanned"]].dropna()
    if d.empty:
        return pd.DataFrame()
    d["has_unplanned"] = d["unplanned"].astype(bool)
    a = d.loc[d["has_unplanned"], "spread"].values
    b = d.loc[~d["has_unplanned"], "spread"].values
    tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    return pd.DataFrame([{
        "metric": "spread_with_unplanned_outage",
        "mean_with_outage": np.nanmean(a),
        "mean_without_outage": np.nanmean(b),
        "mean_diff": np.nanmean(a) - np.nanmean(b),
        "t_stat": tstat,
        "p_value": pval,
        "n_with": int(np.isfinite(a).sum()),
        "n_without": int(np.isfinite(b).sum())
    }])

def neso_behavior(df: pd.DataFrame):
    """NESO bid/offer acceptance & balancing cost relationships."""
    cols = ["SSP", "SBP", "spread", "bid_acceptance", "offer_acceptance", "balancing_cost"]
    d = df[cols].dropna()
    if d.empty:
        return pd.DataFrame()
    # Simple elasticity proxy: spread vs bid/offer acceptance & balancing cost
    X = sm.add_constant(d[["bid_acceptance", "offer_acceptance", "balancing_cost"]].astype(float))
    y = d["spread"].astype(float)
    model = sm.OLS(y, X).fit()
    return pd.DataFrame([{
        "model": "Spread_on_NESO_metrics",
        "n_obs": int(model.nobs),
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "beta_bid": model.params.get("bid_acceptance", np.nan),
        "beta_offer": model.params.get("offer_acceptance", np.nan),
        "beta_balancing_cost": model.params.get("balancing_cost", np.nan),
        "p_bid": model.pvalues.get("bid_acceptance", np.nan),
        "p_offer": model.pvalues.get("offer_acceptance", np.nan),
        "p_balancing_cost": model.pvalues.get("balancing_cost", np.nan),
    }])

# =========================
# ======== PLOTS ==========
# =========================
def correlation_heatmap(df_corr: pd.DataFrame):
    """Save a correlation heatmap (matplotlib, no custom colors per your org standards if needed)."""
    # reshape to matrix
    vars_ = df_corr["variable"].tolist()
    vars_uniq = sorted(set(vars_ + [c for c in df_corr.columns if c not in ("variable")]))
    # If df_corr is the melted style (variable + other columns), rebuild:
    # Simpler: re-compute directly from corr matrix writer:
    # We expect df_corr with columns: variable + metrics (wide). Let's reconstruct square:
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
    print(f"[{datetime.utcnow().isoformat()}] Loading data from BigQuery...")
    df = load_data()
    print(f"[INFO] Loaded {len(df):,} rows")

    # ===== Comparative Statistics =====
    print("[RUN] T-tests (SSP vs SBP)")
    ttest_df = ttest_ssp_sbp(df)
    write_bq(ttest_df, "ttest_results")

    print("[RUN] ANOVA by Season (SSP & SBP)")
    anova_ssp = anova_by_season(df, "SSP")
    anova_sbp = anova_by_season(df, "SBP")
    anova_all = pd.concat([anova_ssp, anova_sbp], ignore_index=True)
    write_bq(anova_all, "anova_results")

    # ===== Correlations =====
    print("[RUN] Correlation Matrix")
    corr_df = correlation_matrix(df)
    write_bq(corr_df, "correlation_matrix")
    try:
        heatmap_path = correlation_heatmap(corr_df)
        print(f"[PLOT] Correlation heatmap saved -> {heatmap_path}")
    except Exception as e:
        print(f"[WARN] Heatmap failed: {e}")

    # ===== Regression =====
    print("[RUN] OLS: Temperature -> SSP")
    reg_temp = regression_temperature_ssp(df)
    write_bq(reg_temp, "regression_temperature_ssp")

    print("[RUN] OLS: SSP vs log(Volume) + controls")
    reg_vol = regression_volume_price(df)
    write_bq(reg_vol, "regression_volume_price")

    # ===== Time Series =====
    print("[RUN] ARIMA (SARIMAX) for SSP")
    arima_df = arima_ssp(df)
    write_bq(arima_df, "arima_forecast_ssp")

    print("[RUN] Seasonal Decomposition for SSP")
    decomp_df = seasonal_decomp(df)
    write_bq(decomp_df, "seasonal_decomposition_stats")

    # ===== External Factors =====
    print("[RUN] Outage impact on spread")
    out_outage = outage_impact(df)
    write_bq(out_outage, "outage_impact_results")

    print("[RUN] NESO behavior & balancing cost analysis")
    out_neso = neso_behavior(df)
    write_bq(out_neso, "neso_behavior_results")

    print("[DONE] All analyses complete.")

if __name__ == "__main__":
    main()
