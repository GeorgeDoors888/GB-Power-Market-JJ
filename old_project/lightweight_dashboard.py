import streamlit as st
import pandas as pd
from google.cloud import bigquery
import time

# Configure the page
st.set_page_config(
    page_title="UK Energy Data Summary",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("UK Energy Data Summary (Lightweight Version)")
st.markdown("This is a lightweight version of the dashboard that only shows basic data summaries.")

# Project information
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"

# Show loading spinner
with st.spinner("Connecting to BigQuery..."):
    try:
        # Create BigQuery client
        client = bigquery.Client(project=PROJECT_ID)
        st.success("✅ Connected to BigQuery successfully!")
    except Exception as e:
        st.error(f"❌ Failed to connect to BigQuery: {e}")
        st.stop()

# Function to run a query with timeout
@st.cache_data(ttl=3600)
def run_query_with_timeout(query, timeout_seconds=30):
    """Run a query with a timeout to prevent hanging"""
    start_time = time.time()
    
    try:
        # Set a small limit on results
        if "LIMIT" not in query.upper():
            query += " LIMIT 100"
            
        job = client.query(query)
        
        # Poll for completion with timeout
        while not job.done():
            if time.time() - start_time > timeout_seconds:
                st.warning(f"Query taking too long (>{timeout_seconds}s). Showing partial results.")
                return None
            time.sleep(0.5)
            
        return job.result().to_dataframe()
    except Exception as e:
        st.error(f"Query error: {e}")
        return None

# Show table information
st.header("Available Tables")

with st.spinner("Loading table information..."):
    try:
        # List tables in the dataset
        tables = list(client.list_tables(DATASET_ID))
        
        if not tables:
            st.warning(f"No tables found in dataset {DATASET_ID}")
        else:
            # Display table information
            table_info = []
            for table in tables:
                table_ref = client.get_table(f"{DATASET_ID}.{table.table_id}")
                table_info.append({
                    "Table Name": table.table_id,
                    "Rows": f"{table_ref.num_rows:,}",
                    "Size": f"{table_ref.num_bytes / (1024**2):.2f} MB"
                })
            
            st.dataframe(pd.DataFrame(table_info), use_container_width=True)
    except Exception as e:
        st.error(f"Error listing tables: {e}")

# Show a preview of selected table
st.header("Table Preview")

# Table selector
table_options = ["Select a table"] + [table.table_id for table in tables] if 'tables' in locals() else ["No tables available"]
selected_table = st.selectbox("Choose a table to preview:", table_options)

if selected_table and selected_table != "Select a table" and selected_table != "No tables available":
    with st.spinner(f"Loading preview of {selected_table}..."):
        # Count rows in table with a timeout
        count_query = f"""
        SELECT COUNT(*) as row_count 
        FROM `{PROJECT_ID}.{DATASET_ID}.{selected_table}`
        """
        
        count_df = run_query_with_timeout(count_query)
        if count_df is not None:
            total_rows = count_df.iloc[0]['row_count']
            st.info(f"Total rows in table: {total_rows:,}")
        
        # Get a preview of the data
        preview_query = f"""
        SELECT * 
        FROM `{PROJECT_ID}.{DATASET_ID}.{selected_table}`
        ORDER BY 1
        LIMIT 10
        """
        
        preview_df = run_query_with_timeout(preview_query)
        if preview_df is not None and not preview_df.empty:
            st.dataframe(preview_df, use_container_width=True)
        else:
            st.warning("No data available to preview or query timed out.")

# Show database summary
st.header("Database Summary")

with st.spinner("Generating database summary..."):
    try:
        # Get summary of table sizes
        summary_query = f"""
        SELECT 
          table_name,
          row_count,
          ROUND(size_bytes/POW(1024,2),2) as size_mb
        FROM 
          `{PROJECT_ID}.{DATASET_ID}.INFORMATION_SCHEMA.TABLES`
        ORDER BY 
          size_bytes DESC
        """
        
        summary_df = run_query_with_timeout(summary_query)
        if summary_df is not None and not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)
            
            # Calculate total size
            total_size_mb = summary_df['size_mb'].sum()
            st.info(f"Total size of all tables: {total_size_mb:.2f} MB")
        else:
            st.warning("Could not generate database summary.")
    except Exception as e:
        st.error(f"Error generating summary: {e}")

# About section
with st.expander("About this lightweight dashboard"):
    st.markdown("""
    This is a simplified version of the UK Energy Dashboard that:
    
    1. Only shows basic table information and previews
    2. Uses strict query timeouts to prevent hanging
    3. Limits all queries to a small number of rows
    4. Does not attempt to create any visualizations
    
    The full dashboard is attempting to process over 1TB of data from GCS, which is causing it to hang.
    This lightweight version only accesses the smaller BigQuery tables directly.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
