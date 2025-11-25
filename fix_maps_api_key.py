#!/usr/bin/env python3
"""
Fix Google Maps API Key Issues
Check current restrictions and provide fix options
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
CURRENT_API_KEY = "AIzaSyCsH49dmxEqcX0Hhi_UJGS8VvuGNLuggTQ"

def main():
    print("=" * 80)
    print("GOOGLE MAPS API KEY DIAGNOSTIC")
    print("=" * 80)
    
    print(f"\n📝 Current API Key: {CURRENT_API_KEY}")
    
    print("\n🔍 Common Issues:")
    print("   1. API key restricted to specific domains")
    print("   2. Maps JavaScript API not enabled")
    print("   3. Referrer restrictions blocking local file://")
    print("   4. Billing not enabled on GCP project")
    
    print("\n" + "=" * 80)
    print("SOLUTION 1: Remove All Restrictions (Testing)")
    print("=" * 80)
    print("\n1. Go to: https://console.cloud.google.com/apis/credentials")
    print(f"2. Find API key: {CURRENT_API_KEY}")
    print("3. Click 'Edit' (pencil icon)")
    print("4. Under 'Application restrictions': Select 'None'")
    print("5. Under 'API restrictions': Select 'Don't restrict key'")
    print("6. Click 'Save'")
    print("7. Wait 1-2 minutes for changes to propagate")
    
    print("\n" + "=" * 80)
    print("SOLUTION 2: Create New Unrestricted Key")
    print("=" * 80)
    print("\n1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click 'Create credentials' → 'API key'")
    print("3. Copy the new key")
    print("4. Don't add any restrictions (for testing)")
    print("5. Update the key in the Python script")
    
    print("\n" + "=" * 80)
    print("SOLUTION 3: Enable Required APIs")
    print("=" * 80)
    print("\n1. Go to: https://console.cloud.google.com/apis/library")
    print("2. Search for 'Maps JavaScript API'")
    print("3. Click 'Enable'")
    print("4. Also enable: 'Maps Embed API', 'Places API' (optional)")
    
    print("\n" + "=" * 80)
    print("SOLUTION 4: Check Billing")
    print("=" * 80)
    print("\n1. Go to: https://console.cloud.google.com/billing")
    print(f"2. Ensure project '{PROJECT_ID}' has billing enabled")
    print("3. Google Maps requires billing (but has free tier)")
    print("4. Free tier: $200/month credit = ~28,000 map loads")
    
    print("\n" + "=" * 80)
    print("TESTING THE FIX")
    print("=" * 80)
    print("\nAfter making changes:")
    print("   1. Wait 1-2 minutes")
    print("   2. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)")
    print("   3. Open: constraint_map_standalone.html")
    print("   4. Check browser console (F12) for errors")
    
    print("\n" + "=" * 80)
    print("ALTERNATIVE: Use Leaflet (No API Key Needed)")
    print("=" * 80)
    print("\nIf Google Maps continues to have issues:")
    print("   - Use OpenStreetMap with Leaflet library")
    print("   - No API key required")
    print("   - Free and open source")
    print("   - Run: python3 generate_constraint_map_leaflet.py")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
