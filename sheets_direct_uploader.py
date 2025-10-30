#!/usr/bin/env python3
"""
Google Sheets Direct API Uploader
--------------------------------
Uploads DNO DUoS data directly to Google Sheets without creating files in Drive first.
Uses the service account key file (jibber_jaber_key.json) for authentication.
"""

import os
import sys
import json
import pandas as pd
import csv
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account

# Define the scopes required for Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleSheetsDirectUploader:
    def __init__(self, key_file='jibber_jaber_key.json'):
        """Initialize with the path to service account key file."""
        self.key_file = key_file
        self.sheets_service = None
        self.drive_service = None

    def authenticate(self):
        """Authenticate with Google APIs using service account."""
        if not os.path.exists(self.key_file):
            print(f"❌ Error: Service account key file '{self.key_file}' not found.")
            sys.exit(1)

        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.key_file, scopes=SCOPES
            )

            # Create service objects
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)

            print("✅ Successfully authenticated with Google APIs using service account")

        except Exception as e:
            print(f"❌ Authentication failed: {str(e)}")
            sys.exit(1)

    def create_folder(self, folder_name):
        """Create a folder in Google Drive and return its ID."""
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            folder = self.drive_service.files().create(
                body=file_metadata, fields='id, name, webViewLink'
            ).execute()

            print(f"📁 Created folder: {folder.get('name')}")
            print(f"   URL: {folder.get('webViewLink')}")

            return folder.get('id')
        except Exception as e:
            print(f"❌ Error creating folder: {str(e)}")
            return None

    def create_spreadsheet(self, title, folder_id=None):
        """Create a new Google Spreadsheet and return its ID."""
        try:
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }

            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body, fields='spreadsheetId,spreadsheetUrl'
            ).execute()

            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl')

            # Move to folder if folder_id is provided
            if folder_id:
                file = self.drive_service.files().get(
                    fileId=spreadsheet_id, fields='parents'
                ).execute()

                previous_parents = ",".join(file.get('parents', []))

                self.drive_service.files().update(
                    fileId=spreadsheet_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()

            print(f"📊 Created spreadsheet: {title}")
            print(f"   URL: {spreadsheet_url}")

            return spreadsheet_id, spreadsheet_url
        except Exception as e:
            print(f"❌ Error creating spreadsheet: {str(e)}")
            return None, None

    def read_csv_data(self, csv_path):
        """Read CSV data into a list of lists."""
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                data = list(reader)
                return data
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
            return []

    def upload_csv_data(self, spreadsheet_id, data, sheet_name='Sheet1'):
        """Upload CSV data to a Google Sheet."""
        try:
            # Create a new sheet with the specified name
            sheet_properties = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
            }

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=sheet_properties
            ).execute()

            # Upload data to the sheet
            body = {
                'values': data
            }

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body=body
            ).execute()

            # Format the header row
            sheet_id = self._get_sheet_id(spreadsheet_id, sheet_name)
            if sheet_id:
                self._format_sheet(spreadsheet_id, sheet_id)

            print(f"   ✅ Uploaded data to sheet: {sheet_name}")
            return True
        except Exception as e:
            print(f"   ❌ Error uploading data: {str(e)}")
            return False

    def _get_sheet_id(self, spreadsheet_id, sheet_name):
        """Get the sheet ID for a specified sheet name."""
        try:
            sheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()

            sheets = sheet_metadata.get('sheets', [])
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']

            return None
        except Exception as e:
            print(f"   ⚠️ Error getting sheet ID: {str(e)}")
            return None

    def _format_sheet(self, spreadsheet_id, sheet_id):
        """Apply basic formatting to a sheet."""
        try:
            format_requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.7,
                                'green': 0.7,
                                'blue': 0.7
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }, {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': sheet_id,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }, {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 26  # Up to column Z
                    }
                }
            }]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': format_requests}
            ).execute()

            print(f"   🎨 Applied formatting to sheet")

        except Exception as e:
            print(f"   ⚠️ Error formatting sheet: {str(e)}")

    def share_with_domain(self, file_id, domain, role='reader'):
        """Share a file with an entire domain."""
        if not file_id:
            return

        try:
            permission = {
                'type': 'domain',
                'domain': domain,
                'role': role,
            }

            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id',
            ).execute()

            print(f"   🔗 Shared with domain: {domain} (role: {role})")
        except Exception as e:
            print(f"   ⚠️ Error sharing file: {str(e)}")

    def share_with_email(self, file_id, email, role='writer'):
        """Share a file with a specific email address."""
        if not file_id:
            return

        try:
            permission = {
                'type': 'user',
                'emailAddress': email,
                'role': role,
            }

            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                fields='id',
            ).execute()

            print(f"   🔗 Shared with email: {email} (role: {role})")
            return True
        except Exception as e:
            print(f"   ⚠️ Error sharing file with email: {str(e)}")
            return False

    def upload_duos_data_direct(self, csv_dir, share_email=None):
        """Upload DNO DUoS data directly to Google Sheets API."""
        print("\n🚀 UPLOADING DNO DUOS DATA DIRECTLY TO GOOGLE SHEETS")
        print("==============================================")

        # Authenticate with Google APIs
        self.authenticate()

        # Create a main folder
        folder_name = f"jibber-jabber-knowledge-direct-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        main_folder_id = self.create_folder(folder_name)
        if not main_folder_id:
            print("❌ Failed to create main folder. Exiting.")
            return

        # Share the folder with the provided email if specified
        if share_email:
            print(f"📧 Sharing folder with: {share_email}")
            self.share_with_email(main_folder_id, share_email, 'writer')

        # Upload main CSV files
        main_csv_files = [
            f for f in os.listdir(csv_dir)
            if f.endswith('.csv') and os.path.isfile(os.path.join(csv_dir, f))
        ]

        # Create a single spreadsheet with all main data
        main_spreadsheet_id, main_spreadsheet_url = self.create_spreadsheet(
            f"DNO_DUoS_Main_Data_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
            main_folder_id
        )

        if not main_spreadsheet_id:
            print("❌ Failed to create main spreadsheet. Exiting.")
            return

        # Upload each CSV as a separate sheet
        for file in main_csv_files:
            file_path = os.path.join(csv_dir, file)
            sheet_name = file.replace('.csv', '')[:31]  # Sheet names limited to 31 chars
            data = self.read_csv_data(file_path)
            if data:
                self.upload_csv_data(main_spreadsheet_id, data, sheet_name)

        # Handle by_year files
        year_dir = os.path.join(csv_dir, 'by_year')
        if os.path.exists(year_dir):
            year_files = [
                f for f in os.listdir(year_dir)
                if f.endswith('.csv') and os.path.isfile(os.path.join(year_dir, f))
            ]

            if year_files:
                # Create a spreadsheet for years
                year_spreadsheet_id, year_spreadsheet_url = self.create_spreadsheet(
                    f"DNO_DUoS_By_Year_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                    main_folder_id
                )

                if year_spreadsheet_id:
                    for file in year_files:
                        file_path = os.path.join(year_dir, file)
                        sheet_name = file.replace('.csv', '')[:31]
                        data = self.read_csv_data(file_path)
                        if data:
                            self.upload_csv_data(year_spreadsheet_id, data, sheet_name)

        # Handle by_dno files
        dno_dir = os.path.join(csv_dir, 'by_dno')
        if os.path.exists(dno_dir):
            dno_files = [
                f for f in os.listdir(dno_dir)
                if f.endswith('.csv') and os.path.isfile(os.path.join(dno_dir, f))
            ]

            if dno_files:
                # Create a spreadsheet for DNOs
                dno_spreadsheet_id, dno_spreadsheet_url = self.create_spreadsheet(
                    f"DNO_DUoS_By_DNO_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}",
                    main_folder_id
                )

                if dno_spreadsheet_id:
                    for file in dno_files:
                        file_path = os.path.join(dno_dir, file)
                        sheet_name = file.replace('.csv', '')[:31]
                        data = self.read_csv_data(file_path)
                        if data:
                            self.upload_csv_data(dno_spreadsheet_id, data, sheet_name)

        # Create an index spreadsheet
        self._create_index_sheet(
            main_folder_id,
            [
                ("Main Data", main_spreadsheet_url),
                ("By Year", year_spreadsheet_url if 'year_spreadsheet_url' in locals() else None),
                ("By DNO", dno_spreadsheet_url if 'dno_spreadsheet_url' in locals() else None)
            ]
        )

        # Ask if user wants to share with a domain
        share = input("\nDo you want to share with a domain? (y/n): ").lower()
        if share == 'y':
            domain = input("Enter domain to share with (e.g., company.com): ")
            role = input("Enter role (reader, commenter, writer): ").lower() or 'reader'
            if domain:
                self.share_with_domain(main_folder_id, domain, role)

        print("\n✅ All data uploaded successfully to Google Sheets!")
        print(f"📁 Main folder URL: https://drive.google.com/drive/folders/{main_folder_id}")

    def upload_excel_to_drive(self, excel_path, folder_id=None, share_email=None):
        """Upload an Excel file to Google Drive and convert it to Google Sheets."""
        try:
            file_name = os.path.basename(excel_path)
            print(f"\n� Uploading Excel file: {file_name}")

            # Create file metadata including parent folder if provided
            file_metadata = {
                'name': file_name.replace('.xlsx', ''),
                'mimeType': 'application/vnd.google-apps.spreadsheet'
            }

            if folder_id:
                file_metadata['parents'] = [folder_id]

            # Upload the file
            media = MediaFileUpload(
                excel_path,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )

            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()

            file_id = file.get('id')
            file_url = file.get('webViewLink')

            print(f"✅ Uploaded and converted to Google Sheets: {file.get('name')}")
            print(f"   URL: {file_url}")

            # Share with the provided email if specified
            if share_email and file_id:
                self.share_with_email(file_id, share_email, 'writer')

            return file_id, file_url
        except Exception as e:
            print(f"❌ Error uploading Excel file: {str(e)}")
            return None, None

    def upload_excel_direct(self, excel_path, share_email=None):
        """Upload an Excel file directly to Google Drive and convert to Sheets."""
        print("\n🚀 UPLOADING EXCEL FILE DIRECTLY TO GOOGLE SHEETS")
        print("==============================================")

        # Authenticate with Google APIs
        self.authenticate()

        # Create a main folder
        folder_name = f"jibber-jabber-knowledge-excel-{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
        main_folder_id = self.create_folder(folder_name)
        if not main_folder_id:
            print("❌ Failed to create main folder. Exiting.")
            return

        # Share the folder with the provided email if specified
        if share_email:
            print(f"📧 Sharing folder with: {share_email}")
            self.share_with_email(main_folder_id, share_email, 'writer')

        # Upload the Excel file
        file_id, file_url = self.upload_excel_to_drive(excel_path, main_folder_id, share_email)

        if file_id:
            print("\n✅ Excel file successfully uploaded and converted to Google Sheets!")
            print(f"📁 Main folder URL: https://drive.google.com/drive/folders/{main_folder_id}")
        else:
            print("\n❌ Failed to upload Excel file.")

        return file_id, file_url


def main():
    """Main function to run the uploader."""
    if len(sys.argv) < 2:
        # Default to the gsheets_csv directory
        csv_dir = "duos_outputs2/gsheets_csv"
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Default directory '{csv_dir}' not found.")
            print("Usage: python sheets_direct_uploader.py <csv_directory> [email_to_share]")
            sys.exit(1)
    else:
        csv_dir = sys.argv[1]
        if not os.path.exists(csv_dir):
            print(f"❌ Error: Directory '{csv_dir}' not found.")
            sys.exit(1)

    # Get the email to share with
    share_email = sys.argv[2] if len(sys.argv) > 2 else "george@upowerenergy.uk"

    uploader = GoogleSheetsDirectUploader('jibber_jaber_key.json')
    uploader.upload_duos_data_direct(csv_dir, share_email)


if __name__ == "__main__":
    main()
