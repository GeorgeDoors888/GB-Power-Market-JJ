# UK DNO Map Visualization in Google Sheets

This guide provides step-by-step instructions for setting up and using the UK Distribution Network Operator (DNO) map visualization in Google Sheets.

## Overview

The DNO Map Visualization allows you to:
- Display UK DNO license areas on an interactive map
- Color-code DNO areas based on data values
- View detailed information about each DNO on hover
- Interact with the map by clicking on areas to zoom

## Prerequisites

- Google account with access to Google Sheets and Google Drive
- Converted GeoJSON files of DNO license areas (using `convert_geojson_for_maps.py`)
- Sample DNO data (generated using `create_dno_map_data.py`)

## Setup Instructions

### Step 1: Generate the Required Data Files

1. Run the `create_dno_map_data.py` script to generate sample DNO data:
   ```bash
   python create_dno_map_data.py
   ```
   This will create:
   - `DNO_Map_Data.csv`: Sample data for DNO visualization
   - `DNO_Map_GeoJSON.json`: A placeholder GeoJSON file

2. Run the `convert_geojson_for_maps.py` script to convert your actual DNO GeoJSON files:
   ```bash
   python convert_geojson_for_maps.py
   ```

### Step 2: Create a New Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) and create a new spreadsheet
2. Rename the spreadsheet to "UK DNO Map Visualization" (or any name you prefer)

### Step 3: Import the DNO Data

1. In your Google Sheet, go to File > Import
2. Select "Upload" and choose the `DNO_Map_Data.csv` file
3. In the import settings:
   - Choose "Replace current sheet"
   - Select "Yes" for headers
   - Click "Import data"
4. Rename the sheet to "DNO_Data" (this name is required for the script to work)

### Step 4: Upload the GeoJSON File to Google Drive

1. Go to [Google Drive](https://drive.google.com)
2. Upload the converted GeoJSON file
3. Right-click on the file and select "Get link"
4. Make sure the sharing settings allow anyone with the link to view the file
5. Copy the file ID from the link (the part after `/d/` and before the next `/`)

### Step 5: Set Up Google Apps Script

1. In your Google Sheet, go to Extensions > Apps Script
2. This will open the Apps Script editor in a new tab
3. Rename the project to "DNO Map Visualization"

4. Replace the contents of the default `Code.gs` file with the code from `dno_map_app_script.js`

5. Create a new HTML file:
   - Click the "+" icon next to Files
   - Select "HTML"
   - Name the file "mapView"
   - Copy the contents from `dno_map_view.html`
   - Replace the placeholder `<?!= JSON.stringify(data) ?>` with the proper Apps Script syntax

6. Save all files (Ctrl+S or Cmd+S)

### Step 6: Configure the GeoJSON File ID

1. In the Apps Script editor, go to Project Settings (gear icon)
2. Click on "Script Properties" tab
3. Click "Add Script Property"
4. Set the property name to "GEOJSON_FILE_ID"
5. Set the property value to the ID you copied from the Google Drive link
6. Click "Save script properties"

### Step 7: Deploy the Web App (Optional)

If you want to access the map outside of Google Sheets:

1. Click on "Deploy" > "New deployment"
2. Select "Web app" as the deployment type
3. Set the following options:
   - Description: "DNO Map Web App"
   - Execute as: "Me"
   - Who has access: "Anyone" or "Anyone with Google Account"
4. Click "Deploy"
5. Copy the web app URL
6. Go back to your HTML file and replace "REPLACE_WITH_WEB_APP_URL" with this URL

## Using the Map

1. Return to your Google Sheet
2. Refresh the page if needed
3. You should see a new menu called "Energy Maps"
4. Click on "Energy Maps" > "Show DNO Map"
5. The map will open in a dialog box

### Initial Setup

The first time you use the map, you may need to:

1. Click on "Energy Maps" > "Setup DNO Map"
2. This will create a sample data sheet if one doesn't exist
3. Follow the prompts to complete the setup

### Importing DNO Data

To import data from a CSV file:

1. Upload your CSV file to Google Drive
2. Get the file ID
3. Click on "Energy Maps" > "Import DNO Data from CSV"
4. Enter the file ID when prompted

## Customizing the Map

### Changing the Color Scheme

You can modify the color scheme by editing the `getColor()` function in the HTML file:

```javascript
function getColor(d) {
  return d > 14000 ? '#800026' :
         d > 12000 ? '#BD0026' :
         d > 10000 ? '#E31A1C' :
         d > 9000 ? '#FC4E2A' :
         d > 8000 ? '#FD8D3C' :
         d > 7000 ? '#FEB24C' :
         d > 6000 ? '#FED976' :
                    '#FFEDA0';
}
```

### Adding Additional Data

To display additional data on the map:

1. Add columns to your DNO_Data sheet
2. Modify the HTML file to include these additional fields in the info display

## Troubleshooting

### Map Not Displaying

1. Check the browser console for errors
2. Verify that the GeoJSON file ID is correct in the script properties
3. Ensure the GeoJSON file is shared with appropriate permissions

### Missing DNO Areas

1. Verify that your GeoJSON file has been properly converted
2. Check that the DNO IDs in the GeoJSON match those in your data sheet

### Data Not Appearing

1. Make sure your data sheet is named "DNO_Data"
2. Verify that your data has columns named "ID", "Name", and "Value"
3. Check that the ID values match the dno_id properties in your GeoJSON

## Additional Resources

- [Leaflet Documentation](https://leafletjs.com/reference.html)
- [Google Apps Script Documentation](https://developers.google.com/apps-script)
- [GeoJSON Specification](https://geojson.org/)

from shapely.geometry import shape, mapping
from shapely.geometry.base import BaseGeometry
