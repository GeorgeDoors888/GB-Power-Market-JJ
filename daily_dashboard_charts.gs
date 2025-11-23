/**
 * GB Power Market - Daily Dashboard Charts (Auto-Updating)
 * Creates charts from Daily_Chart_Data sheet populated by Python
 * 
 * SETUP:
 * 1. Copy this code to Apps Script (Extensions → Apps Script)
 * 2. Run setupAutoRefreshTrigger() once to enable auto-refresh
 * 3. Python script updates data every 30 min → Charts auto-refresh
 */

// ==================== CONFIG ====================
const CHART_DATA_SHEET = 'Daily_Chart_Data';
const CHART_SHEET_PREFIX = 'Chart_';

// ==================== MAIN FUNCTIONS ====================

/**
 * Create menu on sheet open
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📊 Dashboard Charts')
    .addItem('🔄 Refresh All Charts', 'refreshAllCharts')
    .addItem('📈 Create Price Chart', 'createPriceChart')
    .addItem('⚡ Create Demand/Gen Chart', 'createDemandGenChart')
    .addItem('🔌 Create Import Chart', 'createImportChart')
    .addItem('📊 Create Frequency Chart', 'createFrequencyChart')
    .addSeparator()
    .addItem('⚙️ Setup Auto-Refresh', 'setupAutoRefreshTrigger')
    .addItem('🗑️ Remove Auto-Refresh', 'removeAutoRefreshTrigger')
    .addSeparator()
    .addItem('🗑️ Delete All Charts', 'deleteAllCharts')
    .addToUi();
}

/**
 * Auto-refresh trigger (runs every 30 min after setup)
 */
function autoRefreshCharts() {
  try {
    refreshAllCharts();
    Logger.log('✅ Auto-refresh complete: ' + new Date());
  } catch (err) {
    Logger.log('❌ Auto-refresh error: ' + err);
  }
}

/**
 * Refresh all charts (delete old, create new)
 */
function refreshAllCharts() {
  const ss = SpreadsheetApp.getActive();
  
  // Delete old chart sheets
  deleteAllCharts();
  
  // Create new charts
  createPriceChart();
  createDemandGenChart();
  createImportChart();
  createFrequencyChart();
  
  Logger.log('✅ All charts refreshed');
}

/**
 * Delete all chart sheets
 */
function deleteAllCharts() {
  const ss = SpreadsheetApp.getActive();
  const sheets = ss.getSheets();
  
  sheets.forEach(sheet => {
    if (sheet.getName().startsWith(CHART_SHEET_PREFIX)) {
      ss.deleteSheet(sheet);
      Logger.log('🗑️ Deleted: ' + sheet.getName());
    }
  });
}

// ==================== CHART BUILDERS ====================

/**
 * 1. Price Chart - Market Price over time
 */
