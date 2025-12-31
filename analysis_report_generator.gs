/**
 * Analysis Report Generator - Apps Script Functions
 * 
 * Installation:
 * 1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
 * 2. Go to: Extensions > Apps Script
 * 3. Click "+" to add a new file
 * 4. Name it "AnalysisReportGenerator"
 * 5. Paste this code
 * 6. Save (Ctrl+S)
 * 7. Refresh your spreadsheet
 * 8. New menu "📊 Analysis Tools" will appear
 */

/**
 * Create custom menu when spreadsheet opens
 * NOTE: Merge this with existing onOpen() function if you already have one
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  // Create Analysis Tools menu
  ui.createMenu('📊 Analysis Tools')
      .addItem('🔄 Generate Report', 'generateAnalysisReport')
      .addItem('📋 View Report Results', 'viewReportResults')
      .addItem('🧹 Clear Report Data', 'clearReportData')
      .addSeparator()
      .addItem('ℹ️ Help', 'showAnalysisHelp')
      .addToUi();
  
  // Keep existing BtM menu if it exists
  ui.createMenu('⚡ BtM Tools')
      .addItem('🔄 Generate HH Data', 'produceHHData')
      .addItem('📊 View HH DATA Sheet', 'viewHHDataSheet')
      .addToUi();
}

/**
 * Main function to generate analysis report
 * Calls Python webhook server to run generate_analysis_report.py
 */
function generateAnalysisReport() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const analysisSheet = ss.getSheetByName('Analysis');
  
  if (!analysisSheet) {
    ui.alert('❌ Error', 'Analysis sheet not found!', ui.ButtonSet.OK);
    return;
  }
  
  // Read current configuration
  const fromDate = analysisSheet.getRange('B4').getValue();
  const toDate = analysisSheet.getRange('D4').getValue();
  const category = analysisSheet.getRange('B11').getValue();
  const reportType = analysisSheet.getRange('B12').getValue();
  const graphType = analysisSheet.getRange('B13').getValue();
  
  // Confirm action
  const response = ui.alert(
    '🔄 Generate Analysis Report',
    `This will generate a new report with:\n\n` +
    `📅 Date Range: ${fromDate} → ${toDate}\n` +
    `📂 Category: ${category}\n` +
    `📋 Type: ${reportType}\n` +
    `📈 Graph: ${graphType}\n\n` +
    `Old data will be cleared.\n\n` +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    // Show progress
    ui.alert('⏳ Generating report...\n\nThis will take 5-15 seconds.\nPlease wait.');
    
    // OPTION 1: Call webhook server (if running)
    const WEBHOOK_URL = 'https://YOUR_WEBHOOK_URL_HERE/generate_report';
    
    try {
      const webhookResponse = UrlFetchApp.fetch(WEBHOOK_URL, {
        method: 'post',
        contentType: 'application/json',
        payload: JSON.stringify({
          action: 'generate_report',
          spreadsheet_id: ss.getId()
        }),
        muteHttpExceptions: true
      });
      
      if (webhookResponse.getResponseCode() === 200) {
        const result = JSON.parse(webhookResponse.getContentText());
        ui.alert(
          '✅ Success!',
          `Report generated successfully!\n\n` +
          `Rows: ${result.row_count}\n` +
          `Category: ${category}\n\n` +
          'Scroll down to row 18+ to view results.',
          ui.ButtonSet.OK
        );
        return;
      }
    } catch (webhookError) {
      // Webhook not available, show manual instructions
      Logger.log('Webhook not available: ' + webhookError);
    }
    
    // OPTION 2: Manual instructions (fallback)
    ui.alert(
      '🔄 Generate Report',
      `📊 Report Configuration:\n\n` +
      `📅 Date Range: ${fromDate} → ${toDate}\n` +
      `📂 Category: ${category}\n` +
      `📋 Type: ${reportType}\n` +
      `📈 Graph: ${graphType}\n\n` +
      '━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
      '🖥️ Run this command in terminal:\n\n' +
      'python3 generate_analysis_report.py\n\n' +
      '━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
      '⏰ Estimated Time: 5-10 seconds\n' +
      '📊 Results will appear in row 18+\n\n' +
      '💡 TIP: For one-click automation, set up\n' +
      'the webhook server (see documentation)',
      ui.ButtonSet.OK
    );
    
  } catch (error) {
    ui.alert('❌ Error', 'Failed to generate report:\n\n' + error.toString(), ui.ButtonSet.OK);
  }
}

