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
    """Plot a time series using Plotly with enhanced visualization.
    
    Creates high-quality time series visualizations with appropriate data aggregation
    based on the date range and data density.
    """
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
    
    # Check if the data is numeric for appropriate visualization
    is_numeric = False
    try:
        is_numeric = pd.api.types.is_numeric_dtype(df[value_col])
    except:
        is_numeric = False
    
    # Create a copy to avoid modifying the original dataframe
    df_copy = df.copy()
    
    # For time series with numeric data, we'll create an enhanced visualization
    if is_numeric and len(df) > 0:
        # Determine if we need to aggregate based on data size
        needs_aggregation = len(df) > 100
        
        if needs_aggregation:
            # Ensure date column is datetime
            try:
                df_copy[date_col] = pd.to_datetime(df_copy[date_col])
                
                # Get the date range span
                date_range_days = (df_copy[date_col].max() - df_copy[date_col].min()).days
                
                # Create daily aggregation
                df_copy['date_day'] = df_copy[date_col].dt.date
                
                # Group by day and calculate statistics
                daily_stats = df_copy.groupby('date_day').agg({
                    value_col: ['mean', 'min', 'max', 'count']
                }).reset_index()
                
                # Flatten column names
                daily_stats.columns = ['date', 'mean', 'min', 'max', 'count']
                
                # Convert date back to datetime for plotting
                daily_stats['date'] = pd.to_datetime(daily_stats['date'])
                
                # Create figure for aggregated data
                fig = go.Figure()
                
                # Add min-max range area
                fig.add_trace(go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['max'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False
                ))
                
                fig.add_trace(go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['min'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor='rgba(180,200,230,0.3)',
                    name='Daily Range'
                ))
                
                # Add mean line
                fig.add_trace(go.Scatter(
                    x=daily_stats['date'],
                    y=daily_stats['mean'],
                    mode='lines',
                    name='Daily Average',
                    line=dict(color=color, width=2)
                ))
                
            except Exception as e:
                # If aggregation fails, fall back to simple plot
                st.warning(f"Aggregation failed: {e}. Showing simple plot.")
                needs_aggregation = False
        
        if not needs_aggregation:
            # Simple scatter plot for smaller datasets or if aggregation fails
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df_copy[date_col],
                y=df_copy[value_col],
                mode='lines+markers',
                name=display_name,
                line=dict(color=color, width=2)
            ))
    else:
        # For non-numeric data or very small datasets, create a simple bar chart
        if 'settlement_period' in df.columns:
            # If we have settlement periods, count occurrences by date
            count_df = df.groupby(date_col).size().reset_index(name='count')
            
            fig = px.bar(
                count_df,
                x=date_col,
                y='count',
                title=title or f"{display_name} Count by Date",
                labels={
                    date_col: 'Date',
                    'count': 'Count'
                },
                color_discrete_sequence=[color]
            )
        else:
            # Simple line or scatter plot for any other data
            fig = px.line(
                df,
                x=date_col,
                y=value_col,
                title=title or display_name,
                labels={
                    date_col: 'Date',
                    value_col: display_name
                },
                color_discrete_sequence=[color]
            )
    
    # Update layout for all plot types
    fig.update_layout(
        title=title or display_name,
        xaxis_title="Date",
        yaxis_title=unit or "Value",
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
                    marker=dict(
                        size=8, 
                        color=color,
                        line=dict(width=1, color='white')
                    ),
                    showlegend=False,
                    hoverinfo='skip'
                )
            )
    else:
        # For non-numeric data, create an enhanced categorical visualization
        # Group by date and category
        if 'severity' in df.columns:
            # If we have severity, use it for coloring
            category_counts = df.groupby([date_col, value_col, 'severity']).size().reset_index(name='count')
            fig = px.bar(
                category_counts,
                x=date_col,
                y='count',
                color='severity',
                barmode='group',
                labels={
                    date_col: 'Date',
                    'count': 'Count',
                    value_col: display_name,
                    'severity': 'Severity'
                },
                color_discrete_map={
                    'LOW': 'green',
                    'MEDIUM': 'orange',
                    'HIGH': 'red',
                    'CRITICAL': 'darkred'
                }
            )
        else:
            # Standard grouping by category
            category_counts = df.groupby([date_col, value_col]).size().reset_index(name='count')
            
            # Use a nice color sequence
            color_sequence = px.colors.qualitative.Safe if len(df[value_col].unique()) <= 10 else px.colors.qualitative.Plotly
            
            fig = px.bar(
                category_counts,
                x=date_col,
                y='count',
                color=value_col,
                barmode='group',
                color_discrete_sequence=color_sequence,
                labels={
                    date_col: 'Date',
                    'count': 'Count',
                    value_col: display_name
                }
            )
    
    # ENHANCED: Improve layout with better styling and annotations
    adjusted_title = f"{title or display_name} ({time_unit} View)" if is_numeric else (title or display_name)
    
    fig.update_layout(
        title={
            'text': adjusted_title,
            'font': {'size': 24, 'color': '#1E3A8A'}
        },
        xaxis={
            'title': "Date",
            'gridcolor': '#f0f0f0',
            'zeroline': False
        },
        yaxis={
            'title': unit,
            'gridcolor': '#f0f0f0',
            'zeroline': True,
            'zerolinecolor': '#e0e0e0'
        },
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e0e0e0',
            borderwidth=1
        ),
        plot_bgcolor='#ffffff',
        hovermode='closest',
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        )
    )
    
    # Add annotations for data information
    if is_numeric:
        total_records = agg_df['count'].sum()
        date_range_text = f"{agg_df['date'].min().strftime('%Y-%m-%d')} to {agg_df['date'].max().strftime('%Y-%m-%d')}"
        
        fig.add_annotation(
            xref='paper', yref='paper',
            x=0.01, y=0.01,
            text=f"Total records: {total_records:,} | Period: {date_range_text}",
            showarrow=False,
            font=dict(size=10, color="#666666"),
            align="left"
        )
    
    return fig

