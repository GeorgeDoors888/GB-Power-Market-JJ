/**
 * btm_map_button.gs
 *
 * Apps Script code to add "View Constraint Map" button to BtM sheet.
 * Opens interactive Folium map in sidebar or new tab.
 *
 * Installation:
 * 1. Open Google Sheets → Extensions → Apps Script
 * 2. Paste this code
 * 3. Save and run 'createMapButton' once to authorize
 * 4. Button will appear in BtM sheet
 *
 * Map hosting options:
 * - GitHub Pages (recommended): https://georgedoors888.github.io/GB-Power-Market-JJ/btm_constraint_map.html
 * - Google Drive: Share HTML file and use direct link
 * - Local server: Use ngrok tunnel for testing
 */

// ===== CONFIGURATION =====
const MAP_URL = 'https://georgedoors888.github.io/GB-Power-Market-JJ/btm_constraint_map.html';
// Alternative: Use Google Drive file ID
// const MAP_URL = 'https://drive.google.com/file/d/YOUR_FILE_ID/view';

const BTM_SHEET_NAME = 'BtM';
const BUTTON_TEXT = '🗺️ View Constraint Map';
const BUTTON_CELL = 'D2';  // Where to place button


/**
 * Create custom menu when spreadsheet opens
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Maps')
      .addItem('View Constraint Map', 'openConstraintMap')
      .addItem('Refresh BtM Sites Data', 'refreshBtmSites')
      .addSeparator()
      .addItem('About Map', 'showMapInfo')
      .addToUi();
}


/**
 * Open constraint map in new tab
 */
function openConstraintMap() {
  var html = HtmlService.createHtmlOutput(
    '<script>window.open("' + MAP_URL + '", "_blank"); google.script.host.close();</script>'
  ).setWidth(100).setHeight(50);

  SpreadsheetApp.getUi().showModalDialog(html, 'Opening Map...');
}


/**
 * Open constraint map in sidebar (alternative approach)
 */
function openConstraintMapSidebar() {
  var html = HtmlService.createHtmlOutputFromFile('MapSidebar')
      .setTitle('DNO Constraint Map')
      .setWidth(400);

  SpreadsheetApp.getUi().showSidebar(html);
}


/**
 * Create clickable button/image in BtM sheet
 */
