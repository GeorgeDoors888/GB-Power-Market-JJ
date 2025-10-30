#!/usr/bin/env python3
"""
Quick test script for Google Custom Search JSON API
"""

import os
import sys


def test_google_search_api():
    """
    Quick test of the Google Custom Search API setup
    """

    print("🔍 GOOGLE CUSTOM SEARCH API TEST")
    print("=" * 40)

    # Check if we have the google_search_setup module
    try:
        from google_search_setup import GoogleCustomSearch

        print("✅ Module imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Check environment variables or JSON file
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    # Try to load from JSON if environment variables not set
    if not api_key:
        try:
            import json

            with open("jibber_jaber_key.json", "r") as f:
                credentials = json.load(f)
            api_key = credentials.get("google_search_api_key")
            if api_key:
                print("✅ API key loaded from jibber_jaber_key.json")
            else:
                print("❌ No google_search_api_key found in jibber_jaber_key.json")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"❌ Could not load API key from JSON: {e}")
    else:
        print("✅ GOOGLE_SEARCH_API_KEY environment variable found")

    if not api_key:
        print(
            "❌ GOOGLE_SEARCH_API_KEY environment variable not set and not found in JSON"
        )
        print("💡 Run: export GOOGLE_SEARCH_API_KEY='your_api_key'")
        return False
    else:
        print(f"✅ API Key found: {'*' * (len(api_key) - 4)}{api_key[-4:]}")

    if not search_engine_id:
        print("❌ GOOGLE_SEARCH_ENGINE_ID environment variable not set")
        print("💡 Run: export GOOGLE_SEARCH_ENGINE_ID='your_search_engine_id'")
        return False
    else:
        print(f"✅ Search Engine ID found: {search_engine_id}")

    # Test API connection
    try:
        search_client = GoogleCustomSearch()
        print("✅ Client initialized successfully")

        # Test connection
        if search_client.test_connection():
            print("✅ API connection test passed!")

            # Test a simple search
            print("\n🔍 Testing simple search...")
            results = search_client.search("test search", num_results=3)

            if "items" in results:
                print(f"✅ Search successful! Found {len(results['items'])} results")
                for i, item in enumerate(results["items"][:2], 1):
                    print(f"   {i}. {item['title'][:50]}...")
            else:
                print("⚠️  Search returned no results (this might be normal)")

            return True
        else:
            print("❌ API connection test failed")
            return False

    except Exception as e:
        print(f"❌ Error testing API: {e}")
        return False


def test_dno_search():
    """
    Test DNO-specific search functionality
    """

    print("\n🏢 TESTING DNO SEARCH")
    print("=" * 30)

    try:
        from google_search_setup import GoogleCustomSearch

        search_client = GoogleCustomSearch()

        # Test searching for a specific DNO
        test_dno = "SSEN"
        print(f"🔍 Searching for {test_dno} data...")

        results = search_client.search_dno_data(
            dno_name=test_dno, data_types=["DUoS charges"]
        )

        if results:
            print(f"✅ Found {len(results)} potential data sources for {test_dno}")
            for result in results[:2]:  # Show first 2 results
                print(f"   • {result['title'][:60]}...")
                print(f"     URL: {result['url']}")
        else:
            print(f"⚠️  No results found for {test_dno} (this might be normal)")

        return True

    except Exception as e:
        print(f"❌ Error testing DNO search: {e}")
        return False


if __name__ == "__main__":
    success = test_google_search_api()

    if success:
        test_dno_search()
        print("\n🎉 All tests completed!")
        print("\n💡 Next steps:")
        print("   1. Run: python google_search_setup.py")
        print("   2. Use the search functions to find DNO data")
        print("   3. Integrate found data sources into your pipeline")
    else:
        print("\n❌ Setup incomplete. Please check the setup guide.")
        print("📖 See: GOOGLE_SEARCH_SETUP_GUIDE.md")
