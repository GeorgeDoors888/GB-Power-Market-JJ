"""
Test map sidebar integration - diagnose why map isn't loading
"""
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

print("�� DIAGNOSING MAP SIDEBAR ISSUE")
print("=" * 70)

# Test 1: Check if BigQuery tables exist and have data
print("\n1️⃣ Testing BigQuery Data Access")
print("-" * 70)

try:
    query_dno = f"""
    SELECT 
        dno_id,
        dno_full_name as dno_name,
        dno_code as dno_short_code,
        gsp_group as gsp_group_id,
        area_name as region_name,
        ST_AsGeoJSON(boundary) as geometry_json
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    WHERE boundary IS NOT NULL
    LIMIT 1
    """
    result = list(client.query(query_dno).result())
    if result:
        print("✅ DNO query works")
        print(f"   Sample dno_name: {result[0]['dno_name']}")
        geojson_len = len(result[0]['geometry_json']) if result[0]['geometry_json'] else 0
        print(f"   GeoJSON length: {geojson_len} chars")
    else:
        print("❌ DNO query returned no results")
except Exception as e:
    print(f"❌ DNO query failed: {e}")

try:
    query_gsp = f"""
    SELECT 
        gsp_id,
        gsp_name,
        gsp_group,
        region_name,
        area_sqkm,
        ST_AsGeoJSON(boundary) as geometry_json
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    WHERE boundary IS NOT NULL
    LIMIT 1
    """
    result = list(client.query(query_gsp).result())
    if result:
        print("✅ GSP query works")
        print(f"   Sample gsp_name: {result[0]['gsp_name']}")
        geojson_len = len(result[0]['geometry_json']) if result[0]['geometry_json'] else 0
        print(f"   GeoJSON length: {geojson_len} chars")
    else:
        print("❌ GSP query returned no results")
except Exception as e:
    print(f"❌ GSP query failed: {e}")

# Test 2: Check file structure
print("\n2️⃣ Checking Local Files")
print("-" * 70)

import os
files = {
    'map_sidebar.html': 'HTML template for sidebar',
    'map_sidebar.gs': 'Apps Script backend code',
    'MASTER_onOpen.gs': 'Menu integration'
}

for filename, desc in files.items():
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"✅ {filename}: {size} bytes ({desc})")
        
        # Check for critical strings
        with open(filename, 'r') as f:
            content = f.read()
            
        if filename == 'map_sidebar.html':
            checks = {
                'getMapsApiKey()': 'API key function call',
                'initMap()': 'Map initialization',
                'google.maps.Map': 'Google Maps object',
                'getGeoJson': 'BigQuery data fetch'
            }
            for check, desc in checks.items():
                if check in content:
                    print(f"   ✓ Contains: {check} ({desc})")
                else:
                    print(f"   ✗ MISSING: {check} ({desc})")
                    
        elif filename == 'map_sidebar.gs':
            checks = {
                'function getMapsApiKey()': 'Public API key function',
                'function getGeoJson(': 'GeoJSON fetch function',
                'BigQuery.Jobs.query': 'BigQuery API call',
                "createHtmlOutputFromFile('map_sidebarh')": 'Correct HTML filename'
            }
            for check, desc in checks.items():
                if check in content:
                    print(f"   ✓ Contains: {check} ({desc})")
                else:
                    print(f"   ✗ MISSING: {check} ({desc})")
    else:
        print(f"❌ {filename}: NOT FOUND")

# Test 3: Common issues checklist
print("\n3️⃣ Common Issues Checklist")
print("-" * 70)

issues = [
    ("Apps Script file named 'map_sidebarh' (HTML without .html extension)", "Apps Script strips .html extension"),
    ("getMapsApiKey() is public (no underscore)", "Private functions can't be called from HTML"),
    ("BigQuery API enabled in Apps Script Services", "Required for BigQuery.Jobs.query()"),
    ("OAuth scope 'script.container.ui' in appsscript.json", "Required for showSidebar()"),
    ("Script Property 'GOOGLE_MAPS_API_KEY' set", "API key: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"),
    ("Authorization granted for sidebar permissions", "Run showMapSidebar() manually first")
]

for issue, explanation in issues:
    print(f"⚠️  Check: {issue}")
    print(f"   Why: {explanation}")

print("\n4️⃣ Debugging Steps")
print("-" * 70)
print("1. Open Apps Script editor")
print("2. Run function: getMapsApiKey()")
print("3. Check Execution log - should show API key or warning")
print("4. Run function: testGeoJsonFetch()")
print("5. Check Execution log - should show '✅ Loaded 14 dno features'")
print("6. If functions work, open browser console in Sheets:")
print("   - F12 → Console tab")
print("   - Look for errors when clicking map button")
print("   - Check for 'getMapsApiKey is not defined' error")

print("\n5️⃣ Most Likely Issues")
print("-" * 70)
print("🔴 Issue 1: HTML file wrong name in Apps Script")
print("   Fix: Rename HTML file to 'map_sidebarh' (exactly, no .html)")
print("")
print("🔴 Issue 2: getMapsApiKey_ still has underscore")
print("   Fix: Remove underscore: function getMapsApiKey()")
print("")
print("�� Issue 3: API key not in Script Properties")
print("   Fix: File → Project Settings → Script Properties")
print("        Add: GOOGLE_MAPS_API_KEY = AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0")
print("")
print("🔴 Issue 4: BigQuery API not enabled")
print("   Fix: Services (+) → BigQuery API → Add")

print("\n" + "=" * 70)
print("Run these tests in Apps Script to see exact error messages!")
print("=" * 70)

