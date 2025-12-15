#!/usr/bin/env python3
"""Diagnose DNO GeoChart data and test different formats"""
import gspread
from google.oauth2.service_account import Credentials
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_FILE = '/home/george/inner-cinema-credentials.json'
SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8'

creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
spreadsheet = client.open_by_key(SPREADSHEET_ID)
sheet = spreadsheet.worksheet('DNO')

# Read current data
current_data = sheet.get('A1:D15')
print("📋 CURRENT DATA IN SHEET:")
print("=" * 80)
for i, row in enumerate(current_data[:10]):
    print(f"Row {i+1}: {row}")

# Load GeoJSON to check actual data
with open('/home/george/GB-Power-Market-JJ/gb_power_map_deployment/dno_regions.geojson', 'r') as f:
    geojson = json.load(f)

print(f"\n📍 GEOJSON ANALYSIS:")
print("=" * 80)
print(f"Total features: {len(geojson['features'])}")
print("\nAll DNO properties:")
for i, f in enumerate(geojson['features'], 1):
    p = f['properties']
    print(f"\n{i}. MPAN {p.get('mpan_id', '?'):2d}: {p.get('dno_name', 'Unknown')}")
    print(f"   Area: {p.get('area', 'N/A')}")
    print(f"   GSP: {p.get('gsp_name', 'N/A')}")
    print(f"   Coverage: {p.get('coverage', 'N/A')}")
    print(f"   Area km²: {p.get('area_sqkm', 0):.0f}")

# Test different region formats
print(f"\n🧪 TESTING GOOGLE GEOCHART FORMATS:")
print("=" * 80)

# Format 1: Standard UK regions
test_data_1 = [
    ['Region'],
    ['England'],
    ['Scotland'],
    ['Wales'],
    ['Northern Ireland']
]

# Format 2: UK postcode areas
test_data_2 = [
    ['Region'],
    ['London'],
    ['South East'],
    ['Scotland'],
    ['Wales']
]

# Format 3: With values
test_data_3 = [
    ['Region', 'Value'],
    ['England', 100],
    ['Scotland', 80],
    ['Wales', 60]
]

# Write test formats to different columns
sheet.update(values=test_data_1, range_name='F1:F5')
sheet.update(values=test_data_2, range_name='H1:H5')
sheet.update(values=test_data_3, range_name='J1:K4')

print("✅ Written 3 test formats:")
print("  F1:F5 - Format 1: Countries")
print("  H1:H5 - Format 2: UK Regions")
print("  J1:K4 - Format 3: With Values")

print("\n📊 TEST EACH FORMAT:")
print("1. Try F1:F5 → Insert Chart → Geo chart → Region: United Kingdom")
print("2. Try H1:H5 → Insert Chart → Geo chart → Region: United Kingdom")
print("3. Try J1:K4 → Insert Chart → Geo chart → Region: United Kingdom")
print("\nWhichever works, we'll use that format for the DNO data!")
