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
DATASET_ID = "uk_energy_prod"  # Updated to use the new europe-west2 dataset
DATASET_ANALYTICS = "uk_energy_analysis"  # For advanced stats results

# Ensure output directory exists
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

# Original table names and colors for the dashboard
TABLE_CONFIG = {
    "demand": {
        "table_name": "neso_demand_forecasts",
        "date_column": "settlement_date",
        "value_column": "national_demand_forecast",
        "display_name": "Demand Forecasts",
        "unit": "MW",
        "color": "#3366CC"  # Original blue
    },
    "wind": {
        "table_name": "neso_wind_forecasts",
        "date_column": "settlement_date",
        "value_column": "forecast_output_mw",
        "display_name": "Wind Forecasts",
        "unit": "MW",
        "color": "#33A02C"  # Original green
    },
    "carbon": {
        "table_name": "neso_carbon_intensity",
        "date_column": "measurement_date",
        "value_column": "carbon_intensity_gco2_kwh",
        "display_name": "Carbon Intensity",
        "unit": "gCO₂/kWh",
        "color": "#E31A1C"  # Original red
    },
    "interconnector": {
        "table_name": "neso_interconnector_flows",
        "date_column": "settlement_date",
        "value_column": "flow_mw",
        "display_name": "Interconnector Flows",
        "unit": "MW",
        "color": "#FF7F00"  # Original orange
    },
    "balancing": {
        "table_name": "neso_balancing_services",
        "date_column": "settlement_date",
        "value_column": "cost_pounds",
        "display_name": "Balancing Services",
        "unit": "£",
        "color": "#6A3D9A"  # Original purple
    },
    "warnings": {
        "table_name": "elexon_system_warnings",
        "date_column": "warning_date",
        "value_column": "warning_type",
        "display_name": "System Warnings",
        "unit": "",
        "color": "#FF0000"  # Original red for warnings
    }
}

# --- BigQuery ---
@st.cache_resource
def get_bq_client():
    """Initializes and returns a BigQuery client, caching the resource."""
    try:
        return bigquery.Client(project=PROJECT_ID)
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
        return None, None
    
    # Force a 9-year date range as requested
    today = datetime.now().date()
    min_date = today - timedelta(days=9*365)  # 9 years ago
    max_date = today
    
    return min_date, max_date
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
    
    try:
        # Build a query based on the data type
        if config_key == 'demand':
            # For demand data, get daily aggregated values
            q = f"""
            SELECT 
                {date_col},
                AVG({value_col}) as {value_col},
                MIN({value_col}) as min_value,
                MAX({value_col}) as max_value,
                AVG(temperature_forecast) as temperature_forecast,
                COUNT(*) as data_points
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN @start_d AND @end_d
            GROUP BY {date_col}
            ORDER BY {date_col}
            """
        elif config_key == 'wind':
            # For wind data, aggregate by day
            q = f"""
            SELECT 
                {date_col},
                AVG({value_col}) as {value_col},
                MIN({value_col}) as min_value,
                MAX({value_col}) as max_value,
                AVG(actual_output_mw) as actual_output_mw,
                COUNT(*) as data_points
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN @start_d AND @end_d
            GROUP BY {date_col}
            ORDER BY {date_col}
            """
        elif config_key == 'carbon':
            # For carbon intensity data
            q = f"""
            SELECT 
                {date_col},
                AVG({value_col}) as {value_col},
                MIN({value_col}) as min_value,
                MAX({value_col}) as max_value,
                COUNT(*) as data_points
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN @start_d AND @end_d
            GROUP BY {date_col}
            ORDER BY {date_col}
            """
        elif config_key == 'warnings':
            # For warnings, get all details 
            q = f"""
            SELECT *
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN @start_d AND @end_d
            ORDER BY {date_col}
            """
        else:
            # Default aggregation for other datasets
            q = f"""
            SELECT 
                {date_col},
                AVG({value_col}) as {value_col},
                MIN({value_col}) as min_value,
                MAX({value_col}) as max_value,
                COUNT(*) as data_points
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN @start_d AND @end_d
            GROUP BY {date_col}
            ORDER BY {date_col}
            """
        
        # Use parameterized query for security and efficiency
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_d", "DATE", start_d),
                bigquery.ScalarQueryParameter("end_d", "DATE", end_d),
            ]
        )
        job = _client.query(q, job_config=job_config)
        return job.result().to_dataframe()
    
    except Exception as e:
        st.warning(f"Error fetching data for {config_key}: {e}")
        
        # Fallback to a simple query if aggregation fails
        try:
            simple_q = f"""
            SELECT *
            FROM `{get_table_name(table_name)}`
            WHERE {date_col} BETWEEN '{start_d}' AND '{end_d}'
            ORDER BY {date_col}
            LIMIT 1000
            """
            job = _client.query(simple_q)
            return job.result().to_dataframe()
        except Exception as e2:
            st.error(f"Failed to fetch data: {e2}")
            return pd.DataFrame()

