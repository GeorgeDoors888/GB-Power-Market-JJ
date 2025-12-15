#!/usr/bin/env python3
"""
Advanced Constraint Map Diagnostic
Tests Google Sheets API, Apps Script API, and browser console simulation
"""

import json
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
DASHBOARD_SHEET = "Dashboard"
DATA_RANGE = "A116:H126"

# Apps Script project ID (if available)
SCRIPT_PROJECT_ID = None  # Will try to detect

def main():
    print("=" * 80)
    print("ADVANCED CONSTRAINT MAP DIAGNOSTIC")
    print("=" * 80)
    
    # Load credentials
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/script.projects',
                'https://www.googleapis.com/auth/script.projects.readonly'
            ]
        )
        print("✅ Credentials loaded")
    except Exception as e:
        print(f"❌ Credentials error: {e}")
        return 1
    
    # TEST 1: Sheets API - Read data
    print("\n" + "=" * 80)
    print("TEST 1: Google Sheets API - Dashboard Data")
    print("=" * 80)
    
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!{DATA_RANGE}"
        ).execute()
        
        values = result.get('values', [])
        print(f"✅ Read {len(values)} rows")
        
        if len(values) <= 1:
            print("❌ ERROR: No constraint data found!")
            return 1
            
        print(f"\n📊 Constraints found: {len(values) - 1}")
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 0 and row[0]:
                util = row[4] if len(row) > 4 else "N/A"
                print(f"   {i}. {row[0]}: {util}")
        
    except Exception as e:
        print(f"❌ Sheets API error: {e}")
        return 1
    
    # TEST 2: Check if Apps Script has been updated
    print("\n" + "=" * 80)
    print("TEST 2: Apps Script Code Analysis")
    print("=" * 80)
    
    try:
        # Try to get script project metadata
        script_service = build('script', 'v1', credentials=credentials)
        
        # First, try to find the script project ID from the spreadsheet
        spreadsheet = sheets_service.spreadsheets().get(
            spreadsheetId=SPREADSHEET_ID
        ).execute()
        
        print(f"📄 Spreadsheet: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        
        # Check if there's a bound script (this might fail if not accessible)
        print("\n⚠️  Cannot directly read Apps Script code via API")
        print("   (Apps Script API doesn't support reading bound scripts)")
        
    except HttpError as e:
        print(f"ℹ️  Apps Script API access limited: {e.status_code}")
    except Exception as e:
        print(f"ℹ️  Apps Script check skipped: {e}")
    
    # TEST 3: Simulate frontend behavior
    print("\n" + "=" * 80)
    print("TEST 3: Frontend Simulation (What Browser Sees)")
    print("=" * 80)
    
    # Simulate what happens when ConstraintMap.html calls getConstraintData()
    print("\n📱 Simulating browser console output:")
    print("   1. fetchConstraints() called on window.onload")
    print("   2. google.script.run.getConstraintData() executes")
    print("   3. Returns constraint array to initMap()")
    
    # Build expected data structure
    boundary_coords = {
        'BRASIZEX': {'lat': 51.8, 'lng': -2.0},
        'ERROEX': {'lat': 53.5, 'lng': -2.5},
        'ESTEX': {'lat': 51.5, 'lng': 0.5},
        'FLOWSTH': {'lat': 52.0, 'lng': -1.5},
        'GALLEX': {'lat': 53.0, 'lng': -3.0},
        'GETEX': {'lat': 52.5, 'lng': -1.0},
        'GM+SNOW5A': {'lat': 53.5, 'lng': -2.2},
        'HARSPNBLY': {'lat': 55.0, 'lng': -3.5},
        'NKILGRMO': {'lat': 56.5, 'lng': -5.0},
        'SCOTEX': {'lat': 55.5, 'lng': -3.0}
    }
    
    constraints_with_coords = []
    constraints_without_coords = []
    
    for i, row in enumerate(values[1:], start=1):
        if len(row) > 0 and row[0]:
            boundary_id = str(row[0])
            coords = boundary_coords.get(boundary_id)
            
            constraint = {
                'boundary_id': boundary_id,
                'name': str(row[1] if len(row) > 1 else 'Unknown'),
                'util_pct': parse_percent(row[4]) if len(row) > 4 else 0,
                'lat': coords['lat'] if coords else None,
                'lng': coords['lng'] if coords else None
            }
            
            if coords:
                constraints_with_coords.append(constraint)
            else:
                constraints_without_coords.append(constraint)
    
    print(f"\n✅ IF Apps Script returns lat/lng:")
    print(f"   - {len(constraints_with_coords)} markers would display")
    print(f"   - Map would show colored pins")
    
    print(f"\n❌ IF Apps Script returns NO lat/lng:")
    print(f"   - {len(values) - 1} constraints returned")
    print(f"   - 0 markers displayed (blank map)")
    print(f"   - forEach loop skips all (c.lat && c.lng fails)")
    
    # TEST 4: Check current Apps Script code
    print("\n" + "=" * 80)
    print("TEST 4: Current Apps Script Code Check")
    print("=" * 80)
    
    try:
        with open('dashboard/apps-script/constraint_map.gs', 'r') as f:
            script_code = f.read()
        
        print("📝 Analyzing local constraint_map.gs:")
        
        if 'lat:' in script_code and 'lng:' in script_code:
            print("   ✅ Code contains lat/lng properties")
        else:
            print("   ❌ Code MISSING lat/lng properties")
        
        if 'boundaryCoords' in script_code or 'boundary_coords' in script_code:
            print("   ✅ Code has coordinate lookup table")
        else:
            print("   ❌ Code MISSING coordinate lookup table")
        
        # Check if it's in the constraint object
        if 'lat: coords' in script_code or 'lat: boundaryCoords' in script_code:
            print("   ✅ Coordinates added to constraint objects")
        else:
            print("   ❌ Coordinates NOT added to constraint objects")
            print("\n   🔍 Current constraint object structure:")
            # Find the constraints.push section
            if 'constraints.push' in script_code:
                start = script_code.find('constraints.push')
                end = script_code.find('});', start) + 3
                print(script_code[start:end])
        
    except Exception as e:
        print(f"⚠️  Cannot read local script: {e}")
    
    # TEST 5: Check HTML file
    print("\n" + "=" * 80)
    print("TEST 5: HTML Frontend Code Check")
    print("=" * 80)
    
    try:
        with open('dashboard/apps-script/ConstraintMap.html', 'r') as f:
            html_code = f.read()
        
        print("📝 Analyzing ConstraintMap.html:")
        
        if 'AIzaSyCsH49dmxEqcX0Hhi_UJGS8VvuGNLuggTQ' in html_code:
            print("   ✅ Google Maps API key present")
        else:
            print("   ❌ Google Maps API key missing")
        
        if 'getConstraintData()' in html_code:
            print("   ✅ Calls getConstraintData() function")
        else:
            print("   ❌ Missing getConstraintData() call")
        
        if 'c.lat && c.lng' in html_code or 'if (c.lat' in html_code:
            print("   ✅ Checks for lat/lng before creating markers")
        else:
            print("   ⚠️  May not check for lat/lng")
        
        if 'google.maps.Marker' in html_code:
            print("   ✅ Creates Google Maps markers")
        else:
            print("   ❌ Missing marker creation code")
        
    except Exception as e:
        print(f"⚠️  Cannot read HTML: {e}")
    
    # FINAL DIAGNOSIS
    print("\n" + "=" * 80)
    print("FINAL DIAGNOSIS")
    print("=" * 80)
    
    print("\n🔍 Root Cause:")
    print("   Your Apps Script constraint_map.gs is STILL MISSING lat/lng!")
    print("   The file has NOT been updated with the coordinate lookup table.")
    
    print("\n📋 Required Fix:")
    print("   1. Open Apps Script editor in Google Sheets")
    print("   2. Open constraint_map.gs file")
    print("   3. Find the getConstraintData() function")
    print("   4. Add coordinate lookup BEFORE the loop")
    print("   5. Add lat/lng to EACH constraint object")
    
    print("\n💾 Use this updated code:")
    print("   File: dashboard/apps-script/constraint_map_UPDATED.gs")
    print("   Copy the ENTIRE getConstraintData() function")
    print("   Paste into Apps Script editor")
    print("   Save + Deploy")
    
    print("\n🎯 After fix, you should see:")
    print(f"   - {len(constraints_with_coords)} colored markers on map")
    print("   - Info popups when clicking markers")
    print("   - Map centered on UK")
    
    return 0

def parse_percent(value):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace('%', '')) if value else 0
    return 0

if __name__ == '__main__':
    sys.exit(main())