/**
 * Navigate to report results
 */
function viewReportResults() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const analysisSheet = ss.getSheetByName('Analysis');
  
  if (analysisSheet) {
    ss.setActiveSheet(analysisSheet);
    analysisSheet.getRange('A18').activate();
    SpreadsheetApp.getUi().alert(
      '📊 Report Results',
      'Scrolled to row 18 where report data begins.\n\n' +
      'If you don\'t see data, generate a report first:\n' +
      'Menu: 📊 Analysis Tools > 🔄 Generate Report',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } else {
    SpreadsheetApp.getUi().alert('❌ Error', 'Analysis sheet not found!', SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Clear old report data
 */
function clearReportData() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const analysisSheet = ss.getSheetByName('Analysis');
  
  if (!analysisSheet) {
    ui.alert('❌ Error', 'Analysis sheet not found!', ui.ButtonSet.OK);
    return;
  }
  
  const response = ui.alert(
    '🧹 Clear Report Data',
    'This will clear all report data from row 17+\n\n' +
    'Your configuration (rows 4-13) will be preserved.\n\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    analysisSheet.getRange('A17:Z10000').clearContent();
    ui.alert('✅ Success', 'Report data cleared!', ui.ButtonSet.OK);
  } catch (error) {
    ui.alert('❌ Error', 'Failed to clear data:\n\n' + error.toString(), ui.ButtonSet.OK);
  }
}

/**
 * Show help information
 */
function showAnalysisHelp() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    'ℹ️ Analysis Report Generator - Help',
    '📊 HOW TO USE:\n\n' +
    '1. Configure your query (Rows 4-13):\n' +
    '   • Set date range (B4, D4)\n' +
    '   • Select filters (B6-B10)\n' +
    '   • Choose report options (B11-B13)\n\n' +
    '2. Generate Report:\n' +
    '   • Menu: 📊 Analysis Tools > 🔄 Generate Report\n' +
    '   • OR run: python3 generate_analysis_report.py\n\n' +
    '3. View Results:\n' +
    '   • Scroll down to row 18+\n' +
    '   • OR Menu: 📊 Analysis Tools > 📋 View Report Results\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '📂 REPORT CATEGORIES:\n' +
    '• VLP Revenue Analysis\n' +
    '• Balancing Mechanism (BOD)\n' +
    '• Interconnector Flows\n' +
    '• Generator Performance\n' +
    '• Frequency Response\n' +
    '• Curtailment Analysis\n' +
    '• Market Pricing (MID)\n' +
    '• Settlement (DISBSAD)\n' +
    '• Fuel Mix\n' +
    '• Wind Forecasting\n\n' +
    '━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n' +
    '💡 TIPS:\n' +
    '• Use comma-separated values for multi-select\n' +
    '• Set "All" to remove filters\n' +
    '• Check ANALYSIS_SHEET_LAYOUT_GUIDE.md\n\n' +
    '🔧 For webhook automation setup:\n' +
    'See ANALYSIS_REPORT_SYSTEM_GUIDE.md',
    ui.ButtonSet.OK
  );
}

/**
 * BtM HH Data Generator (keep existing function)
 */
function produceHHData() {
  // Keep existing BtM function - see btm_hh_generator.gs
  SpreadsheetApp.getUi().alert(
    'ℹ️ Info',
    'This function is in btm_hh_generator.gs\n\n' +
    'Please see that file for the implementation.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

function viewHHDataSheet() {
  // Keep existing BtM function - see btm_hh_generator.gs
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hhSheet = ss.getSheetByName('HH DATA');
  
  if (hhSheet) {
    ss.setActiveSheet(hhSheet);
    hhSheet.getRange('A1').activate();
  } else {
    SpreadsheetApp.getUi().alert('HH DATA sheet not found. Generate data first.');
  }
}
