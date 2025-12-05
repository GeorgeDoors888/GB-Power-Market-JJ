/**
 * @OnlyCurrentDoc
 * 
 * 📊 GB ENERGY DASHBOARD V3 - HYBRID IMPLEMENTATION
 * --------------------------------------------------
 * OPTION C: Python loads data, Apps Script formats
 * 
 * ARCHITECTURE:
 * 1. Python (populate_dashboard_tables.py) → Loads all backing sheets from BigQuery
 * 2. Apps Script (this file) → Formats Dashboard V3, adds interactivity
 * 3. User → Interacts with filters, DNO selector, manual refresh
 * 
 * BACKING SHEETS (populated by Python):
 * - Chart_Data_V2: Timeseries data (48 rows, columns A-J)
 * - VLP_Data: VLP revenue data (column D)
 * - Market_Prices: Market price data (column C)
 * - BESS: Battery storage metrics (cell B2)
 * - DNO_Map: DNO mapping (columns A, E, F, G)
 * - ESO_Actions: ESO balancing actions (columns A-F)
 * - Outages: Active outages (columns A-H)
 * 
 * Author: Upowerenergy / Overarch Jibber Jabber System
 * Last Updated: 2025-12-04
 */

// ---------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------
const SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc";
const DASHBOARD_SHEET_NAME = "Dashboard V3";
const DNO_MAP_SHEET_NAME = 'DNO_Map';
const GCP_PROJECT_ID = "inner-cinema-476211-u9";

// Cell locations
const TIME_RANGE_CELL = 'B3';
const REGION_CELL = 'F3';

// Color scheme (merged from both designs)
const COLORS = {
  HEADER_BG: '#FFA24D',        // Orange (Python style)
  HEADER_TEXT: '#FFFFFF',      // White
  KPI_HEADER_BG: '#3367D6',    // Blue (Python style)
  KPI_HEADER_TEXT: '#FFFFFF',  // White
  KPI_VALUE_BG: '#F0F9FF',     // Light blue (Apps Script style)
  KPI_VALUE_TEXT: '#1E293B',   // Dark slate
  SECTION_HEADER_BG: '#CBD5E1', // Medium gray
  TABLE_HEADER_BG: '#E2E8F0',  // Light gray
  TABLE_ROW_BG: '#FFFFFF',     // White
  SPARKLINE_COLOR: '#3B82F6'   // Blue
};

// ---------------------------------------------------
// TRIGGERS & MENU
// ---------------------------------------------------

/**
 * Creates custom menu and builds dashboard on spreadsheet open.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ GB Energy V3')
    .addItem('1. Rebuild Dashboard Design', 'buildDashboardV3')
    .addItem('2. Refresh Data (Python)', 'triggerPythonRefresh')
    .addItem('3. Show DNO Map Selector', 'showDnoMap')
    .addSeparator()
    .addItem('⚡ Full Rebuild (Data + Design)', 'fullRebuild')
    .addToUi();
}

/**
 * Runs when user edits time range or DNO filter.
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  const cell = range.getA1Notation();

  if (sheet.getName() === DASHBOARD_SHEET_NAME && 
      (cell === TIME_RANGE_CELL || cell === REGION_CELL)) {
    // Note: This would ideally trigger Python refresh, but we can't do that directly
    // User should run "Refresh Data (Python)" from menu after changing filters
    SpreadsheetApp.getActiveSpreadsheet().toast(
      '⚠️ Filter changed. Run "Refresh Data (Python)" from menu to update data.',
      'Filter Changed',
      5
    );
  }
}

// ---------------------------------------------------
// MAIN DASHBOARD BUILDER
// ---------------------------------------------------

/**
 * 📊 BUILD DASHBOARD V3 - Complete formatting and formulas
 * 
 * This function:
 * 1. Ensures Dashboard V3 sheet exists
 * 2. Clears existing formatting
 * 3. Sets up layout (columns, rows, frozen panes)
 * 4. Writes all headers, labels, and formulas
 * 5. Applies color scheme and formatting
 * 6. Creates sparklines
 * 7. Adds borders and conditional formatting
 * 
 * ASSUMES: Backing sheets already populated by Python
 */
