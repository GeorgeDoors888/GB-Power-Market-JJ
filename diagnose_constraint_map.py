#!/usr/bin/env python3
"""
Diagnose Constraint Map Issues
Uses Google Sheets API and Apps Script API to test the map integration
"""

import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import sys

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # Dashboard sheet
DASHBOARD_SHEET = "Dashboard"
DATA_RANGE = "A116:H126"

def main():
    print("=" * 80)
    print("CONSTRAINT MAP DIAGNOSTIC")
    print("=" * 80)
    
    # Load credentials
    try:
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/script.projects'
            ]
        )
        print("✅ Credentials loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load credentials: {e}")
        return 1
    
    # Test 1: Check Google Sheets API access
    print("\n" + "=" * 80)
    print("TEST 1: Google Sheets API - Read Dashboard Data")
    print("=" * 80)
    
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{DASHBOARD_SHEET}!{DATA_RANGE}"
        ).execute()
        
        values = result.get('values', [])
        print(f"✅ Successfully read {len(values)} rows from Dashboard sheet")
        
        if not values:
            print("❌ ERROR: No data found in range A116:H126!")
            return 1
        
        # Analyze the data
        print(f"\n📊 Data Analysis:")
        print(f"   Total rows: {len(values)}")
        print(f"   Header row: {values[0]}")
        
        constraint_count = 0
        missing_coords = []
        
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 0 and row[0]:
                constraint_count += 1
                boundary_id = row[0]
                name = row[1] if len(row) > 1 else "Unknown"
                util_pct = row[4] if len(row) > 4 else "N/A"
                
                print(f"   Row {i}: {boundary_id} - {name} ({util_pct})")
                
                # Check if lat/lng columns exist
                if len(row) < 9:
                    missing_coords.append(boundary_id)
        
        print(f"\n✅ Found {constraint_count} constraints")
        
        if missing_coords:
            print(f"\n⚠️  WARNING: Constraints missing lat/lng columns:")
            print(f"   Sheet has {len(values[0])} columns, but needs 9+ for lat/lng")
            print(f"   Missing coordinates for: {', '.join(missing_coords[:5])}")
            print(f"\n   SOLUTION: Add lat/lng columns (I or J) to Dashboard sheet")
        
    except Exception as e:
        print(f"❌ Sheets API error: {e}")
        return 1
    
    # Test 2: Simulate Apps Script getConstraintData()
    print("\n" + "=" * 80)
    print("TEST 2: Simulate Apps Script getConstraintData()")
    print("=" * 80)
    
    try:
        # Boundary coordinate lookup (same as Apps Script should use)
        boundary_coords = {
            'B6': {'lat': 55.5, 'lng': -3.0},
            'B7': {'lat': 54.5, 'lng': -2.5},
            'SC1': {'lat': 53.5, 'lng': -1.5},
            'B7a': {'lat': 54.2, 'lng': -2.8},
            'B8': {'lat': 54.8, 'lng': -3.2},
            'EC5': {'lat': 52.5, 'lng': 1.0},
            'LE1': {'lat': 51.5, 'lng': 0.0},
            'B4': {'lat': 56.0, 'lng': -3.5},
            'B2': {'lat': 57.0, 'lng': -3.0},
            'B1': {'lat': 57.5, 'lng': -2.5},
        }
        
        constraints = []
        for i, row in enumerate(values[1:], start=1):
            if len(row) > 0 and row[0]:
                boundary_id = str(row[0])
                coords = boundary_coords.get(boundary_id, {'lat': None, 'lng': None})
                
                constraint = {
                    'boundary_id': boundary_id,
                    'name': str(row[1] if len(row) > 1 else 'Unknown'),
                    'flow_mw': float(row[2]) if len(row) > 2 and row[2] else 0,
                    'limit_mw': float(row[3]) if len(row) > 3 and row[3] else 0,
                    'util_pct': parse_percent(row[4]) if len(row) > 4 else 0,
                    'margin_mw': float(row[5]) if len(row) > 5 and row[5] else 0,
                    'status': str(row[6] if len(row) > 6 else 'Unknown'),
                    'direction': str(row[7] if len(row) > 7 else 'N/A'),
                    'lat': coords['lat'],
                    'lng': coords['lng']
                }
                constraints.append(constraint)
        
        print(f"✅ Simulated Apps Script returned {len(constraints)} constraints")
        
        # Check for missing coordinates
        with_coords = [c for c in constraints if c['lat'] and c['lng']]
        without_coords = [c for c in constraints if not c['lat'] or not c['lng']]
        
        print(f"   {len(with_coords)} constraints WITH coordinates")
        print(f"   {len(without_coords)} constraints WITHOUT coordinates")
        
        if without_coords:
            print(f"\n⚠️  Constraints missing coordinates:")
            for c in without_coords:
                print(f"      {c['boundary_id']} - {c['name']}")
        
        # Show sample constraint
        if with_coords:
            print(f"\n📍 Sample constraint with coordinates:")
            sample = with_coords[0]
            print(f"   {json.dumps(sample, indent=4)}")
        
        # Save to file for inspection
        output_file = "constraint_map_test_data.json"
        with open(output_file, 'w') as f:
            json.dump(constraints, f, indent=2)
        print(f"\n💾 Full data saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 3: Check Apps Script deployment
    print("\n" + "=" * 80)
    print("TEST 3: Apps Script Deployment Check")
    print("=" * 80)
    
    print("ℹ️  Manual checks required:")
    print("   1. Go to Apps Script editor")
    print("   2. Run function: testMapData()")
    print("   3. Check logs for: 'Retrieved X constraints'")
    print("   4. Verify each constraint has lat/lng properties")
    
    # Summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    
    if without_coords:
        print("❌ ISSUE FOUND: Apps Script not returning lat/lng")
        print("\n🔧 FIX:")
        print("   1. Update constraint_map.gs with coordinate lookup table")
        print("   2. Add lat/lng to each constraint object in getConstraintData()")
        print("   3. Redeploy Apps Script")
        print("\n   See: constraint_map_fix.gs for updated code")
        
        # Generate fix
        generate_apps_script_fix(boundary_coords)
    else:
        print("✅ All constraints have coordinates")
        print("   If map still blank, check:")
        print("   - Browser console for JS errors")
        print("   - Google Maps API key restrictions")
        print("   - Apps Script execution permissions")
    
    return 0

def parse_percent(value):
    """Parse percentage value"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return float(value.replace('%', '')) if value else 0
    return 0

def generate_apps_script_fix(boundary_coords):
    """Generate fixed Apps Script code"""
    fix_code = '''// ============================================================================
// UPDATED getConstraintData() with coordinate lookup
// ============================================================================

function getConstraintData() {
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName('Dashboard');
    if (!dashboard) {
      throw new Error('Dashboard sheet not found');
    }
    
    // Read boundary data from rows 116-126
    const boundaryData = dashboard.getRange('A116:H126').getValues();
    
    // Coordinate lookup for each boundary
    const boundaryCoords = {
'''
    
    for bid, coords in boundary_coords.items():
        fix_code += f"      '{bid}': {{lat: {coords['lat']}, lng: {coords['lng']}}},\n"
    
    fix_code += '''    };
    
    // Helper functions
    function parsePercent(value) {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') {
        return parseFloat(value.replace('%', '')) || 0;
      }
      return 0;
    }
    
    function parseNumber(value) {
      if (typeof value === 'number') return value;
      return parseFloat(value) || 0;
    }
    
    const constraints = [];
    for (let i = 1; i < boundaryData.length; i++) {
      const boundaryId = String(boundaryData[i][0]);
      if (boundaryId) {
        const coords = boundaryCoords[boundaryId] || {lat: null, lng: null};
        constraints.push({
          boundary_id: boundaryId,
          name: String(boundaryData[i][1] || 'Unknown'),
          flow_mw: parseNumber(boundaryData[i][2]),
          limit_mw: parseNumber(boundaryData[i][3]),
          util_pct: parsePercent(boundaryData[i][4]),
          margin_mw: parseNumber(boundaryData[i][5]),
          status: String(boundaryData[i][6] || 'Unknown'),
          direction: String(boundaryData[i][7] || 'N/A'),
          lat: coords.lat,
          lng: coords.lng
        });
      }
    }
    
    Logger.log('Retrieved ' + constraints.length + ' constraints');
    return constraints;
    
  } catch (error) {
    Logger.log('Error in getConstraintData: ' + error.toString());
    throw new Error('Failed to load data: ' + error.message);
  }
}
'''
    
    with open('constraint_map_fix.gs', 'w') as f:
        f.write(fix_code)
    print(f"   📝 Generated: constraint_map_fix.gs")

if __name__ == '__main__':
    sys.exit(main())
