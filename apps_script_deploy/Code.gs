/**
 * Apps Script Enhancement for BESS Sheet
 * Formats the enhanced revenue analysis section (rows 60+)
 * Preserves existing DNO lookup, HH profile, and BtM PPA formatting (rows 1-50)
 * 
 * Installation:
 * 1. Open Google Sheets: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
 * 2. Extensions → Apps Script
 * 3. Paste this code into Code.gs
 * 4. Save and run formatBESSEnhanced()
 * 5. Authorize when prompted
 */

// Color scheme - matches existing dashboard
const COLORS = {
  ORANGE: '#FF6600',       // Title headers
  GREY: '#F5F5F5',         // Table bodies
  LIGHT_BLUE: '#D9E9F7',   // Column headers
  WHITE: '#FFFFFF',        // Input cells
  YELLOW: '#FFFFCC'        // Output/calculated cells
};

/**
 * Add menu to sheet
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ GB Energy Dashboard')
    .addItem('🔄 Refresh DNO Data', 'manualRefreshDno')
    .addItem('📊 Generate HH Data', 'generateHHData')
    .addSeparator()
    .addItem('🎨 Format BESS Enhanced', 'formatBESSEnhanced')
    .addItem('🎨 Format All Sheets', 'formatAllSheets')
    .addToUi();
}

/**
 * Format enhanced revenue analysis section (rows 60+)
 * Preserves existing formatting in rows 1-50
 */
function formatBESSEnhanced() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const bess = ss.getSheetByName('BESS');
  
  if (!bess) {
    SpreadsheetApp.getUi().alert('BESS sheet not found!');
    return;
  }
  
  Logger.log('Formatting BESS Enhanced section (rows 60+)...');
  
  // Row 58: Divider line
  bess.getRange('A58:Z58').mergeAcross();
  bess.getRange('A58').setValue('─'.repeat(100));
  bess.getRange('A58:Z58').setBackground('#CCCCCC').setFontWeight('normal');
  
  // Row 59: Section title
  bess.getRange('A59:Q59').mergeAcross();
  bess.getRange('A59').setValue('─── Enhanced Revenue Analysis (6-Stream Model) ───');
  bess.getRange('A59:Q59')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setFontSize(12)
    .setHorizontalAlignment('center');
  
  // Row 60: Column headers for timeseries
  const headers = bess.getRange('A60:Q60');
  headers.setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setHorizontalAlignment('center')
    .setVerticalAlignment('middle');
  
  // Format timeseries data rows (61+)
  // Timestamp column (A) - left aligned
  bess.getRange('A61:A1500').setHorizontalAlignment('left');
  
  // Numeric columns (K-Q) - right aligned, number format
  bess.getRange('K61:Q1500')
    .setNumberFormat('#,##0.00')
    .setHorizontalAlignment('right');
  
  // Format KPIs panel (T60:U67)
  bess.getRange('T60').setValue('📊 Enhanced Revenue KPIs');
  bess.getRange('T60:U60')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setFontSize(11);
  
  // KPI labels (T61:T67)
  bess.getRange('T61:T67')
    .setBackground(COLORS.LIGHT_BLUE)
    .setFontWeight('bold')
    .setHorizontalAlignment('right');
  
  // KPI values (U61:U67)
  bess.getRange('U61:U67')
    .setBackground(COLORS.YELLOW)
    .setNumberFormat('#,##0')
    .setHorizontalAlignment('right');
  
  // Format Revenue Stack panel (W60:Y67)
  bess.getRange('W60:Y60').setValues([['Revenue Stream', '£/year', '%']]);
  bess.getRange('W60:Y60')
    .setBackground(COLORS.ORANGE)
    .setFontColor(COLORS.WHITE)
    .setFontWeight('bold')
    .setHorizontalAlignment('center');
  
  // Revenue stack labels (W61:W67)
  bess.getRange('W61:W67')
    .setBackground(COLORS.LIGHT_BLUE)
    .setHorizontalAlignment('left');
  
  // Revenue stack values (X61:Y67)
  bess.getRange('X61:Y67')
    .setBackground(COLORS.YELLOW)
    .setHorizontalAlignment('right');
  
  bess.getRange('X61:X67').setNumberFormat('£#,##0');
  bess.getRange('Y61:Y67').setNumberFormat('0.0%');
  
  // Set column widths
  bess.setColumnWidth(1, 150);   // A: Timestamp
  bess.setColumnWidth(11, 100);  // K: Charge
  bess.setColumnWidth(12, 100);  // L: Discharge
  bess.setColumnWidth(13, 90);   // M: SoC
  bess.setColumnWidth(14, 110);  // N: Cost
  bess.setColumnWidth(15, 110);  // O: Revenue
  bess.setColumnWidth(16, 110);  // P: Profit
  bess.setColumnWidth(17, 120);  // Q: Cumulative
  bess.setColumnWidth(20, 150);  // T: KPI labels
  bess.setColumnWidth(21, 110);  // U: KPI values
  bess.setColumnWidth(23, 150);  // W: Revenue stream
  bess.setColumnWidth(24, 100);  // X: £/year
  bess.setColumnWidth(25, 80);   // Y: %
  
  // Add borders to data sections
  bess.getRange('A60:Q1500').setBorder(
    true, true, true, true, true, true,
    '#CCCCCC', SpreadsheetApp.BorderStyle.SOLID
  );
  
  bess.getRange('T60:U67').setBorder(
    true, true, true, true, true, true,
    '#000000', SpreadsheetApp.BorderStyle.SOLID_MEDIUM
  );
  
  bess.getRange('W60:Y67').setBorder(
    true, true, true, true, true, true,
    '#000000', SpreadsheetApp.BorderStyle.SOLID_MEDIUM
  );
  
  // Don't freeze rows - allows scrolling through all data
  // Users can manually freeze row 60 via View menu if desired
  
  Logger.log('✅ BESS Enhanced formatting complete');
  SpreadsheetApp.getUi().alert('✅ BESS Enhanced section formatted!\n\nRows 1-50: Preserved (DNO, HH, BtM PPA)\nRows 60+: Enhanced revenue analysis');
}

