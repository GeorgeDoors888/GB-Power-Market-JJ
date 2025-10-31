/**
 * Google Apps Script for GB Power Market Dashboard
 * Automatically creates and updates charts from settlement period data
 * 
 * INSTALLATION:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Delete any existing code
 * 4. Paste this entire script
 * 5. Save (Ctrl/Cmd + S)
 * 6. Run 'createAllCharts' once to create initial charts
 * 7. Set up trigger: Click Clock icon > Add Trigger > updateCharts > Time-driven > Every 30 minutes
 */

// Configuration
const SHEET_NAME = 'Sheet1';
const DATA_RANGE = 'A19:D28'; // SP, Generation, Frequency, Price (excluding header)
const CHART_START_ROW = 35; // Where to place charts (below REMIT data)
const CHART_START_COL = 10; // Column J

/**
 * Create all dashboard charts
 * Run this once manually after pasting the script
 */
function createAllCharts() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  
  // Delete existing charts first
  const charts = sheet.getCharts();
  charts.forEach(chart => sheet.removeChart(chart));
  
  console.log('Creating charts...');
  
  // Chart 1: Generation Over Settlement Periods
  createGenerationChart(sheet);
  
  // Chart 2: Frequency Over Settlement Periods
  createFrequencyChart(sheet);
  
  // Chart 3: Price Over Settlement Periods
  createPriceChart(sheet);
  
  // Chart 4: Combined Overview (Small)
  createCombinedChart(sheet);
  
  SpreadsheetApp.getUi().alert('✅ Charts created successfully!\n\nCharts will auto-update when data changes.');
}

/**
 * Update all charts (called by trigger every 30 minutes)
 */
function updateCharts() {
  console.log('Charts auto-update when data changes - no action needed');
  // Charts automatically update when source data changes
  // This function exists for the trigger, but charts update themselves
}

/**
 * Chart 1: Generation Over Settlement Periods
 */
function createGenerationChart(sheet) {
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A19:A28')) // Settlement Periods (X-axis)
    .addRange(sheet.getRange('B19:B28')) // Generation (Y-axis)
    .setPosition(CHART_START_ROW, CHART_START_COL, 0, 0)
    .setOption('title', '📊 Generation by Settlement Period')
    .setOption('titleTextStyle', {fontSize: 14, bold: true})
    .setOption('hAxis', {
      title: 'Settlement Period',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9}
    })
    .setOption('vAxis', {
      title: 'Generation (GW)',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9},
      minValue: 0
    })
    .setOption('legend', {position: 'none'})
    .setOption('width', 400)
    .setOption('height', 250)
    .setOption('colors', ['#4285F4']) // Google Blue
    .setOption('lineWidth', 3)
    .setOption('pointSize', 5)
    .setOption('curveType', 'function') // Smooth curves
    .setOption('backgroundColor', '#F9F9F9')
    .setOption('chartArea', {width: '75%', height: '65%'})
    .build();
  
  sheet.insertChart(chart);
  console.log('✅ Generation chart created');
}

/**
 * Chart 2: Frequency Over Settlement Periods
 */
function createFrequencyChart(sheet) {
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(sheet.getRange('A19:A28')) // Settlement Periods (X-axis)
    .addRange(sheet.getRange('C19:C28')) // Frequency (Y-axis)
    .setPosition(CHART_START_ROW, CHART_START_COL + 7, 0, 0) // Next to Generation chart
    .setOption('title', '⚡ System Frequency by Settlement Period')
    .setOption('titleTextStyle', {fontSize: 14, bold: true})
    .setOption('hAxis', {
      title: 'Settlement Period',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9}
    })
    .setOption('vAxis', {
      title: 'Frequency (Hz)',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9},
      minValue: 49.8,
      maxValue: 50.2,
      gridlines: {count: 5}
    })
    .setOption('legend', {position: 'none'})
    .setOption('width', 400)
    .setOption('height', 250)
    .setOption('colors', ['#EA4335']) // Google Red
    .setOption('lineWidth', 3)
    .setOption('pointSize', 5)
    .setOption('curveType', 'function')
    .setOption('backgroundColor', '#F9F9F9')
    .setOption('chartArea', {width: '75%', height: '65%'})
    .build();
  
  sheet.insertChart(chart);
  console.log('✅ Frequency chart created');
}

/**
 * Chart 3: Price Over Settlement Periods
 */
