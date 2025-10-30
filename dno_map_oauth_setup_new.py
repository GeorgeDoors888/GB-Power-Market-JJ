#!/usr/bin/env python3
"""
DNO Map OAuth Setup Script - Enhanced Version

This script handles OAuth 2.0 authentication and creates a Google Sheet
with an interactive map of UK Distribution Network Operators (DNOs).

The script:
1. Authenticates with Google using OAuth 2.0
2. Creates or updates a Google Sheet with DNO data
3. Creates an Apps Script project with map visualization
4. Embeds GeoJSON data directly in the Apps Script
"""

import os
import json
import pickle
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes required for API access
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.deployments'
]

# Path to GeoJSON file with DNO license areas
GEOJSON_FILE = 'system_regulatory/gis/merged_geojson.geojson'

# Sample DNO data - replace with actual data source if available
DNO_DATA = [
    {'id': 'EELC', 'name': 'UK Power Networks (EPN)', 'value': 12500},
    {'id': 'EMEB', 'name': 'Western Power Distribution (East Midlands)', 'value': 13200},
    {'id': 'HYDE', 'name': 'Electricity North West', 'value': 9800},
    {'id': 'LOND', 'name': 'UK Power Networks (LPN)', 'value': 15800},
    {'id': 'MANW', 'name': 'SP Energy Networks (MANWEB)', 'value': 10200},
    {'id': 'NEEB', 'name': 'Northern Powergrid (Northeast)', 'value': 8900},
    {'id': 'SOUT', 'name': 'Scottish & Southern Electricity Networks (South)', 'value': 14300},
    {'id': 'SWAE', 'name': 'Western Power Distribution (South Wales)', 'value': 9500},
    {'id': 'SWEB', 'name': 'Western Power Distribution (South West)', 'value': 11200},
    {'id': 'YEDL', 'name': 'Northern Powergrid (Yorkshire)', 'value': 12100},
    {'id': 'SEEB', 'name': 'UK Power Networks (SPN)', 'value': 13800},
    {'id': 'SPMW', 'name': 'SP Energy Networks (SPD)', 'value': 10900},
    {'id': 'HECO', 'name': 'Scottish & Southern Electricity Networks (North)', 'value': 8500},
    {'id': 'WSEB', 'name': 'Western Power Distribution (West Midlands)', 'value': 12800}
]

