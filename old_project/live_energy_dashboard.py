#!/usr/bin/env python3
"""
Live Data Dashboard
==================
Enhanced dashboard that displays real-time data from BigQuery
with automatic refresh capability.
"""

import streamlit as st
import pandas as pd
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, date, timedelta
import time
import math
import os

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"
REFRESH_INTERVAL = 300  # seconds (5 minutes)

# --- Page Configuration ---
st.set_page_config(
    page_title="UK Energy Live Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .last-update {
        font-size: 0.8rem;
        color: #666;
        text-align: right;
    }
    .data-card {
        background-color: #f9f9f9;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-label {
        font-weight: bold;
        color: #555;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .refresh-button {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# --- BigQuery Functions ---
@st.cache_resource(ttl=3600)
def get_bq_client():
    """Initialize and return a BigQuery client"""
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        return None

def _qualified(table_name: str) -> str:
    """Returns the fully qualified BigQuery table name."""
    return f"`{PROJECT_ID}.{DATASET_ID}.{table_name}`"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_demand_data(_client, days=3):
    """Get the latest demand data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT settlementDate, settlementPeriod, demand
    FROM {_qualified("neso_demand_forecasts")}
    WHERE settlementDate BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    ORDER BY settlementDate, settlementPeriod
    """
    
    return _client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_generation_data(_client, days=3):
    """Get the latest generation data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT settlementDate, settlementPeriod, quantity
    FROM {_qualified("neso_wind_forecasts")}
    WHERE settlementDate BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    ORDER BY settlementDate, settlementPeriod
    """
    
    return _client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_latest_carbon_intensity(_client, days=3):
    """Get the latest carbon intensity data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT settlementDate, settlementPeriod, fuel_type, generation
    FROM {_qualified("neso_carbon_intensity")}
    WHERE settlementDate BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    ORDER BY settlementDate, settlementPeriod
    """
    
    return _client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_interconnector_flows(_client, days=3):
    """Get the latest interconnector flow data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT settlementDate, settlementPeriod, interconnector_name, quantity
    FROM {_qualified("neso_interconnector_flows")}
    WHERE settlementDate BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    ORDER BY settlementDate, settlementPeriod
    """
    
    return _client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_system_warnings(_client, days=7):
    """Get recent system warnings"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT settlementDate, warningType, messageText
    FROM {_qualified("elexon_system_warnings")}
    WHERE settlementDate BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
    ORDER BY settlementDate DESC
    LIMIT 20
    """
    
    return _client.query(query).result().to_dataframe()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_data_update_status(_client):
    """Get the latest update timestamp for each table"""
    tables = [
        "neso_demand_forecasts",
        "neso_wind_forecasts",
        "neso_carbon_intensity",
        "neso_interconnector_flows",
        "neso_balancing_services",
        "elexon_demand_outturn",
        "elexon_generation_outturn",
        "elexon_system_warnings"
    ]
    
    results = {}
    for table in tables:
        query = f"""
        SELECT MAX(settlementDate) as latest_date
        FROM {_qualified(table)}
        """
        
        df = _client.query(query).result().to_dataframe()
        if not df.empty and df.latest_date[0] is not None:
            results[table] = df.latest_date[0]
        else:
            results[table] = "No data"
    
    return results

# --- Visualization Functions ---
def plot_demand_forecast(data):
    """Plot demand forecast for recent days"""
    if data.empty:
        return go.Figure().update_layout(title="No demand forecast data available")
    
    # Create datetime column for better plotting
    data['datetime'] = pd.to_datetime(data['settlementDate']) + pd.to_timedelta(data['settlementPeriod'] * 30, unit='m')
    
    fig = px.line(
        data, 
        x='datetime', 
        y='demand',
        title="Electricity Demand Forecast (Last 3 Days)",
        labels={"demand": "Demand (MW)", "datetime": "Date & Time"}
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Date & Time",
        yaxis_title="Demand (MW)"
    )
    
    return fig

def plot_generation_mix(data):
    """Plot generation mix from carbon intensity data"""
    if data.empty:
        return go.Figure().update_layout(title="No generation mix data available")
    
    # Create datetime column and pivot the data
    data['datetime'] = pd.to_datetime(data['settlementDate']) + pd.to_timedelta(data['settlementPeriod'] * 30, unit='m')
    
    # Get the latest date
    latest_date = data['settlementDate'].max()
    latest_data = data[data['settlementDate'] == latest_date]
    
    # Pivot the data
    pivot_df = latest_data.pivot_table(
        index='settlementPeriod', 
        columns='fuel_type', 
        values='generation',
        aggfunc='sum'
    ).fillna(0)
    
    # Create a stacked area chart
    fig = px.area(
        pivot_df, 
        title=f"Generation Mix by Fuel Type ({latest_date})",
        labels={"value": "Generation (MW)", "settlementPeriod": "Settlement Period"}
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Settlement Period",
        yaxis_title="Generation (MW)",
        legend_title="Fuel Type"
    )
    
    return fig

def plot_interconnector_flows(data):
    """Plot interconnector flows"""
    if data.empty:
        return go.Figure().update_layout(title="No interconnector flow data available")
    
    # Create datetime column and get the latest date
    data['datetime'] = pd.to_datetime(data['settlementDate']) + pd.to_timedelta(data['settlementPeriod'] * 30, unit='m')
    latest_date = data['settlementDate'].max()
    
    # Filter for the latest date
    latest_data = data[data['settlementDate'] == latest_date]
    
    # Pivot the data
    pivot_df = latest_data.pivot_table(
        index='settlementPeriod', 
        columns='interconnector_name', 
        values='quantity',
        aggfunc='sum'
    ).fillna(0)
    
    # Create a line chart
    fig = px.line(
        pivot_df, 
        title=f"Interconnector Flows ({latest_date})",
        labels={"value": "Flow (MW)", "settlementPeriod": "Settlement Period"}
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Settlement Period",
        yaxis_title="Flow (MW)",
        legend_title="Interconnector"
    )
    
    return fig

def plot_wind_forecast(data):
    """Plot wind generation forecast"""
    if data.empty:
        return go.Figure().update_layout(title="No wind forecast data available")
    
    # Create datetime column for better plotting
    data['datetime'] = pd.to_datetime(data['settlementDate']) + pd.to_timedelta(data['settlementPeriod'] * 30, unit='m')
    
    fig = px.line(
        data, 
        x='datetime', 
        y='quantity',
        title="Wind Generation Forecast (Last 3 Days)",
        labels={"quantity": "Generation (MW)", "datetime": "Date & Time"}
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Date & Time",
        yaxis_title="Generation (MW)"
    )
    
    return fig

# --- Main Dashboard ---
def main():
    # Header
    st.markdown('<h1 class="main-header">UK Energy Live Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize BigQuery client
    client = get_bq_client()
    if not client:
        st.error("Could not connect to BigQuery. Please check your credentials.")
        return
    
    # Last update time and refresh button
    col1, col2 = st.columns([3, 1])
    with col1:
        last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f'<p class="last-update">Last updated: {last_update}</p>', unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.experimental_rerun()
    
    # Data update status
    with st.expander("Data Update Status"):
        status = get_data_update_status(_client=client)
        
        # Create columns for each table
        cols = st.columns(4)
        
        for i, (table, latest) in enumerate(status.items()):
            col_idx = i % 4
            with cols[col_idx]:
                st.metric(
                    label=table.replace('_', ' ').title(),
                    value=latest if isinstance(latest, str) else (latest.strftime("%Y-%m-%d") if pd.notna(latest) else "No data")
                )
    
    # Main dashboard tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Demand & Generation", "Generation Mix", "Interconnectors", "System Warnings"])
    
    # Tab 1: Demand & Generation
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            demand_data = get_latest_demand_data(_client=client)
            st.plotly_chart(plot_demand_forecast(demand_data), use_container_width=True)
        
        with col2:
            wind_data = get_latest_generation_data(_client=client)
            st.plotly_chart(plot_wind_forecast(wind_data), use_container_width=True)
    
    # Tab 2: Generation Mix
    with tab2:
        carbon_data = get_latest_carbon_intensity(_client=client)
        st.plotly_chart(plot_generation_mix(carbon_data), use_container_width=True)
    
    # Tab 3: Interconnectors
    with tab3:
        flow_data = get_interconnector_flows(_client=client)
        st.plotly_chart(plot_interconnector_flows(flow_data), use_container_width=True)
    
    # Tab 4: System Warnings
    with tab4:
        warnings = get_system_warnings(_client=client)
        
        if warnings.empty:
            st.info("No system warnings in the last 7 days.")
        else:
            for _, row in warnings.iterrows():
                with st.container():
                    st.markdown(f"""
                    <div class="data-card">
                        <p><strong>Date:</strong> {row['settlementDate']}</p>
                        <p><strong>Type:</strong> {row['warningType']}</p>
                        <p><strong>Message:</strong> {row['messageText']}</p>
                    </div>
                    <br>
                    """, unsafe_allow_html=True)
    
    # Auto-refresh (every 5 minutes)
    st.markdown(
        f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {REFRESH_INTERVAL * 1000});
        </script>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