function createPriceChart(sheet) {
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(sheet.getRange('A19:A28')) // Settlement Periods (X-axis)
    .addRange(sheet.getRange('D19:D28')) // Price (Y-axis)
    .setPosition(CHART_START_ROW + 15, CHART_START_COL, 0, 0) // Below Generation chart
    .setOption('title', '💷 System Sell Price by Settlement Period')
    .setOption('titleTextStyle', {fontSize: 14, bold: true})
    .setOption('hAxis', {
      title: 'Settlement Period',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9}
    })
    .setOption('vAxis', {
      title: 'Price (£/MWh)',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9},
      minValue: 0
    })
    .setOption('legend', {position: 'none'})
    .setOption('width', 400)
    .setOption('height', 250)
    .setOption('colors', ['#FBBC04']) // Google Yellow
    .setOption('backgroundColor', '#F9F9F9')
    .setOption('chartArea', {width: '75%', height: '65%'})
    .setOption('bar', {groupWidth: '75%'})
    .build();
  
  sheet.insertChart(chart);
  console.log('✅ Price chart created');
}

/**
 * Chart 4: Combined Overview (All metrics on one chart)
 */
function createCombinedChart(sheet) {
  // Note: This uses a combo chart with different Y-axes
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.COMBO)
    .addRange(sheet.getRange('A19:D28')) // All data
    .setPosition(CHART_START_ROW + 15, CHART_START_COL + 7, 0, 0) // Below Frequency chart
    .setOption('title', '📈 Combined Settlement Period Overview')
    .setOption('titleTextStyle', {fontSize: 14, bold: true})
    .setOption('hAxis', {
      title: 'Settlement Period',
      titleTextStyle: {fontSize: 11, italic: false},
      textStyle: {fontSize: 9}
    })
    .setOption('vAxes', {
      0: {title: 'Generation (GW) / Price (£/MWh)', textStyle: {fontSize: 9}},
      1: {title: 'Frequency (Hz)', textStyle: {fontSize: 9}, minValue: 49.8, maxValue: 50.2}
    })
    .setOption('series', {
      0: {type: 'line', targetAxisIndex: 0, color: '#4285F4', lineWidth: 2}, // Generation
      1: {type: 'line', targetAxisIndex: 1, color: '#EA4335', lineWidth: 2}, // Frequency
      2: {type: 'bars', targetAxisIndex: 0, color: '#FBBC04'} // Price
    })
    .setOption('legend', {position: 'bottom', textStyle: {fontSize: 9}})
    .setOption('width', 400)
    .setOption('height', 250)
    .setOption('backgroundColor', '#F9F9F9')
    .setOption('chartArea', {width: '70%', height: '55%'})
    .setOption('curveType', 'function')
    .build();
  
  sheet.insertChart(chart);
  console.log('✅ Combined chart created');
}

/**
 * Create a custom menu in Google Sheets
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Dashboard Charts')
      .addItem('🔄 Recreate All Charts', 'createAllCharts')
      .addItem('📊 Update Data (Manual)', 'updateCharts')
      .addSeparator()
      .addItem('ℹ️ About', 'showAbout')
      .addToUi();
}

/**
 * Show information dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    '⚡ GB Power Market Dashboard Charts',
    '📊 This script automatically creates and updates charts from settlement period data.\n\n' +
    '✅ Charts update automatically when data changes\n' +
    '🔄 Run "Recreate All Charts" to rebuild charts\n' +
    '⏰ Set up a time-driven trigger for automatic updates\n\n' +
    'Data Range: A19:D28 (Settlement Periods)\n' +
    'Charts Created: 4 (Generation, Frequency, Price, Combined)',
    ui.ButtonSet.OK
  );
}

/**
 * Delete all charts (cleanup function)
 */
function deleteAllCharts() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const charts = sheet.getCharts();
  
  charts.forEach(chart => sheet.removeChart(chart));
  
  SpreadsheetApp.getUi().alert(`✅ Deleted ${charts.length} charts`);
  console.log(`Deleted ${charts.length} charts`);
}

/**
 * Test function to verify data range
 */
function testDataRange() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const data = sheet.getRange(DATA_RANGE).getValues();
  
  console.log('Testing data range:', DATA_RANGE);
  console.log('Rows found:', data.length);
  console.log('First row:', data[0]);
  console.log('Last row:', data[data.length - 1]);
  
  SpreadsheetApp.getUi().alert(
    'Data Range Test',
    `Range: ${DATA_RANGE}\n` +
    `Rows: ${data.length}\n` +
    `First: ${data[0]}\n` +
    `Last: ${data[data.length - 1]}`,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
