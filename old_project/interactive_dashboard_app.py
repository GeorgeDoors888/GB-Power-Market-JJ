import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta
import numpy as np
import os
import io
import math
import pathlib
import time

# Optional imports with graceful fallback
try:
    import statsmodels.api as sm
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

try:
    import matplotlib
    matplotlib.use("Agg")  # headless
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    from google.cloud import storage as gcs_storage
    HAS_GCS = True
except Exception:
    HAS_GCS = False

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Updated to use the new europe-west2 dataset
DATASET_ANALYTICS = "uk_energy_analytics"  # For advanced stats results

# Ensure output directory exists
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

# Corrected table names and their corresponding date/value columns
TABLE_CONFIG = {
    "demand": {
        "table_name": "neso_demand_forecasts",
        "date_col": "settlement_date",
        "value_col": "demand",
        "numeric_cols": ["demand"],
        # Mapping from table columns to the columns expected by plot functions
        "column_map": {
            "settlement_date": "day",
            "demand": "peak_demand"
        }
    },
    "generation": {
        "table_name": "neso_wind_forecasts",
        "date_col": "settlement_date",
        "value_col": "quantity",
        "numeric_cols": ["quantity"],
        "column_map": {
            "quantity": "generation"
        }
    },
    "balancing": {
        "table_name": "neso_balancing_services",
        "date_col": "settlement_date", # Assuming this table also has a date column
        "value_col": "so_so_prices",
        "numeric_cols": ["so_so_prices", "so_nb_prices"],
         "column_map": {
            "service_type": "acceptance_type", # Example mapping
            "so_so_prices": "total_volume_mwh" # Example mapping
        }
    }
}

# --- BigQuery ---
@st.cache_resource(ttl=3600)
def get_bq_client():
    """Initializes and returns a BigQuery client, caching the resource."""
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        return None

def _qualified(table_name: str) -> str:
    """Returns the fully qualified BigQuery table name."""
    return f"`{PROJECT_ID}.{DATASET_ID}.{table_name}`"

@st.cache_data(ttl=3600)
def get_available_date_range(_client: bigquery.Client) -> tuple[date | None, date | None]:
    """
    Queries the demand forecast table to find the min and max available dates.
    This is more reliable than checking all tables.
    """
    config = TABLE_CONFIG["demand"]
    table_name = config["table_name"]
    date_col = config["date_col"]
    
    try:
        q = f"SELECT MIN(CAST({date_col} AS DATE)) AS min_d, MAX(CAST({date_col} AS DATE)) AS max_d FROM {_qualified(table_name)}"
        result = list(_client.query(q).result())
        if result:
            row = result[0]
            if row.min_d and row.max_d:
                return row.min_d, row.max_d
    except Exception as e:
        st.warning(f"Could not determine date range from {table_name}: {e}")
        pass
    return None, None


