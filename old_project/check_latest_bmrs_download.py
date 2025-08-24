import os
from google.cloud import storage
import json
from datetime import datetime

BUCKET_NAME = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
PREFIX = 'bmrs_data_all/'
MAX_FILES = 100

def get_latest_download_timestamp():
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = list(bucket.list_blobs(prefix=PREFIX))
    latest_ts = None
    latest_file = None
    for blob in sorted(blobs, key=lambda b: b.updated, reverse=True)[:MAX_FILES]:
        try:
            data = json.loads(blob.download_as_text())
            ts = data.get('download_timestamp')
            if ts and (latest_ts is None or ts > latest_ts):
                latest_ts = ts
                latest_file = blob.name
        except Exception:
            continue
    if latest_ts:
        print(f"Latest BMRS download: {latest_ts} (file: {latest_file})")
    else:
        print("No download_timestamp found in recent files.")

if __name__ == "__main__":
    get_latest_download_timestamp()
