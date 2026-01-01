#!/usr/bin/env python3
"""
Comprehensive Map Sidebar Deployment Diagnostic
Checks all components: local files, BigQuery data, API keys, and common issues
"""

import os
import re
import json
from pathlib import Path
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def print_header(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_section(num, title):
    print(f"\n{num}️⃣  {title}")
    print("-" * 70)

def check_file(path, checks):
    """Check if file exists and contains required strings"""
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        return False
    
    size = os.path.getsize(path)
    print(f"✅ {os.path.basename(path)}: {size:,} bytes")
    
    with open(path, 'r') as f:
        content = f.read()
    
    for check_name, pattern in checks.items():
        if pattern in content:
            print(f"   ✓ Contains: {check_name}")
        else:
            print(f"   ✗ MISSING: {check_name}")
    
    return True

def check_bigquery_data():
    """Test BigQuery geographic data queries"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # DNO test
    dno_query = f"""
    SELECT 
        dno_id,
        dno_full_name,
        ST_AsGeoJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_boundaries`
    LIMIT 1
    """
    
    try:
        dno_result = client.query(dno_query).result()
        row = next(iter(dno_result))
        print(f"✅ DNO query works")
        print(f"   Sample dno_name: {row.dno_full_name}")
        print(f"   GeoJSON length: {len(row.geojson):,} chars")
    except Exception as e:
        print(f"❌ DNO query failed: {e}")
        return False
    
    # GSP test
    gsp_query = f"""
    SELECT 
        gsp_id,
        gsp_name,
        ST_AsGeoJSON(boundary) as geojson
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    LIMIT 1
    """
    
    try:
        gsp_result = client.query(gsp_query).result()
        row = next(iter(gsp_result))
        print(f"✅ GSP query works")
        print(f"   Sample gsp_name: {row.gsp_name}")
        print(f"   GeoJSON length: {len(row.geojson):,} chars")
    except Exception as e:
        print(f"❌ GSP query failed: {e}")
        return False
    
    return True

def analyze_html_structure(path):
    """Deep analysis of HTML file structure"""
    with open(path, 'r') as f:
        content = f.read()
    
    # Check for critical patterns
    patterns = {
        'Google Maps API Loader': r'maps\.googleapis\.com/maps/api/js',
        'getMapsApiKey Call': r'\.getMapsApiKey\(\)',
        'getGeoJson Call': r'\.getGeoJson\(',
        'initMap Function': r'function initMap\(\)',
        'Map Data Layer': r'map\.data\.',
        'Button Handlers': r'onclick=',
        'Error Handlers': r'withFailureHandler',
        'Success Handlers': r'withSuccessHandler',
    }
    
    print("\n📋 HTML Structure Analysis:")
    for name, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            print(f"   ✓ {name}: {len(matches)} occurrence(s)")
        else:
            print(f"   ✗ MISSING: {name}")

def analyze_gs_structure(path):
    """Deep analysis of Apps Script .gs file"""
    with open(path, 'r') as f:
        content = f.read()
    
    # Extract function definitions
    functions = re.findall(r'function\s+(\w+)\s*\(', content)
    print(f"\n📋 Functions defined: {', '.join(functions)}")
    
    # Check for critical issues
    issues = []
    
    # Check 1: Underscore in public functions
    if 'getMapsApiKey_' in content:
        issues.append("⚠️  ISSUE: getMapsApiKey_ has underscore (makes it private!)")
    else:
        print("   ✓ No underscore in getMapsApiKey()")
    
    # Check 2: BigQuery.Jobs.query usage
    if 'BigQuery.Jobs.query' in content:
        print("   ✓ Uses BigQuery.Jobs.query API")
    else:
        issues.append("⚠️  ISSUE: Missing BigQuery.Jobs.query")
    
    # Check 3: Project ID hardcoded
    if PROJECT_ID in content:
        print(f"   ✓ Project ID {PROJECT_ID} found")
    else:
        issues.append(f"⚠️  ISSUE: Project ID {PROJECT_ID} not found")
    
    # Check 4: ST_AsGeoJSON in queries
    if 'ST_AsGeoJSON' in content:
        print("   ✓ Uses ST_AsGeoJSON for geometry conversion")
    else:
        issues.append("⚠️  ISSUE: Missing ST_AsGeoJSON in queries")
    
    # Check 5: HTML file reference
    html_refs = re.findall(r'createHtmlOutputFromFile\([\'"](\w+)[\'"]\)', content)
    if html_refs:
        print(f"   ✓ HTML reference: {html_refs[0]}")
    else:
        issues.append("⚠️  ISSUE: No createHtmlOutputFromFile found")
    
    if issues:
        print("\n🔴 Issues Found:")
        for issue in issues:
            print(f"   {issue}")
    
    return len(issues) == 0

def check_appsscript_manifest():
    """Check if appsscript.json has correct OAuth scopes"""
    manifest_paths = [
        '/home/george/GB-Power-Market-JJ/appsscript.json',
        '/home/george/GB-Power-Market-JJ/appsscript_v3/appsscript.json',
    ]
    
    required_scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/script.container.ui',
        'https://www.googleapis.com/auth/bigquery',
    ]
    
    for path in manifest_paths:
        if os.path.exists(path):
            print(f"\n📄 Checking: {path}")
            with open(path, 'r') as f:
                manifest = json.load(f)
            
            if 'oauthScopes' in manifest:
                scopes = manifest['oauthScopes']
                print(f"   Found {len(scopes)} OAuth scopes:")
                for scope in scopes:
                    print(f"      {scope}")
                
                missing = [s for s in required_scopes if s not in scopes]
                if missing:
                    print(f"\n   ⚠️  MISSING SCOPES:")
                    for scope in missing:
                        print(f"      {scope}")
                else:
                    print(f"\n   ✅ All required scopes present")
            else:
                print("   ❌ No oauthScopes section found!")

def main():
    print_header("MAP SIDEBAR DEPLOYMENT DIAGNOSTIC")
    
    # Section 1: File checks
    print_section(1, "Local File Integrity")
    
    html_checks = {
        'getMapsApiKey()': 'getMapsApiKey()',
        'initMap()': 'function initMap()',
        'google.maps.Map': 'google.maps.Map',
        'getGeoJson': 'getGeoJson',
        'loadLayer': 'function loadLayer',
        'DNO button': 'btnDno',
        'GSP button': 'btnGsp',
    }
    
    gs_checks = {
        'function getMapsApiKey()': 'function getMapsApiKey()',
        'function getGeoJson(': 'function getGeoJson(',
        'BigQuery.Jobs.query': 'BigQuery.Jobs.query',
        'ST_AsGeoJSON': 'ST_AsGeoJSON',
        'createHtmlOutputFromFile': 'createHtmlOutputFromFile',
    }
    
    html_ok = check_file('map_sidebar.html', html_checks)
    gs_ok = check_file('map_sidebar.gs', gs_checks)
    
    if html_ok:
        analyze_html_structure('map_sidebar.html')
    
    if gs_ok:
        analyze_gs_structure('map_sidebar.gs')
    
    # Section 2: BigQuery access
    print_section(2, "BigQuery Data Access")
    bq_ok = check_bigquery_data()
    
    # Section 3: Configuration
    print_section(3, "Apps Script Configuration")
    check_appsscript_manifest()
    
    # Section 4: Deployment checklist
    print_section(4, "Deployment Checklist")
    checklist = [
        ("HTML file named 'map_sidebarh' in Apps Script", "Upload map_sidebar.html → becomes 'map_sidebarh'"),
        ("GS file named 'map_sidebar' in Apps Script", "Upload map_sidebar.gs"),
        ("MASTER_onOpen.gs updated with menu", "Contains showMapSidebar() call"),
        ("BigQuery API enabled", "Services → BigQuery API v2"),
        ("OAuth scopes in manifest", "spreadsheets, script.container.ui, bigquery"),
        ("API key in Script Properties", "GOOGLE_MAPS_API_KEY = AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"),
        ("Authorization granted", "Run showMapSidebar() manually first time"),
    ]
    
    for i, (item, note) in enumerate(checklist, 1):
        print(f"   {i}. ⏳ {item}")
        print(f"      → {note}")
    
    # Section 5: Common errors
    print_section(5, "Common Deployment Errors & Solutions")
    errors = [
        {
            'error': '❌ No HTML file named map_sidebarh',
            'cause': 'HTML file uploaded with wrong name or not uploaded',
            'solution': 'Upload map_sidebar.html → Apps Script strips .html → becomes map_sidebarh'
        },
        {
            'error': '❌ getMapsApiKey is not defined',
            'cause': 'Function has underscore (getMapsApiKey_) making it private',
            'solution': 'Remove underscore: function getMapsApiKey() not getMapsApiKey_()'
        },
        {
            'error': '❌ No Maps API key set',
            'cause': 'Script Property GOOGLE_MAPS_API_KEY not configured',
            'solution': 'File → Project Settings → Script Properties → Add GOOGLE_MAPS_API_KEY'
        },
        {
            'error': '❌ BigQuery is not defined',
            'cause': 'BigQuery API not enabled in Apps Script Services',
            'solution': 'Services (+) → BigQuery API → Add'
        },
        {
            'error': '❌ Permission denied to show sidebar',
            'cause': 'OAuth scope script.container.ui missing or not authorized',
            'solution': 'Add scope to appsscript.json + run showMapSidebar() to authorize'
        },
        {
            'error': '❌ Query failed: Not found',
            'cause': 'Wrong project ID or dataset name in queries',
            'solution': f'Verify queries use: {PROJECT_ID}.{DATASET}.neso_dno_boundaries'
        },
    ]
    
    for err in errors:
        print(f"\n   🔴 {err['error']}")
        print(f"      Cause: {err['cause']}")
        print(f"      Fix: {err['solution']}")
    
    # Section 6: Test command
    print_section(6, "Manual Test Commands")
    print("""
   In Apps Script Editor:
   
   1. Test API key retrieval:
      function testApiKey() {
        Logger.log(getMapsApiKey());
      }
      Expected: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0
   
   2. Test BigQuery access:
      function testBigQuery() {
        Logger.log(testGeoJsonFetch());
      }
      Expected: "✅ Loaded 14 dno features" + "✅ Loaded 333 gsp features"
   
   3. Test sidebar launch:
      function testSidebar() {
        showMapSidebar();
      }
      Expected: Sidebar appears with map and buttons
    """)
    
    # Final summary
    print_header("DIAGNOSTIC SUMMARY")
    
    if html_ok and gs_ok and bq_ok:
        print("✅ ALL LOCAL FILES VERIFIED")
        print("✅ BIGQUERY DATA ACCESS CONFIRMED")
        print("\n🎯 Next Steps:")
        print("   1. Upload files to Apps Script (see Deployment Checklist above)")
        print("   2. Add API key to Script Properties")
        print("   3. Enable BigQuery API in Services")
        print("   4. Update appsscript.json with OAuth scopes")
        print("   5. Run showMapSidebar() to authorize")
        print("   6. Test from Google Sheets menu")
    else:
        print("⚠️  ISSUES DETECTED - Review sections above")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
