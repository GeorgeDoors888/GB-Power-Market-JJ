
import os
from google.cloud import storage
from datetime import datetime

# --- Configuration ---
BUCKET_NAME = "jibber-jabber-knowledge-bmrs-data"
PREFIX = "elexon/"
SERVICE_ACCOUNT_KEY_FILE = "jibber_jabber_key.json"
# -------------------

def list_gcs_files(bucket_name, prefix, credentials_path):
    """Lists files in a GCS bucket with details."""
    try:
        storage_client = storage.Client.from_service_account_json(credentials_path)
        bucket = storage_client.bucket(bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)

        print(f"--- Files in gs://{bucket_name}/{prefix} ---")
        count = 0
        total_size_bytes = 0

        for blob in blobs:
            count += 1
            total_size_bytes += blob.size
            updated_time = blob.updated.strftime('%Y-%m-%d %H:%M:%S')
            # Convert size to human-readable format
            if blob.size < 1024:
                size_str = f"{blob.size} B"
            elif blob.size < 1024**2:
                size_str = f"{blob.size/1024:.2f} KB"
            else:
                size_str = f"{blob.size/1024**2:.2f} MB"

            print(f"- {blob.name:<80} | Size: {size_str:<10} | Last Modified: {updated_time}")

        print("-" * 40)
        total_size_mb = total_size_bytes / (1024 * 1024)
        print(f"Found {count} files.")
        print(f"Total size: {total_size_mb:.2f} MB")
        print("--- End of list ---")

    except FileNotFoundError:
        print(f"ERROR: Service account key file not found at '{credentials_path}'")
        print("Please ensure the key file is in the correct location.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Ensure the script is run from the root of the workspace
    if not os.path.exists(SERVICE_ACCOUNT_KEY_FILE):
         print(f"Error: Cannot find '{SERVICE_ACCOUNT_KEY_FILE}'.")
         print(f"Please run this script from the root directory of the workspace: '/workspaces/jibber-jabber 24 august 2025 big bop'")
    else:
        list_gcs_files(BUCKET_NAME, PREFIX, SERVICE_ACCOUNT_KEY_FILE)