def main():
    """Main function to run the setup process."""
    print("="*64)
    print("="*32 + " DNO MAP SETUP WITH OAUTH 2.0 AUTHENTICATION")
    print("="*64)
    
    # ----- Step 1: Authenticate with Google APIs -----
    credentials = authenticate()
    
    # ----- Step 2: Initialize API services -----
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        apps_script_service = build('script', 'v1', credentials=credentials)
        print("API clients initialized successfully")
    except Exception as e:
        print(f"Error initializing API clients: {e}")
        return
    
    # ----- Step 3: Create or update spreadsheet -----
    spreadsheet_id = create_or_update_spreadsheet(sheets_service, drive_service)
    if not spreadsheet_id:
        print("Failed to create or update spreadsheet.")
        return
    
    # ----- Step 4: Load GeoJSON data -----
    geojson_data = load_geojson()
    if not geojson_data:
        print("Failed to load GeoJSON data.")
        return
    
    # ----- Step 5: Create or update Apps Script project -----
    script_id = create_apps_script_project(drive_service, apps_script_service, spreadsheet_id)
    
    # ----- Step 6: Update spreadsheet with DNO data -----
    update_spreadsheet_data(sheets_service, spreadsheet_id)
    
    # ----- Step 7: Generate Apps Script code with embedded GeoJSON -----
    geojson_str = json.dumps(geojson_data)
    
    # ----- Step 8: Create Apps Script files content -----
    
    # Manifest file (appsscript.json)
    manifest_content = """{
  "timeZone": "Etc/GMT",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}"""

    # Code.gs file with embedded GeoJSON
    code_gs_content = f"""
    /**
     * UK DNO Map Visualization
     * 
     * This script creates an interactive map of UK Distribution Network Operators (DNOs).
     * The GeoJSON data is embedded directly in the script, eliminating the need for external storage.
     */
    
    // The GeoJSON data is embedded directly in the script
    const GEOJSON_DATA = {geojson_str};
    
    // Create the menu when the spreadsheet opens
    function onOpen() {{
      const ui = SpreadsheetApp.getUi();
      ui.createMenu('Energy Maps')
        .addItem('Show DNO Map', 'showDNOMap')
        .addToUi();
    }}
    
    // Prepare the data for the map
    function prepareMapData() {{
      // Get DNO data from the spreadsheet
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO_Data');
      const data = sheet.getDataRange().getValues();
      
      // Convert to an array of objects for easier handling in the map
      const headers = data[0];
      const result = [];
      
      for (let i = 1; i < data.length; i++) {{
        const row = data[i];
        const item = {{}};
        
        for (let j = 0; j < headers.length; j++) {{
          item[headers[j].toLowerCase()] = row[j];
        }}
        
        result.push(item);
      }}
      
      return result;
    }}
    
    // Show the DNO map dialog
    function showDNOMap() {{
      const data = prepareMapData();
      
      // Check if mapView HTML file exists
      try {{
        const template = HtmlService.createTemplateFromFile('mapView');
        template.data = data;
        
        const html = template.evaluate()
          .setWidth(800)
          .setHeight(600);
          
        SpreadsheetApp.getUi().showModalDialog(html, 'UK DNO Map');
      }} catch (error) {{
        // If mapView not found, create a simple error dialog
        console.error("Error loading mapView:", error);
        const htmlContent = '<div style="text-align:center; padding:20px;"><h3>Error: Could not load map</h3><p>The mapView HTML file was not found. Please contact the administrator.</p></div>';
        
        const html = HtmlService.createHtmlOutput(htmlContent)
          .setWidth(400)
          .setHeight(300);
          
        SpreadsheetApp.getUi().showModalDialog(html, 'Map Error');
      }}
    }}
    """
    
    # mapView.html file - the map visualization
    map_view_html_content = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>UK DNO Map</title>
  <!-- Load Leaflet CSS and JS -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
  <style>
    body, html {
      margin: 0;
      padding: 0;
      height: 100%;
      width: 100%;
      font-family: Arial, sans-serif;
    }
    
    #map-container {
      position: relative;
      height: 580px;
      width: 100%;
    }
    
    #map {
      height: 100%;
      width: 100%;
    }
    
    #loading {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 1000;
      background: white;
      padding: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0,0,0,0.2);
    }
    
    #error {
      display: none;
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 1000;
      background: white;
      padding: 20px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0,0,0,0.2);
      color: red;
    }
    
    #debug {
      position: fixed;
      bottom: 10px;
      right: 10px;
      background: rgba(255, 255, 255, 0.9);
      padding: 10px;
      border-radius: 5px;
      box-shadow: 0 0 10px rgba(0,0,0,0.2);
      max-height: 200px;
      overflow-y: auto;
      width: 300px;
      font-size: 12px;
      z-index: 999;
      display: none;
    }
    
    .info {
      padding: 6px 8px;
      font: 14px/16px Arial, sans-serif;
      background: white;
      background: rgba(255,255,255,0.8);
      box-shadow: 0 0 15px rgba(0,0,0,0.2);
      border-radius: 5px;
      min-width: 250px;
    }
    
    .info h4 {
      margin: 0 0 5px;
      color: #777;
    }
    
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
    
    /* Control buttons at bottom */
    #controls {
      text-align: center;
      margin-top: 10px;
    }
    
    button {
      padding: 8px 12px;
      margin: 0 5px;
      background: #4285f4;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    
    button:hover {
      background: #3367d6;
    }
  </style>
</head>
<body>
  <div id="map-container">
    <div id="map"></div>
    <div id="loading">Loading map data...</div>
    <div id="error"></div>
    <div id="debug"></div>
  </div>
  
  <div id="controls">
    <button onclick="focusOnGB()">Center on GB</button>
    <button onclick="reloadMap()">Reload Map</button>
    <button onclick="toggleDebug()">Toggle Debug</button>
  </div>
  
  <script>
    // Global variables
    var map = null;
    var geojsonLayer = null;
    var debugEnabled = false;
    var logs = [];
    
    // Debug logging
    function log(message) {
      console.log(message);
      var timestamp = new Date().toLocaleTimeString();
      logs.push("[" + timestamp + "] " + message);
      
      // Limit log size
      if (logs.length > 100) logs.shift();
      
      // Update debug panel if visible
      if (debugEnabled) {
        updateDebugPanel();
      }
    }
    
    // Update debug panel
    function updateDebugPanel() {
      var debugDiv = document.getElementById('debug');
      debugDiv.innerHTML = logs.join('<br>');
      debugDiv.scrollTop = debugDiv.scrollHeight;
    }
    
    // Toggle debug panel
    function toggleDebug() {
      debugEnabled = !debugEnabled;
      var debugDiv = document.getElementById('debug');
      debugDiv.style.display = debugEnabled ? 'block' : 'none';
      
      if (debugEnabled) {
        updateDebugPanel();
        log("Debug panel enabled");
      }
    }
    
    // Show error
    function showError(message) {
      var errorDiv = document.getElementById('error');
      errorDiv.innerHTML = "<strong>Error:</strong> " + message;
      errorDiv.style.display = 'block';
      document.getElementById('loading').style.display = 'none';
      log("ERROR: " + message);
    }
    
    // Center map on Great Britain
    function focusOnGB() {
      if (!map) {
        showError("Map not initialized");
        return;
      }
      
      try {
        var gbBounds = L.latLngBounds(
          [49.8, -8.0],  // Southwest
          [60.9, 2.0]    // Northeast
        );
        map.fitBounds(gbBounds);
        log("Map centered on GB");
      } catch (e) {
        showError("Error focusing on GB: " + e.message);
      }
    }
    
    // Reload the map
    function reloadMap() {
      try {
        if (map) {
          map.remove();
          log("Map removed");
        }
        
        document.getElementById('error').style.display = 'none';
        document.getElementById('loading').style.display = 'block';
        
        // Slight delay before reinitializing
        setTimeout(initializeMap, 500);
      } catch (e) {
        showError("Error reloading map: " + e.message);
      }
    }
    
    // Initialize the map
    function initializeMap() {
      try {
        log("Map initialization started");
        
        // Check for map container
        var mapContainer = document.getElementById('map');
        if (!mapContainer) {
          throw new Error("Map container element not found");
        }
        
        log("Map container found: " + mapContainer.clientWidth + "x" + mapContainer.clientHeight);
        
        // Create the map with explicit center on GB
        map = L.map('map', {
          center: [54.5, -2.5],  // GB center
          zoom: 6,
          minZoom: 5,
          maxZoom: 11
        });
        
        log("Map object created");
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        log("Base tile layer added");
        
        // Get the data from the script
        var dnoData = <?= JSON.stringify(data) ?>;
        log("DNO data loaded: " + dnoData.length + " items");
        
        // Create a lookup object for DNO data
        var dnoLookup = {};
        dnoData.forEach(function(row) {
          if (row && row.id) {
            dnoLookup[row.id] = {
              name: row.name || "Unknown",
              value: row.value || 0
            };
          }
        });
        
        log("DNO lookup table created");
        
        // Get GeoJSON data
        var geojsonData;
        try {
          geojsonData = <?= JSON.stringify(GEOJSON_DATA) ?>;
          
          if (!geojsonData || !geojsonData.features) {
            throw new Error("Invalid GeoJSON data structure");
          }
          
          log("GeoJSON data loaded: " + geojsonData.features.length + " features");
        } catch (e) {
          throw new Error("Failed to load GeoJSON data: " + e.message);
        }
        
        // Helper functions for GeoJSON styling
        function getColor(value) {
          return value > 15000 ? '#800026' :
                 value > 14000 ? '#BD0026' :
                 value > 13000 ? '#E31A1C' :
                 value > 12000 ? '#FC4E2A' :
                 value > 11000 ? '#FD8D3C' :
                 value > 10000 ? '#FEB24C' :
                 value > 9000 ? '#FED976' : 
                               '#FFEDA0';
        }
        
        function style(feature) {
          try {
            // Check for properties
            if (!feature || !feature.properties) {
              log("WARNING: Feature missing properties");
              return {
                fillColor: '#ccc',
                weight: 2,
                opacity: 1,
                color: 'white',
                dashArray: '3',
                fillOpacity: 0.7
              };
            }
            
            // Get ID from various possible property names
            var dnoId = feature.properties.id || 
                        feature.properties.ID || 
                        feature.properties.dno_id || 
                        feature.properties.DNO_ID;
            
            // Look up in DNO data
            var dno = dnoLookup[dnoId];
            var value = dno ? Number(dno.value) : 0;
            
            return {
              fillColor: getColor(value),
              weight: 2,
              opacity: 1,
              color: 'white',
              dashArray: '3',
              fillOpacity: 0.7
            };
          } catch (e) {
            log("Error in style function: " + e.message);
            return {
              fillColor: '#999',
              weight: 2,
              opacity: 1,
              color: 'white',
              dashArray: '3',
              fillOpacity: 0.7
            };
          }
        }
        
        // Info control
        var info = L.control();
        info.onAdd = function(map) {
          this._div = L.DomUtil.create('div', 'info');
          this.update();
          return this._div;
        };
        
        info.update = function(props) {
          var dnoId = props ? (props.id || props.ID || props.dno_id || props.DNO_ID) : null;
          var dno = dnoId ? dnoLookup[dnoId] : null;
          
          this._div.innerHTML = '<h4>UK DNO License Areas</h4>' + 
            (props ? 
              '<b>' + (dno ? dno.name : props.name || 'Unknown') + '</b><br>' +
              'Value: ' + (dno ? dno.value : 'N/A') + '<br>' +
              'ID: ' + dnoId
              : 'Hover over an area');
        };
        
        info.addTo(map);
        log("Info control added");
        
        // Legend control
        var legend = L.control({position: 'bottomright'});
        legend.onAdd = function(map) {
          var div = L.DomUtil.create('div', 'info legend');
          var grades = [0, 9000, 10000, 11000, 12000, 13000, 14000, 15000];
          
          div.innerHTML = '<h4>Value</h4>';
          
          for (var i = 0; i < grades.length; i++) {
            div.innerHTML +=
              '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
              grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
          }
          
          return div;
        };
        
        legend.addTo(map);
        log("Legend control added");
        
        // Add a simple test feature first to verify map is working
        try {
          var testFeature = {
            "type": "Feature",
            "properties": {"name": "Test Feature"},
            "geometry": {
              "type": "Polygon",
              "coordinates": [[[-4, 52], [-3, 52], [-3, 53], [-4, 53], [-4, 52]]]
            }
          };
          
          L.geoJSON(testFeature, {
            style: {
              fillColor: 'blue',
              weight: 2,
              opacity: 0.7,
              color: 'white',
              fillOpacity: 0.5
            }
          }).addTo(map);
          
          log("Test GeoJSON feature added successfully");
        } catch (e) {
          log("Error adding test feature: " + e.message);
        }
        
        // Interaction functions
        function highlightFeature(e) {
          var layer = e.target;
          
          layer.setStyle({
            weight: 5,
            color: '#666',
            dashArray: '',
            fillOpacity: 0.7
          });
          
          layer.bringToFront();
          info.update(layer.feature.properties);
        }
        
        function resetHighlight(e) {
          geojsonLayer.resetStyle(e.target);
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
        
        // Now add the main GeoJSON layer
        try {
          log("Creating main GeoJSON layer");
          
          geojsonLayer = L.geoJSON(geojsonData, {
            style: style,
            onEachFeature: onEachFeature
          }).addTo(map);
          
          log("Main GeoJSON layer added");
          
          // Fit map to bounds with a slight delay
          setTimeout(function() {
            try {
              var bounds = geojsonLayer.getBounds();
              map.fitBounds(bounds, {
                padding: [20, 20],
                maxZoom: 7,
                animate: true
              });
              
              log("Map fitted to GeoJSON bounds");
              
              // Force a map refresh
              map.invalidateSize();
              
              // Hide loading indicator
              document.getElementById('loading').style.display = 'none';
              
              log("Map initialization complete");
            } catch (e) {
              showError("Error fitting bounds: " + e.message);
            }
          }, 1000);
        } catch (e) {
          showError("Error creating GeoJSON layer: " + e.message);
        }
      } catch (e) {
        showError("Map initialization failed: " + e.message);
      }
    }
    
    // Start map initialization when window loads
    window.onload = function() {
      log("Window loaded");
      setTimeout(initializeMap, 500);
      
      // Check container visibility and dimensions
      var visibilityCheck = setInterval(function() {
        var mapContainer = document.getElementById('map');
        if (mapContainer && mapContainer.clientWidth > 0 && mapContainer.clientHeight > 0) {
          log("Map container visible: " + mapContainer.clientWidth + "x" + mapContainer.clientHeight);
          if (map) {
            map.invalidateSize();
            log("Map size invalidated");
          }
          clearInterval(visibilityCheck);
        }
      }, 500);
    };
  </script>
</body>
</html>"""
    
    # ----- Step 9: Upload Apps Script code if possible -----
    if script_id != "MANUAL_SETUP_REQUIRED":
        try:
            # Update the Apps Script project content with the code files
            content = {
                "files": [
                    {"name": "appsscript", "type": "JSON", "source": manifest_content},
                    {"name": "Code", "type": "SERVER_JS", "source": code_gs_content},
                    {"name": "mapView", "type": "HTML", "source": map_view_html_content},
                ]
            }
            
            apps_script_service.projects().updateContent(
                scriptId=script_id, body=content
            ).execute()
            
            # Verify the project has all required files by getting its content
            project_content = apps_script_service.projects().getContent(scriptId=script_id).execute()
            files = project_content.get('files', [])
            file_names = [f.get('name') for f in files]
            
            print("Verified Apps Script files:", ", ".join(file_names))
            print("Uploaded Apps Script code successfully\n")
        except Exception as e:
            print(f"Error uploading Apps Script code: {e}")
            print("You may need to manually create the Apps Script project and add the files.")
    
    # ----- Step 10: Display completion message and instructions -----
    print("="*64)
    print("="*32 + " SETUP COMPLETE!")
    print("="*64)
    print("\nGoogle Sheet URL: https://docs.google.com/spreadsheets/d/" + spreadsheet_id)
    print("Apps Script Project ID:", script_id)
    
    if script_id != "MANUAL_SETUP_REQUIRED":
        print("Apps Script Editor URL: https://script.google.com/d/" + script_id + "/edit")
    
    print("\nInstructions:")
    print("1. Open the Google Sheet using the URL above")
    print("2. Wait for the Apps Script to initialize (this may take a moment)")
    print("3. Refresh the page if needed")
    print("4. Click on 'Energy Maps > Show DNO Map' to view the DNO map")
    print("\nNote: You might need to authorize the script to access your Google Sheet")

def authenticate():
    """Authenticate with Google using OAuth 2.0."""
    print("Loading credentials from token.pickle")
    credentials = None
    
    # Check for saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    
    # If credentials are invalid or don't exist, authenticate
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Use client_secrets.json for OAuth flow
            if not os.path.exists('client_secrets.json'):
                print("Error: client_secrets.json not found. Please download this file from Google Cloud Console.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    
    print(f"Successfully authenticated as: {credentials.client_id}")
    return credentials

def create_or_update_spreadsheet(sheets_service, drive_service):
    """Create or update a Google Sheet for DNO data."""
    # Check if spreadsheet ID is stored in a file
    spreadsheet_id = None
    if os.path.exists('spreadsheet_id.txt'):
        with open('spreadsheet_id.txt', 'r') as f:
            spreadsheet_id = f.read().strip()
    
    # If no stored ID, create a new spreadsheet
    if not spreadsheet_id:
        try:
            # Create a new spreadsheet
            spreadsheet = {
                'properties': {
                    'title': 'UK DNO Map Data'
                },
                'sheets': [
                    {
                        'properties': {
                            'title': 'DNO_Data'
                        }
                    }
                ]
            }
            
            result = sheets_service.spreadsheets().create(body=spreadsheet).execute()
            spreadsheet_id = result['spreadsheetId']
            
            # Save the ID for future use
            with open('spreadsheet_id.txt', 'w') as f:
                f.write(spreadsheet_id)
            
            print(f"Created new spreadsheet with ID: {spreadsheet_id}")
        except Exception as e:
            print(f"Error creating spreadsheet: {e}")
            return None
    else:
        # Verify the spreadsheet exists and we have access
        try:
            sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            print(f"Using spreadsheet with ID: {spreadsheet_id}")
        except Exception as e:
            print(f"Error accessing existing spreadsheet: {e}")
            return None
    
    # Get the spreadsheet URL
    try:
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        print(f"Spreadsheet URL: {spreadsheet_url}")
    except Exception as e:
        print(f"Error getting spreadsheet URL: {e}")
    
    # Check if DNO_Data sheet exists, create if not
    try:
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        
        dno_sheet_exists = False
        for sheet in sheets:
            if sheet['properties']['title'] == 'DNO_Data':
                dno_sheet_exists = True
                break
        
        if not dno_sheet_exists:
            request = {
                'addSheet': {
                    'properties': {
                        'title': 'DNO_Data'
                    }
                }
            }
            
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            
            print("Created 'DNO_Data' sheet")
        else:
            print("'DNO_Data' sheet already exists")
    except Exception as e:
        print(f"Error checking/creating DNO_Data sheet: {e}")
    
    return spreadsheet_id

def update_spreadsheet_data(sheets_service, spreadsheet_id):
    """Update the spreadsheet with DNO data."""
    try:
        print("Updating Google Sheet with DNO data...")
        
        # Prepare the data
        values = [['ID', 'Name', 'Value']]  # Header row
        for dno in DNO_DATA:
            values.append([dno['id'], dno['name'], dno['value']])
        
        # Clear existing data
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range='DNO_Data!A1:Z1000'  # Clear a large range to ensure all data is removed
        ).execute()
        
        # Update with new data
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='DNO_Data!A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        print("Updated Google Sheet with DNO data")
    except Exception as e:
        print(f"Error updating spreadsheet data: {e}")

def create_apps_script_project(drive_service, apps_script_service, spreadsheet_id):
    """Create an Apps Script project for the spreadsheet."""
    # Check if script ID is stored in a file
    script_id = None
    if os.path.exists('script_id.txt'):
        with open('script_id.txt', 'r') as f:
            script_id = f.read().strip()
    
    # If no stored ID, create a new Apps Script project
    if not script_id:
        try:
            print("Creating Apps Script project...")
            
            # Create a new Apps Script project
            request = {
                'title': 'UK DNO Map',
                'parentId': spreadsheet_id
            }
            
            response = apps_script_service.projects().create(body=request).execute()
            script_id = response['scriptId']
            
            # Save the ID for future use
            with open('script_id.txt', 'w') as f:
                f.write(script_id)
            
            print(f"Created Apps Script project with ID: {script_id}")
        except Exception as e:
            print(f"Error creating Apps Script project: {e}")
            print("You'll need to manually create the Apps Script project.")
            return "MANUAL_SETUP_REQUIRED"
    else:
        # Verify the script exists and we have access
        try:
            apps_script_service.projects().get(scriptId=script_id).execute()
            print(f"Using existing Apps Script project with ID: {script_id}")
        except Exception as e:
            print(f"Error accessing existing Apps Script project: {e}")
            print("You'll need to manually create the Apps Script project.")
            return "MANUAL_SETUP_REQUIRED"
    
    return script_id

def load_geojson():
    """Load GeoJSON data from file."""
    try:
        print(f"Reading GeoJSON file: {GEOJSON_FILE}")
        with open(GEOJSON_FILE, 'r') as f:
            geojson_data = json.load(f)
        
        print(f"GeoJSON data loaded: {len(json.dumps(geojson_data))} characters")
        return geojson_data
    except Exception as e:
        print(f"Error loading GeoJSON file: {e}")
        return None

if __name__ == "__main__":
    main()
