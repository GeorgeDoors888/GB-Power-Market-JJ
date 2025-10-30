#!/usr/bin/env python3
"""
Google Sheets Direct Uploader (v2) - Uses service account with proper scopes
This script uploads DNO DUoS data directly to Google Sheets using a service account,
avoiding the need to create files in Google Drive first.
"""

import json
import os
from datetime import datetime

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
INPUT_FILE = "DNO_DUoS_Complete_Data_20250914_193447.xlsx"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SPREADSHEET_NAME = f"DNO_DUoS_Data_{TIMESTAMP}"


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


def create_spreadsheet(service):
    """Create a new Google Spreadsheet"""
    try:
        spreadsheet_body = {"properties": {"title": SPREADSHEET_NAME}}

        request = service.spreadsheets().create(body=spreadsheet_body)
        response = request.execute()

        spreadsheet_id = response["spreadsheetId"]
        spreadsheet_url = response["spreadsheetUrl"]

        print(f"📊 Created spreadsheet: {SPREADSHEET_NAME}")
        print(f"   ID: {spreadsheet_id}")
        print(f"   URL: {spreadsheet_url}")

        return spreadsheet_id, spreadsheet_url
    except HttpError as e:
        print(f"❌ Error creating spreadsheet: {e}")
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


def update_sheet_with_data(service, spreadsheet_id, sheet_title, df):
    """Update a specific sheet with dataframe content"""
    try:
        # First create the sheet
        add_sheet_request = {
            "requests": [{"addSheet": {"properties": {"title": sheet_title}}}]
        }

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=add_sheet_request
        ).execute()

        # Convert the dataframe to values list
        values = [df.columns.tolist()]
        values.extend(df.values.tolist())

        # Update the sheet with data
        body = {"values": values}

        result = (
            service.spreadsheets()
            .values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A1",
                valueInputOption="RAW",
                body=body,
            )
            .execute()
        )

        print(
            f"✅ Sheet '{sheet_title}' updated with {result.get('updatedCells')} cells"
        )
        return True
    except Exception as e:
        print(f"❌ Error updating sheet '{sheet_title}': {e}")
        return False


def share_spreadsheet(drive_service, spreadsheet_id, email):
    """Share the spreadsheet with a specific email"""
    try:
        permission = {"type": "user", "role": "writer", "emailAddress": email}

        drive_service.permissions().create(
            fileId=spreadsheet_id, body=permission, fields="id"
        ).execute()

        print(f"✅ Spreadsheet shared with {email}")
        return True
    except Exception as e:
        print(f"❌ Error sharing spreadsheet: {e}")
        return False


def main():
    """Main function to upload data to Google Sheets"""
    print("\n🚀 UPLOADING DNO DUOS DATA DIRECTLY TO GOOGLE SHEETS")
    print("==============================================")

    # Get credentials
    credentials = get_credentials()
    if not credentials:
        print("❌ Failed to authenticate. Exiting.")
        return

    # Create Sheets API service
    sheets_service = build("sheets", "v4", credentials=credentials)

    # Create Drive API service (for sharing)
    drive_service = build("drive", "v3", credentials=credentials)

    # Create new spreadsheet
    spreadsheet_id, spreadsheet_url = create_spreadsheet(sheets_service)
    if not spreadsheet_id:
        print("❌ Failed to create spreadsheet. Exiting.")
        return

    # Read Excel data
    excel_data = read_excel_data()
    if not excel_data:
        print("❌ Failed to read Excel data. Exiting.")
        return

    # Delete the default Sheet1
    try:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "requests": [
                    {"deleteSheet": {"sheetId": 0}}  # Default sheet ID is always 0
                ]
            },
        ).execute()
    except Exception:
        pass  # If it fails, continue anyway

    # Upload each sheet to the spreadsheet
    for sheet_name, df in excel_data.items():
        # Clean sheet name (remove special characters not allowed in sheet names)
        clean_sheet_name = "".join(
            c if c.isalnum() or c in " _-" else "_" for c in sheet_name
        )[:100]
        update_sheet_with_data(sheets_service, spreadsheet_id, clean_sheet_name, df)

    # Share the spreadsheet with the user (optional)
    user_email = input(
        "Enter your email to share the spreadsheet (or press Enter to skip): "
    ).strip()
    if user_email:
        share_spreadsheet(drive_service, spreadsheet_id, user_email)

    print("\n✨ PROCESS COMPLETED")
    print(f"📊 Your spreadsheet is available at: {spreadsheet_url}")


if __name__ == "__main__":
    main()
