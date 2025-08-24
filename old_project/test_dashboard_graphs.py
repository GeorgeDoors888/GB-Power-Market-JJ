import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta

# --- Configuration ---
st.set_page_config(page_title="UK Energy Test Dashboard", layout="wide")

PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Production dataset in europe-west2 region

# Initialize BigQuery client
@st.cache_resource
def get_client():
    return bigquery.Client(project=PROJECT_ID)

# Cache the query results
@st.cache_data(ttl=3600)
def run_query(query):
    client = get_client()
    query_job = client.query(query)
    return query_job.to_dataframe()

# --- Plotting Functions ---

def plot_demand_forecast(df):
    """Plot demand forecast data."""
    if df.empty:
        st.error("No demand forecast data available.")
        return
    
    # Ensure datetime format for settlement_date
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Group by date to get daily stats
    daily_demand = df.groupby('settlement_date').agg({
        'national_demand_forecast': ['mean', 'max', 'min']
    }).reset_index()
    
    daily_demand.columns = ['date', 'mean_demand', 'peak_demand', 'min_demand']
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Scatter(
        x=daily_demand['date'], 
        y=daily_demand['peak_demand'],
        mode='lines',
        name='Peak Demand (MW)'
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_demand['date'], 
        y=daily_demand['mean_demand'],
        mode='lines',
        name='Mean Demand (MW)',
        line=dict(dash='dash')
    ))
    
    # Update layout
    fig.update_layout(
        title="National Demand Forecast",
        xaxis_title="Date",
        yaxis_title="Demand (MW)",
        height=500
    )
    
    return fig

