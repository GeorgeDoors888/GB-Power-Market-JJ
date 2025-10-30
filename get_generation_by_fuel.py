import argparse
from datetime import datetime

import google.auth
import pandas as pd
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import bigquery


def get_generation_data(project_id, start_date, end_date):
    """
    Fetches and prints generation data by fuel type from BigQuery for a given period.

    Args:
        project_id (str): The Google Cloud project ID.
        start_date (str): The start date in YYYY-MM-DD format.
        end_date (str): The end date in YYYY-MM-DD format.
    """
    try:
        # Use application default credentials to connect to BigQuery
        client = bigquery.Client(project=project_id)
        print(f"Successfully connected to BigQuery project: {project_id}")
    except Exception as e:
        print(
            f"Error: Could not connect to BigQuery. Please check your authentication. Details: {e}"
        )
        return

    query = f"""
        SELECT
            settlementDate,
            fuelType,
            SUM(generation) as total_generation
        FROM
            `{project_id}.uk_energy_insights.bmrs_fuelinst`
        WHERE
            settlementDate BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY
            settlementDate,
            fuelType
        ORDER BY
            settlementDate,
            fuelType;
    """

    print("\nExecuting query...")
    print(query)

    try:
        query_job = client.query(query)
        results_df = query_job.to_dataframe()

        if results_df.empty:
            print("\nNo generation data found for the specified period.")
        else:
            # Set pandas display options to show all rows and columns
            pd.set_option("display.max_rows", None)
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", 1000)
            pd.set_option("display.colheader_justify", "center")
            pd.set_option("display.precision", 2)

            print("\n--- Generation Data by Fuel Type ---")
            print(results_df)
            print("------------------------------------")

    except GoogleAPICallError as e:
        print(
            f"\nError: An API error occurred while executing the BigQuery query. Details: {e}"
        )
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch and display generation data by fuel type from BigQuery."
    )
    parser.add_argument(
        "--start", required=True, help="Start date in YYYY-MM-DD format."
    )
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format.")
    parser.add_argument(
        "--project", default="jibber-jabber-knowledge", help="Google Cloud project ID."
    )

    args = parser.parse_args()

    get_generation_data(args.project, args.start, args.end)
