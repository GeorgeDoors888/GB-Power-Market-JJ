#!/usr/bin/env python3
"""
DNO DUoS Data CSV Zipper - Creates a ZIP file of all CSV files
"""

import os
import zipfile
from datetime import datetime

# Constants
OUTPUT_DIR = "csv_output"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
ZIP_FILE = f"DNO_DUoS_CSV_Data_{TIMESTAMP}.zip"


def create_zip():
    """Create a ZIP file containing all CSV files"""
    try:
        # Check if CSV output directory exists
        if not os.path.exists(OUTPUT_DIR):
            print(
                f"❌ CSV output directory '{OUTPUT_DIR}' not found. Run drive_csv_uploader.py first."
            )
            return False

        # Get list of CSV files
        csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".csv")]
        if not csv_files:
            print(
                f"❌ No CSV files found in '{OUTPUT_DIR}'. Run drive_csv_uploader.py first."
            )
            return False

        # Create ZIP file
        with zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in csv_files:
                file_path = os.path.join(OUTPUT_DIR, file)
                zipf.write(file_path, file)
                print(f"✅ Added file to ZIP: {file}")

        print(f"\n✨ ZIP file created: {ZIP_FILE}")
        print(f"   Total files: {len(csv_files)}")
        print(f"   File path: {os.path.abspath(ZIP_FILE)}")

        return True
    except Exception as e:
        print(f"❌ Error creating ZIP file: {e}")
        return False


def main():
    """Main function to create ZIP file"""
    print("\n🚀 CREATING ZIP FILE OF DNO DUOS CSV DATA")
    print("====================================")

    success = create_zip()

    if success:
        print("\n✨ PROCESS COMPLETED")
        print(
            "You can now upload this ZIP file manually to Google Drive or Google Sheets."
        )
        print("Instructions for uploading to Google Sheets:")
        print("1. Go to https://sheets.new to create a new Google Sheet")
        print("2. Click on File > Import > Upload > Select the ZIP file")
        print("3. Choose 'Insert new sheets' and select 'Import data'")
    else:
        print("\n❌ ZIP file creation failed")


if __name__ == "__main__":
    main()
