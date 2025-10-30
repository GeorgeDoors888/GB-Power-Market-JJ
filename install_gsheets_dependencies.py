#!/usr/bin/env python3
"""
Google Sheets API Dependencies Installer
---------------------------------------
Installs the dependencies needed for the Google Sheets Uploader script.
"""

import os
import platform
import subprocess
import sys


def install_dependencies():
    """Install the required dependencies for the Google Sheets Uploader."""
    print("\n🚀 Google Sheets API Dependencies Installer")
    print("=========================================")

    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("❌ Error: pip is not installed or not working properly.")
        print("Please install pip first: https://pip.pypa.io/en/stable/installation/")
        sys.exit(1)

    # List of required packages
    required_packages = [
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "pandas",
        "openpyxl",
    ]

    print("\n📦 Installing required packages:")
    for package in required_packages:
        print(f"   - {package}")

    # Install the packages
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", *required_packages]
        )
        print("\n✅ All dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing dependencies: {str(e)}")
        sys.exit(1)

    # Check for credentials.json
    if not os.path.exists("credentials.json"):
        print("\n⚠️ Warning: credentials.json file not found.")
        print(
            "Please follow the setup guide in GOOGLE_API_SETUP_GUIDE.md to create and download your credentials."
        )
    else:
        print("\n✅ credentials.json file found.")

    # Provide next steps
    print("\n📋 Next Steps:")
    print("   1. If you haven't created a Google Cloud project and credentials yet:")
    print("      - Read the GOOGLE_API_SETUP_GUIDE.md file for instructions")
    print("   2. Once you have credentials.json, run the uploader:")
    print("      - python google_sheets_uploader.py duos_outputs2/gsheets_csv")

    # Open the setup guide if available
    guide_path = "GOOGLE_API_SETUP_GUIDE.md"
    if os.path.exists(guide_path):
        print("\n📖 Opening the setup guide...")
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.call(["open", guide_path])
            elif platform.system() == "Windows":
                os.startfile(guide_path)
            elif platform.system() == "Linux":
                subprocess.call(["xdg-open", guide_path])
        except:
            print(f"   - Please open {guide_path} manually")


if __name__ == "__main__":
    install_dependencies()
