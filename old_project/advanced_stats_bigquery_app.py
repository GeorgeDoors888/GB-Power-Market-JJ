#!/usr/bin/env python3
"""
Advanced Statistical Analysis Suite for BigQuery Energy Market Data
==================================================================

Interactive Streamlit app version with date range selection and calculation buttons.

REQUIREMENTS (install once):
    pip install google-cloud-bigquery pandas numpy scipy statsmodels matplotlib pandas-gbq pyarrow streamlit plotly

OPTIONAL (GCS upload of plots):
    pip install google-cloud-storage

USAGE:
    - Update CONFIG below if needed.
    - Run: streamlit run advanced_stats_bigquery_app.py

OUTPUTS:
    - Results displayed in the Streamlit UI
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
"""

import os
import io
import math
import pathlib
import base64
from datetime import datetime, timedelta
import time

import streamlit as st
import numpy as np
import pandas as pd
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Optional imports with graceful fallback
try:
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    st.warning("statsmodels package not installed. Some advanced analyses will be disabled.")

try:
    import matplotlib
    matplotlib.use("Agg")  # headless
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    st.warning("matplotlib package not installed. Some visualizations will be disabled.")

from google.cloud import bigquery
from pandas_gbq import to_gbq

# Optional: GCS upload for plots
try:
    from google.cloud import storage as gcs_storage
    HAS_GCS = True
except Exception:
    HAS_GCS = False

# =========================
# ======= STREAMLIT =======
# =========================

st.set_page_config(
    page_title="Energy Market Advanced Statistics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Advanced Statistical Analysis Suite for Energy Market Data")

# Sidebar configuration
st.sidebar.header("Configuration")

# Project settings
with st.sidebar.expander("Project Settings", expanded=False):
    PROJECT_ID = st.text_input("GCP Project ID", value="jibber-jabber-knowledge")
    LOCATION = st.selectbox("BigQuery Location", options=["EU", "US"], index=0)
    DATASET_SOURCE = st.text_input("Source Dataset", value="uk_energy_prod")
    DATASET_ANALYTICS = st.text_input("Analytics Dataset", value="uk_energy_analytics")
    GCS_BUCKET = st.text_input("GCS Bucket (optional)", value="")

# Table settings
with st.sidebar.expander("Data Tables", expanded=False):
    TABLE_PRICES = st.text_input("Prices Table", value=f"{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services")
    TABLE_WEATHER = st.text_input("Weather Table", value=f"{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts")
    TABLE_WIND = st.text_input("Wind Table", value=f"{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts")
    TABLE_OUTAGES = st.text_input("Outages Table", value=f"{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services")
    TABLE_NESO = st.text_input("NESO Table", value=f"{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services")

# Column mappings
with st.sidebar.expander("Column Mappings", expanded=False):
    COLUMN_MAP = {
        "timestamp": st.text_input("Timestamp column", value="settlement_date"),
        "region": st.text_input("Region column", value="'UK'"),
        "ssp": st.text_input("SSP column", value="bsuos_rate_pounds_mwh"),
        "sbp": st.text_input("SBP column", value="cost_pounds"),
        "volume": st.text_input("Volume column", value="volume_mwh"),
        "temperature": st.text_input("Temperature column", value="temperature_forecast"),
        "wind_generation": st.text_input("Wind generation column", value="wind_forecast"),
        "outage_mw": st.text_input("Outage MW column", value="balancing_services_cost"),
        "unplanned": st.text_input("Unplanned outage column", value="settlement_period % 2 = 0"),
        "bid_accept": st.text_input("Bid acceptance column", value="balancing_services_cost"),
        "offer_accept": st.text_input("Offer acceptance column", value="transmission_losses_cost"),
        "balancing_cost": st.text_input("Balancing cost column", value="constraint_costs"),
    }

# Date range selection with default of last month
default_end_date = datetime.now().date()
default_start_date = default_end_date - timedelta(days=30)

# Date range picker
st.sidebar.header("Date Range Selection")
DATE_START = st.sidebar.date_input("Start Date", value=default_start_date)
DATE_END = st.sidebar.date_input("End Date", value=default_end_date)

if DATE_START >= DATE_END:
    st.sidebar.error("End date must be after start date")

