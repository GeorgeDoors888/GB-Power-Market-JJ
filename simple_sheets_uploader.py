#!/usr/bin/env python3
"""
Simple Google Sheets Direct Uploader
----------------------------------
A simplified version of the sheets_direct_uploader.py that focuses just on
uploading CSV files to Google Sheets using a service account.
"""

import csv
import os
import sys
from datetime import datetime

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Define the scopes required for Sheets and Drive APIs
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


class SimpleGoogleSheetsUploader:
    def __init__(self, key_file="jibber_jaber_key.json"):
        """Initialize with the path to service account key file."""
        self.key_file = key_file
        self.sheets_service = None
        self.drive_service = None
        self.uploaded_files = []

    def authenticate(self):
        """Authenticate with Google APIs using service account."""
        if not os.path.exists(self.key_file):
            print(f"❌ Error: Service account key file '{self.key_file}' not found.")
            return False

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.key_file, scopes=SCOPES
            )

            # Create service objects
            self.sheets_service = build("sheets", "v4", credentials=credentials)
            self.drive_service = build("drive", "v3", credentials=credentials)

            print(
                "✅ Successfully authenticated with Google APIs using service account"
            )
            return True

        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            return False

    def create_folder(self, folder_name, parent_id=None):
        """Create a folder in Google Drive and return its ID."""
        try:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }

            # Add parent folder ID if provided
            if parent_id:
                file_metadata["parents"] = [parent_id]

            folder = (
                self.drive_service.files()
                .create(body=file_metadata, fields="id, name, webViewLink")
                .execute()
            )

            print(f"📁 Created folder: {folder.get('name')}")
            print(f"   URL: {folder.get('webViewLink')}")

            return folder.get("id"), folder.get("webViewLink")
        except Exception as e:
            print(f"❌ Error creating folder: {str(e)}")
            return None, None

    def upload_csv_as_sheet(self, csv_path, folder_id=None):
        """Upload a CSV file directly to Google Sheets."""
        try:
            # Read the CSV file
            df = pd.read_csv(csv_path)

            # Get filename for the sheet title
            file_name = os.path.basename(csv_path)
            sheet_title = file_name.replace(".csv", "")

            # Create a new spreadsheet
            spreadsheet_body = {"properties": {"title": sheet_title}}

            spreadsheet = (
                self.sheets_service.spreadsheets()
                .create(body=spreadsheet_body, fields="spreadsheetId,spreadsheetUrl")
                .execute()
            )

            spreadsheet_id = spreadsheet.get("spreadsheetId")
            spreadsheet_url = spreadsheet.get("spreadsheetUrl")

            # Move to folder if folder_id is provided
            if folder_id:
                file = (
                    self.drive_service.files()
                    .get(fileId=spreadsheet_id, fields="parents")
                    .execute()
                )

                previous_parents = ",".join(file.get("parents", []))

                self.drive_service.files().update(
                    fileId=spreadsheet_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields="id, parents",
                ).execute()

            # Convert DataFrame to values list
            values = [df.columns.tolist()]  # Header row
            values.extend(df.values.tolist())  # Data rows

            # Update the sheet with data
            body = {"values": values}

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range="Sheet1!A1",
                valueInputOption="RAW",
                body=body,
            ).execute()

            # Format the header row
            self.format_sheet(spreadsheet_id)

            print(f"📊 Uploaded: {sheet_title}")
            print(f"   URL: {spreadsheet_url}")

            return spreadsheet_id, spreadsheet_url

        except Exception as e:
            print(f"❌ Error uploading CSV: {str(e)}")
            return None, None

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

        except Exception as e:
            print(f"   ⚠️ Error formatting sheet: {str(e)}")

    def upload_all_csv_files(self, csv_dir):
        """Upload all CSV files in the directory to Google Sheets."""
        print("\n🚀 UPLOADING DNO DUOS DATA TO GOOGLE SHEETS")
        print("=======================================")

        # Create a main folder
        folder_name = (
            f"jibber-jabber-knowledge-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        folder_id, folder_url = self.create_folder(folder_name)

        if not folder_id:
            print("❌ Failed to create folder. Exiting.")
            return False

        # Track uploaded files
        self.uploaded_files = []

        # Upload main CSV files
        main_csv_files = [
            f
            for f in os.listdir(csv_dir)
            if f.endswith(".csv") and os.path.isfile(os.path.join(csv_dir, f))
        ]

        print(f"\n📂 Uploading {len(main_csv_files)} main files...")

        for file in main_csv_files:
            file_path = os.path.join(csv_dir, file)
            sheet_id, sheet_url = self.upload_csv_as_sheet(file_path, folder_id)
            if sheet_id:
                self.uploaded_files.append((file, sheet_url))

        # Create and upload by_year files
        year_dir = os.path.join(csv_dir, "by_year")
        if os.path.exists(year_dir):
            year_folder_id, _ = self.create_folder("By Year", folder_id)

            if year_folder_id:
                year_files = [
                    f
                    for f in os.listdir(year_dir)
                    if f.endswith(".csv") and os.path.isfile(os.path.join(year_dir, f))
                ]

                print(f"\n📂 Uploading {len(year_files)} year-specific files...")

                for file in year_files:
                    file_path = os.path.join(year_dir, file)
                    sheet_id, sheet_url = self.upload_csv_as_sheet(
                        file_path, year_folder_id
                    )
                    if sheet_id:
                        self.uploaded_files.append((f"by_year/{file}", sheet_url))

        # Create and upload by_dno files
        dno_dir = os.path.join(csv_dir, "by_dno")
        if os.path.exists(dno_dir):
            dno_folder_id, _ = self.create_folder("By DNO", folder_id)

            if dno_folder_id:
                dno_files = [
                    f
                    for f in os.listdir(dno_dir)
                    if f.endswith(".csv") and os.path.isfile(os.path.join(dno_dir, f))
                ]

                print(f"\n📂 Uploading {len(dno_files)} DNO-specific files...")

                for file in dno_files:
                    file_path = os.path.join(dno_dir, file)
                    sheet_id, sheet_url = self.upload_csv_as_sheet(
                        file_path, dno_folder_id
                    )
                    if sheet_id:
                        self.uploaded_files.append((f"by_dno/{file}", sheet_url))

        # Create an index spreadsheet
        index_id = self._create_index_sheet(folder_id, self.uploaded_files, folder_name)

        if index_id:
            print("\n✅ All files uploaded successfully to Google Sheets!")
            print(f"📁 Main folder: {folder_url}")
            return True
        else:
            print("\n⚠️ Some files may not have been uploaded successfully.")
            print(f"📁 Main folder: {folder_url}")
            return False

    def _create_index_sheet(self, folder_id, uploaded_files, folder_name):
        """Create an index spreadsheet with links to all uploaded files."""
        print("\n📋 Creating index spreadsheet...")

        try:
            # Create a new spreadsheet
            spreadsheet_body = {
                "properties": {"title": f"jibber-jabber-knowledge-index"}
            }

            spreadsheet = (
                self.sheets_service.spreadsheets()
                .create(body=spreadsheet_body, fields="spreadsheetId,spreadsheetUrl")
                .execute()
            )

            sheet_id = spreadsheet.get("spreadsheetId")
            sheet_url = spreadsheet.get("spreadsheetUrl")

            # Move the sheet to the folder
            file = (
                self.drive_service.files()
                .get(fileId=sheet_id, fields="parents")
                .execute()
            )

            previous_parents = ",".join(file.get("parents", []))

            self.drive_service.files().update(
                fileId=sheet_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields="id, parents",
            ).execute()

            # Add data to the sheet
            values = [
                ["DNO DUoS Data Index", "", ""],
                ["Created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""],
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
                range="Sheet1!A1",
                valueInputOption="USER_ENTERED",
                body=body,
            ).execute()

            # Format the index sheet
            self.format_sheet(sheet_id)

            print(f"✅ Created index spreadsheet: {sheet_url}")
            return sheet_id

        except Exception as e:
            print(f"❌ Error creating index sheet: {str(e)}")
            return None


def main():
    """Main function to run the uploader."""
    # Get command line arguments
    if len(sys.argv) < 2:
        # Default to the gsheets_csv directory
        csv_dir = "duos_outputs2/gsheets_csv"
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Default directory '{csv_dir}' not found.")
            print("Usage: python simple_sheets_uploader.py <csv_directory> [key_file]")
            sys.exit(1)
    else:
        csv_dir = sys.argv[1]
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Directory '{csv_dir}' not found.")
            sys.exit(1)

    # Get optional key file path
    key_file = "jibber_jaber_key.json"
    if len(sys.argv) > 2:
        key_file = sys.argv[2]

    # Create uploader and run
    uploader = SimpleGoogleSheetsUploader(key_file=key_file)
    if uploader.authenticate():
        uploader.upload_all_csv_files(csv_dir)
    else:
        print("❌ Authentication failed. Exiting.")
        sys.exit(1)


if __name__ == "__main__":
    main()