function createMapButton() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(BTM_SHEET_NAME);

  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: BtM sheet not found');
    return;
  }

  // Method 1: Use drawing (manual setup required)
  // User must manually:
  // 1. Insert → Drawing
  // 2. Add text/shape with "View Map" label
  // 3. Save, then right-click → Assign script → openConstraintMap

  // Method 2: Use button in cell with hyperlink formula
  var cell = sheet.getRange(BUTTON_CELL);
  cell.setFormula('=HYPERLINK("' + MAP_URL + '", "' + BUTTON_TEXT + '")');
  cell.setFontSize(12);
  cell.setFontWeight('bold');
  cell.setHorizontalAlignment('center');
  cell.setBackground('#4285f4');
  cell.setFontColor('#ffffff');
  cell.setBorder(true, true, true, true, false, false, 'black', SpreadsheetApp.BorderStyle.SOLID);

  SpreadsheetApp.getUi().alert(
    'Map button created!',
    'Click cell ' + BUTTON_CELL + ' in BtM sheet to open constraint map.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}


/**
 * Trigger Python script to refresh BtM sites and regenerate map
 * (Requires webhook server or Apps Script HTTP endpoint)
 */
function refreshBtmSites() {
  var ui = SpreadsheetApp.getUi();

  var response = ui.alert(
    'Refresh BtM Sites?',
    'This will:\n' +
    '1. Re-geocode postcodes from BtM sheet\n' +
    '2. Regenerate constraint map\n' +
    '3. Update hosted HTML file\n\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );

  if (response != ui.Button.YES) {
    return;
  }

  // Option 1: Call webhook server (if running)
  var webhookUrl = 'YOUR_WEBHOOK_URL_HERE';  // e.g., ngrok tunnel

  try {
    var options = {
      'method': 'post',
      'contentType': 'application/json',
      'payload': JSON.stringify({
        'action': 'refresh_btm_map',
        'timestamp': new Date().toISOString()
      }),
      'muteHttpExceptions': true
    };

    // Uncomment if webhook server is configured:
    // var result = UrlFetchApp.fetch(webhookUrl, options);
    // ui.alert('Map refresh triggered!\n\nStatus: ' + result.getResponseCode());

    // Placeholder if no webhook:
    ui.alert(
      'Manual Refresh Required',
      'Run these commands on server:\n\n' +
      '1. python3 export_btm_sites_to_csv.py\n' +
      '2. python3 create_constraint_geojson.py\n' +
      '3. python3 create_btm_constraint_map.py\n' +
      '4. Upload btm_constraint_map.html to hosting',
      ui.ButtonSet.OK
    );

  } catch (e) {
    ui.alert('Error: ' + e.toString());
  }
}


/**
 * Show map information dialog
 */
function showMapInfo() {
  var ui = SpreadsheetApp.getUi();

  var html = HtmlService.createHtmlOutput(
    '<div style="font-family: Arial; padding: 20px;">' +
    '<h2>🗺️ DNO Constraint Map</h2>' +
    '<p><b>Data Sources:</b></p>' +
    '<ul>' +
    '<li>BtM Sites: Postcodes from BtM sheet (geocoded via postcodes.io)</li>' +
    '<li>DNO Boundaries: NESO DNO boundaries (GeoJSON)</li>' +
    '<li>Constraint Costs: constraint_costs_by_dno (2017-2025, £10.6B total)</li>' +
    '</ul>' +
    '<p><b>Map Features:</b></p>' +
    '<ul>' +
    '<li>Interactive choropleth showing constraint costs by DNO</li>' +
    '<li>BtM site markers with postcode/location details</li>' +
    '<li>Layer control (toggle DNO boundaries, sites)</li>' +
    '<li>Fullscreen mode</li>' +
    '<li>Multiple base map styles</li>' +
    '</ul>' +
    '<p><b>Technology:</b></p>' +
    '<p>Python (Folium, GeoPandas) → Interactive HTML/JavaScript map</p>' +
    '<p><b>Last Updated:</b> ' + new Date().toLocaleDateString() + '</p>' +
    '<hr>' +
    '<p style="font-size: 11px; color: #666;">GB Power Market JJ | George Major</p>' +
    '</div>'
  ).setWidth(500).setHeight(450);

  ui.showModalDialog(html, 'About Constraint Map');
}


/**
 * Get BtM sheet postcode data for webhook payload
 */
function getBtmPostcodes() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(BTM_SHEET_NAME);

  if (!sheet) {
    return [];
  }

  // Get postcode column (A6 onwards)
  var postcodes = sheet.getRange('A6:A100').getValues();  // Adjust range as needed

  var results = [];
  for (var i = 0; i < postcodes.length; i++) {
    var postcode = postcodes[i][0];
    if (postcode && postcode.toString().trim() !== '') {
      results.push({
        row: i + 6,
        postcode: postcode.toString().trim()
      });
    }
  }

  return results;
}


// ===== SIDEBAR HTML (create separate file: MapSidebar.html) =====
// Uncomment and create this file if using sidebar approach:
/*
<!DOCTYPE html>
<html>
  <head>
    <base target="_blank">
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
      }
      iframe {
        width: 100%;
        height: 100vh;
        border: none;
      }
      .header {
        background-color: #4285f4;
        color: white;
        padding: 10px;
        text-align: center;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <h3>🗺️ DNO Constraint Map</h3>
    </div>
    <iframe src="<?= MAP_URL ?>" allowfullscreen></iframe>
  </body>
</html>
*/
