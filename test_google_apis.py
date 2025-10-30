#!/usr/bin/env python3
"""
Test script to verify all Google API connections are working
"""

import os

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def get_credentials():
    """Get credentials from service account key file"""
    return service_account.Credentials.from_service_account_file(
        "jibber_jabber_key.json", scopes=SCOPES
    )


def test_bigquery():
    """Test BigQuery connection"""
    print("\nTesting BigQuery connection...")
    try:
        client = bigquery.Client()
        # Test query
        query = "SELECT 1"
        query_job = client.query(query)
        results = query_job.result()
        print("✅ BigQuery connection successful!")
        return True
    except Exception as e:
        print(f"❌ BigQuery connection failed: {str(e)}")
        return False


def test_sheets():
    """Test Google Sheets API"""
    print("\nTesting Google Sheets API...")
    try:
        credentials = get_credentials()
        service = build("sheets", "v4", credentials=credentials)

        # Create a test spreadsheet
        spreadsheet = {"properties": {"title": "Test Spreadsheet"}}
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        print(
            f"✅ Google Sheets API working! Created spreadsheet with ID: {spreadsheet.get('spreadsheetId')}"
        )
        return True
    except HttpError as e:
        print(f"❌ Google Sheets API failed: {str(e)}")
        return False


def test_drive():
    """Test Google Drive API"""
    print("\nTesting Google Drive API...")
    try:
        credentials = get_credentials()
        service = build("drive", "v3", credentials=credentials)

        # List files
        results = service.files().list(pageSize=10).execute()
        files = results.get("files", [])
        print(f"✅ Google Drive API working! Found {len(files)} files")
        return True
    except HttpError as e:
        print(f"❌ Google Drive API failed: {str(e)}")
        return False


def test_docs():
    """Test Google Docs API"""
    print("\nTesting Google Docs API...")
    try:
        credentials = get_credentials()
        service = build("docs", "v1", credentials=credentials)

        # Create a test document
        document = {"title": "Test Document"}
        doc = service.documents().create(body=document).execute()
        print(
            f"✅ Google Docs API working! Created document with ID: {doc.get('documentId')}"
        )
        return True
    except HttpError as e:
        print(f"❌ Google Docs API failed: {str(e)}")
        return False


def main():
    print("Starting Google API connection tests...")

    # Test all services
    services = {
        "BigQuery": test_bigquery,
        "Google Sheets": test_sheets,
        "Google Drive": test_drive,
        "Google Docs": test_docs,
    }

    results = {}
    for service_name, test_func in services.items():
        results[service_name] = test_func()

    # Print summary
    print("\n=== Test Summary ===")
    for service_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{service_name}: {status}")


if __name__ == "__main__":
    main()
