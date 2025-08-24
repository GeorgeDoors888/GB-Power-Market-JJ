import os
import pandas as pd
from google.cloud import storage

# CONFIG
BUCKET_NAME = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
ENDPOINTS_CSV = 'endpoints.csv'

# 1. Load all dataset types from endpoints.csv
def get_all_dataset_types():
    df = pd.read_csv(ENDPOINTS_CSV)
    # Only unique endpoint IDs (dataset types)
    return sorted(df['id'].unique())

# 2. List all top-level dataset folders in the GCS bucket
def get_gcs_dataset_folders():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    # List blobs with delimiter to get top-level folders
    iterator = bucket.list_blobs(delimiter='/')
    folders = set()
    for page in iterator.pages:
        folders.update(page.prefixes)
    # Remove trailing slashes
    return sorted(f.rstrip('/') for f in folders)

# 3. Compare and report missing datasets
def main():
    all_datasets = get_all_dataset_types()
    gcs_folders = get_gcs_dataset_folders()
    # Map GCS folder names to dataset IDs (if naming matches)
    missing = [ds for ds in all_datasets if ds not in gcs_folders]
    print('Datasets in endpoints.csv:', all_datasets)
    print('Folders in GCS bucket:', gcs_folders)
    print('Missing datasets in GCS bucket:', missing)
    # Optionally: download/upload missing datasets here

if __name__ == '__main__':
    main()
