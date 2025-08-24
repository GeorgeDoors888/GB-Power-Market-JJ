from google.cloud import bigquery
import pandas as pd

# Initialize the BigQuery client
client = bigquery.Client(project="jibber-jabber-knowledge")

# Define the query to get column names
query = """
SELECT * 
FROM `jibber-jabber-knowledge.uk_energy_prod.neso_balancing_services` 
LIMIT 5
"""

# Run the query and convert to dataframe
try:
    df = client.query(query).to_dataframe()
    
    # Print column names and a sample row
    print("Columns in the balancing table:")
    print(df.columns.tolist())
    
    print("\nSample data (first row):")
    if not df.empty:
        print(df.iloc[0].to_dict())
    else:
        print("No data found in table")
        
except Exception as e:
    print(f"Error querying table: {e}")
