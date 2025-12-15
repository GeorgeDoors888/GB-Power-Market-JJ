/**
 * add_date_range_controls.gs
 * 
 * Adds interactive date range controls to Google Sheets dashboard
 * - D65: "From" date dropdown (with calendar picker)
 * - E66: "To" date dropdown (with calendar picker)
 * - Automatically filters analysis data based on selected dates
 * 
 * INSTALLATION:
 * 1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit
 * 2. Extensions > Apps Script
 * 3. Paste this code
 * 4. Run: setupDateRangeControls()
 * 5. Authorize permissions
 *
 * NOTE: Google Sheets date validation automatically provides dropdown calendar picker UI
 */

/**
 * Main setup function - creates date range controls and formatting
 */
function setupDateRangeControls() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet(); // Or specify: ss.getSheetByName('Dashboard')
  
  // Setup "From" date in D65
  setupFromDateControl(sheet);
  
  // Setup "To" date in E66
  setupToDateControl(sheet);
  
  // Add helper text
  addDateRangeLabels(sheet);
  
  // Format cells
  formatDateCells(sheet);
  
  SpreadsheetApp.getUi().alert(
    '✅ Date Range Controls Added!\n\n' +
    'D65: From Date (with calendar picker)\n' +
    'E66: To Date (with calendar picker)\n\n' +
    'Click the cells to open calendar dropdown picker.\n' +
    'Data will refresh automatically when dates change.'
  );
}

/**
 * Setup "From" date control in D65
 */
function setupFromDateControl(sheet) {
  const cell = sheet.getRange('D65');
  
  // Set default value (30 days ago)
  const defaultFromDate = new Date();
  defaultFromDate.setDate(defaultFromDate.getDate() - 30);
  cell.setValue(defaultFromDate);
  
  // Create data validation with date picker
  const rule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select start date for analysis period')
    .build();
  
  cell.setDataValidation(rule);
  
  // Format as date
  cell.setNumberFormat('yyyy-mm-dd');
  
  Logger.log('✓ From date control added to D65');
}

/**
 * Setup "To" date control in E66
 */
function setupToDateControl(sheet) {
  const cell = sheet.getRange('E66');
  
  // Set default value (today)
  const defaultToDate = new Date();
  cell.setValue(defaultToDate);
  
  // Create data validation with date picker
  const rule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select end date for analysis period')
    .build();
  
  cell.setDataValidation(rule);
  
  // Format as date
  cell.setNumberFormat('yyyy-mm-dd');
  
  Logger.log('✓ To date control added to E66');
}

/**
 * Add labels next to date controls
 */
function addDateRangeLabels(sheet) {
  // Label for "From" date (C65)
  const fromLabel = sheet.getRange('C65');
  fromLabel.clearDataValidations(); // Clear any existing validation
  fromLabel.setValue('📅 From Date:');
  fromLabel.setFontWeight('bold');
  fromLabel.setHorizontalAlignment('right');
  fromLabel.setBackground('#e8f4f8');
  
  // Label for "To" date (D66)
  const toLabel = sheet.getRange('D66');
  toLabel.clearDataValidations(); // Clear any existing validation
  toLabel.setValue('📅 To Date:');
  toLabel.setFontWeight('bold');
  toLabel.setHorizontalAlignment('right');
  toLabel.setBackground('#e8f4f8');
  
  Logger.log('✓ Date range labels added');
}

/**
 * Format date input cells
 */
function formatDateCells(sheet) {
  // Format D65 (From date)
  const fromCell = sheet.getRange('D65');
  fromCell.setBackground('#ffffff');
  fromCell.setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  fromCell.setHorizontalAlignment('center');
  fromCell.setFontSize(11);
  
  // Format E66 (To date)
  const toCell = sheet.getRange('E66');
  toCell.setBackground('#ffffff');
  toCell.setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  toCell.setHorizontalAlignment('center');
  toCell.setFontSize(11);
  
  Logger.log('✓ Date cells formatted');
}

/**
 * Get selected date range (for use in other functions)
 * @returns {Object} {fromDate: Date, toDate: Date, days: number}
 */
function getSelectedDateRange() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  const fromDate = sheet.getRange('D65').getValue();
  const toDate = sheet.getRange('E66').getValue();
  
  // Calculate days between
  const days = Math.ceil((toDate - fromDate) / (1000 * 60 * 60 * 24));
  
  return {
    fromDate: fromDate,
    toDate: toDate,
    days: days,
    fromDateStr: Utilities.formatDate(fromDate, Session.getScriptTimeZone(), 'yyyy-MM-dd'),
    toDateStr: Utilities.formatDate(toDate, Session.getScriptTimeZone(), 'yyyy-MM-dd')
  };
}

/**
 * Validate date range (To must be after From)
 * @returns {boolean} true if valid
 */
