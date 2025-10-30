#!/usr/bin/env python3
"""
Google Sheets API Uploader
-------------------------
Uploads DNO DUoS data to Google Sheets using the Google Sheets and Drive APIs.

Setup Instructions:
1. Install required packages:
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

2. Create a Google Cloud Project:
   a. Go to https://console.cloud.google.com/
   b. Create a new project
   c. Enable the Google Drive API and Google Sheets API
   d. Create OAuth 2.0 credentials (Desktop application)
   e. Download the credentials JSON file and save as 'credentials.json' in the same directory as this script

3. Run this script and follow the authentication prompts in your browser
"""

import os
import pickle
import sys

import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Define the scopes required for Drive and Sheets APIs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleSheetsUploader:
    def __init__(self, credentials_path="credentials.json"):
        """Initialize with the path to credentials.json file."""
        self.credentials_path = credentials_path
        self.drive_service = None
        self.sheets_service = None

    def authenticate(self):
        """Authenticate with Google APIs."""
        creds = None

        # The file token.pickle stores the user's access and refresh tokens
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(
                        f"❌ Error: Credentials file '{self.credentials_path}' not found."
                    )
                    print(
                        "   Please follow the setup instructions in the script header."
                    )
                    sys.exit(1)

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)

        # Create service objects
        self.drive_service = build("drive", "v3", credentials=creds)
        self.sheets_service = build("sheets", "v4", credentials=creds)

        print("✅ Successfully authenticated with Google APIs")

    def create_folder(self, folder_name, parent_id=None):
        """Create a folder in Google Drive."""
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }

        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = (
            self.drive_service.files()
            .create(body=file_metadata, fields="id, name, webViewLink")
            .execute()
        )

        print(f"📁 Created folder: {folder.get('name')}")
        print(f"   URL: {folder.get('webViewLink')}")

        return folder.get("id")

    def upload_csv_as_sheet(self, csv_path, folder_id=None):
        """Upload a CSV file and convert to Google Sheets."""
        file_name = os.path.basename(csv_path)
        sheets_name = file_name.replace(".csv", "")

        print(f"📤 Uploading: {file_name}")

        # Define file metadata
        file_metadata = {
            "name": sheets_name,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        if folder_id:
            file_metadata["parents"] = [folder_id]

        # Upload the file with conversion
        media = MediaFileUpload(csv_path, mimetype="text/csv", resumable=True)

        file = (
            self.drive_service.files()
            .create(
                body=file_metadata, media_body=media, fields="id, name, webViewLink"
            )
            .execute()
        )

        print(f"   ✅ Uploaded as Google Sheet: {file.get('name')}")
        print(f"   URL: {file.get('webViewLink')}")

        return file.get("id"), file.get("webViewLink")

    def format_sheet(self, sheet_id):
        """Apply basic formatting to a Google Sheet."""
        try:
            # Get sheet metadata
            sheet_metadata = (
                self.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            )

            # Get the first sheet
            sheet = sheet_metadata.get("sheets", [])[0]
            sheet_id_num = sheet.get("properties", {}).get("sheetId", 0)

            # Format the header row
            format_requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id_num,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.7,
                                    "green": 0.7,
                                    "blue": 0.7,
                                },
                                "textFormat": {"bold": True},
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)",
                    }
                },
                {
                    # Freeze the header row
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id_num,
                            "gridProperties": {"frozenRowCount": 1},
                        },
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
                {
                    # Auto-resize columns
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id_num,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 26,  # Up to column Z
                        }
                    }
                },
            ]

            # Apply the formatting
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body={"requests": format_requests}
            ).execute()

            print(f"   🎨 Applied formatting to sheet")

        except Exception as e:
            print(f"   ⚠️ Error formatting sheet: {str(e)}")

    def upload_duos_data(self, csv_dir):
        """Upload all DNO DUoS CSV data to Google Sheets."""
        print("\n🚀 UPLOADING DNO DUOS DATA TO GOOGLE SHEETS")
        print("=======================================")

        # Authenticate with Google APIs
        self.authenticate()

        # Create a main folder
        folder_name = (
            f"jibber-jabber-knowledge-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        )
        main_folder_id = self.create_folder(folder_name)

        # Track uploaded files
        uploaded_files = []

        # Upload main CSV files
        main_csv_files = [
            f
            for f in os.listdir(csv_dir)
            if f.endswith(".csv") and os.path.isfile(os.path.join(csv_dir, f))
        ]

        for file in main_csv_files:
            file_path = os.path.join(csv_dir, file)
            sheet_id, sheet_url = self.upload_csv_as_sheet(file_path, main_folder_id)
            self.format_sheet(sheet_id)
            uploaded_files.append((file, sheet_url))

        # Create and upload by_year files
        year_dir = os.path.join(csv_dir, "by_year")
        if os.path.exists(year_dir):
            year_folder_id = self.create_folder("By Year", main_folder_id)

            year_files = [
                f
                for f in os.listdir(year_dir)
                if f.endswith(".csv") and os.path.isfile(os.path.join(year_dir, f))
            ]

            for file in year_files:
                file_path = os.path.join(year_dir, file)
                sheet_id, sheet_url = self.upload_csv_as_sheet(
                    file_path, year_folder_id
                )
                self.format_sheet(sheet_id)
                uploaded_files.append((f"by_year/{file}", sheet_url))

        # Create and upload by_dno files
        dno_dir = os.path.join(csv_dir, "by_dno")
        if os.path.exists(dno_dir):
            dno_folder_id = self.create_folder("By DNO", main_folder_id)

            dno_files = [
                f
                for f in os.listdir(dno_dir)
                if f.endswith(".csv") and os.path.isfile(os.path.join(dno_dir, f))
            ]

            for file in dno_files:
                file_path = os.path.join(dno_dir, file)
                sheet_id, sheet_url = self.upload_csv_as_sheet(file_path, dno_folder_id)
                self.format_sheet(sheet_id)
                uploaded_files.append((f"by_dno/{file}", sheet_url))

        # Create an index spreadsheet
        self._create_index_sheet(main_folder_id, uploaded_files, folder_name)

        print("\n✅ All files uploaded successfully to Google Sheets!")
        print(
            f"📁 Main folder URL: https://drive.google.com/drive/folders/{main_folder_id}"
        )

    def _create_index_sheet(self, folder_id, uploaded_files, folder_name):
        """Create an index spreadsheet with links to all uploaded files."""
        print("\n📋 Creating index spreadsheet...")

        # Create a new spreadsheet
        spreadsheet = {
            "properties": {"title": f"jibber-jabber-knowledge-index"},
            "sheets": [{"properties": {"title": "Index"}}],
        }

        sheet = (
            self.sheets_service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId,spreadsheetUrl")
            .execute()
        )

        sheet_id = sheet.get("spreadsheetId")
        sheet_url = sheet.get("spreadsheetUrl")

        # Move the sheet to the folder
        file = (
            self.drive_service.files().get(fileId=sheet_id, fields="parents").execute()
        )

        previous_parents = ",".join(file.get("parents"))

        self.drive_service.files().update(
            fileId=sheet_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        ).execute()

        # Add data to the sheet
        values = [
            ["DNO DUoS Data Index", "", ""],
            ["Created", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"), ""],
            ["", "", ""],
            ["File Name", "Type", "Link"],
        ]

        # Add links to all uploaded files
        for file_name, file_url in uploaded_files:
            # Determine file type
            file_type = "Main Data"
            if "by_year" in file_name:
                file_type = "Year Data"
            elif "by_dno" in file_name:
                file_type = "DNO Data"

            # Clean up the display name
            display_name = os.path.basename(file_name).replace(".csv", "")

            # Add a formula for a hyperlink
            values.append(
                [display_name, file_type, f'=HYPERLINK("{file_url}", "Open Sheet")']
            )

        # Update the values
        body = {"values": values}

        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range="Index!A1",
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

        # Format the index sheet
        try:
            # Apply formatting
            requests = [
                {
                    "updateCells": {
                        "rows": {
                            "values": [
                                {
                                    "userEnteredFormat": {
                                        "textFormat": {"fontSize": 14, "bold": True}
                                    }
                                }
                            ]
                        },
                        "fields": "userEnteredFormat.textFormat",
                        "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1},
                    }
                },
                {
                    "updateCells": {
                        "rows": {
                            "values": [
                                {
                                    "userEnteredFormat": {
                                        "backgroundColor": {
                                            "red": 0.8,
                                            "green": 0.8,
                                            "blue": 0.8,
                                        },
                                        "textFormat": {"bold": True},
                                    }
                                }
                            ]
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)",
                        "range": {"sheetId": 0, "startRowIndex": 3, "endRowIndex": 4},
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": 0,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": 3,
                        }
                    }
                },
            ]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body={"requests": requests}
            ).execute()

        except Exception as e:
            print(f"   ⚠️ Error formatting index sheet: {str(e)}")

        print(f"✅ Created index spreadsheet: {sheet_url}")


def main():
    """Main function to run the uploader."""
    if len(sys.argv) < 2:
        # Default to the gsheets_csv directory
        csv_dir = "duos_outputs2/gsheets_csv"
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Default directory '{csv_dir}' not found.")
            print("Usage: python google_sheets_uploader.py <csv_directory>")
            sys.exit(1)
    else:
        csv_dir = sys.argv[1]
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Directory '{csv_dir}' not found.")
            sys.exit(1)

    uploader = GoogleSheetsUploader()
    uploader.upload_duos_data(csv_dir)


if __name__ == "__main__":
    main()
