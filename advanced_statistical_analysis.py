#!/usr/bin/env python3
"""
Advanced Statistical Analysis Suite for UK Energy Data
=======================================================

Adapted to inner-cinema-476211-u9.uk_energy_prod schema:
- bmrs_mid: Market prices (SSP/SBP proxies)
- bmrs_boalf: Acceptance volumes
- bmrs_fuelinst_iris: Wind generation
- bmrs_inddem_iris: Demand data
- bmrs_freq: Grid frequency (system stress proxy)

Analyses:
1. T-tests (SSP vs SBP)
2. ANOVA by season
3. Correlation matrices
4. OLS regressions (demand/wind on prices)
5. ARIMA forecasting (30-min SARIMAX)
6. Seasonal decomposition
7. Frequency-price relationship (grid stress)
8. Balancing volume impact on spread

Outputs: BigQuery tables + plots to ./output/

Usage:
    .venv/bin/python advanced_statistical_analysis.py
"""

import os
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

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("whitegrid")

# ==================== CONFIG ====================
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_SOURCE = "uk_energy_prod"
DATASET_ANALYTICS = "uk_energy_analysis"  # Will be created if doesn't exist
LOCATION = "US"  # Your tables are in US location, NOT europe-west2

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Date range
DATE_START = "2024-01-01"  # Adjust to your data coverage
DATE_END = "2025-11-01"

# Output directory for plots
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)


# ==================== UTILITIES ====================
def save_plot(fig, fname: str):
    """Save plot locally"""
    local_path = OUTDIR / fname
    fig.savefig(local_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"📊 Saved plot: {local_path}")
    return str(local_path)


def write_bq(df: pd.DataFrame, table_name: str, if_exists="replace"):
    """Write DataFrame to BigQuery"""
    if df.empty:
        print(f"⚠️  {table_name}: DataFrame empty, skipping write")
        return
    
    full_table = f"{PROJECT_ID}.{DATASET_ANALYTICS}.{table_name}"
    
    try:
        to_gbq(df, full_table, project_id=PROJECT_ID, 
               if_exists=if_exists, location=LOCATION)
        print(f"✅ Wrote {len(df):,} rows to {full_table}")
    except Exception as e:
        print(f"❌ Failed to write {table_name}: {e}")


def add_calendar_fields(df: pd.DataFrame, ts_col: str):
    """Add date/time features"""
    ts = pd.to_datetime(df[ts_col])
    df["date"] = ts.dt.date
    df["month"] = ts.dt.month
    df["dow"] = ts.dt.dayofweek
    df["hour"] = ts.dt.hour
    df["is_weekend"] = df["dow"] >= 5
    
    def season(m):
        if m in (12, 1, 2): return "Winter"
        elif m in (3, 4, 5): return "Spring"
        elif m in (6, 7, 8): return "Summer"
        else: return "Autumn"
    
    df["season"] = df["month"].apply(season)
    return df