def plot_wind_generation(df):
    """Plot wind generation data."""
    if df.empty:
        st.error("No wind generation data available.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Group by date and wind farm
    daily_gen = df.groupby(['settlement_date', 'wind_farm_name']).agg({
        'forecast_output_mw': 'mean',
        'actual_output_mw': 'mean',
        'capacity_mw': 'first'
    }).reset_index()
    
    # Create figure
    fig = px.line(
        daily_gen, 
        x='settlement_date', 
        y='actual_output_mw',
        color='wind_farm_name',
        labels={
            'settlement_date': 'Date',
            'actual_output_mw': 'Generation (MW)',
            'wind_farm_name': 'Wind Farm'
        },
        title="Wind Farm Generation"
    )
    
    # Update layout
    fig.update_layout(height=500)
    
    return fig

def plot_balancing_costs(df):
    """Plot balancing costs."""
    if df.empty:
        st.error("No balancing costs data available.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Group by date
    daily_costs = df.groupby('settlement_date').agg({
        'cost_pounds': 'sum',
        'balancing_services_cost': 'sum',
        'transmission_losses_cost': 'sum',
        'constraint_costs': 'sum'
    }).reset_index()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Bar(
        x=daily_costs['settlement_date'],
        y=daily_costs['balancing_services_cost'],
        name='Balancing Services',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=daily_costs['settlement_date'],
        y=daily_costs['transmission_losses_cost'],
        name='Transmission Losses',
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        x=daily_costs['settlement_date'],
        y=daily_costs['constraint_costs'],
        name='Constraint Costs',
        marker_color='red'
    ))
    
    # Update layout to stack bars
    fig.update_layout(
        barmode='stack',
        title="Daily Balancing Costs",
        xaxis_title="Date",
        yaxis_title="Cost (£)",
        height=500
    )
    
    return fig

def plot_demand_vs_wind(demand_df, wind_df):
    """Plot demand vs wind generation."""
    if demand_df.empty or wind_df.empty:
        st.error("Either demand or wind generation data is missing.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in demand_df.columns:
        demand_df['settlement_date'] = pd.to_datetime(demand_df['settlement_date'])
    if 'settlement_date' in wind_df.columns:
        wind_df['settlement_date'] = pd.to_datetime(wind_df['settlement_date'])
    
    # Aggregate demand by date
    daily_demand = demand_df.groupby('settlement_date').agg({
        'national_demand_forecast': 'mean'
    }).reset_index()
    
    # Aggregate wind by date
    wind_sum = wind_df.groupby('settlement_date').agg({
        'forecast_output_mw': 'sum'
    }).reset_index()
    
    # Merge datasets
    merged_df = pd.merge(
        daily_demand, 
        wind_sum, 
        on='settlement_date', 
        how='inner'
    )
    
    # Create figure
    fig = go.Figure()
    
    # Create secondary Y axis
    fig.add_trace(go.Scatter(
        x=merged_df['settlement_date'],
        y=merged_df['national_demand_forecast'],
        name='Demand (MW)',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=merged_df['settlement_date'],
        y=merged_df['forecast_output_mw'],
        name='Wind Generation (MW)',
        line=dict(color='green', dash='dot'),
        yaxis="y2"
    ))
    
    # Update layout with secondary y-axis
    fig.update_layout(
        title="Demand vs Wind Generation",
        xaxis_title="Date",
        yaxis_title="Demand (MW)",
        yaxis2=dict(
            title="Wind Generation (MW)",
            overlaying="y",
            side="right"
        ),
        height=500
    )
    
    return fig

# --- Main Dashboard ---
st.title("UK Energy Test Dashboard - Graph Verification")
st.write("This dashboard demonstrates that all visualizations work with test data before using the full 200GB+ dataset.")

# Sidebar for time range selection
st.sidebar.header("Date Range Selection")

# Get the date range from the test data
# We'll default to 3 months of data to avoid performance issues during testing
end_date = date(2024, 3, 31)  # Q1 2024 end
start_date = date(2024, 1, 1)  # Q1 2024 start

date_range = st.sidebar.date_input(
    "Select date range:",
    value=(start_date, end_date),
    min_value=date(2023, 1, 1),
    max_value=date(2024, 12, 31)
)

if len(date_range) == 2:
    start_date, end_date = date_range
    date_filter = f"WHERE settlement_date BETWEEN '{start_date}' AND '{end_date}'"
else:
    date_filter = ""

# Get data from BigQuery
try:
    # Demand data
    demand_query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.neso_demand_forecasts`
    {date_filter}
    ORDER BY settlement_date
    """
    
    # Wind data
    wind_query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.neso_wind_forecasts`
    {date_filter}
    ORDER BY settlement_date
    """
    
    # Balancing data
    balancing_query = f"""
    SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.neso_balancing_services`
    {date_filter}
    ORDER BY settlement_date
    """
    
    with st.spinner("Loading data from BigQuery..."):
        demand_df = run_query(demand_query)
        wind_df = run_query(wind_query)
        balancing_df = run_query(balancing_query)
    
    # Display data statistics
    st.sidebar.subheader("Data Statistics")
    st.sidebar.write(f"Demand records: {len(demand_df):,}")
    st.sidebar.write(f"Wind records: {len(wind_df):,}")
    st.sidebar.write(f"Balancing records: {len(balancing_df):,}")
    
    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs(["Demand Forecast", "Wind Generation", "Balancing Costs", "Demand vs Wind"])
    
    with tab1:
        st.subheader("Demand Forecast")
        demand_fig = plot_demand_forecast(demand_df)
        if demand_fig:
            st.plotly_chart(demand_fig, use_container_width=True)
    
    with tab2:
        st.subheader("Wind Generation")
        wind_fig = plot_wind_generation(wind_df)
        if wind_fig:
            st.plotly_chart(wind_fig, use_container_width=True)
    
    with tab3:
        st.subheader("Balancing Costs")
        balancing_fig = plot_balancing_costs(balancing_df)
        if balancing_fig:
            st.plotly_chart(balancing_fig, use_container_width=True)
    
    with tab4:
        st.subheader("Demand vs Wind")
        combined_fig = plot_demand_vs_wind(demand_df, wind_df)
        if combined_fig:
            st.plotly_chart(combined_fig, use_container_width=True)
    
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.exception(e)

# Additional information
st.sidebar.markdown("---")
st.sidebar.info("""
This dashboard is for testing purposes only. It verifies that all graphs work 
with test data before using the real 200GB+ dataset. Test data was generated 
using the `generate_test_data.py` script for dates between Jan 1, 2023 and Dec 31, 2024.
""")
