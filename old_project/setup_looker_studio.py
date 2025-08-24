"""
Lists all BigQuery views in the specified dataset that are ready for Looker Studio.

This script connects to Google BigQuery, iterates through the tables in the
uk_energy dataset, and prints a list of all the views (identified by the 'v_' prefix).
This provides a clear checklist for manually adding data sources in Looker Studio.
"""
from google.cloud import bigquery
from google.api_core import exceptions

# --- Configuration ---
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy"

def list_analytics_views(project_id, dataset_id):
    """
    Lists all views in a BigQuery dataset intended for analytics.

    Args:
        project_id (str): The Google Cloud project ID.
        dataset_id (str): The BigQuery dataset ID.

    Returns:
        list: A list of view IDs, or None if an error occurs.
    """
    try:
        client = bigquery.Client(project=project_id)
        dataset_ref = client.dataset(dataset_id)
        tables = list(client.list_tables(dataset_ref))

        print(f"Found {len(tables)} tables/views in dataset '{project_id}.{dataset_id}'.")
        
        view_ids = [
            table.table_id
            for table in tables
            if table.table_id.startswith("v_")
        ]

        if not view_ids:
            print("No analytics views (starting with 'v_') found.")
            return None

        print("\n--- Looker Studio Data Sources to Add ---")
        for view_id in sorted(view_ids):
            print(f"- {view_id}")
        
        return sorted(view_ids)

    except exceptions.NotFound:
        print(f"Error: Dataset '{project_id}.{dataset_id}' not found.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

if __name__ == "__main__":
    list_analytics_views(PROJECT_ID, DATASET_ID)
