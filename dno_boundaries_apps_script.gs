/**
 * Automatically create DNO Boundaries Geo Chart from postcode data
 * Shows Distribution Network Operator coverage areas across GB
 * Each DNO gets a unique color for boundary identification
 */
function createDnoBoundariesChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('DNO Boundaries Map');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "DNO Boundaries Map" sheet not found');
    return;
  }

  // Remove any existing charts first
  var charts = dataSheet.getCharts();
  for (var i = 0; i < charts.length; i++) {
    dataSheet.removeChart(charts[i]);
  }

  // Get all data
  var lastRow = dataSheet.getLastRow();
  var data = dataSheet.getRange('A1:H' + lastRow).getValues();

  // Define DNO colors
  var dnoColors = {
    'Eastern Power Networks (EPN)': '#FF6B6B',
    'National Grid Electricity Distribution (East Midlands) Plc': '#4ECDC4',
    'Northern Powergrid (Yorkshire) plc': '#45B7D1',
    'SCOTTISH HYDRO ELECTRIC POWER DISTRIBUTION PLC': '#FFA07A',
    'SOUTHERN ELECTRIC POWER DISTRIBUTION PLC': '#98D8C8',
    'National Grid Electricity Distribution (West Midlands) Plc': '#F7DC6F',
    'Northern Powergrid (Northeast) plc': '#BB8FCE',
    'South Eastern Power Networks (SPN)': '#85C1E2',
    'SP Distribution Ltd': '#F8B739',
    'ELECTRICITY NORTH WEST LIMITED': '#52B788',
    'South Wales Electricity Limited': '#E63946',
    'London Power Networks (LPN)': '#A8DADC',
    'SP Manweb plc': '#457B9D',
    'Western Power Distribution (South West) plc': '#E76F51'
  };

  // Create a helper sheet with DNO color coding
  var helperSheet;
  try {
    helperSheet = ss.getSheetByName('DNO Color Helper');
    helperSheet.clear();
  } catch(e) {
    helperSheet = ss.insertSheet('DNO Color Helper');
  }

  // Prepare data with color codes (convert DNO to numeric code)
  var helperData = [['Postcode', 'DNO Code', 'DNO Name', 'Capacity']];
  var dnoList = [];
  var dnoIndex = {};
  var dnoCode = 1;

  // Skip header
  for (var i = 1; i < data.length; i++) {
    var postcode = data[i][0];
    var capacity = data[i][1];
    var dno = data[i][3];

    if (!dnoIndex[dno]) {
      dnoIndex[dno] = dnoCode++;
      dnoList.push(dno);
    }

    helperData.push([postcode, dnoIndex[dno], dno, capacity]);
  }

  // Write helper data
  helperSheet.getRange(1, 1, helperData.length, 4).setValues(helperData);

  // Create geo chart using helper data
  var helperRange = helperSheet.getRange('A1:B' + helperData.length);
  var chart = helperSheet.newChart()
    .setChartType(Charts.ChartType.GEO)
    .addRange(helperRange)
    .setPosition(1, 6, 0, 0)
    .setOption('displayMode', 'markers')
    .setOption('colorAxis', {
      minValue: 1,
      maxValue: dnoCode - 1,
      colors: ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F',
               '#BB8FCE', '#85C1E2', '#F8B739', '#52B788', '#E63946', '#A8DADC',
               '#457B9D', '#E76F51']
    })
    .setOption('sizeAxis', {minValue: 0, maxSize: 8})
    .setOption('title', 'DNO Boundaries - Each Color = Different DNO')
    .setOption('width', 900)
    .setOption('height', 700)
    .build();

  helperSheet.insertChart(chart);

  // Create legend on helper sheet
  var legendData = [['DNO', 'Color Code']];
  for (var i = 0; i < dnoList.length; i++) {
    legendData.push([dnoList[i], i + 1]);
  }
  helperSheet.getRange(1, 10, legendData.length, 2).setValues(legendData);

  // Format legend header
  helperSheet.getRange('J1:K1').setBackground('#4285F4').setFontColor('#FFFFFF').setFontWeight('bold');

  SpreadsheetApp.getUi().alert(
    'DNO Map Created!',
    'Geo Chart shows DNO boundaries with unique colors.\n\n' +
    'Check "DNO Color Helper" sheet for:\n' +
    '• Map visualization\n' +
    '• Legend showing which color = which DNO\n\n' +
    'Each marker color represents a different DNO area.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Create comparison chart showing DNO total capacities
 */
function createDnoComparisonChart() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dataSheet = ss.getSheetByName('DNO Boundaries Map');

  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('Error: "DNO Boundaries Map" sheet not found');
    return;
  }

  // Aggregate by DNO
  var data = dataSheet.getDataRange().getValues();
  var dnoTotals = {};

  // Skip header row
  for (var i = 1; i < data.length; i++) {
    var dno = data[i][3];  // Column D
    var capacity = data[i][1];  // Column B

    if (dno && capacity) {
      if (!dnoTotals[dno]) {
        dnoTotals[dno] = 0;
      }
      dnoTotals[dno] += capacity;
    }
  }

  // Create summary sheet
  var summarySheet;
  try {
    summarySheet = ss.getSheetByName('DNO Summary');
    summarySheet.clear();
  } catch(e) {
    summarySheet = ss.insertSheet('DNO Summary');
  }

  // Write summary data
  var summaryData = [['DNO', 'Total Capacity (MW)']];
  for (var dno in dnoTotals) {
    summaryData.push([dno, dnoTotals[dno]]);
  }
  summarySheet.getRange(1, 1, summaryData.length, 2).setValues(summaryData);

  // Create bar chart
  var summaryRange = summarySheet.getRange('A1:B' + summaryData.length);
  var barChart = summarySheet.newChart()
    .setChartType(Charts.ChartType.BAR)
    .addRange(summaryRange)
    .setPosition(2, 4, 0, 0)
    .setOption('title', 'DNO Generation Capacity Comparison')
    .setOption('hAxis', {title: 'Capacity (MW)'})
    .setOption('vAxis', {title: 'DNO'})
    .setOption('legend', {position: 'none'})
    .setOption('width', 600)
    .setOption('height', 400)
    .build();

  summarySheet.insertChart(barChart);

  SpreadsheetApp.getUi().alert('DNO comparison chart created on "DNO Summary" sheet!');
}

/**
 * Add menu items
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ DNO Maps')
    .addItem('Create Boundary Map', 'createDnoBoundariesChart')
    .addItem('Create Comparison Chart', 'createDnoComparisonChart')
    .addToUi();
}
