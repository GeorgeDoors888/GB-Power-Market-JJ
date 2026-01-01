/**
 * Diagnostic function to test map sidebar deployment
 * Run this from Apps Script to see detailed error messages
 */
function testMapSidebarDeployment() {
  Logger.log('=== MAP SIDEBAR DIAGNOSTIC ===');
  
  // Test 1: Check HTML file exists
  Logger.log('\n[1] Testing HTML file...');
  try {
    var html = HtmlService.createHtmlOutputFromFile('map_sidebar_v2');
    Logger.log('[OK] HTML file "map_sidebar_v2" found');
    Logger.log('   Content length: ' + html.getContent().length + ' characters');
  } catch (e) {
    Logger.log('[FAIL] HTML file error: ' + e.message);
    return;
  }
  
  // Test 2: Check API key
  Logger.log('\n[2] Testing API key...');
}
