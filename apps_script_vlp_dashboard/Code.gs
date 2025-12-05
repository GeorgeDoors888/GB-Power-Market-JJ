/**
 * VLP Document Dashboard - Apps Script + SPARKLINE Hybrid
 * 
 * This script creates a custom menu and automates:
 * 1. Loading VLP document data from BigQuery (via Python backend)
 * 2. Inserting SPARKLINE formulas for visualizations
 * 3. Applying conditional formatting for document health
 * 4. Creating data validation dropdowns
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📄 VLP Documents')
    .addItem('🔄 Refresh Document Data', 'refreshVLPDocuments')
    .addItem('🎨 Format Dashboard', 'formatVLPDashboard')
    .addItem('📊 Insert Sparklines', 'insertSparklines')
    .addItem('✅ Apply Conditional Formatting', 'applyConditionalFormatting')
    .addSeparator()
    .addItem('📈 Generate Summary Report', 'generateSummaryReport')
    .addToUi();
}

/**
 * Refresh VLP Documents from BigQuery
 * Note: Actual data fetch should be done via Python (google-cloud-bigquery)
 * This function formats the sheet to receive data
 */
function refreshVLPDocuments() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("VLP Documents");
  
  if (!sheet) {
    sheet = ss.insertSheet("VLP Documents");
  }
  
  // Setup headers
  const headers = [
    "Document ID", "Title", "Source", "Document Type", 
    "Scraped Date", "Chunk Count", "URL", "Trend", "Status"
  ];
  
  sheet.getRange(1, 1, 1, headers.length)
    .setValues([headers])
    .setBackground("#4A90E2")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setFontSize(11)
    .setHorizontalAlignment("center");
  
  // Set column widths
  sheet.setColumnWidth(1, 150); // Document ID
  sheet.setColumnWidth(2, 300); // Title
  sheet.setColumnWidth(3, 100); // Source
  sheet.setColumnWidth(4, 120); // Document Type
  sheet.setColumnWidth(5, 110); // Scraped Date
  sheet.setColumnWidth(6, 100); // Chunk Count
  sheet.setColumnWidth(7, 80);  // URL (link icon)
  sheet.setColumnWidth(8, 150); // Trend (sparkline)
  sheet.setColumnWidth(9, 100); // Status
  
  // Add timestamp
  sheet.getRange("K1")
    .setValue("⚡ Last Updated: " + new Date().toLocaleString())
    .setFontSize(9)
    .setFontColor("#666666");
  
  SpreadsheetApp.getUi().alert(
    '✅ Sheet prepared for data refresh\n\n' +
    'Now run Python script to load data:\n' +
    'python load_vlp_to_sheets.py'
  );
}

/**
 * Format VLP Dashboard with professional styling
 */
function formatVLPDashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("VLP Documents");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('❌ VLP Documents sheet not found. Run Refresh first.');
    return;
  }
  
  const lastRow = sheet.getLastRow();
  const lastCol = sheet.getLastColumn();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('❌ No data to format. Load data first.');
    return;
  }
  
  // Freeze header row
  sheet.setFrozenRows(1);
  
  // Zebra striping for data rows
  for (let row = 2; row <= lastRow; row++) {
    const color = (row % 2 === 0) ? "#F9F9F9" : "#FFFFFF";
    sheet.getRange(row, 1, 1, lastCol).setBackground(color);
  }
  
  // Center align specific columns
  sheet.getRange(2, 3, lastRow - 1, 1).setHorizontalAlignment("center"); // Source
  sheet.getRange(2, 5, lastRow - 1, 1).setHorizontalAlignment("center"); // Date
  sheet.getRange(2, 6, lastRow - 1, 1).setHorizontalAlignment("center"); // Chunk Count
  sheet.getRange(2, 9, lastRow - 1, 1).setHorizontalAlignment("center"); // Status
  
  // Add borders
  sheet.getRange(1, 1, lastRow, lastCol)
    .setBorder(true, true, true, true, true, true, "#CCCCCC", SpreadsheetApp.BorderStyle.SOLID);
  
  // Bold chunk count numbers
  sheet.getRange(2, 6, lastRow - 1, 1).setFontWeight("bold");
  
  SpreadsheetApp.getUi().alert('✅ Dashboard formatted successfully!');
}

/**
 * Insert SPARKLINE formulas for document trends
 * Assumes chunk_count column has historical data or can show trend
 */
function insertSparklines() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("VLP Documents");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('❌ VLP Documents sheet not found.');
    return;
  }
  
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('❌ No data to add sparklines.');
    return;
  }
  
  // Column H (8) = Trend sparklines
  // Create mini bar charts based on chunk_count (column F/6)
  for (let row = 2; row <= lastRow; row++) {
    const chunkCount = sheet.getRange(row, 6).getValue();
    
    // SPARKLINE showing chunk count as a simple bar
    // For more complex trends, you'd need historical data
    const sparklineFormula = `=SPARKLINE(F${row}, {"charttype","bar";"max",1000;"color1","#4A90E2"})`;
    sheet.getRange(row, 8).setFormula(sparklineFormula);
  }
  
  SpreadsheetApp.getUi().alert('✅ Sparklines inserted for all documents!');
}

/**
 * Apply conditional formatting rules
 */
