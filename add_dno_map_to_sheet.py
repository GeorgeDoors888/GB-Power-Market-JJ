#!/usr/bin/env python3
"""
Add DNO Map to Google Sheet
Creates an interactive map visualization of UK DNO license areas in the DNO sheet
"""

import json
import gspread
from google.oauth2.service_account import Credentials

# Configuration
SHEET_ID = '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I'
GEOJSON_FILE = 'uk_dno_license_areas.geojson'

def load_geojson():
    """Load DNO regions from GeoJSON file"""
    with open(GEOJSON_FILE, 'r') as f:
        return json.load(f)

def create_dno_table(geojson_data):
    """Extract DNO information into a table format"""
    rows = [['DNO Name', 'Company', 'Region', 'Customers', 'Area (km²)', 'License']]
    
    for feature in geojson_data['features']:
        props = feature['properties']
        rows.append([
            props.get('dno_name', ''),
            props.get('company', ''),
            props.get('region', ''),
            props.get('customers', 0),
            props.get('area_sqkm', 0),
            props.get('license', '')
        ])
    
    return rows

def create_apps_script_map():
    """Generate Apps Script code for interactive DNO map"""
    return '''
function createDNOMap() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO');
  if (!sheet) {
    sheet = SpreadsheetApp.getActiveSpreadsheet().insertSheet('DNO');
  }
  
  // Create HTML map
  var html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>UK DNO License Areas</title>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; padding: 0; }
    #map { height: 100vh; width: 100%; }
    .info {
      padding: 6px 8px;
      font: 14px/16px Arial, Helvetica, sans-serif;
      background: white;
      background: rgba(255,255,255,0.9);
      box-shadow: 0 0 15px rgba(0,0,0,0.2);
      border-radius: 5px;
    }
    .info h4 { margin: 0 0 5px; color: #777; }
    .legend {
      line-height: 18px;
      color: #555;
    }
    .legend i {
      width: 18px;
      height: 18px;
      float: left;
      margin-right: 8px;
      opacity: 0.7;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    // UK DNO GeoJSON data
    var dnoData = ` + getGeoJSONData() + `;
    
    // Initialize map centered on UK
    var map = L.map('map').setView([54.5, -3], 6);
    
    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);
    
    // Color scheme for different DNOs
    function getColor(dno) {
      var colors = {
        'EPN': '#FF6B6B',
        'LPN': '#4ECDC4',
        'SPN': '#45B7D1',
        'WM': '#96CEB4',
        'EM': '#FFEAA7',
        'SW': '#DFE6E9',
        'WA': '#A29BFE',
        'NW': '#FD79A8',
        'NE': '#FDCB6E',
        'Y': '#6C5CE7',
        'SHEPD': '#74B9FF',
        'HYDRO': '#00B894',
        'SP': '#FFA07A',
        'NPG': '#E17055'
      };
      return colors[dno] || '#95A5A6';
    }
    
    // Style function
    function style(feature) {
      return {
        fillColor: getColor(feature.properties.license),
        weight: 2,
        opacity: 1,
        color: 'white',
        dashArray: '3',
        fillOpacity: 0.7
      };
    }
    
    // Highlight feature on hover
    function highlightFeature(e) {
      var layer = e.target;
      layer.setStyle({
        weight: 5,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.9
      });
      layer.bringToFront();
      info.update(layer.feature.properties);
    }
    
    function resetHighlight(e) {
      geojson.resetStyle(e.target);
      info.update();
    }
    
    function zoomToFeature(e) {
      map.fitBounds(e.target.getBounds());
    }
    
    function onEachFeature(feature, layer) {
      layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: zoomToFeature
      });
    }
    
    // Add GeoJSON layer
    var geojson = L.geoJson(dnoData, {
      style: style,
      onEachFeature: onEachFeature
    }).addTo(map);
    
    // Info control
    var info = L.control();
    
    info.onAdd = function (map) {
      this._div = L.DomUtil.create('div', 'info');
      this.update();
      return this._div;
    };
    
    info.update = function (props) {
      this._div.innerHTML = '<h4>UK DNO License Areas</h4>' +  (props ?
        '<b>' + props.dno_name + '</b><br />' +
        'Company: ' + props.company + '<br />' +
        'Region: ' + props.region + '<br />' +
        'Customers: ' + (props.customers / 1000000).toFixed(1) + 'M<br />' +
        'Area: ' + props.area_sqkm.toLocaleString() + ' km²'
        : 'Hover over a region');
    };
    
    info.addTo(map);
    
    // Legend
    var legend = L.control({position: 'bottomright'});
    
    legend.onAdd = function (map) {
      var div = L.DomUtil.create('div', 'info legend');
      var licenses = ['EPN', 'LPN', 'SPN', 'WM', 'EM', 'SW', 'WA', 'NW'];
      
      div.innerHTML = '<h4>License Areas</h4>';
      for (var i = 0; i < licenses.length; i++) {
        div.innerHTML +=
          '<i style="background:' + getColor(licenses[i]) + '"></i> ' +
          licenses[i] + '<br>';
      }
      return div;
    };
    
    legend.addTo(map);
  </script>
</body>
</html>
  `)
  .setWidth(1200)
  .setHeight(800);
  
  SpreadsheetApp.getUi().showModalDialog(html, 'UK DNO License Areas Map');
}

function getGeoJSONData() {
  // Return GeoJSON data as string
  return JSON.stringify(` + open('uk_dno_license_areas.geojson').read() + `);
}

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ DNO Map')
      .addItem('View Interactive Map', 'createDNOMap')
      .addToUi();
}
'''

