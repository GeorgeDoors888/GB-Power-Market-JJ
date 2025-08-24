import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
from plotly.subplots import make_subplots

# Try to import optional packages but provide fallbacks if they're not available
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    st.warning("matplotlib and/or seaborn not available. Some visualizations will use alternatives.")

try:
    import statsmodels.api as sm
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    st.warning("statsmodels not available. Trend lines will be disabled in some charts.")

# --- Configuration ---
st.set_page_config(page_title="UK Energy Comprehensive Test Dashboard", layout="wide")

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
    
    fig.add_trace(go.Scatter(
        x=daily_demand['date'], 
        y=daily_demand['min_demand'],
        mode='lines',
        name='Min Demand (MW)',
        line=dict(dash='dot')
    ))
    
    # Update layout
    fig.update_layout(
        title="National Demand Forecast",
        xaxis_title="Date",
        yaxis_title="Demand (MW)",
        height=500
    )
    
    return fig

def plot_demand_by_hour(df):
    """Plot demand by hour of day."""
    if df.empty:
        st.error("No demand data available.")
        return
    
    # Create hour column from settlement period
    df['hour'] = (df['settlement_period'] - 1) // 2
    
    # Aggregate by hour
    hourly_demand = df.groupby('hour').agg({
        'national_demand_forecast': 'mean'
    }).reset_index()
    
    # Create figure
    fig = px.line(
        hourly_demand, 
        x='hour', 
        y='national_demand_forecast',
        labels={
            'hour': 'Hour of Day',
            'national_demand_forecast': 'Average Demand (MW)'
        },
        title="Demand Profile by Hour of Day"
    )
    
    # Update layout
    fig.update_layout(height=400)
    fig.update_xaxes(tickvals=list(range(0, 24)))
    
    return fig

def plot_demand_heatmap(df):
    """Plot demand heatmap by day of week and hour."""
    if df.empty:
        st.error("No demand data available.")
        return
    
    # Convert to datetime
    df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Create day of week and hour
    df['dow'] = df['settlement_date'].dt.dayofweek
    df['hour'] = (df['settlement_period'] - 1) // 2
    
    # Map day of week to name
    dow_map = {
        0: 'Monday',
        1: 'Tuesday',
        2: 'Wednesday',
        3: 'Thursday',
        4: 'Friday',
        5: 'Saturday',
        6: 'Sunday'
    }
    df['day_name'] = df['dow'].map(dow_map)
    
    # Aggregate
    heatmap_data = df.groupby(['day_name', 'hour']).agg({
        'national_demand_forecast': 'mean'
    }).reset_index()
    
    # Pivot for heatmap
    pivot_data = heatmap_data.pivot(
        index='day_name', 
        columns='hour', 
        values='national_demand_forecast'
    )
    
    # Order days correctly
    pivot_data = pivot_data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
    
    # Create heatmap
    fig = px.imshow(
        pivot_data,
        labels=dict(x="Hour of Day", y="Day of Week", color="Demand (MW)"),
        x=list(range(0, 24)),
        y=pivot_data.index,
        color_continuous_scale="Viridis",
        title="Demand Heatmap by Day and Hour"
    )
    
    # Update layout
    fig.update_layout(height=500)
    
    return fig

def plot_temperature_vs_demand(df):
    """Plot temperature vs demand scatter."""
    if df.empty or 'temperature_forecast' not in df.columns:
        st.error("No temperature data available.")
        return
    
    # Filter to avoid outliers
    df_filtered = df[
        (df['temperature_forecast'] > -5) &
        (df['temperature_forecast'] < 35) &
        (df['national_demand_forecast'] > 10000)
    ]
    
    # Create figure
    fig = px.scatter(
        df_filtered, 
        x='temperature_forecast', 
        y='national_demand_forecast',
        trendline="ols" if STATSMODELS_AVAILABLE else None,  # Use simple OLS if statsmodels not available
        labels={
            'temperature_forecast': 'Temperature (°C)',
            'national_demand_forecast': 'Demand (MW)'
        },
        title="Temperature vs Demand Relationship"
    )
    
    # If statsmodels not available, add a note on the chart
    if not STATSMODELS_AVAILABLE:
        fig.add_annotation(
            text="Note: Install statsmodels package for trend lines",
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            showarrow=False,
            font=dict(size=12, color="red")
        )
    
    # Update layout
    fig.update_layout(height=500)
    
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

