import os

from dotenv import load_dotenv
from google.cloud import bigquery

# Load environment variables from .env file
load_dotenv()


def verify_bigquery_table(project_id, dataset_id, table_id, num_rows=5):
    """
    Connects to BigQuery, prints the table schema (headers), and displays a specified number of rows.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.
        table_id (str): The BigQuery table ID.
        num_rows (int): The number of rows to preview.
    """
    try:
        # Ensure credentials are set
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            print("Error: GOOGLE_APPLICATION_CREDENTIALS environment variable not set.")
            print("Please ensure your .env file is configured correctly.")
            return

        # Initialize BigQuery client
        client = bigquery.Client(project=project_id)
        table_ref = client.dataset(dataset_id).table(table_id)

        # Get table object
        table = client.get_table(table_ref)

        # --- 1. Print Headers (Schema) ---
        print(f"--- Headers for table {project_id}.{dataset_id}.{table_id} ---")
        for schema_field in table.schema:
            print(f"- {schema_field.name} ({schema_field.field_type})")

        # --- 2. Print Data Preview ---
        print(f"\n--- Previewing first {num_rows} rows ---")
        rows = client.list_rows(table, max_results=num_rows)

        # Convert rows to a more readable format (list of dictionaries)
        row_list = [dict(row) for row in rows]

        if not row_list:
            print("Table is empty or no rows were fetched.")
            return

        # Print data
        for i, row_data in enumerate(row_list):
            print(f"\n[Row {i+1}]")
            for key, value in row_data.items():
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # Configuration from the logs
    PROJECT = "jibber-jabber-knowledge"
    DATASET = "uk_energy_insights"
    TABLE = "bmrs_bod"

    print(f"Verifying data for: {PROJECT}.{DATASET}.{TABLE}")
    verify_bigquery_table(PROJECT, DATASET, TABLE)
