import json
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# ----- Configuration -----
# Path to the client secrets file downloaded from Google Cloud Console
CLIENT_SECRETS_FILE = "client_secrets.json"
# The OAuth 2.0 scopes needed for the application
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/script.projects",
]
# Path to store the OAuth token
TOKEN_FILE = "token.pickle"
# Path to GeoJSON file
GEOJSON_FILE_PATH = "system_regulatory/gis/merged_geojson.geojson"
# Existing spreadsheet ID
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"


def get_credentials():
    """Get valid user credentials from storage or initiate OAuth 2.0 flow."""
    credentials = None

    # Try to load credentials from token.pickle
    if os.path.exists(TOKEN_FILE):
        print(f"Loading credentials from {TOKEN_FILE}")
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)

    # If credentials don't exist or are invalid, trigger OAuth flow
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("Refreshing expired credentials")
            credentials.refresh(Request())
        else:
            print("No valid credentials found. Starting OAuth 2.0 flow...")
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"ERROR: {CLIENT_SECRETS_FILE} not found.")
                print(
                    "Please download the OAuth client secrets file from Google Cloud Console:"
                )
                print("1. Go to https://console.cloud.google.com/apis/credentials")
                print("2. Create an OAuth client ID (Application type: Desktop app)")
                print("3. Download the JSON and save it as 'client_secrets.json'")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save the credentials for future use
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
            print(f"Credentials saved to {TOKEN_FILE}")

    return credentials


