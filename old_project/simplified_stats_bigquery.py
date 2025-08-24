"""
Advanced Statistical Analysis for BigQuery UK Energy Data (Simplified)
======================================================================

A simplified version that focuses on available tables:
- neso_interconnector_flows
- neso_wind_forecasts
- neso_carbon_intensity
- neso_balancing_services
- neso_demand_forecasts
- elexon_system_warnings
"""

import pathlib
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

from google.cloud import bigquery
from pandas_gbq import to_gbq

# =========================
# ======== CONFIG =========
# =========================
PROJECT_ID = "jibber-jabber-knowledge"
LOCATION = "europe-west2"
DATASET_SOURCE = "uk_energy_prod"
DATASET_ANALYTICS = "uk_energy_analysis"

# ---- Optional: upload plots to GCS ----
GCS_BUCKET = ""  # Leave empty to save locally

# ---- Date range for analysis ----
DATE_START = "2024-12-01"
DATE_END = "2024-12-31"  # exclusive upper bound

# =========================
# ====== UTILITIES ========
# =========================
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

def save_plot(fig, fname: str):
    """Save plot locally."""
    local_path = OUTDIR / fname
    fig.savefig(local_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
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
def load_data() -> pd.DataFrame:
    """
    Load and harmonize series from available tables:
    - Wind generation: neso_wind_forecasts
    - Demand forecasts: neso_demand_forecasts
    - Interconnector flows: neso_interconnector_flows
    - Carbon intensity: neso_carbon_intensity
    - System warnings: elexon_system_warnings
    - Balancing services: neso_balancing_services
    """
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

    # Time grid (using neso_wind_forecasts as base)
    grid_cte = f"""
    WITH grid AS (
      SELECT
        settlement_date,
        settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT * FROM grid
    """

    # Wind generation (from neso_wind_forecasts)
    wind_cte = f"""
    WITH w AS (
      SELECT
        settlement_date,
        settlement_period,
        AVG(COALESCE(actual_output_mw, forecast_output_mw)) AS wind_generation
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      wind_generation
    FROM w
    """

    # Temperature from demand forecasts
    temp_cte = f"""
    WITH f AS (
      SELECT
        settlement_date,
        settlement_period,
        AVG(temperature_forecast) AS temperature
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_demand_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      temperature
    FROM f
    """

    # Interconnector flows
    interconnector_cte = f"""
    WITH ic AS (
      SELECT
        settlement_date,
        settlement_period,
        SUM(flow_mw) AS total_flow_mw,
        SUM(capacity_mw) AS total_capacity_mw,
        AVG(utilization_pct) AS avg_utilization_pct
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_interconnector_flows`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      total_flow_mw,
      total_capacity_mw,
      avg_utilization_pct
    FROM ic
    """

    # Carbon intensity
    carbon_cte = f"""
    WITH c AS (
      SELECT
        measurement_date AS settlement_date,
        EXTRACT(HOUR FROM measurement_time) * 2 + 
        CASE 
          WHEN EXTRACT(MINUTE FROM measurement_time) >= 30 THEN 2 
          ELSE 1 
        END AS settlement_period,
        AVG(carbon_intensity_gco2_kwh) AS carbon_intensity
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_carbon_intensity`
      WHERE measurement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      carbon_intensity
    FROM c
    """

    # System warnings - convert to settlement periods
    warnings_cte = f"""
    WITH times AS (
      SELECT
        warning_date AS settlement_date,
        warning_id,
        severity,
        start_time,
        COALESCE(end_time, start_time) AS end_time
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.elexon_system_warnings`
      WHERE warning_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
    ),
    periods AS (
      SELECT
        settlement_date,
        settlement_period,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS period_start,
        TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period)*30 MINUTE) AS period_end
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_wind_forecasts`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    ),
    warnings_by_period AS (
      SELECT
        p.settlement_date,
        p.settlement_period,
        COUNT(DISTINCT t.warning_id) AS warning_count,
        MAX(CASE WHEN t.severity = 'HIGH' THEN 1 ELSE 0 END) AS has_severe_warning
      FROM periods p
      LEFT JOIN times t
      ON p.settlement_date = t.settlement_date
      AND (
        (t.start_time < p.period_end AND t.end_time > p.period_start) OR
        (DATE(t.start_time) = p.settlement_date)
      )
      GROUP BY p.settlement_date, p.settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      warning_count,
      CAST(has_severe_warning AS BOOL) AS has_severe_warning
    FROM warnings_by_period
    """

    # Balancing services
    balancing_cte = f"""
    WITH b AS (
      SELECT
        settlement_date,
        settlement_period,
        SUM(cost_pounds) AS total_balancing_cost,
        SUM(volume_mwh) AS total_volume_mwh,
        SAFE_DIVIDE(SUM(cost_pounds), NULLIF(SUM(volume_mwh),0)) AS cost_per_mwh
      FROM `{PROJECT_ID}.{DATASET_SOURCE}.neso_balancing_services`
      WHERE settlement_date BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
      GROUP BY settlement_date, settlement_period
    )
    SELECT 
      settlement_date,
      settlement_period,
      total_balancing_cost,
      total_volume_mwh,
      cost_per_mwh
    FROM b
    """

    # Final join
    sql = f"""
    WITH grid AS ({grid_cte}),
         wind AS ({wind_cte}),
         temp AS ({temp_cte}),
         ic   AS ({interconnector_cte}),
         carb AS ({carbon_cte}),
         warn AS ({warnings_cte}),
         bal  AS ({balancing_cte})
    SELECT
      g.ts,
      g.settlement_date,
      g.settlement_period,
      wind.wind_generation,
      temp.temperature,
      ic.total_flow_mw,
      ic.total_capacity_mw,
      ic.avg_utilization_pct,
      carb.carbon_intensity,
      COALESCE(warn.warning_count, 0) AS warning_count,
      COALESCE(warn.has_severe_warning, FALSE) AS has_severe_warning,
      bal.total_balancing_cost,
      bal.total_volume_mwh,
      bal.cost_per_mwh
    FROM grid g
    LEFT JOIN wind USING (settlement_date, settlement_period)
    LEFT JOIN temp USING (settlement_date, settlement_period)
    LEFT JOIN ic   USING (settlement_date, settlement_period)
    LEFT JOIN carb USING (settlement_date, settlement_period)
    LEFT JOIN warn USING (settlement_date, settlement_period)
    LEFT JOIN bal  USING (settlement_date, settlement_period)
    WHERE g.ts >= TIMESTAMP('{DATE_START}') AND g.ts < TIMESTAMP('{DATE_END}')
    ORDER BY g.ts
    """

    df = client.query(sql).to_dataframe(create_bqstorage_client=True)
    if df.empty:
        raise RuntimeError("No data returned from BigQuery for the specified date range.")
    
    df = add_calendar_fields(df, "ts")
    return df

# =========================
# ====== STATISTICS =======
# =========================
def correlation_matrix(df: pd.DataFrame):
    """Calculate correlation matrix between numeric columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return pd.DataFrame()
    cm = df[numeric_cols].corr(method="pearson")
    cm = cm.reset_index().rename(columns={"index": "variable"})
    return cm

def correlation_heatmap(corr_df):
    """Create correlation heatmap."""
    if corr_df.empty:
        return None
    
    corr_matrix = corr_df.set_index('variable')
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    plt.colorbar(im, ax=ax)
    
    # Add variable names
    variables = corr_matrix.index
    ax.set_xticks(np.arange(len(variables)))
    ax.set_yticks(np.arange(len(variables)))
    ax.set_xticklabels(variables, rotation=45, ha="right")
    ax.set_yticklabels(variables)
    
    # Add correlation values
    for i in range(len(variables)):
        for j in range(len(variables)):
            text = ax.text(j, i, f"{corr_matrix.iloc[i, j]:.2f}",
                          ha="center", va="center", color="black" if abs(corr_matrix.iloc[i, j]) < 0.6 else "white")
    
    ax.set_title("Correlation Matrix")
    fig.tight_layout()
    
    return save_plot(fig, "correlation_heatmap.png")

def seasonal_analysis(df: pd.DataFrame, target_col='wind_generation'):
    """Analyze seasonal patterns."""
    if target_col not in df.columns or df[target_col].isna().all():
        return pd.DataFrame()
    
    # Group by month
    monthly = df.groupby('month')[target_col].agg(['mean', 'std', 'count']).reset_index()
    monthly['month_name'] = monthly['month'].apply(lambda m: datetime(2000, m, 1).strftime('%B'))
    
    # Group by day of week
    dow = df.groupby('dow')[target_col].agg(['mean', 'std', 'count']).reset_index()
    dow['day_name'] = dow['dow'].apply(lambda d: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][d])
    
    # Group by season
    seasonal = df.groupby('season')[target_col].agg(['mean', 'std', 'count']).reset_index()
    
    # Plot seasonal patterns
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Month plot
    months = monthly['month_name']
    ax1.bar(months, monthly['mean'], yerr=monthly['std']/np.sqrt(monthly['count']))
    ax1.set_title(f'{target_col} by Month')
    ax1.set_xticklabels(months, rotation=45)
    
    # Day of week plot
    days = dow['day_name']
    ax2.bar(days, dow['mean'], yerr=dow['std']/np.sqrt(dow['count']))
    ax2.set_title(f'{target_col} by Day of Week')
    ax2.set_xticklabels(days, rotation=45)
    
    plt.tight_layout()
    monthly_plot_path = save_plot(fig, f"{target_col}_seasonal.png")
    
    # Return a dataframe with the analysis
    result = pd.concat([
        monthly[['month', 'month_name', 'mean', 'std', 'count']].rename(columns={'month': 'period_num', 'month_name': 'period_name'}),
        dow[['dow', 'day_name', 'mean', 'std', 'count']].rename(columns={'dow': 'period_num', 'day_name': 'period_name'}),
        seasonal[['season', 'mean', 'std', 'count']].rename(columns={'season': 'period_name'}).assign(period_num=np.nan)
    ])
    
    result['metric'] = target_col
    result['period_type'] = ['month']*len(monthly) + ['day_of_week']*len(dow) + ['season']*len(seasonal)
    result['plot_path'] = monthly_plot_path
    
    return result

def regression_model(df: pd.DataFrame, y_col='carbon_intensity', x_cols=None):
    """Run regression model."""
    if y_col not in df.columns:
        return pd.DataFrame()
    
    if x_cols is None:
        # Use available numeric predictors
        all_numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        x_cols = [col for col in all_numeric if col != y_col and col not in ['settlement_period', 'month', 'dow']]
    
    # Clean data for regression
    model_data = df[[y_col] + x_cols].dropna()
    if len(model_data) < 30:
        return pd.DataFrame()
    
    # Run regression
    X = sm.add_constant(model_data[x_cols].astype(float))
    y = model_data[y_col].astype(float)
    model = sm.OLS(y, X).fit()
    
    # Collect results
    results = {
        'model': f'OLS_{y_col}',
        'n_obs': int(model.nobs),
        'r_squared': float(model.rsquared),
        'adj_r_squared': float(model.rsquared_adj),
        'intercept': float(model.params.get('const', np.nan)),
        'p_intercept': float(model.pvalues.get('const', np.nan)),
    }
    
    # Add coefficients and p-values for each predictor
    for col in x_cols:
        results[f'beta_{col}'] = float(model.params.get(col, np.nan))
        results[f'p_{col}'] = float(model.pvalues.get(col, np.nan))
    
    return pd.DataFrame([results])

def time_series_decomposition(df: pd.DataFrame, col='wind_generation', period=48):
    """Decompose time series into trend, seasonal, and residual components."""
    if col not in df.columns:
        return pd.DataFrame()
    
    # Create time series
    ts = df.sort_values('ts').set_index('ts')[col].dropna()
    if len(ts) < period * 2:
        return pd.DataFrame()
    
    # Fill small gaps if needed
    ts = ts.asfreq('30min', method='ffill')
    
    # Decompose
    decomposition = seasonal_decompose(ts, period=period, model='additive')
    
    # Plot
    fig, axes = plt.subplots(4, 1, figsize=(10, 12))
    
    # Original
    axes[0].plot(ts.index, ts.values)
    axes[0].set_title('Original')
    axes[0].set_xticklabels([])
    
    # Trend
    axes[1].plot(decomposition.trend.index, decomposition.trend.values)
    axes[1].set_title('Trend')
    axes[1].set_xticklabels([])
    
    # Seasonal
    axes[2].plot(decomposition.seasonal.index, decomposition.seasonal.values)
    axes[2].set_title('Seasonal')
    axes[2].set_xticklabels([])
    
    # Residual
    axes[3].plot(decomposition.resid.index, decomposition.resid.values)
    axes[3].set_title('Residual')
    
    plt.tight_layout()
    plot_path = save_plot(fig, f"{col}_decomposition.png")
    
    # Calculate statistics
    trend_mean = decomposition.trend.mean()
    trend_std = decomposition.trend.std()
    seasonal_mean = decomposition.seasonal.mean()
    seasonal_std = decomposition.seasonal.std()
    resid_mean = decomposition.resid.mean()
    resid_std = decomposition.resid.std()
    
    # Create output DataFrame
    result = pd.DataFrame([{
        'metric': col,
        'period': period,
        'trend_mean': trend_mean,
        'trend_std': trend_std,
        'seasonal_mean': seasonal_mean,
        'seasonal_std': seasonal_std,
        'resid_mean': resid_mean,
        'resid_std': resid_std,
        'plot_path': plot_path
    }])
    
    return result

# =========================
# ========= MAIN ==========
# =========================
def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Loading harmonized data from BigQuery uk_energy…")
    df = load_data()
    print(f"[INFO] Loaded {len(df):,} rows")

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

    # ===== Seasonal Analysis =====
    print("[RUN] Seasonal Analysis - Wind Generation")
    seasonal_wind = seasonal_analysis(df, 'wind_generation')
    write_bq(seasonal_wind, "seasonal_wind_generation")
    
    print("[RUN] Seasonal Analysis - Carbon Intensity")
    seasonal_carbon = seasonal_analysis(df, 'carbon_intensity')
    write_bq(seasonal_carbon, "seasonal_carbon_intensity")
    
    print("[RUN] Seasonal Analysis - Interconnector Flow")
    seasonal_flow = seasonal_analysis(df, 'total_flow_mw')
    write_bq(seasonal_flow, "seasonal_interconnector_flow")

    # ===== Regression Models =====
    print("[RUN] Regression: Carbon Intensity ~ Wind + Temperature")
    reg_carbon = regression_model(df, 'carbon_intensity', ['wind_generation', 'temperature'])
    write_bq(reg_carbon, "regression_carbon_intensity")
    
    print("[RUN] Regression: Balancing Cost ~ Wind + Temperature + Carbon Intensity")
    reg_balancing = regression_model(df, 'cost_per_mwh', ['wind_generation', 'temperature', 'carbon_intensity'])
    write_bq(reg_balancing, "regression_balancing_cost")

    # ===== Time Series Decomposition =====
    print("[RUN] Time Series Decomposition: Wind Generation")
    decomp_wind = time_series_decomposition(df, 'wind_generation', period=48)  # 48 periods per day
    write_bq(decomp_wind, "decomposition_wind")
    
    print("[RUN] Time Series Decomposition: Carbon Intensity")
    decomp_carbon = time_series_decomposition(df, 'carbon_intensity', period=48)
    write_bq(decomp_carbon, "decomposition_carbon")

    print("[DONE] All analyses complete.")

if __name__ == "__main__":
    main()