def plot_wind_capacity_factor(df):
    """Plot wind capacity factor over time."""
    if df.empty:
        st.error("No wind generation data available.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Calculate capacity factor
    df['capacity_factor'] = df['actual_output_mw'] / df['capacity_mw']
    
    # Filter out invalid capacity factors
    df = df[(df['capacity_factor'] >= 0) & (df['capacity_factor'] <= 1)]
    
    # Group by date and wind farm
    daily_cf = df.groupby(['settlement_date', 'wind_farm_name']).agg({
        'capacity_factor': 'mean'
    }).reset_index()
    
    # Create figure
    fig = px.line(
        daily_cf, 
        x='settlement_date', 
        y='capacity_factor',
        color='wind_farm_name',
        labels={
            'settlement_date': 'Date',
            'capacity_factor': 'Capacity Factor',
            'wind_farm_name': 'Wind Farm'
        },
        title="Wind Farm Capacity Factor"
    )
    
    # Update layout
    fig.update_layout(height=500)
    fig.update_yaxes(range=[0, 1])
    
    return fig

def plot_forecast_vs_actual(df):
    """Plot forecast vs actual wind generation."""
    if df.empty:
        st.error("No wind generation data available.")
        return
    
    # Filter out extremes
    df_filtered = df[
        (df['forecast_output_mw'] > 0) & 
        (df['actual_output_mw'] > 0)
    ]
    
    # Create scatter plot
    fig = px.scatter(
        df_filtered,
        x='forecast_output_mw',
        y='actual_output_mw',
        color='wind_farm_name',
        trendline="ols" if STATSMODELS_AVAILABLE else None,
        labels={
            'forecast_output_mw': 'Forecast Output (MW)',
            'actual_output_mw': 'Actual Output (MW)',
            'wind_farm_name': 'Wind Farm'
        },
        title="Forecast vs Actual Wind Generation"
    )
    
    # Add reference line (perfect forecast)
    max_val = max(df_filtered['forecast_output_mw'].max(), df_filtered['actual_output_mw'].max())
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(dash='dash', color='gray'),
            name='Perfect Forecast'
        )
    )
    
    # Update layout
    fig.update_layout(height=500)
    fig.update_xaxes(range=[0, max_val])
    fig.update_yaxes(range=[0, max_val])
    
    return fig

def plot_wind_speed_power_curve(df):
    """Plot wind speed vs power output."""
    if df.empty or 'wind_speed_ms' not in df.columns:
        st.error("No wind speed data available.")
        return
    
    # Group by wind speed (rounded) and farm
    df['wind_speed_rounded'] = np.round(df['wind_speed_ms'])
    power_curve = df.groupby(['wind_speed_rounded', 'wind_farm_name']).agg({
        'actual_output_mw': 'mean',
        'capacity_mw': 'first'
    }).reset_index()
    
    # Calculate capacity factor
    power_curve['capacity_factor'] = power_curve['actual_output_mw'] / power_curve['capacity_mw']
    
    # Create figure
    fig = px.line(
        power_curve,
        x='wind_speed_rounded',
        y='capacity_factor',
        color='wind_farm_name',
        labels={
            'wind_speed_rounded': 'Wind Speed (m/s)',
            'capacity_factor': 'Capacity Factor',
            'wind_farm_name': 'Wind Farm'
        },
        title="Wind Power Curve"
    )
    
    # Update layout
    fig.update_layout(height=500)
    fig.update_yaxes(range=[0, 1])
    
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

