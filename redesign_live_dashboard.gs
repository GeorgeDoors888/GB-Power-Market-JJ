/**
 * REDESIGNED LIVE DASHBOARD - Clean, Professional Layout
 * 
 * Layout Structure:
 * ┌─────────────────────────────────────────────────────────┐
 * │ Header: GB Power Market - Live Dashboard        [Time] │
 * ├─────────────────────────────────────────────────────────┤
 * │ [KPI Card 1] [KPI Card 2] [KPI Card 3] [KPI Card 4]   │
 * │ [KPI Card 5] [KPI Card 6] [KPI Card 7] [KPI Card 8]   │
 * ├─────────────────────────────────────────────────────────┤
 * │ Generation Mix (Chart) │ Interconnectors (Table)       │
 * ├─────────────────────────────────────────────────────────┤
 * │ Battery Revenue (Top 10) │ SP Trends (Last 12 SPs)     │
 * └─────────────────────────────────────────────────────────┘
 * 
 * Separate tabs: Outages | BM Trends | Calculator | Schema
 */

function redesignLiveDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // Find source sheet
  const src = ss.getSheets().find(s => s.getName().toLowerCase().includes("live dashboardv2"));
  if (!src) throw new Error("Could not find 'live dashboardv2' sheet");
  
  // Backup original (once)
  const backupName = "live dashboardv2 (backup)";
  if (!ss.getSheetByName(backupName)) {
    src.copyTo(ss).setName(backupName);
  }
  
  // Create clean destination sheets
  const dash = createCleanSheet_(ss, "Dashboard");
  const outages = createCleanSheet_(ss, "Outages");
  const trends = createCleanSheet_(ss, "BM Trends");
  const calc = createCleanSheet_(ss, "BtM Calculator");
  const schema = createCleanSheet_(ss, "Schema");
  
  // Build dashboard sections
  buildHeader_(dash);
  buildKPICards_(dash, src);
  buildGenerationSection_(dash, src);
  buildBatterySection_(dash, src);
  buildSPTrendsSection_(dash, src);
  
  // Populate other tabs
  populateOutages_(outages, src);
  populateTrends_(trends, src);
  populateCalculator_(calc, src);
  populateSchema_(schema, src);
  
  // Apply styling
  applyDashboardStyle_(dash);
  applyTabStyle_(outages, "Outages");
  applyTabStyle_(trends, "BM Trends");
  applyTabStyle_(calc, "Calculator");
  applyTabStyle_(schema, "Reference");
  
  // Set as active
  ss.setActiveSheet(dash);
  ss.moveActiveSheet(1);
  
  SpreadsheetApp.flush();
  SpreadsheetApp.getUi().alert('✅ Dashboard redesigned successfully!');
}

/** ========== DASHBOARD SECTIONS ========== **/

function buildHeader_(sheet) {
  // Row 1: Main title
  sheet.getRange("A1:L1").merge()
    .setValue("⚡ GB Power Market - Live Dashboard")
    .setFontSize(18)
    .setFontWeight("bold")
    .setFontColor("#FFFFFF")
    .setBackground("#1a73e8")
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  
  // Row 2: Subtitle with last update
  sheet.getRange("A2:L2").merge()
    .setFormula('="Last updated: " & TEXT(NOW(), "DD/MM/YYYY HH:MM:SS")')
    .setFontSize(10)
    .setFontColor("#666666")
    .setHorizontalAlignment("center");
  
  sheet.setRowHeight(1, 50);
  sheet.setRowHeight(2, 25);
}