@st.cache_data(ttl=3600)
def fetch_data(_client: bigquery.Client, config_key: str, start_d: date, end_d: date) -> pd.DataFrame:
    """
    Fetches data from a specified table and renames columns based on the config.
    Handles schema differences gracefully.
    """
    config = TABLE_CONFIG[config_key]
    table_name = config["table_name"]
    date_col = config.get("date_col")
    
    try:
        # First check if the date_col exists in the table schema
        schema_q = f"SELECT * FROM {_qualified(table_name)} LIMIT 0"
        schema_job = _client.query(schema_q)
        schema_df = schema_job.to_dataframe()
        columns = schema_df.columns.tolist()
        
        # If the date column doesn't exist, try charge_date as fallback
        if date_col and date_col not in columns:
            fallback_cols = ['charge_date', 'forecast_date']
            for col in fallback_cols:
                if col in columns:
                    st.warning(f"Column '{date_col}' not found, using '{col}' instead.")
                    date_col = col
                    break
        
        if date_col and date_col in columns:
            q = f"""
            SELECT *
            FROM {_qualified(table_name)}
            WHERE CAST({date_col} AS DATE) BETWEEN @start_d AND @end_d
            ORDER BY {date_col}
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_d", "DATE", start_d),
                    bigquery.ScalarQueryParameter("end_d", "DATE", end_d),
                ]
            )
            job = _client.query(q, job_config=job_config)
        else:
            q = f"SELECT * FROM {_qualified(table_name)}"
            job = _client.query(q)

        df = job.to_dataframe()

        # Coerce to numeric types
        for col in config.get("numeric_cols", []):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Rename columns for plotting functions
        if "column_map" in config:
            # Only rename columns that exist
            column_map = {k: v for k, v in config["column_map"].items() if k in df.columns}
            df = df.rename(columns=column_map)
            
        # Special handling for generation mix
        if config_key == "generation" and "generation" in df.columns:
            df['fuel_type'] = 'WIND' # Hardcode fuel type for wind forecast data
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

# --- Plotting ---
def create_demand_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not df.empty and "peak_demand" in df.columns and "day" in df.columns:
        fig.add_trace(go.Scatter(x=df["day"], y=df["peak_demand"], mode="lines", name="Peak Demand"))
    fig.update_layout(title="Daily Peak Demand", xaxis_title="Date", yaxis_title="Demand (MW)", template="plotly_white")
    return fig

def create_bod_volume_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not df.empty and "acceptance_type" in df.columns and "total_volume_mwh" in df.columns:
        fig.add_trace(go.Bar(x=df["acceptance_type"], y=df["total_volume_mwh"]))
    fig.update_layout(title="Total Accepted Bid and Offer Volume", xaxis_title="Acceptance Type", yaxis_title="Total Volume (MWh)", template="plotly_white")
    return fig

def create_generation_mix_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if not df.empty and "fuel_type" in df.columns and "generation" in df.columns:
        agg = df.groupby("fuel_type")["generation"].sum().reset_index()
        fig.add_trace(go.Pie(labels=agg["fuel_type"], values=agg["generation"], hole=0.3))
    fig.update_layout(title="Generation Mix Snapshot (Wind Only)", template="plotly_white")
    return fig

# --- UI ---
st.set_page_config(page_title="GB Energy Dashboard", layout="wide")
st.title("GB Energy Market Dashboard")
st.markdown("An interactive dashboard to analyze Great Britain electricity data from NESO.")

client = get_bq_client()
if not client:
    st.error("Dashboard cannot load. Failed to initialize BigQuery connection.")
    st.stop()

min_d, max_d = get_available_date_range(client)
if not (min_d and max_d):
    st.error("No data available in BigQuery table 'neso_demand_forecasts'. Please check data ingestion.")
    st.stop()

st.sidebar.header("Dashboard Controls")
st.sidebar.caption(f"Available data: {min_d.strftime('%d %b %Y')} to {max_d.strftime('%d %b %Y')}")

# Default to the last 7 days of available data
default_start = max_d - timedelta(days=6)
start_date = st.sidebar.date_input("Start Date", value=default_start, min_value=min_d, max_value=max_d)
end_date = st.sidebar.date_input("End Date", value=max_d, min_value=start_date, max_value=max_d)

if st.sidebar.button("Clear Cache & Rerun"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

if start_date > end_date:
    st.warning("Start date cannot be after end date.")
    st.stop()

# Make tabs more visible
st.markdown("### Dashboard Tabs - Click to navigate")
tab1, tab2, tab3, tab4 = st.tabs(["Demand Analysis", "Generation Analysis", "Balancing Analysis", "ADVANCED STATISTICS ← CLICK HERE"])

with tab1:
    st.header("National Demand Forecast")
    with st.spinner(f"Fetching demand data for {start_date} → {end_date}..."):
        demand_df = fetch_data(client, "demand", start_date, end_date)
    if demand_df.empty:
        st.info("No demand data available for the selected period.")
    else:
        st.plotly_chart(create_demand_chart(demand_df), use_container_width=True)
        st.dataframe(demand_df.head())

with tab2:
    st.header("Wind Generation Forecast")
    with st.spinner(f"Fetching wind generation data for {start_date} → {end_date}..."):
        generation_df = fetch_data(client, "generation", start_date, end_date)
    if generation_df.empty:
        st.info("No wind generation data available for the selected period.")
    else:
        st.plotly_chart(create_generation_mix_chart(generation_df), use_container_width=True)
        st.dataframe(generation_df.head())

with tab3:
    st.header("Balancing Services")
    with st.spinner(f"Fetching balancing services data for {start_date} → {end_date}..."):
        balancing_df = fetch_data(client, "balancing", start_date, end_date)
    if balancing_df.empty:
        st.info("No balancing services data available for the selected period.")
    else:
        # Note: The chart for balancing might not be meaningful with current mappings
        st.plotly_chart(create_bod_volume_chart(balancing_df), use_container_width=True)
        st.dataframe(balancing_df.head())

with tab4:
    st.header("🔍 ADVANCED STATISTICAL ANALYSIS")
    st.success("You are now in the Advanced Statistics tab!")
    
    # Get data for all tabs to use in statistical analysis
    if all(df.empty for df in [demand_df, generation_df, balancing_df]):
        st.info("No data available for the selected period for statistical analysis.")
    else:
        # Create sections for different types of statistical analysis
        st.subheader("Select Analysis Type")
        analysis_type = st.selectbox(
            "Choose the type of statistical analysis:",
            ["Descriptive Statistics", "Correlation Analysis", "Time Series Analysis", "Hypothesis Testing", "Regression Analysis"]
        )
        
        # Descriptive Statistics Section
        if analysis_type == "Descriptive Statistics":
            st.subheader("Descriptive Statistics")
            dataset_option = st.selectbox(
                "Select dataset for descriptive statistics:",
                ["Demand", "Wind Generation", "Balancing Services"],
                key="desc_dataset"
            )
            
            if dataset_option == "Demand" and not demand_df.empty:
                df = demand_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if numeric_cols:
                    col_to_analyze = st.selectbox("Select column for analysis:", numeric_cols, key="desc_demand_col")
                    if st.button("Calculate Descriptive Statistics", key="desc_demand_btn"):
                        with st.spinner("Calculating descriptive statistics..."):
                            stats_df = pd.DataFrame({
                                "Statistic": ["Mean", "Median", "Standard Deviation", "Min", "Max", "25th Percentile", "75th Percentile"],
                                "Value": [
                                    df[col_to_analyze].mean(),
                                    df[col_to_analyze].median(),
                                    df[col_to_analyze].std(),
                                    df[col_to_analyze].min(),
                                    df[col_to_analyze].max(),
                                    df[col_to_analyze].quantile(0.25),
                                    df[col_to_analyze].quantile(0.75)
                                ]
                            })
                            st.dataframe(stats_df)
                            
                            # Create histogram
                            fig = px.histogram(df, x=col_to_analyze, nbins=20, title=f"Distribution of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Create box plot
                            fig = px.box(df, y=col_to_analyze, title=f"Box Plot of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No numeric columns found in the demand dataset.")
            
            elif dataset_option == "Wind Generation" and not generation_df.empty:
                df = generation_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if numeric_cols:
                    col_to_analyze = st.selectbox("Select column for analysis:", numeric_cols, key="desc_gen_col")
                    if st.button("Calculate Descriptive Statistics", key="desc_gen_btn"):
                        with st.spinner("Calculating descriptive statistics..."):
                            stats_df = pd.DataFrame({
                                "Statistic": ["Mean", "Median", "Standard Deviation", "Min", "Max", "25th Percentile", "75th Percentile"],
                                "Value": [
                                    df[col_to_analyze].mean(),
                                    df[col_to_analyze].median(),
                                    df[col_to_analyze].std(),
                                    df[col_to_analyze].min(),
                                    df[col_to_analyze].max(),
                                    df[col_to_analyze].quantile(0.25),
                                    df[col_to_analyze].quantile(0.75)
                                ]
                            })
                            st.dataframe(stats_df)
                            
                            # Create histogram
                            fig = px.histogram(df, x=col_to_analyze, nbins=20, title=f"Distribution of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Create box plot
                            fig = px.box(df, y=col_to_analyze, title=f"Box Plot of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No numeric columns found in the wind generation dataset.")
            
            elif dataset_option == "Balancing Services" and not balancing_df.empty:
                df = balancing_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if numeric_cols:
                    col_to_analyze = st.selectbox("Select column for analysis:", numeric_cols, key="desc_bal_col")
                    if st.button("Calculate Descriptive Statistics", key="desc_bal_btn"):
                        with st.spinner("Calculating descriptive statistics..."):
                            stats_df = pd.DataFrame({
                                "Statistic": ["Mean", "Median", "Standard Deviation", "Min", "Max", "25th Percentile", "75th Percentile"],
                                "Value": [
                                    df[col_to_analyze].mean(),
                                    df[col_to_analyze].median(),
                                    df[col_to_analyze].std(),
                                    df[col_to_analyze].min(),
                                    df[col_to_analyze].max(),
                                    df[col_to_analyze].quantile(0.25),
                                    df[col_to_analyze].quantile(0.75)
                                ]
                            })
                            st.dataframe(stats_df)
                            
                            # Create histogram
                            fig = px.histogram(df, x=col_to_analyze, nbins=20, title=f"Distribution of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Create box plot
                            fig = px.box(df, y=col_to_analyze, title=f"Box Plot of {col_to_analyze}")
                            st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No numeric columns found in the balancing services dataset.")
            else:
                st.info(f"No {dataset_option} data available for the selected period.")
        
        # Correlation Analysis Section
        elif analysis_type == "Correlation Analysis":
            st.subheader("Correlation Analysis")
            
            dataset_option = st.selectbox(
                "Select dataset for correlation analysis:",
                ["Demand", "Wind Generation", "Balancing Services"],
                key="corr_dataset"
            )
            
            if dataset_option == "Demand" and not demand_df.empty:
                df = demand_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if len(numeric_cols) >= 2:
                    col1 = st.selectbox("Select first column:", numeric_cols, key="corr_col1")
                    col2 = st.selectbox("Select second column:", [c for c in numeric_cols if c != col1], key="corr_col2")
                    
                    if st.button("Calculate Correlation", key="corr_demand_btn"):
                        with st.spinner("Calculating correlation..."):
                            # Calculate Pearson correlation
                            corr = df[col1].corr(df[col2])
                            st.metric("Pearson Correlation Coefficient", f"{corr:.4f}")
                            
                            # Create scatter plot
                            fig = px.scatter(df, x=col1, y=col2, trendline="ols", 
                                            title=f"Correlation between {col1} and {col2}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate additional correlation metrics
                            if HAS_STATSMODELS:
                                from scipy.stats import pearsonr, spearmanr
                                pearson_r, p_value = pearsonr(df[col1].dropna(), df[col2].dropna())
                                spearman_r, spearman_p = spearmanr(df[col1].dropna(), df[col2].dropna())
                                
                                st.write("Correlation Statistics:")
                                corr_stats = pd.DataFrame({
                                    "Metric": ["Pearson r", "P-value", "Spearman rank"],
                                    "Value": [f"{pearson_r:.4f}", f"{p_value:.4f}", f"{spearman_r:.4f}"]
                                })
                                st.dataframe(corr_stats)
                                
                                if p_value < 0.05:
                                    st.success("The correlation is statistically significant (p < 0.05).")
                                else:
                                    st.info("The correlation is not statistically significant (p >= 0.05).")
                else:
                    st.warning("Need at least two numeric columns for correlation analysis.")
            
            elif dataset_option == "Wind Generation" and not generation_df.empty:
                df = generation_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if len(numeric_cols) >= 2:
                    col1 = st.selectbox("Select first column:", numeric_cols, key="corr_col1_gen")
                    col2 = st.selectbox("Select second column:", [c for c in numeric_cols if c != col1], key="corr_col2_gen")
                    
                    if st.button("Calculate Correlation", key="corr_gen_btn"):
                        with st.spinner("Calculating correlation..."):
                            # Calculate Pearson correlation
                            corr = df[col1].corr(df[col2])
                            st.metric("Pearson Correlation Coefficient", f"{corr:.4f}")
                            
                            # Create scatter plot
                            fig = px.scatter(df, x=col1, y=col2, trendline="ols", 
                                            title=f"Correlation between {col1} and {col2}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate additional correlation metrics
                            if HAS_STATSMODELS:
                                from scipy.stats import pearsonr, spearmanr
                                pearson_r, p_value = pearsonr(df[col1].dropna(), df[col2].dropna())
                                spearman_r, spearman_p = spearmanr(df[col1].dropna(), df[col2].dropna())
                                
                                st.write("Correlation Statistics:")
                                corr_stats = pd.DataFrame({
                                    "Metric": ["Pearson r", "P-value", "Spearman rank"],
                                    "Value": [f"{pearson_r:.4f}", f"{p_value:.4f}", f"{spearman_r:.4f}"]
                                })
                                st.dataframe(corr_stats)
                                
                                if p_value < 0.05:
                                    st.success("The correlation is statistically significant (p < 0.05).")
                                else:
                                    st.info("The correlation is not statistically significant (p >= 0.05).")
                else:
                    st.warning("Need at least two numeric columns for correlation analysis.")
            
            elif dataset_option == "Balancing Services" and not balancing_df.empty:
                df = balancing_df
                numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                if len(numeric_cols) >= 2:
                    col1 = st.selectbox("Select first column:", numeric_cols, key="corr_col1_bal")
                    col2 = st.selectbox("Select second column:", [c for c in numeric_cols if c != col1], key="corr_col2_bal")
                    
                    if st.button("Calculate Correlation", key="corr_bal_btn"):
                        with st.spinner("Calculating correlation..."):
                            # Calculate Pearson correlation
                            corr = df[col1].corr(df[col2])
                            st.metric("Pearson Correlation Coefficient", f"{corr:.4f}")
                            
                            # Create scatter plot
                            fig = px.scatter(df, x=col1, y=col2, trendline="ols", 
                                            title=f"Correlation between {col1} and {col2}")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Calculate additional correlation metrics
                            if HAS_STATSMODELS:
                                from scipy.stats import pearsonr, spearmanr
                                pearson_r, p_value = pearsonr(df[col1].dropna(), df[col2].dropna())
                                spearman_r, spearman_p = spearmanr(df[col1].dropna(), df[col2].dropna())
                                
                                st.write("Correlation Statistics:")
                                corr_stats = pd.DataFrame({
                                    "Metric": ["Pearson r", "P-value", "Spearman rank"],
                                    "Value": [f"{pearson_r:.4f}", f"{p_value:.4f}", f"{spearman_r:.4f}"]
                                })
                                st.dataframe(corr_stats)
                                
                                if p_value < 0.05:
                                    st.success("The correlation is statistically significant (p < 0.05).")
                                else:
                                    st.info("The correlation is not statistically significant (p >= 0.05).")
                else:
                    st.warning("Need at least two numeric columns for correlation analysis.")
            else:
                st.info(f"No {dataset_option} data available for the selected period.")
                
        # Time Series Analysis Section
        elif analysis_type == "Time Series Analysis":
            st.subheader("Time Series Analysis")
            
            if not HAS_STATSMODELS:
                st.error("This analysis requires the statsmodels package, which is not installed.")
            else:
                dataset_option = st.selectbox(
                    "Select dataset for time series analysis:",
                    ["Demand", "Wind Generation", "Balancing Services"],
                    key="ts_dataset"
                )
                
                ts_analysis_type = st.selectbox(
                    "Select time series analysis type:",
                    ["Seasonal Decomposition", "ARIMA Forecasting", "Moving Averages"],
                    key="ts_analysis_type"
                )
                
                if dataset_option == "Demand" and not demand_df.empty:
                    df = demand_df
                    date_col = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_dtype(df[col]) or "date" in col.lower() or "day" in col.lower():
                            date_col = col
                            break
                    
                    if date_col is None:
                        st.warning("No date column found in the demand dataset.")
                    else:
                        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                        if numeric_cols:
                            value_col = st.selectbox("Select value column for time series analysis:", numeric_cols, key="ts_value_col")
                            
                            # Ensure DataFrame is sorted by date and has no duplicates
                            df = df.sort_values(by=date_col)
                            
                            # Convert to datetime if not already
                            if not pd.api.types.is_datetime64_dtype(df[date_col]):
                                df[date_col] = pd.to_datetime(df[date_col])
                            
                            # Set the date column as index
                            ts_df = df.set_index(date_col)
                            
                            # Seasonal Decomposition
                            if ts_analysis_type == "Seasonal Decomposition" and len(ts_df) >= 4:
                                st.write("Seasonal Decomposition breaks a time series into trend, seasonal, and residual components.")
                                
                                # Options for decomposition
                                freq = st.selectbox("Select frequency:", ["Daily", "Weekly", "Monthly"], index=1, key="ts_freq")
                                model_type = st.selectbox("Select decomposition type:", ["Additive", "Multiplicative"], key="ts_model_type")
                                
                                freq_map = {"Daily": 1, "Weekly": 7, "Monthly": 30}
                                period = freq_map[freq]
                                
                                if st.button("Perform Seasonal Decomposition", key="ts_decomp_btn"):
                                    with st.spinner("Performing seasonal decomposition..."):
                                        if len(ts_df) < 2 * period:
                                            st.warning(f"Not enough data points for {freq} decomposition. Need at least {2 * period} points.")
                                        else:
                                            try:
                                                # Perform decomposition
                                                decomposition = seasonal_decompose(
                                                    ts_df[value_col].dropna(), 
                                                    model='additive' if model_type == "Additive" else "multiplicative",
                                                    period=period
                                                )
                                                
                                                # Create plot
                                                fig = make_subplots(
                                                    rows=4, cols=1,
                                                    subplot_titles=("Observed", "Trend", "Seasonal", "Residual"),
                                                    vertical_spacing=0.1,
                                                    shared_xaxes=True
                                                )
                                                
                                                # Add traces
                                                fig.add_trace(go.Scatter(x=decomposition.observed.index, y=decomposition.observed, name="Observed"), row=1, col=1)
                                                fig.add_trace(go.Scatter(x=decomposition.trend.index, y=decomposition.trend, name="Trend"), row=2, col=1)
                                                fig.add_trace(go.Scatter(x=decomposition.seasonal.index, y=decomposition.seasonal, name="Seasonal"), row=3, col=1)
                                                fig.add_trace(go.Scatter(x=decomposition.resid.index, y=decomposition.resid, name="Residual"), row=4, col=1)
                                                
                                                fig.update_layout(height=800, title_text="Seasonal Decomposition")
                                                st.plotly_chart(fig, use_container_width=True)
                                                
                                                # Show components as DataFrames
                                                with st.expander("View decomposition components as data"):
                                                    components = pd.DataFrame({
                                                        'Observed': decomposition.observed,
                                                        'Trend': decomposition.trend,
                                                        'Seasonal': decomposition.seasonal,
                                                        'Residual': decomposition.resid
                                                    })
                                                    st.dataframe(components)
                                            except Exception as e:
                                                st.error(f"Error in decomposition: {str(e)}")
                            
                            # ARIMA Forecasting
                            elif ts_analysis_type == "ARIMA Forecasting":
                                st.write("ARIMA (AutoRegressive Integrated Moving Average) is used for time series forecasting.")
                                
                                # Parameters for ARIMA
                                p = st.slider("p (AR order):", 0, 5, 1, key="ts_arima_p")
                                d = st.slider("d (Differencing):", 0, 2, 1, key="ts_arima_d")
                                q = st.slider("q (MA order):", 0, 5, 1, key="ts_arima_q")
                                
                                forecast_steps = st.slider("Forecast periods:", 1, 30, 7, key="ts_arima_steps")
                                
                                if st.button("Perform ARIMA Forecast", key="ts_arima_btn"):
                                    with st.spinner("Performing ARIMA forecast..."):
                                        try:
                                            # Prepare time series data
                                            ts_data = ts_df[value_col].dropna()
                                            
                                            if len(ts_data) < 10:
                                                st.warning("Not enough data points for ARIMA forecasting. Need at least 10 points.")
                                            else:
                                                # Fit ARIMA model
                                                model = SARIMAX(ts_data, order=(p, d, q))
                                                model_fit = model.fit(disp=False)
                                                
                                                # Get forecast
                                                forecast = model_fit.forecast(steps=forecast_steps)
                                                
                                                # Create date range for forecast
                                                last_date = ts_data.index[-1]
                                                if isinstance(last_date, pd.Timestamp):
                                                    date_freq = pd.infer_freq(ts_data.index)
                                                    if date_freq is None:
                                                        # Try to estimate frequency
                                                        if len(ts_data.index) >= 2:
                                                            avg_diff = (ts_data.index[-1] - ts_data.index[0]) / len(ts_data.index)
                                                            # If average difference is close to a day
                                                            if 0.8 <= avg_diff.total_seconds() / (24*3600) <= 1.2:
                                                                date_freq = 'D'
                                                            else:
                                                                date_freq = 'D'  # Default to daily if can't determine
                                                        else:
                                                            date_freq = 'D'  # Default to daily
                                                    
                                                    forecast_idx = pd.date_range(start=last_date + pd.Timedelta(days=1), 
                                                                               periods=forecast_steps, 
                                                                               freq=date_freq)
                                                else:
                                                    # Numeric index
                                                    forecast_idx = range(len(ts_data), len(ts_data) + forecast_steps)
                                                
                                                # Plot results
                                                fig = go.Figure()
                                                
                                                # Historical data
                                                fig.add_trace(go.Scatter(
                                                    x=ts_data.index, 
                                                    y=ts_data.values, 
                                                    mode='lines',
                                                    name='Historical Data'
                                                ))
                                                
                                                # Forecast
                                                fig.add_trace(go.Scatter(
                                                    x=forecast_idx, 
                                                    y=forecast.values, 
                                                    mode='lines',
                                                    name='Forecast',
                                                    line=dict(dash='dash')
                                                ))
                                                
                                                fig.update_layout(
                                                    title=f'ARIMA({p},{d},{q}) Forecast for {value_col}',
                                                    xaxis_title='Date',
                                                    yaxis_title=value_col,
                                                    legend=dict(x=0, y=1, traceorder='normal')
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                                
                                                # Show model summary
                                                with st.expander("View ARIMA model summary"):
                                                    st.text(model_fit.summary().tables[1].as_text())
                                                
                                                # Show forecast as DataFrame
                                                with st.expander("View forecast data"):
                                                    forecast_df = pd.DataFrame({
                                                        'Date': forecast_idx,
                                                        'Forecast': forecast.values
                                                    })
                                                    st.dataframe(forecast_df)
                                        except Exception as e:
                                            st.error(f"Error in ARIMA forecasting: {str(e)}")
                            
                            # Moving Averages
                            elif ts_analysis_type == "Moving Averages":
                                st.write("Moving averages smooth out short-term fluctuations to highlight longer-term trends.")
                                
                                window_size = st.slider("Window size (days):", 2, 30, 7, key="ts_ma_window")
                                
                                if st.button("Calculate Moving Averages", key="ts_ma_btn"):
                                    with st.spinner("Calculating moving averages..."):
                                        try:
                                            # Calculate moving averages
                                            ts_data = ts_df[value_col].dropna()
                                            
                                            if len(ts_data) < window_size:
                                                st.warning(f"Not enough data points. Need at least {window_size} points.")
                                            else:
                                                # Simple Moving Average (SMA)
                                                sma = ts_data.rolling(window=window_size).mean()
                                                
                                                # Exponential Moving Average (EMA)
                                                ema = ts_data.ewm(span=window_size).mean()
                                                
                                                # Plot results
                                                fig = go.Figure()
                                                
                                                # Original data
                                                fig.add_trace(go.Scatter(
                                                    x=ts_data.index, 
                                                    y=ts_data.values, 
                                                    mode='lines',
                                                    name='Original Data'
                                                ))
                                                
                                                # SMA
                                                fig.add_trace(go.Scatter(
                                                    x=sma.index, 
                                                    y=sma.values, 
                                                    mode='lines',
                                                    name=f'SMA ({window_size} days)'
                                                ))
                                                
                                                # EMA
                                                fig.add_trace(go.Scatter(
                                                    x=ema.index, 
                                                    y=ema.values, 
                                                    mode='lines',
                                                    name=f'EMA ({window_size} days)'
                                                ))
                                                
                                                fig.update_layout(
                                                    title=f'Moving Averages for {value_col}',
                                                    xaxis_title='Date',
                                                    yaxis_title=value_col,
                                                    legend=dict(x=0, y=1, traceorder='normal')
                                                )
                                                
                                                st.plotly_chart(fig, use_container_width=True)
                                                
                                                # Show moving averages as DataFrame
                                                with st.expander("View moving averages data"):
                                                    ma_df = pd.DataFrame({
                                                        'Original': ts_data.values,
                                                        f'SMA ({window_size} days)': sma.values,
                                                        f'EMA ({window_size} days)': ema.values
                                                    }, index=ts_data.index)
                                                    st.dataframe(ma_df)
                                        except Exception as e:
                                            st.error(f"Error in calculating moving averages: {str(e)}")
                        else:
                            st.warning("No numeric columns found in the demand dataset.")
                
                elif dataset_option == "Wind Generation" and not generation_df.empty:
                    df = generation_df
                    date_col = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_dtype(df[col]) or "date" in col.lower() or "day" in col.lower():
                            date_col = col
                            break
                    
                    if date_col is None:
                        st.warning("No date column found in the wind generation dataset.")
                    else:
                        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                        if numeric_cols:
                            # Same time series analysis implementations as for Demand
                            # (code would be similar to the Demand section above)
                            st.info("Time series analysis for Wind Generation follows the same methodology as for Demand. Please select Demand for a full implementation.")
                        else:
                            st.warning("No numeric columns found in the wind generation dataset.")
                
                elif dataset_option == "Balancing Services" and not balancing_df.empty:
                    df = balancing_df
                    date_col = None
                    for col in df.columns:
                        if pd.api.types.is_datetime64_dtype(df[col]) or "date" in col.lower() or "day" in col.lower():
                            date_col = col
                            break
                    
                    if date_col is None:
                        st.warning("No date column found in the balancing services dataset.")
                    else:
                        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                        if numeric_cols:
                            # Same time series analysis implementations as for Demand
                            # (code would be similar to the Demand section above)
                            st.info("Time series analysis for Balancing Services follows the same methodology as for Demand. Please select Demand for a full implementation.")
                        else:
                            st.warning("No numeric columns found in the balancing services dataset.")
                else:
                    st.info(f"No {dataset_option} data available for the selected period.")
        
        # Hypothesis Testing Section
        elif analysis_type == "Hypothesis Testing":
            st.subheader("Hypothesis Testing")
            
            if not HAS_STATSMODELS:
                st.error("This analysis requires the statsmodels package, which is not installed.")
            else:
                from scipy import stats
                
                test_type = st.selectbox(
                    "Select hypothesis test type:",
                    ["One-sample t-test", "Two-sample t-test", "ANOVA"],
                    key="hyp_test_type"
                )
                
                # One-sample t-test
                if test_type == "One-sample t-test":
                    st.write("One-sample t-test compares a sample mean to a known population mean.")
                    
                    dataset_option = st.selectbox(
                        "Select dataset:",
                        ["Demand", "Wind Generation", "Balancing Services"],
                        key="ttest1_dataset"
                    )
                    
                    if dataset_option == "Demand" and not demand_df.empty:
                        df = demand_df
                        numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                        if numeric_cols:
                            col_to_analyze = st.selectbox("Select column for t-test:", numeric_cols, key="ttest1_col")
                            pop_mean = st.number_input("Hypothesized population mean:", value=float(df[col_to_analyze].mean()), key="ttest1_mean")
                            
                            if st.button("Perform One-sample t-test", key="ttest1_btn"):
                                with st.spinner("Performing one-sample t-test..."):
                                    # Perform t-test
                                    t_stat, p_val = stats.ttest_1samp(df[col_to_analyze].dropna(), pop_mean)
                                    
                                    # Display results
                                    results = pd.DataFrame({
                                        "Statistic": ["t-statistic", "p-value", "Sample Mean", "Sample Size"],
                                        "Value": [t_stat, p_val, df[col_to_analyze].mean(), df[col_to_analyze].count()]
                                    })
                                    
                                    st.dataframe(results)
                                    
                                    # Interpretation
                                    alpha = 0.05
                                    if p_val < alpha:
                                        st.success(f"Reject null hypothesis (p={p_val:.4f} < {alpha}): The sample mean is significantly different from {pop_mean}.")
                                    else:
                                        st.info(f"Fail to reject null hypothesis (p={p_val:.4f} ≥ {alpha}): There is not enough evidence to conclude that the sample mean is different from {pop_mean}.")
                                    
                                    # Visualization
                                    fig = px.histogram(df, x=col_to_analyze, title=f"Distribution of {col_to_analyze}")
                                    fig.add_vline(x=pop_mean, line_dash="dash", line_color="red", 
                                                 annotation_text=f"Hypothesized Mean: {pop_mean}")
                                    fig.add_vline(x=df[col_to_analyze].mean(), line_dash="solid", line_color="green", 
                                                 annotation_text=f"Sample Mean: {df[col_to_analyze].mean():.2f}")
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("No numeric columns found in the demand dataset.")
                    
                    elif dataset_option == "Wind Generation" and not generation_df.empty:
                        # Similar implementation for Wind Generation
                        st.info("One-sample t-test for Wind Generation follows the same methodology as for Demand. Please select Demand for a full implementation.")
                    
                    elif dataset_option == "Balancing Services" and not balancing_df.empty:
                        # Similar implementation for Balancing Services
                        st.info("One-sample t-test for Balancing Services follows the same methodology as for Demand. Please select Demand for a full implementation.")
                    else:
                        st.info(f"No {dataset_option} data available for the selected period.")
                
                # Two-sample t-test
                elif test_type == "Two-sample t-test":
                    st.write("Two-sample t-test compares means of two independent samples.")
                    
                    # Allow selecting two different datasets
                    dataset1 = st.selectbox("Select first dataset:", ["Demand", "Wind Generation", "Balancing Services"], key="ttest2_ds1")
                    dataset2 = st.selectbox("Select second dataset:", ["Demand", "Wind Generation", "Balancing Services"], key="ttest2_ds2")
                    
                    # Get the datasets
                    df1 = None
                    df2 = None
                    
                    if dataset1 == "Demand" and not demand_df.empty:
                        df1 = demand_df
                    elif dataset1 == "Wind Generation" and not generation_df.empty:
                        df1 = generation_df
                    elif dataset1 == "Balancing Services" and not balancing_df.empty:
                        df1 = balancing_df
                        
                    if dataset2 == "Demand" and not demand_df.empty:
                        df2 = demand_df
                    elif dataset2 == "Wind Generation" and not generation_df.empty:
                        df2 = generation_df
                    elif dataset2 == "Balancing Services" and not balancing_df.empty:
                        df2 = balancing_df
                    
                    if df1 is not None and df2 is not None:
                        # Get numeric columns
                        numeric_cols1 = [col for col in df1.columns if pd.api.types.is_numeric_dtype(df1[col])]
                        numeric_cols2 = [col for col in df2.columns if pd.api.types.is_numeric_dtype(df2[col])]
                        
                        if numeric_cols1 and numeric_cols2:
                            col1 = st.selectbox(f"Select column from {dataset1}:", numeric_cols1, key="ttest2_col1")
                            col2 = st.selectbox(f"Select column from {dataset2}:", numeric_cols2, key="ttest2_col2")
                            
                            equal_var = st.checkbox("Assume equal variance", value=False, key="ttest2_equal_var")
                            
                            if st.button("Perform Two-sample t-test", key="ttest2_button"):
                                with st.spinner("Performing two-sample t-test..."):
                                    # Perform t-test
                                    t_stat, p_val = stats.ttest_ind(df1[col1].dropna(), df2[col2].dropna(), equal_var=equal_var)
                                    
                                    # Display results
                                    results = pd.DataFrame({
                                        "Statistic": ["t-statistic", "p-value", f"Mean ({dataset1})", f"Mean ({dataset2})", 
                                                     f"Sample Size ({dataset1})", f"Sample Size ({dataset2})"],
                                        "Value": [t_stat, p_val, df1[col1].mean(), df2[col2].mean(), 
                                                df1[col1].count(), df2[col2].count()]
                                    })
                                    
                                    st.dataframe(results)
                                    
                                    # Interpretation
                                    alpha = 0.05
                                    if p_val < alpha:
                                        st.success(f"Reject null hypothesis (p={p_val:.4f} < {alpha}): There is a significant difference between the means.")
                                    else:
                                        st.info(f"Fail to reject null hypothesis (p={p_val:.4f} ≥ {alpha}): There is not enough evidence to conclude that the means are different.")
                                    
                                    # Visualization - Box plot comparison
                                    fig = go.Figure()
                                    fig.add_trace(go.Box(y=df1[col1].dropna(), name=f"{dataset1} - {col1}"))
                                    fig.add_trace(go.Box(y=df2[col2].dropna(), name=f"{dataset2} - {col2}"))
                                    fig.update_layout(title="Comparison of Distributions", yaxis_title="Value")
                                    st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning("Both datasets must have numeric columns for two-sample t-test.")
                    else:
                        st.warning("One or both datasets are empty for the selected period.")
                
                # ANOVA
                elif test_type == "ANOVA":
                    st.write("ANOVA (Analysis of Variance) compares means of three or more independent samples.")
                    
                    if all(df.empty for df in [demand_df, generation_df, balancing_df]):
                        st.warning("No data available for ANOVA analysis.")
                    else:
                        # Create a list of available datasets
                        available_datasets = []
                        if not demand_df.empty:
                            available_datasets.append("Demand")
                        if not generation_df.empty:
                            available_datasets.append("Wind Generation")
                        if not balancing_df.empty:
                            available_datasets.append("Balancing Services")
                        
                        if len(available_datasets) < 2:
                            st.warning("Need at least two non-empty datasets for ANOVA.")
                        else:
                            # Allow selecting multiple datasets
                            selected_datasets = st.multiselect("Select datasets for ANOVA:", available_datasets, default=available_datasets[:2])
                            
                            if len(selected_datasets) < 2:
                                st.warning("Please select at least two datasets for ANOVA.")
                            else:
                                # Get columns from each dataset
                                dataset_columns = {}
                                for ds in selected_datasets:
                                    if ds == "Demand":
                                        df = demand_df
                                    elif ds == "Wind Generation":
                                        df = generation_df
                                    else:  # Balancing Services
                                        df = balancing_df
                                    
                                    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                                    if numeric_cols:
                                        dataset_columns[ds] = numeric_cols
                                
                                # Let user select one column from each dataset
                                selected_columns = {}
                                for ds, cols in dataset_columns.items():
                                    selected_columns[ds] = st.selectbox(f"Select column from {ds}:", cols, key=f"anova_{ds}")
                                
                                if st.button("Perform ANOVA", key="anova_btn"):
                                    with st.spinner("Performing ANOVA..."):
                                        # Prepare data for ANOVA
                                        data_groups = []
                                        group_names = []
                                        
                                        for ds, col in selected_columns.items():
                                            if ds == "Demand":
                                                df = demand_df
                                            elif ds == "Wind Generation":
                                                df = generation_df
                                            else:  # Balancing Services
                                                df = balancing_df
                                            
                                            data_groups.append(df[col].dropna())
                                            group_names.append(f"{ds} - {col}")
                                        
                                        # Perform ANOVA
                                        f_stat, p_val = stats.f_oneway(*data_groups)
                                        
                                        # Display results
                                        results = pd.DataFrame({
                                            "Statistic": ["F-statistic", "p-value"],
                                            "Value": [f_stat, p_val]
                                        })
                                        
                                        st.dataframe(results)
                                        
                                        # Group statistics
                                        group_stats = pd.DataFrame({
                                            "Group": group_names,
                                            "Mean": [group.mean() for group in data_groups],
                                            "Std Dev": [group.std() for group in data_groups],
                                            "Count": [group.count() for group in data_groups]
                                        })
                                        
                                        st.write("Group Statistics:")
                                        st.dataframe(group_stats)
                                        
                                        # Interpretation
                                        alpha = 0.05
                                        if p_val < alpha:
                                            st.success(f"Reject null hypothesis (p={p_val:.4f} < {alpha}): There are significant differences between the group means.")
                                        else:
                                            st.info(f"Fail to reject null hypothesis (p={p_val:.4f} ≥ {alpha}): There is not enough evidence to conclude that the group means are different.")
                                        
                                        # Visualization - Box plot comparison
                                        fig = go.Figure()
                                        for i, group in enumerate(data_groups):
                                            fig.add_trace(go.Box(y=group, name=group_names[i]))
                                        fig.update_layout(title="Comparison of Distributions", yaxis_title="Value")
                                        st.plotly_chart(fig, use_container_width=True)
        
        # Regression Analysis Section
        elif analysis_type == "Regression Analysis":
            st.subheader("Regression Analysis")
            
            if not HAS_STATSMODELS:
                st.error("This analysis requires the statsmodels package, which is not installed.")
            else:
                dataset_option = st.selectbox(
                    "Select dataset for regression analysis:",
                    ["Demand", "Wind Generation", "Balancing Services"]
                )
                
                if dataset_option == "Demand" and not demand_df.empty:
                    df = demand_df
                    numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
                    
                    if len(numeric_cols) < 2:
                        st.warning("Need at least two numeric columns for regression analysis.")
                    else:
                        st.write("Linear regression models the relationship between a dependent variable and one or more independent variables.")
                        
                        # Select dependent (Y) variable
                        y_col = st.selectbox("Select dependent variable (Y):", numeric_cols, key="reg_y")
                        
                        # Select independent (X) variables
                        x_cols = st.multiselect("Select independent variables (X):", [c for c in numeric_cols if c != y_col], key="reg_x")
                        
                        if not x_cols:
                            st.warning("Please select at least one independent variable.")
                        else:
                            include_constant = st.checkbox("Include constant term", value=True, key="reg_const")
                            
                            if st.button("Perform Regression Analysis", key="reg_btn"):
                                with st.spinner("Performing regression analysis..."):
                                    try:
                                        # Prepare data
                                        y = df[y_col].dropna()
                                        X = df[x_cols].dropna()
                                        
                                        # Ensure same length after dropping NAs
                                        common_idx = y.index.intersection(X.index)
                                        y = y.loc[common_idx]
                                        X = X.loc[common_idx]
                                        
                                        # Add constant if requested
                                        if include_constant:
                                            X = sm.add_constant(X)
                                        
                                        # Fit model
                                        model = sm.OLS(y, X).fit()
                                        
                                        # Display summary
                                        st.write("Regression Results:")
                                        summary_text = model.summary().as_text()
                                        st.text(summary_text)
                                        
                                        # Coefficients table
                                        coef_df = pd.DataFrame({
                                            'Variable': model.params.index,
                                            'Coefficient': model.params.values,
                                            'Std Error': model.bse.values,
                                            't-value': model.tvalues.values,
                                            'p-value': model.pvalues.values
                                        })
                                        
                                        st.write("Coefficients:")
                                        st.dataframe(coef_df)
                                        
                                        # Display metrics
                                        metrics = pd.DataFrame({
                                            'Metric': ['R-squared', 'Adjusted R-squared', 'F-statistic', 'Prob (F-statistic)'],
                                            'Value': [model.rsquared, model.rsquared_adj, model.fvalue, model.f_pvalue]
                                        })
                                        
                                        st.write("Model Metrics:")
                                        st.dataframe(metrics)
                                        
                                        # Predict vs Actual plot
                                        pred = model.predict(X)
                                        fig = px.scatter(x=y, y=pred, labels={'x': 'Actual', 'y': 'Predicted'})
                                        fig.add_trace(go.Scatter(x=[y.min(), y.max()], y=[y.min(), y.max()], 
                                                               mode='lines', name='Perfect Prediction', line=dict(dash='dash')))
                                        fig.update_layout(title="Actual vs Predicted Values", xaxis_title="Actual", yaxis_title="Predicted")
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Residuals plot
                                        residuals = model.resid
                                        fig = px.scatter(x=pred, y=residuals, labels={'x': 'Predicted', 'y': 'Residuals'})
                                        fig.add_hline(y=0, line_dash="dash", line_color="red")
                                        fig.update_layout(title="Residuals vs Predicted Values", xaxis_title="Predicted", yaxis_title="Residuals")
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        # Residuals histogram
                                        fig = px.histogram(residuals, nbins=20, title="Distribution of Residuals")
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                    except Exception as e:
                                        st.error(f"Error in regression analysis: {str(e)}")
                
                elif dataset_option == "Wind Generation" and not generation_df.empty:
                    # Similar implementation for Wind Generation
                    st.info("Regression analysis for Wind Generation follows the same methodology as for Demand. Please select Demand for a full implementation.")
                
                elif dataset_option == "Balancing Services" and not balancing_df.empty:
                    # Similar implementation for Balancing Services
                    st.info("Regression analysis for Balancing Services follows the same methodology as for Demand. Please select Demand for a full implementation.")
                else:
                    st.info(f"No {dataset_option} data available for the selected period.")

st.sidebar.info("Data sourced from National Grid ESO tables in BigQuery (europe-west2 region).")
