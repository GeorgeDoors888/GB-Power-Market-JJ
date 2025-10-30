#!/usr/bin/env python3
"""
Jibber-Jabber Knowledge Google Cloud Setup
----------------------------------------
This script provides information about connecting to the existing jibber-jabber-knowledge
Google Cloud project and setting up the necessary credentials.
"""

import os
import sys
import webbrowser


def main():
    """Show instructions for using the existing Google Cloud project."""
    print("\n" + "=" * 80)
    print("🔑 JIBBER-JABBER-KNOWLEDGE GOOGLE CLOUD SETUP")
    print("=" * 80)

    print(
        "\nThis script will guide you through connecting to the existing 'jibber-jabber-knowledge' Google Cloud project."
    )

    # Check if credentials already exist
    if os.path.exists("credentials.json"):
        print(
            f"✅ Credentials file already exists: {os.path.abspath('credentials.json')}"
        )
        print(
            "\nYou can use these existing credentials for uploading data to Google Sheets."
        )
        print(
            "If you need to create new credentials, please delete the existing file first."
        )

        run_uploader = input(
            "\nDo you want to run the uploader with existing credentials? (y/n): "
        ).lower()
        if run_uploader == "y":
            cmd = f"python google_sheets_uploader.py duos_outputs2/gsheets_csv"
            print(f"\nRunning: {cmd}")
            os.system(cmd)
        return

    print("\n📌 CONNECTING TO EXISTING GOOGLE CLOUD PROJECT")
    print("------------------------------------------")

    print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
    webbrowser.open("https://console.cloud.google.com/")

    print("\n2. Select the 'jibber-jabber-knowledge' project from the dropdown")
    print(
        "   - If you don't see it, you may need to request access from the project owner"
    )

    print("\n3. Navigate to 'APIs & Services' > 'Credentials'")
    webbrowser.open("https://console.cloud.google.com/apis/credentials")

    print("\n4. Click 'Create Credentials' > 'OAuth client ID'")
    print("5. Select 'Desktop app' as the application type")
    print("6. Enter 'jibber-jabber-knowledge-client' as the name")
    print("7. Click 'Create'")
    print(
        "8. Download the JSON file and save it as 'credentials.json' in this directory"
    )

    # Wait for user to download credentials
    while True:
        if os.path.exists("credentials.json"):
            print(
                f"\n✅ Credentials file downloaded: {os.path.abspath('credentials.json')}"
            )
            break

        check = input("\nHave you downloaded the credentials file? (y/n): ").lower()
        if check != "y":
            print("Please download the credentials file to continue.")
        else:
            if not os.path.exists("credentials.json"):
                print("⚠️ Could not find 'credentials.json' in the current directory.")
                print("Please make sure you've saved it correctly.")
            else:
                break

    # Run the uploader if credentials exist
    if os.path.exists("credentials.json"):
        run_uploader = input("\nDo you want to run the uploader now? (y/n): ").lower()
        if run_uploader == "y":
            cmd = f"python google_sheets_uploader.py duos_outputs2/gsheets_csv"
            print(f"\nRunning: {cmd}")
            os.system(cmd)

    print("\n" + "=" * 80)
    print("✅ SETUP COMPLETE!")
    print("=" * 80)
    print("\nYou can now use the Google Sheets uploader with your credentials.")
    print(
        "To upload data, run: python google_sheets_uploader.py duos_outputs2/gsheets_csv"
    )


if __name__ == "__main__":
    main()
