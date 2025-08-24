import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta, datetime
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

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Main production dataset
DATASET_ANALYTICS = "uk_energy_analysis"  # For advanced stats results

# Enable caching to speed up queries
st.set_page_config(
    page_title="UK Energy Dashboard (Optimized)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add performance information in sidebar
st.sidebar.title("⚡ UK Energy Dashboard")
st.sidebar.info("**OPTIMIZED VERSION**  \nThis dashboard only uses BigQuery tables and avoids loading from the 1TB+ GCS dataset directly.")

# Ensure output directory exists
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

# Corrected table names and their corresponding date/value columns
TABLE_CONFIG = {
    "demand": {
        "table_name": "neso_demand_forecasts",
        "date_column": "settlement_date",
        "value_column": "forecast_mw",
        "display_name": "Demand Forecasts",
        "unit": "MW",
        "color": "blue"
    },
    "wind": {
        "table_name": "neso_wind_forecasts",
        "date_column": "settlement_date",
        "value_column": "forecast_mw",
        "display_name": "Wind Forecasts",
        "unit": "MW",
        "color": "green"
    },
    "carbon": {
        "table_name": "neso_carbon_intensity",
        "date_column": "settlement_date",
        "value_column": "intensity_gco2_per_kwh",
        "display_name": "Carbon Intensity",
        "unit": "gCO₂/kWh",
        "color": "red"
    },
    "interconnector": {
        "table_name": "neso_interconnector_flows",
        "date_column": "settlement_date",
        "value_column": "flow_mw",
        "display_name": "Interconnector Flows",
        "unit": "MW",
        "color": "orange"
    },
    "balancing": {
        "table_name": "neso_balancing_services",
        "date_column": "settlement_date",
        "value_column": "cost_gbp",
        "display_name": "Balancing Services",
        "unit": "£",
        "color": "purple"
    },
    "warnings": {
        "table_name": "elexon_system_warnings",
        "date_column": "issue_date",
        "value_column": "warning_type",
        "display_name": "System Warnings",
        "unit": "",
        "color": "red"
    }
}

# --- BigQuery ---
@st.cache_resource
def get_bq_client():
    """Initializes and returns a BigQuery client, caching the resource."""
    try:
        st.info("Initializing BigQuery client...")
        client = bigquery.Client(project=PROJECT_ID)
        st.success("BigQuery client initialized successfully")
        return client
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        return None

def get_table_name(table_name):
    """Returns the fully qualified BigQuery table name."""
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_available_date_range(_client: bigquery.Client) -> tuple[date | None, date | None]:
    """Queries to find the min and max dates across all tables."""
    if not _client:
        st.error("No BigQuery client available")
        return None, None
    
    st.info("Checking for available date range in BigQuery...")
    
    # Only check the main neso_demand_forecasts table to speed up this query
    q = f"""
    SELECT MIN(settlement_date) as min_date, MAX(settlement_date) as max_date
    FROM `{get_table_name('neso_demand_forecasts')}`
    """
    
    try:
        st.info(f"Executing query: {q}")
        result = list(_client.query(q).result())
        st.success("Query executed successfully")
        
        if result and len(result) > 0:
            st.info(f"Found date range: {result[0].min_date} to {result[0].max_date}")
            return result[0].min_date, result[0].max_date
        else:
            st.warning("Query returned no results")
    except Exception as e:
        st.error(f"Error getting date range: {e}")
        
        # Fallback to a hardcoded date range if query fails
        st.warning("Using fallback date range (2023-01-01 to 2024-12-31)")
        return date(2023, 1, 1), date(2024, 12, 31)
        
    return None, None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_data(_client: bigquery.Client, config_key: str, start_d: date, end_d: date) -> pd.DataFrame:
    """Fetches data from BigQuery with caching."""
    if not _client:
        return pd.DataFrame()
    
    config = TABLE_CONFIG.get(config_key)
    if not config:
        return pd.DataFrame()
    
    table_name = config['table_name']
    date_col = config['date_column']
    value_col = config['value_column']
    
    # Get schema to determine all columns
    schema_q = f"""
    SELECT column_name
    FROM {PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.COLUMNS
    WHERE table_name = '{table_name}'
    """
    try:
        schema_job = _client.query(schema_q)
        columns = [row.column_name for row in schema_job.result()]
        
        # If no columns found or error, use the minimum required columns
        if not columns:
            columns = [date_col, value_col]
            if 'secondary_column' in config:
                columns.append(config['secondary_column'])
        
        # Build SELECT statement with all columns
        select_clause = ", ".join(columns)
        
        # Build the parameterized query
        q = f"""
        SELECT {select_clause}
        FROM `{get_table_name(table_name)}`
        WHERE {date_col} BETWEEN @start_d AND @end_d
        ORDER BY {date_col}
        """
        
        # Use parameterized query for security and efficiency
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("start_d", "DATE", start_d),
                    bigquery.ScalarQueryParameter("end_d", "DATE", end_d),
                ]
            )
            job = _client.query(q, job_config=job_config)
        except Exception:
            # Fallback to non-parameterized query if parameters fail
            q = f"""
            SELECT {select_clause}
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN '{start_d}' AND '{end_d}'
            ORDER BY {date_col}
            """
            job = _client.query(q)
            
        return job.result().to_dataframe()
    except Exception as e:
        st.warning(f"Error fetching data for {config_key}: {e}")
        return pd.DataFrame()