function buildDashboardV3() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  
  if (!sheet) {
    sheet = ss.insertSheet(DASHBOARD_SHEET_NAME);
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Created Dashboard V3 sheet');
  }

  SpreadsheetApp.getActiveSpreadsheet().toast('🔧 Building Dashboard V3...', 'Progress', -1);

  // ═══════════════════════════════════════════════════
  // STEP 0: CLEAR PROBLEMATIC CELLS FIRST (before clearFormats)
  // ═══════════════════════════════════════════════════
  sheet.getRange("B3").clearContent().clearDataValidations();
  sheet.getRange("F3").clearContent().clearDataValidations();

  // ═══════════════════════════════════════════════════
  // STEP 1: RESET & GLOBAL SETTINGS
  // ═══════════════════════════════════════════════════
  sheet.clearFormats();
  sheet.setFrozenRows(3);
  sheet.setFrozenColumns(0);
  
  // Set column widths
  sheet.setColumnWidths(1, 5, 150);  // A-E: 150px
  sheet.setColumnWidths(6, 7, 130);  // F-L: 130px
  
  // Set font
  sheet.getRange("A1:M100").setFontFamily("Roboto");

  // ═══════════════════════════════════════════════════
  // STEP 2: HEADER SECTION (Rows 1-2)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A1:M1").merge()
    .setValue("⚡ GB ENERGY DASHBOARD V3 – REAL-TIME")
    .setFontSize(22)
    .setFontWeight("bold")
    .setHorizontalAlignment("center")
    .setBackground(COLORS.HEADER_BG)
    .setFontColor(COLORS.HEADER_TEXT);

  sheet.getRange("A2:M2").merge()
    .setFormula('=CONCAT("Last Updated: ",TEXT(NOW(),"yyyy-mm-dd HH:mm:ss"))')
    .setHorizontalAlignment("right")
    .setFontSize(10)
    .setFontStyle("italic")
    .setFontColor("#64748B");

  // ═══════════════════════════════════════════════════
  // STEP 3: FILTER DROPDOWNS (Row 3)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A3").setValue("Time Range:").setFontWeight("bold");
  
  // Add data validation for time range (B3 already cleared in STEP 0)
  const timeRangeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(['Today – Auto Refresh', 'Today – Manual', 'Last 7 Days', 'Last 30 Days', 'Year to Date'], true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("B3").setDataValidation(timeRangeRule);
  sheet.getRange("B3").setValue("Last 7 Days");

  sheet.getRange("E3").setValue("Region / DNO:").setFontWeight("bold");
  
  // Add data validation for DNO (F3 already cleared in STEP 0)
  // Check if DNO_Map has data before setting validation
  const dnoMapSheet = ss.getSheetByName('DNO_Map');
  if (dnoMapSheet && dnoMapSheet.getLastRow() > 1) {
    const dnoRule = SpreadsheetApp.newDataValidation()
      .requireValueInRange(ss.getRange('DNO_Map!A2:A20'), true)
      .setAllowInvalid(true)  // Allow "All GB" even if not in list
      .build();
    sheet.getRange("F3").setDataValidation(dnoRule);
  }
  sheet.getRange("F3").setValue("All GB");

  // ═══════════════════════════════════════════════════
  // STEP 4: KPI ZONE (Rows 9-11, Columns F-L)
  // ═══════════════════════════════════════════════════
  // KPI Headers
  const kpiHeaders = [
    "📊 VLP Revenue (£k)",
    "💰 Wholesale Avg (£/MWh)",
    "📈 Market Vol (%)",
    "💹 All-GB Net Margin (£/MWh)",
    "🎯 Selected DNO Net Margin (£/MWh)",
    "⚡ Selected DNO Volume (MWh)",
    "💷 Selected DNO Revenue (£k)"
  ];
  
  sheet.getRange("F9:L9").setValues([kpiHeaders])
    .setFontWeight("bold")
    .setFontSize(10)
    .setHorizontalAlignment("center")
    .setBackground(COLORS.KPI_HEADER_BG)
    .setFontColor(COLORS.KPI_HEADER_TEXT)
    .setWrap(true);

  // KPI Values (Row 10)
  const kpiFormulas = [
    // F10: VLP Revenue - Average from VLP_Data
    '=IFERROR(AVERAGE(VLP_Data!D:D)/1000, 0)',
    
    // G10: Wholesale Avg - Average from Market_Prices
    '=IFERROR(AVERAGE(Market_Prices!C:C), 0)',
    
    // H10: Market Volatility - StdDev/Mean
    '=IFERROR(STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C), 0)',
    
    // I10: All-GB Net Margin - From Chart_Data_V2 column J
    '=IFERROR(AVERAGE(FILTER(Chart_Data_V2!J:J, NOT(ISBLANK(Chart_Data_V2!J:J)))), 0)',
    
    // J10: Selected DNO Net Margin - XLOOKUP from DNO_Map
    '=IFERROR(IF($F$3="All GB", I10, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$E:$E, 0)), 0)',
    
    // K10: Selected DNO Volume
    '=IFERROR(IF($F$3="All GB", SUM(FILTER(Chart_Data_V2!D:D, NOT(ISBLANK(Chart_Data_V2!D:D))))/2, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$F:$F, 0)), 0)',
    
    // L10: Selected DNO Revenue
    '=IFERROR(IF($F$3="All GB", SUM(DNO_Map!$G:$G)/1000, XLOOKUP($F$3, DNO_Map!$A:$A, DNO_Map!$G:$G, 0)/1000), 0)'
  ];
  
  sheet.getRange("F10:L10").setFormulas([kpiFormulas])
    .setFontSize(16)
    .setFontWeight("bold")
    .setHorizontalAlignment("center")
    .setBackground(COLORS.KPI_VALUE_BG)
    .setFontColor(COLORS.KPI_VALUE_TEXT);

  // Number formatting for KPIs
  sheet.getRange("F10").setNumberFormat("£#,##0.0");     // VLP Revenue
  sheet.getRange("G10").setNumberFormat("£#,##0.00");    // Wholesale
  sheet.getRange("H10").setNumberFormat("0.00%");        // Volatility
  sheet.getRange("I10:J10").setNumberFormat("£#,##0.00"); // Net Margins
  sheet.getRange("K10").setNumberFormat("#,##0");        // Volume
  sheet.getRange("L10").setNumberFormat("£#,##0.0");     // Revenue

  // Sparklines (Row 11)
  const sparklineFormulas = [
    // F11: VLP Revenue trend (column chart)
    '=SPARKLINE(VLP_Data!D2:D8, {"charttype","column"; "color","' + COLORS.SPARKLINE_COLOR + '"})',
    
    // G11: Wholesale price trend (line)
    '=SPARKLINE(Market_Prices!C2:C8, {"charttype","line"; "color","' + COLORS.SPARKLINE_COLOR + '"; "linewidth",2})',
    
    // H11: Volatility trend (column)
    '=SPARKLINE(Market_Prices!C2:C8, {"charttype","column"; "color","' + COLORS.SPARKLINE_COLOR + '"})',
    
    // I11: All-GB net margin trend
    '=SPARKLINE(Chart_Data_V2!J2:J49, {"charttype","line"; "color","' + COLORS.SPARKLINE_COLOR + '"; "linewidth",2})',
    
    // J11-L11: No sparklines for DNO-specific (complex to implement)
    '', '', ''
  ];
  
  sheet.getRange("F11:L11").setFormulas([sparklineFormulas])
    .setHorizontalAlignment("center");
  sheet.setRowHeight(11, 40);

  // ═══════════════════════════════════════════════════
  // STEP 5: GENERATION MIX TABLE (Rows 8-18, Columns A-E)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A8:E8").merge()
    .setValue("⚡ GENERATION MIX & INTERCONNECTORS")
    .setFontWeight("bold")
    .setFontSize(12)
    .setHorizontalAlignment("center")
    .setBackground(COLORS.SECTION_HEADER_BG);

  sheet.getRange("A9:E9").setValues([["Fuel Type", "GW", "%", "Interconnector", "Flow (MW)"]])
    .setFontWeight("bold")
    .setBackground(COLORS.TABLE_HEADER_BG)
    .setHorizontalAlignment("center");

  sheet.getRange("A10:E25").setFontSize(10).setHorizontalAlignment("center");

  // ═══════════════════════════════════════════════════
  // STEP 6: OUTAGES TABLE (Rows 27-38)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A27:H27").merge()
    .setValue("🚨 ACTIVE OUTAGES (TOP 15 by MW Lost)")
    .setFontWeight("bold")
    .setFontSize(12)
    .setHorizontalAlignment("center")
    .setBackground(COLORS.SECTION_HEADER_BG);

  sheet.getRange("A28:H28").setValues([
    ["BM Unit", "Plant", "Fuel", "MW Lost", "% Lost", "Region", "Start Time", "Status"]
  ])
    .setBackground(COLORS.TABLE_HEADER_BG)
    .setFontWeight("bold")
    .setHorizontalAlignment("center");

  sheet.getRange("A29:H44").setFontSize(10).setHorizontalAlignment("center");

  // ═══════════════════════════════════════════════════
  // STEP 7: ESO INTERVENTIONS TABLE (Rows 46-56)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A46:F46").merge()
    .setValue("⚡ ESO BALANCING ACTIONS (Last 10)")
    .setFontWeight("bold")
    .setFontSize(12)
    .setHorizontalAlignment("center")
    .setBackground(COLORS.SECTION_HEADER_BG);

  sheet.getRange("A47:F47").setValues([
    ["BM Unit", "Mode", "MW", "£/MWh", "Duration (min)", "Action Type"]
  ])
    .setBackground(COLORS.TABLE_HEADER_BG)
    .setFontWeight("bold")
    .setHorizontalAlignment("center");

  // Query formula to pull top 10 from ESO_Actions
  sheet.getRange("A48").setFormula(
    '=QUERY(ESO_Actions!A:F, "SELECT * ORDER BY A DESC LIMIT 10", 1)'
  );

  // ═══════════════════════════════════════════════════
  // STEP 8: FOOTNOTES (Row 60)
  // ═══════════════════════════════════════════════════
  sheet.getRange("A60:M60").merge()
    .setValue(
      "📘 Data Sources: BigQuery (inner-cinema-476211-u9.uk_energy_prod) | " +
      "Tables: bmrs_mid_iris, bmrs_boalf_iris, bmrs_bod_iris, bmrs_fuelinst_iris | " +
      "KPIs: £/MWh prices, 7-day averages | Net Margin = Imbalance - Market Price | " +
      "Auto-refresh: Python every 15 min | Manual refresh: Menu → Refresh Data"
    )
    .setFontSize(9)
    .setFontColor("#475569")
    .setWrap(true);

  // ═══════════════════════════════════════════════════
  // STEP 9: BORDERS
  // ═══════════════════════════════════════════════════
  sheet.getRange("F9:L11").setBorder(
    true, true, true, true, true, true,
    "#CBD5E1", SpreadsheetApp.BorderStyle.SOLID
  );
  
  sheet.getRange("A8:E25").setBorder(
    true, true, true, true, true, true,
    "#E2E8F0", SpreadsheetApp.BorderStyle.SOLID
  );
  
  sheet.getRange("A27:H44").setBorder(
    true, true, true, true, true, true,
    "#E2E8F0", SpreadsheetApp.BorderStyle.SOLID
  );
  
  sheet.getRange("A46:F56").setBorder(
    true, true, true, true, true, true,
    "#E2E8F0", SpreadsheetApp.BorderStyle.SOLID
  );

  // ═══════════════════════════════════════════════════
  // STEP 10: CONDITIONAL FORMATTING
  // ═══════════════════════════════════════════════════
  // Fuel type highlighting (Generation Mix table)
  const rules = sheet.getConditionalFormatRules();
  
  // CCGT = Tan
  const ccgtRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains("CCGT")
    .setBackground("#FFE4B5")
    .setRanges([sheet.getRange("A10:E25")])
    .build();
  
  // WIND = Light blue
  const windRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains("WIND")
    .setBackground("#DBEAFE")
    .setRanges([sheet.getRange("A10:E25")])
    .build();
  
  // NUCLEAR = Light green
  const nuclearRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextContains("NUCLEAR")
    .setBackground("#D1FAE5")
    .setRanges([sheet.getRange("A10:E25")])
    .build();

  // IC Flow: Red=export, Green=import
  const exportRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(0)
    .setBackground("#FEE2E2")
    .setRanges([sheet.getRange("E10:E25")])
    .build();
  
  const importRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(0)
    .setBackground("#D1FAE5")
    .setRanges([sheet.getRange("E10:E25")])
    .build();

  sheet.setConditionalFormatRules([ccgtRule, windRule, nuclearRule, exportRule, importRule]);

  // ═══════════════════════════════════════════════════
  // COMPLETE
  // ═══════════════════════════════════════════════════
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ Dashboard V3 design complete! Now run "Refresh Data (Python)" to populate.',
    'Success',
    5
  );
}

