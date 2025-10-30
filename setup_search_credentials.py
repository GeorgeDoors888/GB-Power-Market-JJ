#!/usr/bin/env python3
"""
Interactive Google Custom Search API Setup
"""


def main():
    print("🔧 GOOGLE CUSTOM SEARCH JSON API SETUP")
    print("=" * 50)
    print()

    print("📋 This setup will help you configure Google Custom Search API")
    print("   to find DNO (Distribution Network Operator) data sources.")
    print()

    print("🎯 What you'll be able to do:")
    print("   • Search for DNO DUoS charging data")
    print("   • Find distribution tariff documents")
    print("   • Discover connection charge information")
    print("   • Locate network data from the 11 missing DNOs")
    print()

    print("📋 Prerequisites:")
    print("   1. Google API Key with Custom Search JSON API enabled")
    print("   2. Custom Search Engine ID")
    print()

    response = input("Do you have these credentials ready? (y/n): ").lower().strip()

    if response == "y":
        print("\n✅ Great! Let's set up your API credentials...")

        # Get API credentials
        api_key = input("\n🔑 Enter your Google API Key: ").strip()
        search_engine_id = input("🔍 Enter your Custom Search Engine ID: ").strip()

        if api_key and search_engine_id:
            # Create environment file
            env_content = f"""# Google Custom Search JSON API Configuration
# Source this file: source .env.search
export GOOGLE_SEARCH_API_KEY="{api_key}"
export GOOGLE_SEARCH_ENGINE_ID="{search_engine_id}"
"""

            with open(".env.search", "w") as f:
                f.write(env_content)

            print("\n💾 Credentials saved to .env.search")
            print("\n🚀 To activate, run:")
            print("   source .env.search")
            print("\n🧪 To test, run:")
            print("   python test_google_search.py")
            print("\n🔍 To start searching for DNO data, run:")
            print("   python google_search_setup.py")

        else:
            print("❌ Please provide both API key and Search Engine ID")

    else:
        print("\n📖 Setup Guide:")
        print("=" * 30)
        print()
        print("🔗 Step 1: Get Google API Key")
        print("   1. Go to: https://console.developers.google.com/")
        print("   2. Create/select a project")
        print("   3. Enable 'Custom Search JSON API'")
        print("   4. Create credentials (API Key)")
        print()
        print("🔗 Step 2: Create Custom Search Engine")
        print("   1. Go to: https://cse.google.com/cse/")
        print("   2. Create a new search engine")
        print("   3. Add sites to search: *.gov.uk, *.co.uk")
        print("   4. Copy the Search Engine ID")
        print()
        print("📄 For detailed instructions, see:")
        print("   GOOGLE_SEARCH_SETUP_GUIDE.md")
        print()
        print("🔄 Run this script again when you have the credentials.")


if __name__ == "__main__":
    main()
