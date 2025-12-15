
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