def main():
    """Main function to set up the DNO map with OAuth authentication."""
    print("=" * 80)
    print("DNO MAP SETUP WITH OAUTH 2.0 AUTHENTICATION")
    print("=" * 80)

    # ----- Step 1: Get OAuth credentials -----
    credentials = get_credentials()
    if not credentials:
        print("Failed to obtain credentials. Exiting.")
        return

    print(f"Successfully authenticated as: {credentials.client_id}")

    # ----- Step 2: Initialize API clients -----
    sheets_service = build("sheets", "v4", credentials=credentials)
    drive_service = build("drive", "v3", credentials=credentials)
    apps_script_service = build("script", "v1", credentials=credentials)

    print("API clients initialized successfully")

    # ----- Step 3: Prepare the Google Sheet -----
    print(f"Using spreadsheet with ID: {SPREADSHEET_ID}")
    print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

    # Check if DNO_Data sheet exists, create it if not
    try:
        sheet_metadata = (
            sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        )
        sheets = sheet_metadata.get("sheets", "")
        sheet_exists = False
        for sheet in sheets:
            if sheet.get("properties", {}).get("title", "") == "DNO_Data":
                sheet_exists = True
                break

        if not sheet_exists:
            # Add DNO_Data sheet
            request = {"addSheet": {"properties": {"title": "DNO_Data"}}}
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID, body={"requests": [request]}
            ).execute()
            print("Created 'DNO_Data' sheet")
        else:
            print("'DNO_Data' sheet already exists")
    except Exception as e:
        print(f"Error checking/creating sheet: {e}")
        print("Please ensure the spreadsheet exists and you have access to it")
        return

    # ----- Step 4: Prepare GeoJSON data for embedding -----
    try:
        print(f"Reading GeoJSON file: {GEOJSON_FILE_PATH}")
        with open(GEOJSON_FILE_PATH, "r") as f:
            geojson_data = json.load(f)

        # Convert to JSON string for embedding
        geojson_str = json.dumps(geojson_data)
        print(f"GeoJSON data loaded: {len(geojson_str)} characters")
    except Exception as e:
        print(f"Error loading GeoJSON file: {e}")
        print("Please ensure the GeoJSON file exists at the specified path")
        return

    # ----- Step 5: Prepare DNO data -----
    # Sample DNO data - replace with your actual data source if available
    dno_data = [
        ["ID", "Name", "Value"],
        ["1", "Northern Powergrid - Northeast", "12500"],
        ["2", "Northern Powergrid - Yorkshire", "13200"],
        ["3", "UK Power Networks - London", "16800"],
        ["4", "UK Power Networks - South East", "14300"],
        ["5", "UK Power Networks - East", "11700"],
        ["6", "Western Power Distribution - East Midlands", "12900"],
        ["7", "Western Power Distribution - West Midlands", "13500"],
        ["8", "Western Power Distribution - South West", "10800"],
        ["9", "Western Power Distribution - South Wales", "11200"],
        ["10", "Scottish and Southern Energy - Scottish Hydro", "9800"],
        ["11", "Scottish and Southern Energy - Southern", "13700"],
        ["12", "SP Energy Networks - Distribution", "12300"],
        ["13", "SP Energy Networks - Manweb", "11500"],
        ["14", "Electricity North West", "12100"],
    ]

    # ----- Step 6: Update Google Sheet with DNO data -----
    try:
        print("Updating Google Sheet with DNO data...")
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="DNO_Data!A1",
            valueInputOption="RAW",
            body={"values": dno_data},
        ).execute()
        print("Updated Google Sheet with DNO data")
    except Exception as e:
        print(f"Error updating sheet with DNO data: {e}")
        print("Please ensure you have write access to the spreadsheet")
        return

    # ----- Step 7: Create Apps Script project -----
    try:
        print("Creating Apps Script project...")
        script_metadata = {"title": "DNO Map Visualization", "parentId": SPREADSHEET_ID}
        script_project = (
            apps_script_service.projects().create(body=script_metadata).execute()
        )
        script_id = script_project["scriptId"]
        print(f"Created Apps Script project with ID: {script_id}")
    except Exception as e:
        print(f"Error creating Apps Script project: {e}")
        print("Trying to use existing Apps Script project if available...")

        try:
            # List existing projects to find one attached to the spreadsheet
            projects = apps_script_service.projects().list().execute()
            found_project = None

            if "scriptApps" in projects:
                for project in projects.get("scriptApps", []):
                    if "parentId" in project and project["parentId"] == SPREADSHEET_ID:
                        found_project = project
                        break

            if found_project:
                script_id = found_project["scriptId"]
                print(f"Using existing Apps Script project with ID: {script_id}")
            else:
                # Create a standalone project as fallback
                script_metadata = {"title": "DNO Map Visualization (Standalone)"}
                script_project = (
                    apps_script_service.projects()
                    .create(body=script_metadata)
                    .execute()
                )
                script_id = script_project["scriptId"]
                print(f"Created standalone Apps Script project with ID: {script_id}")
                print(
                    "NOTE: You'll need to manually connect this script to your spreadsheet."
                )
        except Exception as e2:
            print(f"Error accessing or creating Apps Script projects: {e2}")
            print("Generating local files for manual setup...")
            script_id = "MANUAL_SETUP_REQUIRED"

    # ----- Step 8: Prepare Apps Script code -----
    # Create a manifest file (appsscript.json) - required for API uploads
    manifest_content = """{
  "timeZone": "Europe/London",
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
      <!-- Load Leaflet from CDN with specific version to ensure reliability -->
      <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.css" />
      <script src="https://cdn.jsdelivr.net/npm/leaflet@1.7.1/dist/leaflet.js"></script>
      <style>
        html, body {
          margin: 0;
          padding: 0;
          height: 100%;
          width: 100%;
        }
        #map-container {
          position: relative;
          height: 500px;
          width: 100%;
          border: 1px solid #ccc;
        }
        #map {
          position: absolute;
          top: 0;
          bottom: 0;
          left: 0;
          right: 0;
          height: 100%;
          width: 100%;
          z-index: 1;
        }
        #error-message {
          display: none;
          color: red;
          background-color: #ffe6e6;
          padding: 10px;
          margin: 10px 0;
          border: 1px solid red;
          border-radius: 4px;
        }
        #loading {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          z-index: 1000;
          background-color: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        #debug-info {
          position: fixed;
          bottom: 10px;
          right: 10px;
          background: rgba(255,255,255,0.9);
          border: 1px solid #ccc;
          padding: 10px;
          max-height: 200px;
          overflow-y: auto;
          width: 300px;
          font-size: 12px;
          z-index: 1000;
          display: none;
        }
        .info {
          padding: 6px 8px;
          font: 14px/16px Arial, Helvetica, sans-serif;
          background: white;
          background: rgba(255,255,255,0.8);
          box-shadow: 0 0 15px rgba(0,0,0,0.2);
          border-radius: 5px;
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
      </style>
    </head>
    <body>
      <div id="map-container">
        <div id="map"></div>
        <div id="loading">Loading map, please wait...</div>
      </div>
      <div id="error-message"></div>
      <div id="debug-info"></div>

      <!-- Control buttons -->
      <div style="text-align: center; margin-top: 10px;">
        <button onclick="focusOnGB()" style="padding: 5px 10px;">Center on Great Britain</button>
        <button onclick="reloadMap()" style="padding: 5px 10px;">Reload Map</button>
        <button onclick="toggleDebug()" style="padding: 5px 10px;">Toggle Debug</button>
      </div>

      <script>
        // Global variables
        var map, geojsonLayer;
        var debugEnabled = false;
        var logs = [];

        // Debug logging function
        function debugLog(message) {
          var now = new Date();
          var timestamp = now.toLocaleTimeString();
          var logMessage = '[' + timestamp + '] ' + message;

          // Store in logs array
          logs.push(logMessage);

          // Keep only the last 100 logs
          if (logs.length > 100) {
            logs.shift();
          }

          // Log to console always
          console.log(message);

          // Update debug panel if visible
          if (debugEnabled) {
            updateDebugPanel();
          }
        }

        // Update the debug panel with all logs
        function updateDebugPanel() {
          var debugPanel = document.getElementById('debug-info');
          debugPanel.innerHTML = '<h4>Debug Log</h4>';
          for (var i = 0; i < logs.length; i++) {
            debugPanel.innerHTML += '<div>' + logs[i] + '</div>';
          }
          debugPanel.scrollTop = debugPanel.scrollHeight;
        }

        // Toggle debug panel visibility
        function toggleDebug() {
          debugEnabled = !debugEnabled;
          var debugPanel = document.getElementById('debug-info');
          debugPanel.style.display = debugEnabled ? 'block' : 'none';

          if (debugEnabled) {
            updateDebugPanel();
            debugLog('Debug panel enabled');
          }
        }

        // Helper function to show error messages
        function showError(message) {
          var errorDiv = document.getElementById('error-message');
          errorDiv.textContent = message;
          errorDiv.style.display = 'block';

          // Also log to debug
          debugLog('ERROR: ' + message);

          // Hide loading indicator
          document.getElementById('loading').style.display = 'none';
        }
          border: 1px solid red;
          border-radius: 4px;
        }
        #loading {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          z-index: 1000;
          background-color: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 0 10px rgba(0,0,0,0.2);
        }
        .info {
          padding: 6px 8px;
          font: 14px/16px Arial, Helvetica, sans-serif;
          background: white;
          background: rgba(255,255,255,0.8);
          box-shadow: 0 0 15px rgba(0,0,0,0.2);
          border-radius: 5px;
        }
        .info h4 {
          margin: 0 0 5px;
          color: #777;
        }
        .legend {
          line-height: 18px;
          color: #555;
        }
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
      <div id="loading">Loading map, please wait...</div>
      <div id="error-message"></div>
      <div id="map"></div>
      <div id="debug-panel" style="display:none;"></div>

      <!-- Control buttons -->
      <div style="text-align: center; margin-top: 10px;">
        <button onclick="focusOnGB()" style="padding: 5px 10px;">Center on Great Britain</button>
        <button onclick="reloadMap()" style="padding: 5px 10px;">Reload Map</button>
        <button onclick="toggleDebug()" style="padding: 5px 10px;">Toggle Debug Info</button>
      </div>

      <script>
        // Global variables
        var map, geojsonLayer;
        var debugEnabled = false;

        // Debug logging function
        function debugLog(message) {
          console.log(message);
          if (debugEnabled) {
            var debugPanel = document.getElementById('debug-panel');
            var now = new Date();
            var timestamp = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
            debugPanel.innerHTML += '<div>[' + timestamp + '] ' + message + '</div>';
            debugPanel.scrollTop = debugPanel.scrollHeight;
          }
        }

        // Toggle debug panel visibility
        function toggleDebug() {
          debugEnabled = !debugEnabled;
          var debugPanel = document.getElementById('debug-panel');
          debugPanel.style.display = debugEnabled ? 'block' : 'none';
          debugLog('Debug panel ' + (debugEnabled ? 'enabled' : 'disabled'));
        }

        // Helper function to show error messages
        function showError(message) {
          var errorDiv = document.getElementById('error-message');
          errorDiv.textContent = message;
          errorDiv.style.display = 'block';

          // Also log to console for debugging
          debugLog('ERROR: ' + message);

          // Hide loading indicator
          document.getElementById('loading').style.display = 'none';
        }

        // Function to focus map on Great Britain
        function focusOnGB() {
          if (map) {
            try {
              // Specific bounds for Great Britain
              var gbBounds = L.latLngBounds(
                [49.8, -8.0],  // Southwest corner
                [60.9, 2.0]    // Northeast corner
              );
              map.fitBounds(gbBounds);
              debugLog("Map centered on GB bounds");
            } catch (error) {
              showError("Error focusing on GB: " + error.message);
            }
          } else {
            showError("Map not initialized yet");
          }
        }

        // Function to reload the map
        function reloadMap() {
          try {
            // Remove old map if it exists
            if (map) {
              map.remove();
              debugLog("Old map instance removed");
            }

            // Hide any error messages
            document.getElementById('error-message').style.display = 'none';

            // Show loading indicator
            document.getElementById('loading').style.display = 'block';

            // Initialize map again
            debugLog("Initializing new map instance");
            initializeMap();
          } catch (error) {
            showError("Error reloading map: " + error.message);
          }
        }

        // Function to initialize the map
        function initializeMap() {
          try {
            debugLog("Starting map initialization");

            // Check if map container exists and has dimensions
            var mapContainer = document.getElementById('map');
            if (!mapContainer) {
              throw new Error("Map container element not found");
            }

            debugLog("Map container dimensions: " + mapContainer.clientWidth + "x" + mapContainer.clientHeight);
            if (mapContainer.clientWidth === 0 || mapContainer.clientHeight === 0) {
              debugLog("WARNING: Map container has zero dimensions!");
            }

            // Data passed from the Apps Script
            var dnoData;
            try {
              dnoData = <?= JSON.stringify(data) ?>;
              debugLog("DNO data loaded: " + (dnoData ? dnoData.length : 0) + " items");
            } catch (e) {
              debugLog("Error loading DNO data: " + e.message);
              dnoData = [];
            }

            // Get GeoJSON data directly from the embedded constant in Code.gs
            var geojsonData;
            try {
              geojsonData = <?= JSON.stringify(GEOJSON_DATA) ?>;

              if (!geojsonData || !geojsonData.features) {
                throw new Error("Invalid GeoJSON data structure");
              }

              debugLog("GeoJSON data loaded: " + geojsonData.features.length + " features");
            } catch (e) {
              throw new Error("Failed to load GeoJSON data: " + e.message);
            }

            // Create a lookup object for DNO data
            var dnoLookup = {};
            if (dnoData && dnoData.length) {
              dnoData.forEach(function(row) {
                if (row && row.id) {
                  dnoLookup[row.id] = {
                    name: row.name || 'Unknown',
                    value: row.value || 0
                  };
                }
              });
              debugLog("DNO lookup table created with " + Object.keys(dnoLookup).length + " entries");
            } else {
              debugLog("WARNING: No DNO data available for lookup");
            }

            // Initialize map with explicit dimensions and configuration
            debugLog("Creating map instance with default center");
            map = L.map('map', {
              center: [54.5, -2.5],    // Center of Great Britain
              zoom: 6,                 // Initial zoom level
              minZoom: 5,              // Prevent zooming out too far
              maxZoom: 10,             // Prevent zooming in too far
              zoomControl: true,       // Show zoom controls
              attributionControl: true // Show attribution
            });

            if (!map) {
              throw new Error("Failed to create map instance");
            }

            debugLog("Map instance created successfully");

            // Add OpenStreetMap base layer
            try {
              var tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              });

              tileLayer.addTo(map);
              debugLog("Base map tile layer added");
            } catch (e) {
              throw new Error("Failed to add tile layer: " + e.message);
            }

            // Color scale for the map
            function getColor(value) {
              return value > 16000 ? '#800026' :
                     value > 14000 ? '#BD0026' :
                     value > 13000 ? '#E31A1C' :
                     value > 12000 ? '#FC4E2A' :
                     value > 11000 ? '#FD8D3C' :
                     value > 10000 ? '#FEB24C' :
                     value > 9000 ? '#FED976' :
                                  '#FFEDA0';
            }

            // Style function for GeoJSON features
            function style(feature) {
              // Check different possible ID field names
              var dnoId = feature.properties ? (
                feature.properties.id ||
                feature.properties.dno_id ||
                feature.properties.DNO_ID ||
                feature.properties.ID
              ) : null;

              if (!dnoId) {
                debugLog("WARNING: Feature missing ID: " + JSON.stringify(feature.properties));
              }

              var dno = dnoId ? dnoLookup[dnoId] : null;
              var value = dno ? Number(dno.value) : 0;

              return {
                fillColor: getColor(value),
                weight: 2,
                opacity: 1,
                color: 'white',
                dashArray: '3',
                fillOpacity: 0.7
              };
            }

            // Highlight feature on mouseover
            function highlightFeature(e) {
              if (!e || !e.target) return;

              var layer = e.target;

              layer.setStyle({
                weight: 5,
                color: '#666',
                dashArray: '',
                fillOpacity: 0.7
              });

              layer.bringToFront();
              if (info) info.update(layer.feature.properties);
            }

            // Reset highlight on mouseout
            function resetHighlight(e) {
              if (!e || !e.target || !geojsonLayer) return;

              geojsonLayer.resetStyle(e.target);
              if (info) info.update();
            }

            // Zoom to feature on click
            function zoomToFeature(e) {
              if (!e || !e.target || !map) return;

              try {
                map.fitBounds(e.target.getBounds());
              } catch (error) {
                debugLog("Error zooming to feature: " + error.message);
              }
            }

            // Set up interaction for each feature
            function onEachFeature(feature, layer) {
              if (!layer) return;

              layer.on({
                mouseover: highlightFeature,
                mouseout: resetHighlight,
                click: zoomToFeature
              });
            }        // Create info control
        var info = L.control();

        info.onAdd = function (map) {
          this._div = L.DomUtil.create('div', 'info');
          this.update();
          return this._div;
        };

        info.update = function (props) {
          // Check different possible ID field names
          var dnoId = props ? (props.id || props.dno_id || props.DNO_ID || props.ID) : null;
          var dno = dnoId ? dnoLookup[dnoId] : null;

          this._div.innerHTML = '<h4>UK DNO Areas</h4>' +
            (props ?
              '<b>' + (dno ? dno.name : props.name || 'Unknown') + '</b><br />' +
              'Value: ' + (dno ? dno.value : 'N/A')
              : 'Hover over a DNO area');
        };

        info.addTo(map);

        // Create legend control
        var legend = L.control({position: 'bottomright'});

        legend.onAdd = function (map) {
          var div = L.DomUtil.create('div', 'info legend');
          var grades = [0, 9000, 10000, 11000, 12000, 13000, 14000, 16000];

          div.innerHTML += '<h4>Value</h4>';

          for (var i = 0; i < grades.length; i++) {
            div.innerHTML +=
              '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
              grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
          }

          return div;
        };

        legend.addTo(map);

        // Display the GeoJSON data directly (no fetch needed)
        try {
          debugLog("Creating GeoJSON layer with " + geojsonData.features.length + " features");

          // Create the GeoJSON layer
          geojsonLayer = L.geoJSON(geojsonData, {
            style: style,
            onEachFeature: onEachFeature
          }).addTo(map);

          debugLog("GeoJSON layer added to map");

          // Fit bounds with a slight delay to ensure rendering
          setTimeout(function() {
            debugLog("Fitting map to GeoJSON bounds");
            // Fit the map to the bounds of the GeoJSON layer
            map.fitBounds(geojsonLayer.getBounds(), {
              padding: [20, 20],
              maxZoom: 7,
              animate: true
            });

            // Force a map refresh
            map.invalidateSize();
            debugLog("Map bounds fitted to GeoJSON layer");

            // Hide loading indicator
            document.getElementById('loading').style.display = 'none';
          }, 1000); // Longer delay to ensure proper rendering

        } catch (error) {
          showError("Error displaying GeoJSON data: " + error.message);
          debugLog("GeoJSON error details: " + JSON.stringify(error));
        }
      } catch (error) {
        showError("Error initializing map: " + error.message);
        debugLog("Map initialization error: " + JSON.stringify(error));
      }
    }

    // Start the map initialization with a slight delay to ensure the DOM is fully loaded
    window.onload = function() {
      debugLog("Window loaded, initializing map with delay...");
      setTimeout(initializeMap, 800);

      // Set up visibility check to handle iframe sizing issues
      var visibilityCheck = setInterval(function() {
        var mapContainer = document.getElementById('map');
        if (mapContainer && mapContainer.clientWidth > 0 && mapContainer.clientHeight > 0) {
          debugLog("Map container visible with size: " + mapContainer.clientWidth + "x" + mapContainer.clientHeight);
          if (map) {
            map.invalidateSize();
            debugLog("Map size invalidated to force refresh");
          }
          clearInterval(visibilityCheck);
        }
      }, 500);
    };
      </script>
    </body>
    </html>
    """

    # ----- Step 9: Upload Apps Script code if possible -----
    if script_id != "MANUAL_SETUP_REQUIRED":
        try:
            # Update the Apps Script project content with the code files
            content = {
                "files": [
                    {"name": "appsscript", "type": "JSON", "source": manifest_content},
                    {"name": "Code", "type": "SERVER_JS", "source": code_gs_content},
                    {
                        "name": "mapView",
                        "type": "HTML",
                        "source": map_view_html_content,
                    },
                ]
            }

            apps_script_service.projects().updateContent(
                scriptId=script_id, body=content
            ).execute()

            # Verify the project has all required files by getting its content
            project_content = (
                apps_script_service.projects().getContent(scriptId=script_id).execute()
            )
            files = project_content.get("files", [])
            file_names = [f.get("name") for f in files]

            print("Verified Apps Script files:", ", ".join(file_names))

            if "mapView" not in file_names:
                print(
                    "WARNING: mapView file was not found in the project. Attempting to add it again..."
                )
                # Try adding just the HTML file
                content = {
                    "files": [
                        {
                            "name": "mapView",
                            "type": "HTML",
                            "source": map_view_html_content,
                        },
                    ]
                }
                apps_script_service.projects().updateContent(
                    scriptId=script_id, body=content
                ).execute()
                print("Added mapView HTML file separately")

            print("Uploaded Apps Script code successfully")
        except Exception as e:
            print(f"Error updating Apps Script content: {e}")
            print("Setting up for manual configuration...")
            script_id = "MANUAL_SETUP_REQUIRED"

    # ----- Step 10: Generate manual setup files if needed -----
    if script_id == "MANUAL_SETUP_REQUIRED":
        print("\nGenerating files for manual setup...")

        # Create a directory for the manual setup files
        manual_dir = "dno_map_oauth_manual"
        if not os.path.exists(manual_dir):
            os.makedirs(manual_dir)

        # Save the manifest file
        with open(f"{manual_dir}/appsscript.json", "w") as f:
            f.write(manifest_content)

        # Save the Code.gs file
        with open(f"{manual_dir}/Code.gs", "w") as f:
            f.write(code_gs_content)

        # Save the mapView.html file
        with open(f"{manual_dir}/mapView.html", "w") as f:
            f.write(map_view_html_content)

        print(f"Manual setup files generated in the '{manual_dir}' directory")
        print("Follow these steps for manual setup:")
        print("1. In your Google Sheet, go to Extensions > Apps Script")
        print("2. In the Apps Script editor, paste the contents of Code.gs")
        print(
            "3. Click the + button next to 'Files' and create an HTML file named 'mapView'"
        )
        print("4. Paste the contents of mapView.html into this file")
        print("5. Save the project and return to your spreadsheet")
        print("6. Refresh the page and you should see the 'Energy Maps' menu")

    # ----- Step 11: Print final instructions -----
    print("\n" + "=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print(
        f"\nGoogle Sheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    )

    if script_id != "MANUAL_SETUP_REQUIRED":
        print(f"Apps Script Project ID: {script_id}")
        print(f"Apps Script Editor URL: https://script.google.com/d/{script_id}/edit")

    print("\nInstructions:")
    print("1. Open the Google Sheet using the URL above")
    print("2. Wait for the Apps Script to initialize (this may take a moment)")
    print("3. Refresh the page if needed")
    print("4. Click on 'Energy Maps > Show DNO Map' to view the DNO map")
    print("\nNote: You might need to authorize the script to access your Google Sheet")


if __name__ == "__main__":
    main()
