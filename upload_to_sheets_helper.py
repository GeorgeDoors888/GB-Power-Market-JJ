#!/usr/bin/env python3
"""
DNO DUoS Data Google Sheets Upload Helper
----------------------------------------
Simplifies the process of uploading DNO DUoS CSV data to Google Sheets by:
1. Creating optimized CSV files (if needed)
2. Creating a ZIP archive of all CSV files
3. Providing options for both manual upload and direct API upload

This tool supports two upload methods:
- Manual upload (no authentication needed)
- Direct API upload using the service account (jibber_jaber_key.json)
"""

import argparse
import datetime
import importlib.util
import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def check_csv_files(csv_dir):
    """Check if CSV files exist and are ready for upload."""
    csv_path = Path(csv_dir)

    if not csv_path.exists():
        print(f"❌ CSV directory not found: {csv_dir}")
        return False

    csv_files = list(csv_path.glob("*.csv"))
    if not csv_files:
        print(f"❌ No CSV files found in {csv_dir}")
        return False

    print(f"✅ Found {len(csv_files)} CSV files in main directory")

    # Check subdirectories
    by_year = csv_path / "by_year"
    by_dno = csv_path / "by_dno"

    if by_year.exists():
        year_files = list(by_year.glob("*.csv"))
        print(f"✅ Found {len(year_files)} year-specific CSV files")

    if by_dno.exists():
        dno_files = list(by_dno.glob("*.csv"))
        print(f"✅ Found {len(dno_files)} DNO-specific CSV files")

    return True


def create_csv_files(input_path):
    """Run the create_gsheets_csv.py script to generate optimized CSV files."""
    print("\n🔄 CREATING GOOGLE SHEETS OPTIMIZED CSV FILES")
    print("==========================================")

    cmd = [sys.executable, "create_gsheets_csv.py", input_path]
    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print("✅ CSV files created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating CSV files: {e}")
        return False
    except FileNotFoundError:
        print("❌ create_gsheets_csv.py script not found")
        return False


def create_zip_archive(csv_dir):
    """Create a ZIP archive of all CSV files."""
    print("\n🔄 CREATING ZIP ARCHIVE")
    print("===================")

    cmd = [sys.executable, "create_duos_sheets_zip.py", "--csv-dir", csv_dir]
    print(f"Running: {' '.join(cmd)}")

    try:
        output = subprocess.check_output(cmd, universal_newlines=True)

        # Try to extract the ZIP file path from the output
        zip_path = None
        for line in output.splitlines():
            if "Location:" in line:
                zip_path = line.split("Location:")[1].strip()
                break

        return zip_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating ZIP archive: {e}")
        return None
    except FileNotFoundError:
        print("❌ create_duos_sheets_zip.py script not found")
        return None


