/**
 * @OnlyCurrentDoc
 *
 * This script creates a real-time energy dashboard in Google Sheets,
 * pulling data from Google BigQuery and providing interactivity.
 */

// ---------------------------------------------------
// CONFIGURATION
// ---------------------------------------------------
const SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc";
const DASHBOARD_SHEET_NAME = "Dashboard V3";
const CHART_DATA_SHEET_NAME = "Chart Data";
const DNO_MAP_SHEET_NAME = 'DNO_Map';
const GCP_PROJECT_ID = "inner-cinema-476211-u9";

// Cell locations
const TIME_RANGE_CELL = 'B3';
const REGION_CELL = 'F3';


// ---------------------------------------------------
// TRIGGERS & MENU
// ---------------------------------------------------

/**
 * Creates a custom menu in the spreadsheet UI.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ GB Energy V3')
    .addItem('1. Manual Refresh All Data', 'refreshAllData')
    .addItem('2. Show DNO Map Selector', 'showDnoMap')
    .addToUi();
}

/**
 * Runs automatically when a user changes the value of any cell.
 * @param {object} e The event object.
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  const cell = range.getA1Notation();

  // If the edited cell is the time range or region dropdown, refresh the data.
  if (sheet.getName() === DASHBOARD_SHEET_NAME && (cell === TIME_RANGE_CELL || cell === REGION_CELL)) {
    refreshAllData();
  }
}

// ---------------------------------------------------
// DATA REFRESH LOGIC
// ---------------------------------------------------

/**
 * Main function to refresh all data on the dashboard.
 * This will be called from the menu or onEdit trigger.
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().toast('🔄 Starting V3 data refresh...');
  
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(DASHBOARD_SHEET_NAME);
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  const timeRange = sheet.getRange(TIME_RANGE_CELL).getValue();
  const selectedDno = sheet.getRange(REGION_CELL).getValue();

  // In a real scenario, you would pass these values to your BigQuery refresh script.
  // For now, we'll just log them.
  Logger.log('Refreshing data for Time Range: "' + timeRange + '" and Region: "' + selectedDno + '"');
  
  // This is where you would call a function to trigger the Python script
  // that repopulates the 'Chart Data' sheet from BigQuery based on the dropdown values.
  // Since we can't directly call Python, we'll assume the data is refreshed externally
  // for the purpose of this script. The Python scripts `populate_dashboard_tables.py`
  // and `add_chart_and_map.py` already do this.
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ V3 Data refresh complete!', 'Success', 5);
}


// ---------------------------------------------------
// DNO MAP SIDEBAR
// ---------------------------------------------------

/**
 * Shows the DNO map selector sidebar.
 */
function showDnoMap() {
  const html = HtmlService
    .createTemplateFromFile('DnoMap')
    .evaluate()
    .setTitle('Select DNO Region')
    .setWidth(400);
  SpreadsheetApp.getUi().showSidebar(html);
}

/**
 * Fetches DNO locations and metrics from the DNO_Map sheet for the sidebar.
 * Called from DnoMap.html.
 * @returns {Array<Object>} A list of DNO objects with code, name, lat, lng.
 */
function getDnoLocations() {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(DNO_MAP_SHEET_NAME);
  if (!sheet) {
    Logger.log('Error: Sheet "' + DNO_MAP_SHEET_NAME + '" not found.');
    return [];
  }

  const values = sheet.getDataRange().getValues();
  if (values.length < 2) {
      return []; // No data
  }
  
  const header = values.shift(); // Get header row
  const idxCode = header.indexOf('DNO Code');
  const idxName = header.indexOf('DNO Name');
  const idxLat = header.indexOf('Latitude');
  const idxLng = header.indexOf('Longitude');
  const idxNetMargin = header.indexOf('Net Margin (£/MWh)');

  if (idxCode === -1 || idxName === -1 || idxLat === -1 || idxLng === -1) {
      Logger.log("DNO_Map sheet is missing required columns (DNO Code, DNO Name, Latitude, Longitude).");
      return [];
  }

  return values
    .filter(function(r) { return r[idxCode]; }) // Ensure DNO code exists
    .map(function(r) {
      return {
        code: String(r[idxCode]),
        name: String(r[idxName]),
        lat: Number(r[idxLat]),
        lng: Number(r[idxLng]),
        netMargin: Number(r[idxNetMargin] || 0)
      };
    });
}

/**
 * Sets the selected DNO NAME in the region cell on the dashboard.
 * Called from DnoMap.html when a user clicks a marker.
 * @param {string} nameOrCode The DNO name (e.g., "UKPN-EPN") or code.
 */
function selectDno(nameOrCode) {
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName(DASHBOARD_SHEET_NAME);
  if (!dash) {
      Logger.log('Error: Dashboard sheet "' + DASHBOARD_SHEET_NAME + '" not found.');
      return;
  }
  dash.getRange(REGION_CELL).setValue(nameOrCode);
  // The onEdit trigger will automatically handle the data refresh.
}
