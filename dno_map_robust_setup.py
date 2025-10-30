import base64
import json
import os

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ----- Configuration -----
SERVICE_ACCOUNT_FILE = "jibber_jabber_key.json"
GEOJSON_FILE_PATH = "system_regulatory/gis/merged_geojson.geojson"
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_insights"
TABLE_ID = "dno_map_data"  # Table containing DNO data
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"  # Your existing sheet

# ----- Authentication -----
# Scopes for Google Drive and Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/script.projects",
    "https://www.googleapis.com/auth/bigquery",
]

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Initialize API clients
sheets_service = build("sheets", "v4", credentials=credentials)
drive_service = build("drive", "v3", credentials=credentials)
apps_script_service = build("script", "v1", credentials=credentials)
bq_client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

print("API clients initialized successfully")

# ----- Step 1: Check spreadsheet access -----
try:
    sheet_metadata = (
        sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    )
    print(
        f"Successfully accessed spreadsheet: {sheet_metadata.get('properties', {}).get('title', 'Unknown')}"
    )
    print(f"Spreadsheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
except Exception as e:
    print(f"Error accessing spreadsheet: {e}")
    print("Please check permissions and spreadsheet ID")
    exit(1)

# ----- Step 2: Check if DNO_Data sheet exists, create it if not -----
sheets = sheet_metadata.get("sheets", [])
sheet_exists = False
for sheet in sheets:
    if sheet.get("properties", {}).get("title", "") == "DNO_Data":
        sheet_exists = True
        break

if not sheet_exists:
    # Add DNO_Data sheet
    request = {"addSheet": {"properties": {"title": "DNO_Data"}}}
    try:
        sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body={"requests": [request]}
        ).execute()
        print("Created 'DNO_Data' sheet")
    except Exception as e:
        print(f"Error creating DNO_Data sheet: {e}")
        print("Using default 'Sheet1' instead")
        # If we can't create a new sheet, we'll use the default one
        sheets_service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": [["ID", "Name", "Value"]]},
        ).execute()
else:
    print("'DNO_Data' sheet already exists")

# ----- Step 3: Create sample DNO data -----
try:
    # Try to query BigQuery for DNO data
    print(f"Querying BigQuery for DNO data from {PROJECT_ID}.{DATASET_ID}.{TABLE_ID}")
    query = f"""
    SELECT id, name, value
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    """
    query_job = bq_client.query(query)
    rows = list(query_job.result())

    if rows:
        # Convert BigQuery results to the format needed for Sheets
        dno_data = [["ID", "Name", "Value"]]
        for row in rows:
            dno_data.append([row["id"], row["name"], row["value"]])
        print(f"Retrieved {len(rows)} rows of DNO data from BigQuery")
    else:
        # If no data found, create sample data
        raise Exception("No data found in BigQuery table")

except Exception as e:
    print(f"Error querying BigQuery: {e}")
    print("Using sample DNO data instead")
    # Sample DNO data
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

# ----- Step 4: Update Google Sheet with DNO data -----
print("Updating Google Sheet with DNO data...")
try:
    sheet_range = "DNO_Data!A1" if sheet_exists else "Sheet1!A1"
    sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range,
        valueInputOption="RAW",
        body={"values": dno_data},
    ).execute()
    print("Updated Google Sheet with DNO data")
except Exception as e:
    print(f"Error updating sheet with DNO data: {e}")
    print("Please check spreadsheet permissions")
    exit(1)

# ----- Step 5: Process and upload GeoJSON file -----
print(f"Reading GeoJSON file: {GEOJSON_FILE_PATH}")
try:
    with open(GEOJSON_FILE_PATH, "r") as f:
        geojson_data = json.load(f)

    print(
        f"Successfully loaded GeoJSON data with {len(geojson_data.get('features', []))} features"
    )

    # Save the GeoJSON to a new file
    output_geojson_path = "dno_map_data.geojson"
    with open(output_geojson_path, "w") as f:
        json.dump(geojson_data, f)

    print(f"Saved processed GeoJSON to {output_geojson_path}")

    # Try to upload to Google Drive
    print("Attempting to upload GeoJSON to Google Drive...")
    try:
        file_metadata = {"name": "DNO_Map_GeoJSON.json", "mimeType": "application/json"}
        media = MediaFileUpload(output_geojson_path, mimetype="application/json")
        file = (
            drive_service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )
        geojson_file_id = file.get("id")
        print(
            f"Successfully uploaded GeoJSON to Google Drive with ID: {geojson_file_id}"
        )

        # Make the file publicly accessible
        permission = {"type": "anyone", "role": "reader"}
        drive_service.permissions().create(
            fileId=geojson_file_id, body=permission
        ).execute()
        print(f"Made GeoJSON file publicly accessible")
        print(
            f"GeoJSON file URL: https://drive.google.com/file/d/{geojson_file_id}/view"
        )

        geojson_url = (
            f"https://www.googleapis.com/drive/v3/files/{geojson_file_id}?alt=media"
        )
        print(f"Direct GeoJSON access URL for Apps Script: {geojson_url}")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
        print("You'll need to host the GeoJSON file manually")
        geojson_file_id = None
        geojson_url = "YOUR_HOSTED_GEOJSON_URL"

