import json
import os

# Paths
geojson_path = "system_regulatory/gis/merged_geojson.geojson"
output_dir = "dno_map_manual_setup"
code_gs_path = os.path.join(output_dir, "Code.gs")
map_view_path = os.path.join(output_dir, "mapView.html")

# Ensure output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Read GeoJSON data
print(f"Reading GeoJSON file: {geojson_path}")
with open(geojson_path, "r") as f:
    geojson_data = json.load(f)

# Convert to JSON string for embedding
geojson_str = json.dumps(geojson_data)
print(f"GeoJSON data loaded: {len(geojson_str)} characters")

# Read the existing template Code.gs file
with open(code_gs_path, "r") as f:
    code_gs_content = f.read()

# Replace the placeholder GeoJSON with the actual data
if "// Your GeoJSON features would be here" in code_gs_content:
    code_gs_content = code_gs_content.replace(
        """const GEOJSON_DATA = {
  "type": "FeatureCollection",
  "features": [
    // Your GeoJSON features would be here
    // This is a placeholder - the actual GeoJSON data will be added by the Python script
  ]
};""",
        f"const GEOJSON_DATA = {geojson_str};",
    )
    print("Replaced placeholder with actual GeoJSON data in Code.gs")
else:
    print("Warning: Could not find GeoJSON placeholder in Code.gs")

# Write updated Code.gs file
print(f"Writing updated Code.gs file ({len(code_gs_content)} characters)")
with open(code_gs_path, "w") as f:
    f.write(code_gs_content)

print("\nFiles updated successfully:")
print(f"1. {code_gs_path}")
print(f"2. {map_view_path}")

print("\nFollow these steps for manual setup:")
print("1. In your Google Sheet, go to Extensions > Apps Script")
print("2. In the Apps Script editor, paste the contents of Code.gs")
print("3. Click the + button next to 'Files' and create an HTML file named 'mapView'")
print("4. Paste the contents of mapView.html into this file")
print("5. Save the project")
print("6. Select the 'onOpen' function from the dropdown menu and click the Run button")
print(
    "7. Return to your spreadsheet, refresh the page, and you should see the 'Energy Maps' menu"
)
print("8. Click on 'Energy Maps > Show DNO Map' to view your interactive DNO map")
