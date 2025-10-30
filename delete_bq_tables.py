import os

from google.cloud import bigquery
from google.oauth2 import service_account

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "elexon_data_landing_zone"
TABLES_TO_DELETE = [
    "bmrs_boalf",
    "bmrs_freq",
    "bmrs_fuelinst",
]


def delete_tables():
    """Deletes specified tables from a BigQuery dataset."""
    print(f"Authenticating with Google Cloud...")
    # Assumes GOOGLE_APPLICATION_CREDENTIALS is set in the environment
    client = bigquery.Client(project=PROJECT_ID)
    print(f"Authenticated successfully.")

    for table_name in TABLES_TO_DELETE:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        try:
            print(f"Attempting to delete table: {table_id}...")
            client.delete_table(table_id, not_found_ok=True)
            print(f"✅ Successfully deleted table: {table_id}")
        except Exception as e:
            print(f"❌ Error deleting table {table_id}: {e}")


if __name__ == "__main__":
    delete_tables()
