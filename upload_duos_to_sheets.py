#!/usr/bin/env python3
"""
Google Sheets DUoS Data Uploader - Uses service account
This script uploads the DUoS Excel data to Google Sheets
"""

import os
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
INPUT_FILE = "duos_outputs2/DNO_DUoS_All_Data_Consolidated_Complete.xlsx"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SPREADSHEET_NAME = f"DNO_DUoS_All_Data_Consolidated_{TIMESTAMP}"


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


def create_spreadsheet(service, file_name):
    """Upload Excel file and convert to Google Sheets"""
    try:
        print(f"📤 Uploading {file_name} to Google Drive and converting to Sheets...")

        media = MediaFileUpload(
            INPUT_FILE,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            resumable=True,
        )

        file_metadata = {
            "name": file_name,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )

        print("✅ File uploaded and converted successfully")
        print(f"📊 Spreadsheet URL: {file.get('webViewLink')}")
        return file.get("id"), file.get("webViewLink")

    except HttpError as e:
        print(f"❌ Upload failed: {e}")
        return None, None


def main():
    """Main function to handle the upload process"""
    print("🚀 Starting DUoS data upload to Google Sheets")

    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Input file not found: {INPUT_FILE}")
        return

    # Get credentials
    credentials = get_credentials()
    if not credentials:
        return

    # Create Drive API service
    drive_service = build("drive", "v3", credentials=credentials)

    # Upload and convert file
    file_id, web_link = create_spreadsheet(drive_service, SPREADSHEET_NAME)

    if file_id and web_link:
        print("\n✨ Upload complete!")
        print("You can now access the spreadsheet at:")
        print(web_link)
    else:
        print("❌ Upload failed")


if __name__ == "__main__":
    main()
