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
    .addItem('📍 Show Map (Leaflet - No API Key)', 'showConstraintMapLeaflet')
    .addItem('📍 Show Map (Google Maps)', 'showConstraintMapGoogle')
    .addItem('🔄 Refresh Map Data', 'refreshMapData')
    .addToUi();
}

/**
 * Show Leaflet map (recommended - no API key issues)
 */
function showConstraintMapLeaflet() {
  const html = HtmlService.createHtmlOutputFromFile('ConstraintMap_Leaflet')
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Show Google Maps version (requires API key)
 */
function showConstraintMapGoogle() {
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
