#!/usr/bin/env python3
"""
Google Cloud Credentials Helper
------------------------------
This script helps create credentials.json for Google Sheets API by guiding
you through the process of setting up a Google Cloud project.
"""

import json
import os
import sys
import time
import webbrowser
from datetime import datetime


class GoogleCloudSetupHelper:
    def __init__(self):
        """Initialize the helper."""
        self.credentials_file = "credentials.json"
        self.project_name = "jibber-jabber-knowledge"

    def run(self):
        """Run the helper to guide the user through setup."""
        print("\n" + "=" * 80)
        print("🔑 GOOGLE CLOUD CREDENTIALS SETUP HELPER")
        print("=" * 80)

        print("\nThis script will guide you through creating Google Cloud credentials.")
        print("You'll need a Google account to complete these steps.\n")

        # Check if credentials already exist
        if os.path.exists(self.credentials_file):
            print(f"⚠️ Credentials file '{self.credentials_file}' already exists.")
            overwrite = input("Do you want to create new credentials? (y/n): ").lower()
            if overwrite != "y":
                print("Exiting without creating new credentials.")
                return

        # Step 1: Create Google Cloud Project
        self._step_create_project()

        # Step 2: Enable APIs
        self._step_enable_apis()

        # Step 3: Create OAuth credentials
        self._step_create_credentials()

        # Step 4: Download and save credentials
        self._step_download_credentials()

        # Final instructions
        self._show_final_instructions()

    def _step_create_project(self):
        """Guide the user through creating a Google Cloud project."""
        print("\n📌 STEP 1: CREATE GOOGLE CLOUD PROJECT")
        print("---------------------------------")

        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        webbrowser.open("https://console.cloud.google.com/")

        print("2. Click on the project dropdown at the top of the page")
        print("3. Click 'New Project'")
        print(f"4. Enter a project name (suggested: {self.project_name})")
        print("5. Click 'Create'")

        input("\nPress Enter when you've completed this step...")

    def _step_enable_apis(self):
        """Guide the user through enabling the required APIs."""
        print("\n📌 STEP 2: ENABLE REQUIRED APIS")
        print("---------------------------")

        print("1. In the Google Cloud Console, select your new project")
        print("2. In the left sidebar, navigate to 'APIs & Services' > 'Library'")

        # Open API Library
        webbrowser.open("https://console.cloud.google.com/apis/library")

        print("\n3. Search for and enable these APIs (one at a time):")

        # Google Sheets API
        print("\n   a) Google Sheets API")
        webbrowser.open(
            "https://console.cloud.google.com/apis/library/sheets.googleapis.com"
        )
        input("      Press Enter when you've enabled the Google Sheets API...")

        # Google Drive API
        print("\n   b) Google Drive API")
        webbrowser.open(
            "https://console.cloud.google.com/apis/library/drive.googleapis.com"
        )
        input("      Press Enter when you've enabled the Google Drive API...")

    def _step_create_credentials(self):
        """Guide the user through creating OAuth credentials."""
        print("\n📌 STEP 3: CREATE OAUTH CREDENTIALS")
        print("-------------------------------")

        # Open credentials page
        webbrowser.open("https://console.cloud.google.com/apis/credentials")

        print("1. In the left sidebar, navigate to 'APIs & Services' > 'Credentials'")
        print("2. Click 'Create Credentials' > 'OAuth client ID'")

        print("\n3. If prompted, configure the OAuth consent screen:")
        print("   - User Type: External")
        print("   - App name: 'jibber-jabber-knowledge'")
        print("   - User support email: Your email address")
        print("   - Developer contact information: Your email address")
        print(
            "   - Save and continue through the wizard (no need to add scopes or test users)"
        )

        input("\nPress Enter when you've configured the consent screen...")

        print("\n4. Return to the Credentials page")
        print("5. Click 'Create Credentials' > 'OAuth client ID' again")
        print("6. Application type: Desktop app")
        print("7. Name: 'jibber-jabber-knowledge-client'")
        print("8. Click 'Create'")

        input("\nPress Enter when you've created the OAuth client ID...")

    def _step_download_credentials(self):
        """Guide the user through downloading and saving credentials."""
        print("\n📌 STEP 4: DOWNLOAD AND SAVE CREDENTIALS")
        print("------------------------------------")

        print("1. After creating the OAuth client ID, you should see a download button")
        print("2. Click 'Download JSON'")
        print(
            f"3. Save the file as '{self.credentials_file}' in the current directory:"
        )
        print(f"   {os.path.abspath(os.curdir)}")

        # Wait for the user to download and move the file
        while not os.path.exists(self.credentials_file):
            response = input(
                "\nHave you downloaded and saved the credentials file? (y/n): "
            ).lower()
            if response == "y":
                if not os.path.exists(self.credentials_file):
                    print(
                        f"⚠️ Could not find '{self.credentials_file}' in the current directory."
                    )
                    print("Please make sure you've saved it correctly.")
                else:
                    break
            else:
                print("Please download and save the credentials file to continue.")
                time.sleep(2)

        print(f"\n✅ Found credentials file: {self.credentials_file}")

        # Validate the credentials file
        try:
            with open(self.credentials_file, "r") as f:
                creds = json.load(f)

            if "installed" in creds and "client_id" in creds["installed"]:
                print("✅ Credentials file is valid.")
            else:
                print(
                    "⚠️ Credentials file format may not be correct, but proceeding anyway."
                )
        except Exception as e:
            print(f"⚠️ Error validating credentials file: {str(e)}")
            print("Please ensure you've downloaded the correct file.")

    def _show_final_instructions(self):
        """Show final instructions for using the credentials."""
        print("\n" + "=" * 80)
        print("✅ GOOGLE CLOUD CREDENTIALS SETUP COMPLETE!")
        print("=" * 80)

        print("\nYour credentials have been saved to:")
        print(f"  {os.path.abspath(self.credentials_file)}")

        print("\n📋 NEXT STEPS:")
        print("1. Run the uploader script with your new credentials:")
        print("   python google_sheets_uploader.py duos_outputs2/gsheets_csv")

        print("\n2. The first time you run the script, it will open a browser window")
        print("   asking you to log in with your Google account and grant permissions.")

        print("\n3. After authentication, the script will:")
        print("   - Create a folder in your Google Drive")
        print("   - Upload all CSV files as Google Sheets")
        print("   - Create an index sheet with links to all files")

        print("\n4. To share the files with colleagues:")
        print("   - Open the main folder in Google Drive")
        print("   - Click the 'Share' button")
        print("   - Enter email addresses and set permissions")

        print("\nGood luck! 🚀")


if __name__ == "__main__":
    helper = GoogleCloudSetupHelper()
    helper.run()
