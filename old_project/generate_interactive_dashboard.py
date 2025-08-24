"""
Generates an interactive HTML dashboard using Plotly to visualize UK energy data.

This script connects to a BigQuery project, queries pre-built analytics views,
and creates a series of interactive charts which are then compiled into a single,
standalone HTML file.
"""
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from google.api_core import exceptions

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy"
OUTPUT_HTML_FILE = "interactive_dashboard.html"

def get_data_from_view(client, view_name, date_limit="2025-07-31"):
    """
    Queries a BigQuery view and returns the result as a pandas DataFrame.

    Args:
        client (bigquery.Client): An authenticated BigQuery client.
        view_name (str): The name of the view to query.
        date_limit (str, optional): The end date for the data query. Defaults to "2025-07-31".

    Returns:
        pd.DataFrame: A DataFrame containing the query results, or None on error.
    """
    print(f"Querying view: {view_name}...")
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{view_name}`
        WHERE date <= '{date_limit}'
        ORDER BY timestamp_utc
    """
    try:
        df = client.query(query).to_dataframe()
        print(f"Successfully fetched {len(df)} rows.")
        return df
    except exceptions.NotFound:
        print(f"Error: View '{view_name}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while querying {view_name}: {e}")
        return None

def create_demand_profile_chart(df):
    """Creates a line chart for the national demand profile."""
    if df is None or df.empty:
        return None
    
    print("Creating demand profile chart...")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['timestamp_utc'],
        y=df['national_demand_mw'],
        mode='lines',
        name='National Demand',
        line=dict(color='royalblue', width=2)
    ))
    fig.update_layout(
        title_text='UK National Demand Profile (July 2025)',
        xaxis_title='Date / Time',
        yaxis_title='Demand (MW)',
        template='plotly_white'
    )
    return fig

def main():
    """Main function to generate and save the dashboard."""
    try:
        client = bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        print(f"Failed to create BigQuery client. Please check authentication. Error: {e}")
        return

    # --- Generate Charts ---
    demand_df = get_data_from_view(client, "v_demand_outturn_sp")
    demand_chart = create_demand_profile_chart(demand_df)

    # --- Assemble Dashboard ---
    print("Assembling dashboard...")
    with open(OUTPUT_HTML_FILE, 'w') as f:
        f.write("<html><head><title>UK Energy Analytics Dashboard</title></head><body>")
        f.write("<h1>UK Energy Analytics Dashboard</h1>")
        
        if demand_chart:
            f.write("<h2>National Demand Profile</h2>")
            f.write(demand_chart.to_html(full_html=False, include_plotlyjs='cdn'))
        else:
            f.write("<p>Could not generate demand profile chart.</p>")

        # (Future charts will be added here)

        f.write("</body></html>")
    
    print(f"\nDashboard successfully generated: {OUTPUT_HTML_FILE}")
    print("You can now open this file in your web browser.")

if __name__ == "__main__":
    main()
