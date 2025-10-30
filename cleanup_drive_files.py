#!/usr/bin/env python3
"""
Clean up old files from Google Drive to free up space
"""

import os
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_credentials():
    """Authenticate using service account"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        print("✅ Successfully authenticated with Google APIs using service account")
        return credentials
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return None


def delete_old_files():
    """Delete files older than 2 days"""
    credentials = get_credentials()
    if not credentials:
        return

    service = build("drive", "v3", credentials=credentials)

    # Get all files
    results = (
        service.files()
        .list(
            pageSize=100, fields="nextPageToken, files(id, name, createdTime, mimeType)"
        )
        .execute()
    )

    files = results.get("files", [])

    # Calculate cutoff date (2 days ago)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=2)

    # Delete old files
    deleted_count = 0
    for file in files:
        created_time = datetime.fromisoformat(
            file["createdTime"].replace("Z", "+00:00")
        )
        if created_time < cutoff_date:
            try:
                service.files().delete(fileId=file["id"]).execute()
                print(f"🗑️  Deleted: {file['name']}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {file['name']}: {e}")

    print(f"\n✨ Cleanup complete! Deleted {deleted_count} files")


if __name__ == "__main__":
    delete_old_files()
