#!/usr/bin/env python3
"""
Google Sheets Header Cleanup
Fixes the header row issues in the tracking spreadsheet
"""

import os

import google.auth
import gspread
from google.oauth2 import service_account


def fix_google_sheets():
    """Clean up and fix Google Sheets headers"""
    print("🔧 Fixing Google Sheets headers...")

    SPREADSHEET_ID = "1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw"

    try:
        # Use default credentials
        credentials, _ = google.auth.default(
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )

        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(SPREADSHEET_ID).sheet1

        print("📋 Clearing existing content...")
        # Clear all content
        sheet.clear()

        print("📝 Setting proper headers...")
        # Set clean headers
        headers = ["Source", "Dataset", "Last_Update", "Status", "Tracked_At", "Notes"]
        sheet.update("A1:F1", [headers])

        print("✅ Headers fixed successfully!")
        print("🔗 Spreadsheet ready at:")
        print(f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit")

        return True

    except Exception as e:
        print(f"❌ Error fixing sheets: {e}")
        return False


if __name__ == "__main__":
    fix_google_sheets()
