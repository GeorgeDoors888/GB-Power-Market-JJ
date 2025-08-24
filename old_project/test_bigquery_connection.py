import streamlit as st
from google.cloud import bigquery
import pandas as pd
from datetime import date, datetime

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"

st.set_page_config(
    page_title="BigQuery Connection Test",
    page_icon="🔍",
    layout="wide"
)

st.title("BigQuery Connection Test")
st.write("This simple app tests the connection to BigQuery and displays available tables.")

@st.cache_resource
def get_bq_client():
    """Initializes and returns a BigQuery client, caching the resource."""
    try:
        st.info("Initializing BigQuery client...")
        client = bigquery.Client(project=PROJECT_ID)
        st.success("BigQuery client initialized successfully")
        return client
    except Exception as e:
        st.error(f"Failed to connect to BigQuery: {e}")
        return None

def get_table_name(table_name):
    """Returns the fully qualified BigQuery table name."""
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

def main():
    st.write("Testing BigQuery connection...")
    
    # Initialize BigQuery client
    try:
        client = get_bq_client()
        if not client:
            st.error("Failed to initialize BigQuery connection.")
            st.stop()
    except Exception as e:
        st.error(f"Error connecting to BigQuery: {str(e)}")
        st.stop()
    
    # List available datasets
    try:
        st.subheader("Available Datasets")
        datasets = list(client.list_datasets())
        
        if datasets:
            dataset_names = [ds.dataset_id for ds in datasets]
            st.write(f"Found {len(datasets)} datasets: {', '.join(dataset_names)}")
            
            # Allow user to select a dataset
            selected_dataset = st.selectbox("Select a dataset to view tables:", dataset_names)
            
            # List tables in selected dataset
            st.subheader(f"Tables in {selected_dataset}")
            tables = list(client.list_tables(selected_dataset))
            
            if tables:
                table_names = [table.table_id for table in tables]
                st.write(f"Found {len(tables)} tables")
                
                # Display table list
                for table_name in table_names:
                    st.write(f"- {table_name}")
                
                # Allow user to select a table for preview
                if st.button("Preview a small sample of data"):
                    sample_table = tables[0].table_id
                    st.subheader(f"Sample data from {sample_table}")
                    
                    query = f"""
                    SELECT * 
                    FROM `{selected_dataset}.{sample_table}`
                    LIMIT 10
                    """
                    
                    try:
                        st.code(query, language="sql")
                        results = client.query(query).result().to_dataframe()
                        st.dataframe(results)
                        st.success("Query executed successfully")
                    except Exception as e:
                        st.error(f"Error executing query: {e}")
            else:
                st.info(f"No tables found in dataset {selected_dataset}")
        else:
            st.warning("No datasets found in project")
    except Exception as e:
        st.error(f"Error listing datasets: {e}")
    
    # Show connection info
    st.sidebar.subheader("Connection Info")
    st.sidebar.info(f"""
    **Project ID**: {PROJECT_ID}
    **Test Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

if __name__ == "__main__":
    main()
