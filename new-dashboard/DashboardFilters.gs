/**
 * DashboardFilters.gs
 * ==================
 * Interactive filter handlers for Dashboard V2
 * Responds to dropdown changes in filter bar (Row 3)
 */

// Configuration
const FILTER_ROW = 3;
const TIME_RANGE_COL = 2;  // Column B
const REGION_COL = 4;      // Column D
const ALERT_COL = 6;       // Column F

/**
 * Trigger when user changes a cell
 */
function onEdit(e) {
  if (!e) return;
  
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // Only process Dashboard sheet, Row 3 (filter bar)
  if (sheet.getName() !== "Dashboard" || range.getRow() !== FILTER_ROW) {
    return;
  }
  
  const col = range.getColumn();
  const value = range.getValue();
  
  // Handle filter changes
  if (col === TIME_RANGE_COL) {
    handleTimeRangeChange(sheet, value);
  } else if (col === REGION_COL) {
    handleRegionChange(sheet, value);
  } else if (col === ALERT_COL) {
    handleAlertChange(sheet, value);
  }
}

/**
 * Handle time range filter change
 */
function handleTimeRangeChange(sheet, timeRange) {
  Logger.log(`Time range changed to: ${timeRange}`);
  
  // Add timestamp to show filter is active
  const now = new Date();
  sheet.getRange("A2").setValue(`Last updated: ${Utilities.formatDate(now, "GMT", "yyyy-MM-dd HH:mm:ss")} | Filter: ${timeRange}`);
  
  // TODO: Trigger data refresh based on time range
  // This would call your Python updater scripts with time parameters
  // For now, just log and update timestamp
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Time filter set to: ${timeRange}`,
    "Filter Applied",
    3
  );
}

/**
 * Handle region filter change
 */
function handleRegionChange(sheet, region) {
  Logger.log(`Region changed to: ${region}`);
  
  // Hide/show rows based on region
  // For "All GB", show all data
  // For specific region, filter data (would need region column in data)
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Region filter set to: ${region}`,
    "Filter Applied",
    3
  );
  
  // TODO: Implement region filtering logic
  // This might involve filtering the generation/outages data by region
}

/**
 * Handle alert filter change
 */
function handleAlertChange(sheet, alertType) {
  Logger.log(`Alert type changed to: ${alertType}`);
  
  const outagesStartRow = 32;  // Row where outages data starts
  const outagesEndRow = 42;    // Last row of outages
  
  // Show/hide rows based on alert type
  if (alertType === "Critical Only") {
    // Hide rows with capacity < 500 MW (column B)
    for (let row = outagesStartRow; row <= outagesEndRow; row++) {
      const capacity = sheet.getRange(row, 2).getValue();  // Column B
      
      if (typeof capacity === 'number') {
        if (capacity < 500) {
          sheet.hideRows(row);
        } else {
          sheet.showRows(row);
        }
      }
    }
  } else if (alertType === "All") {
    // Show all rows
    sheet.showRows(outagesStartRow, outagesEndRow - outagesStartRow + 1);
  }
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Alert filter set to: ${alertType}`,
    "Filter Applied",
    3
  );
}

/**
 * Create custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Dashboard')
    .addItem('🔄 Refresh All Data', 'refreshAllData')
    .addItem('⚠️ Show Critical Outages', 'showCriticalOutages')
    .addItem('📊 Reset Filters', 'resetFilters')
    .addSeparator()
    .addItem('ℹ️ About Dashboard', 'showAbout')
    .addToUi();
}

/**
 * Refresh all data (calls Python automation)
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Triggering data refresh... This may take 30-60 seconds.',
    'Refreshing',
    5
  );
  
  // TODO: Trigger webhook or Cloud Function to run Python updater scripts
  // For now, just update timestamp
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  const now = new Date();
  sheet.getRange("A2").setValue(`Manual refresh requested: ${Utilities.formatDate(now, "GMT", "yyyy-MM-dd HH:mm:ss")}`);
  
  Logger.log("Data refresh triggered");
}

/**
 * Quick filter to show only critical outages
 */
function showCriticalOutages() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Set alert filter to "Critical Only"
  sheet.getRange(FILTER_ROW, ALERT_COL).setValue("Critical Only");
  
  // This will trigger onEdit and apply the filter
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Showing only critical outages (>500 MW)',
    'Filter Applied',
    3
  );
}

/**
 * Reset all filters to defaults
 */
function resetFilters() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Reset to defaults
  sheet.getRange(FILTER_ROW, TIME_RANGE_COL).setValue("Real-Time (10 min)");
  sheet.getRange(FILTER_ROW, REGION_COL).setValue("All GB");
  sheet.getRange(FILTER_ROW, ALERT_COL).setValue("All");
  
  // Show all hidden rows
  const outagesStartRow = 32;
  const outagesEndRow = 42;
  sheet.showRows(outagesStartRow, outagesEndRow - outagesStartRow + 1);
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'All filters reset to defaults',
    'Filters Reset',
    3
  );
}

/**
 * Show about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    '⚡ GB Energy Dashboard V2',
    '\\n' +
    'Real-time GB power market insights\\n\\n' +
    'Features:\\n' +
    '• Live generation data by fuel type\\n' +
    '• Interconnector flows\\n' +
    '• Critical outages tracking\\n' +
    '• Interactive filters\\n\\n' +
    'Data updates every 5-10 minutes via automation.\\n\\n' +
    'Last updated: ' + new Date().toLocaleString(),
    ui.ButtonSet.OK
  );
}

/**
 * Apply conditional formatting programmatically
 * (Alternative to API method)
 */
function applyConditionalFormatting() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Remove existing rules
  const rules = sheet.getConditionalFormatRules();
  sheet.clearConditionalFormatRules();
  
  // Rule 1: Critical outages (B32:B42 > 500)
  const criticalRange = sheet.getRange("B32:B42");
  const criticalRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(500)
    .setBackground("#FFB3B3")
    .setBold(true)
    .setRanges([criticalRange])
    .build();
  
  // Rule 2: High generation (B10:B18 > 5000)
  const highGenRange = sheet.getRange("B10:B18");
  const highGenRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(5000)
    .setBackground("#B3E6B3")
    .setBold(true)
    .setRanges([highGenRange])
    .build();
  
  // Apply rules
  const newRules = [criticalRule, highGenRule];
  sheet.setConditionalFormatRules(newRules);
  
  Logger.log("Conditional formatting applied");
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Conditional formatting rules applied',
    'Formatting Updated',
    3
  );
}

/**
 * Setup data validation programmatically
 * (Alternative to API method)
 */
function setupDataValidation() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Time range validation (B3)
  const timeValues = ["Real-Time (10 min)", "24 h", "48 h", "7 days", "30 days"];
  const timeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(timeValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("B3").setDataValidation(timeRule);
  
  // Region validation (D3)
  const regionValues = [
    "All GB", "NGET East", "SPEN Scotland", "WPD South West",
    "SSE North", "UKPN East", "ENW North West", "NGED Midlands"
  ];
  const regionRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(regionValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("D3").setDataValidation(regionRule);
  
  // Alert validation (F3)
  const alertValues = ["All", "Critical Only", "Wind Warning", "Outages", "Price Spike"];
  const alertRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(alertValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("F3").setDataValidation(alertRule);
  
  Logger.log("Data validation setup complete");
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Dropdown filters configured',
    'Validation Setup',
    3
  );
}

/**
 * Initialize dashboard (run once after deployment)
 */
function initializeDashboard() {
  setupDataValidation();
  applyConditionalFormatting();
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Dashboard initialization complete!',
    'Setup Complete',
    5
  );
}
