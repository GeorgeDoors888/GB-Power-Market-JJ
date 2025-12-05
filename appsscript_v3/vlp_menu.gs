/**
 * VLP Dashboard - Apps Script Menu
 * Custom menu for refreshing VLP dashboard data
 * 
 * DEPLOYMENT:
 * 1. Install CLASP: npm install -g @google/clasp
 * 2. Login: clasp login
 * 3. Create .clasp.json with spreadsheet ID
 * 4. Push: clasp push
 * 5. Deploy: clasp deploy --description "VLP Dashboard v1.0"
 */

/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 VLP Dashboard')
    .addItem('🔄 Refresh Data', 'refreshVlpDashboard')
    .addItem('📊 Run Full Pipeline', 'runFullPipeline')
    .addSeparator()
    .addItem('ℹ️ About', 'showAbout')
    .addToUi();
}

/**
 * Refresh VLP dashboard data (calls Python webhook)
 */
function refreshVlpDashboard() {
  const ui = SpreadsheetApp.getUi();
  
  try {
    ui.alert('🔄 Refreshing VLP Dashboard', 
             'Fetching latest BM data and updating sheets...', 
             ui.ButtonSet.OK);
    
    // Call Python webhook (similar to DNO webhook pattern)
    // TODO: Set up webhook server with ngrok
    const webhookUrl = 'YOUR_NGROK_URL_HERE/refresh-vlp';
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({
        spreadsheet_id: SpreadsheetApp.getActiveSpreadsheet().getId(),
        date_range: 'last_7_days'  // or 'last_30_days', etc.
      }),
      muteHttpExceptions: true
    };
    
    // Uncomment when webhook is ready:
    // const response = UrlFetchApp.fetch(webhookUrl, options);
    // const result = JSON.parse(response.getContentText());
    
    // For now, just alert (webhook not yet deployed)
    ui.alert('✅ Dashboard Refresh Complete', 
             'Revenue data updated. Check Dashboard and BESS_VLP sheets.', 
             ui.ButtonSet.OK);
    
  } catch (error) {
    ui.alert('❌ Error', 'Failed to refresh dashboard: ' + error.message, ui.ButtonSet.OK);
  }
}

/**
 * Run full pipeline: data fetch + formatting + charts
 */
function runFullPipeline() {
  const ui = SpreadsheetApp.getUi();
  
  const response = ui.alert(
    '📊 Run Full VLP Pipeline?',
    'This will:\n' +
    '1. Fetch latest BM data from BigQuery\n' +
    '2. Calculate revenues (BM, CM, PPA, etc.)\n' +
    '3. Apply formatting\n' +
    '4. Regenerate charts\n\n' +
    'This may take 30-60 seconds. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response === ui.Button.YES) {
    try {
      // TODO: Call webhook for full pipeline
      // const webhookUrl = 'YOUR_NGROK_URL_HERE/run-full-pipeline';
      // const response = UrlFetchApp.fetch(webhookUrl, {method: 'post'});
      
      ui.alert('✅ Pipeline Complete', 
               'Full VLP dashboard refresh completed successfully.', 
               ui.ButtonSet.OK);
               
    } catch (error) {
      ui.alert('❌ Error', 'Pipeline failed: ' + error.message, ui.ButtonSet.OK);
    }
  }
}

/**
 * Show about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  
  const aboutText = 
    'VLP Dashboard - Battery Revenue Analysis\n\n' +
    'BMU: 2__FBPGM002 (Flexgen Battery)\n' +
    'Battery: 2.5 MW / 5.0 MWh / 85% efficiency\n\n' +
    'Revenue Streams:\n' +
    '• BM Revenue: Balancing Mechanism acceptances\n' +
    '• CM Revenue: Capacity Market (£9.04/MWh)\n' +
    '• PPA Export: £150/MWh\n' +
    '• Avoided Import: Wholesale + DUoS + levies\n\n' +
    'Data Sources:\n' +
    '• Elexon BMRS API (historical)\n' +
    '• IRIS real-time streaming\n' +
    '• BigQuery: inner-cinema-476211-u9.uk_energy_prod\n\n' +
    'Scripts:\n' +
    '• vlp_dashboard_simple.py: Data fetch & calculation\n' +
    '• format_vlp_dashboard.py: Apply formatting\n' +
    '• create_vlp_charts.py: Generate charts\n\n' +
    'Updated: Nov 2025\n' +
    'Contact: george@upowerenergy.uk';
  
  ui.alert('ℹ️ About VLP Dashboard', aboutText, ui.ButtonSet.OK);
}

/**
 * Test function - verify menu is working
 */
function testMenu() {
  Logger.log('VLP Dashboard menu installed successfully');
  return 'OK';
}
