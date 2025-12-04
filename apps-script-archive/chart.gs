/**
 * Builds the main combo chart on the 'Dashboard' sheet.
 * This function is designed to be called from the custom menu.
 */
function buildDashboardChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboardSheet = ss.getSheetByName('Dashboard');
  var chartDataSheet = ss.getSheetByName('Chart Data');

  if (!dashboardSheet || !chartDataSheet) {
    SpreadsheetApp.getUi().alert('Required sheets ("Dashboard", "Chart Data") not found.');
    return;
  }

  // Log the start of the action
  logAudit('Rebuild Chart', 'Starting chart build process.', 'In Progress');

  try {
    // Remove existing charts to avoid duplicates
    var charts = dashboardSheet.getCharts();
    charts.forEach(function(chart) {
      dashboardSheet.removeChart(chart);
    });

    // Define the data ranges for the chart
    var dataRange = chartDataSheet.getRange('A1:J49'); // As per the plan
    
    // Create the combo chart
    var chartBuilder = dashboardSheet.newChart()
      .setChartType(Charts.ChartType.COMBO)
      .addRange(dataRange)
      .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
      .setTransposeRowsAndColumns(false)
      .setNumHeaders(1)
      .setOption('title', 'GB Market Overview')
      .setOption('titleTextStyle', { color: '#333', fontSize: 18, bold: true })
      .setOption('legend', { position: 'bottom' })
      .setOption('series', {
        // Left Axis (MW)
        2: {type: 'area', color: '#4285F4', targetAxisIndex: 0}, // Demand
        3: {type: 'area', color: '#DB4437', targetAxisIndex: 0}, // Generation
        4: {type: 'area', color: '#F4B400', targetAxisIndex: 0}, // IC Flow
        5: {type: 'line', color: '#0F9D58', targetAxisIndex: 0, lineDashStyle: [4, 4]}, // BM Actions
        6: {type: 'line', color: '#9E9E9E', targetAxisIndex: 0, lineDashStyle: [4, 4]}, // VLP Revenue
        // Right Axis (£/MWh)
        0: {type: 'line', color: '#3367D6', targetAxisIndex: 1}, // DA Price
        1: {type: 'line', color: '#C62828', targetAxisIndex: 1}  // Imbalance Price
      })
      .setOption('vAxes', {
        0: {title: 'Power (MW)', textStyle: {color: '#555'}},
        1: {title: 'Price (£/MWh)', format: '£#,##0', textStyle: {color: '#555'}}
      })
      .setOption('hAxis', {title: 'Settlement Period'})
      .setPosition(5, 12, 0, 0); // Anchor at L5

    // Build the chart
    dashboardSheet.insertChart(chartBuilder.build());
    
    SpreadsheetApp.getUi().alert('✅ Dashboard chart has been rebuilt successfully!');
    logAudit('Rebuild Chart', 'Chart created and inserted at L5.', 'Success');

  } catch (e) {
    SpreadsheetApp.getUi().alert('❌ Failed to build chart: ' + e.message);
    logAudit('Rebuild Chart', 'Error during chart construction.', 'Error', e.message);
  }
}
