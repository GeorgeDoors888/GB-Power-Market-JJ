#!/usr/bin/env python3
"""
Test Google Sheets API Authentication

This script tests authentication with the Google Sheets API using the service account.
It attempts to connect to the configured spreadsheet and read the data.
"""

import json
import os
import sys
from datetime import datetime

import gspread
from dotenv import load_dotenv
from google.oauth2 import service_account

# Load environment variables
if os.path.exists("google_sheets.env"):
    load_dotenv("google_sheets.env")
else:
    load_dotenv()

# Configuration
SPREADSHEET_ID = os.environ.get(
    "SPREADSHEET_ID", "1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw"
)
WORKSHEET_NAME = os.environ.get("WORKSHEET_NAME", "Sheet1")


def test_connection():
    """Test connection to Google Sheets"""
    print(f"Testing connection to Google Sheets spreadsheet: {SPREADSHEET_ID}")

    # First try using environment variables
    service_account_info = {
        "type": "service_account",
        "project_id": "jibber-jabber-knowledge",
        "private_key_id": os.environ.get("GOOGLE_PRIVATE_KEY_ID", ""),
        "private_key": os.environ.get("GOOGLE_PRIVATE_KEY", "").replace("\\n", "\n"),
        "client_email": "jibber-jabber-knowledge@appspot.gserviceaccount.com",
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/jibber-jabber-knowledge%40appspot.gserviceaccount.com",
        "universe_domain": "googleapis.com",
    }

    # If any of the required keys are missing, try to find a credentials file
    if (
        not service_account_info["private_key"]
        or not service_account_info["private_key_id"]
    ):
        print(
            "Missing required environment variables, checking for credential files..."
        )

        cred_files = [
            "client_secrets.json",
            "service_account.json",
            "google_credentials.json",
            f'{os.path.expanduser("~")}/.config/gcloud/application_default_credentials.json',
        ]

        credentials = None
        for cred_file in cred_files:
            if os.path.exists(cred_file):
                try:
                    print(f"Trying credentials from {cred_file}")
                    credentials = service_account.Credentials.from_service_account_file(
                        cred_file,
                        scopes=[
                            "https://www.googleapis.com/auth/spreadsheets",
                            "https://www.googleapis.com/auth/drive",
                        ],
                    )
                    break
                except Exception as e:
                    print(f"Could not load {cred_file}: {e}")
    else:
        try:
            print("Using credentials from environment variables")
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
        except Exception as e:
            print(f"Could not use service account info from environment: {e}")
            credentials = None

    # If we still don't have credentials, try to use application default credentials
    if not credentials:
        try:
            print("No service account credentials found. Trying default ADC.")
            import google.auth

            credentials, _ = google.auth.default(
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
            )
        except Exception as e:
            print(f"Failed to get default credentials: {e}")
            return False

    try:
        # Connect to Google Sheets
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)

        # Test operations
        print("Successfully connected to the spreadsheet!")

        # Get headers
        headers = sheet.row_values(1)
        print(f"Headers: {headers}")

        # Get all data
        data = sheet.get_all_records()
        print(f"Found {len(data)} rows of data")

        # Test write operation
        test_row = [
            "TEST",
            "CONNECTION",
            datetime.now().isoformat(),
            "SUCCESS",
            datetime.now().isoformat(),
            f"Connection test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        ]

        # If we got this far, we can clean up before adding a test row
        existing_test_rows = []
        for i, row in enumerate(data):
            if row.get("Source") == "TEST" and row.get("Dataset") == "CONNECTION":
                existing_test_rows.append(i + 2)  # +2 for header and 1-indexing

        # Remove old test rows if they exist
        if existing_test_rows:
            print(f"Cleaning up {len(existing_test_rows)} old test rows")
            for row_index in sorted(existing_test_rows, reverse=True):
                sheet.delete_row(row_index)

        # Add new test row
        print("Adding test row...")
        sheet.append_row(test_row)
        print("Test row added successfully!")

        return True

    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return False


if __name__ == "__main__":
    print("Google Sheets Authentication Test")
    print("=================================")
    print(f"Current directory: {os.getcwd()}")

    success = test_connection()

    if success:
        print("\n✅ Google Sheets authentication test passed!")
        sys.exit(0)
    else:
        print("\n❌ Google Sheets authentication test failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have the correct service account credentials")
        print("2. Check that the service account has access to the spreadsheet")
        print("3. Verify that the spreadsheet ID is correct")
        print("4. Ensure you have the right API scopes enabled")
        sys.exit(1)
