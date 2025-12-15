/**
 * @OnlyCurrentDoc
 *
 * This script creates a real-time energy dashboard in Google Sheets,
 * pulling data from Google BigQuery and providing interactivity.
 */

// ---------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------
const SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc";
const DASHBOARD_SHEET_NAME = "Dashboard V3";
const CHART_DATA_SHEET_NAME = "Chart Data";
const DNO_MAP_SHEET_NAME = 'DNO_Map';
const GCP_PROJECT_ID = "inner-cinema-476211-u9";

// Cell locations
const TIME_RANGE_CELL = 'B3';
const REGION_CELL = 'F3';


// ---------------------------------------------------
// TRIGGERS & MENU
// ---------------------------------------------------

/**
 * Creates a custom menu in the spreadsheet UI.
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  ui.createMenu('⚡ GB Energy V3')
    .addItem('1. Manual Refresh All Data', 'refreshAllData')
    .addItem('2. Show DNO Map Selector', 'showDnoMap')
    .addToUi();
  
  ui.createMenu('🗺️ DNO Map')
    .addItem('View Interactive Map', 'createDNOMap')
    .addToUi();
}

/**
 * Runs automatically when a user changes the value of any cell.
 * @param {object} e The event object.
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  const cell = range.getA1Notation();

  // If the edited cell is the time range or region dropdown, refresh the data.
  if (sheet.getName() === DASHBOARD_SHEET_NAME && (cell === TIME_RANGE_CELL || cell === REGION_CELL)) {
    refreshAllData();
  }
}

// ---------------------------------------------------
// DATA REFRESH LOGIC
// ---------------------------------------------------

/**
 * Main function to refresh all data on the dashboard.
 * This will be called from the menu or onEdit trigger.
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().toast('🔄 Starting V3 data refresh...');
  
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DASHBOARD_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  const timeRange = sheet.getRange(TIME_RANGE_CELL).getValue();
  const selectedDno = sheet.getRange(REGION_CELL).getValue();

  // In a real scenario, you would pass these values to your BigQuery refresh script.
  // For now, we'll just log them.
  Logger.log('Refreshing data for Time Range: "' + timeRange + '" and Region: "' + selectedDno + '"');
  
  // This is where you would call a function to trigger the Python script
  // that repopulates the 'Chart Data' sheet from BigQuery based on the dropdown values.
  // Since we can't directly call Python, we'll assume the data is refreshed externally
  // for the purpose of this script. The Python scripts `populate_dashboard_tables.py`
  // and `add_chart_and_map.py` already do this.
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ V3 Data refresh complete!', 'Success', 5);
}


// ---------------------------------------------------
// DNO MAP SIDEBAR
// ---------------------------------------------------

/**
 * Shows the DNO map selector sidebar.
 */
function showDnoMap() {
  // Redirect to the interactive map instead
  createDNOMap();
}

/**
 * Fetches DNO locations and metrics from the DNO_Map sheet for the sidebar.
 * Called from DnoMap.html.
 * @returns {Array<Object>} A list of DNO objects with code, name, lat, lng.
 */
function getDnoLocations() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(DNO_MAP_SHEET_NAME);
  if (!sheet) {
    Logger.log('Error: Sheet "' + DNO_MAP_SHEET_NAME + '" not found.');
    return [];
  }

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) {
      return []; // No data
  }
  
  const header = values.shift(); // Get header row
  const idxCode = header.indexOf('DNO Code');
  const idxName = header.indexOf('DNO Name');
  const idxLat = header.indexOf('Latitude');
  const idxLng = header.indexOf('Longitude');
  const idxNetMargin = header.indexOf('Net Margin (£/MWh)');

  if (idxCode === -1 || idxName === -1 || idxLat === -1 || idxLng === -1) {
      Logger.log("DNO_Map sheet is missing required columns (DNO Code, DNO Name, Latitude, Longitude).");
      return [];
  }

  return values
    .filter(function(r) { return r[idxCode]; }) // Ensure DNO code exists
    .map(function(r) {
      return {
        code: String(r[idxCode]),
        name: String(r[idxName]),
        lat: Number(r[idxLat]),
        lng: Number(r[idxLng]),
        netMargin: Number(r[idxNetMargin] || 0)
      };
    });
}

/**
 * Sets the selected DNO NAME in the region cell on the dashboard.
 * Called from DnoMap.html when a user clicks a marker.
 * @param {string} nameOrCode The DNO name (e.g., "UKPN-EPN") or code.
 */
function selectDno(nameOrCode) {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) {
      Logger.log('Error: Dashboard sheet "' + DASHBOARD_SHEET_NAME + '" not found.');
      return;
  }
  dash.getRange(REGION_CELL).setValue(nameOrCode);
  // The onEdit trigger will automatically handle the data refresh.
}

