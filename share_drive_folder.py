#!/usr/bin/env python3
"""
Share Google Drive Folder
------------------------
Shares a specific Google Drive folder with an email address using service account credentials.
"""

import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

# Folder ID from the URL
FOLDER_ID = "1IJ1aGZR0FxhMPWmITcz9aGH0dWHjJGk3"


def share_folder(email, role="reader", folder_id=FOLDER_ID):
    """Share a Google Drive folder with a specific email address."""
    print(f"\n🔄 Sharing folder {folder_id} with {email}...")

    # Set up credentials
    credentials_file = "jibber_jaber_key.json"

    if not os.path.exists(credentials_file):
        print(f"❌ Error: Service account key file '{credentials_file}' not found.")
        return False

    try:
        # Create credentials from service account
        credentials = service_account.Credentials.from_service_account_file(
            credentials_file, scopes=["https://www.googleapis.com/auth/drive"]
        )

        # Build the Drive API service
        drive_service = build("drive", "v3", credentials=credentials)

        # Check if folder exists
        try:
            folder = drive_service.files().get(fileId=folder_id).execute()
            print(f"✅ Found folder: {folder.get('name', 'Unnamed folder')}")
        except Exception as e:
            print(f"❌ Error: Folder not found. {str(e)}")
            return False

        # Create permission
        user_permission = {"type": "user", "role": role, "emailAddress": email}

        # Share the folder
        result = (
            drive_service.permissions()
            .create(
                fileId=folder_id,
                body=user_permission,
                fields="id",
                sendNotificationEmail=True,
            )
            .execute()
        )

        print(f"✅ Successfully shared folder with {email}")
        print(f"🔗 Folder URL: https://drive.google.com/drive/folders/{folder_id}")
        return True

    except Exception as e:
        print(f"❌ Error sharing folder: {str(e)}")
        return False


def main():
    """Main function to share a folder."""
    print("\n📂 GOOGLE DRIVE FOLDER SHARING TOOL")
    print("================================")

    # Get email from command line or prompt
    if len(sys.argv) > 1:
        email = sys.argv[1]
    else:
        print(
            "Please enter YOUR personal Google account email (NOT the service account email)"
        )
        print("This should be the email you use to login to Google Drive/Gmail/etc.")
        email = input("Enter your personal Google account email: ").strip()

    # Check if email is the service account
    if "gserviceaccount.com" in email:
        print(
            "⚠️ You entered a service account email. You should enter your personal Google email instead."
        )
        correction = input(
            "Enter your personal Google account email (or press Enter to continue anyway): "
        ).strip()
        if correction:
            email = correction

    if not email or "@" not in email:
        print("❌ Invalid email address.")
        return

    # Get role (optional)
    role = "writer"  # Default to writer permissions
    if len(sys.argv) > 2:
        role = sys.argv[2]

    success = share_folder(email, role)

    if success:
        print("\n📋 NEXT STEPS:")
        print("1. Check your email for a notification about shared access")
        print("2. Visit https://drive.google.com and look in 'Shared with me'")
        print("3. The folder will appear with full access permissions")
        print("4. You can now view and edit the files in Google Sheets")
    else:
        print("\n⚠️ Sharing failed. Alternative options:")
        print(
            "1. Try accessing the folder directly: "
            f"https://drive.google.com/drive/folders/{FOLDER_ID}"
        )
        print("2. If that doesn't work, check the service account permissions")
        print(
            "3. The CSV files are also available locally in the 'csv_output' directory"
        )


if __name__ == "__main__":
    main()
