#!/usr/bin/env python3
"""
DNO DUoS Google Sheets Uploader - Complete Process
------------------------------------------------
This script runs the complete process of uploading DNO DUoS data to Google Sheets:
1. Ensures the virtual environment is activated
2. Guides you through setting up Google Cloud credentials
3. Uploads all DNO DUoS data to Google Sheets
4. Provides instructions for sharing the files with colleagues
"""

import os
import subprocess
import sys
import time


def check_virtual_env():
    """Check if running in the virtual environment."""
    # Check if running in a virtual environment
    if not hasattr(sys, "real_prefix") and not (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    ):
        print("\n⚠️ Not running in a virtual environment.")
        print("Please activate the virtual environment first:")
        print("source gsheets_env/bin/activate")
        return False
    return True


def run_command(command, explanation=None):
    """Run a command and print its output."""
    if explanation:
        print(f"\n📌 {explanation}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        # Print output in real-time
        for line in process.stdout:
            print(line, end="")

        process.wait()
        return process.returncode == 0
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return False


def main():
    """Run the complete process."""
    print("\n" + "=" * 80)
    print("🚀 DNO DUOS GOOGLE SHEETS UPLOADER - COMPLETE PROCESS")
    print("=" * 80)

    # Check virtual environment
    if not check_virtual_env():
        sys.exit(1)

    # Step 1: Check required files exist
    csv_dir = "duos_outputs2/gsheets_csv"
    if not os.path.exists(csv_dir):
        print(f"\n❌ Error: CSV directory '{csv_dir}' not found.")
        print(
            "Please run 'python create_gsheets_csv.py' first to generate the CSV files."
        )
        sys.exit(1)

    # Step 2: Check Google Cloud credentials
    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        print(f"\n⚠️ Google Cloud credentials file '{credentials_file}' not found.")
        print("Let's set up your Google Cloud credentials first.")

        # Run the credentials setup helper
        if not run_command(
            "python setup_google_cloud_credentials.py",
            "Setting up Google Cloud credentials",
        ):
            print("\n❌ Error setting up Google Cloud credentials.")
            sys.exit(1)
    else:
        print("\n✅ Google Cloud credentials file found.")

    # Step 3: Upload data to Google Sheets
    print("\n📤 Ready to upload DNO DUoS data to Google Sheets.")
    input("Press Enter to continue or Ctrl+C to cancel...")

    if not run_command(
        f"python google_sheets_uploader.py {csv_dir}", "Uploading data to Google Sheets"
    ):
        print("\n❌ Error uploading data to Google Sheets.")
        sys.exit(1)

    # Step 4: Final instructions
    print("\n" + "=" * 80)
    print("🎉 DNO DUOS DATA UPLOAD COMPLETE!")
    print("=" * 80)

    print("\n📋 SHARING INSTRUCTIONS:")
    print("1. Open the Google Drive folder that was created")
    print("2. Click the 'Share' button in the top-right corner")
    print("3. Enter email addresses of your colleagues")
    print("4. Set appropriate permissions (Viewer, Commenter, or Editor)")
    print("5. Click 'Send' to share the folder and all its contents")

    print("\n📊 DATA ORGANIZATION:")
    print("- The 'Index' sheet provides links to all uploaded sheets")
    print("- DNO-specific data is in the 'By DNO' folder")
    print("- Year-specific data is in the 'By Year' folder")
    print("- Summary statistics are in the main folder")

    print("\n🔄 TO UPDATE THE DATA IN THE FUTURE:")
    print("1. Generate new CSV files with 'python create_gsheets_csv.py'")
    print("2. Run this script again to upload the updated data")

    print("\nThank you for using the DNO DUoS Google Sheets Uploader! 🚀")


if __name__ == "__main__":
    main()