function applyConditionalFormatting() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("VLP Documents");
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('❌ VLP Documents sheet not found.');
    return;
  }
  
  const lastRow = sheet.getLastRow();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('❌ No data for conditional formatting.');
    return;
  }
  
  // Clear existing conditional formatting
  sheet.clearConditionalFormatRules();
  
  const rules = [];
  
  // Rule 1: Highlight high chunk count (>200) in green
  const highChunkRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(200)
    .setBackground("#D4EDDA")
    .setFontColor("#155724")
    .setRanges([sheet.getRange(2, 6, lastRow - 1, 1)]) // Chunk Count column
    .build();
  rules.push(highChunkRule);
  
  // Rule 2: Highlight low chunk count (<20) in yellow
  const lowChunkRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(20)
    .setBackground("#FFF3CD")
    .setFontColor("#856404")
    .setRanges([sheet.getRange(2, 6, lastRow - 1, 1)])
    .build();
  rules.push(lowChunkRule);
  
  // Rule 3: Status column - color code by status
  // Green for "Complete", Yellow for "Partial", Red for "Missing"
  const completeRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("Complete")
    .setBackground("#28A745")
    .setFontColor("#FFFFFF")
    .setRanges([sheet.getRange(2, 9, lastRow - 1, 1)]) // Status column
    .build();
  rules.push(completeRule);
  
  const partialRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("Partial")
    .setBackground("#FFC107")
    .setFontColor("#000000")
    .setRanges([sheet.getRange(2, 9, lastRow - 1, 1)])
    .build();
  rules.push(partialRule);
  
  const missingRule = SpreadsheetApp.newConditionalFormatRule()
    .whenTextEqualTo("Missing")
    .setBackground("#DC3545")
    .setFontColor("#FFFFFF")
    .setRanges([sheet.getRange(2, 9, lastRow - 1, 1)])
    .build();
  rules.push(missingRule);
  
  // Apply all rules
  sheet.setConditionalFormatRules(rules);
  
  SpreadsheetApp.getUi().alert(
    '✅ Conditional formatting applied!\n\n' +
    '🟢 High chunks (>200): Green\n' +
    '🟡 Low chunks (<20): Yellow\n' +
    '🟢 Complete: Green\n' +
    '🟡 Partial: Yellow\n' +
    '🔴 Missing: Red'
  );
}

/**
 * Generate Summary Report on separate sheet
 */
function generateSummaryReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataSheet = ss.getSheetByName("VLP Documents");
  
  if (!dataSheet) {
    SpreadsheetApp.getUi().alert('❌ VLP Documents sheet not found.');
    return;
  }
  
  const lastRow = dataSheet.getLastRow();
  
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert('❌ No data to summarize.');
    return;
  }
  
  // Get or create summary sheet
  let summarySheet = ss.getSheetByName("VLP Summary");
  if (!summarySheet) {
    summarySheet = ss.insertSheet("VLP Summary");
  } else {
    summarySheet.clear();
  }
  
  // Get data range
  const data = dataSheet.getRange(2, 1, lastRow - 1, 9).getValues();
  
  // Calculate statistics
  let totalDocs = data.length;
  let totalChunks = 0;
  let sourceCounts = {};
  let typeCounts = {};
  let chunkCounts = [];
  
  data.forEach(row => {
    const chunks = row[5]; // Chunk Count
    const source = row[2]; // Source
    const type = row[3]; // Document Type
    
    totalChunks += chunks;
    chunkCounts.push(chunks);
    
    sourceCounts[source] = (sourceCounts[source] || 0) + 1;
    typeCounts[type] = (typeCounts[type] || 0) + 1;
  });
  
  const avgChunks = Math.round(totalChunks / totalDocs);
  const maxChunks = Math.max(...chunkCounts);
  const minChunks = Math.min(...chunkCounts);
  
  // Write summary
  summarySheet.getRange("A1").setValue("VLP Document Summary Report")
    .setFontSize(16)
    .setFontWeight("bold")
    .setBackground("#4A90E2")
    .setFontColor("#FFFFFF");
  
  summarySheet.getRange("A2").setValue("Generated: " + new Date().toLocaleString())
    .setFontSize(9)
    .setFontColor("#666666");
  
  // Key metrics
  const metrics = [
    ["📊 Key Metrics", ""],
    ["Total Documents", totalDocs],
    ["Total Chunks", totalChunks],
    ["Average Chunks/Doc", avgChunks],
    ["Max Chunks", maxChunks],
    ["Min Chunks", minChunks],
    ["", ""],
    ["📁 By Source", "Count"]
  ];
  
  Object.entries(sourceCounts).forEach(([source, count]) => {
    metrics.push([source, count]);
  });
  
  metrics.push(["", ""]);
  metrics.push(["📄 By Document Type", "Count"]);
  
  Object.entries(typeCounts).forEach(([type, count]) => {
    metrics.push([type, count]);
  });
  
  summarySheet.getRange(4, 1, metrics.length, 2).setValues(metrics);
  
  // Format metrics section
  summarySheet.getRange("A4:B4").setBackground("#E8F4F8").setFontWeight("bold");
  summarySheet.getRange("A11:B11").setBackground("#E8F4F8").setFontWeight("bold");
  
  // Add sparkline showing distribution
  const metricsStartRow = 4 + metrics.length + 2;
  summarySheet.getRange(metricsStartRow, 1).setValue("Chunk Distribution:");
  summarySheet.getRange(metricsStartRow, 2).setFormula(
    `=SPARKLINE('VLP Documents'!F2:F${lastRow}, {"charttype","column";"color","#4A90E2"})`
  );
  
  // Auto-resize columns
  summarySheet.autoResizeColumns(1, 2);
  
  SpreadsheetApp.getUi().alert('✅ Summary report generated on "VLP Summary" sheet!');
}

/**
 * Helper: Add data validation dropdown for Status column
 * Call this after data is loaded
 */
function addStatusDropdowns() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName("VLP Documents");
  
  if (!sheet) return;
  
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return;
  
  // Create data validation rule for Status column
  const statusValues = ["Complete", "Partial", "Missing"];
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(statusValues, true)
    .setAllowInvalid(false)
    .build();
  
  sheet.getRange(2, 9, lastRow - 1, 1).setDataValidation(rule);
}