# --- Plotting Functions ---
def plot_time_series(df, config_key, title=None, height=500):
    """Plot a time series using Plotly with original styling."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No data available for the selected date range",
            xaxis_title="Date",
            yaxis_title="Value",
            height=height,
            template="plotly_white"
        )
        return fig
    
    config = TABLE_CONFIG.get(config_key)
    if not config:
        return go.Figure()
    
    date_col = config['date_column']
    value_col = config['value_column']
    display_name = config['display_name']
    unit = config['unit']
    color = config['color']
    
    # For time series, we need to aggregate by date if we have settlement periods
    if 'settlement_period' in df.columns and len(df) > 100:
        # Get daily aggregates
        if pd.api.types.is_numeric_dtype(df[value_col]):
            # For numeric data, calculate daily average
            daily_data = df.groupby(date_col)[value_col].agg(['mean', 'min', 'max']).reset_index()
            
            # Create figure with daily min, max, and mean
            fig = go.Figure()
            
            # Add min-max range area
            fig.add_trace(
                go.Scatter(
                    x=daily_data[date_col],
                    y=daily_data['max'],
                    fill=None,
                    mode='lines',
                    line=dict(color=color, width=0),
                    showlegend=False
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=daily_data[date_col],
                    y=daily_data['min'],
                    fill='tonexty',
                    mode='lines',
                    line=dict(color=color, width=0),
                    fillcolor=f'rgba(230,230,250,0.3)',
                    name='Daily Range'
                )
            )
            
            # Add daily average line
            fig.add_trace(
                go.Scatter(
                    x=daily_data[date_col],
                    y=daily_data['mean'],
                    mode='lines',
                    name='Daily Average',
                    line=dict(color=color, width=2)
                )
            )
        else:
            # For non-numeric data, just count occurrences by date
            daily_counts = df.groupby([date_col, value_col]).size().reset_index(name='count')
            
            # Create figure with counts by category
            fig = px.bar(
                daily_counts,
                x=date_col,
                y='count',
                color=value_col,
                title=title or display_name,
                labels={
                    date_col: 'Date',
                    'count': 'Count',
                    value_col: display_name
                },
                color_discrete_sequence=px.colors.qualitative.Plotly
            )
    else:
        # Regular time series with all data points
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=df[date_col],
                y=df[value_col],
                mode='lines+markers',
                name=display_name,
                line=dict(color=color, width=2),
                marker=dict(size=6, color=color)
            )
        )
    
    # Update layout with original styling
    fig.update_layout(
        title=title or display_name,
        xaxis_title="Date",
        yaxis_title=unit,
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def plot_warning_timeline(df, height=500):
    """Plot system warnings as a timeline."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(
            title="No system warnings available for the selected date range",
            xaxis_title="Date",
            yaxis_title="Warning Type",
            height=height,
            template="plotly_white"
        )
        return fig
    
    # Get the configuration
    config = TABLE_CONFIG.get('warnings')
    date_col = config['date_column']
    value_col = config['value_column']
    
    # Create a figure with one row per warning type
    warning_types = sorted(df[value_col].unique())
    
    if 'severity' in df.columns:
        # Create a custom figure with color by severity
        severity_colors = {
            'LOW': '#4CAF50',  # Green
            'MEDIUM': '#FF9800',  # Orange
            'HIGH': '#F44336',  # Red
            'CRITICAL': '#B71C1C'  # Dark Red
        }
        
        fig = go.Figure()
        
        for warning_type in warning_types:
            subset = df[df[value_col] == warning_type]
            
            for _, row in subset.iterrows():
                severity = row.get('severity', 'MEDIUM')
                color = severity_colors.get(severity, '#FF9800')
                
                # Add the warning point
                fig.add_trace(
                    go.Scatter(
                        x=[row[date_col]],
                        y=[warning_type],
                        mode='markers',
                        marker=dict(
                            size=12,
                            color=color,
                            symbol='square',
                            line=dict(width=1, color='black')
                        ),
                        name=f"{severity} - {warning_type}",
                        hovertext=f"Type: {warning_type}<br>Date: {row[date_col]}<br>Severity: {severity}",
                        showlegend=False
                    )
                )
                
                # If we have start and end times, add a line segment
                if 'start_time' in df.columns and 'end_time' in df.columns:
                    if pd.notna(row.get('start_time')) and pd.notna(row.get('end_time')):
                        try:
                            start = row['start_time']
                            end = row['end_time']
                            
                            fig.add_trace(
                                go.Scatter(
                                    x=[start, end],
                                    y=[warning_type, warning_type],
                                    mode='lines',
                                    line=dict(color=color, width=3),
                                    showlegend=False
                                )
                            )
                        except:
                            pass  # Skip if dates aren't valid
    else:
        # Simple scatter plot for just warning types and dates
        fig = px.scatter(
            df, 
            x=date_col, 
            y=value_col,
            color=value_col,
            title="System Warnings Timeline",
            labels={
                date_col: "Date",
                value_col: "Warning Type"
            },
            height=height,
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
    
    # Update layout with original styling
    fig.update_layout(
        title="System Warnings Timeline",
        xaxis_title="Date",
        yaxis_title="Warning Type",
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(
            type='category',
            categoryorder='array',
            categoryarray=warning_types
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

# Helper function to calculate proper date range display
def format_date_range(start_date, end_date):
    """Format a date range in a human-readable format, accounting for years."""
    if not start_date or not end_date:
        return "Unknown date range"
    
    # Calculate the difference
    delta = end_date - start_date
    days = delta.days
    
    # Calculate years, months, days
    years = days // 365
    remaining_days = days % 365
    months = remaining_days // 30
    remaining_days = remaining_days % 30
    
    # Format the string
    parts = []
    if years > 0:
        parts.append(f"{years} {'year' if years == 1 else 'years'}")
    if months > 0:
        parts.append(f"{months} {'month' if months == 1 else 'months'}")
    if remaining_days > 0 or (years == 0 and months == 0):
        parts.append(f"{remaining_days} {'day' if remaining_days == 1 else 'days'}")
    
    return ", ".join(parts)

# --- Application ---
def main():
    # Page configuration
    st.set_page_config(
        page_title="GB Energy Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for styling similar to the original
    st.markdown("""
    <style>
    .stPlotlyChart {
        background-color: #0E1117;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .stMetric {
        background-color: #0E1117;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #1E1E1E;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2C2C2C;
        border-bottom: 2px solid #3366CC;
    }
    div[data-testid="stSidebarContent"] {
        background-color: #0E1117;
    }
    h1, h2, h3 {
        color: #3366CC;
    }
    .stDataFrame {
        background-color: #0E1117;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize BigQuery client
    client = get_bq_client()
    if not client:
        st.error("Dashboard cannot load. Failed to initialize BigQuery connection.")
        return
    
    # Get available date range
    min_date, max_date = get_available_date_range(client)
    if not min_date or not max_date:
        st.error("No data available in BigQuery tables. Please check data ingestion.")
        return
    
    # Main dashboard area
    st.title("⚡ GB Energy Dashboard")
    
    # Add explanation of data source
    st.markdown("""
    This dashboard provides insights into Great Britain's energy system using data from the BigQuery dataset.
    Select date ranges and data sources using the sidebar controls.
    """)
    
    # Dashboard metrics summary with proper date range calculation
    st.subheader("Dashboard Overview")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate date range for metrics
    date_range_days = (max_date - min_date).days
    date_range_years = date_range_days / 365.25
    formatted_range = format_date_range(min_date, max_date)
    
    with col1:
        st.metric(
            "Data Date Range", 
            f"{formatted_range}",
            help=f"Data available from {min_date} to {max_date}"
        )
    
    with col2:
        try:
            # Get total records across all tables
            tables_count = 0
            for key, config in TABLE_CONFIG.items():
                if key != 'warnings':  # Skip warnings for the total
                    table_name = config['table_name']
                    count_query = f"""
                    SELECT COUNT(*) as count FROM `{get_table_name(table_name)}`
                    """
                    result = list(client.query(count_query).result())
                    if result:
                        tables_count += result[0].count
            
            st.metric(
                "Total Records", 
                f"{tables_count:,}",
                help="Total number of records across all data sources"
            )
        except:
            st.metric("Total Records", "Unknown")
    
    with col3:
        try:
            wind_count_query = f"""
            SELECT COUNT(*) as count FROM `{get_table_name('neso_wind_forecasts')}`
            """
            wind_count = list(client.query(wind_count_query).result())[0].count
            st.metric(
                "Wind Records", 
                f"{wind_count:,}",
                help="Total number of wind forecast records"
            )
        except:
            st.metric("Wind Records", "Unknown")
    
    with col4:
        try:
            warning_count_query = f"""
            SELECT COUNT(*) as count FROM `{get_table_name('elexon_system_warnings')}`
            """
            warning_count = list(client.query(warning_count_query).result())[0].count
            st.metric(
                "System Warnings", 
                f"{warning_count:,}",
                help="Total number of system warnings"
            )
        except:
            st.metric("System Warnings", "Unknown")
    
    # Add a divider
    st.markdown("---")
    
    # Sidebar configuration
    st.sidebar.title("Dashboard Controls")
    
    # Date range selector
    st.sidebar.header("Date Range")
    
    # Default to last 30 days if available, otherwise use full range
    default_end = max_date
    default_start = max(min_date, default_end - timedelta(days=30))
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=default_start,
        min_value=min_date,
        max_value=max_date
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=default_end,
        min_value=min_date,
        max_value=max_date
    )
    
    # Ensure start_date <= end_date
    if start_date > end_date:
        st.sidebar.error("End date must be after start date.")
        start_date, end_date = end_date, start_date
    
    # Quick date selectors
    st.sidebar.subheader("Quick Select")
    date_options = st.sidebar.columns(3)
    
    with date_options[0]:
        if st.button("Last Week"):
            end_date = max_date
            start_date = end_date - timedelta(days=7)
    
    with date_options[1]:
        if st.button("Last Month"):
            end_date = max_date
            start_date = end_date - timedelta(days=30)
    
    with date_options[2]:
        if st.button("Last Year"):
            end_date = max_date
            start_date = end_date - timedelta(days=365)
    
    # Show selected date range
    selected_range = format_date_range(start_date, end_date)
    st.sidebar.info(f"Selected: {selected_range} ({start_date} to {end_date})")
    
    # Sidebar - data source selection
    st.sidebar.header("Data Sources")
    
    # Add a "Select All" option
    select_all = st.sidebar.checkbox("Select All Sources", value=True)
    
    # Group data sources by category
    forecast_sources = ["demand", "wind"]
    operational_sources = ["carbon", "interconnector", "balancing"]
    warning_sources = ["warnings"]
    
    # Add checkboxes for each data source by category
    selected_sources = {}
    
    st.sidebar.subheader("Forecasts")
    for key in forecast_sources:
        config = TABLE_CONFIG[key]
        default_value = select_all
        selected_sources[key] = st.sidebar.checkbox(config['display_name'], value=default_value)
    
    st.sidebar.subheader("Operational Data")
    for key in operational_sources:
        config = TABLE_CONFIG[key]
        default_value = select_all
        selected_sources[key] = st.sidebar.checkbox(config['display_name'], value=default_value)
    
    st.sidebar.subheader("Warnings")
    for key in warning_sources:
        config = TABLE_CONFIG[key]
        default_value = select_all
        selected_sources[key] = st.sidebar.checkbox(config['display_name'], value=default_value)
    
    # Add visualization options
    st.sidebar.header("Visualization Options")
    
    chart_height = st.sidebar.slider(
        "Chart Height",
        min_value=300,
        max_value=800,
        value=500,
        step=50
    )
    
    # Show data tables option
    show_data_tables = st.sidebar.checkbox("Show Data Tables", value=True)
    
    # Background color option
    background_color = st.sidebar.selectbox(
        "Background Color",
        options=["White", "Light Gray", "Original"],
        index=0
    )
    
    if background_color == "Light Gray":
        st.markdown("""
        <style>
        .stPlotlyChart {
            background-color: #f5f5f5;
        }
        </style>
        """, unsafe_allow_html=True)
    elif background_color == "Original":
        st.markdown("""
        <style>
        .stPlotlyChart {
            background-color: #f0f2f6;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Load data for selected sources
    data = {}
    progress_text = "Loading data from BigQuery..."
    progress_bar = st.progress(0)
    
    total_sources = sum(selected_sources.values())
    if total_sources == 0:
        st.warning("Please select at least one data source from the sidebar.")
        return
    
    loaded_sources = 0
    
    for key, selected in selected_sources.items():
        if selected:
            with st.spinner(f"Loading {TABLE_CONFIG[key]['display_name']} data..."):
                data[key] = fetch_data(client, key, start_date, end_date)
                loaded_sources += 1
                progress_bar.progress(loaded_sources / total_sources)
    
    progress_bar.empty()
    
    # Display data in tabs
    tab_names = [TABLE_CONFIG[key]['display_name'] for key, selected in selected_sources.items() if selected]
    # Add the advanced statistics tab
    tab_names.append("ADVANCED STATISTICS ← CLICK HERE")
    
    if tab_names:
        tabs = st.tabs(tab_names)
        
        tab_index = 0
        for key, selected in selected_sources.items():
            if selected:
                df = data[key]
                config = TABLE_CONFIG[key]
                
                with tabs[tab_index]:
                    # Add header with description
                    st.header(config['display_name'])
                    
                    # Show summary information
                    if not df.empty:
                        data_points = len(df)
                        date_range_text = f"{df[config['date_column']].min().strftime('%Y-%m-%d')} to {df[config['date_column']].max().strftime('%Y-%m-%d')}"
                        st.markdown(f"**Data Range:** {date_range_text} | **Records:** {data_points:,}")
                    
                    # Display chart
                    if key == 'warnings':
                        fig = plot_warning_timeline(df, height=chart_height)
                    else:
                        fig = plot_time_series(df, key, height=chart_height)
                    
                    st.plotly_chart(fig, use_container_width=True, key=f"main_chart_{key}")
                    
                    # Show data stats
                    if not df.empty and config['value_column'] in df.columns:
                        st.subheader("Statistics")
                        value_col = config['value_column']
                        
                        # Create metrics row
                        metric_cols = st.columns(4)
                        
                        # Only show numeric stats for numeric columns
                        if pd.api.types.is_numeric_dtype(df[value_col]):
                            # Min value
                            with metric_cols[0]:
                                min_val = df[value_col].min()
                                st.metric(
                                    "Minimum", 
                                    f"{min_val:.2f} {config['unit']}"
                                )
                            
                            # Max value
                            with metric_cols[1]:
                                max_val = df[value_col].max()
                                st.metric(
                                    "Maximum", 
                                    f"{max_val:.2f} {config['unit']}"
                                )
                            
                            # Average
                            with metric_cols[2]:
                                mean_val = df[value_col].mean()
                                st.metric(
                                    "Average", 
                                    f"{mean_val:.2f} {config['unit']}"
                                )
                            
                            # Standard deviation or median
                            with metric_cols[3]:
                                try:
                                    std_val = df[value_col].std()
                                    st.metric(
                                        "Std. Deviation", 
                                        f"{std_val:.2f} {config['unit']}"
                                    )
                                except:
                                    median_val = df[value_col].median()
                                    st.metric(
                                        "Median", 
                                        f"{median_val:.2f} {config['unit']}"
                                    )
                        else:
                            # For non-numeric data, show category counts
                            value_counts = df[value_col].value_counts()
                            
                            # Most common value
                            with metric_cols[0]:
                                most_common = value_counts.index[0] if not value_counts.empty else "None"
                                st.metric(
                                    "Most Common", 
                                    f"{most_common}"
                                )
                            
                            # Count of most common
                            with metric_cols[1]:
                                count_most_common = value_counts.iloc[0] if not value_counts.empty else 0
                                st.metric(
                                    "Count", 
                                    f"{count_most_common:,}"
                                )
                            
                            # Number of categories
                            with metric_cols[2]:
                                num_categories = len(value_counts)
                                st.metric(
                                    "Categories", 
                                    f"{num_categories:,}"
                                )
                            
                            # Total records
                            with metric_cols[3]:
                                st.metric(
                                    "Total Records", 
                                    f"{len(df):,}"
                                )
                    
                    # Show data table with pagination if enabled
                    if show_data_tables:
                        st.subheader("Data Table")
                        if not df.empty:
                            # Limit to first 1000 rows for performance
                            display_df = df.head(1000)
                            st.dataframe(display_df, use_container_width=True)
                            
                            if len(df) > 1000:
                                st.info(f"Showing first 1,000 of {len(df):,} records")
                            
                            # Add download button for CSV
                            csv = df.to_csv(index=False).encode('utf-8')
                            st.download_button(
                                label="Download as CSV",
                                data=csv,
                                file_name=f"{config['table_name']}_{start_date}_to_{end_date}.csv",
                                mime='text/csv',
                            )
                        else:
                            st.info("No data available for the selected date range")
                
                tab_index += 1
        
        # Add the advanced statistics tab content
        with tabs[-1]:  # The last tab is the advanced statistics tab
            st.header("ADVANCED STATISTICS")
            st.write("Perform advanced statistical analysis on the energy data.")
            
            # Analysis type selector
            analysis_type = st.selectbox(
                "Choose the type of statistical analysis:",
                ["Descriptive Statistics", "Correlation Analysis", "Time Series Analysis", 
                 "Hypothesis Testing", "Regression Analysis"]
            )
            
            # Data source selector for analysis
            analysis_source = st.selectbox(
                "Select data source for analysis:",
                [TABLE_CONFIG[key]['display_name'] for key, selected in selected_sources.items() if selected]
            )
            
            # Get the corresponding data for the selected source
            selected_key = None
            for key, value in TABLE_CONFIG.items():
                if value['display_name'] == analysis_source and key in data:
                    selected_key = key
                    break
            
            if selected_key and not data[selected_key].empty:
                df = data[selected_key]
                config = TABLE_CONFIG[selected_key]
                value_col = config['value_column']
                date_col = config['date_column']
                
                st.subheader(f"Analysis of {config['display_name']}")
                
                if analysis_type == "Descriptive Statistics":
                    st.write("### Descriptive Statistics")
                    desc_stats = df[value_col].describe()
                    st.dataframe(desc_stats)
                    
                    # Add histogram
                    fig = px.histogram(df, x=value_col, 
                                      title=f"Distribution of {config['display_name']}",
                                      labels={value_col: f"{config['display_name']} ({config['unit']})"},
                                      color_discrete_sequence=[config['color']])
                    fig.update_layout(bargap=0.1, template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True, key=f"histogram_{selected_key}")
                
                elif analysis_type == "Correlation Analysis":
                    st.write("### Correlation Analysis")
                    
                    # Select secondary variable
                    secondary_source = st.selectbox(
                        "Select secondary data source to correlate with:",
                        [TABLE_CONFIG[k]['display_name'] for k in data.keys() if k != selected_key and not data[k].empty]
                    )
                    
                    # Find the key for the secondary source
                    secondary_key = None
                    for k, v in TABLE_CONFIG.items():
                        if v['display_name'] == secondary_source and k in data:
                            secondary_key = k
                            break
                    
                    if secondary_key:
                        df2 = data[secondary_key]
                        value_col2 = TABLE_CONFIG[secondary_key]['value_column']
                        date_col2 = TABLE_CONFIG[secondary_key]['date_column']
                        
                        # Merge the dataframes on date
                        merged_df = pd.merge(
                            df[[date_col, value_col]], 
                            df2[[date_col2, value_col2]],
                            left_on=date_col, right_on=date_col2,
                            how='inner'
                        )
                        
                        if not merged_df.empty:
                            # Calculate correlation
                            corr = merged_df[value_col].corr(merged_df[value_col2])
                            st.metric("Correlation Coefficient", f"{corr:.4f}")
                            
                            # Scatter plot
                            fig = px.scatter(merged_df, x=value_col, y=value_col2,
                                           title=f"Correlation between {config['display_name']} and {TABLE_CONFIG[secondary_key]['display_name']}",
                                           labels={
                                               value_col: f"{config['display_name']} ({config['unit']})",
                                               value_col2: f"{TABLE_CONFIG[secondary_key]['display_name']} ({TABLE_CONFIG[secondary_key]['unit']})"
                                           },
                                           trendline="ols")
                            fig.update_layout(template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True, key=f"scatter_{selected_key}_{secondary_key}")
                        else:
                            st.warning("No matching dates found between the selected data sources.")
                    else:
                        st.warning("Please select a secondary data source.")
                
                elif analysis_type == "Time Series Analysis":
                    st.write("### Time Series Analysis")
                    
                    if HAS_STATSMODELS:
                        decomposition_type = st.selectbox(
                            "Select decomposition type:",
                            ["Seasonal Decomposition", "Moving Average", "Trend Analysis"]
                        )
                        
                        if decomposition_type == "Seasonal Decomposition":
                            # Sort by date
                            ts_df = df.sort_values(by=date_col)
                            
                            # Set the frequency of the time series
                            freq = st.selectbox("Select frequency for decomposition:", 
                                              ["Daily", "Weekly", "Monthly"])
                            
                            freq_map = {"Daily": 1, "Weekly": 7, "Monthly": 30}
                            period = freq_map[freq]
                            
                            try:
                                # Perform decomposition
                                result = seasonal_decompose(
                                    ts_df[value_col], model='additive', period=period
                                )
                                
                                # Create subplot figure
                                fig = make_subplots(rows=4, cols=1, 
                                                 subplot_titles=["Observed", "Trend", "Seasonal", "Residual"])
                                
                                # Add traces
                                fig.add_trace(go.Scatter(x=ts_df[date_col], y=result.observed, 
                                                      name="Observed", line=dict(color=config['color'])), 
                                           row=1, col=1)
                                
                                fig.add_trace(go.Scatter(x=ts_df[date_col], y=result.trend, 
                                                      name="Trend", line=dict(color="#FF7F0E")), 
                                           row=2, col=1)
                                
                                fig.add_trace(go.Scatter(x=ts_df[date_col], y=result.seasonal, 
                                                      name="Seasonal", line=dict(color="#2CA02C")), 
                                           row=3, col=1)
                                
                                fig.add_trace(go.Scatter(x=ts_df[date_col], y=result.resid, 
                                                      name="Residual", line=dict(color="#D62728")), 
                                           row=4, col=1)
                                
                                fig.update_layout(height=800, template="plotly_dark")
                                st.plotly_chart(fig, use_container_width=True, key=f"decomp_{selected_key}_{freq}")
                            except Exception as e:
                                st.error(f"Error in decomposition: {e}")
                                st.info("Try a different frequency or ensure you have enough data points.")
                        
                        elif decomposition_type == "Moving Average":
                            # Sort by date
                            ts_df = df.sort_values(by=date_col)
                            
                            # Select window size
                            window_size = st.slider("Moving Average Window Size", 
                                                  min_value=2, max_value=30, value=7)
                            
                            # Calculate moving average
                            ts_df['moving_avg'] = ts_df[value_col].rolling(window=window_size).mean()
                            
                            # Plot
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=ts_df[date_col], y=ts_df[value_col],
                                                  name=f"{config['display_name']} (Actual)",
                                                  line=dict(color=config['color'])))
                            
                            fig.add_trace(go.Scatter(x=ts_df[date_col], y=ts_df['moving_avg'],
                                                  name=f"{window_size}-Day Moving Average",
                                                  line=dict(color="#FF7F0E", width=3)))
                            
                            fig.update_layout(
                                title=f"{window_size}-Day Moving Average of {config['display_name']}",
                                xaxis_title="Date",
                                yaxis_title=f"{config['display_name']} ({config['unit']})",
                                template="plotly_dark"
                            )
                            st.plotly_chart(fig, use_container_width=True, key=f"moving_avg_{selected_key}_{window_size}")
                        
                        elif decomposition_type == "Trend Analysis":
                            # Sort by date
                            ts_df = df.sort_values(by=date_col)
                            
                            # Add numeric index for trend analysis
                            ts_df['index'] = range(len(ts_df))
                            
                            # Calculate linear trend
                            X = ts_df['index'].values.reshape(-1, 1)
                            y = ts_df[value_col].values
                            
                            model = sm.OLS(y, sm.add_constant(X)).fit()
                            ts_df['trend'] = model.predict(sm.add_constant(X))
                            
                            # Plot
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=ts_df[date_col], y=ts_df[value_col],
                                                  name=f"{config['display_name']} (Actual)",
                                                  line=dict(color=config['color'])))
                            
                            fig.add_trace(go.Scatter(x=ts_df[date_col], y=ts_df['trend'],
                                                  name="Linear Trend",
                                                  line=dict(color="#FF7F0E", width=3)))
                            
                            fig.update_layout(
                                title=f"Linear Trend Analysis of {config['display_name']}",
                                xaxis_title="Date",
                                yaxis_title=f"{config['display_name']} ({config['unit']})",
                                template="plotly_dark"
                            )
                            st.plotly_chart(fig, use_container_width=True, key=f"trend_{selected_key}")
                            
                            # Display trend statistics
                            st.write("### Trend Model Summary")
                            st.text(f"Slope: {model.params[1]:.4f}")
                            st.text(f"R-squared: {model.rsquared:.4f}")
                            st.text(f"p-value: {model.pvalues[1]:.4f}")
                            
                            if model.pvalues[1] < 0.05:
                                trend_direction = "increasing" if model.params[1] > 0 else "decreasing"
                                st.success(f"There is a statistically significant {trend_direction} trend.")
                            else:
                                st.info("No statistically significant trend detected.")
                    else:
                        st.error("Please install statsmodels to use Time Series Analysis features.")
                        st.code("pip install statsmodels")
                
                elif analysis_type == "Hypothesis Testing":
                    st.write("### Hypothesis Testing")
                    
                    test_type = st.selectbox(
                        "Select hypothesis test type:",
                        ["One-sample t-test", "Two-sample t-test", "ANOVA"]
                    )
                    
                    if test_type == "One-sample t-test":
                        # One-sample t-test
                        test_value = st.number_input(
                            f"Test if the mean is different from (in {config['unit']}):",
                            value=float(df[value_col].mean())
                        )
                        
                        t_stat, p_value = stats.ttest_1samp(df[value_col].dropna(), test_value)
                        
                        col1, col2 = st.columns(2)
                        col1.metric("T-statistic", f"{t_stat:.4f}")
                        col2.metric("P-value", f"{p_value:.4f}")
                        
                        alpha = 0.05
                        if p_value < alpha:
                            st.success(f"The mean is significantly different from {test_value} {config['unit']} (p < {alpha}).")
                        else:
                            st.info(f"The mean is not significantly different from {test_value} {config['unit']} (p > {alpha}).")
                    
                    elif test_type == "Two-sample t-test":
                        # Select secondary variable
                        secondary_source = st.selectbox(
                            "Select secondary data source to compare with:",
                            [TABLE_CONFIG[k]['display_name'] for k in data.keys() if k != selected_key and not data[k].empty]
                        )
                        
                        # Find the key for the secondary source
                        secondary_key = None
                        for k, v in TABLE_CONFIG.items():
                            if v['display_name'] == secondary_source and k in data:
                                secondary_key = k
                                break
                        
                        if secondary_key:
                            df2 = data[secondary_key]
                            value_col2 = TABLE_CONFIG[secondary_key]['value_column']
                            
                            # Perform t-test
                            t_stat, p_value = stats.ttest_ind(
                                df[value_col].dropna(),
                                df2[value_col2].dropna(),
                                equal_var=False  # Welch's t-test
                            )
                            
                            col1, col2 = st.columns(2)
                            col1.metric("T-statistic", f"{t_stat:.4f}")
                            col2.metric("P-value", f"{p_value:.4f}")
                            
                            alpha = 0.05
                            if p_value < alpha:
                                st.success(f"The means are significantly different (p < {alpha}).")
                            else:
                                st.info(f"The means are not significantly different (p > {alpha}).")
                            
                            # Show histograms for comparison
                            fig = go.Figure()
                            fig.add_trace(go.Histogram(
                                x=df[value_col].dropna(),
                                name=config['display_name'],
                                opacity=0.7,
                                marker_color=config['color']
                            ))
                            fig.add_trace(go.Histogram(
                                x=df2[value_col2].dropna(),
                                name=TABLE_CONFIG[secondary_key]['display_name'],
                                opacity=0.7,
                                marker_color=TABLE_CONFIG[secondary_key]['color']
                            ))
                            fig.update_layout(
                                title="Distribution Comparison",
                                barmode='overlay',
                                template="plotly_dark"
                            )
                            st.plotly_chart(fig, use_container_width=True, key=f"hist_compare_{selected_key}_{secondary_key}")
                        else:
                            st.warning("Please select a secondary data source.")
                    
                    elif test_type == "ANOVA":
                        st.write("ANOVA compares means across multiple groups.")
                        
                        # Group data by month
                        df['month'] = pd.to_datetime(df[date_col]).dt.month
                        groups = df.groupby('month')[value_col].apply(list).tolist()
                        
                        if len(groups) > 1:
                            # Perform ANOVA
                            f_stat, p_value = stats.f_oneway(*groups)
                            
                            col1, col2 = st.columns(2)
                            col1.metric("F-statistic", f"{f_stat:.4f}")
                            col2.metric("P-value", f"{p_value:.4f}")
                            
                            alpha = 0.05
                            if p_value < alpha:
                                st.success(f"There are significant differences between months (p < {alpha}).")
                            else:
                                st.info(f"No significant differences between months (p > {alpha}).")
                            
                            # Box plot by month
                            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                         'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                            df['month_name'] = df['month'].apply(lambda x: month_names[x-1])
                            
                            fig = px.box(df, x='month_name', y=value_col,
                                       title=f"{config['display_name']} by Month",
                                       labels={
                                           'month_name': 'Month',
                                           value_col: f"{config['display_name']} ({config['unit']})"
                                       },
                                       color_discrete_sequence=[config['color']])
                            fig.update_layout(template="plotly_dark")
                            st.plotly_chart(fig, use_container_width=True, key=f"boxplot_{selected_key}")
                        else:
                            st.warning("Not enough monthly data for ANOVA. Need at least 2 months.")
                
                elif analysis_type == "Regression Analysis":
                    st.write("### Regression Analysis")
                    
                    if HAS_STATSMODELS:
                        # Select secondary variable
                        secondary_source = st.selectbox(
                            "Select predictor variable:",
                            [TABLE_CONFIG[k]['display_name'] for k in data.keys() if k != selected_key and not data[k].empty]
                        )
                        
                        # Find the key for the secondary source
                        secondary_key = None
                        for k, v in TABLE_CONFIG.items():
                            if v['display_name'] == secondary_source and k in data:
                                secondary_key = k
                                break
                        
                        if secondary_key:
                            df2 = data[secondary_key]
                            value_col2 = TABLE_CONFIG[secondary_key]['value_column']
                            date_col2 = TABLE_CONFIG[secondary_key]['date_column']
                            
                            # Merge the dataframes on date
                            merged_df = pd.merge(
                                df[[date_col, value_col]], 
                                df2[[date_col2, value_col2]],
                                left_on=date_col, right_on=date_col2,
                                how='inner'
                            )
                            
                            if not merged_df.empty:
                                # Fit OLS model
                                X = merged_df[value_col2]
                                y = merged_df[value_col]
                                
                                X = sm.add_constant(X)
                                model = sm.OLS(y, X).fit()
                                
                                # Display regression statistics
                                st.write("#### Regression Statistics")
                                col1, col2, col3 = st.columns(3)
                                col1.metric("R-squared", f"{model.rsquared:.4f}")
                                col2.metric("Adjusted R-squared", f"{model.rsquared_adj:.4f}")
                                col3.metric("F-statistic", f"{model.fvalue:.4f}")
                                
                                # Display coefficients
                                st.write("#### Coefficients")
                                coef_df = pd.DataFrame({
                                    'Coefficient': model.params,
                                    'Std Error': model.bse,
                                    't-value': model.tvalues,
                                    'p-value': model.pvalues
                                })
                                st.dataframe(coef_df)
                                
                                # Create prediction line
                                x_range = np.linspace(merged_df[value_col2].min(), merged_df[value_col2].max(), 100)
                                X_pred = sm.add_constant(x_range)
                                y_pred = model.predict(X_pred)
                                
                                # Plot scatter with regression line
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=merged_df[value_col2], 
                                    y=merged_df[value_col],
                                    mode='markers',
                                    name='Data Points',
                                    marker=dict(color=config['color'])
                                ))
                                fig.add_trace(go.Scatter(
                                    x=x_range,
                                    y=y_pred,
                                    mode='lines',
                                    name='Regression Line',
                                    line=dict(color='red', width=3)
                                ))
                                fig.update_layout(
                                    title=f"Regression: {config['display_name']} vs {TABLE_CONFIG[secondary_key]['display_name']}",
                                    xaxis_title=f"{TABLE_CONFIG[secondary_key]['display_name']} ({TABLE_CONFIG[secondary_key]['unit']})",
                                    yaxis_title=f"{config['display_name']} ({config['unit']})",
                                    template="plotly_dark"
                                )
                                st.plotly_chart(fig, use_container_width=True, key=f"regression_{selected_key}_{secondary_key}")
                                
                                # Interpretation
                                intercept = model.params[0]
                                slope = model.params[1]
                                p_value = model.pvalues[1]
                                
                                interpretation = f"For each unit increase in {TABLE_CONFIG[secondary_key]['display_name']}, "
                                interpretation += f"the {config['display_name']} changes by {slope:.4f} {config['unit']}."
                                
                                if p_value < 0.05:
                                    st.success(interpretation + " This relationship is statistically significant (p < 0.05).")
                                else:
                                    st.info(interpretation + " However, this relationship is not statistically significant (p > 0.05).")
                            else:
                                st.warning("No matching dates found between the selected data sources.")
                        else:
                            st.warning("Please select a predictor variable.")
                    else:
                        st.error("Please install statsmodels to use Regression Analysis features.")
                        st.code("pip install statsmodels")
            else:
                st.warning("Please select valid data sources for analysis.")
    else:
        st.warning("Please select at least one data source from the sidebar.")
    
    # Footer with data source information
    st.markdown("---")
    st.markdown("### Data Source Information")
    
    # Calculate the exact span of data in years, months, days
    years_diff = max_date.year - min_date.year
    months_diff = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month
    days_diff = (max_date - min_date).days
    
    data_span = f"{years_diff} years, {months_diff % 12} months" if years_diff > 0 else f"{months_diff} months, {days_diff % 30} days"
    
    st.markdown(f"""
    - **Source:** BigQuery tables in dataset `{DATASET_ID}`
    - **Data Range:** {min_date} to {max_date} ({data_span})
    - **Last Dashboard Update:** {time.strftime("%Y-%m-%d %H:%M:%S")}
    
    This dashboard is powered by Streamlit and uses data from the National Grid ESO and Elexon.
    """)
    
    # Add version information
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Dashboard Version: 2.0.0")
    st.sidebar.caption(f"Updated: {time.strftime('%Y-%m-%d')}")
    st.sidebar.caption("⚡ GB Energy Dashboard")

if __name__ == "__main__":
    main()