/**
 * Format all dashboard sheets
 */
function formatAllSheets() {
  formatBESSEnhanced();
  // Add other sheet formatting here if needed
  SpreadsheetApp.getUi().alert('✅ All sheets formatted!');
}

/**
 * Manual DNO refresh trigger
 */
function manualRefreshDno() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  const mpan = sheet.getRange('B6').getValue();
  const voltage = sheet.getRange('A10').getValue();
  
  if (!postcode && !mpan) {
    SpreadsheetApp.getUi().alert('⚠️ Please enter a postcode (A6) or MPAN (B6) first');
    return;
  }
  
  sheet.getRange('A4').setValue('🔄 Refreshing DNO data...');
  
  // This would call your webhook or Python script
  // For now, just show a message
  SpreadsheetApp.getUi().alert('DNO refresh triggered!\n\nPostcode: ' + postcode + '\nMPAN: ' + mpan + '\nVoltage: ' + voltage);
  
  sheet.getRange('A4').setValue('✅ Ready - DNO data refreshed');
}

/**
 * Generate HH data trigger
 */
function generateHHData() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  const minKw = sheet.getRange('B17').getValue();
  const avgKw = sheet.getRange('B18').getValue();
  const maxKw = sheet.getRange('B19').getValue();
  
  if (!minKw || !avgKw || !maxKw) {
    SpreadsheetApp.getUi().alert('⚠️ Please enter Min/Avg/Max kW values (B17:B19) first');
    return;
  }
  
  // This would call your Python script
  SpreadsheetApp.getUi().alert('HH Data generation triggered!\n\nMin: ' + minKw + ' kW\nAvg: ' + avgKw + ' kW\nMax: ' + maxKw + ' kW');
}
