
/**
 * Automatically create Google Geo Chart from constraint data
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

  // Create minimal geo chart
  var chart = Charts.newGeoChart()
    .setDataTable(Charts.newDataTable()
      .addColumn(Charts.ColumnType.STRING, 'Region')
      .addColumn(Charts.ColumnType.NUMBER, 'Volume')
      .build())
    .setOption('width', 600)
    .setOption('height', 400)
    .build();

  // Actually, use the built-in chart builder instead
  var range = dataSheet.getRange('A1:B' + lastRow);
  var chartBuilder = dataSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(range)
    .setPosition(2, 7, 0, 0);

  dataSheet.insertChart(chartBuilder.build());

  SpreadsheetApp.getUi().alert('Chart created! Check column G.');
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
