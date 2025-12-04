/**
 * GB Energy Dashboard V3 - Apps Script Installation
 * 
 * INSTALLATION INSTRUCTIONS:
 * 1. Open your spreadsheet: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
 * 2. Go to Extensions → Apps Script
 * 3. Delete any existing Code.gs file
 * 4. Copy the entire code below and paste it as Code.gs
 * 5. Create a new HTML file: File → New → HTML file, name it "DnoMap"
 * 6. Copy the HTML code from the next section
 * 7. Save and reload your spreadsheet
 */

// ============================================================================
// CODE.GS - Main Apps Script Code
// ============================================================================

const DASHBOARD_SHEET_NAME = 'Dashboard';
const DNO_MAP_SHEET_NAME = 'DNO_Map';
const DNO_TARGET_CELL = 'F3';

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ GB Energy')
    .addItem('DNO Map Selector', 'showDnoMap')
    .addToUi();
}

function showDnoMap() {
  const html = HtmlService
    .createHtmlOutputFromFile('DnoMap')
    .setTitle('Select DNO Region')
    .setWidth(500);
  SpreadsheetApp.getUi().showSidebar(html);
}

// Returns DNO locations + KPIs for the DnoMap.html UI
function getDnoLocations() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(DNO_MAP_SHEET_NAME);
  if (!sheet) return [];

  const values = sheet.getDataRange().getValues();
  if (!values.length) return [];

  const header = values.shift();
  const idxCode = header.indexOf('DNO Code');
  const idxName = header.indexOf('DNO Name');
  const idxLat  = header.indexOf('Latitude');
  const idxLng  = header.indexOf('Longitude');
  const idxNetMargin = header.indexOf('Net Margin (£/MWh)');

  return values
    .filter(r => r[idxCode])
    .map(r => ({
      code: String(r[idxCode]),
      name: String(r[idxName]),
      lat: Number(r[idxLat]),
      lng: Number(r[idxLng]),
      netMargin: Number(r[idxNetMargin] || 0)
    }));
}

// Called from HTML when user chooses a DNO
function selectDno(code) {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) return;
  dash.getRange(DNO_TARGET_CELL).setValue(code);
}
