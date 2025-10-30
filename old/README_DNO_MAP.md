# UK DNO Map Visualization

This project provides tools to visualize UK Distribution Network Operator (DNO) areas on interactive maps using Google Apps Script and Leaflet.

## Project Components

### Python Scripts

1. **convert_geojson_for_google_maps.py**
   - Converts GeoJSON files of DNO license areas for use with Google Maps
   - Transforms coordinates from OSGB (EPSG:27700) to WGS84 (EPSG:4326)
   - Simplifies geometry to reduce file size
   - Adds proper DNO ID properties
   
2. **create_dno_map_data.py**
   - Creates sample DNO data for visualization
   - Generates a CSV file for import into Google Sheets
   - Creates a minimal sample GeoJSON file

### Google Apps Script Files

1. **dno_map_app_script.js**
   - The main Google Apps Script file for the map application
   - Provides functions to display the map, load data, and handle user interactions
   
2. **dno_map_html_template.html**
   - HTML template for the map display
   - Uses Leaflet for the interactive map
   - Note: The `<?!= JSON.stringify(data) ?>` syntax is specific to Google Apps Script's HTML Service
   - This line will show linting errors in VS Code but will work correctly in Google Apps Script

### Documentation

1. **DNO_MAP_SETUP_GUIDE.md**
   - Comprehensive guide for setting up the DNO map visualization
   - Step-by-step instructions for importing data, setting up Google Apps Script, and using the map

## Getting Started

1. First, ensure you have the required Python libraries:
   ```
   pip install pandas pyproj shapely
   ```

2. Generate sample DNO data:
   ```
   python create_dno_map_data.py
   ```

3. Convert your GeoJSON files for use with Google Maps:
   ```
   python convert_geojson_for_google_maps.py --input-dir ./your_geojson_dir --output-file dno_areas_for_maps.json
   ```

4. Follow the instructions in **DNO_MAP_SETUP_GUIDE.md** to set up the Google Apps Script application.

## Data Requirements

The mapping relies on the following data structures:

### DNO Reference Data (CSV)

A CSV file with DNO reference data containing at least these columns:
- MPAN_Code: The DNO ID (first 2 digits of MPAN)
- DNO_Key: A unique key for the DNO
- DNO_Name: The full name of the DNO
- Short_Code: A short code for the DNO

### GeoJSON File

The converted GeoJSON file should contain features with the following properties:
- dno_id: The DNO ID (matching MPAN_Code in the reference data)
- dno_name: The name of the DNO
- dno_key: The unique key for the DNO

### Map Data (CSV)

A CSV file with the following columns:
- ID: The DNO ID (matching MPAN_Code/dno_id)
- Name: The name of the DNO
- Value: A numeric value for color-coding the map

## Google Apps Script Implementation Notes

When implementing in Google Apps Script:

1. The HTML template uses a special syntax `<?!= JSON.stringify(data) ?>` to insert data from the server
2. This syntax will show linting errors in VS Code but will work correctly in Google Apps Script
3. For testing outside of Google Apps Script, the template includes sample data

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
