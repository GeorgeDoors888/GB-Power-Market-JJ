// ============================================================================
// MINIMAL CONSTRAINT MAP - Python-Generated HTML Display
// ============================================================================

/**
 * @OnlyCurrentDoc
 */

/**
 * Add custom menu for map controls
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🗺️ Constraint Map')
    .addItem('📍 Show Interactive Map', 'showConstraintMap')
    .addItem('🔄 Refresh Map Data', 'refreshMapData')
    .addToUi();
}

/**
 * Show interactive constraint map in sidebar
 * Uses Python-generated HTML with embedded data
 */
function showConstraintMap() {
  const html = HtmlService.createHtmlOutputFromFile('ConstraintMap_Python')
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Refresh map data
 * Note: Data is embedded in HTML, regenerate HTML with Python script
 */
function refreshMapData() {
  SpreadsheetApp.getUi().alert(
    'To refresh map data:\n\n' +
    '1. Run: python3 generate_constraint_map_html.py\n' +
    '2. Upload new ConstraintMap_Python.html to Apps Script\n' +
    '3. Or set up auto-refresh with cron job\n\n' +
    'Current data is embedded in the HTML file.'
  );
}