// ---------------------------------------------------
// PYTHON INTEGRATION
// ---------------------------------------------------

/**
 * Trigger Python data refresh (placeholder).
 * In production, this would call a webhook or Cloud Function
 * that runs populate_dashboard_tables.py.
 */
function triggerPythonRefresh() {
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '⚠️ Python refresh must be run manually:\n\n' +
    'python3 python/populate_dashboard_tables.py\n\n' +
    'Or set up cron job for automatic refresh.',
    'Manual Action Required',
    10
  );
  
  // TODO: Add webhook call to trigger Python script
  // Example:
  // const url = 'https://your-cloud-function-url.com/refresh-dashboard';
  // const options = {
  //   method: 'post',
  //   payload: JSON.stringify({
  //     timeRange: SpreadsheetApp.getActiveSpreadsheet()
  //       .getSheetByName(DASHBOARD_SHEET_NAME).getRange('B3').getValue(),
  //     dno: SpreadsheetApp.getActiveSpreadsheet()
  //       .getSheetByName(DASHBOARD_SHEET_NAME).getRange('F3').getValue()
  //   })
  // };
  // UrlFetchApp.fetch(url, options);
}

/**
 * Full rebuild: Design + Data.
 * Note: Data refresh still requires Python to run externally.
 */
function fullRebuild() {
  buildDashboardV3();
  triggerPythonRefresh();
}