# --- Plotting Functions ---
def plot_time_series(df, config_key, title=None, height=400):
    """Plot a time series using Plotly."""
    if df.empty:
        return go.Figure()
    
    config = TABLE_CONFIG.get(config_key)
    if not config:
        return go.Figure()
    
    date_col = config['date_column']
    value_col = config['value_column']
    display_name = config['display_name']
    unit = config['unit']
    color = config['color']
    
    # Create figure
    fig = go.Figure()
    
    # Add trace
    fig.add_trace(
        go.Scatter(
            x=df[date_col],
            y=df[value_col],
            mode='lines',
            name=display_name,
            line=dict(color=color, width=2)
        )
    )
    
    # Update layout
    fig.update_layout(
        title=title or display_name,
        xaxis_title="Date",
        yaxis_title=unit,
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def plot_warning_timeline(df, height=400):
    """Plot system warnings as a timeline."""
    if df.empty:
        return go.Figure()
    
    # Get the configuration
    config = TABLE_CONFIG.get('warnings')
    date_col = config['date_column']
    value_col = config['value_column']
    
    # Create figure
    fig = go.Figure()
    
    # Get unique warning types
    warning_types = df[value_col].unique()
    colors = px.colors.qualitative.Safe
    
    # Add a trace for each warning type
    for i, warning_type in enumerate(warning_types):
        subset = df[df[value_col] == warning_type]
        color = colors[i % len(colors)]
        
        fig.add_trace(
            go.Scatter(
                x=subset[date_col],
                y=[warning_type] * len(subset),
                mode='markers',
                name=warning_type,
                marker=dict(
                    symbol='square',
                    size=12,
                    color=color
                )
            )
        )
    
    # Update layout
    fig.update_layout(
        title="System Warnings Timeline",
        xaxis_title="Date",
        yaxis_title="Warning Type",
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

# --- Application ---
def main():
    st.header("Initializing Dashboard")
    st.write("Setting up BigQuery connection...")
    
    # Initialize BigQuery client
    try:
        client = get_bq_client()
        if client:
            st.success("Successfully connected to BigQuery")
        else:
            st.error("Dashboard cannot load. Failed to initialize BigQuery connection.")
            st.stop()
    except Exception as e:
        st.error(f"Error connecting to BigQuery: {str(e)}")
        st.stop()
    
    # Get available date range
    try:
        st.write("Fetching available date range...")
        min_date, max_date = get_available_date_range(client)
        if not min_date or not max_date:
            st.error("No data available in BigQuery table 'neso_demand_forecasts'. Please check data ingestion.")
            st.stop()
        st.success(f"Found data range: {min_date} to {max_date}")
    except Exception as e:
        st.error(f"Error fetching date range: {str(e)}")
        st.stop()
    
    # Show current database status
    st.sidebar.subheader("Database Info")
    st.sidebar.info(f"Data Range: {min_date} to {max_date}")
    
    # Date range selector
    st.sidebar.subheader("Date Range")
    
    # Default to last 30 days if available, otherwise use full range
    default_end = max_date
    default_start = max(min_date, default_end - timedelta(days=30))
    
    start_date = st.sidebar.date_input("Start Date", value=default_start, min_value=min_date, max_value=max_date)
    end_date = st.sidebar.date_input("End Date", value=default_end, min_value=min_date, max_value=max_date)
    
    # Ensure start_date <= end_date
    if start_date > end_date:
        st.sidebar.error("End date must be after start date.")
        start_date, end_date = end_date, start_date
    
    # Sidebar - data source selection
    st.sidebar.subheader("Data Sources")
    selected_sources = {}
    for key, config in TABLE_CONFIG.items():
        selected_sources[key] = st.sidebar.checkbox(config['display_name'], value=True)
    
    # Calculate date difference for query optimization warning
    date_diff = (end_date - start_date).days
    if date_diff > 180:  # If more than 6 months
        st.sidebar.warning(f"⚠️ Large date range selected ({date_diff} days). Dashboard may be slower to load.")
    
    # Main dashboard area
    st.title("UK Energy Dashboard (Optimized)")
    
    # Show time range and source information
    st.markdown(f"**Data Period:** {start_date} to {end_date} ({date_diff} days)")
    
    # Add explanation of optimization
    with st.expander("About this optimized dashboard"):
        st.markdown("""
        This dashboard has been optimized to provide faster performance:
        
        - Uses only BigQuery tables instead of loading data directly from GCS
        - Implements caching to reduce repeated queries
        - Optimizes query parameters to improve execution speed
        - Focuses on the most important data sources
        """)
    
    # Load data for selected sources
    data = {}
    progress_text = "Loading data from BigQuery..."
    progress_bar = st.progress(0)
    
    total_sources = sum(selected_sources.values())
    loaded_sources = 0
    
    for key, selected in selected_sources.items():
        if selected:
            data[key] = fetch_data(client, key, start_date, end_date)
            loaded_sources += 1
            progress_bar.progress(loaded_sources / total_sources)
    
    progress_bar.empty()
    
    # Display data in tabs
    tab_names = [TABLE_CONFIG[key]['display_name'] for key, selected in selected_sources.items() if selected]
    if tab_names:
        tabs = st.tabs(tab_names)
        
        tab_index = 0
        for key, selected in selected_sources.items():
            if selected:
                df = data[key]
                config = TABLE_CONFIG[key]
                
                with tabs[tab_index]:
                    # Display chart
                    if key == 'warnings':
                        fig = plot_warning_timeline(df)
                    else:
                        fig = plot_time_series(df, key)
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show data stats
                    st.subheader("Statistics")
                    if not df.empty and config['value_column'] in df.columns:
                        value_col = config['value_column']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Minimum", f"{df[value_col].min():.2f} {config['unit']}")
                        with col2:
                            st.metric("Maximum", f"{df[value_col].max():.2f} {config['unit']}")
                        with col3:
                            st.metric("Average", f"{df[value_col].mean():.2f} {config['unit']}")
                        with col4:
                            st.metric("Records", f"{len(df):,}")
                    
                    # Show data table with pagination
                    st.subheader("Data Table")
                    if not df.empty:
                        # Limit to first 1000 rows for performance
                        display_df = df.head(1000)
                        
                        # Only keep important columns
                        if len(display_df.columns) > 5:
                            # Keep date, value, and up to 3 other important columns
                            keep_cols = [config['date_column'], config['value_column']]
                            
                            # Add a few more potentially useful columns
                            for col in ['settlement_period', 'interconnector_name', 'warning_type', 'fuel_type']:
                                if col in display_df.columns and col not in keep_cols:
                                    keep_cols.append(col)
                            
                            # Only keep selected columns if they exist
                            display_df = display_df[[col for col in keep_cols if col in display_df.columns]]
                        
                        st.dataframe(display_df, use_container_width=True)
                        
                        if len(df) > 1000:
                            st.info(f"Showing first 1,000 of {len(df):,} records")
                    else:
                        st.info("No data available for the selected date range")
                
                tab_index += 1
    else:
        st.warning("Please select at least one data source from the sidebar.")
    
    # Show last updated time
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
