#!/usr/bin/env python3
"""
Google Drive CSV Uploader - Uses service account with Drive scopes
This script converts Excel data to CSV files and uploads them to Google Drive
"""

import json
import os
from datetime import datetime

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
INPUT_FILE = "duos_outputs2/DNO_DUoS_Complete_Data_20250914_193447.xlsx"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
FOLDER_NAME = f"jibber-jabber-knowledge-CSV-{TIMESTAMP}"
OUTPUT_DIR = "csv_output"


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


def create_drive_folder(service, folder_name):
    """Create a folder in Google Drive"""
    try:
        folder_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        folder = (
            service.files()
            .create(body=folder_metadata, fields="id, webViewLink")
            .execute()
        )
        folder_id = folder.get("id")
        folder_url = folder.get("webViewLink")

        print(f"📁 Created folder: {folder_name}")
        print(f"   URL: {folder_url}")

        return folder_id, folder_url
    except HttpError as e:
        print(f"❌ Error creating folder: {e}")
        return None, None


def read_excel_data():
    """Read data from Excel file with multiple sheets"""
    try:
        # Read all sheets from the Excel file
        excel_data = pd.read_excel(INPUT_FILE, sheet_name=None)
        print(f"📖 Successfully read data from {INPUT_FILE}")
        print(f"   Found {len(excel_data)} sheets: {', '.join(excel_data.keys())}")
        return excel_data
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return None


def ensure_output_dir():
    """Ensure output directory exists"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📂 Created local output directory: {OUTPUT_DIR}")


def convert_to_csv(excel_data):
    """Convert Excel sheets to CSV files"""
    ensure_output_dir()
    csv_files = []

    for sheet_name, df in excel_data.items():
        # Clean sheet name for filename
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in sheet_name)
        file_path = os.path.join(OUTPUT_DIR, f"{clean_name}.csv")

        # Save to CSV
        df.to_csv(file_path, index=False)
        csv_files.append((sheet_name, file_path))
        print(f"✅ Converted sheet '{sheet_name}' to CSV: {file_path}")

    return csv_files


def upload_file_to_drive(service, file_path, file_name, folder_id):
    """Upload a file to Google Drive"""
    try:
        file_metadata = {"name": file_name, "parents": [folder_id]}

        media = MediaFileUpload(file_path, resumable=True)

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )

        file_id = file.get("id")
        file_url = file.get("webViewLink")

        print(f"✅ Uploaded file: {file_name}")
        print(f"   URL: {file_url}")

        return file_id, file_url
    except HttpError as e:
        print(f"❌ Error uploading file '{file_name}': {e}")
        return None, None


def convert_to_google_sheets(service, file_id, file_name):
    """Convert a CSV file to Google Sheets format"""
    try:
        # Copy the file to convert it to Google Sheets
        sheet_metadata = {
            "name": f"{file_name.replace('.csv', '')} - Sheet",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        sheet = (
            service.files()
            .copy(fileId=file_id, body=sheet_metadata, fields="id, webViewLink")
            .execute()
        )

        sheet_id = sheet.get("id")
        sheet_url = sheet.get("webViewLink")

        print(f"📊 Converted to Google Sheets: {file_name}")
        print(f"   URL: {sheet_url}")

        return sheet_id, sheet_url
    except HttpError as e:
        print(f"❌ Error converting to Google Sheets: {e}")
        return None, None


def share_folder(service, folder_id, email):
    """Share the folder with a specific email"""
    try:
        permission = {"type": "user", "role": "writer", "emailAddress": email}

        service.permissions().create(
            fileId=folder_id, body=permission, fields="id"
        ).execute()

        print(f"✅ Folder shared with {email}")
        return True
    except Exception as e:
        print(f"❌ Error sharing folder: {e}")
        return False


def main():
    """Main function to convert Excel to CSV and upload to Google Drive"""
    print("\n🚀 CONVERTING DNO DUOS DATA TO CSV AND UPLOADING TO GOOGLE DRIVE")
    print("=============================================================")

    # Get credentials
    credentials = get_credentials()
    if not credentials:
        print("❌ Failed to authenticate. Exiting.")
        return

    # Create Drive API service
    drive_service = build("drive", "v3", credentials=credentials)

    # Create new folder in Google Drive
    folder_id, folder_url = create_drive_folder(drive_service, FOLDER_NAME)
    if not folder_id:
        print("❌ Failed to create folder in Google Drive. Exiting.")
        return

    # Read Excel data
    excel_data = read_excel_data()
    if not excel_data:
        print("❌ Failed to read Excel data. Exiting.")
        return

    # Convert Excel sheets to CSV files
    csv_files = convert_to_csv(excel_data)
    if not csv_files:
        print("❌ Failed to convert Excel to CSV. Exiting.")
        return

    # Upload CSV files to Google Drive
    all_files = []
    for sheet_name, file_path in csv_files:
        file_name = os.path.basename(file_path)
        file_id, file_url = upload_file_to_drive(
            drive_service, file_path, file_name, folder_id
        )
        if file_id:
            all_files.append((file_id, file_name))

    # Convert CSV files to Google Sheets (if possible)
    print("\n📊 ATTEMPTING TO CONVERT CSV FILES TO GOOGLE SHEETS")
    for file_id, file_name in all_files:
        sheet_id, sheet_url = convert_to_google_sheets(
            drive_service, file_id, file_name
        )

    # Share the folder with the user (optional)
    user_email = input(
        "Enter your email to share the folder (or press Enter to skip): "
    ).strip()
    if user_email:
        share_folder(drive_service, folder_id, user_email)

    print("\n✨ PROCESS COMPLETED")
    print(f"📁 Your files are available in Google Drive at: {folder_url}")
    print(f"💾 Local CSV files were saved to the '{OUTPUT_DIR}' directory")


if __name__ == "__main__":
    main()
