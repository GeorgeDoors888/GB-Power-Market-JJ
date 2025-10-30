#!/usr/bin/env python3
"""
Google Custom Search API Activation Helper
==========================================

This script opens the correct Google Cloud Console page to enable
the Custom Search API for your jibber-jabber-knowledge project.
"""

import sys
import webbrowser


def main():
    """Open the API activation page."""

    project_id = "1090450657636"  # Your project number from the error
    api_url = f"https://console.developers.google.com/apis/api/customsearch.googleapis.com/overview?project={project_id}"

    print("🔧 Google Custom Search API Activation")
    print("=" * 45)
    print(f"\n📋 Steps to complete setup:")
    print(f"1. Click the link below (or copy to browser)")
    print(f"2. Click 'ENABLE' on the Custom Search API page")
    print(f"3. Wait 2-3 minutes for activation")
    print(f"4. Re-run: python setup_google_search.py")

    print(f"\n🔗 API Activation URL:")
    print(f"{api_url}")

    try:
        user_input = input(f"\n🌐 Open in browser? (y/n): ").strip().lower()
        if user_input in ["y", "yes", ""]:
            print("🚀 Opening browser...")
            webbrowser.open(api_url)
            print("✅ Opened in browser!")
        else:
            print("💡 Copy the URL above to activate manually")

        print(f"\n⏱️ After enabling, wait 2-3 minutes then test with:")
        print(f"   python setup_google_search.py")

    except KeyboardInterrupt:
        print(f"\n📋 Manual activation URL:")
        print(f"{api_url}")


if __name__ == "__main__":
    main()