# ==================== DATA LOADING ====================
def load_data():
    """
    Load and harmonize data from uk_energy_prod tables
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    print(f"🔍 Loading data from {PROJECT_ID}.{DATASET_SOURCE}...")
    print(f"   Date range: {DATE_START} to {DATE_END}")
    
    # Build comprehensive query
    query = f"""
    WITH 
    -- Time grid (30-minute settlement periods)
    time_grid AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            TIMESTAMP_ADD(
                TIMESTAMP(settlementDate), 
                INTERVAL (settlementPeriod - 1) * 30 MINUTE
            ) as ts
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_mid`
        WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Market prices (SSP/SBP proxy from bmrs_mid)
    prices AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            AVG(CASE WHEN price > 0 THEN price END) as price_gbp_mwh,
            MAX(CASE WHEN price > 0 THEN price END) as max_price,
            MIN(CASE WHEN price > 0 THEN price END) as min_price,
            STDDEV(CASE WHEN price > 0 THEN price END) as price_std
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_mid`
        WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Balancing volumes (proxy for market stress)
    balancing_volumes AS (
        SELECT 
            settlementDate,
            settlementPeriodFrom as settlementPeriod,
            SUM(ABS(levelTo - levelFrom)) as total_balancing_mw,
            COUNT(DISTINCT acceptanceNumber) as num_acceptances,
            SUM(CASE WHEN (levelTo - levelFrom) > 0 THEN (levelTo - levelFrom) ELSE 0 END) as total_increase_mw,
            SUM(CASE WHEN (levelTo - levelFrom) < 0 THEN ABS(levelTo - levelFrom) ELSE 0 END) as total_decrease_mw
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_boalf`
        WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
        GROUP BY settlementDate, settlementPeriodFrom
    ),
    
    -- Wind generation (from fuelinst_iris)
    wind AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            AVG(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as wind_mw
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_fuelinst_iris`
        WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
          AND fuelType = 'WIND'
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Demand (from inddem_iris)
    demand AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            AVG(demand) as demand_mw
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_inddem_iris`
        WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
        GROUP BY settlementDate, settlementPeriod
    ),
    
    -- Grid frequency (system stress proxy)
    freq AS (
        SELECT 
            CAST(measurementTime AS DATE) as settlementDate,
            -- Map to settlement period (1-48)
            EXTRACT(HOUR FROM measurementTime) * 2 + 
            CAST(EXTRACT(MINUTE FROM measurementTime) >= 30 AS INT64) + 1 as settlementPeriod,
            AVG(frequency) as avg_frequency_hz,
            STDDEV(frequency) as frequency_volatility,
            MIN(frequency) as min_frequency,
            MAX(frequency) as max_frequency
        FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_freq`
        WHERE CAST(measurementTime AS DATE) BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
        GROUP BY settlementDate, settlementPeriod
    )
    
    -- Final join
    SELECT 
        tg.ts,
        tg.settlementDate as date,
        tg.settlementPeriod as period,
        p.price_gbp_mwh as price,
        p.price_std as price_volatility,
        bv.total_balancing_mw as balancing_volume,
        bv.num_acceptances,
        bv.total_increase_mw,
        bv.total_decrease_mw,
        w.wind_mw,
        d.demand_mw,
        f.avg_frequency_hz as frequency,
        f.frequency_volatility,
        f.min_frequency,
        f.max_frequency
    FROM time_grid tg
    LEFT JOIN prices p USING (settlementDate, settlementPeriod)
    LEFT JOIN balancing_volumes bv USING (settlementDate, settlementPeriod)
    LEFT JOIN wind w USING (settlementDate, settlementPeriod)
    LEFT JOIN demand d USING (settlementDate, settlementPeriod)
    LEFT JOIN freq f USING (settlementDate, settlementPeriod)
    WHERE p.price_gbp_mwh IS NOT NULL  -- Must have price data
    ORDER BY tg.ts
    """
    
    try:
        df = client.query(query).to_dataframe()
        print(f"✅ Loaded {len(df):,} rows")
        
        if df.empty:
            raise ValueError("No data returned. Check date range and table names.")
        
        # Add calendar features
        df = add_calendar_fields(df, "ts")
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        raise


# ==================== STATISTICAL ANALYSES ====================

def ttest_analysis(df: pd.DataFrame):
    """
    T-test: Compare prices across different conditions
    """
    print("\n📊 Running T-tests...")
    
    results = []
    
    # 1. Weekend vs Weekday prices
    if "is_weekend" in df.columns and "price" in df.columns:
        weekday = df[~df["is_weekend"]]["price"].dropna()
        weekend = df[df["is_weekend"]]["price"].dropna()
        
        if len(weekday) > 0 and len(weekend) > 0:
            t_stat, p_val = stats.ttest_ind(weekday, weekend, equal_var=False)
            results.append({
                "test": "Weekend_vs_Weekday_Price",
                "group1_mean": float(weekday.mean()),
                "group2_mean": float(weekend.mean()),
                "mean_diff": float(weekend.mean() - weekday.mean()),
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "n_group1": len(weekday),
                "n_group2": len(weekend),
                "significant": p_val < 0.05
            })
    
    # 2. High wind vs Low wind prices
    if "wind_mw" in df.columns and "price" in df.columns:
        wind_median = df["wind_mw"].median()
        high_wind = df[df["wind_mw"] > wind_median]["price"].dropna()
        low_wind = df[df["wind_mw"] <= wind_median]["price"].dropna()
        
        if len(high_wind) > 0 and len(low_wind) > 0:
            t_stat, p_val = stats.ttest_ind(high_wind, low_wind, equal_var=False)
            results.append({
                "test": "High_Wind_vs_Low_Wind_Price",
                "group1_mean": float(low_wind.mean()),
                "group2_mean": float(high_wind.mean()),
                "mean_diff": float(high_wind.mean() - low_wind.mean()),
                "t_statistic": float(t_stat),
                "p_value": float(p_val),
                "n_group1": len(low_wind),
                "n_group2": len(high_wind),
                "significant": p_val < 0.05
            })
    
    return pd.DataFrame(results)


def anova_by_season(df: pd.DataFrame):
    """
    ANOVA: Test if prices differ significantly across seasons
    """
    print("\n📊 Running ANOVA by season...")
    
    if "season" not in df.columns or "price" not in df.columns:
        return pd.DataFrame()
    
    groups = [group["price"].dropna().values 
              for name, group in df.groupby("season")]
    groups = [g for g in groups if len(g) > 1]
    
    if len(groups) < 2:
        return pd.DataFrame()
    
    f_stat, p_val = stats.f_oneway(*groups)
    
    season_means = df.groupby("season")["price"].mean().to_dict()
    season_counts = df.groupby("season").size().to_dict()
    
    return pd.DataFrame([{
        "variable": "price",
        "f_statistic": float(f_stat),
        "p_value": float(p_val),
        "n_groups": len(groups),
        "significant": p_val < 0.05,
        "winter_mean": season_means.get("Winter", np.nan),
        "spring_mean": season_means.get("Spring", np.nan),
        "summer_mean": season_means.get("Summer", np.nan),
        "autumn_mean": season_means.get("Autumn", np.nan),
        "winter_n": season_counts.get("Winter", 0),
        "spring_n": season_counts.get("Spring", 0),
        "summer_n": season_counts.get("Summer", 0),
        "autumn_n": season_counts.get("Autumn", 0),
    }])


def correlation_analysis(df: pd.DataFrame):
    """
    Correlation matrix for key variables
    """
    print("\n📊 Calculating correlations...")
    
    cols = [c for c in ["price", "demand_mw", "wind_mw", "balancing_volume", 
                        "frequency", "price_volatility"] 
            if c in df.columns]
    
    if not cols:
        return pd.DataFrame()
    
    corr_matrix = df[cols].corr(method="pearson")
    
    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt=".3f", cmap="coolwarm", 
                center=0, ax=ax, square=True)
    ax.set_title("Correlation Matrix - UK Energy Market Variables")
    save_plot(fig, "correlation_matrix.png")
    
    # Return as long format
    corr_df = corr_matrix.reset_index().melt(id_vars="index")
    corr_df.columns = ["variable1", "variable2", "correlation"]
    
    return corr_df


def regression_demand_price(df: pd.DataFrame):
    """
    OLS regression: Price ~ Demand + Wind + Hour
    """
    print("\n📊 Running OLS: Price ~ Demand + Wind + Hour...")
    
    required = ["price", "demand_mw", "wind_mw", "hour"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()
    
    analysis_df = df[required].dropna()
    
    if len(analysis_df) < 100:
        return pd.DataFrame()
    
    X = sm.add_constant(analysis_df[["demand_mw", "wind_mw", "hour"]])
    y = analysis_df["price"]
    
    try:
        model = sm.OLS(y, X).fit()
        
        results = {
            "model": "Price_on_Demand_Wind_Hour",
            "n_obs": int(model.nobs),
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "intercept": float(model.params.get("const", np.nan)),
            "beta_demand": float(model.params.get("demand_mw", np.nan)),
            "beta_wind": float(model.params.get("wind_mw", np.nan)),
            "beta_hour": float(model.params.get("hour", np.nan)),
            "p_demand": float(model.pvalues.get("demand_mw", np.nan)),
            "p_wind": float(model.pvalues.get("wind_mw", np.nan)),
            "p_hour": float(model.pvalues.get("hour", np.nan)),
        }
        
        # Plot residuals
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # Fitted vs Actual
        axes[0,0].scatter(model.fittedvalues, y, alpha=0.3, s=1)
        axes[0,0].plot([y.min(), y.max()], [y.min(), y.max()], 'r--')
        axes[0,0].set_xlabel("Fitted Price")
        axes[0,0].set_ylabel("Actual Price")
        axes[0,0].set_title("Fitted vs Actual")
        
        # Residuals
        axes[0,1].scatter(model.fittedvalues, model.resid, alpha=0.3, s=1)
        axes[0,1].axhline(0, color='r', linestyle='--')
        axes[0,1].set_xlabel("Fitted Price")
        axes[0,1].set_ylabel("Residuals")
        axes[0,1].set_title("Residual Plot")
        
        # Q-Q plot
        sm.qqplot(model.resid, line='45', ax=axes[1,0])
        axes[1,0].set_title("Q-Q Plot")
        
        # Residual histogram
        axes[1,1].hist(model.resid, bins=50, edgecolor='black')
        axes[1,1].set_xlabel("Residuals")
        axes[1,1].set_ylabel("Frequency")
        axes[1,1].set_title("Residual Distribution")
        
        plt.tight_layout()
        save_plot(fig, "regression_diagnostics.png")
        
        return pd.DataFrame([results])
        
    except Exception as e:
        print(f"⚠️  Regression failed: {e}")
        return pd.DataFrame()


def arima_forecast(df: pd.DataFrame):
    """
    ARIMA/SARIMAX forecast for prices (next 48 periods = 24 hours)
    """
    print("\n📊 Running ARIMA forecast...")
    
    if "price" not in df.columns or "ts" not in df.columns:
        return pd.DataFrame()
    
    ts_data = df[["ts", "price"]].dropna().copy()
    ts_data["ts"] = pd.to_datetime(ts_data["ts"])
    
    # Remove duplicates by taking first occurrence
    ts_data = ts_data.drop_duplicates(subset="ts", keep="first")
    
    ts_data = ts_data.set_index("ts").sort_index()
    
    # Resample to 30-min frequency and interpolate
    y = ts_data["price"].asfreq("30min").interpolate(limit_direction="both")
    
    if y.size < 48 * 14:  # Need at least 2 weeks
        print("⚠️  Not enough data for ARIMA (need 2+ weeks)")
        return pd.DataFrame()
    
    # SARIMAX with weekly seasonality (48 periods/day * 7 days)
    order = (1, 1, 1)
    seasonal_order = (1, 1, 1, 48 * 7)
    
    try:
        model = SARIMAX(y, order=order, seasonal_order=seasonal_order,
                       enforce_stationarity=False, enforce_invertibility=False)
        results = model.fit(disp=False, maxiter=100)
        
        # Forecast 48 periods ahead (24 hours)
        forecast = results.get_forecast(steps=48)
        pred = forecast.predicted_mean
        ci = forecast.conf_int(alpha=0.05)
        
        # Plot
        fig, ax = plt.subplots(figsize=(14, 6))
        y.tail(48 * 7).plot(ax=ax, label="Historical (Last 7 days)", linewidth=1)
        pred.plot(ax=ax, label="Forecast (Next 24h)", linewidth=2, color='red')
        ax.fill_between(pred.index, ci.iloc[:, 0], ci.iloc[:, 1], 
                        alpha=0.2, label="95% CI")
        ax.set_title("Price ARIMA Forecast (Next 24 Hours)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Price (£/MWh)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        save_plot(fig, "arima_forecast.png")
        
        # Return forecast as DataFrame
        forecast_df = pd.DataFrame({
            "forecast_timestamp": pred.index,
            "forecast_price": pred.values,
            "ci_lower": ci.iloc[:, 0].values,
            "ci_upper": ci.iloc[:, 1].values,
            "model_order": str(order),
            "seasonal_order": str(seasonal_order),
            "aic": results.aic,
            "bic": results.bic,
        })
        
        return forecast_df
        
    except Exception as e:
        print(f"⚠️  ARIMA failed: {e}")
        return pd.DataFrame()


def seasonal_decomposition(df: pd.DataFrame):
    """
    Seasonal decomposition of price time series
    """
    print("\n📊 Running seasonal decomposition...")
    
    if "price" not in df.columns or "ts" not in df.columns:
        return pd.DataFrame()
    
    ts_data = df[["ts", "price"]].dropna().copy()
    ts_data["ts"] = pd.to_datetime(ts_data["ts"])
    
    # Remove duplicates by taking first occurrence
    ts_data = ts_data.drop_duplicates(subset="ts", keep="first")
    
    ts_data = ts_data.set_index("ts").sort_index()
    
    y = ts_data["price"].asfreq("30min").interpolate(limit_direction="both")
    
    period = 48 * 7  # Weekly seasonality
    
    if len(y) < period * 2:
        print("⚠️  Not enough data for seasonal decomposition")
        return pd.DataFrame()
    
    try:
        decomp = seasonal_decompose(y, model="additive", period=period, 
                                    two_sided=False, extrapolate_trend="freq")
        
        # Plot
        fig, axes = plt.subplots(4, 1, figsize=(14, 10))
        
        axes[0].plot(y.index, y.values)
        axes[0].set_ylabel("Observed")
        axes[0].set_title("Price Time Series Decomposition")
        axes[0].grid(True, alpha=0.3)
        
        axes[1].plot(decomp.trend.index, decomp.trend.values)
        axes[1].set_ylabel("Trend")
        axes[1].grid(True, alpha=0.3)
        
        axes[2].plot(decomp.seasonal.index, decomp.seasonal.values)
        axes[2].set_ylabel("Seasonal")
        axes[2].grid(True, alpha=0.3)
        
        axes[3].plot(decomp.resid.index, decomp.resid.values)
        axes[3].set_ylabel("Residual")
        axes[3].set_xlabel("Time")
        axes[3].grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_plot(fig, "seasonal_decomposition.png")
        
        # Stats
        stats_df = pd.DataFrame([{
            "period": int(period),
            "obs_count": int(len(y)),
            "trend_variance": float(np.nanvar(decomp.trend.values)),
            "seasonal_variance": float(np.nanvar(decomp.seasonal.values)),
            "residual_variance": float(np.nanvar(decomp.resid.values)),
            "seasonal_strength": float(1 - np.nanvar(decomp.resid.values) / 
                                      np.nanvar(decomp.trend.values + decomp.resid.values)),
        }])
        
        return stats_df
        
    except Exception as e:
        print(f"⚠️  Seasonal decomposition failed: {e}")
        return pd.DataFrame()


def frequency_price_analysis(df: pd.DataFrame):
    """
    Analyze relationship between grid frequency and prices
    (Low frequency = system stress = higher prices)
    """
    print("\n📊 Analyzing frequency-price relationship...")
    
    required = ["frequency", "price"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()
    
    analysis_df = df[required].dropna()
    
    if len(analysis_df) < 100:
        return pd.DataFrame()
    
    # Classify frequency events
    analysis_df = analysis_df.copy()
    analysis_df["freq_category"] = pd.cut(
        analysis_df["frequency"], 
        bins=[0, 49.8, 50.2, 100],
        labels=["Low (<49.8 Hz)", "Normal (49.8-50.2 Hz)", "High (>50.2 Hz)"]
    )
    
    # Compare prices across frequency categories
    low_freq = analysis_df[analysis_df["freq_category"] == "Low (<49.8 Hz)"]["price"]
    normal_freq = analysis_df[analysis_df["freq_category"] == "Normal (49.8-50.2 Hz)"]["price"]
    
    results = []
    
    if len(low_freq) > 10 and len(normal_freq) > 10:
        t_stat, p_val = stats.ttest_ind(low_freq, normal_freq, equal_var=False)
        
        results.append({
            "comparison": "Low_Freq_vs_Normal_Freq",
            "low_freq_mean_price": float(low_freq.mean()),
            "normal_freq_mean_price": float(normal_freq.mean()),
            "price_diff": float(low_freq.mean() - normal_freq.mean()),
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "n_low_freq": len(low_freq),
            "n_normal_freq": len(normal_freq),
            "significant": p_val < 0.05
        })
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Scatter plot
    axes[0].scatter(analysis_df["frequency"], analysis_df["price"], 
                   alpha=0.3, s=1)
    axes[0].axvline(49.8, color='r', linestyle='--', label="Low freq threshold")
    axes[0].axvline(50.2, color='r', linestyle='--', label="High freq threshold")
    axes[0].set_xlabel("Frequency (Hz)")
    axes[0].set_ylabel("Price (£/MWh)")
    axes[0].set_title("Frequency vs Price")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Box plot by category
    analysis_df.boxplot(column="price", by="freq_category", ax=axes[1])
    axes[1].set_xlabel("Frequency Category")
    axes[1].set_ylabel("Price (£/MWh)")
    axes[1].set_title("Price Distribution by Frequency Category")
    plt.suptitle("")  # Remove default title
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_plot(fig, "frequency_price_analysis.png")
    
    return pd.DataFrame(results) if results else pd.DataFrame()


def balancing_volume_analysis(df: pd.DataFrame):
    """
    Analyze how balancing volumes affect prices
    """
    print("\n📊 Analyzing balancing volume impact...")
    
    required = ["balancing_volume", "price"]
    if not all(c in df.columns for c in required):
        return pd.DataFrame()
    
    analysis_df = df[required].dropna()
    
    if len(analysis_df) < 100:
        return pd.DataFrame()
    
    # Regression: Price ~ Balancing Volume
    X = sm.add_constant(analysis_df[["balancing_volume"]])
    y = analysis_df["price"]
    
    try:
        model = sm.OLS(y, X).fit()
        
        # Plot
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(analysis_df["balancing_volume"], analysis_df["price"], 
                  alpha=0.3, s=1)
        
        # Regression line
        x_range = np.linspace(analysis_df["balancing_volume"].min(), 
                             analysis_df["balancing_volume"].max(), 100)
        y_pred = model.params["const"] + model.params["balancing_volume"] * x_range
        ax.plot(x_range, y_pred, 'r-', linewidth=2, 
               label=f"R² = {model.rsquared:.3f}")
        
        ax.set_xlabel("Balancing Volume (MW)")
        ax.set_ylabel("Price (£/MWh)")
        ax.set_title("Balancing Volume vs Price")
        ax.legend()
        ax.grid(True, alpha=0.3)
        save_plot(fig, "balancing_volume_price.png")
        
        return pd.DataFrame([{
            "model": "Price_on_Balancing_Volume",
            "n_obs": int(model.nobs),
            "r_squared": float(model.rsquared),
            "adj_r_squared": float(model.rsquared_adj),
            "intercept": float(model.params["const"]),
            "beta_balancing_volume": float(model.params["balancing_volume"]),
            "p_balancing_volume": float(model.pvalues["balancing_volume"]),
            "interpretation": "Positive beta = Higher balancing volumes → Higher prices"
        }])
        
    except Exception as e:
        print(f"⚠️  Balancing volume regression failed: {e}")
        return pd.DataFrame()


# ==================== MAIN ====================
def main():
    """
    Execute all statistical analyses
    """
    print("\n" + "="*100)
    print("🔬 ADVANCED STATISTICAL ANALYSIS SUITE - UK ENERGY MARKET")
    print("="*100)
    print(f"\n⚙️  Configuration:")
    print(f"   Project:       {PROJECT_ID}")
    print(f"   Source Dataset: {DATASET_SOURCE}")
    print(f"   Analytics Dataset: {DATASET_ANALYTICS}")
    print(f"   Location:      {LOCATION}")
    print(f"   Date Range:    {DATE_START} to {DATE_END}")
    print(f"   Output Dir:    {OUTDIR}")
    print()
    
    # Load data
    try:
        df = load_data()
    except Exception as e:
        print(f"\n❌ Fatal error loading data: {e}")
        return
    
    print(f"\n📊 Data Summary:")
    print(f"   Rows: {len(df):,}")
    print(f"   Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Columns: {', '.join(df.columns)}")
    print()
    
    # Run analyses
    print("\n" + "="*100)
    print("🔬 RUNNING STATISTICAL ANALYSES")
    print("="*100)
    
    # 1. T-tests
    ttest_df = ttest_analysis(df)
    write_bq(ttest_df, "ttest_results")
    
    # 2. ANOVA
    anova_df = anova_by_season(df)
    write_bq(anova_df, "anova_results")
    
    # 3. Correlations
    corr_df = correlation_analysis(df)
    write_bq(corr_df, "correlation_matrix")
    
    # 4. Regression
    reg_df = regression_demand_price(df)
    write_bq(reg_df, "regression_demand_price")
    
    # 5. ARIMA
    arima_df = arima_forecast(df)
    write_bq(arima_df, "arima_forecast")
    
    # 6. Seasonal Decomposition
    seasonal_df = seasonal_decomposition(df)
    write_bq(seasonal_df, "seasonal_decomposition_stats")
    
    # 7. Frequency-Price
    freq_df = frequency_price_analysis(df)
    write_bq(freq_df, "frequency_price_analysis")
    
    # 8. Balancing Volume
    bal_df = balancing_volume_analysis(df)
    write_bq(bal_df, "balancing_volume_analysis")
    
    print("\n" + "="*100)
    print("✅ ALL ANALYSES COMPLETE!")
    print("="*100)
    print(f"\n📊 Results saved to:")
    print(f"   BigQuery: {PROJECT_ID}.{DATASET_ANALYTICS}.*")
    print(f"   Plots:    {OUTDIR}/*.png")
    print()
    print("📋 Tables created:")
    print("   - ttest_results")
    print("   - anova_results")
    print("   - correlation_matrix")
    print("   - regression_demand_price")
    print("   - arima_forecast")
    print("   - seasonal_decomposition_stats")
    print("   - frequency_price_analysis")
    print("   - balancing_volume_analysis")
    print()


if __name__ == "__main__":
    main()
