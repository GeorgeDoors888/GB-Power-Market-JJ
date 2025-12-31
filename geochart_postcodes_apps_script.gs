/**
 * Automatically create Google Geo Chart from postcode constraint data
 * Run this function once to add chart to dashboard
 */
function createConstraintGeoChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('Constraint Geo Map');
  
  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "Constraint Geo Map" sheet not found');
    return;
  }
  
  // Get data range
  var lastRow = dataSheet.getLastRow();
  
  // Remove any existing charts first
  var charts = dataSheet.getCharts();
  for (var i = 0; i < charts.length; i++) {
    dataSheet.removeChart(charts[i]);
  }
  
  // Create geo chart with UK postcodes
  var range = dataSheet.getRange('A1:B' + lastRow);
  var chart = dataSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(range)
    .setPosition(2, 7, 0, 0)
    .setOption('region', 'GB')
    .setOption('displayMode', 'markers')
    .setOption('colorAxis', {
      colors: ['#ffffff', '#ffcccc', '#ff6666', '#ff0000']
    })
    .setOption('title', 'GB Constraint Costs by Postcode (Last 7 Days)')
    .build();
  
  dataSheet.insertChart(chart);
  
  SpreadsheetApp.getUi().alert(
    'Chart Created!',
    'Geo Chart created using UK postcodes.\n\n' +
    'The map shows constraint locations across GB.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Add menu item to easily create chart
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Constraint Maps')
    .addItem('Create Geo Chart', 'createConstraintGeoChart')
    .addToUi();
}