# Convert to string format
DATE_START_STR = DATE_START.strftime("%Y-%m-%d")
DATE_END_STR = DATE_END.strftime("%Y-%m-%d")

# Date presets for quick selection
st.sidebar.subheader("Quick Date Ranges")
preset_cols = st.sidebar.columns(3)

with preset_cols[0]:
    if st.button("Last 7 Days"):
        DATE_END = datetime.now().date()
        DATE_START = DATE_END - timedelta(days=7)
        st.experimental_rerun()

with preset_cols[1]:
    if st.button("Last 30 Days"):
        DATE_END = datetime.now().date()
        DATE_START = DATE_END - timedelta(days=30)
        st.experimental_rerun()

with preset_cols[2]:
    if st.button("Last 90 Days"):
        DATE_END = datetime.now().date()
        DATE_START = DATE_END - timedelta(days=90)
        st.experimental_rerun()

date_range_cols = st.sidebar.columns(2)
with date_range_cols[0]:
    if st.button("Year to Date"):
        DATE_END = datetime.now().date()
        DATE_START = datetime(DATE_END.year, 1, 1).date()
        st.experimental_rerun()

with date_range_cols[1]:
    if st.button("Last Year"):
        DATE_END = datetime.now().date()
        DATE_START = datetime(DATE_END.year-1, DATE_END.month, DATE_END.day).date()
        st.experimental_rerun()

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
            st.warning(f"GCS_BUCKET set but google-cloud-storage not installed; saved locally to {local_path}")
            return str(local_path)
        client = gcs_storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(f"output/{fname}")
        with open(local_path, "rb") as f:
            blob.upload_from_file(f)
        st.success(f"Uploaded to GCS: gs://{GCS_BUCKET}/output/{fname}")
        return f"gs://{GCS_BUCKET}/output/{fname}"
    return str(local_path)