except Exception as e:
    print(f"Error processing GeoJSON: {e}")
    print("Please check that the GeoJSON file exists and is valid")
    exit(1)

# ----- Step 6: Generate Apps Script code -----
print("Generating Apps Script code...")

# Code.gs file
code_gs_content = f"""
// DNO Map Visualization

// Create the menu when the spreadsheet opens
function onOpen() {{
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('Energy Maps')
    .addItem('Show DNO Map', 'showDNOMap')
    .addToUi();
}}

// Show the DNO map dialog
function showDNOMap() {{
  const html = HtmlService.createHtmlOutputFromFile('mapView')
    .setWidth(800)
    .setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'DNO Map');
}}
"""

# mapView.html file
map_view_html_content = f"""
<!DOCTYPE html>
<html>
  <head>
    <title>DNO Map</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
    <style>
      html, body {{
        height: 100%;
        margin: 0;
        padding: 0;
      }}
      #map {{
        height: 100%;
        width: 100%;
      }}
      .info {{
        padding: 6px 8px;
        font: 14px/16px Arial, Helvetica, sans-serif;
        background: white;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
        border-radius: 5px;
      }}
      .info h4 {{
        margin: 0 0 5px;
        color: #777;
      }}
      .legend {{
        text-align: left;
        line-height: 18px;
        color: #555;
      }}
      .legend i {{
        width: 18px;
        height: 18px;
        float: left;
        margin-right: 8px;
        opacity: 0.7;
      }}
    </style>
  </head>
  <body>
    <div id="map"></div>
    <script>
      // Get DNO data from the spreadsheet
      const dnoData = <?= JSON.stringify(SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO_Data') ?
                          SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO_Data').getDataRange().getValues() :
                          SpreadsheetApp.getActiveSpreadsheet().getSheets()[0].getDataRange().getValues()) ?>;

      // Create a lookup object for DNO data
      const dnoLookup = {{}};
      for (let i = 1; i < dnoData.length; i++) {{
        dnoLookup[dnoData[i][0]] = {{
          name: dnoData[i][1],
          value: dnoData[i][2]
        }};
      }}

      // Initialize the map centered on the UK
      const map = L.map('map').setView([54.5, -2.5], 6);

      // Add the base map layer
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }}).addTo(map);

      // Define color function for choropleth map
      function getColor(d) {{
        return d > 16000 ? '#800026' :
               d > 14000 ? '#BD0026' :
               d > 13000 ? '#E31A1C' :
               d > 12000 ? '#FC4E2A' :
               d > 11000 ? '#FD8D3C' :
               d > 10000 ? '#FEB24C' :
               d > 9000 ? '#FED976' :
                          '#FFEDA0';
      }}

      // Define style function for GeoJSON features
      function style(feature) {{
        const dnoId = feature.properties.id || feature.properties.dno_id;
        const dno = dnoLookup[dnoId];
        const value = dno ? Number(dno.value) : 0;

        return {{
          fillColor: getColor(value),
          weight: 2,
          opacity: 1,
          color: 'white',
          dashArray: '3',
          fillOpacity: 0.7
        }};
      }}

      // Create info control
      const info = L.control();

      info.onAdd = function(map) {{
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
      }};

      info.update = function(props) {{
        const dnoId = props ? (props.id || props.dno_id) : null;
        const dno = dnoId ? dnoLookup[dnoId] : null;

        this._div.innerHTML = '<h4>UK DNO Areas</h4>' +
          (props ?
            '<b>' + (dno ? dno.name : props.name || 'Unknown') + '</b><br />' +
            'Value: ' + (dno ? dno.value : 'N/A')
            : 'Hover over a DNO area');
      }};

      info.addTo(map);

      // Create legend control
      const legend = L.control({{position: 'bottomright'}});

      legend.onAdd = function(map) {{
        const div = L.DomUtil.create('div', 'info legend');
        const grades = [0, 9000, 10000, 11000, 12000, 13000, 14000, 16000];

        div.innerHTML += '<h4>Value</h4>';

        for (let i = 0; i < grades.length; i++) {{
          div.innerHTML +=
            '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
            grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
        }}

        return div;
      }};

      legend.addTo(map);

      // Add interaction
      function highlightFeature(e) {{
        const layer = e.target;

        layer.setStyle({{
          weight: 5,
          color: '#666',
          dashArray: '',
          fillOpacity: 0.7
        }});

        layer.bringToFront();
        info.update(layer.feature.properties);
      }}

      function resetHighlight(e) {{
        geojsonLayer.resetStyle(e.target);
        info.update();
      }}

      function zoomToFeature(e) {{
        map.fitBounds(e.target.getBounds());
      }}

      function onEachFeature(feature, layer) {{
        layer.on({{
          mouseover: highlightFeature,
          mouseout: resetHighlight,
          click: zoomToFeature
        }});
      }}

      // Load GeoJSON data from a URL
      const GEOJSON_URL = '{geojson_url}';

      // Fetch and display the GeoJSON data
      let geojsonLayer;

      // For Google Drive URLs, we need to add authentication
      const headers = {{}};
      if (GEOJSON_URL.includes('googleapis.com')) {{
        headers['Authorization'] = 'Bearer ' + <?= ScriptApp.getOAuthToken() ?>;
      }}

      fetch(GEOJSON_URL, {{ headers }})
        .then(response => response.json())
        .then(data => {{
          geojsonLayer = L.geoJSON(data, {{
            style: style,
            onEachFeature: onEachFeature
          }}).addTo(map);

          // Fit map to GeoJSON bounds
          map.fitBounds(geojsonLayer.getBounds());
        }})
        .catch(error => {{
          console.error('Error loading GeoJSON:', error);
          document.getElementById('map').innerHTML =
            '<div style="color:red;text-align:center;padding-top:50px;">' +
            '<h3>Error loading map data</h3>' +
            '<p>Please check the GeoJSON URL.</p>' +
            '</div>';
        }});
    </script>
  </body>
</html>
"""

