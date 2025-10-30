#!/usr/bin/env python3
"""
Excel to Google Sheets Upload Helper
-----------------------------------
Instructions for uploading an Excel file to Google Sheets.
"""

import os
import sys


def print_instructions(file_path):
    """Print instructions for uploading an Excel file to Google Sheets."""
    file_name = os.path.basename(file_path)

    print("\n" + "=" * 80)
    print(f"HOW TO CONVERT {file_name} TO GOOGLE SHEETS")
    print("=" * 80)

    print("\nOption 1: Manual Upload (Recommended)")
    print("--------------------------------------")
    print("1. Go to Google Drive (https://drive.google.com)")
    print("2. Click the '+ New' button and select 'File upload'")
    print(f"3. Navigate to this file location: {file_path}")
    print(
        "4. After uploading, right-click on the file and select 'Open with' > 'Google Sheets'"
    )
    print("5. To save it as a Google Sheets file, go to File > 'Save as Google Sheets'")

    print("\nOption 2: Using Google Drive's 'Backup and Sync' Tool")
    print("---------------------------------------------------")
    print("1. Install Google Drive for Desktop: https://www.google.com/drive/download/")
    print("2. Set up Google Drive to sync with a folder on your computer")
    print(
        f"3. Copy the Excel file to your Google Drive folder: cp '{file_path}' ~/Google\\ Drive/"
    )
    print("4. Access the file in Google Drive through your browser")
    print("5. Right-click on the file and select 'Open with' > 'Google Sheets'")

    print("\nOption 3: Email to Yourself")
    print("-------------------------")
    print(f"1. Email the file to yourself as an attachment: {file_path}")
    print("2. Open the email in Gmail")
    print("3. Click on the attachment and select 'Open with Google Sheets'")

    print("\n" + "=" * 80)
    print("IMPORTANT NOTES:")
    print("=" * 80)
    print("- Google Sheets has limitations compared to Excel (max 5 million cells)")
    print(
        "- Some advanced Excel features might not translate perfectly to Google Sheets"
    )
    print(
        "- For large files or complex formatting, consider using the CSV files instead"
    )
    print("- The CSV files are located in the 'duos_outputs2' directory")
    print("\n")


def main():
    """Main function to check file and print instructions."""
    if len(sys.argv) < 2:
        print("Usage: python excel_to_gsheets_helper.py <excel_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)

    print_instructions(file_path)


if __name__ == "__main__":
    main()
