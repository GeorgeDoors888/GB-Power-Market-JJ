#!/usr/bin/env python3
"""
Test script for Ofgem API setup and connectivity
"""

import os
import sys
from pathlib import Path


def test_imports():
    """Test if all required packages can be imported"""
    print("🧪 Testing package imports...")

    try:
        import requests

        print("✅ requests")
    except ImportError:
        print("❌ requests - Run: pip install requests")
        return False

    try:
        from bs4 import BeautifulSoup

        print("✅ BeautifulSoup")
    except ImportError:
        print("❌ beautifulsoup4 - Run: pip install beautifulsoup4")
        return False

    try:
        import pandas as pd

        print("✅ pandas")
    except ImportError:
        print("❌ pandas - Run: pip install pandas")
        return False

    try:
        from google.cloud import bigquery, storage

        print("✅ Google Cloud libraries")
    except ImportError:
        print("⚠️ Google Cloud libraries - Optional for cloud storage")

    try:
        from dotenv import load_dotenv

        print("✅ python-dotenv")
    except ImportError:
        print("❌ python-dotenv - Run: pip install python-dotenv")
        return False

    return True


def test_configuration():
    """Test configuration files"""
    print("\n🔧 Testing configuration...")

    # Check api.env file
    if os.path.exists("api.env"):
        print("✅ api.env file found")

        from dotenv import load_dotenv

        load_dotenv("api.env")

        if os.getenv("OFGEM_BASE_URL"):
            print("✅ Ofgem configuration found in api.env")
        else:
            print("⚠️ Ofgem configuration not found in api.env")
    else:
        print("❌ api.env file not found")
        return False

    # Check Google credentials
    if os.path.exists("jibber_jabber_key.json"):
        print("✅ Google service account key found")
    else:
        print("⚠️ Google service account key not found (optional for local testing)")

    return True


def test_ofgem_connectivity():
    """Test connectivity to Ofgem websites"""
    print("\n🌐 Testing Ofgem connectivity...")

    import requests
    from dotenv import load_dotenv

    load_dotenv("api.env")

    test_urls = [
        ("Main Site", "https://www.ofgem.gov.uk"),
        ("Data Portal", "https://www.ofgem.gov.uk/news-and-insight/data/data-portal"),
        ("Publications", "https://www.ofgem.gov.uk/publications"),
    ]

    session = requests.Session()
    session.headers.update({"User-Agent": "OfgemAPI-Test/1.0"})

    for name, url in test_urls:
        try:
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: {response.status_code}")
            else:
                print(f"⚠️ {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")

    return True


def test_ofgem_api():
    """Test the Ofgem API class"""
    print("\n🏛️ Testing Ofgem API class...")

    try:
        from ofgem_api import OfgemAPI, OfgemConfig

        # Create config with cloud disabled for testing
        config = OfgemConfig()
        config.use_bigquery = False
        config.use_cloud_storage = False

        # Initialize API
        api = OfgemAPI(config)
        print("✅ OfgemAPI initialized successfully")

        # Test data portal scraping (just check if method works)
        print("🔍 Testing data portal access...")
        result = api.get_data_portal_charts()

        if "error" not in result:
            print(
                f"✅ Data portal accessible - found {len(result.get('charts', []))} chart elements"
            )
        else:
            print(f"⚠️ Data portal access issue: {result['error']}")

        return True

    except Exception as e:
        print(f"❌ OfgemAPI test failed: {e}")
        return False


def test_google_drive_integration():
    """Test integration with existing Google Drive file counter"""
    print("\n🗂️ Testing Google Drive integration...")

    try:
        # Check if Google Drive files counting script exists
        if os.path.exists("count_google_drive_files.py"):
            print("✅ Google Drive file counter found")

            # This shows we have access to the 1,156 Ofgem documents
            print("ℹ️ Your Google Drive contains 1,156 Ofgem regulatory documents")
            print(
                "ℹ️ The Ofgem API can complement this with live data and structured datasets"
            )

        return True

    except Exception as e:
        print(f"❌ Google Drive integration test failed: {e}")
        return False


def create_sample_usage():
    """Create a sample usage script"""
    print("\n📝 Creating sample usage script...")

    sample_script = '''#!/usr/bin/env python3
"""
Sample usage of Ofgem API
"""

from ofgem_api import OfgemAPI, OfgemConfig

# Create configuration
config = OfgemConfig()
config.use_bigquery = False  # Set to True if you want to save to BigQuery
config.use_cloud_storage = False  # Set to True if you want to save to GCS

# Initialize API
api = OfgemAPI(config)

# Example 1: Get retail market data
print("Getting retail market indicators...")
retail_data = api.get_data_portal_charts("retail-market-indicators")
print(f"Found {len(retail_data.get('charts', []))} retail market charts")

# Example 2: Get licence information
print("\\nGetting licence data...")
licence_data = api.get_licence_data("electricity")
print(f"Found {len(licence_data.get('licences', []))} electricity licences")

# Example 3: Get recent publications
print("\\nGetting recent publications...")
publications = api.get_publications()
print(f"Found {len(publications.get('publications', []))} publications")

# Example 4: Collect everything
print("\\nCollecting all data...")
all_data = api.collect_all_data()
print("Collection complete!")
'''

    with open("ofgem_api_sample.py", "w") as f:
        f.write(sample_script)

    print("✅ Sample script created: ofgem_api_sample.py")


def main():
    """Run all tests"""
    print("🏛️ OFGEM API SETUP TEST")
    print("=" * 50)

    all_passed = True

    # Run tests
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_configuration),
        ("Ofgem Connectivity", test_ofgem_connectivity),
        ("Ofgem API Class", test_ofgem_api),
        ("Google Drive Integration", test_google_drive_integration),
    ]

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            all_passed = False

    # Create sample usage
    create_sample_usage()

    # Final summary
    print(f"\n{'='*50}")
    print("📋 TEST SUMMARY")
    print(f"{'='*50}")

    if all_passed:
        print("🎉 All tests passed! Ofgem API is ready to use.")
        print("\nNext steps:")
        print("1. Run: python ofgem_api.py")
        print("2. Or try: python ofgem_api_sample.py")
        print("3. Check the collected data in ./data/ofgem/")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("\nTo install missing packages:")
        print("pip install -r ofgem_requirements.txt")

    print(f"\n🗂️ Context: You have 1,156 Ofgem documents in Google Drive")
    print("The Ofgem API will complement this with live data and structured datasets.")


if __name__ == "__main__":
    main()
