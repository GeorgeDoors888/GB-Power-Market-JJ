#!/usr/bin/env python3
"""
Check if electricityproduction.uk has an API or bulk data download
"""

import requests
from bs4 import BeautifulSoup

print("🔍 Checking for faster data access options...\n")

# Check common API/data endpoints
endpoints_to_try = [
    "https://electricityproduction.uk/api/plants",
    "https://electricityproduction.uk/api/v1/plants",
    "https://electricityproduction.uk/data/plants.json",
    "https://electricityproduction.uk/data/plants.csv",
    "https://electricityproduction.uk/download",
    "https://electricityproduction.uk/export",
]

for endpoint in endpoints_to_try:
    try:
        response = requests.head(endpoint, timeout=5)
        if response.status_code in [200, 301, 302]:
            print(f"✅ Found: {endpoint} (Status: {response.status_code})")
    except:
        pass

# Check the main page for any download links
print("\n🔍 Checking main page for download links...")
try:
    response = requests.get("https://electricityproduction.uk/", timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for download/export/API links
    download_keywords = ['download', 'export', 'api', 'data', 'csv', 'json', 'bulk']
    
    for link in soup.find_all('a'):
        href = link.get('href', '')
        text = link.get_text().lower()
        
        if any(keyword in href.lower() or keyword in text for keyword in download_keywords):
            print(f"   Found link: {text[:50]} -> {href}")

except Exception as e:
    print(f"Error: {e}")

print("\n💡 Alternative: Since this is taking too long, we could:")
print("   1. Use existing NESO BMU data (469 sites)")
print("   2. Scrape just the table on each page (faster than individual plant pages)")
print("   3. Use the EIC database which might be available as bulk download")
print("   4. Compile top 100 manually from Wikipedia/known sources")
