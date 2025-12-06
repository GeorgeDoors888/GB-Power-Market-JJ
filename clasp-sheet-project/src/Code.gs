/**
 * Main Apps Script File
 * UI Layer Only - All data processing happens in Python
 * 
 * This handles:
 * - Custom menus
 * - Button triggers
 * - Sheet formatting
 * - Layout management
 */

/**
 * Runs when spreadsheet opens
 * Creates custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Automation')
    .addItem('🔄 Refresh Data', 'triggerPythonRefresh')
    .addItem('🎨 Apply Formatting', 'applySheetFormatting')
    .addItem('📊 Update Charts', 'updateCharts')
    .addSeparator()
    .addItem('⚙️ Settings', 'openSettings')
    .addToUi();
}

/**
 * Triggers Python script via webhook
 * Python does the heavy lifting, then updates sheet
 */
function triggerPythonRefresh() {
  const ui = SpreadsheetApp.getUi();
  
  // Show loading message
  ui.alert('🔄 Refresh Started', 'Python script is running... This may take 30-60 seconds.', ui.ButtonSet.OK);
  
  try {
    // Call your Python webhook/API
    const PYTHON_WEBHOOK = PropertiesService.getScriptProperties().getProperty('PYTHON_WEBHOOK_URL');
    
    if (!PYTHON_WEBHOOK) {
      ui.alert('❌ Error', 'Webhook URL not configured. Go to Settings first.', ui.ButtonSet.OK);
      return;
    }
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        spreadsheetId: SpreadsheetApp.getActiveSpreadsheet().getId(),
        action: 'refresh_data',
        timestamp: new Date().toISOString()
      }),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(PYTHON_WEBHOOK, options);
    const result = JSON.parse(response.getContentText());
    
    if (result.success) {
      ui.alert('✅ Success', `Data refreshed!\n\n${result.message}`, ui.ButtonSet.OK);
    } else {
      ui.alert('⚠️ Warning', `Refresh completed with warnings:\n\n${result.message}`, ui.ButtonSet.OK);
    }
    
  } catch (error) {
    ui.alert('❌ Error', `Failed to refresh data:\n\n${error.message}`, ui.ButtonSet.OK);
    console.error('Refresh error:', error);
  }
}

/**
 * Apply consistent formatting to active sheet
 * Design changes handled here, not in Python
 */
function applySheetFormatting() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const ui = SpreadsheetApp.getUi();
  
  try {
    // Header row formatting
    const headerRange = sheet.getRange(1, 1, 1, sheet.getLastColumn());
    headerRange.setBackground('#1a73e8')
              .setFontColor('#ffffff')
              .setFontWeight('bold')
              .setFontSize(11)
              .setHorizontalAlignment('center')
              .setVerticalAlignment('middle');
    
    // Freeze header row
    sheet.setFrozenRows(1);
    
    // Auto-resize columns
    for (let i = 1; i <= sheet.getLastColumn(); i++) {
      sheet.autoResizeColumn(i);
    }
    
    // Alternating row colors for data
    const dataRange = sheet.getRange(2, 1, sheet.getLastRow() - 1, sheet.getLastColumn());
    dataRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, false, false);
    
    // Grid lines
    sheet.getRange(1, 1, sheet.getLastRow(), sheet.getLastColumn())
         .setBorder(true, true, true, true, true, true, '#d3d3d3', SpreadsheetApp.BorderStyle.SOLID);
    
    ui.alert('✅ Formatting Applied', 'Sheet formatting complete!', ui.ButtonSet.OK);
    
  } catch (error) {
    ui.alert('❌ Error', `Formatting failed:\n\n${error.message}`, ui.ButtonSet.OK);
    console.error('Formatting error:', error);
  }
}

/**
 * Update/create charts
 * Chart design managed here
 */
function updateCharts() {
  const sheet = SpreadsheetApp.getActiveSheet();
  const ui = SpreadsheetApp.getUi();
  
  try {
    // Example: Create a simple chart
    // Customize based on your data structure
    
    const dataRange = sheet.getRange('A1:B10'); // Adjust as needed
    
    const chart = sheet.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(dataRange)
      .setPosition(5, 5, 0, 0)
      .setOption('title', 'Revenue Over Time')
      .setOption('legend', {position: 'bottom'})
      .setOption('width', 600)
      .setOption('height', 400)
      .build();
    
    // Remove old charts
    const charts = sheet.getCharts();
    charts.forEach(c => sheet.removeChart(c));
    
    // Add new chart
    sheet.insertChart(chart);
    
    ui.alert('✅ Charts Updated', 'Chart refresh complete!', ui.ButtonSet.OK);
    
  } catch (error) {
    ui.alert('❌ Error', `Chart update failed:\n\n${error.message}`, ui.ButtonSet.OK);
    console.error('Chart error:', error);
  }
}

/**
 * Settings dialog
 * Configure Python webhook URL
 */
function openSettings() {
  const ui = SpreadsheetApp.getUi();
  const props = PropertiesService.getScriptProperties();
  
  const currentUrl = props.getProperty('PYTHON_WEBHOOK_URL') || 'Not set';
  
  const result = ui.prompt(
    '⚙️ Settings',
    `Current webhook URL:\n${currentUrl}\n\nEnter new webhook URL (or cancel to keep current):`,
    ui.ButtonSet.OK_CANCEL
  );
  
  if (result.getSelectedButton() === ui.Button.OK) {
    const newUrl = result.getResponseText().trim();
    if (newUrl) {
      props.setProperty('PYTHON_WEBHOOK_URL', newUrl);
      ui.alert('✅ Saved', `Webhook URL updated to:\n${newUrl}`, ui.ButtonSet.OK);
    }
  }
}

/**
 * Utility: Get data from specific range
 * Can be called by other functions
 */
function getSheetData(sheetName, range) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  return sheet.getRange(range).getValues();
}

/**
 * Utility: Write data to sheet
 * Called after Python processes data
 */
function writeDataToSheet(sheetName, startRow, startCol, data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  
  // Create sheet if doesn't exist
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  
  const numRows = data.length;
  const numCols = data[0].length;
  
  sheet.getRange(startRow, startCol, numRows, numCols).setValues(data);
}

/**
 * Utility: Clear sheet contents
 */
function clearSheet(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  
  if (sheet) {
    sheet.clear();
  }
}

/**
 * Create custom button in sheet
 * Example: Add this via drawing in sheet, then assign function
 */
function customButton_Refresh() {
  triggerPythonRefresh();
}

/**
 * Scheduled trigger - runs automatically
 * Set up via: Edit > Current project's triggers
 */
function scheduledRefresh() {
  // This can run hourly/daily without user interaction
  triggerPythonRefresh();
}
