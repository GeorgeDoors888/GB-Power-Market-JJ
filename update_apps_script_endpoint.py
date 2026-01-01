#!/usr/bin/env python3
"""
Update Apps Script API_ENDPOINT with ngrok public URL
Reads search_interface.gs and updates the API_ENDPOINT constant
"""

import re
import sys

def update_endpoint(ngrok_url):
    """Update API_ENDPOINT in search_interface.gs"""
    
    file_path = 'search_interface.gs'
    
    # Ensure URL ends with /search
    if not ngrok_url.endswith('/search'):
        if ngrok_url.endswith('/'):
            ngrok_url = ngrok_url + 'search'
        else:
            ngrok_url = ngrok_url + '/search'
    
    # Read file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace API_ENDPOINT line
    pattern = r"var API_ENDPOINT = '[^']*';"
    replacement = f"var API_ENDPOINT = '{ngrok_url}';"
    
    new_content = re.sub(pattern, replacement, content)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated API_ENDPOINT to: {ngrok_url}")
    print(f"\n📋 Next steps:")
    print(f"1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
    print(f"2. Go to Extensions > Apps Script")
    print(f"3. Replace Code.gs with updated search_interface.gs")
    print(f"4. Save (Ctrl+S) and refresh spreadsheet")
    print(f"5. Click Search button → Should auto-execute! ✨")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python3 update_apps_script_endpoint.py <ngrok_url>")
        print("Example: python3 update_apps_script_endpoint.py https://abc123.ngrok.io")
        sys.exit(1)
    
    ngrok_url = sys.argv[1]
    update_endpoint(ngrok_url)