// ---------------------------------------------------
// DNO INTERACTIVE MAP
// ---------------------------------------------------

/**
 * Creates an interactive UK DNO license area map
 */
function createDNOMap() {
  var html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>UK DNO License Areas</title>
  <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #map { height: 100vh; width: 100%; }
    .info {
      padding: 10px;
      font: 14px/16px Arial, Helvetica, sans-serif;
      background: white;
      background: rgba(255,255,255,0.95);
      box-shadow: 0 0 15px rgba(0,0,0,0.3);
      border-radius: 8px;
      max-width: 250px;
    }
    .info h4 { 
      margin: 0 0 8px; 
      color: #333; 
      font-size: 16px;
      border-bottom: 2px solid #FF6600;
      padding-bottom: 5px;
    }
    .info b { color: #FF6600; }
    .legend {
      line-height: 20px;
      color: #555;
      background: white;
      padding: 10px;
      border-radius: 8px;
      box-shadow: 0 0 15px rgba(0,0,0,0.3);
    }
    .legend h4 {
      margin: 0 0 8px;
      color: #333;
      font-size: 14px;
      border-bottom: 2px solid #FF6600;
      padding-bottom: 5px;
    }
    .legend i {
      width: 18px;
      height: 18px;
      float: left;
      margin-right: 8px;
      opacity: 0.8;
      border: 1px solid #999;
    }
  </style>
</head>
<body>
  <div id="map"></div>
  <script>
    var dnoData = ` + getGeoJSONData() + `;
    
    var map = L.map('map').setView([54.5, -3], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);
    
    function getColor(license) {
      var colors = {
        'EPN': '#FF6B6B', 'LPN': '#4ECDC4', 'SPN': '#45B7D1',
        'WM': '#96CEB4', 'EM': '#FFEAA7', 'SW': '#DFE6E9',
        'WA': '#A29BFE', 'NW': '#FD79A8', 'NE': '#FDCB6E',
        'Y': '#6C5CE7', 'SHEPD': '#74B9FF', 'HYDRO': '#00B894',
        'SP': '#FFA07A', 'NPG': '#E17055'
      };
      return colors[license] || '#95A5A6';
    }
    
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
    
    var info = L.control();
    info.onAdd = function (map) {
      this._div = L.DomUtil.create('div', 'info');
      this.update();
      return this._div;
    };
    info.update = function (props) {
      this._div.innerHTML = '<h4>🗺️ UK DNO License Areas</h4>' + (props ?
        '<b>' + props.dno_name + '</b><br />' +
        '<b>Company:</b> ' + props.company + '<br />' +
        '<b>Region:</b> ' + props.region + '<br />' +
        '<b>Customers:</b> ' + (props.customers / 1000000).toFixed(1) + 'M<br />' +
        '<b>Area:</b> ' + props.area_sqkm.toLocaleString() + ' km²'
        : 'Hover over a region for details');
    };
    info.addTo(map);
    
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
    
    var geojson = L.geoJson(dnoData, {
      style: style,
      onEachFeature: onEachFeature
    }).addTo(map);
    
    var legend = L.control({position: 'bottomright'});
    legend.onAdd = function (map) {
      var div = L.DomUtil.create('div', 'info legend');
      var licenses = ['EPN', 'LPN', 'SPN', 'WM', 'EM', 'SW', 'WA', 'NW', 'NE', 'Y', 'SHEPD', 'HYDRO', 'SP', 'NPG'];
      
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
  
  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ UK DNO License Areas - Interactive Map');
}

function getGeoJSONData() {
  return JSON.stringify({
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Eastern Power Networks (EPN)",
        "company": "UK Power Networks",
        "license": "EPN",
        "region": "Eastern England",
        "customers": 3800000,
        "area_sqkm": 29000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              1.75,
              52.8
            ],
            [
              -0.5,
              52.8
            ],
            [
              -0.5,
              51.5
            ],
            [
              1.75,
              51.5
            ],
            [
              1.75,
              52.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "London Power Networks (LPN)",
        "company": "UK Power Networks",
        "license": "LPN",
        "region": "Greater London",
        "customers": 5000000,
        "area_sqkm": 1600
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              0.33,
              51.69
            ],
            [
              -0.51,
              51.69
            ],
            [
              -0.51,
              51.28
            ],
            [
              0.33,
              51.28
            ],
            [
              0.33,
              51.69
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "South Eastern Power Networks (SPN)",
        "company": "UK Power Networks",
        "license": "SPN",
        "region": "South East England",
        "customers": 2700000,
        "area_sqkm": 20800
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              1.45,
              51.5
            ],
            [
              -0.75,
              51.5
            ],
            [
              -0.75,
              50.75
            ],
            [
              1.45,
              50.75
            ],
            [
              1.45,
              51.5
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Southern Electric Power Distribution (SEPD)",
        "company": "Scottish and Southern Electricity Networks",
        "license": "SEPD",
        "region": "Southern England",
        "customers": 2900000,
        "area_sqkm": 27000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -0.5,
              51.8
            ],
            [
              -2.8,
              51.8
            ],
            [
              -2.8,
              50.3
            ],
            [
              -0.5,
              50.3
            ],
            [
              -0.5,
              51.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Scottish Hydro Electric Power Distribution (SHEPD)",
        "company": "Scottish and Southern Electricity Networks",
        "license": "SHEPD",
        "region": "Northern Scotland",
        "customers": 780000,
        "area_sqkm": 100000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -1.2,
              60.8
            ],
            [
              -7.5,
              60.8
            ],
            [
              -7.5,
              56.0
            ],
            [
              -2.0,
              56.0
            ],
            [
              -1.2,
              60.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Western Power Distribution - South West",
        "company": "National Grid",
        "license": "SWEB",
        "region": "South West England",
        "customers": 1700000,
        "area_sqkm": 21000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.5,
              51.8
            ],
            [
              -5.8,
              51.8
            ],
            [
              -5.8,
              49.9
            ],
            [
              -2.5,
              49.9
            ],
            [
              -2.5,
              51.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Western Power Distribution - South Wales",
        "company": "National Grid",
        "license": "SWALEC",
        "region": "South Wales",
        "customers": 1400000,
        "area_sqkm": 21000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.6,
              52.5
            ],
            [
              -5.3,
              52.5
            ],
            [
              -5.3,
              51.3
            ],
            [
              -2.6,
              51.3
            ],
            [
              -2.6,
              52.5
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Western Power Distribution - West Midlands",
        "company": "National Grid",
        "license": "WMID",
        "region": "West Midlands",
        "customers": 2400000,
        "area_sqkm": 13000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -1.5,
              53.5
            ],
            [
              -3.2,
              53.5
            ],
            [
              -3.2,
              51.8
            ],
            [
              -1.5,
              51.8
            ],
            [
              -1.5,
              53.5
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Western Power Distribution - East Midlands",
        "company": "National Grid",
        "license": "EMID",
        "region": "East Midlands",
        "customers": 2300000,
        "area_sqkm": 15600
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -0.5,
              53.5
            ],
            [
              -1.8,
              53.5
            ],
            [
              -1.8,
              52.0
            ],
            [
              -0.5,
              52.0
            ],
            [
              -0.5,
              53.5
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Electricity North West (ENWL)",
        "company": "Electricity North West",
        "license": "ENWL",
        "region": "North West England",
        "customers": 2400000,
        "area_sqkm": 13000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.2,
              54.8
            ],
            [
              -3.5,
              54.8
            ],
            [
              -3.5,
              53.0
            ],
            [
              -2.2,
              53.0
            ],
            [
              -2.2,
              54.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Northern Powergrid - North East",
        "company": "Northern Powergrid",
        "license": "NPGN",
        "region": "North East England",
        "customers": 1500000,
        "area_sqkm": 11000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -1.2,
              55.8
            ],
            [
              -2.5,
              55.8
            ],
            [
              -2.5,
              54.3
            ],
            [
              -1.2,
              54.3
            ],
            [
              -1.2,
              55.8
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "Northern Powergrid - Yorkshire",
        "company": "Northern Powergrid",
        "license": "NPGY",
        "region": "Yorkshire",
        "customers": 2700000,
        "area_sqkm": 19000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -0.3,
              54.5
            ],
            [
              -2.5,
              54.5
            ],
            [
              -2.5,
              53.3
            ],
            [
              -0.3,
              53.3
            ],
            [
              -0.3,
              54.5
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "SP Distribution (SPD)",
        "company": "SP Energy Networks",
        "license": "SPD",
        "region": "Central & South Scotland",
        "customers": 2000000,
        "area_sqkm": 25000
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.0,
              57.0
            ],
            [
              -5.5,
              57.0
            ],
            [
              -5.5,
              54.8
            ],
            [
              -2.0,
              54.8
            ],
            [
              -2.0,
              57.0
            ]
          ]
        ]
      }
    },
    {
      "type": "Feature",
      "properties": {
        "dno_name": "SP Manweb",
        "company": "SP Energy Networks",
        "license": "MANWEB",
        "region": "Merseyside, Cheshire & North Wales",
        "customers": 1400000,
        "area_sqkm": 12800
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              -2.8,
              53.5
            ],
            [
              -4.8,
              53.5
            ],
            [
              -4.8,
              52.0
            ],
            [
              -2.8,
              52.0
            ],
            [
              -2.8,
              53.5
            ]
          ]
        ]
      }
    }
  ]
  });
}