def use_direct_uploader(csv_dir, key_file="jibber_jaber_key.json"):
    """Use the simple_sheets_uploader.py to upload directly via API."""
    print("\n🔄 USING DIRECT API UPLOAD")
    print("=======================")

    # Check if key file exists
    if not os.path.exists(key_file):
        print(f"❌ Service account key file '{key_file}' not found")
        print("   Please ensure the file exists in the current directory")
        return False

    # Check if direct uploader module exists
    uploader_path = "simple_sheets_uploader.py"
    if not os.path.exists(uploader_path):
        print(f"❌ Simple uploader script '{uploader_path}' not found")
        return False

    print(f"✅ Found service account key: {key_file}")
    print(f"✅ Found uploader script: {uploader_path}")

    # Import the module dynamically
    try:
        spec = importlib.util.spec_from_file_location(
            "simple_sheets_uploader", uploader_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Create uploader instance
        uploader = module.SimpleGoogleSheetsUploader(key_file=key_file)

        # Call the upload method
        print("\n🔄 Starting direct upload to Google Sheets...")
        if uploader.authenticate():
            success = uploader.upload_all_csv_files(csv_dir)

            if success:
                print("\n✅ Direct API upload completed successfully!")
                return True
            else:
                print("\n⚠️ Some files may not have uploaded correctly.")
                print("   Please check the Google Drive folder for details.")
                return False
        else:
            print("\n❌ Authentication failed with the service account.")
            return False
    except Exception as e:
        if "permission" in str(e).lower():
            print("\n❌ Permission error with the service account.")
            print(
                "   The service account needs to have the Sheets and Drive APIs enabled."
            )
            print("   Please check the following:")
            print(
                "   1. Make sure the service account is enabled in Google Cloud Console"
            )
            print(
                "   2. Google Sheets API and Google Drive API are enabled for the project"
            )
            print("   3. The service account has appropriate permissions")
        else:
            print(f"\n❌ Error during direct upload: {str(e)}")
            import traceback

            traceback.print_exc()
        return False
        return True
    except Exception as e:
        print(f"\n❌ Error during direct upload: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def show_upload_instructions(zip_path):
    """Display instructions for uploading to Google Sheets."""
    print("\n📋 UPLOAD INSTRUCTIONS")
    print("===================")

    print(f"\n1. Your ZIP file is ready: {zip_path}")
    print("\n2. Choose one of these upload methods:")

    print("\n   OPTION A: Direct Google Drive Upload (Recommended)")
    print("   ------------------------------------------")
    print("   a. Go to Google Drive: https://drive.google.com")
    print("   b. Create a new folder for the DNO DUoS data")
    print("   c. Upload the ZIP file to that folder")
    print("   d. Right-click the ZIP file and select 'Open with' > 'Google Workspace'")
    print(
        "   e. Google will extract the files and you can open them with Google Sheets"
    )

    print("\n   OPTION B: Extract and Upload Individual Files")
    print("   -----------------------------------------")
    print("   a. Extract the ZIP file on your computer")
    print("   b. Go to Google Sheets: https://sheets.new")
    print("   c. Use File > Import > Upload to select each CSV file")

    print("\n3. Would you like to open Google Drive now to start uploading?")
    choice = input("   Enter 'y' to open Google Drive or any other key to continue: ")

    if choice.lower() == "y":
        webbrowser.open("https://drive.google.com")
        print("\n✅ Opened Google Drive in your web browser")


def find_default_paths():
    """Find default paths for input and output."""
    # Look for the enhanced CSV file
    input_paths = [
        "duos_outputs2/duos_all_bands_enhanced_v3.csv",
        "duos_outputs/duos_all_bands_enhanced_v3.csv",
        "duos_outputs2/duos_all_bands_enhanced.csv",
        "duos_outputs/duos_all_bands_enhanced.csv",
    ]

    for path in input_paths:
        if os.path.exists(path):
            return path

    # If no specific file found, look for directories
    dirs = ["duos_outputs2", "duos_outputs", "outputs"]
    for dir_path in dirs:
        if os.path.exists(dir_path):
            # Look for any CSV file in this directory
            csv_files = list(Path(dir_path).glob("*.csv"))
            if csv_files:
                return str(csv_files[0])

    return None


def main():
    """Main function to run the upload helper."""
    parser = argparse.ArgumentParser(
        description="DNO DUoS Data Google Sheets Upload Helper"
    )
    parser.add_argument("--input", help="Path to the enhanced CSV file")
    parser.add_argument(
        "--csv-dir", help="Directory containing the Google Sheets optimized CSV files"
    )
    parser.add_argument(
        "--skip-csv-creation",
        action="store_true",
        help="Skip creating CSV files and use existing ones",
    )
    parser.add_argument(
        "--direct-upload",
        action="store_true",
        help="Use direct API upload with service account",
    )
    parser.add_argument(
        "--key-file",
        default="jibber_jaber_key.json",
        help="Path to service account key file",
    )
    parser.add_argument(
        "--manual-only",
        action="store_true",
        help="Skip API upload and only prepare files for manual upload",
    )
    args = parser.parse_args()

    print("\n🚀 DNO DUoS DATA GOOGLE SHEETS UPLOAD HELPER")
    print("=========================================")

    # Determine CSV directory
    csv_dir = args.csv_dir
    if not csv_dir:
        csv_dir = "duos_outputs2/gsheets_csv"

    # Check if CSV files exist
    csv_files_exist = check_csv_files(csv_dir)

    # If CSV files don't exist or we're not skipping creation, create them
    if not csv_files_exist and not args.skip_csv_creation:
        input_path = args.input
        if not input_path:
            input_path = find_default_paths()
            if not input_path:
                print("❌ Could not find input CSV file. Please specify with --input")
                return

        print(f"🔍 Using input file: {input_path}")

        # Create the CSV files
        if not create_csv_files(input_path):
            print("❌ Failed to create CSV files. Exiting.")
            return
    elif args.skip_csv_creation:
        print("⏩ Skipping CSV file creation as requested")

    # Determine upload method
    if args.direct_upload:
        # Try direct API upload first
        if use_direct_uploader(csv_dir, args.key_file):
            print("\n✨ DIRECT API UPLOAD COMPLETED SUCCESSFULLY")
            print(
                "Your data has been uploaded to Google Sheets using the service account."
            )
            return
        else:
            print("\n⚠️ Direct API upload failed. Falling back to manual upload...")
    elif not args.manual_only:
        # If not explicitly choosing direct or manual, ask the user
        print("\n📊 UPLOAD METHOD")
        print("=============")
        print("1. Direct API Upload (using service account)")
        print("2. Manual Upload (prepare files for manual upload)")

        try:
            choice = input("\nEnter your choice (1 or 2): ")
            if choice == "1":
                if use_direct_uploader(csv_dir, args.key_file):
                    print("\n✨ DIRECT API UPLOAD COMPLETED SUCCESSFULLY")
                    print(
                        "Your data has been uploaded to Google Sheets using the service account."
                    )
                    return
                else:
                    print(
                        "\n⚠️ Direct API upload failed. Falling back to manual upload..."
                    )
        except KeyboardInterrupt:
            print("\n⏩ Continuing with manual upload preparation...")

    # Create the ZIP archive for manual upload
    zip_path = create_zip_archive(csv_dir)
    if not zip_path:
        print("❌ Failed to create ZIP archive. Exiting.")
        return

    # Show upload instructions
    show_upload_instructions(zip_path)

    print("\n✨ PROCESS COMPLETED SUCCESSFULLY")
    print(
        "You can now upload your data to Google Sheets following the instructions above."
    )
    print("The ZIP file contains both the data files and detailed instructions.")


if __name__ == "__main__":
    main()
