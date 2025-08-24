import streamlit as st
import pandas as pd
import numpy as np
import json
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, datetime, timedelta
import ast

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"  # Production dataset in europe-west2 region

# Table configurations with column mappings
TABLE_CONFIG = {
    "demand": {
        "table_name": "neso_demand_forecasts",
        "date_col": "settlement_date",
        "value_col": "national_demand_forecast",
        "numeric_cols": ["national_demand_forecast", "temperature_forecast", "wind_forecast", "solar_forecast"],
        "column_map": {
            "settlement_date": "day",
            "national_demand_forecast": "peak_demand"
        }
    },
    "generation": {
        "table_name": "neso_wind_forecasts",
        "date_col": "settlement_date",
        "value_col": "forecast_output_mw",
        "numeric_cols": ["forecast_output_mw", "actual_output_mw", "capacity_mw"],
        "column_map": {
            "forecast_output_mw": "generation",
            "wind_farm_name": "fuel_type"
        }
    },
    "balancing": {
        "table_name": "neso_balancing_services",
        "date_col": "settlement_date",
        "value_col": "volume_mwh",
        "numeric_cols": ["bsuos_rate_pounds_mwh", "volume_mwh", "cost_pounds", 
                         "balancing_services_cost", "transmission_losses_cost", "constraint_costs"],
        "column_map": {
            "balancing_services_cost": "acceptance_type",
            "volume_mwh": "total_volume_mwh"
        }
    },
    "carbon": {
        "table_name": "neso_carbon_intensity",
        "date_col": "measurement_date",
        "value_col": "carbon_intensity_gco2_kwh",
        "numeric_cols": ["carbon_intensity_gco2_kwh", "forecast_carbon_intensity_gco2_kwh"],
        "column_map": {}
    },
    "interconnectors": {
        "table_name": "neso_interconnector_flows",
        "date_col": "settlement_date",
        "value_col": "flow_mw",
        "numeric_cols": ["flow_mw", "capacity_mw", "price_differential_gbp_mwh", "utilization_pct"],
        "column_map": {}
    },
    "warnings": {
        "table_name": "elexon_system_warnings",
        "date_col": "warning_date",
        "value_col": "impact_mw",
        "numeric_cols": ["impact_mw"],
        "column_map": {}
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
        
        # If the date column doesn't exist, try fallback columns
        if date_col and date_col not in columns:
            fallback_cols = ['charge_date', 'forecast_date', 'measurement_date', 'warning_date']
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
        
        if df.empty:
            return df
            
        # Ensure datetime columns are properly formatted
        datetime_cols = [
            col for col in df.columns 
            if any(term in col.lower() for term in ['date', 'time', 'timestamp'])
        ]
        
        for col in datetime_cols:
            if col in df.columns:
                try:
                    if 'time' in col.lower() and 'date' not in col.lower():
                        # Just time column, leave as is
                        pass
                    else:
                        # Try to convert to datetime
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                except:
                    pass

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
            if "fuel_type" not in df.columns:
                df['fuel_type'] = 'WIND'  # Default if no fuel type column
        
        # Special handling for carbon intensity generation mix
        if config_key == "carbon" and "generation_mix" in df.columns:
            # Try to convert string representation of dict to actual dict
            try:
                df['gen_mix_dict'] = df['generation_mix'].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else 
                    (json.loads(x) if isinstance(x, str) else x)
                )
            except Exception as e:
                st.warning(f"Could not parse generation mix data: {e}")
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

# --- Plotting Functions ---
def create_demand_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a line chart for demand data."""
    fig = go.Figure()
    if not df.empty and "peak_demand" in df.columns and "day" in df.columns:
        # Aggregate by day to get daily peak
        daily_peak = df.groupby("day")["peak_demand"].max().reset_index()
        fig.add_trace(go.Scatter(x=daily_peak["day"], y=daily_peak["peak_demand"], 
                                mode="lines+markers", name="Peak Demand", 
                                line=dict(color='blue', width=2)))
    fig.update_layout(
        title="Daily Peak Demand",
        xaxis_title="Date", 
        yaxis_title="Demand (MW)",
        template="plotly_white"
    )
    return fig

def create_demand_vs_temperature_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a scatter plot of demand vs temperature."""
    fig = go.Figure()
    try:
        if not df.empty and "peak_demand" in df.columns and "temperature_forecast" in df.columns:
            # Use index as color scale - simple but effective
            df = df.reset_index()  # Ensure we have a numeric index
            
            fig.add_trace(go.Scatter(
                x=df["temperature_forecast"], 
                y=df["peak_demand"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=df.index,  # Use numeric index for coloring
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Data Point")
                ),
                name="Demand vs Temperature"
            ))
        fig.update_layout(
            title="Demand vs Temperature Relationship",
            xaxis_title="Temperature (°C)", 
            yaxis_title="Demand (MW)",
            template="plotly_white"
        )
    except Exception as e:
        st.warning(f"Error creating demand vs temperature chart: {e}")
        fig.update_layout(
            title="Demand vs Temperature Relationship (Error)",
            annotations=[dict(
                text=f"Error creating chart: {str(e)}",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
    return fig

def create_generation_mix_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a pie chart for generation mix."""
    fig = go.Figure()
    if not df.empty and "fuel_type" in df.columns and "generation" in df.columns:
        # Aggregate by fuel type
        agg = df.groupby("fuel_type")["generation"].sum().reset_index()
        fig.add_trace(go.Pie(
            labels=agg["fuel_type"], 
            values=agg["generation"], 
            hole=0.3,
            marker=dict(colors=px.colors.qualitative.Safe)
        ))
    fig.update_layout(
        title="Generation Mix by Source",
        template="plotly_white"
    )
    return fig

def create_wind_farms_comparison(df: pd.DataFrame) -> go.Figure:
    """Creates a bar chart comparing wind farm output."""
    fig = go.Figure()
    if not df.empty and "wind_farm_name" in df.columns and "forecast_output_mw" in df.columns:
        # Aggregate by wind farm
        agg = df.groupby("wind_farm_name")[["forecast_output_mw", "actual_output_mw"]].mean().reset_index()
        
        fig.add_trace(go.Bar(
            x=agg["wind_farm_name"],
            y=agg["forecast_output_mw"],
            name="Forecast Output",
            marker_color='royalblue'
        ))
        
        fig.add_trace(go.Bar(
            x=agg["wind_farm_name"],
            y=agg["actual_output_mw"],
            name="Actual Output",
            marker_color='darkblue'
        ))
    
    fig.update_layout(
        title="Wind Farm Output Comparison",
        xaxis_title="Wind Farm",
        yaxis_title="Average Output (MW)",
        barmode='group',
        template="plotly_white"
    )
    return fig

def create_balancing_costs_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a stacked area chart for balancing costs."""
    fig = go.Figure()
    try:
        if not df.empty:
            # First, check which columns actually exist in the dataframe
            available_columns = []
            expected_columns = ['balancing_services_cost', 'transmission_losses_cost', 'constraint_costs']
            
            # Find which columns exist
            for col in expected_columns:
                if col in df.columns:
                    available_columns.append(col)
            
            # If none of the expected columns exist, try to use what we have
            if not available_columns and 'cost_pounds' in df.columns:
                df['total_cost'] = df['cost_pounds']
                available_columns = ['total_cost']
            
            # If we still have no usable columns, return empty figure with message
            if not available_columns:
                fig.update_layout(
                    title="Balancing Costs (No Data)",
                    annotations=[dict(
                        text="No cost data available in the dataset",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )]
                )
                return fig
            
            # Ensure we have a date column for grouping
            if 'settlement_date' in df.columns:
                df['day'] = pd.to_datetime(df['settlement_date'])
            elif 'charge_date' in df.columns:
                df['day'] = pd.to_datetime(df['charge_date'])
            else:
                # If no date column, create one from index
                df['day'] = pd.to_datetime('2023-01-01') + pd.to_timedelta(df.index, unit='D')
            
            # Aggregate by day using only the columns that exist
            agg_dict = {col: 'sum' for col in available_columns}
            daily = df.groupby('day').agg(agg_dict).reset_index()
            
            # Create a trace for each available column
            colors = ['rgb(66, 135, 245)', 'rgb(253, 127, 111)', 'rgb(126, 172, 109)', 'rgb(190, 148, 210)']
            
            for i, col in enumerate(available_columns):
                color = colors[i % len(colors)]  # Cycle through colors if we have more columns than colors
                
                fig.add_trace(go.Scatter(
                    x=daily['day'], 
                    y=daily[col],
                    mode='lines',
                    line=dict(width=0.5, color=color),
                    stackgroup='one',
                    name=col.replace('_', ' ').title()  # Format the column name for display
                ))
        
        fig.update_layout(
            title="Daily Balancing Costs Breakdown",
            xaxis_title="Date",
            yaxis_title="Cost (£)",
            template="plotly_white"
        )
    except Exception as e:
        st.warning(f"Error creating balancing costs chart: {e}")
        fig.update_layout(
            title="Balancing Costs (Error)",
            annotations=[dict(
                text=f"Error creating chart: {str(e)}",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
    return fig

def create_carbon_intensity_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a line chart for carbon intensity by region."""
    fig = go.Figure()
    if not df.empty and "carbon_intensity_gco2_kwh" in df.columns and "region" in df.columns:
        # Ensure measurement_date and measurement_time are proper datetime
        try:
            # Try to create a datetime column
            if "measurement_date" in df.columns and "measurement_time" in df.columns:
                df["measurement_date"] = pd.to_datetime(df["measurement_date"]).dt.date
                df["datetime"] = pd.to_datetime(
                    df["measurement_date"].astype(str) + " " + 
                    df["measurement_time"].astype(str)
                )
            else:
                # If those columns aren't available, create a dummy datetime from index
                df["datetime"] = pd.to_datetime(df.index)
        except Exception as e:
            st.warning(f"Error processing datetime in carbon intensity data: {e}")
            df["datetime"] = pd.to_datetime(df.index)
        
        # Create a plot for each region
        for region in df['region'].unique():
            region_data = df[df['region'] == region]
            # Group by date and calculate average intensity
            if "datetime" in region_data.columns:
                daily_avg = region_data.groupby(region_data['datetime'].dt.date)['carbon_intensity_gco2_kwh'].mean().reset_index()
                daily_avg["datetime"] = pd.to_datetime(daily_avg["datetime"])
                
                fig.add_trace(go.Scatter(
                    x=daily_avg['datetime'], 
                    y=daily_avg['carbon_intensity_gco2_kwh'],
                    mode='lines',
                    name=region
                ))
    
    fig.update_layout(
        title="Carbon Intensity by Region",
        xaxis_title="Date",
        yaxis_title="Carbon Intensity (gCO₂/kWh)",
        template="plotly_white"
    )
    return fig

def create_carbon_generation_mix(df: pd.DataFrame) -> go.Figure:
    """Creates a pie chart showing the generation mix from the carbon intensity data."""
    fig = go.Figure()
    
    try:
        if not df.empty and "generation_mix" in df.columns:
            # Extract just the most recent data point for national data
            national_data = df[df['region'] == 'National'].sort_values('measurement_date', ascending=False)
            
            if not national_data.empty:
                latest_data = national_data.iloc[0]
                
                # Try to parse the generation mix string into a dictionary
                gen_mix = None
                
                if "gen_mix_dict" in df.columns and isinstance(latest_data.get('gen_mix_dict'), dict):
                    gen_mix = latest_data['gen_mix_dict']
                elif isinstance(latest_data['generation_mix'], str):
                    try:
                        # Try different parsing methods
                        try:
                            gen_mix = ast.literal_eval(latest_data['generation_mix'])
                        except:
                            # Try json parsing
                            gen_mix = json.loads(latest_data['generation_mix'].replace("'", "\""))
                    except:
                        st.warning("Could not parse generation mix data.")
                
                if gen_mix and isinstance(gen_mix, dict):
                    fig.add_trace(go.Pie(
                        labels=list(gen_mix.keys()),
                        values=list(gen_mix.values()),
                        hole=0.3,
                        marker=dict(colors=px.colors.qualitative.Bold)
                    ))
    except Exception as e:
        st.warning(f"Error creating generation mix chart: {e}")
    
    fig.update_layout(
        title="Current Generation Mix",
        template="plotly_white"
    )
    return fig

def create_interconnector_flows_chart(df: pd.DataFrame) -> go.Figure:
    """Creates a bar chart showing interconnector flows."""
    fig = go.Figure()
    
    try:
        if not df.empty and "flow_mw" in df.columns:
            # Check if interconnector_name is present, otherwise try to use interconnector_id
            name_col = "interconnector_name" if "interconnector_name" in df.columns else "interconnector_id"
            
            if name_col not in df.columns:
                # If neither name nor id available, return empty chart
                return fig
            
            # Aggregate by interconnector
            agg = df.groupby(name_col)["flow_mw"].mean().reset_index()
            
            if not agg.empty:
                # Sort by absolute flow value
                agg = agg.sort_values(by="flow_mw", key=abs, ascending=False)
                
                # Create color list based on flow direction
                colors = ['green' if flow >= 0 else 'red' for flow in agg['flow_mw']]
                
                # Create text labels
                text_labels = agg["flow_mw"].round(0).astype(int).astype(str) + " MW"
                
                fig.add_trace(go.Bar(
                    x=agg[name_col],
                    y=agg["flow_mw"],
                    marker_color=colors,
                    text=text_labels,
                    textposition="auto"
                ))
                
                # Add a zero line
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    y0=0,
                    x1=len(agg)-0.5,
                    y1=0,
                    line=dict(color="black", width=1, dash="dash")
                )
    except Exception as e:
        st.warning(f"Error creating interconnector flows chart: {e}")
    
    fig.update_layout(
        title="Average Interconnector Flows (+ Export, - Import)",
        xaxis_title="Interconnector",
        yaxis_title="Flow (MW)",
        template="plotly_white"
    )
    return fig

def create_system_warnings_timeline(df: pd.DataFrame) -> go.Figure:
    """Creates a timeline of system warnings."""
    fig = go.Figure()
    
    try:
        if not df.empty and "warning_date" in df.columns and "warning_type" in df.columns:
            # Convert to datetime if not already
            for col in ['start_time', 'end_time']:
                if col in df.columns:
                    if not pd.api.types.is_datetime64_dtype(df[col]):
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except:
                            # If conversion fails, create dummy values
                            if col == 'start_time':
                                df[col] = pd.to_datetime(df['warning_date'])
                            elif col == 'end_time':
                                df[col] = pd.to_datetime(df['warning_date']) + pd.Timedelta(hours=2)
            
            # Define colors for warning types
            warning_colors = {
                "Capacity Warning": "orange",
                "Demand Control": "red",
                "System Stress": "purple",
                "Interconnector Issue": "blue",
                "Generation Shortfall": "brown"
            }
            
            # Make sure warning_types is a list (for y-axis)
            warning_types = df['warning_type'].unique().tolist()
            
            for idx, row in df.iterrows():
                color = warning_colors.get(row['warning_type'], 'gray')
                
                # Hover text
                hover_text = f"ID: {row.get('warning_id', 'Unknown')}<br>" + \
                            f"Type: {row['warning_type']}<br>"
                
                if 'severity' in row:
                    hover_text += f"Severity: {row['severity']}<br>"
                    
                if 'affected_area' in row:
                    hover_text += f"Area: {row['affected_area']}<br>"
                    
                if 'status' in row:
                    hover_text += f"Status: {row['status']}"
                
                if 'impact_mw' in row and pd.notna(row['impact_mw']):
                    hover_text += f"<br>Impact: {row['impact_mw']:.0f} MW"
                
                # Add event as a rectangular shape
                fig.add_trace(go.Scatter(
                    x=[row['start_time'], row['end_time']],
                    y=[row['warning_type'], row['warning_type']],
                    mode='lines',
                    line=dict(color=color, width=10),
                    name=str(row.get('warning_id', f"Warning {idx}")),
                    text=hover_text,
                    hoverinfo='text',
                    showlegend=False
                ))
        
        fig.update_layout(
            title="System Warnings Timeline",
            xaxis_title="Date/Time",
            yaxis_title="Warning Type",
            template="plotly_white",
            height=400,
            yaxis=dict(
                categoryorder='array',
                categoryarray=sorted(df['warning_type'].unique().tolist()) if not df.empty else []
            )
        )
    except Exception as e:
        st.warning(f"Error creating system warnings timeline: {e}")
        # Create an empty figure with a message
        fig.update_layout(
            title="System Warnings Timeline (Error)",
            annotations=[dict(
                text=f"Error creating chart: {str(e)}",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5
            )]
        )
    
    return fig

# --- UI ---
st.set_page_config(page_title="UK Energy Dashboard", layout="wide")
st.title("🇬🇧 UK Energy Market Dashboard")
st.markdown("An interactive dashboard to analyze UK electricity data from various sources.")

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

# Default to the last 14 days of available data
default_start = max_d - timedelta(days=14)
start_date = st.sidebar.date_input("Start Date", value=default_start, min_value=min_d, max_value=max_d)
end_date = st.sidebar.date_input("End Date", value=max_d, min_value=start_date, max_value=max_d)

if st.sidebar.button("Clear Cache & Rerun"):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

if start_date > end_date:
    st.warning("Start date cannot be after end date.")
    st.stop()

# Create tabs for different analysis areas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Demand Analysis", 
    "Generation Analysis", 
    "Balancing Analysis",
    "Carbon Intensity",
    "System Status"
])

with tab1:
    st.header("Demand Analysis")
    
    # Demand forecast
    st.subheader("National Demand Forecast")
    with st.spinner(f"Fetching demand data for {start_date} → {end_date}..."):
        demand_df = fetch_data(client, "demand", start_date, end_date)
    
    if demand_df.empty:
        st.info("No demand data available for the selected period.")
    else:
        demand_chart = create_demand_chart(demand_df)
        st.plotly_chart(demand_chart, use_container_width=True)
    
    # Demand vs Temperature
    st.subheader("Demand vs Temperature Relationship")
    if not demand_df.empty and "temperature_forecast" in demand_df.columns:
        temp_chart = create_demand_vs_temperature_chart(demand_df)
        st.plotly_chart(temp_chart, use_container_width=True)
    else:
        st.info("Temperature data not available for this period.")

with tab2:
    st.header("Generation Analysis")
    
    # Wind generation
    st.subheader("Wind Generation")
    with st.spinner(f"Fetching wind generation data for {start_date} → {end_date}..."):
        generation_df = fetch_data(client, "generation", start_date, end_date)
    
    if generation_df.empty:
        st.info("No wind generation data available for the selected period.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            # Wind farm comparison
            wind_chart = create_wind_farms_comparison(generation_df)
            st.plotly_chart(wind_chart, use_container_width=True)
        
        with col2:
            # Generation mix
            mix_chart = create_generation_mix_chart(generation_df)
            st.plotly_chart(mix_chart, use_container_width=True)

with tab3:
    st.header("Balancing Analysis")
    
    # Balancing services
    st.subheader("Balancing Services Costs")
    with st.spinner(f"Fetching balancing services data for {start_date} → {end_date}..."):
        balancing_df = fetch_data(client, "balancing", start_date, end_date)
    
    if balancing_df.empty:
        st.info("No balancing services data available for the selected period.")
    else:
        balancing_chart = create_balancing_costs_chart(balancing_df)
        st.plotly_chart(balancing_chart, use_container_width=True)
        
        # Show the raw data in an expandable section
        with st.expander("View Balancing Services Data"):
            st.dataframe(balancing_df.head(10))

with tab4:
    st.header("Carbon Intensity Analysis")
    
    # Carbon intensity
    st.subheader("Carbon Intensity by Region")
    with st.spinner(f"Fetching carbon intensity data for {start_date} → {end_date}..."):
        carbon_df = fetch_data(client, "carbon", start_date, end_date)
    
    if carbon_df.empty:
        st.info("No carbon intensity data available for the selected period.")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            carbon_chart = create_carbon_intensity_chart(carbon_df)
            st.plotly_chart(carbon_chart, use_container_width=True)
        
        with col2:
            mix_chart = create_carbon_generation_mix(carbon_df)
            st.plotly_chart(mix_chart, use_container_width=True)

with tab5:
    st.header("System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Interconnector flows
        st.subheader("Interconnector Flows")
        with st.spinner(f"Fetching interconnector data for {start_date} → {end_date}..."):
            interconnector_df = fetch_data(client, "interconnectors", start_date, end_date)
        
        if interconnector_df.empty:
            st.info("No interconnector data available for the selected period.")
        else:
            interconnector_chart = create_interconnector_flows_chart(interconnector_df)
            st.plotly_chart(interconnector_chart, use_container_width=True)
    
    with col2:
        # System warnings
        st.subheader("System Warnings")
        with st.spinner(f"Fetching system warnings for {start_date} → {end_date}..."):
            warnings_df = fetch_data(client, "warnings", start_date, end_date)
        
        if warnings_df.empty:
            st.info("No system warnings issued for the selected period.")
        else:
            warnings_chart = create_system_warnings_timeline(warnings_df)
            st.plotly_chart(warnings_chart, use_container_width=True)

st.sidebar.info("Data sourced from National Grid ESO tables in BigQuery (europe-west2 region).")
