#!/usr/bin/env python3
"""
Task 9: Streamlit Event Explorer - Interactive 4-Lane Timeline Visualization

Purpose: Visual exploration of wind farm events with synchronized timeline lanes
- Lane 1: Generation (actual vs expected, capacity factor)
- Lane 2: On-site weather (wind speed, temperature, gusts)
- Lane 3: Event flags (CALM, STORM, TURBULENCE, ICING, CURTAILMENT)
- Lane 4: Alerts/Anomalies (threshold violations, rapid changes)

Features:
- Farm selector dropdown
- Date range picker
- Interactive Plotly charts with zoom/pan
- Event highlighting across all lanes
- Export filtered data to CSV

Usage:
    streamlit run streamlit_event_explorer.py

Requirements:
    pip install streamlit plotly pandas google-cloud-bigquery
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Page config
st.set_page_config(
    page_title="Wind Farm Event Explorer",
    page_icon="🌬️",
    layout="wide"
)

@st.cache_resource
def get_bigquery_client():
    """Initialize BigQuery client (cached)."""
    return bigquery.Client(project=PROJECT_ID, location="US")

@st.cache_data(ttl=3600)
def get_farm_list():
    """Get list of farms with event data."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT farm_name
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_unified_features`
    WHERE has_any_event = TRUE
    ORDER BY farm_name
    """
    df = client.query(query).to_dataframe()
    return df['farm_name'].tolist()

@st.cache_data(ttl=600)
def get_farm_data(farm_name, start_date, end_date):
    """
    Fetch unified features data for selected farm and date range.
    """
    client = get_bigquery_client()
    
    query = f"""
    SELECT
        hour,
        -- Generation
        actual_mw,
        expected_mw,
        capacity_mw,
        capacity_factor_pct,
        cf_deviation_pct,
        lost_mw,
        revenue_loss_estimate_gbp,
        -- Weather
        temperature_2m_c,
        wind_speed_100m_ms,
        wind_gusts_10m_ms,
        gust_factor,
        wind_direction_100m_deg,
        surface_pressure_hpa,
        relative_humidity_2m_pct,
        -- Event flags
        is_calm_event,
        is_storm_event,
        is_turbulence_event,
        is_icing_event,
        is_curtailment_event,
        has_any_event,
        -- Derived categories
        wind_regime,
        performance_category,
        -- Icing risk
        icing_risk_level,
        dew_point_spread_c
    FROM `{PROJECT_ID}.{DATASET}.wind_unified_features`
    WHERE farm_name = @farm_name
      AND DATE(hour) BETWEEN @start_date AND @end_date
    ORDER BY hour
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("farm_name", "STRING", farm_name),
            bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
            bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        ]
    )
    
    df = client.query(query, job_config=job_config).to_dataframe()
    return df

def create_4lane_timeline(df, farm_name):
    """
    Create interactive 4-lane timeline visualization.
    """
    
    # Create subplots with 4 rows
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            "Lane 1: Generation (MW & Capacity Factor)",
            "Lane 2: On-Site Weather",
            "Lane 3: Event Flags",
            "Lane 4: Performance Category"
        ),
        row_heights=[0.25, 0.25, 0.25, 0.25]
    )
    
    # LANE 1: GENERATION
    if 'actual_mw' in df.columns and df['actual_mw'].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df['hour'], y=df['actual_mw'],
                name='Actual MW',
                line=dict(color='blue', width=2),
                hovertemplate='<b>Actual:</b> %{y:.1f} MW<br><extra></extra>'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df['hour'], y=df['expected_mw'],
                name='Expected MW',
                line=dict(color='lightblue', width=1, dash='dash'),
                hovertemplate='<b>Expected:</b> %{y:.1f} MW<br><extra></extra>'
            ),
            row=1, col=1
        )
        
        # Capacity factor on secondary y-axis
        fig.add_trace(
            go.Scatter(
                x=df['hour'], y=df['capacity_factor_pct'],
                name='Capacity Factor %',
                line=dict(color='orange', width=1),
                yaxis='y2',
                hovertemplate='<b>CF:</b> %{y:.1f}%<br><extra></extra>'
            ),
            row=1, col=1
        )
    
    # LANE 2: WEATHER
    fig.add_trace(
        go.Scatter(
            x=df['hour'], y=df['wind_speed_100m_ms'],
            name='Wind Speed (m/s)',
            line=dict(color='green', width=2),
            hovertemplate='<b>Wind:</b> %{y:.1f} m/s<br><extra></extra>'
        ),
        row=2, col=1
    )
    
    if 'wind_gusts_10m_ms' in df.columns and df['wind_gusts_10m_ms'].notna().any():
        fig.add_trace(
            go.Scatter(
                x=df['hour'], y=df['wind_gusts_10m_ms'],
                name='Gusts (m/s)',
                line=dict(color='lightgreen', width=1, dash='dot'),
                hovertemplate='<b>Gusts:</b> %{y:.1f} m/s<br><extra></extra>'
            ),
            row=2, col=1
        )
    
    fig.add_trace(
        go.Scatter(
            x=df['hour'], y=df['temperature_2m_c'],
            name='Temperature (°C)',
            line=dict(color='red', width=1),
            yaxis='y4',
            hovertemplate='<b>Temp:</b> %{y:.1f}°C<br><extra></extra>'
        ),
        row=2, col=1
    )
    
    # LANE 3: EVENT FLAGS (as colored bands)
    event_types = [
        ('is_calm_event', 'CALM', 'blue', 5),
        ('is_storm_event', 'STORM', 'red', 4),
        ('is_turbulence_event', 'TURBULENCE', 'orange', 3),
        ('is_icing_event', 'ICING', 'cyan', 2),
        ('is_curtailment_event', 'CURTAILMENT', 'purple', 1),
    ]
    
    for col, name, color, y_level in event_types:
        if col in df.columns:
            event_hours = df[df[col] == 1]['hour']
            if len(event_hours) > 0:
                fig.add_trace(
                    go.Scatter(
                        x=event_hours,
                        y=[y_level] * len(event_hours),
                        mode='markers',
                        name=name,
                        marker=dict(color=color, size=8, symbol='square'),
                        hovertemplate=f'<b>{name} Event</b><br>%{{x}}<extra></extra>'
                    ),
                    row=3, col=1
                )
    
    # LANE 4: PERFORMANCE CATEGORY (color-coded bars)
    if 'performance_category' in df.columns:
        perf_colors = {
            'SEVERE_UNDERPERFORMANCE': 'darkred',
            'HIGH_UNDERPERFORMANCE': 'red',
            'MODERATE_UNDERPERFORMANCE': 'orange',
            'SLIGHT_UNDERPERFORMANCE': 'yellow',
            'NORMAL': 'lightgray',
            'OVERPERFORMANCE': 'green'
        }
        
        for category, color in perf_colors.items():
            category_data = df[df['performance_category'] == category]
            if len(category_data) > 0:
                fig.add_trace(
                    go.Bar(
                        x=category_data['hour'],
                        y=[1] * len(category_data),
                        name=category,
                        marker_color=color,
                        hovertemplate=f'<b>{category}</b><br>CF Dev: %{{customdata:.1f}}%<extra></extra>',
                        customdata=category_data['cf_deviation_pct']
                    ),
                    row=4, col=1
                )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title=f"Wind Farm Event Explorer: {farm_name}",
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Y-axis labels
    fig.update_yaxes(title_text="MW", row=1, col=1)
    fig.update_yaxes(title_text="m/s", row=2, col=1)
    fig.update_yaxes(title_text="Event Type", row=3, col=1, 
                     tickvals=[1, 2, 3, 4, 5],
                     ticktext=['CURTAILMENT', 'ICING', 'TURBULENCE', 'STORM', 'CALM'])
    fig.update_yaxes(title_text="Performance", row=4, col=1, showticklabels=False)
    
    # X-axis label
    fig.update_xaxes(title_text="Time", row=4, col=1)
    
    return fig

def main():
    """
    Main Streamlit app.
    """
    
    st.title("🌬️ Wind Farm Event Explorer")
    st.markdown("Interactive 4-lane timeline for event analysis")
    
    # Sidebar controls
    st.sidebar.header("🎛️ Controls")
    
    # Farm selector
    farms = get_farm_list()
    if len(farms) == 0:
        st.error("No farms with event data found!")
        return
    
    selected_farm = st.sidebar.selectbox(
        "Select Farm",
        farms,
        index=0
    )
    
    # Date range
    st.sidebar.subheader("📅 Date Range")
    
    # Default to last 30 days with events
    default_end = datetime.now().date()
    default_start = default_end - timedelta(days=30)
    
    start_date = st.sidebar.date_input(
        "Start Date",
        value=default_start,
        min_value=datetime(2020, 1, 1).date(),
        max_value=default_end
    )
    
    end_date = st.sidebar.date_input(
        "End Date",
        value=default_end,
        min_value=start_date,
        max_value=default_end
    )
    
    # Filters
    st.sidebar.subheader("🔍 Event Filters")
    show_calm = st.sidebar.checkbox("CALM Events", value=True)
    show_storm = st.sidebar.checkbox("STORM Events", value=True)
    show_turbulence = st.sidebar.checkbox("TURBULENCE Events", value=True)
    show_icing = st.sidebar.checkbox("ICING Events", value=True)
    show_curtailment = st.sidebar.checkbox("CURTAILMENT Events", value=True)
    
    # Load data
    if st.sidebar.button("🔄 Load Data"):
        with st.spinner(f"Loading data for {selected_farm}..."):
            df = get_farm_data(selected_farm, start_date, end_date)
            
            if len(df) == 0:
                st.warning(f"No data found for {selected_farm} between {start_date} and {end_date}")
                return
            
            # Store in session state
            st.session_state['df'] = df
            st.session_state['farm_name'] = selected_farm
    
    # Display data if available
    if 'df' in st.session_state:
        df = st.session_state['df']
        farm_name = st.session_state['farm_name']
        
        # Apply event filters
        filtered_df = df.copy()
        if not show_calm:
            filtered_df = filtered_df[filtered_df['is_calm_event'] != 1]
        if not show_storm:
            filtered_df = filtered_df[filtered_df['is_storm_event'] != 1]
        if not show_turbulence:
            filtered_df = filtered_df[filtered_df['is_turbulence_event'] != 1]
        if not show_icing:
            filtered_df = filtered_df[filtered_df['is_icing_event'] != 1]
        if not show_curtailment:
            filtered_df = filtered_df[filtered_df['is_curtailment_event'] != 1]
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Hours", len(filtered_df))
        
        with col2:
            event_hours = filtered_df['has_any_event'].sum()
            st.metric("Event Hours", event_hours)
        
        with col3:
            if 'capacity_factor_pct' in filtered_df.columns:
                avg_cf = filtered_df['capacity_factor_pct'].mean()
                st.metric("Avg Capacity Factor", f"{avg_cf:.1f}%")
            else:
                st.metric("Avg Capacity Factor", "N/A")
        
        with col4:
            if 'lost_mw' in filtered_df.columns:
                total_lost = filtered_df['lost_mw'].sum()
                st.metric("Total Lost Generation", f"{total_lost:.0f} MW")
            else:
                st.metric("Total Lost Generation", "N/A")
        
        # Event breakdown
        st.subheader("📊 Event Summary")
        event_cols = st.columns(5)
        
        event_counts = {
            'CALM': filtered_df['is_calm_event'].sum() if 'is_calm_event' in filtered_df.columns else 0,
            'STORM': filtered_df['is_storm_event'].sum() if 'is_storm_event' in filtered_df.columns else 0,
            'TURBULENCE': filtered_df['is_turbulence_event'].sum() if 'is_turbulence_event' in filtered_df.columns else 0,
            'ICING': filtered_df['is_icing_event'].sum() if 'is_icing_event' in filtered_df.columns else 0,
            'CURTAILMENT': filtered_df['is_curtailment_event'].sum() if 'is_curtailment_event' in filtered_df.columns else 0,
        }
        
        for col, (event_type, count) in zip(event_cols, event_counts.items()):
            with col:
                st.metric(event_type, int(count))
        
        # 4-lane timeline
        st.subheader("📈 4-Lane Timeline Visualization")
        fig = create_4lane_timeline(filtered_df, farm_name)
        st.plotly_chart(fig, use_container_width=True)
        
        # Data table
        st.subheader("📋 Raw Data")
        
        # Show only event hours by default
        show_all = st.checkbox("Show all hours (not just events)", value=False)
        
        if show_all:
            display_df = filtered_df
        else:
            display_df = filtered_df[filtered_df['has_any_event'] == 1]
        
        st.dataframe(
            display_df[[
                'hour', 'wind_speed_100m_ms', 'temperature_2m_c',
                'capacity_factor_pct', 'cf_deviation_pct',
                'is_calm_event', 'is_storm_event', 'is_turbulence_event',
                'wind_regime', 'performance_category'
            ]].style.format({
                'wind_speed_100m_ms': '{:.1f}',
                'temperature_2m_c': '{:.1f}',
                'capacity_factor_pct': '{:.1f}',
                'cf_deviation_pct': '{:.1f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Export button
        st.subheader("💾 Export Data")
        
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"{farm_name}_{start_date}_{end_date}_events.csv",
            mime="text/csv"
        )
    
    else:
        st.info("👈 Select a farm and date range, then click 'Load Data' to begin")

if __name__ == "__main__":
    main()
