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

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Updated to use the new europe-west2 dataset
DATASET_ANALYTICS = "uk_energy_analysis"  # For advanced stats results

# Ensure output directory exists
OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

# Corrected table names and their corresponding date/value columns
TABLE_CONFIG = {
    "demand": {
        "table_name": "neso_demand_forecasts",
        "date_column": "settlement_date",
        "value_column": "national_demand_forecast",
        "display_name": "Demand Forecasts",
        "unit": "MW",
        "color": "blue"
    },
    "wind": {
        "table_name": "neso_wind_forecasts",
        "date_column": "settlement_date",
        "value_column": "forecast_output_mw",
        "display_name": "Wind Forecasts",
        "unit": "MW",
        "color": "green"
    },
    "carbon": {
        "table_name": "neso_carbon_intensity",
        "date_column": "measurement_date",
        "value_column": "carbon_intensity_gco2_kwh",
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
        "value_column": "cost_pounds",
        "display_name": "Balancing Services",
        "unit": "£",
        "color": "purple"
    },
    "warnings": {
        "table_name": "elexon_system_warnings",
        "date_column": "warning_date",
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
    
    # Only check the main neso_demand_forecasts table to speed up this query
    q = f"""
    SELECT MIN(settlement_date) as min_date, MAX(settlement_date) as max_date
    FROM `{get_table_name('neso_demand_forecasts')}`
    """
    try:
        result = list(_client.query(q).result())
        if result and len(result) > 0:
            return result[0].min_date, result[0].max_date
    except Exception as e:
        st.warning(f"Error getting date range: {e}")
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
    """Plot a time series using Plotly."""
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
                    fillcolor='rgba(180,200,230,0.3)',
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
                }
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
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
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
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red',
            'CRITICAL': 'darkred'
        }
        
        fig = go.Figure()
        
        for warning_type in warning_types:
            subset = df[df[value_col] == warning_type]
            
            for _, row in subset.iterrows():
                severity = row.get('severity', 'MEDIUM')
                color = severity_colors.get(severity, 'orange')
                
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
            height=height
        )
    
    # Update layout
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
        )
    )
    
    return fig

# --- Application ---
def main():
    # Page configuration
    st.set_page_config(
        page_title="GB Energy Dashboard",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .stPlotlyChart {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #1E3A8A;
    }
    .stSidebar {
        background-color: #f0f2f6;
    }
    .stTab {
        border-radius: 4px 4px 0 0;
    }
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
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
    
    # Dashboard metrics summary
    st.subheader("Dashboard Overview")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate date range for metrics
    date_range_days = (max_date - min_date).days
    
    with col1:
        st.metric(
            "Data Date Range", 
            f"{date_range_days} days",
            help=f"Data available from {min_date} to {max_date}"
        )
    
    with col2:
        try:
            demand_count_query = f"""
            SELECT COUNT(*) as count FROM `{get_table_name('neso_demand_forecasts')}`
            """
            demand_count = list(client.query(demand_count_query).result())[0].count
            st.metric(
                "Demand Records", 
                f"{demand_count:,}",
                help="Total number of demand forecast records"
            )
        except:
            st.metric("Demand Records", "Unknown")
    
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
    
    # Sidebar - data source selection
    st.sidebar.header("Data Sources")
    
    # Add a "Select All" option
    select_all = st.sidebar.checkbox("Select All Sources", value=True)
    
    # Add checkboxes for each data source
    selected_sources = {}
    for key, config in TABLE_CONFIG.items():
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
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
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
    else:
        st.warning("Please select at least one data source from the sidebar.")
    
    # Footer with data source information
    st.markdown("---")
    st.markdown("### Data Source Information")
    st.markdown(f"""
    - **Source:** BigQuery tables in dataset `{DATASET_ID}`
    - **Data Range:** {min_date} to {max_date}
    - **Last Dashboard Update:** {time.strftime("%Y-%m-%d %H:%M:%S")}
    
    This dashboard is powered by Streamlit and uses data from the BigQuery.
    """)
    
    # Add version information
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Dashboard Version: 1.2.0")
    st.sidebar.caption(f"Updated: {time.strftime('%Y-%m-%d')}")
    st.sidebar.caption("⚡ GB Energy Dashboard")

if __name__ == "__main__":
    main()