# Write the Apps Script code files to local files
with open("dno_map_code.gs", "w") as f:
    f.write(code_gs_content)

with open("dno_map_view.html", "w") as f:
    f.write(map_view_html_content)

print("Generated Apps Script code files:")
print("- dno_map_code.gs")
print("- dno_map_view.html")

# ----- Step 7: Try to create/update Apps Script project -----
try:
    print("Attempting to create/update Apps Script project...")

    # Check if there's already a bound script project
    drive_response = (
        drive_service.files()
        .get(fileId=SPREADSHEET_ID, fields="name,properties")
        .execute()
    )

    script_id = None
    if "properties" in drive_response and "script" in drive_response["properties"]:
        script_id = drive_response["properties"]["script"]
        print(f"Found existing bound Apps Script project with ID: {script_id}")

    if not script_id:
        # Create a new Apps Script project
        script_metadata = {"title": "DNO Map Visualization", "parentId": SPREADSHEET_ID}
        try:
            script_project = (
                apps_script_service.projects().create(body=script_metadata).execute()
            )
            script_id = script_project["scriptId"]
            print(f"Created new bound Apps Script project with ID: {script_id}")
        except Exception as e:
            print(f"Error creating bound script: {e}")

            # Try creating a standalone script as fallback
            script_metadata = {"title": "DNO Map Visualization"}
            try:
                script_project = (
                    apps_script_service.projects()
                    .create(body=script_metadata)
                    .execute()
                )
                script_id = script_project["scriptId"]
                print(f"Created standalone Apps Script project with ID: {script_id}")
            except Exception as e2:
                print(f"Error creating standalone script: {e2}")
                script_id = None

    # If we have a script ID, try to update its content
    if script_id:
        content = {
            "files": [
                {"name": "Code", "type": "SERVER_JS", "source": code_gs_content},
                {"name": "mapView", "type": "HTML", "source": map_view_html_content},
            ]
        }

        try:
            apps_script_service.projects().updateContent(
                scriptId=script_id, body=content
            ).execute()
            print("Successfully updated Apps Script project content")
        except Exception as e:
            print(f"Error updating Apps Script content: {e}")
            print("You'll need to update the Apps Script project manually")
    else:
        print(
            "No script ID available. You'll need to create the Apps Script project manually"
        )

except Exception as e:
    print(f"Error working with Apps Script: {e}")
    print("You'll need to create and configure the Apps Script project manually")

# ----- Step 8: Print final instructions -----
print("\n" + "=" * 80)
print("SETUP PROCESS COMPLETE!")
print("=" * 80)

print(f"\nGoogle Sheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

if geojson_file_id:
    print(f"GeoJSON file ID: {geojson_file_id}")
    print(f"GeoJSON file URL: https://drive.google.com/file/d/{geojson_file_id}/view")
else:
    print("GeoJSON file: You need to host the file 'dno_map_data.geojson' manually")

if script_id:
    print(f"Apps Script Project ID: {script_id}")
    print(f"Apps Script Editor URL: https://script.google.com/d/{script_id}/edit")
else:
    print("Apps Script: You need to create the Apps Script project manually")

print("\nManual Setup Instructions (if needed):")
print("1. Open the Google Sheet")
print("2. Go to Extensions > Apps Script")
print("3. Replace the content of Code.gs with the content of dno_map_code.gs")
print(
    "4. Create a new HTML file called 'mapView' and paste the content of dno_map_view.html"
)
print("5. Save the project")
print("6. Refresh the Sheet and look for the 'Energy Maps' menu")

print(
    "\nNote: If you hosted the GeoJSON file manually, update the GEOJSON_URL in the mapView.html file"
)
