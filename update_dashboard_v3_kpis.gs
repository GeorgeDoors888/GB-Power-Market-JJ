/**
 * Update Dashboard V3 KPI Formulas to use bod_boalf_7d_summary View
 * 
 * Tasks 3-7 from PHASE1_COMPLETION_SUMMARY.md:
 * - Fix F10: VLP Revenue (All-GB)
 * - Fix I10: All-GB Net Margin 
 * - Fix J10: Selected DNO Net Margin
 * - Fix K10: Selected DNO Volume
 * - Fix L10: Selected DNO Revenue
 * 
 * Run from: Tools → Script editor in Google Sheets
 */

function updateDashboardV3KPIs() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Dashboard V3');
  
  if (!sheet) {
    Logger.log('❌ Dashboard V3 sheet not found');
    return;
  }
  
  Logger.log('🔧 Updating Dashboard V3 KPI formulas...');
  
  // BigQuery connector formula format (if using Data Connector)
  // Note: If using Apps Script, you'll need BigQuery Apps Script library
  
  // For now, we'll use QUERY formulas that reference a data import tab
  // Assumption: bod_boalf_7d_summary data is imported to a tab called 'BOD_SUMMARY'
  
  var formulas = {
    // Task 3: F10 - VLP Revenue £k (All-GB)
    'F10': '=IFERROR(QUERY(BOD_SUMMARY!A:N, "SELECT M WHERE A=\'GB_total\' LIMIT 1")/1000, "N/A")',
    
    // Task 4: I10 - All-GB Net Margin (£/MWh)
    'I10': '=IFERROR(QUERY(BOD_SUMMARY!A:N, "SELECT H WHERE A=\'GB_total\' LIMIT 1"), "N/A")',
    
    // Task 5: J10 - Selected DNO Net Margin (£/MWh)
    'J10': '=IFERROR(QUERY(BOD_SUMMARY!A:N, "SELECT H WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1"), "N/A")',
    
    // Task 6: K10 - Selected DNO Volume (MWh)
    'K10': '=IFERROR(QUERY(BOD_SUMMARY!A:N, "SELECT D WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1"), "N/A")',
    
    // Task 7: L10 - Selected DNO Revenue £k
    'L10': '=IFERROR(QUERY(BOD_SUMMARY!A:N, "SELECT M WHERE A=\'selected_dno\' AND B=\'"&BESS!B6&"\' LIMIT 1")/1000, "N/A")'
  };
  
  // Apply formulas
  for (var cell in formulas) {
    var range = sheet.getRange(cell);
    range.setFormula(formulas[cell]);
    Logger.log('✅ Updated ' + cell + ': ' + formulas[cell]);
  }
  
  Logger.log('\n📊 All KPI formulas updated!');
  Logger.log('⚠️  NOTE: Formulas assume bod_boalf_7d_summary data is imported to BOD_SUMMARY tab');
  Logger.log('   If using BigQuery Connected Sheets, formulas will need adjustment.');
}

/**
 * Alternative: Direct BigQuery Access
 * Requires: BigQuery Apps Script library enabled
 * Library ID: 1Lv6OnFG2s3T5zDmOiZg3LqCQHxrUf95B08cHWEFaQcFmQN0qqGUcR4Yy
 */
function updateDashboardV3KPIs_BigQuery() {
  var PROJECT_ID = 'inner-cinema-476211-u9';
  var DATASET = 'uk_energy_prod';
  var VIEW = 'bod_boalf_7d_summary';
  
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Dashboard V3');
  
  if (!sheet) {
    Logger.log('❌ Dashboard V3 sheet not found');
    return;
  }
  
  Logger.log('🔧 Querying BigQuery for KPI data...');
  
  try {
    // Query GB Total
    var queryGBTotal = 'SELECT * FROM `' + PROJECT_ID + '.' + DATASET + '.' + VIEW + '` WHERE breakdown = "GB_total"';
    var gbResult = BigQuery.Jobs.query({query: queryGBTotal}, PROJECT_ID);
    
    if (gbResult.rows && gbResult.rows.length > 0) {
      var gbRow = gbResult.rows[0].f;
      
      // Extract values (adjust indices based on actual column order)
      var gbRevenue = parseFloat(gbRow[2].v) / 1000; // total_revenue_gbp / 1000
      var gbMargin = parseFloat(gbRow[7].v); // net_margin_gbp_per_mwh
      
      // Update cells
      sheet.getRange('F10').setValue(gbRevenue);
      sheet.getRange('I10').setValue(gbMargin);
      
      Logger.log('✅ GB Total KPIs updated');
    }
    
    // Query Selected DNO
    var selectedDNO = ss.getSheetByName('BESS').getRange('B6').getValue();
    if (selectedDNO) {
      var queryDNO = 'SELECT * FROM `' + PROJECT_ID + '.' + DATASET + '.' + VIEW + 
                     '` WHERE breakdown = "selected_dno" AND dno = "' + selectedDNO + '"';
      var dnoResult = BigQuery.Jobs.query({query: queryDNO}, PROJECT_ID);
      
      if (dnoResult.rows && dnoResult.rows.length > 0) {
        var dnoRow = dnoResult.rows[0].f;
        
        var dnoMargin = parseFloat(dnoRow[7].v);
        var dnoVolume = parseFloat(dnoRow[3].v);
        var dnoRevenue = parseFloat(dnoRow[2].v) / 1000;
        
        sheet.getRange('J10').setValue(dnoMargin);
        sheet.getRange('K10').setValue(dnoVolume);
        sheet.getRange('L10').setValue(dnoRevenue);
        
        Logger.log('✅ Selected DNO KPIs updated for: ' + selectedDNO);
      }
    }
    
    Logger.log('\n📊 All KPIs updated from BigQuery!');
    
  } catch (e) {
    Logger.log('❌ Error querying BigQuery: ' + e.message);
    Logger.log('   Make sure BigQuery Apps Script library is enabled');
  }
}

/**
 * Create menu item
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔧 Dashboard Tools')
      .addItem('Update KPI Formulas', 'updateDashboardV3KPIs')
      .addItem('Refresh from BigQuery', 'updateDashboardV3KPIs_BigQuery')
      .addToUi();
}