function buildKPICards_(sheet, src) {
  // 2 rows × 4 columns = 8 KPI cards
  const cards = [
    // Row 1
    {row: 4, col: 1, label: "BM Revenue Today", formula: '=SUMIF(A:A,TODAY(),D:D)', format: '"£"#,##0', color: "#34a853"},
    {row: 4, col: 4, label: "Net Volume (MWh)", formula: '=SUMIF(A:A,TODAY(),H:H)', format: '#,##0.0', color: "#4285f4"},
    {row: 4, col: 7, label: "EWAP (£/MWh)", formula: '=AVERAGE(FILTER(I:I,A:A=TODAY()))', format: '"£"#,##0.00', color: "#fbbc04"},
    {row: 4, col: 10, label: "Acceptances/hr", formula: '=COUNTIF(B:B,">="&NOW()-1/24)/1', format: '#,##0', color: "#ea4335"},
    
    // Row 2
    {row: 7, col: 1, label: "Wholesale Price", formula: '=INDEX(MID_Price,MATCH(MAX(MID_Time),MID_Time,0))', format: '"£"#,##0.00', color: "#9e9e9e"},
    {row: 7, col: 4, label: "Frequency (Hz)", formula: '=INDEX(Freq_Value,MATCH(MAX(Freq_Time),Freq_Time,0))', format: '0.000', color: "#9e9e9e"},
    {row: 7, col: 7, label: "Demand (GW)", formula: '=INDEX(Demand_Value,MATCH(MAX(Demand_Time),Demand_Time,0))/1000', format: '0.00', color: "#9e9e9e"},
    {row: 7, col: 10, label: "Wind Output (GW)", formula: '=INDEX(Wind_Value,MATCH(MAX(Wind_Time),Wind_Time,0))/1000', format: '0.00', color: "#9e9e9e"}
  ];
  
  cards.forEach(card => {
    // Merge 2×3 cell block for each card
    const range = sheet.getRange(card.row, card.col, 2, 3);
    range.merge();
    
    // Label in top-left corner (small)
    const labelCell = sheet.getRange(card.row, card.col);
    labelCell.setValue(card.label)
      .setFontSize(9)
      .setFontColor("#666666")
      .setVerticalAlignment("top")
      .setHorizontalAlignment("left");
    
    // Value in center (large)
    const valueCell = sheet.getRange(card.row, card.col + 1);
    valueCell.setFormula(card.formula)
      .setFontSize(24)
      .setFontWeight("bold")
      .setFontColor(card.color)
      .setVerticalAlignment("middle")
      .setHorizontalAlignment("center")
      .setNumberFormat(card.format);
    
    // Border and background
    range.setBorder(true, true, true, true, false, false, "#e0e0e0", SpreadsheetApp.BorderStyle.SOLID_MEDIUM)
      .setBackground("#f8f9fa");
  });
  
  sheet.setRowHeights(4, 2, 60);
  sheet.setRowHeights(7, 2, 60);
}

function buildGenerationSection_(sheet, src) {
  const startRow = 10;
  
  // Section header
  sheet.getRange(startRow, 1, 1, 6).merge()
    .setValue("🔌 Generation Mix")
    .setFontSize(12)
    .setFontWeight("bold")
    .setBackground("#e8f0fe");
  
  // Copy generation mix data from source
  copyRange_(src, "A10:F22", sheet, `A${startRow + 1}`);
  
  // Interconnectors on the right
  sheet.getRange(startRow, 8, 1, 5).merge()
    .setValue("🔗 Interconnectors")
    .setFontSize(12)
    .setFontWeight("bold")
    .setBackground("#e8f0fe");
  
  copyRange_(src, "H10:L22", sheet, `H${startRow + 1}`);
}

function buildBatterySection_(sheet, src) {
  const startRow = 25;
  
  // Section header
  sheet.getRange(startRow, 1, 1, 10).merge()
    .setValue("🔋 Battery BM Revenue - Top 10")
    .setFontSize(12)
    .setFontWeight("bold")
    .setBackground("#fce8e6");
  
  // Table headers
  const headers = ["Rank", "BMU ID", "Technology", "Capacity (MW)", "Revenue (£)", "Offer (£)", "Bid (£)", "MWh", "VWAP", "£/MW-day"];
  sheet.getRange(startRow + 1, 1, 1, 10)
    .setValues([headers])
    .setFontWeight("bold")
    .setBackground("#f4cccc")
    .setHorizontalAlignment("center");
  
  // Copy battery data (compact view - top 10 only)
  copyRange_(src, "A23:J32", sheet, `A${startRow + 2}`);
  
  // Conditional formatting for revenue column
  const revenueRange = sheet.getRange(startRow + 2, 5, 10, 1);
  const rule = SpreadsheetApp.newConditionalFormatRule()
    .setGradientMaxpoint("#34a853")
    .setGradientMidpoint("#fbbc04")
    .setGradientMinpoint("#ea4335")
    .setRanges([revenueRange])
    .build();
  sheet.setConditionalFormatRules([rule]);
}

