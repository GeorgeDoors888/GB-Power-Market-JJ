#!/usr/bin/env python3
"""
Google Sheets Setup for Energy Data Tracking
This script initializes your Google Sheets for tracking data ingestion.
"""

import os
import sys
from datetime import datetime, timezone

from automated_data_tracker import DataTracker


def setup_google_sheets():
    """Setup Google Sheets with proper headers and initial data"""
    print("🔧 Setting up Google Sheets for energy data tracking...")

    try:
        tracker = DataTracker()

        # Ensure headers are set
        print("📋 Setting up sheet headers...")
        tracker.ensure_sheet_headers()

        # Add initial tracking entries
        print("📊 Adding initial tracking entries...")
        current_time = datetime.now(timezone.utc)

        # Add Elexon entry
        tracker.update_ingestion_time(
            "ELEXON",
            "ALL",
            current_time,
            "INITIALIZED",
        )

        # Add NESO entry
        tracker.update_ingestion_time("NESO", "ALL", current_time, "INITIALIZED")

        print("✅ Google Sheets setup completed successfully!")
        print("")
        print("Your tracking spreadsheet is now ready at:")
        print(
            "https://docs.google.com/spreadsheets/d/1K4mIoPBuqNTbQmrxkYsp0UJF1e2r1jAAdtSYxBEkZsw/edit"
        )
        print("")
        print("The sheet now contains:")
        print("  • Source: Data source (ELEXON, NESO)")
        print("  • Dataset: Dataset identifier")
        print("  • Last_Update: Timestamp of last successful update")
        print("  • Status: Current status (SUCCESS, FAILED, etc.)")
        print("  • Tracked_At: When this entry was recorded")
        print("  • Notes: Additional information")

    except Exception as e:
        print(f"❌ Error setting up Google Sheets: {e}")
        print("")
        print("Common solutions:")
        print("1. Make sure you've run: gcloud auth application-default login")
        print("2. Ensure the Google Sheets API is enabled in your Google Cloud project")
        print("3. Check that your account has access to the spreadsheet")
        sys.exit(1)


if __name__ == "__main__":
    setup_google_sheets()