// ---------------------------------------------------
// DNO MAP SIDEBAR
// ---------------------------------------------------

/**
 * Shows DNO map selector sidebar.
 */
function showDnoMap() {
  const html = HtmlService
    .createTemplateFromFile('DnoMap')
    .evaluate()
    .setTitle('Select DNO Region')
    .setWidth(400);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Fetches DNO locations from DNO_Map sheet.
 * @returns {Array<Object>} DNO locations with code, name, lat, lng, netMargin.
 */
function getDnoLocations() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(DNO_MAP_SHEET_NAME);
  if (!sheet) {
    Logger.log('Error: DNO_Map sheet not found.');
    return [];
  }

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) return [];
  
  const header = values.shift();
  const idxCode = header.indexOf('DNO Code');
  const idxName = header.indexOf('DNO Name');
  const idxLat = header.indexOf('Latitude');
  const idxLng = header.indexOf('Longitude');
  const idxNetMargin = header.indexOf('Net Margin (£/MWh)');

  if (idxCode === -1 || idxName === -1 || idxLat === -1 || idxLng === -1) {
    Logger.log("DNO_Map sheet missing required columns.");
    return [];
  }

  return values
    .filter(function(r) { return r[idxCode]; })
    .map(function(r) {
      return {
        code: String(r[idxCode]),
        name: String(r[idxName]),
        lat: Number(r[idxLat]),
        lng: Number(r[idxLng]),
        netMargin: Number(r[idxNetMargin] || 0)
      };
    });
}

/**
 * Sets selected DNO in Dashboard V3 F3 cell.
 * @param {string} dnoCode The DNO code from map click.
 */
function selectDno(dnoCode) {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) {
    Logger.log('Error: Dashboard V3 not found.');
    return;
  }
  dash.getRange(REGION_CELL).setValue(dnoCode);
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ Selected DNO: ' + dnoCode + '\n\nRun "Refresh Data (Python)" to update KPIs.',
    'DNO Selected',
    5
  );
}
