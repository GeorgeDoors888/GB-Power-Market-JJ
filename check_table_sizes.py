from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import os

# Set your project ID and dataset ID
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "elexon_insights_data"

# This script relies on the GOOGLE_APPLICATION_CREDENTIALS environment variable being set.
# You can set it in your terminal before running the script, for example:
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"

def get_or_create_dataset(client, dataset_id):
    """Checks if a dataset exists, creates it if it doesn't."""
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{dataset_id}' already exists.")
    except NotFound:
        print(f"Dataset '{dataset_id}' not found. Creating it now...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "EU"  # You can change this to your preferred location
        client.create_dataset(dataset)
        print(f"Dataset '{dataset_id}' created successfully.")
    return dataset_ref

def get_table_sizes(project_id, dataset_id):
    """Prints the size of all tables in a given dataset."""
    try:
        client = bigquery.Client(project=project_id)

        # Ensure the dataset exists before trying to list tables
        dataset_ref = get_or_create_dataset(client, dataset_id)

        tables = list(client.list_tables(dataset_ref))

        if not tables:
            print(f"\nNo tables found in dataset: {dataset_id}")
            print("This is likely because the ingestion script did not successfully load any data.")
            return

        print(f"\nTable sizes for dataset: {dataset_id}\n")
        total_size_bytes = 0

        for table in tables:
            table_ref = table.reference

            # Fetch the table details to get the num_bytes property
            table_info = client.get_table(table_ref)

            size_bytes = table_info.num_bytes if table_info.num_bytes is not None else 0
            total_size_bytes += size_bytes
            size_gb = size_bytes / (1024**3)  # Convert bytes to gigabytes

            print(f"Table: {table.table_id}")
            print(f"  Size (bytes): {size_bytes:,.0f}")
            print(f"  Size (GB): {size_gb:.4f}\n")

        total_size_gb = total_size_bytes / (1024**3)
        print("---------------------------------")
        print(f"Total size of all tables:")
        print(f"  Bytes: {total_size_bytes:,.0f}")
        print(f"  GB:    {total_size_gb:.4f}")
        print("---------------------------------")

    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function if the environment variable is set
if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
    get_table_sizes(PROJECT_ID, DATASET_ID)
else:
    print("Error: The GOOGLE_APPLICATION_CREDENTIALS environment variable is not set.")
    print("Please set it to the path of your service account key file before running.")