def plot_bsuos_rate(df):
    """Plot BSUoS rate over time."""
    if df.empty or 'bsuos_rate_pounds_mwh' not in df.columns:
        st.error("No BSUoS rate data available.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in df.columns:
        df['settlement_date'] = pd.to_datetime(df['settlement_date'])
    
    # Group by date
    daily_rate = df.groupby('settlement_date').agg({
        'bsuos_rate_pounds_mwh': ['mean', 'max', 'min']
    }).reset_index()
    
    daily_rate.columns = ['date', 'mean_rate', 'max_rate', 'min_rate']
    
    # Create figure
    fig = go.Figure()
    
    # Add mean rate
    fig.add_trace(go.Scatter(
        x=daily_rate['date'],
        y=daily_rate['mean_rate'],
        mode='lines',
        name='Average BSUoS Rate',
        line=dict(color='blue')
    ))
    
    # Add range
    fig.add_trace(go.Scatter(
        x=daily_rate['date'],
        y=daily_rate['max_rate'],
        mode='lines',
        name='Max BSUoS Rate',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=daily_rate['date'],
        y=daily_rate['min_rate'],
        mode='lines',
        name='Min-Max Range',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(0, 0, 255, 0.2)'
    ))
    
    # Update layout
    fig.update_layout(
        title="BSUoS Rate Over Time",
        xaxis_title="Date",
        yaxis_title="BSUoS Rate (£/MWh)",
        height=500
    )
    
    return fig

def plot_cost_volume_relationship(df):
    """Plot relationship between cost and volume."""
    if df.empty:
        st.error("No balancing data available.")
        return
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x='volume_mwh',
        y='cost_pounds',
        opacity=0.5,
        trendline="ols" if STATSMODELS_AVAILABLE else None,
        labels={
            'volume_mwh': 'Volume (MWh)',
            'cost_pounds': 'Cost (£)'
        },
        title="Cost vs Volume Relationship"
    )
    
    # If statsmodels not available, add a note
    if not STATSMODELS_AVAILABLE:
        fig.add_annotation(
            text="Install statsmodels package for trend lines",
            xref="paper", yref="paper",
            x=0.5, y=1.05,
            showarrow=False,
            font=dict(size=12, color="red")
        )
    
    # Update layout
    fig.update_layout(height=500)
    
    return fig

def plot_balancing_costs_by_hour(df):
    """Plot balancing costs by hour of day."""
    if df.empty:
        st.error("No balancing data available.")
        return
    
    # Create hour column from settlement period
    df['hour'] = (df['settlement_period'] - 1) // 2
    
    # Aggregate by hour
    hourly_costs = df.groupby('hour').agg({
        'cost_pounds': 'mean',
        'balancing_services_cost': 'mean',
        'transmission_losses_cost': 'mean',
        'constraint_costs': 'mean'
    }).reset_index()
    
    # Create figure
    fig = go.Figure()
    
    # Add traces
    fig.add_trace(go.Bar(
        x=hourly_costs['hour'],
        y=hourly_costs['balancing_services_cost'],
        name='Balancing Services',
        marker_color='blue'
    ))
    
    fig.add_trace(go.Bar(
        x=hourly_costs['hour'],
        y=hourly_costs['transmission_losses_cost'],
        name='Transmission Losses',
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        x=hourly_costs['hour'],
        y=hourly_costs['constraint_costs'],
        name='Constraint Costs',
        marker_color='red'
    ))
    
    # Update layout
    fig.update_layout(
        barmode='stack',
        title="Balancing Costs by Hour of Day",
        xaxis_title="Hour",
        yaxis_title="Average Cost (£)",
        height=500
    )
    fig.update_xaxes(tickvals=list(range(0, 24)))
    
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
    
    # Aggregate demand by date and settlement period
    demand_agg = demand_df.groupby(['settlement_date', 'settlement_period']).agg({
        'national_demand_forecast': 'mean'
    }).reset_index()
    
    # Aggregate wind by date and settlement period
    wind_agg = wind_df.groupby(['settlement_date', 'settlement_period']).agg({
        'actual_output_mw': 'sum'
    }).reset_index()
    
    # Merge datasets on date and settlement period
    merged_df = pd.merge(
        demand_agg, 
        wind_agg, 
        on=['settlement_date', 'settlement_period'], 
        how='inner'
    )
    
    # Create figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add demand trace
    fig.add_trace(
        go.Scatter(
            x=merged_df['settlement_date'],
            y=merged_df['national_demand_forecast'],
            name='Demand (MW)',
            line=dict(color='blue')
        ),
        secondary_y=False
    )
    
    # Add wind trace
    fig.add_trace(
        go.Scatter(
            x=merged_df['settlement_date'],
            y=merged_df['actual_output_mw'],
            name='Wind Generation (MW)',
            line=dict(color='green')
        ),
        secondary_y=True
    )
    
    # Update layout
    fig.update_layout(
        title="Demand vs Wind Generation",
        height=500
    )
    
    # Update axes
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Demand (MW)", secondary_y=False)
    fig.update_yaxes(title_text="Wind Generation (MW)", secondary_y=True)
    
    return fig

