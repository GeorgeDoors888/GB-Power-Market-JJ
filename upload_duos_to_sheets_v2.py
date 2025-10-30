#!/usr/bin/env python3
"""
Google Sheets DUoS Data Uploader - Uses service account
This script splits and uploads the DUoS Excel data to Google Sheets
"""

import os
from datetime import datetime

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SERVICE_ACCOUNT_FILE = "jibber_jaber_key.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]
INPUT_FILE = "duos_outputs2/DNO_DUoS_All_Data_Consolidated_Complete.xlsx"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_DIR = "temp_csv"


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


def create_spreadsheet(service, sheet_name, df):
    """Create a new Google Sheet and upload data"""
    try:
        spreadsheet = {"properties": {"title": sheet_name}}

        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet["spreadsheetId"]

        # Convert the DataFrame values to a list of lists
        values = [df.columns.values.tolist()] + df.values.tolist()

        body = {"values": values}

        # Update the sheet with the data
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1",
            valueInputOption="RAW",
            body=body,
        ).execute()

        print(f"✅ Created sheet: {sheet_name}")
        print(f"📊 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")
        return spreadsheet_id

    except HttpError as e:
        print(f"❌ Failed to create sheet {sheet_name}: {e}")
        return None


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

    # Create Sheets API service
    sheets_service = build("sheets", "v4", credentials=credentials)

    # Read each sheet from the Excel file
    xl = pd.ExcelFile(INPUT_FILE)
    sheet_names = xl.sheet_names

    print(f"📑 Found {len(sheet_names)} sheets to process")

    base_name = f"DNO_DUoS_Data_{TIMESTAMP}"
    sheet_urls = {}

    for i, sheet_name in enumerate(sheet_names, 1):
        print(f"\n⏳ Processing sheet {i}/{len(sheet_names)}: {sheet_name}")

        # Read the sheet
        df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)

        # Create a Google Sheet for this tab
        gsheet_name = f"{base_name}_{sheet_name}"
        sheet_id = create_spreadsheet(sheets_service, gsheet_name, df)

        if sheet_id:
            sheet_urls[sheet_name] = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}"
            )

    print("\n✨ Upload complete!")
    print("\nSheet URLs:")
    for name, url in sheet_urls.items():
        print(f"{name}: {url}")


if __name__ == "__main__":
    main()
