import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from plotly.subplots import make_subplots


def get_bigquery_data(query):
    """Execute BigQuery query and return pandas DataFrame"""
    client = bigquery.Client(project="jibber-jabber-knowledge")
    return client.query(query).to_dataframe()


def create_dashboard():
    print("Creating Energy Dashboard...")
    print("1. Fetching data from BigQuery...")

    # Create subplot figure
    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Grid Frequency (Last Hour)",
            "Generation Mix (Last 24h)",
            "System Prices (Last 7 Days)",
            "Interconnector Flows",
            "Demand (Last 7 Days)",
            "Wind Generation (Last 24h)",
        ),
        specs=[
            [{"secondary_y": True}, {"secondary_y": True}],
            [{"secondary_y": True}, {"secondary_y": True}],
            [{"secondary_y": True}, {"secondary_y": True}],
        ],
    )

    try:
        # 1. Grid Frequency
        print("2. Creating frequency plot...")
        freq_query = """
        SELECT time, frequency
        FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
        WHERE time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        ORDER BY time ASC
        """
        freq_df = get_bigquery_data(freq_query)
        fig.add_trace(
            go.Scatter(
                x=freq_df["time"],
                y=freq_df["frequency"],
                name="Grid Frequency",
                line=dict(color="blue"),
            ),
            row=1,
            col=1,
        )
        fig.add_hline(y=50.0, line_dash="dash", line_color="green", row=1, col=1)

        # Continue with other plots...
        print("3. Creating generation mix plot...")
        # Add generation mix plot code

        print("4. Creating system prices plot...")
        # Add system prices plot code

        print("5. Creating interconnector flows plot...")
        # Add interconnector flows plot code

        print("6. Creating demand plot...")
        # Add demand plot code

        print("7. Creating wind generation plot...")
        # Add wind generation plot code

        # Update layout
        fig.update_layout(
            height=1200,
            width=1600,
            title_text="GB Electricity System Dashboard",
            showlegend=True,
            template="plotly_white",
        )

        # Save dashboard
        output_path = os.path.join(os.getcwd(), "energy_dashboard.html")
        fig.write_html(output_path)
        print(f"\nDashboard created successfully: {output_path}")

    except Exception as e:
        print(f"Error creating dashboard: {e}")


if __name__ == "__main__":
    create_dashboard()
