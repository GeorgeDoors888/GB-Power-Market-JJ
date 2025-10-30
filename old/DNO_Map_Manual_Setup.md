### DNO Map Setup Instructions

1. **Create HTML File in Apps Script**:
   - Go to your Google Sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
   - Click "Extensions" > "Apps Script"
   - Rename the project to "DNO Map Visualization"
   - Replace the content of Code.gs with the code from dno_map_code.gs
   - Click the "+" icon next to Files
   - Select "HTML"
   - Name the file "mapView"
   - Paste the code from the following section
   - Save all files

2. **mapView.html Code**:
```html
<!DOCTYPE html>
<html>
  <head>
    <title>DNO Map</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/leaflet.css" />
    <style>
      html, body {
        height: 100%;
        margin: 0;
        padding: 0;
      }
      #map {
        height: 100%;
        width: 100%;
      }
      .info {
        padding: 6px 8px;
        font: 14px/16px Arial, Helvetica, sans-serif;
        background: white;
        background: rgba(255, 255, 255, 0.8);
        box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
        border-radius: 5px;
      }
      .info h4 {
        margin: 0 0 5px;
        color: #777;
      }
      .legend {
        text-align: left;
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
      // Get DNO data from the spreadsheet
      const dnoData = <?= JSON.stringify(SpreadsheetApp.getActiveSpreadsheet().getSheetByName('DNO_Data').getDataRange().getValues()) ?>;

      // Create a lookup object for DNO data
      const dnoLookup = {};
      for (let i = 1; i < dnoData.length; i++) {
        dnoLookup[dnoData[i][0]] = {
          name: dnoData[i][1],
          value: dnoData[i][2]
        };
      }

      // Initialize the map centered on the UK
      const map = L.map('map').setView([54.5, -2.5], 6);

      // Add the base map layer
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
      }).addTo(map);

      // Define color function for choropleth map
      function getColor(d) {
        return d > 16000 ? '#800026' :
               d > 14000 ? '#BD0026' :
               d > 13000 ? '#E31A1C' :
               d > 12000 ? '#FC4E2A' :
               d > 11000 ? '#FD8D3C' :
               d > 10000 ? '#FEB24C' :
               d > 9000 ? '#FED976' :
                          '#FFEDA0';
      }

      // Define style function for GeoJSON features
      function style(feature) {
        const dnoId = feature.properties.id || feature.properties.dno_id;
        const dno = dnoLookup[dnoId];
        const value = dno ? Number(dno.value) : 0;

        return {
          fillColor: getColor(value),
          weight: 2,
          opacity: 1,
          color: 'white',
          dashArray: '3',
          fillOpacity: 0.7
        };
      }

      // Create info control
      const info = L.control();

      info.onAdd = function(map) {
        this._div = L.DomUtil.create('div', 'info');
        this.update();
        return this._div;
      };

      info.update = function(props) {
        const dnoId = props ? (props.id || props.dno_id) : null;
        const dno = dnoId ? dnoLookup[dnoId] : null;

        this._div.innerHTML = '<h4>UK DNO Areas</h4>' +
          (props ?
            '<b>' + (dno ? dno.name : props.name || 'Unknown') + '</b><br />' +
            'Value: ' + (dno ? dno.value : 'N/A')
            : 'Hover over a DNO area');
      };

      info.addTo(map);

      // Create legend control
      const legend = L.control({position: 'bottomright'});

      legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'info legend');
        const grades = [0, 9000, 10000, 11000, 12000, 13000, 14000, 16000];

        div.innerHTML += '<h4>Value</h4>';

        for (let i = 0; i < grades.length; i++) {
          div.innerHTML +=
            '<i style="background:' + getColor(grades[i] + 1) + '"></i> ' +
            grades[i] + (grades[i + 1] ? '&ndash;' + grades[i + 1] + '<br>' : '+');
        }

        return div;
      };

      legend.addTo(map);

      // Add interaction
      function highlightFeature(e) {
        const layer = e.target;

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

      // Load GeoJSON data from a URL or string
      // (Replace this URL with your own hosted GeoJSON)
      const GEOJSON_URL = 'https://storage.googleapis.com/jibber-jabber-maps/dno_map_data.geojson';

      // Fetch and display the GeoJSON data
      let geojsonLayer;
      fetch(GEOJSON_URL)
        .then(response => response.json())
        .then(data => {
          geojsonLayer = L.geoJSON(data, {
            style: style,
            onEachFeature: onEachFeature
          }).addTo(map);

          // Fit map to GeoJSON bounds
          map.fitBounds(geojsonLayer.getBounds());
        })
        .catch(error => {
          console.error('Error loading GeoJSON:', error);
          document.getElementById('map').innerHTML =
            '<div style="color:red;text-align:center;padding-top:50px;">' +
            '<h3>Error loading map data</h3>' +
            '<p>Please check the GeoJSON URL.</p>' +
            '</div>';
        });
    </script>
  </body>
</html>
```

3. **Host the GeoJSON File**:
   - Upload your merged GeoJSON file to a hosting service that allows CORS (Cross-Origin Resource Sharing)
   - Options:
     - GitHub repository (make it public)
     - Google Cloud Storage bucket (with public access)
     - Any other web hosting service
   - Update the `GEOJSON_URL` variable in the HTML file with the URL to your hosted GeoJSON file

4. **View the Map**:
   - Return to your Google Sheet
   - Refresh the page
   - You should see a new menu called "Energy Maps"
   - Click on "Energy Maps" > "Show DNO Map"
   - The map will open in a dialog box

5. **Troubleshooting**:
   - If the map doesn't appear, check the browser console for errors
   - Ensure your GeoJSON file is accessible from the URL you provided
   - Verify that the DNO_Data sheet contains the correct information
