#!/usr/bin/env python
"""
Script to list files in Google Drive for the service account
and optionally delete old files to free up space.
"""

import json
import os
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Constants
SCOPES = ["https://www.googleapis.com/auth/drive"]
CREDENTIAL_FILE = "jibber_jaber_key.json"


def get_service():
    """Authenticate and return the Google Drive service."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIAL_FILE, scopes=SCOPES
        )

        drive_service = build("drive", "v3", credentials=credentials)
        print("✅ Successfully authenticated with Google Drive API")
        return drive_service
    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return None


def list_files(drive_service, query=None, max_files=100):
    """List files in Google Drive with option to filter."""
    try:
        results = (
            drive_service.files()
            .list(
                q=query,
                pageSize=max_files,
                fields="nextPageToken, files(id, name, mimeType, createdTime, size, parents)",
            )
            .execute()
        )

        items = results.get("files", [])
        return items
    except Exception as e:
        print(f"❌ Error listing files: {str(e)}")
        return []


def delete_file(drive_service, file_id):
    """Delete a file from Google Drive."""
    try:
        drive_service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"❌ Error deleting file {file_id}: {str(e)}")
        return False


def print_files(files):
    """Print file information in a readable format."""
    if not files:
        print("No files found.")
        return

    print(f"\nFound {len(files)} files:")
    print("-" * 80)
    print(
        f"{'ID':<40} | {'Name':<30} | {'Type':<20} | {'Created':<20} | {'Size (MB)':<10}"
    )
    print("-" * 80)

    total_size = 0
    for file in files:
        file_id = file.get("id", "N/A")
        name = file.get("name", "N/A")
        mime_type = file.get("mimeType", "N/A").split("/")[-1]
        created = file.get("createdTime", "N/A")
        if created != "N/A":
            created = datetime.fromisoformat(created.replace("Z", "+00:00")).strftime(
                "%Y-%m-%d %H:%M"
            )

        size_mb = "N/A"
        if "size" in file:
            size_mb = f"{float(file['size']) / (1024 * 1024):.2f}"
            total_size += float(file["size"])

        print(
            f"{file_id:<40} | {name[:30]:<30} | {mime_type[:20]:<20} | {created:<20} | {size_mb:<10}"
        )

    print("-" * 80)
    print(f"Total size: {total_size / (1024 * 1024):.2f} MB")


def prompt_for_deletion(drive_service, files, days_old=7):
    """Prompt user to delete files older than specified days."""
    if not files:
        return

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    old_files = []

    for file in files:
        if "createdTime" in file:
            created = datetime.fromisoformat(file["createdTime"].replace("Z", "+00:00"))
            if created < cutoff_date:
                old_files.append(file)

    if not old_files:
        print(f"\nNo files found older than {days_old} days.")
        return

    print(f"\nFound {len(old_files)} files older than {days_old} days:")
    print_files(old_files)

    choice = input(
        "\nWould you like to delete these files to free up space? (y/n): "
    ).lower()
    if choice == "y":
        deleted_count = 0
        for file in old_files:
            if delete_file(drive_service, file["id"]):
                deleted_count += 1

        print(f"\n✅ Successfully deleted {deleted_count} of {len(old_files)} files.")
    else:
        print("\nNo files were deleted.")


def main():
    """Main function to list and manage Google Drive files."""
    print("🔍 LISTING GOOGLE DRIVE FILES")
    print("=" * 50)

    drive_service = get_service()
    if not drive_service:
        return

    # List all files (not in trash)
    query = "trashed = false"
    files = list_files(drive_service, query)

    print_files(files)

    # Prompt for deletion of old files
    prompt_for_deletion(drive_service, files)


if __name__ == "__main__":
    main()
