import streamlit as st
import pandas as pd
import numpy as np
from google.cloud import bigquery
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import time

# Page configuration
st.set_page_config(
    page_title="UK Energy Dashboard (BigQuery Only)",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Project configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"

# Sidebar title
st.sidebar.title("UK Energy Dashboard")
st.sidebar.info("This version uses **only** BigQuery tables and does NOT access any GCS data.")

# Initialize BigQuery client
@st.cache_resource
def get_bigquery_client():
    return bigquery.Client(project=PROJECT_ID)

# Cache data retrieval to improve performance
@st.cache_data(ttl=3600)
def get_table_data(table_name, date_column=None, start_date=None, end_date=None, max_rows=10000):
    """Fetch data from a BigQuery table with optional date filtering"""
    client = get_bigquery_client()
    
    if date_column and start_date and end_date:
        query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        WHERE {date_column} BETWEEN '{start_date}' AND '{end_date}'
        LIMIT {max_rows}
        """
    else:
        query = f"""
        SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
        LIMIT {max_rows}
        """
    
    try:
        start_time = time.time()
        df = client.query(query).to_dataframe()
        query_time = time.time() - start_time
        return df, query_time
    except Exception as e:
        st.error(f"Error querying table {table_name}: {e}")
        return pd.DataFrame(), 0

# Get available tables
@st.cache_data(ttl=3600)
def get_available_tables():
    client = get_bigquery_client()
    try:
        tables = list(client.list_tables(DATASET_ID))
        return [table.table_id for table in tables]
    except Exception as e:
        st.error(f"Error listing tables: {e}")
        return []

# Get min and max dates from a table
@st.cache_data(ttl=3600)
def get_date_range(table_name, date_column):
    client = get_bigquery_client()
    query = f"""
    SELECT MIN({date_column}) as min_date, MAX({date_column}) as max_date
    FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
    """
    try:
        result = client.query(query).to_dataframe()
        if not result.empty:
            return result['min_date'].iloc[0], result['max_date'].iloc[0]
    except Exception as e:
        st.warning(f"Could not determine date range for {table_name}: {e}")
    return None, None

# Main application
def main():
    st.title("UK Energy Dashboard (BigQuery Only)")
    
    # Get available tables
    available_tables = get_available_tables()
    
    if not available_tables:
        st.error("No tables found in the dataset or error connecting to BigQuery")
        return
    
    # Table selection in sidebar
    st.sidebar.subheader("Data Selection")
    selected_table = st.sidebar.selectbox("Select Table", available_tables)
    
    # Load table schema to find date columns
    client = get_bigquery_client()
    try:
        table_ref = client.get_table(f"{PROJECT_ID}.{DATASET_ID}.{selected_table}")
        date_columns = [field.name for field in table_ref.schema 
                        if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP')]
    except Exception as e:
        st.error(f"Error getting schema for {selected_table}: {e}")
        date_columns = []
    
    # Date column selection
    date_column = None
    if date_columns:
        date_column = st.sidebar.selectbox(
            "Select Date Column", 
            date_columns,
            index=0 if 'settlement_date' in date_columns else None
        )
    
    # Date range selection if date column is available
    start_date, end_date = None, None
    if date_column:
        min_date, max_date = get_date_range(selected_table, date_column)
        
        if min_date and max_date:
            st.sidebar.subheader("Date Range")
            
            # Default to last 30 days
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
    
    # Query size limit
    max_rows = st.sidebar.slider("Max Rows to Load", 100, 50000, 10000)
    
    # Load the data
    with st.spinner(f"Loading data from {selected_table}..."):
        df, query_time = get_table_data(selected_table, date_column, start_date, end_date, max_rows)
    
    # Display data info
    st.subheader(f"Data from {selected_table}")
    st.info(f"Loaded {len(df):,} rows in {query_time:.2f} seconds")
    
    if df.empty:
        st.warning("No data found for the selected criteria")
        return
    
    # Data summary
    st.subheader("Data Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Number of Rows", f"{len(df):,}")
    
    with col2:
        date_range_text = f"{start_date} to {end_date}" if start_date and end_date else "All dates"
        st.metric("Date Range", date_range_text)
    
    with col3:
        st.metric("Number of Columns", f"{len(df.columns):,}")
    
    # Detect numeric columns for visualization
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    
    # Visualization section
    if numeric_columns and date_column and date_column in df.columns:
        st.subheader("Data Visualization")
        
        # Column selection for visualization
        selected_y_column = st.selectbox("Select Value Column for Chart", numeric_columns)
        
        # Create time series plot
        fig = px.line(
            df, 
            x=date_column, 
            y=selected_y_column,
            title=f"{selected_y_column} over time"
        )
        
        fig.update_layout(
            xaxis_title=date_column,
            yaxis_title=selected_y_column,
            height=500,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Data table (paginated)
    st.subheader("Data Table")
    st.dataframe(df, use_container_width=True)
    
    # Download option
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name=f"{selected_table}.csv",
        mime="text/csv",
    )

if __name__ == "__main__":
    main()
