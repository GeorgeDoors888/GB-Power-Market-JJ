import os
from datetime import datetime, timedelta

import pandas as pd
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


def get_gcp_project_id():
    """Gets the GCP project ID from the environment."""
    project_id = os.environ.get("GCP_PROJECT")
    if not project_id:
        # Fallback for local development or different configuration
        try:
            from google.colab import auth

            auth.authenticate_user()
            import gspread
            from google.auth import default

            creds, project_id = default()
        except ImportError:
            # If not in Colab, try to get from gcloud config
            import subprocess

            try:
                project_id = (
                    subprocess.check_output(
                        ["gcloud", "config", "get-value", "project"],
                        stderr=subprocess.PIPE,
                    )
                    .strip()
                    .decode("utf-8")
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return "jibber-jabber-knowledge"  # Hardcoded fallback
    return project_id


def analyze_price_arbitrage(client, dataset_id, end_date_str):
    """
    Analyzes the bmrs_mid table for price arbitrage opportunities.
    """
    print("\\n--- Analyzing Price Arbitrage Opportunities (Last 7 Days) ---")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d")

    query = f"""
        SELECT
            settlementDate,
            -- Filter out zero prices which likely represent missing data or specific market conditions not suitable for simple arbitrage
            MIN(NULLIF(price, 0)) as min_price,
            MAX(price) as max_price,
            ROUND(MAX(price) - MIN(NULLIF(price, 0)), 2) as price_spread
        FROM
            `{client.project}.{dataset_id}.bmrs_mid`
        WHERE
            settlementDate BETWEEN '{start_date_str}' AND '{end_date_str}'
            AND dataProvider = 'APXMIDP' -- Focusing on a single provider for consistency
        GROUP BY
            settlementDate
        HAVING
            min_price IS NOT NULL AND max_price IS NOT NULL
        ORDER BY
            settlementDate DESC
    """
    try:
        df = client.query(query).to_dataframe()
        if df.empty:
            print("No data found for price arbitrage analysis in the last 7 days.")
            return
        print(
            "Daily Price Spreads (Potential revenue per MWh, buying low and selling high):"
        )
        print(df.to_string(index=False))
    except NotFound:
        print(f"Table `{client.project}.{dataset_id}.bmrs_mid` not found.")
    except Exception as e:
        print(f"An error occurred during price arbitrage analysis: {e}")


def analyze_ancillary_services(client, dataset_id, end_date_str):
    """
    Analyzes the bmrs_disbsad table for ancillary service opportunities.
    """
    print("\\n--- Analyzing Ancillary Services Market (Last 7 Days) ---")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d")

    query_daily_total = f"""
        SELECT
            settlementDate,
            ROUND(SUM(cost), 2) as total_daily_cost
        FROM
            `{client.project}.{dataset_id}.bmrs_disbsad`
        WHERE
            settlementDate BETWEEN '{start_date_str}' AND '{end_date_str}'
        GROUP BY
            settlementDate
        ORDER BY
            settlementDate DESC
    """

    query_top_players = f"""
        SELECT
            partyId,
            ROUND(SUM(cost), 2) as total_cost
        FROM
            `{client.project}.{dataset_id}.bmrs_disbsad`
        WHERE
            settlementDate BETWEEN '{start_date_str}' AND '{end_date_str}'
        GROUP BY
            partyId
        ORDER BY
            total_cost DESC
        LIMIT 5
    """
    try:
        df_daily = client.query(query_daily_total).to_dataframe()
        if not df_daily.empty:
            print("\\nTotal Daily Cost of Balancing Services:")
            print(df_daily.to_string(index=False))
        else:
            print("No data found for daily ancillary service costs in the last 7 days.")

        df_players = client.query(query_top_players).to_dataframe()
        if not df_players.empty:
            print("\\nTop 5 Players in Balancing Market (by total action cost):")
            print(df_players.to_string(index=False))
        else:
            print("No data found for top players in the ancillary service market.")

    except NotFound:
        print(f"Table `{client.project}.{dataset_id}.bmrs_disbsad` not found.")
    except Exception as e:
        print(f"An error occurred during ancillary services analysis: {e}")


def main():
    """Main function to run the analysis."""
    project_id = get_gcp_project_id()
    dataset_id = "uk_energy_insights"

    if not project_id:
        print("GCP_PROJECT environment variable not set.")
        return

    print(f"Using project: {project_id}, dataset: {dataset_id}")

    try:
        client = bigquery.Client(project=project_id)
    except Exception as e:
        print(f"Failed to create BigQuery client: {e}")
        print(
            "Please ensure you are authenticated with Google Cloud CLI ('gcloud auth application-default login')"
        )
        return

    # Use yesterday's date for a complete day's data
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    analysis_date_str = yesterday.strftime("%Y-%m-%d")

    print(f"Analyzing data up to {analysis_date_str}")

    analyze_price_arbitrage(client, dataset_id, analysis_date_str)
    analyze_ancillary_services(client, dataset_id, analysis_date_str)


if __name__ == "__main__":
    main()
