# -*- coding: utf-8 -*-
"""
Advanced Statistical Analysis Suite for BigQuery UK Energy Data
================================================================

PURPOSE:
    Comprehensive statistical analysis for GB power market operations including:
    - Battery storage optimization (charge/discharge scheduling)
    - Solar PV revenue forecasting and curtailment planning
    - Market modeling (price elasticity, supply-demand dynamics)
    - Transmission cost optimization (DUoS/BSUoS/TNUoS)

OUTPUTS (written to BigQuery):
    1. ttest_results             - SSP vs SBP statistical comparison
    2. regression_temperature_ssp - Weather impact on prices
    3. regression_volume_price    - Multi-factor price drivers
    4. correlation_matrix         - Variable relationships + heatmap
    5. arima_forecast_ssp         - 24h SSP forecast with CI
    6. seasonal_decomposition_stats - Trend/seasonal/residual components
    7. outage_impact_results      - Event-day stress testing
    8. neso_behavior_results      - Balancing cost linkage
    9. anova_results              - Seasonal pricing regimes

REQUIREMENTS:
    pip install google-cloud-bigquery google-cloud-storage pandas numpy scipy
    pip install statsmodels matplotlib pandas-gbq pyarrow db-dtypes

USAGE:
    # Basic run:
    python advanced_statistical_analysis.py

    # Custom date range:
    python advanced_statistical_analysis.py --start 2024-01-01 --end 2025-10-31

    # Skip plots (faster):
    python advanced_statistical_analysis.py --no-plots

DOCUMENTATION:
    See STATISTICAL_ANALYSIS_GUIDE.md for detailed interpretation of each output

AUTHOR: GB Power Market Analytics Team
DATE: October 31, 2025
REPOSITORY: https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop
"""

import argparse
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # Headless mode for server deployment
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX

from google.cloud import bigquery
from pandas_gbq import to_gbq

# Optional GCS for plot storage
try:
    from google.cloud import storage as gcs_storage
    HAS_GCS = True
except ImportError:
    HAS_GCS = False
    warnings.warn("google-cloud-storage not installed; plots will be saved locally only")

# Suppress statsmodels convergence warnings (expected for some ARIMA fits)
warnings.filterwarnings('ignore', category=UserWarning, module='statsmodels')

# =========================
# ========= CONFIG ========
# =========================

# BigQuery projects and datasets
PROJECT_ID = "inner-cinema-476211-u9"  # ✅ FIXED: Changed from jibber-jabber-knowledge
LOCATION = "US"  # Dataset location - US for inner-cinema-476211-u9
DATASET_SOURCE = "uk_energy_prod"  # Source tables (bmrs_*, etc.)
DATASET_ANALYTICS = "uk_energy_analysis"  # Output tables

# GCS bucket for plots (empty string = save locally only)
GCS_BUCKET = ""  # e.g., "jibber-jabber-knowledge-bmrs-data"

# Analysis date range (can be overridden via CLI)
DATE_START = "2019-01-01"
DATE_END = "2025-10-31"

# Output directory for local plots
OUTDIR = Path("./statistical_analysis_output")
OUTDIR.mkdir(exist_ok=True)

# =========================
# ===== UTILITIES =========
# =========================

def log(msg: str, level: str = "INFO"):
    """Timestamped logging"""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def save_plot(fig, fname: str, enable_plots: bool = True) -> str:
    """
    Save plot locally and optionally to GCS
    
    Args:
        fig: matplotlib figure
        fname: filename (e.g., "correlation_heatmap.png")
        enable_plots: if False, skip plot generation (for faster runs)
    
    Returns:
        Path to saved plot (local or GCS URI)
    """
    if not enable_plots:
        plt.close(fig)
        return "plots_disabled"
    
    local_path = OUTDIR / fname
    try:
        fig.savefig(local_path, bbox_inches="tight", dpi=150)
        log(f"Plot saved locally: {local_path}")
    except Exception as e:
        log(f"Failed to save plot locally: {e}", "ERROR")
        plt.close(fig)
        return "error_saving_plot"
    finally:
        plt.close(fig)
    
    # Upload to GCS if configured
    if GCS_BUCKET and HAS_GCS:
        try:
            client = gcs_storage.Client(project=PROJECT_ID)
            blob = client.bucket(GCS_BUCKET).blob(f"statistical_analysis/{fname}")
            with open(local_path, "rb") as f:
                blob.upload_from_file(f)
            gcs_path = f"gs://{GCS_BUCKET}/statistical_analysis/{fname}"
            log(f"Plot uploaded to GCS: {gcs_path}")
            return gcs_path
        except Exception as e:
            log(f"Failed to upload to GCS: {e}", "WARN")
            return str(local_path)
    
    return str(local_path)

def write_bq(df: pd.DataFrame, table_name: str, if_exists: str = "replace"):
    """
    Write DataFrame to BigQuery
    
    Args:
        df: Data to write
        table_name: Target table name (without dataset prefix)
        if_exists: 'replace', 'append', or 'fail'
    """
    if df is None or df.empty:
        log(f"{table_name}: No data to write (empty DataFrame)", "WARN")
        return
    
    full_table = f"{PROJECT_ID}.{DATASET_ANALYTICS}.{table_name}"
    
    try:
        # Add metadata columns
        df = df.copy()
        df["_analysis_run_timestamp"] = datetime.utcnow()
        df["_analysis_date_range"] = f"{DATE_START} to {DATE_END}"
        
        to_gbq(
            df, 
            full_table, 
            project_id=PROJECT_ID, 
            if_exists=if_exists, 
            location=LOCATION
        )
        log(f"✅ Wrote {len(df):,} rows → {full_table}")
    except Exception as e:
        log(f"Failed to write {table_name}: {e}", "ERROR")
        raise