def plot_wind_penetration(demand_df, wind_df):
    """Plot wind penetration (wind as % of demand)."""
    if demand_df.empty or wind_df.empty:
        st.error("Either demand or wind generation data is missing.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in demand_df.columns:
        demand_df['settlement_date'] = pd.to_datetime(demand_df['settlement_date'])
    if 'settlement_date' in wind_df.columns:
        wind_df['settlement_date'] = pd.to_datetime(wind_df['settlement_date'])
    
    # Aggregate demand by date
    demand_agg = demand_df.groupby('settlement_date').agg({
        'national_demand_forecast': 'mean'
    }).reset_index()
    
    # Aggregate wind by date
    wind_agg = wind_df.groupby('settlement_date').agg({
        'actual_output_mw': 'sum'
    }).reset_index()
    
    # Merge datasets
    merged_df = pd.merge(
        demand_agg, 
        wind_agg, 
        on='settlement_date', 
        how='inner'
    )
    
    # Calculate wind penetration
    merged_df['wind_penetration'] = (merged_df['actual_output_mw'] / merged_df['national_demand_forecast']) * 100
    
    # Create figure
    fig = go.Figure()
    
    # Add wind penetration
    fig.add_trace(go.Scatter(
        x=merged_df['settlement_date'],
        y=merged_df['wind_penetration'],
        mode='lines',
        name='Wind Penetration (%)',
        line=dict(color='green')
    ))
    
    # Add reference line for 20% renewable target
    fig.add_trace(go.Scatter(
        x=[merged_df['settlement_date'].min(), merged_df['settlement_date'].max()],
        y=[20, 20],
        mode='lines',
        name='20% Renewable Target',
        line=dict(dash='dash', color='red')
    ))
    
    # Update layout
    fig.update_layout(
        title="Wind Penetration (% of Demand)",
        xaxis_title="Date",
        yaxis_title="Wind Penetration (%)",
        height=500
    )
    
    return fig

def plot_correlation_matrix(demand_df, wind_df, balancing_df):
    """Plot correlation matrix between key variables."""
    # Check data
    if demand_df.empty or wind_df.empty or balancing_df.empty:
        st.error("Missing data for correlation matrix.")
        return
    
    # Ensure datetime format
    if 'settlement_date' in demand_df.columns:
        demand_df['settlement_date'] = pd.to_datetime(demand_df['settlement_date'])
    if 'settlement_date' in wind_df.columns:
        wind_df['settlement_date'] = pd.to_datetime(wind_df['settlement_date'])
    if 'settlement_date' in balancing_df.columns:
        balancing_df['settlement_date'] = pd.to_datetime(balancing_df['settlement_date'])
    
    # Aggregate by date
    demand_daily = demand_df.groupby('settlement_date').agg({
        'national_demand_forecast': 'mean',
        'temperature_forecast': 'mean',
        'wind_forecast': 'mean'
    }).reset_index()
    
    wind_daily = wind_df.groupby('settlement_date').agg({
        'actual_output_mw': 'sum',
        'wind_speed_ms': 'mean'
    }).reset_index()
    
    balancing_daily = balancing_df.groupby('settlement_date').agg({
        'cost_pounds': 'sum',
        'bsuos_rate_pounds_mwh': 'mean'
    }).reset_index()
    
    # Merge datasets
    merged_df = pd.merge(
        demand_daily, 
        wind_daily, 
        on='settlement_date', 
        how='inner',
        suffixes=('', '_wind')
    )
    
    merged_df = pd.merge(
        merged_df,
        balancing_daily,
        on='settlement_date',
        how='inner'
    )
    
    # Rename columns for clarity
    merged_df = merged_df.rename(columns={
        'national_demand_forecast': 'demand',
        'temperature_forecast': 'temperature',
        'wind_forecast': 'wind_forecast',
        'actual_output_mw': 'wind_generation',
        'wind_speed_ms': 'wind_speed',
        'cost_pounds': 'balancing_cost',
        'bsuos_rate_pounds_mwh': 'bsuos_rate'
    })
    
    # Select columns for correlation
    corr_cols = ['demand', 'temperature', 'wind_forecast', 'wind_generation', 
                 'wind_speed', 'balancing_cost', 'bsuos_rate']
    
    # Calculate correlation matrix
    corr_matrix = merged_df[corr_cols].corr()
    
    # Create heatmap with plotly (doesn't require seaborn)
    z = corr_matrix.values
    x = corr_matrix.columns.tolist()
    y = corr_matrix.index.tolist()
    
    # Create annotated heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=x,
        y=y,
        colorscale='RdBu_r',
        zmin=-1, zmax=1
    ))
    
    # Add text annotations
    annotations = []
    for i, row in enumerate(z):
        for j, value in enumerate(row):
            annotations.append(
                dict(
                    x=x[j],
                    y=y[i],
                    text=f"{value:.2f}",
                    font=dict(color='white' if abs(value) > 0.5 else 'black'),
                    showarrow=False
                )
            )
    
    fig.update_layout(
        title="Correlation Matrix",
        height=600,
        annotations=annotations
    )
    
    return fig