def main():
    print("🗺️  Adding DNO Map to Google Sheet...")
    print("=" * 80)
    
    # Load GeoJSON data
    print("\n📂 Loading GeoJSON data...")
    geojson_data = load_geojson()
    print(f"   ✅ Loaded {len(geojson_data['features'])} DNO regions")
    
    # Create DNO table
    print("\n📊 Creating DNO reference table...")
    table_data = create_dno_table(geojson_data)
    print(f"   ✅ Created table with {len(table_data)} rows")
    
    # Authenticate with Google Sheets
    print("\n🔐 Authenticating...")
    import os
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    
    # Try to find credentials file
    cred_paths = [
        'inner-cinema-credentials.json',
        os.path.expanduser('~/inner-cinema-credentials.json'),
        os.path.expanduser('~/.config/gcloud/inner-cinema-credentials.json')
    ]
    
    creds_file = None
    for path in cred_paths:
        if os.path.exists(path):
            creds_file = path
            break
    
    if not creds_file:
        print("   ⚠️  Credentials file not found. Generating Apps Script code only...")
        # Generate Apps Script code even without credentials
        script_code = create_apps_script_map()
        with open('dno_map_apps_script.gs', 'w') as f:
            f.write(script_code)
        print("\n💾 Apps Script code saved to: dno_map_apps_script.gs")
        print("\n📋 MANUAL STEPS TO ADD MAP:")
        print("=" * 80)
        print("\n1. Open spreadsheet: https://docs.google.com/spreadsheets/d/" + SHEET_ID)
        print("\n2. Create a sheet named 'DNO' if it doesn't exist")
        print("\n3. Go to: Extensions → Apps Script")
        print("\n4. Paste the content from dno_map_apps_script.gs")
        print("\n5. Save and refresh spreadsheet")
        print("\n6. New menu: 🗺️ DNO Map → View Interactive Map")
        return
    
    creds = Credentials.from_service_account_file(creds_file, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Open spreadsheet
    print(f"\n📝 Opening spreadsheet {SHEET_ID}...")
    spreadsheet = client.open_by_key(SHEET_ID)
    
    # Get or create DNO sheet
    try:
        sheet = spreadsheet.worksheet('DNO')
        print("   ✅ Found existing DNO sheet")
    except:
        sheet = spreadsheet.add_worksheet(title='DNO', rows=100, cols=20)
        print("   ✅ Created new DNO sheet")
    
    # Write table data
    print("\n✍️  Writing DNO reference table...")
    sheet.clear()
    sheet.update(range_name='A1', values=table_data)
    print(f"   ✅ Wrote {len(table_data)} rows to sheet")
    
    # Format header
    print("\n🎨 Formatting sheet...")
    sheet.format('A1:F1', {
        'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.5},
        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format header row
    print("\n🎨 Formatting sheet...")
    from gspread_formatting import set_column_width
    
    # Set column widths
    set_column_width(sheet, 'A', 200)  # DNO Name
    set_column_width(sheet, 'B', 180)  # Company
    set_column_width(sheet, 'C', 100)  # License
    set_column_width(sheet, 'D', 150)  # Region
    set_column_width(sheet, 'E', 120)  # Customers
    set_column_width(sheet, 'F', 120)  # Area
    
    print("   ✅ Formatting complete")
    
    # Add Apps Script instructions
    print("\n" + "=" * 80)
    print("📋 TO ADD INTERACTIVE MAP:")
    print("=" * 80)
    print("\n1. Open spreadsheet: https://docs.google.com/spreadsheets/d/" + SHEET_ID)
    print("\n2. Go to: Extensions → Apps Script")
    print("\n3. Replace Code.gs content with the generated code")
    print("\n4. Save and refresh spreadsheet")
    print("\n5. New menu: 🗺️ DNO Map → View Interactive Map")
    print("\n" + "=" * 80)
    
    # Save Apps Script code to file
    script_code = create_apps_script_map()
    with open('dno_map_apps_script.gs', 'w') as f:
        f.write(script_code)
    print("\n💾 Apps Script code saved to: dno_map_apps_script.gs")
    
    print("\n✅ DNO sheet setup complete!")
    print(f"\n🔗 View sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={sheet.id}")

if __name__ == '__main__':
    main()