function buildSPTrendsSection_(sheet, src) {
  const startRow = 25;
  const startCol = 12; // Column L
  
  // Section header
  sheet.getRange(startRow, startCol, 1, 4).merge()
    .setValue("📊 Settlement Period Trends (Last 12 SPs)")
    .setFontSize(12)
    .setFontWeight("bold")
    .setBackground("#e6f4ea");
  
  // Table headers
  const headers = ["SP", "Revenue (£)", "MWh", "EWAP"];
  sheet.getRange(startRow + 1, startCol, 1, 4)
    .setValues([headers])
    .setFontWeight("bold")
    .setBackground("#b7e1cd")
    .setHorizontalAlignment("center");
  
  // Formula to get last 12 SPs
  const dataFormula = '=QUERY(SORT(FILTER(A:D, A:A=TODAY()), 2, FALSE), "LIMIT 12")';
  sheet.getRange(startRow + 2, startCol).setFormula(dataFormula);
  
  // Sparkline for quick visualization
  sheet.getRange(startRow + 14, startCol, 1, 4).merge()
    .setFormula('=SPARKLINE(L' + (startRow + 2) + ':L' + (startRow + 13) + ', {"charttype","column";"color1","#4285f4"})')
    .setHorizontalAlignment("center");
}

/** ========== OTHER TABS ========== **/

function populateOutages_(sheet, src) {
  // Header
  sheet.getRange("A1:I1").merge()
    .setValue("⚠️ Current Outages")
    .setFontSize(14)
    .setFontWeight("bold")
    .setBackground("#fce8e6")
    .setHorizontalAlignment("center");
  
  // Copy outages data
  const outagesStart = findRowContaining_(src, "Asset Name") || 31;
  copyRange_(src, `H${outagesStart}:Q${outagesStart + 30}`, sheet, "A3");
  
  // Auto-filter
  sheet.getRange("A3:I3").createFilter();
}

function populateTrends_(sheet, src) {
  // Header
  sheet.getRange("A1:L1").merge()
    .setValue("📈 Balancing Mechanism Trends")
    .setFontSize(14)
    .setFontWeight("bold")
    .setBackground("#e8f0fe")
    .setHorizontalAlignment("center");
  
  // Copy trends data
  copyRange_(src, "R30:AB90", sheet, "A3");
}

function populateCalculator_(sheet, src) {
  // Header
  sheet.getRange("A1:H1").merge()
    .setValue("🧮 Behind-the-Meter Calculator")
    .setFontSize(14)
    .setFontWeight("bold")
    .setBackground("#fff4e6")
    .setHorizontalAlignment("center");
  
  // Copy calculator
  const calcStart = findRowContaining_(src, "Input / Parameter") || 86;
  const lastRow = src.getLastRow();
  copyRange_(src, `A${calcStart}:H${lastRow}`, sheet, "A3");
}

function populateSchema_(sheet, src) {
  // Header
  sheet.getRange("A1:L1").merge()
    .setValue("📋 Data Schema Reference")
    .setFontSize(14)
    .setFontWeight("bold")
    .setBackground("#f3e5f5")
    .setHorizontalAlignment("center");
  
  // Copy schema
  copyRange_(src, "A83:AB90", sheet, "A3");
}

/** ========== STYLING ========== **/

function applyDashboardStyle_(sheet) {
  // General settings
  sheet.setFrozenRows(3);
  sheet.setFrozenColumns(0);
  sheet.setHiddenGridlines(true);
  
  // Column widths
  sheet.setColumnWidths(1, 12, 95);
  sheet.setColumnWidth(1, 80);  // Rank/Index column
  sheet.setColumnWidth(2, 110); // BMU ID
  
  // Row heights
  sheet.setRowHeight(1, 50);
  sheet.setRowHeight(2, 25);
  sheet.setRowHeight(3, 15); // Spacer
  
  // Alternating row colors for tables
  const batteryData = sheet.getRange("A27:J36");
  batteryData.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY);
}

function applyTabStyle_(sheet, title) {
  sheet.setHiddenGridlines(true);
  sheet.setFrozenRows(2);
  sheet.setRowHeight(1, 40);
  sheet.setRowHeight(2, 10); // Spacer
  
  const cols = Math.min(15, sheet.getMaxColumns());
  sheet.setColumnWidths(1, cols, 110);
}

/** ========== HELPERS ========== **/

function createCleanSheet_(ss, name) {
  let sh = ss.getSheetByName(name);
  if (sh) sh.clear();
  else sh = ss.insertSheet(name);
  return sh;
}

function copyRange_(src, srcA1, dst, dstA1) {
  const srcRange = src.getRange(srcA1);
  const dstRange = dst.getRange(dstA1);
  srcRange.copyTo(dstRange, {contentsOnly: false});
}

function findRowContaining_(sheet, needle) {
  const values = sheet.getDataRange().getDisplayValues();
  for (let i = 0; i < values.length; i++) {
    for (let j = 0; j < values[i].length; j++) {
      if (values[i][j].toString().includes(needle)) return i + 1;
    }
  }
  return null;
}