function createPriceChart() {
  const ss = SpreadsheetApp.getActive();
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET);
  
  if (!dataSheet) {
    Logger.log('❌ Data sheet not found: ' + CHART_DATA_SHEET);
    return;
  }
  
  // Get or create chart sheet
  let chartSheet = ss.getSheetByName(CHART_SHEET_PREFIX + 'Prices');
  if (chartSheet) {
    ss.deleteSheet(chartSheet);
  }
  chartSheet = ss.insertSheet(CHART_SHEET_PREFIX + 'Prices');
  
  const lastRow = dataSheet.getLastRow();
  
  // Create chart (timestamp A, Market Price C)
  const chart = chartSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange(2, 1, lastRow - 1, 1)) // Date
    .addRange(dataSheet.getRange(2, 3, lastRow - 1, 1)) // Market Price
    .setPosition(2, 2, 0, 0)
    .setOption('title', '💰 Market Price (APXMIDP) - Last 30 Days')
    .setOption('titleTextStyle', {fontSize: 16, bold: true})
    .setOption('hAxis', {
      title: 'Date & Settlement Period',
      titleTextStyle: {fontSize: 12, italic: true},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Price (£/MWh)',
      titleTextStyle: {fontSize: 12, italic: true},
      minValue: 0
    })
    .setOption('series', {
      0: {color: '#34A853', lineWidth: 2, labelInLegend: 'Market Price'}
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('width', 1200)
    .setOption('height', 500)
    .setOption('curveType', 'function')
    .build();
  
  chartSheet.insertChart(chart);
  Logger.log('✅ Created: Price Chart');
}

/**
 * 2. Demand & Generation Chart
 */
function createDemandGenChart() {
  const ss = SpreadsheetApp.getActive();
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET);
  
  if (!dataSheet) return;
  
  let chartSheet = ss.getSheetByName(CHART_SHEET_PREFIX + 'Demand_Gen');
  if (chartSheet) {
    ss.deleteSheet(chartSheet);
  }
  chartSheet = ss.insertSheet(CHART_SHEET_PREFIX + 'Demand_Gen');
  
  const lastRow = dataSheet.getLastRow();
  
  // Date (A), Demand (D), Generation (E)
  const chart = chartSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange(2, 1, lastRow - 1, 1))
    .addRange(dataSheet.getRange(2, 4, lastRow - 1, 1))
    .addRange(dataSheet.getRange(2, 5, lastRow - 1, 1))
    .setPosition(2, 2, 0, 0)
    .setOption('title', '⚡ GB Demand & Generation - Last 30 Days')
    .setOption('titleTextStyle', {fontSize: 16, bold: true})
    .setOption('hAxis', {
      title: 'Date & Settlement Period',
      titleTextStyle: {fontSize: 12, italic: true},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Power (MW)',
      titleTextStyle: {fontSize: 12, italic: true},
      minValue: 0
    })
    .setOption('series', {
      0: {color: '#FBBC04', lineWidth: 2, labelInLegend: 'Demand'},
      1: {color: '#4285F4', lineWidth: 2, labelInLegend: 'Generation'}
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('width', 1200)
    .setOption('height', 500)
    .setOption('curveType', 'function')
    .build();
  
  chartSheet.insertChart(chart);
  Logger.log('✅ Created: Demand & Generation Chart');
}

/**
 * 3. Interconnector Import Chart
 */
function createImportChart() {
  const ss = SpreadsheetApp.getActive();
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET);
  
  if (!dataSheet) return;
  
  let chartSheet = ss.getSheetByName(CHART_SHEET_PREFIX + 'IC_Import');
  if (chartSheet) {
    ss.deleteSheet(chartSheet);
  }
  chartSheet = ss.insertSheet(CHART_SHEET_PREFIX + 'IC_Import');
  
  const lastRow = dataSheet.getLastRow();
  
  // Date (A), IC Import (F)
  const chart = chartSheet.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(dataSheet.getRange(2, 1, lastRow - 1, 1))
    .addRange(dataSheet.getRange(2, 6, lastRow - 1, 1))
    .setPosition(2, 2, 0, 0)
    .setOption('title', '🔌 Total Interconnector Imports - Last 30 Days')
    .setOption('titleTextStyle', {fontSize: 16, bold: true})
    .setOption('hAxis', {
      title: 'Date & Settlement Period',
      titleTextStyle: {fontSize: 12, italic: true},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Import (MW)',
      titleTextStyle: {fontSize: 12, italic: true},
      minValue: 0
    })
    .setOption('series', {
      0: {color: '#9C27B0', areaOpacity: 0.5, labelInLegend: 'IC Imports'}
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('width', 1200)
    .setOption('height', 500)
    .build();
  
  chartSheet.insertChart(chart);
  Logger.log('✅ Created: Interconnector Import Chart');
}

/**
 * 4. Frequency Chart
 */
function createFrequencyChart() {
  const ss = SpreadsheetApp.getActive();
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET);
  
  if (!dataSheet) return;
  
  let chartSheet = ss.getSheetByName(CHART_SHEET_PREFIX + 'Frequency');
  if (chartSheet) {
    ss.deleteSheet(chartSheet);
  }
  chartSheet = ss.insertSheet(CHART_SHEET_PREFIX + 'Frequency');
  
  const lastRow = dataSheet.getLastRow();
  
  // Date (A), Frequency (G)
  const chart = chartSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange(2, 1, lastRow - 1, 1))
    .addRange(dataSheet.getRange(2, 7, lastRow - 1, 1))
    .setPosition(2, 2, 0, 0)
    .setOption('title', '📊 System Frequency - Last 30 Days')
    .setOption('titleTextStyle', {fontSize: 16, bold: true})
    .setOption('hAxis', {
      title: 'Date & Settlement Period',
      titleTextStyle: {fontSize: 12, italic: true},
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxis', {
      title: 'Frequency (Hz)',
      titleTextStyle: {fontSize: 12, italic: true},
      minValue: 49.5,
      maxValue: 50.5,
      gridlines: {count: 11}
    })
    .setOption('series', {
      0: {color: '#FF6D00', lineWidth: 1.5, labelInLegend: 'Frequency (Hz)'}
    })
    .setOption('legend', {position: 'bottom'})
    .setOption('width', 1200)
    .setOption('height', 500)
    .build();
  
  chartSheet.insertChart(chart);
  
  chartSheet.getRange('A1').setValue('Target: 50.0 Hz | Operating Range: 49.8 - 50.2 Hz');
  chartSheet.getRange('A1').setFontWeight('bold').setFontSize(12);
  
  Logger.log('✅ Created: Frequency Chart');
}

// ==================== TRIGGER MANAGEMENT ====================

/**
 * Set up automatic refresh trigger (run once)
 */
function setupAutoRefreshTrigger() {
  // Delete existing triggers
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'autoRefreshCharts') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger - every 30 minutes
  ScriptApp.newTrigger('autoRefreshCharts')
    .timeBased()
    .everyMinutes(30)
    .create();
  
  Logger.log('✅ Auto-refresh trigger installed (every 30 min)');
  SpreadsheetApp.getUi().alert('✅ Trigger Installed', 'Charts will auto-refresh every 30 minutes', SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Remove automatic refresh trigger
 */
function removeAutoRefreshTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'autoRefreshCharts') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  Logger.log('🗑️ Auto-refresh trigger removed');
  SpreadsheetApp.getUi().alert('🗑️ Trigger Removed', 'Auto-refresh disabled', SpreadsheetApp.getUi().ButtonSet.OK);
}
