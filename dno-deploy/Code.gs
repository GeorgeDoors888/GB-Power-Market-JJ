function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ DNO Map')
    .addItem('View Interactive Map', 'createDNOMap')
    .addToUi();
}

function createDNOMap() {
  var html = HtmlService.createHtmlOutput(
    '<!DOCTYPE html>' +
    '<html><head>' +
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>' +
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>' +
    '<style>body{margin:0;padding:0}#map{height:100vh;width:100%}</style>' +
    '</head><body><div id="map"></div><script>' +
    'var map=L.map("map").setView([54.5,-3],6);' +
    'L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(map);' +
    'fetch("https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/gb_power_map_deployment/dno_regions.geojson")' +
    '.then(r=>r.json()).then(d=>{' +
    'L.geoJSON(d,{style:f=>({fillColor:["#FF6B6B","#4ECDC4","#45B7D1","#FFA07A","#98D8C8","#F7DC6F","#BB8FCE","#85C1E9","#F8B739","#52B788","#E76F51","#2A9D8F","#264653","#E9C46A"][f.properties.mpan_id%14],weight:2,opacity:1,color:"#666",fillOpacity:0.6}),onEachFeature:(f,l)=>{l.bindPopup("<b>"+f.properties.dno_name+"</b><br/>MPAN: "+f.properties.mpan_id)}}).addTo(map);' +
    '});' +
    '</script></body></html>'
  ).setWidth(1200).setHeight(800);
  
  SpreadsheetApp.getUi().showModalDialog(html, '🗺️ UK DNO Map');
}
