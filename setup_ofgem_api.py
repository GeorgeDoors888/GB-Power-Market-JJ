#!/usr/bin/env python3
"""
Setup script for Ofgem API
"""

import os
import subprocess
import sys
from pathlib import Path


def install_packages():
    """Install required packages"""
    print("📦 Installing required packages...")

    packages = [
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "requests>=2.31.0",
        "pandas>=2.0.0",
        "python-dotenv>=1.0.0",
    ]

    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False

    return True


def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")

    directories = [
        "./data/ofgem",
        "./data/ofgem/csv",
        "./data/ofgem/documents",
        "./logs",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {directory}")


def check_google_credentials():
    """Check Google credentials"""
    print("🔐 Checking Google credentials...")

    if os.path.exists("jibber_jabber_key.json"):
        print("✅ Google service account key found")
        return True
    else:
        print("⚠️ Google service account key not found")
        print("   This is optional - you can still use Ofgem API without cloud storage")
        return False


def main():
    """Main setup function"""
    print("🏛️ OFGEM API SETUP")
    print("=" * 40)

    print("This will set up the Ofgem API for collecting regulatory data.")
    print("The API complements your existing 1,156 Ofgem documents in Google Drive.")
    print()

    # Install packages
    if not install_packages():
        print("❌ Package installation failed")
        return

    # Create directories
    create_directories()

    # Check credentials
    check_google_credentials()

    print("\n" + "=" * 40)
    print("✅ Setup complete!")
    print()
    print("Next steps:")
    print("1. Run the test: python test_ofgem_api.py")
    print("2. Try the API: python ofgem_api.py")
    print("3. Use sample script: python ofgem_api_sample.py")
    print()
    print("📊 Data will be saved to: ./data/ofgem/")
    print("📋 Logs will be saved to: ./logs/")


if __name__ == "__main__":
    main()