# --- Main Dashboard ---
st.title("UK Energy Comprehensive Test Dashboard")
st.write("This dashboard demonstrates all visualizations work with test data before using the full 200GB+ dataset.")

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
    
    # Create main tab groups
    main_tabs = st.tabs(["Demand Analysis", "Wind Generation", "Balancing Costs", "Cross-Dataset Analysis"])
    
    # Demand Analysis Tab
    with main_tabs[0]:
        st.header("Demand Analysis")
        
        # Create sub-tabs
        demand_tabs = st.tabs(["Time Series", "Patterns", "Temperature Impact"])
        
        with demand_tabs[0]:
            st.subheader("Demand Forecast Time Series")
            demand_fig = plot_demand_forecast(demand_df)
            if demand_fig:
                st.plotly_chart(demand_fig, use_container_width=True)
        
        with demand_tabs[1]:
            st.subheader("Demand Patterns")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Hourly Demand Profile")
                hourly_fig = plot_demand_by_hour(demand_df)
                if hourly_fig:
                    st.plotly_chart(hourly_fig, use_container_width=True)
            
            with col2:
                st.subheader("Weekly Demand Pattern")
                heatmap_fig = plot_demand_heatmap(demand_df)
                if heatmap_fig:
                    st.plotly_chart(heatmap_fig, use_container_width=True)
        
        with demand_tabs[2]:
            st.subheader("Temperature Impact on Demand")
            temp_fig = plot_temperature_vs_demand(demand_df)
            if temp_fig:
                st.plotly_chart(temp_fig, use_container_width=True)
    
    # Wind Generation Tab
    with main_tabs[1]:
        st.header("Wind Generation")
        
        # Create sub-tabs
        wind_tabs = st.tabs(["Generation", "Performance", "Wind Speed", "Forecast Accuracy"])
        
        with wind_tabs[0]:
            st.subheader("Wind Generation by Farm")
            wind_fig = plot_wind_generation(wind_df)
            if wind_fig:
                st.plotly_chart(wind_fig, use_container_width=True)
        
        with wind_tabs[1]:
            st.subheader("Wind Farm Performance")
            cf_fig = plot_wind_capacity_factor(wind_df)
            if cf_fig:
                st.plotly_chart(cf_fig, use_container_width=True)
        
        with wind_tabs[2]:
            st.subheader("Wind Speed Impact")
            power_curve_fig = plot_wind_speed_power_curve(wind_df)
            if power_curve_fig:
                st.plotly_chart(power_curve_fig, use_container_width=True)
        
        with wind_tabs[3]:
            st.subheader("Forecast vs Actual Generation")
            forecast_fig = plot_forecast_vs_actual(wind_df)
            if forecast_fig:
                st.plotly_chart(forecast_fig, use_container_width=True)
    
    # Balancing Costs Tab
    with main_tabs[2]:
        st.header("Balancing Costs")
        
        # Create sub-tabs
        balancing_tabs = st.tabs(["Cost Breakdown", "BSUoS Rates", "Cost Drivers", "Hourly Pattern"])
        
        with balancing_tabs[0]:
            st.subheader("Daily Balancing Cost Breakdown")
            balancing_fig = plot_balancing_costs(balancing_df)
            if balancing_fig:
                st.plotly_chart(balancing_fig, use_container_width=True)
        
        with balancing_tabs[1]:
            st.subheader("BSUoS Rate Trends")
            bsuos_fig = plot_bsuos_rate(balancing_df)
            if bsuos_fig:
                st.plotly_chart(bsuos_fig, use_container_width=True)
        
        with balancing_tabs[2]:
            st.subheader("Cost vs Volume Relationship")
            cost_vol_fig = plot_cost_volume_relationship(balancing_df)
            if cost_vol_fig:
                st.plotly_chart(cost_vol_fig, use_container_width=True)
        
        with balancing_tabs[3]:
            st.subheader("Balancing Costs by Hour")
            hourly_cost_fig = plot_balancing_costs_by_hour(balancing_df)
            if hourly_cost_fig:
                st.plotly_chart(hourly_cost_fig, use_container_width=True)
    
    # Cross-Dataset Analysis Tab
    with main_tabs[3]:
        st.header("Cross-Dataset Analysis")
        
        # Create sub-tabs
        cross_tabs = st.tabs(["Demand vs Wind", "Wind Penetration", "Correlation Analysis"])
        
        with cross_tabs[0]:
            st.subheader("Demand vs Wind Generation")
            combined_fig = plot_demand_vs_wind(demand_df, wind_df)
            if combined_fig:
                st.plotly_chart(combined_fig, use_container_width=True)
        
        with cross_tabs[1]:
            st.subheader("Wind Penetration")
            penetration_fig = plot_wind_penetration(demand_df, wind_df)
            if penetration_fig:
                st.plotly_chart(penetration_fig, use_container_width=True)
        
        with cross_tabs[2]:
            st.subheader("Correlation Matrix")
            corr_fig = plot_correlation_matrix(demand_df, wind_df, balancing_df)
            if corr_fig:
                st.plotly_chart(corr_fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.exception(e)

# Additional information
st.sidebar.markdown("---")
st.sidebar.info("""
This comprehensive dashboard is for testing all visualizations before using the real 200GB+ dataset. 
It includes 15+ visualization types across multiple data categories.
""")
