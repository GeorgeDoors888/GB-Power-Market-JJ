#!/usr/bin/env python3
"""
Google Sheets Service Account Uploader
------------------------------------
Uploads DNO DUoS data to Google Sheets using a service account key.
Uses the service account key file (jibber_jaber_key.json) for authentication.
"""

import json
import os
import sys

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Define the scopes required for Drive and Sheets APIs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


class GoogleSheetsServiceUploader:
    def __init__(self, service_account_file="jibber_jaber_key.json"):
        """Initialize with the path to service account file."""
        self.service_account_file = service_account_file
        self.drive_service = None
        self.sheets_service = None

    def authenticate(self):
        """Authenticate with Google APIs using service account."""
        try:
            # Check if service account file exists
            if not os.path.exists(self.service_account_file):
                print(
                    f"❌ Error: Service account file '{self.service_account_file}' not found."
                )
                return False

            # Create credentials from service account
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file, scopes=SCOPES
            )

            # Create service objects
            self.drive_service = build("drive", "v3", credentials=credentials)
            self.sheets_service = build("sheets", "v4", credentials=credentials)

            print(
                "✅ Successfully authenticated with Google APIs using service account"
            )
            return True

        except Exception as e:
            print(f"❌ Error authenticating with service account: {str(e)}")
            import traceback

            traceback.print_exc()
            return False

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

    def share_file(self, file_id, email, role="reader"):
        """Share a file with a specific user."""
        try:
            permission = {"type": "user", "role": role, "emailAddress": email}

            result = (
                self.drive_service.permissions()
                .create(
                    fileId=file_id,
                    body=permission,
                    fields="id",
                    sendNotificationEmail=True,
                )
                .execute()
            )

            print(f"   🔗 Shared with {email} as {role}")
            return True

        except Exception as e:
            print(f"   ⚠️ Error sharing file: {str(e)}")
            return False

    def upload_duos_data(self, csv_dir):
        """Upload all DNO DUoS CSV data to Google Sheets."""
        print("\n🚀 UPLOADING DNO DUOS DATA TO GOOGLE SHEETS")
        print("=======================================")

        # Authenticate with Google APIs
        if not self.authenticate():
            print("❌ Authentication failed. Please check your service account file.")
            return

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
            uploaded_files.append((file, sheet_id, sheet_url))

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
                uploaded_files.append((f"by_year/{file}", sheet_id, sheet_url))

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
                uploaded_files.append((f"by_dno/{file}", sheet_id, sheet_url))

        # Create an index spreadsheet
        index_id = self._create_index_sheet(main_folder_id, uploaded_files, folder_name)

        print("\n✅ All files uploaded successfully to Google Sheets!")
        print(
            f"📁 Main folder URL: https://drive.google.com/drive/folders/{main_folder_id}"
        )

        # Ask if user wants to share the folder
        share_option = input(
            "\nDo you want to share this folder with someone? (y/n): "
        ).lower()
        if share_option == "y":
            email = input("Enter the email address to share with: ")
            role = input("Enter the role (reader, writer, commenter): ").lower()
            if role not in ["reader", "writer", "commenter"]:
                role = "reader"

            self.share_file(main_folder_id, email, role)
            print(f"\n✅ Folder shared with {email} as {role}")

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
        for file_name, file_id, file_url in uploaded_files:
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
        return sheet_id


def main():
    """Main function to run the uploader."""
    if len(sys.argv) < 2:
        # Default to the gsheets_csv directory
        csv_dir = "duos_outputs2/gsheets_csv"
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Default directory '{csv_dir}' not found.")
            print("Usage: python service_account_uploader.py <csv_directory>")
            sys.exit(1)
    else:
        csv_dir = sys.argv[1]
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Directory '{csv_dir}' not found.")
            sys.exit(1)

    uploader = GoogleSheetsServiceUploader()
    uploader.upload_duos_data(csv_dir)


if __name__ == "__main__":
    main()