def plot_warning_timeline(df, height=500):
    """Plot system warnings as a timeline with enhanced visualization.
    
    This function creates high-quality warning timeline visualizations with:
    - Severity-based color coding
    - Duration indicators for warnings with start/end times
    - Enhanced hover information
    - Better categorization and sorting of warning types
    - Visual markers to differentiate warning types
    """
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
    
    # Create a copy to avoid modifying the original dataframe
    warnings_df = df.copy()
    
    # Ensure warning_date is datetime
    warnings_df[date_col] = pd.to_datetime(warnings_df[date_col])
    
    # Get unique warning types and sort them
    warning_types = sorted(warnings_df[value_col].unique())
    
    # Create figure
    fig = go.Figure()
    
    # Define severity colors
    severity_colors = {
        'LOW': '#4CAF50',     # Green
        'MEDIUM': '#FF9800',  # Orange
        'HIGH': '#F44336',    # Red
        'CRITICAL': '#B71C1C' # Dark Red
    }
    
    # Define warning symbols
    warning_symbols = {
        'CAPACITY_MARKET_NOTICE': 'circle',
        'DEMAND_CONTROL': 'square',
        'ELECTRICITY_MARGIN_NOTICE': 'diamond',
        'HIGH_RISK_OF_DEMAND_REDUCTION': 'triangle-up',
        'SYSTEM_STRESS_EVENT': 'x',
    }
    
    # Default values
    default_color = '#FF9800'  # Default to orange
    default_symbol = 'circle'  # Default to circle
    
    # Create legends for severity and warning types (once per type)
    severity_shown = set()
    warning_type_shown = set()
    
    for _, row in warnings_df.iterrows():
        warning_type = row[value_col]
        
        # Get the warning date
        warning_date = row[date_col]
        
        # Determine severity if available
        severity = row.get('severity', 'MEDIUM')  # Default to MEDIUM if not specified
        color = severity_colors.get(severity, default_color)
        
        # Determine symbol based on warning type
        symbol = warning_symbols.get(warning_type, default_symbol)
        
        # Create the hover text with all available information
        hover_text = f"<b>Type:</b> {warning_type}<br><b>Date:</b> {warning_date.strftime('%Y-%m-%d')}<br>"
        
        if 'severity' in row:
            hover_text += f"<b>Severity:</b> {severity}<br>"
        
        if 'description' in row and pd.notna(row['description']):
            hover_text += f"<b>Description:</b> {row['description']}<br>"
            
        if 'start_time' in row and pd.notna(row['start_time']):
            hover_text += f"<b>Start:</b> {row['start_time']}<br>"
            
        if 'end_time' in row and pd.notna(row['end_time']):
            hover_text += f"<b>End:</b> {row['end_time']}<br>"
            
        if 'affected_region' in row and pd.notna(row['affected_region']):
            hover_text += f"<b>Region:</b> {row['affected_region']}"
        
        # Determine if this is the first occurrence of this warning type and severity
        show_warning_in_legend = warning_type not in warning_type_shown
        show_severity_in_legend = severity not in severity_shown
        
        # Determine legend name
        if show_warning_in_legend:
            legend_name = warning_type
            warning_type_shown.add(warning_type)
        elif show_severity_in_legend:
            legend_name = f"Severity: {severity}"
            severity_shown.add(severity)
        else:
            legend_name = None  # Don't show in legend
            
        # Add the warning point
        fig.add_trace(
            go.Scatter(
                x=[warning_date],
                y=[warning_type],
                mode='markers',
                marker=dict(
                    size=12,
                    color=color,
                    symbol=symbol,
                    line=dict(width=1, color='black')
                ),
                name=legend_name,
                hovertemplate=hover_text + "<extra></extra>",
                showlegend=bool(legend_name)
            )
        )
        
        # Add duration line if we have start and end times
        if 'start_time' in warnings_df.columns and 'end_time' in warnings_df.columns:
            if pd.notna(row.get('start_time')) and pd.notna(row.get('end_time')):
                try:
                    # Convert to datetime if they're not already
                    start = pd.to_datetime(row['start_time']) if not isinstance(row['start_time'], pd.Timestamp) else row['start_time']
                    end = pd.to_datetime(row['end_time']) if not isinstance(row['end_time'], pd.Timestamp) else row['end_time']
                    
                    # Add a line representing the duration
                    fig.add_trace(
                        go.Scatter(
                            x=[start, end],
                            y=[warning_type, warning_type],
                            mode='lines',
                            line=dict(
                                color=color,
                                width=4,
                                dash='solid'
                            ),
                            showlegend=False,
                            hoverinfo='skip'
                        )
                    )
                except Exception as e:
                    # Skip if dates can't be processed
                    pass
    
    # Add a header for the timeline
    title_text = "System Warnings Timeline"
    
    # Add warning count information
    warnings_count = len(warnings_df)
    unique_days = warnings_df[date_col].dt.date.nunique()
    
    # Get date range for subtitle
    if not warnings_df.empty:
        min_date = warnings_df[date_col].min().strftime('%Y-%m-%d')
        max_date = warnings_df[date_col].max().strftime('%Y-%m-%d')
        subtitle = f"{warnings_count} warnings across {unique_days} days ({min_date} to {max_date})"
    else:
        subtitle = "No warnings in selected period"
    
    # Update layout with enhanced styling
    fig.update_layout(
        title={
            'text': title_text,
            'font': {'size': 24, 'color': '#1E3A8A'}
        },
        xaxis={
            'title': "Date",
            'gridcolor': '#f0f0f0',
            'zeroline': False
        },
        yaxis={
            'title': "Warning Type",
            'gridcolor': '#f0f0f0',
            'zeroline': False,
            'type': 'category',
            'categoryorder': 'array',
            'categoryarray': warning_types
        },
        height=height,
        template="plotly_white",
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='#e0e0e0',
            borderwidth=1
        ),
        plot_bgcolor='#ffffff',
        hovermode='closest',
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        )
    )
    
    # Add subtitle as annotation
    fig.add_annotation(
        xref='paper', yref='paper',
        x=0.5, y=1.06,
        text=subtitle,
        showarrow=False,
        font=dict(size=14, color="#666666"),
        align="center"
    )
    
    # Add grid lines for better readability
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#f0f0f0')
    
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
    .stMarkdown a {
        color: #3366cc;
        text-decoration: none;
    }
    .stMarkdown a:hover {
        text-decoration: underline;
    }
    div[data-testid="stDecoration"] {
        background-image: linear-gradient(90deg, #1E3A8A, #3366cc);
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
    This dashboard provides comprehensive insights into Great Britain's energy system using data from the 
    National Electricity System Operator (NESO) and Elexon, stored in BigQuery. 
    
    Select date ranges and data sources using the sidebar controls to explore different aspects of 
    the electricity grid including demand forecasts, wind generation, carbon intensity, and system warnings.
    """)
    
    # Dashboard metrics summary
    st.subheader("Dashboard Overview")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate date range for metrics
    date_range_days = (max_date - min_date).days
    data_freshness_days = (date.today() - max_date).days
    
    with col1:
        st.metric(
            "Data Date Range", 
            f"{date_range_days} days",
            help=f"Data available from {min_date} to {max_date}"
        )
    
    with col2:
        freshness_delta = None if data_freshness_days == 0 else f"-{data_freshness_days} days"
        freshness_label = "Current" if data_freshness_days == 0 else f"{data_freshness_days} days ago"
        st.metric(
            "Last Updated", 
            freshness_label,
            delta=freshness_delta,
            delta_color="inverse",
            help=f"Data was last updated on {max_date}"
        )
    
    with col3:
        # Get table row counts
        try:
            demand_count_query = f"""
            SELECT COUNT(*) as count FROM `{get_table_name('neso_demand_forecasts')}`
            """
            demand_count = list(client.query(demand_count_query).result())[0].count
            st.metric(
                "Total Demand Records", 
                f"{demand_count:,}",
                help="Total number of demand forecast records in the database"
            )
        except:
            st.metric("Total Demand Records", "Unknown")
    
    with col4:
        try:
            warning_count_query = f"""
            SELECT COUNT(*) as count FROM `{get_table_name('elexon_system_warnings')}`
            """
            warning_count = list(client.query(warning_count_query).result())[0].count
            st.metric(
                "System Warnings", 
                f"{warning_count:,}",
                help="Total number of system warnings in the database"
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
    selected_sources = {}
    
    # Group sources into categories
    forecast_sources = ['demand', 'wind']
    operational_sources = ['carbon', 'interconnector', 'balancing']
    warning_sources = ['warnings']
    
    # Add a "Select All" option
    select_all = st.sidebar.checkbox("Select All Sources", value=True)
    
    # Add checkboxes by category
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
        step=50,
        help="Adjust the height of charts in pixels"
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
                                    f"{min_val:.2f} {config['unit']}",
                                    help=f"Minimum value of {config['display_name']}"
                                )
                            
                            # Max value
                            with metric_cols[1]:
                                max_val = df[value_col].max()
                                st.metric(
                                    "Maximum", 
                                    f"{max_val:.2f} {config['unit']}",
                                    help=f"Maximum value of {config['display_name']}"
                                )
                            
                            # Average
                            with metric_cols[2]:
                                mean_val = df[value_col].mean()
                                st.metric(
                                    "Average", 
                                    f"{mean_val:.2f} {config['unit']}",
                                    help=f"Average value of {config['display_name']}"
                                )
                            
                            # Standard deviation or median
                            with metric_cols[3]:
                                try:
                                    std_val = df[value_col].std()
                                    st.metric(
                                        "Std. Deviation", 
                                        f"{std_val:.2f} {config['unit']}",
                                        help=f"Standard deviation of {config['display_name']}"
                                    )
                                except:
                                    median_val = df[value_col].median()
                                    st.metric(
                                        "Median", 
                                        f"{median_val:.2f} {config['unit']}",
                                        help=f"Median value of {config['display_name']}"
                                    )
                        else:
                            # For non-numeric data, show category counts
                            value_counts = df[value_col].value_counts()
                            
                            # Most common value
                            with metric_cols[0]:
                                most_common = value_counts.index[0] if not value_counts.empty else "None"
                                st.metric(
                                    "Most Common", 
                                    f"{most_common}",
                                    help=f"Most common {config['display_name']}"
                                )
                            
                            # Count of most common
                            with metric_cols[1]:
                                count_most_common = value_counts.iloc[0] if not value_counts.empty else 0
                                st.metric(
                                    "Count", 
                                    f"{count_most_common:,}",
                                    help=f"Count of most common {config['display_name']}"
                                )
                            
                            # Number of categories
                            with metric_cols[2]:
                                num_categories = len(value_counts)
                                st.metric(
                                    "Categories", 
                                    f"{num_categories:,}",
                                    help=f"Number of unique {config['display_name']}"
                                )
                            
                            # Total records
                            with metric_cols[3]:
                                st.metric(
                                    "Total Records", 
                                    f"{len(df):,}",
                                    help=f"Total number of {config['display_name']} records"
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
    
    This dashboard is powered by Streamlit and uses data from the National Electricity System Operator (NESO) and Elexon.
    The data is stored in Google BigQuery and updated regularly.
    """)
    
    # Add version information
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Dashboard Version: 1.2.0")
    st.sidebar.caption(f"Updated: {time.strftime('%Y-%m-%d')}")
    st.sidebar.caption("⚡ GB Energy Dashboard")

if __name__ == "__main__":
    main()
