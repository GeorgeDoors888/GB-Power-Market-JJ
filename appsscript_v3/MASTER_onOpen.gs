/**
 * MASTER onOpen() - Consolidates ALL Menu Items
 * 
 * DEPLOYMENT INSTRUCTIONS:
 * 1. Open: Extensions → Apps Script
 * 2. Delete or rename any other onOpen() functions in all .gs files
 * 3. Copy THIS function to a file called "Menu.gs" or "MasterMenu.gs"
 * 4. Save and refresh spreadsheet
 * 5. ALL menus will appear!
 */

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  // Menu 1: Search Tools
  ui.createMenu('🔍 Search Tools')
      .addItem('🔍 Run Search', 'onSearchButtonClick')
      .addItem('🧹 Clear Search', 'onClearButtonClick')
      .addItem('ℹ️ Help', 'onHelpButtonClick')
      .addSeparator()
      .addItem('📋 View Party Details', 'viewSelectedPartyDetails')
      .addItem('📊 Generate Report', 'generateReportFromSearch')
      .addSeparator()
      .addItem('🔧 Test API Connection', 'testAPIConnection')
      .addToUi();
  
  // Menu 2: Setup Tools
  ui.createMenu('🔧 Setup')
      .addItem('Apply Data Validations', 'applyDataValidations')
      .addItem('Install GSP-DNO Linking', 'installGspDnoTrigger')
      .addToUi();
  
  // Menu 3: GB Live Dashboard
  ui.createMenu('GB Live Dashboard')
      .addItem('Add KPI Sparklines', 'addKPISparklinesManual')
      .addSeparator()
      .addItem('Enable Auto-Maintenance', 'installSparklineMaintenance')
      .addToUi();
  
  // Menu 4: Geographic Map (NEW)
  ui.createMenu('🗺️ Geographic Map')
      .addItem('Show DNO & GSP Boundaries', 'showMapSidebar')
      .addToUi();
  
  Logger.log('✅ All menus created: Search Tools, Setup, GB Live Dashboard, Geographic Map');
}
