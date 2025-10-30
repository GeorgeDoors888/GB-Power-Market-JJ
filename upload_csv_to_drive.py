#!/usr/bin/env python3
"""
Upload CSV Files to Google Drive
-------------------------------
Uploads all CSV files from the duos_outputs2/gsheets_csv directory to Google Drive
using the service account credentials.
"""

import os
import sys
import time

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def upload_csv_files(folder_id=None):
    """Upload all CSV files to Google Drive."""
    print("\n🚀 UPLOADING CSV FILES TO GOOGLE DRIVE")
    print("===================================")

    # Set up credentials
    credentials_file = "jibber_jaber_key.json"
    csv_dir = "duos_outputs2/gsheets_csv"

    if not os.path.exists(credentials_file):
        print(f"❌ Error: Service account key file '{credentials_file}' not found.")
        return None

    if not os.path.exists(csv_dir):
        print(f"❌ Error: CSV directory '{csv_dir}' not found.")
        return None

    try:
        # Create credentials from service account
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Build the Drive API service
        drive_service = build("drive", "v3", credentials=credentials)

        # Create main folder if not provided
        if not folder_id:
            folder_metadata = {
                "name": f"DNO_DUoS_CSV_Files_{int(time.time())}",
                "mimeType": "application/vnd.google-apps.folder",
            }

            folder = (
                drive_service.files()
                .create(body=folder_metadata, fields="id, name, webViewLink")
                .execute()
            )

            folder_id = folder.get("id")
            folder_name = folder.get("name")
            folder_link = folder.get("webViewLink")

            print(f"✅ Created folder: {folder_name}")
            print(f"🔗 Folder URL: {folder_link}")
        else:
            try:
                folder = drive_service.files().get(fileId=folder_id).execute()
                folder_name = folder.get("name")
                print(f"✅ Using existing folder: {folder_name}")
                print(
                    f"🔗 Folder URL: https://drive.google.com/drive/folders/{folder_id}"
                )
            except Exception as e:
                print(f"❌ Error: Folder not found. {str(e)}")
                return None

        # Create subfolders for by_dno and by_year
        by_dno_folder_id = create_subfolder(drive_service, "by_dno", folder_id)
        by_year_folder_id = create_subfolder(drive_service, "by_year", folder_id)

        # Upload main CSV files
        main_files = [
            f
            for f in os.listdir(csv_dir)
            if f.endswith(".csv") and os.path.isfile(os.path.join(csv_dir, f))
        ]
        for file_name in main_files:
            file_path = os.path.join(csv_dir, file_name)
            upload_file(drive_service, file_path, folder_id)

        # Upload by_dno files
        by_dno_dir = os.path.join(csv_dir, "by_dno")
        if os.path.exists(by_dno_dir):
            dno_files = [f for f in os.listdir(by_dno_dir) if f.endswith(".csv")]
            for file_name in dno_files:
                file_path = os.path.join(by_dno_dir, file_name)
                upload_file(drive_service, file_path, by_dno_folder_id)

        # Upload by_year files
        by_year_dir = os.path.join(csv_dir, "by_year")
        if os.path.exists(by_year_dir):
            year_files = [f for f in os.listdir(by_year_dir) if f.endswith(".csv")]
            for file_name in year_files:
                file_path = os.path.join(by_year_dir, file_name)
                upload_file(drive_service, file_path, by_year_folder_id)

        print("\n✅ All CSV files uploaded successfully!")
        return folder_id

    except Exception as e:
        print(f"❌ Error uploading files: {str(e)}")
        return None


def create_subfolder(drive_service, folder_name, parent_id):
    """Create a subfolder in Google Drive."""
    print(f"\n📁 Creating subfolder: {folder_name}")

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }

    folder = (
        drive_service.files().create(body=folder_metadata, fields="id, name").execute()
    )

    folder_id = folder.get("id")
    print(f"  ✅ Created subfolder: {folder.get('name')} (ID: {folder_id})")
    return folder_id


def upload_file(drive_service, file_path, parent_id):
    """Upload a file to Google Drive."""
    file_name = os.path.basename(file_path)
    print(f"📤 Uploading: {file_name}")

    file_metadata = {"name": file_name, "parents": [parent_id]}

    # Set proper MIME type for CSV
    media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)

    try:
        file = (
            drive_service.files()
            .create(
                body=file_metadata, media_body=media, fields="id, name, webViewLink"
            )
            .execute()
        )

        print(f"  ✅ Uploaded: {file.get('name')} (ID: {file.get('id')})")
        return file.get("id")
    except Exception as e:
        print(f"  ❌ Error uploading {file_name}: {str(e)}")
        return None


def share_folder_with_email(drive_service, folder_id, email, role="writer"):
    """Share a Google Drive folder with a specific email address."""
    print(f"\n🔄 Sharing folder with {email}...")

    user_permission = {"type": "user", "role": role, "emailAddress": email}

    try:
        drive_service.permissions().create(
            fileId=folder_id,
            body=user_permission,
            fields="id",
            sendNotificationEmail=True,
        ).execute()

        print(f"✅ Successfully shared folder with {email}")
        return True
    except Exception as e:
        print(f"❌ Error sharing folder: {str(e)}")
        return False


def main():
    """Main function to upload CSV files and share the folder."""
    # Upload CSV files to Google Drive
    folder_id = upload_csv_files()

    if not folder_id:
        print("❌ Failed to upload CSV files to Google Drive.")
        return

    # Ask user for email to share the folder with
    print("\n📧 SHARE FOLDER ACCESS")
    print(
        "Please enter YOUR personal Google account email (NOT the service account email)"
    )
    print("This should be the email you use to login to Google Drive/Gmail/etc.")
    email = input("Enter your personal Google account email: ").strip()

    # Check if email is the service account
    if "gserviceaccount.com" in email:
        print(
            "⚠️ You entered a service account email. You should enter your personal Google email instead."
        )
        correction = input(
            "Enter your personal Google account email (or press Enter to continue anyway): "
        ).strip()
        if correction:
            email = correction

    if email and "@" in email:
        # Create credentials from service account
        credentials = service_account.Credentials.from_service_account_file(
            "jibber_jaber_key.json", scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Build the Drive API service
        drive_service = build("drive", "v3", credentials=credentials)

        # Share the folder
        share_folder_with_email(drive_service, folder_id, email)

    print("\n📋 NEXT STEPS:")
    print("1. Check your email for a notification about shared access")
    print("2. Visit https://drive.google.com and look in 'Shared with me'")
    print(f"3. Open the folder: https://drive.google.com/drive/folders/{folder_id}")
    print("4. You can view the CSV files directly in Google Drive")


if __name__ == "__main__":
    main()
