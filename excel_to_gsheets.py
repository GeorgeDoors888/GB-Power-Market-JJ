#!/usr/bin/env python3
"""
Excel to Google Sheets Converter
--------------------------------
Uploads an Excel file to Google Drive and converts it to Google Sheets format.

Requirements:
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import os
import pickle
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def authenticate_google_drive():
    """Authenticate with Google Drive API."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def upload_and_convert_to_sheets(service, file_path, output_name=None):
    """Upload an Excel file to Google Drive and convert it to Google Sheets."""
    file_name = os.path.basename(file_path)

    if output_name is None:
        output_name = file_name.replace(".xlsx", "")

    print(f"Uploading {file_name} to Google Drive...")

    # Upload file with conversion
    file_metadata = {
        "name": output_name,
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }

    media = MediaFileUpload(
        file_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        resumable=True,
    )

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,name,webViewLink")
        .execute()
    )

    print(f"File uploaded and converted to Google Sheets!")
    print(f"Name: {file.get('name')}")
    print(f"ID: {file.get('id')}")
    print(f"URL: {file.get('webViewLink')}")

    return file


def main():
    """Main function to handle the conversion."""
    if len(sys.argv) < 2:
        print("Usage: python excel_to_gsheets.py <excel_file_path> [output_name]")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)

    output_name = None
    if len(sys.argv) > 2:
        output_name = sys.argv[2]

    try:
        service = authenticate_google_drive()
        upload_and_convert_to_sheets(service, file_path, output_name)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