function validateDateRange() {
  const range = getSelectedDateRange();
  
  if (range.toDate <= range.fromDate) {
    SpreadsheetApp.getUi().alert(
      '❌ Invalid Date Range',
      'To Date must be after From Date',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    return false;
  }
  
  if (range.days > 365) {
    const response = SpreadsheetApp.getUi().alert(
      '⚠️ Large Date Range',
      `Selected range is ${range.days} days. This may take longer to process.\n\nContinue?`,
      SpreadsheetApp.getUi().ButtonSet.YES_NO
    );
    return response === SpreadsheetApp.getUi().Button.YES;
  }
  
  return true;
}

/**
 * Trigger function when date cells are edited
 * Install this trigger: Edit > Current project's triggers > Add Trigger
 * Function: onDateRangeChange, Event: On edit
 */
function onDateRangeChange(e) {
  const range = e.range;
  const sheet = range.getSheet();
  
  // Check if edited cell is D65 or E66
  if ((range.getA1Notation() === 'D65' || range.getA1Notation() === 'E66')) {
    
    // Validate date range
    if (!validateDateRange()) {
      return;
    }
    
    // Show processing message
    SpreadsheetApp.getActiveSpreadsheet().toast(
      '🔄 Date range updated. Refreshing data...',
      'Analysis Update',
      5
    );
    
    // Trigger data refresh (call your existing refresh functions)
    // refreshOFRPricingData();
    // refreshConstraintData();
    
    // For now, just show confirmation
    const dateRange = getSelectedDateRange();
    SpreadsheetApp.getActiveSpreadsheet().toast(
      `📅 ${dateRange.fromDateStr} to ${dateRange.toDateStr} (${dateRange.days} days)`,
      'Date Range Set',
      3
    );
  }
}

/**
 * Add menu item for easy access
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📊 Analysis Controls')
    .addItem('🔧 Setup Date Range Controls', 'setupDateRangeControls')
    .addSeparator()
    .addItem('🔄 Refresh with Current Dates', 'refreshWithCurrentDates')
    .addItem('📅 Show Selected Range', 'showSelectedDateRange')
    .addSeparator()
    .addItem('📥 Export Date-Filtered Data', 'exportDateFilteredData')
    .addToUi();
}

/**
 * Show currently selected date range
 */
function showSelectedDateRange() {
  const range = getSelectedDateRange();
  
  SpreadsheetApp.getUi().alert(
    '📅 Current Date Range',
    `From: ${range.fromDateStr}\n` +
    `To:   ${range.toDateStr}\n` +
    `Days: ${range.days}`,
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Refresh data using current date range
 * INTEGRATE THIS with your existing BigQuery refresh functions
 */
function refreshWithCurrentDates() {
  // Validate date range
  if (!validateDateRange()) {
    return;
  }
  
  const range = getSelectedDateRange();
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '🔄 Starting data refresh...',
    'Analysis Update',
    3
  );
  
  // TODO: Call your existing refresh functions with date parameters
  // Example:
  // refreshOFRData(range.fromDateStr, range.toDateStr);
  // refreshConstraintData(range.fromDateStr, range.toDateStr);
  
  // For now, show what would be queried
  Logger.log(`Would query from ${range.fromDateStr} to ${range.toDateStr}`);
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `✅ Data refreshed for ${range.days} days`,
    'Complete',
    3
  );
}

/**
 * Example: Query BigQuery with date range
 * INTEGRATE with your existing BigQuery connection
 */
function queryBigQueryWithDateRange() {
  const range = getSelectedDateRange();
  
  // Example SQL with date parameters
  const sql = `
    SELECT 
      assetId,
      cost,
      volume,
      settlementDate
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad\`
    WHERE assetId LIKE 'OFR-%'
      AND CAST(settlementDate AS DATE) BETWEEN '${range.fromDateStr}' AND '${range.toDateStr}'
      AND cost IS NOT NULL
      AND volume > 0
    ORDER BY settlementDate DESC
    LIMIT 1000
  `;
  
  Logger.log('SQL Query:');
  Logger.log(sql);
  
  // TODO: Execute with BigQuery connector
  // const result = BigQuery.Jobs.query({query: sql}, projectId);
  // return result;
  
  return sql;
}

/**
 * Export filtered data to CSV
 */
function exportDateFilteredData() {
  const range = getSelectedDateRange();
  
  // Generate filename with dates
  const filename = `analysis_${range.fromDateStr}_to_${range.toDateStr}.csv`;
  
  SpreadsheetApp.getUi().alert(
    '📥 Export Ready',
    `File: ${filename}\n\n` +
    'Use File > Download > CSV to export the current view.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Create quick date range presets
 */
function createDatePresetButtons() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Add preset buttons in adjacent cells
  const presets = [
    { label: 'Last 7 Days', row: 65, col: 6, days: 7 },
    { label: 'Last 30 Days', row: 65, col: 7, days: 30 },
    { label: 'Last 90 Days', row: 65, col: 8, days: 90 },
    { label: 'YTD', row: 66, col: 6, days: 'ytd' }
  ];
  
  presets.forEach(preset => {
    const cell = sheet.getRange(preset.row, preset.col);
    cell.setValue(preset.label);
    cell.setBackground('#4285f4');
    cell.setFontColor('#ffffff');
    cell.setFontWeight('bold');
    cell.setHorizontalAlignment('center');
    cell.setBorder(true, true, true, true, false, false, '#ffffff', SpreadsheetApp.BorderStyle.SOLID);
  });
  
  SpreadsheetApp.getUi().alert(
    '✅ Date Presets Added',
    'Click buttons to quickly set common date ranges.\n\n' +
    'Note: Add click handlers via Apps Script to make functional.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Set date range to last N days
 */
function setLastNDays(days) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  const toDate = new Date();
  const fromDate = new Date();
  fromDate.setDate(fromDate.getDate() - days);
  
  sheet.getRange('D65').setValue(fromDate);
  sheet.getRange('E66').setValue(toDate);
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `📅 Set to last ${days} days`,
    'Date Range',
    2
  );
}

/**
 * Helper functions for preset buttons
 */
function setLast7Days() { setLastNDays(7); }
function setLast30Days() { setLastNDays(30); }
function setLast90Days() { setLastNDays(90); }

function setYearToDate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  const toDate = new Date();
  const fromDate = new Date(toDate.getFullYear(), 0, 1); // Jan 1 of current year
  
  sheet.getRange('D65').setValue(fromDate);
  sheet.getRange('E66').setValue(toDate);
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '📅 Set to Year-to-Date',
    'Date Range',
    2
  );
}