def write_bq(df: pd.DataFrame, table_name: str, if_exists="replace"):
    """Write a DataFrame to BigQuery."""
    if df is None or df.empty:
        st.warning(f"{table_name}: DataFrame is empty; skipping write.")
        return
    
    full_table = f"{PROJECT_ID}.{DATASET_ANALYTICS}.{table_name}"
    to_gbq(df, full_table, project_id=PROJECT_ID, if_exists=if_exists, location=LOCATION)
    st.success(f"Wrote {len(df):,} rows to {full_table} (if_exists={if_exists})")

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
@st.cache_data(ttl=3600, show_spinner=True)
def load_data(date_start, date_end):
    """Load and join source data from BigQuery within date range."""
    progress_text = "Loading data from BigQuery..."
    progress_bar = st.progress(0, text=progress_text)
    
    try:
        client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
        st.success(f"Connected to BigQuery project: {PROJECT_ID}")
        
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
          WHERE {COLUMN_MAP['timestamp']} >= DATE('{date_start}') 
            AND {COLUMN_MAP['timestamp']} < DATE('{date_end}')
        ),
        weather AS (
          SELECT
            {COLUMN_MAP['timestamp']} AS ts,
            {COLUMN_MAP['region']} AS region,
            {COLUMN_MAP['temperature']} AS temperature
          FROM `{TABLE_WEATHER}`
          WHERE {COLUMN_MAP['timestamp']} >= DATE('{date_start}') 
            AND {COLUMN_MAP['timestamp']} < DATE('{date_end}')
        ),
        wind AS (
          SELECT
            {COLUMN_MAP['timestamp']} AS ts,
            {COLUMN_MAP['region']} AS region,
            {COLUMN_MAP['wind_generation']} AS wind_generation
          FROM `{TABLE_WIND}`
          WHERE {COLUMN_MAP['timestamp']} >= DATE('{date_start}') 
            AND {COLUMN_MAP['timestamp']} < DATE('{date_end}')
        ),
        outages AS (
          SELECT
            {COLUMN_MAP['timestamp']} AS ts,
            {COLUMN_MAP['region']} AS region,
            {COLUMN_MAP['outage_mw']} AS outage_mw,
            CAST({COLUMN_MAP['unplanned']} AS BOOL) AS unplanned
          FROM `{TABLE_OUTAGES}`
          WHERE {COLUMN_MAP['timestamp']} >= DATE('{date_start}') 
            AND {COLUMN_MAP['timestamp']} < DATE('{date_end}')
        ),
        neso AS (
          SELECT
            {COLUMN_MAP['timestamp']} AS ts,
            {COLUMN_MAP['bid_accept']} AS bid_acceptance,
            {COLUMN_MAP['offer_accept']} AS offer_acceptance,
            {COLUMN_MAP['balancing_cost']} AS balancing_cost
          FROM `{TABLE_NESO}`
          WHERE {COLUMN_MAP['timestamp']} >= DATE('{date_start}') 
            AND {COLUMN_MAP['timestamp']} < DATE('{date_end}')
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
        
        progress_bar.progress(10, text="Query submitted to BigQuery...")
        df = client.query(sql).to_dataframe(create_bqstorage_client=True)
        progress_bar.progress(90, text="Data received, processing...")
        
        if df.empty:
            st.error("No data returned from BigQuery for the specified date range.")
            progress_bar.empty()
            return None
            
        df = df.dropna(subset=["SSP", "SBP"])
        df = add_calendar_fields(df, "ts")
        df["spread"] = df["SBP"] - df["SSP"]
        
        progress_bar.progress(100, text="Data loaded successfully!")
        time.sleep(0.5)  # Give users time to see the success message
        progress_bar.empty()
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        progress_bar.empty()
        return None

# =========================
# ====== STATISTICS =======
# =========================
def ttest_ssp_sbp(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - T-test analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner("Performing t-test analysis..."):
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
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - ANOVA analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner(f"Performing ANOVA analysis for {price_col} by season..."):
        groups = [g[price_col].dropna().values for _, g in df.groupby("season")]
        if len(groups) < 2:
            st.warning("Not enough seasonal groups for ANOVA")
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
    if df is None or df.empty:
        return None
        
    with st.spinner("Calculating correlation matrix..."):
        cols = ["SSP", "SBP", "volume", "temperature", "wind_generation", "spread", 
                "bid_acceptance", "offer_acceptance", "balancing_cost"]
        cols = [c for c in cols if c in df.columns]
        cm = df[cols].corr(method="pearson")
        cm = cm.reset_index().rename(columns={"index": "variable"})
        return cm

def regression_temperature_ssp(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - regression analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner("Performing temperature regression analysis..."):
        d = df[["SSP", "temperature"]].dropna()
        if d.empty:
            st.warning("No data available for temperature regression")
            return None
            
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

        # Create plotly figure instead of matplotlib
        fig = px.scatter(d, x="temperature", y="SSP", opacity=0.6, 
                        title="Temperature vs SSP (OLS Regression)")
        
        # Add the regression line
        xgrid = np.linspace(d["temperature"].min(), d["temperature"].max(), 200)
        yhat = summary["intercept"] + summary["slope_temperature"] * xgrid
        
        fig.add_trace(go.Scatter(
            x=xgrid, 
            y=yhat,
            mode='lines',
            name='OLS Regression',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            xaxis_title="Temperature",
            yaxis_title="SSP",
            showlegend=True
        )

        return pd.DataFrame([summary]), fig

def regression_volume_price(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - regression analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner("Performing volume-price regression analysis..."):
        # Price elasticity proxy: regress SSP on log(volume) and wind + temperature controls
        d = df[["SSP", "volume", "wind_generation", "temperature"]].dropna()
        if d.empty:
            st.warning("No data available for volume-price regression")
            return None
            
        d = d[(d["volume"] > 0)]
        d["log_volume"] = np.log(d["volume"])
        X = sm.add_constant(d[["log_volume", "wind_generation", "temperature"]].astype(float))
        y = d["SSP"].astype(float)
        model = sm.OLS(y, X).fit()
        
        result = pd.DataFrame([{
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
        
        # Create a partial dependence plot for log_volume
        partial_data = pd.DataFrame({
            'log_volume': np.linspace(d['log_volume'].min(), d['log_volume'].max(), 100)
        })
        partial_data['SSP_pred'] = (model.params['const'] + 
                                   model.params['log_volume'] * partial_data['log_volume'] +
                                   model.params['wind_generation'] * d['wind_generation'].mean() +
                                   model.params['temperature'] * d['temperature'].mean())
        
        # Create the plot
        fig = px.line(partial_data, x='log_volume', y='SSP_pred', 
                     title='Partial Dependence: log(Volume) → SSP')
        fig.update_layout(
            xaxis_title="log(Volume)",
            yaxis_title="Predicted SSP (holding other variables at mean)"
        )
        
        return result, fig

def arima_ssp(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - ARIMA analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
    
    with st.spinner("Performing ARIMA forecasting (this may take a while)..."):
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
            model = SARIMAX(y, order=order, seasonal_order=seasonal_order, 
                           enforce_stationarity=False, enforce_invertibility=False)
            res = model.fit(disp=False)
        except Exception as e:
            st.error(f"ARIMA failed: {e}")
            return None

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

        # Create Plotly figure
        fig = go.Figure()
        
        # Historical data (last week)
        hist_data = y.tail(48*7)
        fig.add_trace(go.Scatter(
            x=hist_data.index, 
            y=hist_data.values,
            mode='lines',
            name='Historical'
        ))
        
        # Forecast
        fig.add_trace(go.Scatter(
            x=pred.index, 
            y=pred.values,
            mode='lines',
            name='Forecast',
            line=dict(color='red')
        ))
        
        # Confidence interval
        fig.add_trace(go.Scatter(
            x=list(out["ts"]) + list(out["ts"])[::-1],
            y=list(out["ci_hi"]) + list(out["ci_lo"])[::-1],
            fill='toself',
            fillcolor='rgba(231,107,243,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% Confidence Interval'
        ))
        
        fig.update_layout(
            title="SSP ARIMA Forecast (next 24h, 30-min steps)",
            xaxis_title="Time",
            yaxis_title="SSP",
            showlegend=True
        )

        out["aic"] = res.aic
        out["bic"] = res.bic
        out["order"] = str(order)
        out["seasonal_order"] = str(seasonal_order)
        return out, fig

def seasonal_decomp(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - seasonal decomposition disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner("Performing seasonal decomposition..."):
        d = df[["ts", "SSP"]].dropna().copy()
        d["ts"] = pd.to_datetime(d["ts"])
        d = d.set_index("ts").sort_index()
        y = d["SSP"].asfreq("30min").interpolate(limit_direction="both")
        period = 48 * 7  # weekly seasonal period for 30-min data
        
        try:
            decomp = seasonal_decompose(y, model="additive", period=period, 
                                      two_sided=False, extrapolate_trend="freq")
        except Exception as e:
            st.error(f"Seasonal decomposition failed: {e}")
            return None

        # Create Plotly figure with subplots
        fig = make_subplots(rows=4, cols=1, 
                          subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
                          shared_xaxes=True,
                          vertical_spacing=0.05)
        
        # Add observed data
        fig.add_trace(go.Scatter(
            x=y.index, y=y.values, name="Observed", mode="lines"
        ), row=1, col=1)
        
        # Add trend
        fig.add_trace(go.Scatter(
            x=decomp.trend.index, y=decomp.trend.values, name="Trend", mode="lines"
        ), row=2, col=1)
        
        # Add seasonal
        fig.add_trace(go.Scatter(
            x=decomp.seasonal.index, y=decomp.seasonal.values, name="Seasonal", mode="lines"
        ), row=3, col=1)
        
        # Add residual
        fig.add_trace(go.Scatter(
            x=decomp.resid.index, y=decomp.resid.values, name="Residual", mode="lines"
        ), row=4, col=1)
        
        fig.update_layout(
            height=800,
            title="Seasonal Decomposition of SSP",
            showlegend=False
        )

        stats_out = pd.DataFrame([{
            "period": period,
            "obs_count": len(y),
            "trend_var": np.nanvar(decomp.trend.values),
            "seasonal_var": np.nanvar(decomp.seasonal.values),
            "resid_var": np.nanvar(decomp.resid.values)
        }])
        
        return stats_out, fig

def outage_impact(df: pd.DataFrame):
    if df is None or df.empty:
        return None
        
    with st.spinner("Analyzing outage impact..."):
        """Quantify unplanned outage effects on spread."""
        d = df[["spread", "outage_mw", "unplanned"]].dropna()
        if d.empty:
            st.warning("No data available for outage impact analysis")
            return None
            
        d["has_unplanned"] = d["unplanned"].astype(bool)
        a = d.loc[d["has_unplanned"], "spread"].values
        b = d.loc[~d["has_unplanned"], "spread"].values
        
        if len(a) < 2 or len(b) < 2:
            st.warning("Insufficient data in one or both outage groups")
            return None
            
        tstat, pval = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
        
        result = pd.DataFrame([{
            "metric": "spread_with_unplanned_outage",
            "mean_with_outage": np.nanmean(a),
            "mean_without_outage": np.nanmean(b),
            "mean_diff": np.nanmean(a) - np.nanmean(b),
            "t_stat": tstat,
            "p_value": pval,
            "n_with": int(np.isfinite(a).sum()),
            "n_without": int(np.isfinite(b).sum())
        }])
        
        # Create a box plot comparing the distributions
        outage_data = [
            go.Box(y=a, name="With Unplanned Outage", boxmean=True),
            go.Box(y=b, name="Without Unplanned Outage", boxmean=True)
        ]
        
        fig = go.Figure(data=outage_data)
        fig.update_layout(
            title="Price Spread Distribution by Outage Status",
            yaxis_title="Price Spread",
            boxmode="group"
        )
        
        return result, fig

def neso_behavior(df: pd.DataFrame):
    if not HAS_STATSMODELS:
        st.warning("statsmodels not installed - NESO behavior analysis disabled")
        return None
        
    if df is None or df.empty:
        return None
        
    with st.spinner("Analyzing NESO behavior..."):
        """NESO bid/offer acceptance & balancing cost relationships."""
        cols = ["SSP", "SBP", "spread", "bid_acceptance", "offer_acceptance", "balancing_cost"]
        d = df[cols].dropna()
        if d.empty:
            st.warning("No data available for NESO behavior analysis")
            return None
            
        # Simple elasticity proxy: spread vs bid/offer acceptance & balancing cost
        X = sm.add_constant(d[["bid_acceptance", "offer_acceptance", "balancing_cost"]].astype(float))
        y = d["spread"].astype(float)
        model = sm.OLS(y, X).fit()
        
        result = pd.DataFrame([{
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
        
        # Create scatter plot of actual vs predicted values
        y_pred = model.predict(X)
        
        fig = px.scatter(
            x=y, y=y_pred, 
            labels={"x": "Actual Spread", "y": "Predicted Spread"},
            title="NESO Model: Actual vs Predicted Spread"
        )
        
        # Add 45-degree line (perfect prediction)
        min_val = min(y.min(), y_pred.min())
        max_val = max(y.max(), y_pred.max())
        fig.add_trace(
            go.Scatter(
                x=[min_val, max_val],
                y=[min_val, max_val],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="Perfect Prediction"
            )
        )
        
        return result, fig

# =========================
# ======== PLOTS ==========
# =========================
def correlation_heatmap(df_corr: pd.DataFrame):
    """Create a correlation heatmap with Plotly."""
    if df_corr is None:
        return None
        
    with st.spinner("Creating correlation heatmap..."):
        cols = [c for c in df_corr.columns if c != "variable"]
        mat = df_corr.set_index("variable")[cols]
        
        fig = px.imshow(
            mat.values,
            x=cols,
            y=mat.index,
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Correlation Matrix (Pearson)"
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            width=800,
            height=700
        )
        
        return fig

# =========================
# ===== UI COMPONENTS =====
# =========================

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Data Overview",
    "Basic Statistics", 
    "Regression Analysis", 
    "Time Series Analysis", 
    "External Factors"
])

# Data Overview tab
with tab1:
    st.header("Data Overview")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("Load Data", key="load_data_btn", type="primary"):
            df = load_data(DATE_START_STR, DATE_END_STR)
            if df is not None:
                st.session_state["data"] = df
                st.success(f"Loaded {len(df):,} rows of data for period {DATE_START_STR} to {DATE_END_STR}")
    
    with col2:
        # Show date range for context
        st.info(f"Date Range: {DATE_START_STR} to {DATE_END_STR}")
    
    if "data" in st.session_state and st.session_state["data"] is not None:
        df = st.session_state["data"]
        
        st.subheader("Preview of Loaded Data")
        st.dataframe(df.head(10))
        
        st.subheader("Summary Statistics")
        st.dataframe(df.describe())
        
        # Show data availability by columns
        st.subheader("Data Availability")
        availability = pd.DataFrame({
            'Column': df.columns,
            'Non-Null Count': df.count().values,
            'Null Count': df.isnull().sum().values,
            'Percentage Complete': (df.count() / len(df) * 100).values.round(2)
        })
        st.dataframe(availability)
        
        # Simple time series plot
        st.subheader("SSP/SBP Time Series")
        ts_fig = px.line(df, x="ts", y=["SSP", "SBP"], title="SSP and SBP Over Time")
        ts_fig.update_layout(xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(ts_fig, use_container_width=True)

# Basic Statistics tab
with tab2:
    st.header("Basic Statistical Analysis")
    
    if "data" not in st.session_state or st.session_state["data"] is None:
        st.warning("Please load data first from the Data Overview tab.")
    else:
        df = st.session_state["data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run T-Test (SSP vs SBP)", key="ttest_btn"):
                ttest_results = ttest_ssp_sbp(df)
                if ttest_results is not None:
                    st.session_state["ttest_results"] = ttest_results
                    
                    if st.checkbox("Write to BigQuery", key="write_ttest"):
                        write_bq(ttest_results, "ttest_results")
        
        with col2:
            if st.button("Run ANOVA by Season", key="anova_btn"):
                anova_ssp = anova_by_season(df, "SSP")
                anova_sbp = anova_by_season(df, "SBP")
                
                if anova_ssp is not None and anova_sbp is not None:
                    anova_all = pd.concat([anova_ssp, anova_sbp], ignore_index=True)
                    st.session_state["anova_results"] = anova_all
                    
                    if st.checkbox("Write to BigQuery", key="write_anova"):
                        write_bq(anova_all, "anova_results")
        
        # Correlation analysis
        if st.button("Calculate Correlation Matrix", key="corr_btn"):
            corr_df = correlation_matrix(df)
            if corr_df is not None:
                st.session_state["corr_results"] = corr_df
                
                # Generate heatmap
                heatmap_fig = correlation_heatmap(corr_df)
                if heatmap_fig is not None:
                    st.session_state["heatmap_fig"] = heatmap_fig
                
                if st.checkbox("Write to BigQuery", key="write_corr"):
                    write_bq(corr_df, "correlation_matrix")
        
        # Show results if available
        if "ttest_results" in st.session_state:
            st.subheader("T-Test Results: SSP vs SBP")
            df_ttest = st.session_state["ttest_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mean SSP", f"{df_ttest['mean_SSP'].values[0]:.2f}")
            with col2:
                st.metric("Mean SBP", f"{df_ttest['mean_SBP'].values[0]:.2f}")
            with col3:
                st.metric("p-value", f"{df_ttest['p_value'].values[0]:.4f}")
            
            st.dataframe(df_ttest)
            
            # Visual comparison of means with confidence interval
            ttest_fig = go.Figure()
            ttest_fig.add_trace(go.Bar(
                x=['SSP', 'SBP'],
                y=[df_ttest['mean_SSP'].values[0], df_ttest['mean_SBP'].values[0]],
                error_y=dict(
                    type='data',
                    array=[
                        1.96 * np.nanstd(df['SSP']) / np.sqrt(df_ttest['n_SSP'].values[0]),
                        1.96 * np.nanstd(df['SBP']) / np.sqrt(df_ttest['n_SBP'].values[0])
                    ],
                    visible=True
                )
            ))
            ttest_fig.update_layout(
                title="Comparison of SSP and SBP Means (with 95% CI)",
                xaxis_title="Price Type",
                yaxis_title="Price Value"
            )
            st.plotly_chart(ttest_fig, use_container_width=True)
        
        if "anova_results" in st.session_state:
            st.subheader("ANOVA Results by Season")
            df_anova = st.session_state["anova_results"]
            st.dataframe(df_anova)
            
            # Visualize means by season
            for price_col in df_anova['price_col'].unique():
                row = df_anova[df_anova['price_col'] == price_col].iloc[0]
                
                anova_fig = go.Figure()
                anova_fig.add_trace(go.Bar(
                    x=row['group_names'],
                    y=row['group_means'],
                    text=[f"n={size}" for size in row['group_sizes']],
                    textposition='auto'
                ))
                anova_fig.update_layout(
                    title=f"{price_col} by Season (F={row['f_stat']:.2f}, p={row['p_value']:.4f})",
                    xaxis_title="Season",
                    yaxis_title=price_col
                )
                st.plotly_chart(anova_fig, use_container_width=True)
        
        if "heatmap_fig" in st.session_state:
            st.subheader("Correlation Matrix")
            st.plotly_chart(st.session_state["heatmap_fig"], use_container_width=True)
            
            if "corr_results" in st.session_state:
                with st.expander("View Correlation Data"):
                    st.dataframe(st.session_state["corr_results"])

# Regression Analysis tab
with tab3:
    st.header("Regression Analysis")
    
    if "data" not in st.session_state or st.session_state["data"] is None:
        st.warning("Please load data first from the Data Overview tab.")
    else:
        df = st.session_state["data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Temperature → SSP Regression", key="temp_reg_btn"):
                result = regression_temperature_ssp(df)
                if result is not None:
                    temp_reg_df, temp_reg_fig = result
                    st.session_state["temp_reg_results"] = temp_reg_df
                    st.session_state["temp_reg_fig"] = temp_reg_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_temp_reg"):
                        write_bq(temp_reg_df, "regression_temperature_ssp")
        
        with col2:
            if st.button("Run Volume-Price Regression", key="vol_reg_btn"):
                result = regression_volume_price(df)
                if result is not None:
                    vol_reg_df, vol_reg_fig = result
                    st.session_state["vol_reg_results"] = vol_reg_df
                    st.session_state["vol_reg_fig"] = vol_reg_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_vol_reg"):
                        write_bq(vol_reg_df, "regression_volume_price")
        
        # Show results if available
        if "temp_reg_results" in st.session_state and "temp_reg_fig" in st.session_state:
            st.subheader("Temperature → SSP Regression Results")
            
            df_temp_reg = st.session_state["temp_reg_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("R²", f"{df_temp_reg['r_squared'].values[0]:.4f}")
            with col2:
                st.metric("Intercept", f"{df_temp_reg['intercept'].values[0]:.2f}")
            with col3:
                st.metric("Temperature Slope", f"{df_temp_reg['slope_temperature'].values[0]:.4f}")
            
            with st.expander("View Full Regression Results"):
                st.dataframe(df_temp_reg)
            
            st.plotly_chart(st.session_state["temp_reg_fig"], use_container_width=True)
        
        if "vol_reg_results" in st.session_state and "vol_reg_fig" in st.session_state:
            st.subheader("Volume-Price Regression Results")
            
            df_vol_reg = st.session_state["vol_reg_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("R²", f"{df_vol_reg['r_squared'].values[0]:.4f}")
            with col2:
                st.metric("Log(Volume) Coefficient", f"{df_vol_reg['beta_log_volume'].values[0]:.4f}")
            with col3:
                p_val = df_vol_reg['p_log_volume'].values[0]
                st.metric("p-value", f"{p_val:.4f}", delta="Significant" if p_val < 0.05 else "Not Significant")
            
            with st.expander("View Full Regression Results"):
                st.dataframe(df_vol_reg)
            
            st.plotly_chart(st.session_state["vol_reg_fig"], use_container_width=True)

# Time Series Analysis tab
with tab4:
    st.header("Time Series Analysis")
    
    if "data" not in st.session_state or st.session_state["data"] is None:
        st.warning("Please load data first from the Data Overview tab.")
    else:
        df = st.session_state["data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run ARIMA Forecast", key="arima_btn"):
                result = arima_ssp(df)
                if result is not None:
                    arima_df, arima_fig = result
                    st.session_state["arima_results"] = arima_df
                    st.session_state["arima_fig"] = arima_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_arima"):
                        write_bq(arima_df, "arima_forecast_ssp")
        
        with col2:
            if st.button("Run Seasonal Decomposition", key="decomp_btn"):
                result = seasonal_decomp(df)
                if result is not None:
                    decomp_df, decomp_fig = result
                    st.session_state["decomp_results"] = decomp_df
                    st.session_state["decomp_fig"] = decomp_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_decomp"):
                        write_bq(decomp_df, "seasonal_decomposition_stats")
        
        # Show results if available
        if "arima_results" in st.session_state and "arima_fig" in st.session_state:
            st.subheader("ARIMA Forecast Results")
            
            with st.expander("View ARIMA Forecast Data"):
                st.dataframe(st.session_state["arima_results"])
            
            st.plotly_chart(st.session_state["arima_fig"], use_container_width=True)
        
        if "decomp_results" in st.session_state and "decomp_fig" in st.session_state:
            st.subheader("Seasonal Decomposition Results")
            
            df_decomp = st.session_state["decomp_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trend Variance", f"{df_decomp['trend_var'].values[0]:.2f}")
            with col2:
                st.metric("Seasonal Variance", f"{df_decomp['seasonal_var'].values[0]:.2f}")
            with col3:
                st.metric("Residual Variance", f"{df_decomp['resid_var'].values[0]:.2f}")
            
            with st.expander("View Full Decomposition Stats"):
                st.dataframe(df_decomp)
            
            st.plotly_chart(st.session_state["decomp_fig"], use_container_width=True)

# External Factors tab
with tab5:
    st.header("External Factors Analysis")
    
    if "data" not in st.session_state or st.session_state["data"] is None:
        st.warning("Please load data first from the Data Overview tab.")
    else:
        df = st.session_state["data"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Analyze Outage Impact", key="outage_btn"):
                result = outage_impact(df)
                if result is not None:
                    outage_df, outage_fig = result
                    st.session_state["outage_results"] = outage_df
                    st.session_state["outage_fig"] = outage_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_outage"):
                        write_bq(outage_df, "outage_impact_results")
        
        with col2:
            if st.button("Analyze NESO Behavior", key="neso_btn"):
                result = neso_behavior(df)
                if result is not None:
                    neso_df, neso_fig = result
                    st.session_state["neso_results"] = neso_df
                    st.session_state["neso_fig"] = neso_fig
                    
                    if st.checkbox("Write to BigQuery", key="write_neso"):
                        write_bq(neso_df, "neso_behavior_results")
        
        # Show results if available
        if "outage_results" in st.session_state and "outage_fig" in st.session_state:
            st.subheader("Outage Impact Analysis")
            
            df_outage = st.session_state["outage_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Mean With Outage", f"{df_outage['mean_with_outage'].values[0]:.2f}")
            with col2:
                st.metric("Mean Without Outage", f"{df_outage['mean_without_outage'].values[0]:.2f}")
            with col3:
                p_val = df_outage['p_value'].values[0]
                significance = "Significant" if p_val < 0.05 else "Not Significant"
                st.metric("p-value", f"{p_val:.4f}", delta=significance)
            
            with st.expander("View Full Outage Impact Results"):
                st.dataframe(df_outage)
            
            st.plotly_chart(st.session_state["outage_fig"], use_container_width=True)
        
        if "neso_results" in st.session_state and "neso_fig" in st.session_state:
            st.subheader("NESO Behavior Analysis")
            
            df_neso = st.session_state["neso_results"]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("R²", f"{df_neso['r_squared'].values[0]:.4f}")
            with col2:
                st.metric("Balancing Cost Effect", f"{df_neso['beta_balancing_cost'].values[0]:.4f}")
            with col3:
                p_val = df_neso['p_balancing_cost'].values[0]
                significance = "Significant" if p_val < 0.05 else "Not Significant"
                st.metric("p-value", f"{p_val:.4f}", delta=significance)
            
            with st.expander("View Full NESO Behavior Results"):
                st.dataframe(df_neso)
            
            st.plotly_chart(st.session_state["neso_fig"], use_container_width=True)

# =========================
# ====== FOOTER ===========
# =========================
st.markdown("---")
st.markdown("""
<div style="text-align: center">
<p>Advanced Statistical Analysis Suite for Energy Market Data | v1.0.0</p>
<p>Data date range: {start} to {end}</p>
</div>
""".format(start=DATE_START_STR, end=DATE_END_STR), unsafe_allow_html=True)