def add_calendar_features(df: pd.DataFrame, ts_col: str = "ts") -> pd.DataFrame:
    """
    Add calendar features for time-based analysis
    
    Features added:
        - month (1-12)
        - dow (day of week, 0=Monday)
        - is_weekend (bool)
        - season (Winter/Spring/Summer/Autumn)
        - hour (0-23)
        - settlement_period (1-48)
    """
    ts = pd.to_datetime(df[ts_col])
    df["month"] = ts.dt.month
    df["dow"] = ts.dt.dayofweek
    df["is_weekend"] = df["dow"] >= 5
    df["hour"] = ts.dt.hour
    
    # Settlement period (1-48, 30-min intervals)
    minutes_since_midnight = ts.dt.hour * 60 + ts.dt.minute
    df["settlement_period"] = (minutes_since_midnight // 30) + 1
    
    # Season mapping
    def get_season(month):
        if month in (12, 1, 2):
            return "Winter"
        elif month in (3, 4, 5):
            return "Spring"
        elif month in (6, 7, 8):
            return "Summer"
        else:
            return "Autumn"
    
    df["season"] = df["month"].apply(get_season)
    
    return df

def check_table_exists(client: bigquery.Client, table_ref: str) -> bool:
    """Check if BigQuery table exists"""
    try:
        client.get_table(table_ref)
        return True
    except Exception:
        return False

# =========================
# ====== DATA LOAD ========
# =========================

def load_harmonised_data(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Build harmonised 30-min time series with all required features
    
    Features included:
        - SSP, SBP, spread (from prices or BOD)
        - volume (MWh per settlement period from demand)
        - temperature (from NESO forecasts)
        - wind_generation (from NESO wind forecasts)
        - unplanned_event, severe_event (from system warnings)
        - balancing_cost, balancing_cost_per_mwh (from NESO balancing)
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD, exclusive)
    
    Returns:
        DataFrame with harmonised 30-min time series
    """
    log(f"Loading data for {start_date} to {end_date}...")
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Check if dedicated prices table exists
    prices_table = f"{PROJECT_ID}.{DATASET_SOURCE}.prices"
    has_prices = check_table_exists(client, prices_table)
    
    if not has_prices:
        log("No prices table found; will derive from BOD acceptances", "WARN")
    
    # Build SQL query
    sql = build_harmonised_query(start_date, end_date, has_prices)
    
    try:
        log("Executing BigQuery query...")
        df = client.query(sql).to_dataframe(create_bqstorage_client=True)
        log(f"✅ Retrieved {len(df):,} rows from BigQuery")
    except Exception as e:
        log(f"Query failed: {e}", "ERROR")
        raise
    
    if df.empty:
        raise ValueError(f"No data returned for date range {start_date} to {end_date}")
    
    # Clean and process
    df = df.dropna(subset=["SSP", "SBP"], how="all")
    df = add_calendar_features(df, "ts")
    
    log(f"✅ Data prepared: {len(df):,} rows with {len(df.columns)} features")
    return df

def build_harmonised_query(start_date: str, end_date: str, has_prices: bool) -> str:
    """
    Build SQL query for harmonised data load
    
    Strategy:
        - Use dedicated prices table if available
        - Otherwise derive volume-weighted average from BOD
        - LEFT JOIN all other features (temperature, wind, warnings, balancing)
    """
    
    # Settlement period clock (for aligning timestamps)
    sp_clock = f"""
    SELECT
        settlement_date,
        settlement_period,
        TIMESTAMP_ADD(
            TIMESTAMP(DATETIME(settlement_date)), 
            INTERVAL (settlement_period - 1) * 30 MINUTE
        ) AS ts
    FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_bid_offer_acceptances`
    WHERE settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
    GROUP BY settlement_date, settlement_period
    """
    
    # Price data (from table or BOD calculation)
    if has_prices:
        price_cte = f"""
        prices_raw AS (
            SELECT 
                TIMESTAMP(ts) AS ts,
                CAST(SSP AS FLOAT64) AS SSP,
                CAST(SBP AS FLOAT64) AS SBP
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.prices`
            WHERE ts >= TIMESTAMP('{start_date}') 
                AND ts < TIMESTAMP('{end_date}')
        ),
        prices AS (
            SELECT ts, SSP, SBP 
            FROM prices_raw
        )
        """
    else:
        price_cte = f"""
        bod AS (
            SELECT
                settlement_date,
                settlement_period,
                -- SBP = volume-weighted average of accepted offers
                SUM(CASE WHEN accepted_offer_volume > 0 
                    THEN offer_price * accepted_offer_volume END)
                / NULLIF(SUM(CASE WHEN accepted_offer_volume > 0 
                    THEN accepted_offer_volume END), 0) AS SBP,
                -- SSP = volume-weighted average of accepted bids
                SUM(CASE WHEN accepted_bid_volume > 0 
                    THEN bid_price * accepted_bid_volume END)
                / NULLIF(SUM(CASE WHEN accepted_bid_volume > 0 
                    THEN accepted_bid_volume END), 0) AS SSP
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_bid_offer_acceptances`
            WHERE settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            GROUP BY settlement_date, settlement_period
        ),
        sp_clock AS ({sp_clock}),
        prices AS (
            SELECT c.ts, b.SSP, b.SBP
            FROM sp_clock c
            LEFT JOIN bod b USING (settlement_date, settlement_period)
        )
        """
    
    # Temperature (from NESO demand forecasts)
    temp_cte = f"""
    temp AS (
        SELECT 
            c.ts,
            AVG(f.temperature_forecast) AS temperature
        FROM (
            SELECT 
                settlement_date, 
                settlement_period,
                TIMESTAMP_ADD(
                    TIMESTAMP(DATETIME(settlement_date)), 
                    INTERVAL (settlement_period - 1) * 30 MINUTE
                ) AS ts
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts`
            WHERE settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            GROUP BY settlement_date, settlement_period
        ) c
        LEFT JOIN `{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts` f 
            USING (settlement_date, settlement_period)
        WHERE f.settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY c.ts
    )
    """
    
    # Wind generation (from NESO wind forecasts)
    wind_cte = f"""
    wind AS (
        SELECT 
            c.ts,
            AVG(COALESCE(w.actual_output_mw, w.forecast_output_mw)) AS wind_generation
        FROM (
            SELECT 
                settlement_date, 
                settlement_period,
                TIMESTAMP_ADD(
                    TIMESTAMP(DATETIME(settlement_date)), 
                    INTERVAL (settlement_period - 1) * 30 MINUTE
                ) AS ts
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
            WHERE settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            GROUP BY settlement_date, settlement_period
        ) c
        LEFT JOIN `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts` w 
            USING (settlement_date, settlement_period)
        WHERE w.settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY c.ts
    )
    """
    
    # Volume (demand × 0.5 hours = MWh per settlement period)
    volume_cte = f"""
    volume AS (
        SELECT 
            c.ts,
            AVG(d.national_demand) * 0.5 AS volume
        FROM (
            SELECT 
                settlement_date, 
                settlement_period,
                TIMESTAMP_ADD(
                    TIMESTAMP(DATETIME(settlement_date)), 
                    INTERVAL (settlement_period - 1) * 30 MINUTE
                ) AS ts
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_demand_outturn`
            WHERE settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            GROUP BY settlement_date, settlement_period
        ) c
        LEFT JOIN `{PROJECT_ID}.{DATASET_SOURCE}.elexon_demand_outturn` d 
            USING (settlement_date, settlement_period)
        WHERE d.settlement_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY c.ts
    )
    """
    
    # System warnings (unplanned events, severe events)
    warnings_cte = f"""
    warnings AS (
        WITH event_windows AS (
            SELECT 
                TIMESTAMP(timestamp) AS ts_start,
                TIMESTAMP(COALESCE(end_time, timestamp)) AS ts_end,
                COALESCE(severity, 'UNKNOWN') AS severity
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_system_warnings`
            WHERE DATE(timestamp) BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        ),
        time_grid AS (
            SELECT ts
            FROM UNNEST(
                GENERATE_TIMESTAMP_ARRAY(
                    TIMESTAMP('{start_date}'),
                    TIMESTAMP('{end_date}'),
                    INTERVAL 30 MINUTE
                )
            ) AS ts
        )
        SELECT 
            g.ts,
            MAX(CASE WHEN g.ts BETWEEN e.ts_start AND e.ts_end 
                THEN 1 ELSE 0 END) > 0 AS unplanned_event,
            MAX(CASE WHEN g.ts BETWEEN e.ts_start AND e.ts_end 
                    AND e.severity = 'HIGH' 
                THEN 1 ELSE 0 END) > 0 AS severe_event
        FROM time_grid g
        LEFT JOIN event_windows e ON g.ts BETWEEN e.ts_start AND e.ts_end
        GROUP BY g.ts
    )
    """
    
    # Balancing costs (from NESO balancing services)
    balancing_cte = f"""
    balancing AS (
        SELECT 
            c.ts,
            SUM(b.cost_pounds) AS balancing_cost,
            SAFE_DIVIDE(
                SUM(b.cost_pounds), 
                NULLIF(SUM(b.volume_mwh), 0)
            ) AS balancing_cost_per_mwh
        FROM (
            SELECT 
                charge_date AS settlement_date, 
                settlement_period,
                TIMESTAMP_ADD(
                    TIMESTAMP(DATETIME(charge_date)), 
                    INTERVAL (settlement_period - 1) * 30 MINUTE
                ) AS ts
            FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services`
            WHERE charge_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
            GROUP BY settlement_date, settlement_period
        ) c
        LEFT JOIN `{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services` b 
            ON c.settlement_date = b.charge_date AND c.settlement_period = b.settlement_period
        WHERE b.charge_date BETWEEN DATE('{start_date}') AND DATE('{end_date}')
        GROUP BY c.ts
    )
    """
    
    # Main query: join all CTEs
    # Build the CTE list properly to avoid trailing commas
    ctes = []
    if not has_prices:
        ctes.append(price_cte)
    else:
        prices_clause = f'prices AS (SELECT ts, SSP, SBP FROM `{prices_table}` WHERE ts >= TIMESTAMP(\'{start_date}\') AND ts < TIMESTAMP(\'{end_date}\'))'
        ctes.append(prices_clause)
    
    ctes.extend([temp_cte, wind_cte, volume_cte, warnings_cte, balancing_cte])
    ctes_str = ',\n'.join(ctes)
    
    main_query = f"""
    WITH 
        {ctes_str}
    
    SELECT
        p.ts,
        p.SSP,
        p.SBP,
        (p.SBP - p.SSP) AS spread,
        v.volume,
        t.temperature,
        w.wind_generation,
        warn.unplanned_event,
        warn.severe_event,
        bal.balancing_cost,
        bal.balancing_cost_per_mwh
    FROM prices p
    LEFT JOIN volume v USING (ts)
    LEFT JOIN temp t USING (ts)
    LEFT JOIN wind w USING (ts)
    LEFT JOIN warnings warn USING (ts)
    LEFT JOIN balancing bal USING (ts)
    WHERE p.ts >= TIMESTAMP('{start_date}') 
        AND p.ts < TIMESTAMP('{end_date}')
    ORDER BY p.ts
    """
    
    return main_query

# =========================
# ====== ANALYTICS ========
# =========================

def analyze_ttest_ssp_sbp(df: pd.DataFrame) -> pd.DataFrame:
    """
    1) T-test: SSP vs SBP
    
    Tests if System Sell Price differs significantly from System Buy Price.
    The spread (SBP - SSP) is the arbitrage window for battery storage.
    
    Returns DataFrame with test statistics and confidence intervals.
    """
    log("Running t-test: SSP vs SBP")
    
    if not {"SSP", "SBP"}.issubset(df.columns):
        log("Missing SSP or SBP columns", "WARN")
        return pd.DataFrame()
    
    ssp = pd.to_numeric(df["SSP"], errors="coerce").dropna().values
    sbp = pd.to_numeric(df["SBP"], errors="coerce").dropna().values
    
    if len(ssp) < 3 or len(sbp) < 3:
        log("Insufficient data for t-test", "WARN")
        return pd.DataFrame()
    
    # Welch's t-test (unequal variances)
    t_stat, p_value = stats.ttest_ind(ssp, sbp, equal_var=False, nan_policy="omit")
    
    mean_ssp = float(np.nanmean(ssp))
    mean_sbp = float(np.nanmean(sbp))
    mean_diff = mean_sbp - mean_ssp
    
    # 95% confidence interval
    s_ssp = np.nanstd(ssp, ddof=1)
    s_sbp = np.nanstd(sbp, ddof=1)
    n_ssp = len(ssp)
    n_sbp = len(sbp)
    se = np.sqrt(s_ssp**2 / n_ssp + s_sbp**2 / n_sbp)
    ci_lo = mean_diff - 1.96 * se
    ci_hi = mean_diff + 1.96 * se
    
    result = pd.DataFrame([{
        "metric": "SSP_vs_SBP",
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "mean_SSP": mean_ssp,
        "mean_SBP": mean_sbp,
        "mean_diff": mean_diff,
        "ci_95_lo": float(ci_lo),
        "ci_95_hi": float(ci_hi),
        "std_SSP": float(s_ssp),
        "std_SBP": float(s_sbp),
        "n_SSP": n_ssp,
        "n_SBP": n_sbp
    }])
    
    log(f"  Mean diff (SBP - SSP): £{mean_diff:.2f}/MWh (p={p_value:.4f})")
    return result

def analyze_regression_temperature_ssp(df: pd.DataFrame, enable_plots: bool = True) -> pd.DataFrame:
    """
    2) Regression: Temperature → SSP
    
    OLS model: SSP = β₀ + β₁ × Temperature + ε
    
    Shows how ambient temperature affects System Sell Price.
    Typically negative slope (milder temps → lower demand → lower price).
    
    Returns DataFrame with regression coefficients and R².
    """
    log("Running regression: Temperature → SSP")
    
    required = {"SSP", "temperature"}
    if not required.issubset(df.columns):
        log(f"Missing columns: {required - set(df.columns)}", "WARN")
        return pd.DataFrame()
    
    data = df[["SSP", "temperature"]].dropna()
    
    if len(data) < 10:
        log("Insufficient data for regression", "WARN")
        return pd.DataFrame()
    
    # Prepare regression
    X = sm.add_constant(data["temperature"].astype(float))
    y = data["SSP"].astype(float)
    
    try:
        model = sm.OLS(y, X).fit()
    except Exception as e:
        log(f"Regression failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Create plot
    plot_path = "plots_disabled"
    if enable_plots:
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.scatter(data["temperature"], data["SSP"], s=8, alpha=0.3, label="Data")
            
            # Regression line
            temp_range = np.linspace(data["temperature"].min(), data["temperature"].max(), 200)
            ssp_pred = model.params["const"] + model.params["temperature"] * temp_range
            ax.plot(temp_range, ssp_pred, 'r-', linewidth=2, label="OLS Fit")
            
            ax.set_xlabel("Temperature (°C)", fontsize=11)
            ax.set_ylabel("SSP (£/MWh)", fontsize=11)
            ax.set_title("Temperature vs System Sell Price", fontsize=13, fontweight="bold")
            ax.legend()
            ax.grid(alpha=0.3)
            
            plot_path = save_plot(fig, "regression_temperature_ssp.png", enable_plots)
        except Exception as e:
            log(f"Plot creation failed: {e}", "WARN")
    
    result = pd.DataFrame([{
        "model": "OLS_SSP_on_Temperature",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "intercept": float(model.params.get("const", np.nan)),
        "slope_temperature": float(model.params.get("temperature", np.nan)),
        "p_intercept": float(model.pvalues.get("const", np.nan)),
        "p_temperature": float(model.pvalues.get("temperature", np.nan)),
        "se_temperature": float(model.bse.get("temperature", np.nan)),
        "plot_path": plot_path
    }])
    
    slope = result["slope_temperature"].iloc[0]
    r2 = result["r_squared"].iloc[0]
    log(f"  Slope: {slope:.3f} £/MWh per °C (R²={r2:.3f})")
    
    return result

def analyze_regression_volume_price(df: pd.DataFrame) -> pd.DataFrame:
    """
    3) Regression: SSP ~ log(volume) + wind + temperature
    
    Multi-factor price elasticity model showing impact of:
        - Demand (log-transformed volume)
        - Wind generation (merit order effect)
        - Temperature (weather proxy)
    
    Returns DataFrame with coefficients for all factors.
    """
    log("Running multi-factor regression: Volume + Wind + Temp → SSP")
    
    required = {"SSP", "volume"}
    if not required.issubset(df.columns):
        log(f"Missing required columns: {required - set(df.columns)}", "WARN")
        return pd.DataFrame()
    
    # Select available columns
    feature_cols = ["SSP", "volume", "wind_generation", "temperature"]
    available_cols = [c for c in feature_cols if c in df.columns]
    data = df[available_cols].dropna()
    
    # Filter positive volume
    data = data[data["volume"] > 0].copy()
    
    if len(data) < 50:
        log("Insufficient data for multi-factor regression", "WARN")
        return pd.DataFrame()
    
    # Log-transform volume
    data["log_volume"] = np.log(data["volume"])
    
    # Build feature matrix
    X_cols = ["log_volume"]
    if "wind_generation" in data.columns:
        X_cols.append("wind_generation")
    if "temperature" in data.columns:
        X_cols.append("temperature")
    
    X = sm.add_constant(data[X_cols].astype(float))
    y = data["SSP"].astype(float)
    
    try:
        model = sm.OLS(y, X).fit()
    except Exception as e:
        log(f"Regression failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Extract results
    result = {
        "model": "OLS_SSP_multifactor",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "intercept": float(model.params.get("const", np.nan)),
        "beta_log_volume": float(model.params.get("log_volume", np.nan)),
        "p_log_volume": float(model.pvalues.get("log_volume", np.nan)),
        "se_log_volume": float(model.bse.get("log_volume", np.nan))
    }
    
    if "wind_generation" in X.columns:
        result["beta_wind"] = float(model.params.get("wind_generation", np.nan))
        result["p_wind"] = float(model.pvalues.get("wind_generation", np.nan))
        result["se_wind"] = float(model.bse.get("wind_generation", np.nan))
    
    if "temperature" in X.columns:
        result["beta_temp"] = float(model.params.get("temperature", np.nan))
        result["p_temp"] = float(model.pvalues.get("temperature", np.nan))
        result["se_temp"] = float(model.bse.get("temperature", np.nan))
    
    result_df = pd.DataFrame([result])
    
    r2 = result_df["r_squared"].iloc[0]
    beta_vol = result_df["beta_log_volume"].iloc[0]
    log(f"  beta_log_volume: {beta_vol:.2f}, R²={r2:.3f}")
    
    return result_df

def analyze_correlation_matrix(df: pd.DataFrame, enable_plots: bool = True) -> Tuple[pd.DataFrame, str]:
    """
    4) Correlation Matrix + Heatmap
    
    Pearson correlations between key variables:
        SSP, SBP, spread, volume, temperature, wind, balancing costs
    
    Returns:
        - DataFrame with correlation matrix
        - Path to heatmap plot
    """
    log("Computing correlation matrix")
    
    metric_cols = [
        "SSP", "SBP", "spread", "volume", 
        "temperature", "wind_generation",
        "balancing_cost", "balancing_cost_per_mwh"
    ]
    available_cols = [c for c in metric_cols if c in df.columns]
    
    if len(available_cols) < 2:
        log("Insufficient columns for correlation matrix", "WARN")
        return pd.DataFrame(), ""
    
    corr_matrix = df[available_cols].corr(method="pearson")
    corr_df = corr_matrix.reset_index().rename(columns={"index": "variable"})
    
    # Create heatmap
    heatmap_path = "plots_disabled"
    if enable_plots:
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            im = ax.imshow(corr_matrix.values, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
            
            # Axis labels
            ax.set_xticks(range(len(available_cols)))
            ax.set_yticks(range(len(available_cols)))
            ax.set_xticklabels(available_cols, rotation=45, ha="right", fontsize=10)
            ax.set_yticklabels(available_cols, fontsize=10)
            
            # Colorbar
            cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label("Correlation", fontsize=11)
            
            ax.set_title("Correlation Matrix (Pearson)", fontsize=13, fontweight="bold", pad=15)
            
            # Add correlation values as text
            for i in range(len(available_cols)):
                for j in range(len(available_cols)):
                    val = corr_matrix.iloc[i, j]
                    color = "white" if abs(val) > 0.5 else "black"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", 
                           color=color, fontsize=8)
            
            heatmap_path = save_plot(fig, "correlation_heatmap.png", enable_plots)
        except Exception as e:
            log(f"Heatmap creation failed: {e}", "WARN")
    
    log(f"  Correlation matrix: {len(available_cols)}×{len(available_cols)}")
    return corr_df, heatmap_path

def analyze_arima_forecast(df: pd.DataFrame, enable_plots: bool = True) -> pd.DataFrame:
    """
    5) ARIMA Forecast: SSP next 24 hours
    
    SARIMAX model with weekly seasonality (48 SPs/day × 7 days = 336 periods).
    Produces 48-step forecast (next 24 hours) with 95% confidence interval.
    
    Returns DataFrame with timestamp, forecast, and CI bounds.
    """
    log("Running ARIMA forecast (SSP, 24h ahead)")
    
    if "SSP" not in df.columns:
        log("No SSP column for ARIMA", "WARN")
        return pd.DataFrame()
    
    data = df[["ts", "SSP"]].dropna().copy()
    
    if data.empty:
        log("No data for ARIMA", "WARN")
        return pd.DataFrame()
    
    # Prepare time series
    data["ts"] = pd.to_datetime(data["ts"])
    ts = data.set_index("ts").sort_index()["SSP"]
    ts = ts.asfreq("30min").interpolate(method="time", limit_direction="both")
    
    # Need at least 2 weeks of data
    if ts.size < 48 * 14:
        log(f"ARIMA requires ≥2 weeks; got {ts.size} periods", "WARN")
        return pd.DataFrame()
    
    # SARIMAX parameters
    order = (1, 1, 1)  # (p, d, q)
    seasonal_order = (1, 1, 1, 48 * 7)  # (P, D, Q, s) - weekly seasonality
    
    try:
        log("  Fitting SARIMAX model (this may take 30-60 seconds)...")
        model = SARIMAX(
            ts,
            order=order,
            seasonal_order=seasonal_order,
            enforce_stationarity=False,
            enforce_invertibility=False
        ).fit(disp=False, maxiter=200)
        
        log(f"  Model fit complete (AIC={model.aic:.1f}, BIC={model.bic:.1f})")
    except Exception as e:
        log(f"ARIMA fitting failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Forecast 48 steps (24 hours)
    forecast_steps = 48
    try:
        forecast = model.get_forecast(steps=forecast_steps)
        pred = forecast.predicted_mean
        ci = forecast.conf_int(alpha=0.05)
    except Exception as e:
        log(f"ARIMA forecast failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Build result DataFrame
    result = pd.DataFrame({
        "ts": pred.index,
        "forecast_ssp": pred.values,
        "ci_lo": ci.iloc[:, 0].values,
        "ci_hi": ci.iloc[:, 1].values
    }).reset_index(drop=True)
    
    result["aic"] = float(model.aic)
    result["bic"] = float(model.bic)
    result["order"] = str(order)
    result["seasonal_order"] = str(seasonal_order)
    
    # Create plot
    plot_path = "plots_disabled"
    if enable_plots:
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Historical (last week)
            ts.tail(48 * 7).plot(ax=ax, label="Historical (7 days)", color="steelblue")
            
            # Forecast
            pred.plot(ax=ax, label="Forecast (24h)", color="orangered", linewidth=2)
            
            # Confidence interval
            ax.fill_between(
                result["ts"], 
                result["ci_lo"], 
                result["ci_hi"],
                alpha=0.2, 
                color="orangered",
                label="95% CI"
            )
            
            ax.set_xlabel("Time (UTC)", fontsize=11)
            ax.set_ylabel("SSP (£/MWh)", fontsize=11)
            ax.set_title("SSP ARIMA Forecast (24h, 30-min steps)", fontsize=13, fontweight="bold")
            ax.legend(loc="best")
            ax.grid(alpha=0.3)
            
            plot_path = save_plot(fig, "arima_ssp_forecast.png", enable_plots)
        except Exception as e:
            log(f"ARIMA plot failed: {e}", "WARN")
    
    result["plot_path"] = plot_path
    
    log(f"  Forecast generated: {forecast_steps} periods")
    return result

def analyze_seasonal_decomposition(df: pd.DataFrame, enable_plots: bool = True) -> pd.DataFrame:
    """
    6) Seasonal Decomposition: Trend + Seasonal + Residual
    
    Additive decomposition of SSP into:
        - Trend: Long-term movement
        - Seasonal: Weekly repeating pattern
        - Residual: Noise + shocks
    
    Returns DataFrame with variance components.
    """
    log("Running seasonal decomposition (SSP)")
    
    if "SSP" not in df.columns:
        log("No SSP column for decomposition", "WARN")
        return pd.DataFrame()
    
    data = df[["ts", "SSP"]].dropna().copy()
    data["ts"] = pd.to_datetime(data["ts"])
    
    # Prepare time series
    ts = data.set_index("ts").sort_index()["SSP"]
    ts = ts.asfreq("30min").interpolate(method="time", limit_direction="both")
    
    period = 48 * 7  # Weekly seasonality
    
    if ts.size < 2 * period:
        log(f"Decomposition requires ≥2 periods; got {ts.size}", "WARN")
        return pd.DataFrame()
    
    try:
        decomp = seasonal_decompose(
            ts, 
            model="additive", 
            period=period,
            two_sided=False,
            extrapolate_trend="freq"
        )
    except Exception as e:
        log(f"Decomposition failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Create plot
    plot_path = "plots_disabled"
    if enable_plots:
        try:
            fig, axes = plt.subplots(4, 1, figsize=(12, 10))
            
            # Observed
            axes[0].plot(ts.index, ts.values, color="steelblue")
            axes[0].set_title("Observed (SSP)", fontweight="bold")
            axes[0].set_ylabel("£/MWh")
            axes[0].grid(alpha=0.3)
            
            # Trend
            axes[1].plot(decomp.trend.index, decomp.trend.values, color="green")
            axes[1].set_title("Trend", fontweight="bold")
            axes[1].set_ylabel("£/MWh")
            axes[1].grid(alpha=0.3)
            
            # Seasonal
            axes[2].plot(decomp.seasonal.index, decomp.seasonal.values, color="orange")
            axes[2].set_title("Seasonal (Weekly)", fontweight="bold")
            axes[2].set_ylabel("£/MWh")
            axes[2].grid(alpha=0.3)
            
            # Residual
            axes[3].plot(decomp.resid.index, decomp.resid.values, color="red", alpha=0.5)
            axes[3].set_title("Residual", fontweight="bold")
            axes[3].set_ylabel("£/MWh")
            axes[3].set_xlabel("Time (UTC)")
            axes[3].grid(alpha=0.3)
            
            plt.tight_layout()
            plot_path = save_plot(fig, "seasonal_decomposition_ssp.png", enable_plots)
        except Exception as e:
            log(f"Decomposition plot failed: {e}", "WARN")
    
    result = pd.DataFrame([{
        "period": int(period),
        "obs_count": int(len(ts)),
        "trend_var": float(np.nanvar(decomp.trend.values)),
        "seasonal_var": float(np.nanvar(decomp.seasonal.values)),
        "resid_var": float(np.nanvar(decomp.resid.values)),
        "plot_path": plot_path
    }])
    
    log(f"  Variances - Trend: {result['trend_var'].iloc[0]:.1f}, "
        f"Seasonal: {result['seasonal_var'].iloc[0]:.1f}, "
        f"Residual: {result['resid_var'].iloc[0]:.1f}")
    
    return result

def analyze_outage_impact(df: pd.DataFrame) -> pd.DataFrame:
    """
    7) Outage Impact Analysis: Event vs Normal Spreads
    
    T-test comparing spread during system warning events vs normal periods.
    Quantifies stress on spreads during tight margins, frequency issues, etc.
    
    Returns DataFrame with test statistics.
    """
    log("Analyzing outage/event impact on spreads")
    
    required = {"spread", "unplanned_event"}
    if not required.issubset(df.columns):
        log(f"Missing columns: {required - set(df.columns)}", "WARN")
        return pd.DataFrame()
    
    data = df[["spread", "unplanned_event"]].dropna()
    
    if data.empty:
        log("No data for outage impact analysis", "WARN")
        return pd.DataFrame()
    
    # Split by event flag
    with_event = data.loc[data["unplanned_event"] == True, "spread"].values
    without_event = data.loc[data["unplanned_event"] == False, "spread"].values
    
    if len(with_event) < 5 or len(without_event) < 5:
        log(f"Insufficient events: with={len(with_event)}, without={len(without_event)}", "WARN")
        return pd.DataFrame()
    
    # Welch's t-test
    t_stat, p_value = stats.ttest_ind(with_event, without_event, equal_var=False, nan_policy="omit")
    
    result = pd.DataFrame([{
        "metric": "spread_during_system_events",
        "mean_with_event": float(np.nanmean(with_event)),
        "mean_without_event": float(np.nanmean(without_event)),
        "mean_diff": float(np.nanmean(with_event) - np.nanmean(without_event)),
        "t_stat": float(t_stat),
        "p_value": float(p_value),
        "std_with_event": float(np.nanstd(with_event, ddof=1)),
        "std_without_event": float(np.nanstd(without_event, ddof=1)),
        "n_with": int(np.isfinite(with_event).sum()),
        "n_without": int(np.isfinite(without_event).sum())
    }])
    
    diff = result["mean_diff"].iloc[0]
    log(f"  Spread difference: £{diff:.2f}/MWh (events vs normal, p={p_value:.4f})")
    
    return result

def analyze_neso_behavior(df: pd.DataFrame) -> pd.DataFrame:
    """
    8) NESO Behavior Analysis: Balancing Cost → Spread
    
    OLS regression: Spread ~ Balancing Cost + Cost per MWh
    
    Shows how NESO balancing actions correlate with market spreads.
    Useful for unified DUoS/BSUoS/TNUoS cost modeling.
    
    Returns DataFrame with regression coefficients.
    """
    log("Analyzing NESO behavior: Balancing costs → Spread")
    
    required = {"spread", "balancing_cost"}
    if not required.issubset(df.columns):
        log(f"Missing columns: {required - set(df.columns)}", "WARN")
        return pd.DataFrame()
    
    # Select columns
    feature_cols = ["spread", "balancing_cost"]
    if "balancing_cost_per_mwh" in df.columns:
        feature_cols.append("balancing_cost_per_mwh")
    
    data = df[feature_cols].dropna()
    
    if len(data) < 50:
        log("Insufficient data for NESO behavior regression", "WARN")
        return pd.DataFrame()
    
    # Regression
    X_cols = [c for c in feature_cols if c != "spread"]
    X = sm.add_constant(data[X_cols].astype(float))
    y = data["spread"].astype(float)
    
    try:
        model = sm.OLS(y, X).fit()
    except Exception as e:
        log(f"Regression failed: {e}", "ERROR")
        return pd.DataFrame()
    
    result = {
        "model": "Spread_on_BalancingCosts",
        "n_obs": int(model.nobs),
        "r_squared": float(model.rsquared),
        "adj_r_squared": float(model.rsquared_adj),
        "intercept": float(model.params.get("const", np.nan)),
        "beta_balancing_cost": float(model.params.get("balancing_cost", np.nan)),
        "p_balancing_cost": float(model.pvalues.get("balancing_cost", np.nan)),
        "se_balancing_cost": float(model.bse.get("balancing_cost", np.nan))
    }
    
    if "balancing_cost_per_mwh" in X.columns:
        result["beta_cost_per_mwh"] = float(model.params.get("balancing_cost_per_mwh", np.nan))
        result["p_cost_per_mwh"] = float(model.pvalues.get("balancing_cost_per_mwh", np.nan))
        result["se_cost_per_mwh"] = float(model.bse.get("balancing_cost_per_mwh", np.nan))
    
    result_df = pd.DataFrame([result])
    
    r2 = result_df["r_squared"].iloc[0]
    beta = result_df["beta_balancing_cost"].iloc[0]
    log(f"  beta_balancing_cost: {beta:.6f}, R²={r2:.3f}")
    
    return result_df

def analyze_anova_seasons(df: pd.DataFrame, price_col: str = "SSP") -> pd.DataFrame:
    """
    9) ANOVA: Seasonal Pricing Regimes
    
    One-way ANOVA testing if mean price differs across seasons.
    Useful for tariff design and seasonal business cases.
    
    Args:
        df: Data with 'season' column
        price_col: Column to test ("SSP" or "SBP")
    
    Returns DataFrame with F-statistic and group statistics.
    """
    log(f"Running ANOVA: {price_col} by season")
    
    if price_col not in df.columns or "season" not in df.columns:
        log(f"Missing {price_col} or season column", "WARN")
        return pd.DataFrame()
    
    # Group by season
    groups = [grp[price_col].dropna().values for _, grp in df.groupby("season")]
    groups = [g for g in groups if len(g) > 1]
    
    if len(groups) < 2:
        log("Insufficient groups for ANOVA", "WARN")
        return pd.DataFrame()
    
    # One-way ANOVA
    try:
        f_stat, p_value = stats.f_oneway(*groups)
    except Exception as e:
        log(f"ANOVA failed: {e}", "ERROR")
        return pd.DataFrame()
    
    # Group statistics
    season_names = [name for name, _ in df.groupby("season")]
    group_sizes = [len(g) for g in groups]
    group_means = [float(np.nanmean(g)) for g in groups]
    group_stds = [float(np.nanstd(g, ddof=1)) for g in groups]
    
    result = pd.DataFrame([{
        "price_col": price_col,
        "f_stat": float(f_stat),
        "p_value": float(p_value),
        "n_groups": len(groups),
        "group_names": season_names,
        "group_sizes": group_sizes,
        "group_means": group_means,
        "group_stds": group_stds
    }])
    
    log(f"  F-stat: {f_stat:.2f} (p={p_value:.4f}), Groups: {season_names}")
    
    return result

# =========================
# ========= MAIN ==========
# =========================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Advanced Statistical Analysis for GB Power Market",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run with defaults
    python advanced_statistical_analysis.py
    
    # Custom date range
    python advanced_statistical_analysis.py --start 2024-01-01 --end 2025-10-31
    
    # Skip plots (faster)
    python advanced_statistical_analysis.py --no-plots
    
    # Custom project
    python advanced_statistical_analysis.py --project my-project-id
        """
    )
    
    parser.add_argument(
        "--start",
        type=str,
        default=DATE_START,
        help=f"Start date (YYYY-MM-DD). Default: {DATE_START}"
    )
    
    parser.add_argument(
        "--end",
        type=str,
        default=DATE_END,
        help=f"End date (YYYY-MM-DD, exclusive). Default: {DATE_END}"
    )
    
    parser.add_argument(
        "--project",
        type=str,
        default=PROJECT_ID,
        help=f"GCP project ID. Default: {PROJECT_ID}"
    )
    
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip plot generation (faster execution)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTDIR,
        help=f"Output directory for plots. Default: {OUTDIR}"
    )
    
    return parser.parse_args()

def main():
    """Main execution flow"""
    args = parse_args()
    
    # Update globals from args
    global DATE_START, DATE_END, PROJECT_ID, OUTDIR
    DATE_START = args.start
    DATE_END = args.end
    PROJECT_ID = args.project
    OUTDIR = args.output_dir
    OUTDIR.mkdir(exist_ok=True)
    
    enable_plots = not args.no_plots
    
    log("=" * 70)
    log("ADVANCED STATISTICAL ANALYSIS FOR GB POWER MARKET")
    log("=" * 70)
    log(f"Project: {PROJECT_ID}")
    log(f"Date range: {DATE_START} to {DATE_END}")
    log(f"Output dir: {OUTDIR}")
    log(f"Plots enabled: {enable_plots}")
    log("=" * 70)
    
    try:
        # Step 1: Load data
        df = load_harmonised_data(DATE_START, DATE_END)
        log(f"✅ Loaded {len(df):,} rows with {len(df.columns)} features")
        
        # Step 2: Run analyses
        log("\n" + "=" * 70)
        log("RUNNING STATISTICAL ANALYSES")
        log("=" * 70 + "\n")
        
        # 1) T-test: SSP vs SBP
        ttest_results = analyze_ttest_ssp_sbp(df)
        write_bq(ttest_results, "ttest_results")
        
        # 2) Regression: Temperature → SSP
        reg_temp_results = analyze_regression_temperature_ssp(df, enable_plots)
        write_bq(reg_temp_results, "regression_temperature_ssp")
        
        # 3) Regression: Multi-factor price model
        reg_multi_results = analyze_regression_volume_price(df)
        write_bq(reg_multi_results, "regression_volume_price")
        
        # 4) Correlation matrix + heatmap
        corr_matrix, heatmap_path = analyze_correlation_matrix(df, enable_plots)
        write_bq(corr_matrix, "correlation_matrix")
        if heatmap_path and enable_plots:
            log(f"  Heatmap: {heatmap_path}")
        
        # 5) ARIMA forecast
        arima_results = analyze_arima_forecast(df, enable_plots)
        write_bq(arima_results, "arima_forecast_ssp")
        
        # 6) Seasonal decomposition
        decomp_results = analyze_seasonal_decomposition(df, enable_plots)
        write_bq(decomp_results, "seasonal_decomposition_stats")
        
        # 7) Outage impact
        outage_results = analyze_outage_impact(df)
        write_bq(outage_results, "outage_impact_results")
        
        # 8) NESO behavior
        neso_results = analyze_neso_behavior(df)
        write_bq(neso_results, "neso_behavior_results")
        
        # 9) ANOVA by season (SSP and SBP)
        anova_ssp = analyze_anova_seasons(df, "SSP")
        anova_sbp = analyze_anova_seasons(df, "SBP")
        anova_all = pd.concat([anova_ssp, anova_sbp], ignore_index=True)
        write_bq(anova_all, "anova_results")
        
        log("\n" + "=" * 70)
        log("✅ ALL ANALYSES COMPLETE")
        log("=" * 70)
        log(f"\nResults written to: {PROJECT_ID}.{DATASET_ANALYTICS}")
        log(f"Plots saved to: {OUTDIR}" + (" (disabled)" if not enable_plots else ""))
        log("\n📖 See STATISTICAL_ANALYSIS_GUIDE.md for interpretation guidance")
        
    except KeyboardInterrupt:
        log("\n⚠️  Analysis interrupted by user", "WARN")
        sys.exit(1)
    except Exception as e:
        log(f"\n❌ FATAL ERROR: {e}", "ERROR")
        raise

if __name__ == "__main__":
    main()
