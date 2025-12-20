/**
 * @OnlyCurrentDoc
 */

const PROJECT_ID = 'inner-cinema-476211-u9';
const DATASET = 'uk_energy_prod';

/**
 * Adds a custom menu to the spreadsheet.
 */
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('GB Live Dashboard')
      .addItem('Force Refresh Dashboard', 'updateDashboard')
      .addItem('Setup Live Dashboard v2', 'createV2Dashboard')
      .addSeparator()
      .addItem('Add KPI Sparklines', 'addKPISparklinesManual')
      .addItem('Enable Auto-Sparklines', 'installSparklineMaintenance')
      .addSeparator()
      .addItem('Test Connection', 'testConnection')
      .addToUi();

  // Add BtM Tools menu
  try {
    createBtmMenu();
  } catch (e) {
    Logger.log('BtM menu creation failed: ' + e);
  }

  // Auto-add KPI sparklines on sheet open if they're missing
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName('Live Dashboard v2');
    if (sheet) {
      const b4 = sheet.getRange('B4').getFormula();
      if (!b4 || !b4.includes('SPARKLINE')) {
        updateKPISparklines();
      }
    }
  } catch (e) {
    Logger.log('Auto-sparkline failed: ' + e);
  }
}

function testConnection() {
  const scriptId = ScriptApp.getScriptId();
  SpreadsheetApp.getUi().alert('✅ Connection Successful!\n\nRunning Script ID: ' + scriptId + '\n\n(Target: 1b2dOZ...)');
}

/**
 * Main function to update the dashboard.
 */
function updateDashboard() {
  Logger.log('VERSION: Bigger Sparklines 2.0 - Script ID Check');

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getActiveSheet();

    // Check if we are on v2 sheet to apply v2 layout (Case insensitive)
    if (sheet.getName().toLowerCase().includes('v2')) {
      setupDashboardLayoutV2(sheet);
    } else {
      setupDashboardLayout(sheet);
    }

    const data = fetchData();

    if (data) {
      displayData(sheet, data);
      createCharts(sheet, data);
      sheet.getRange('A2:L2').merge()
        .setValue('Last Updated: ' + new Date().toLocaleString('en-GB', { timeZone: 'Europe/London' }) + ' (v2.0)');
      SpreadsheetApp.getUi().alert('Dashboard refresh complete! (v2.0)');
    } else {
      SpreadsheetApp.getUi().alert('Failed to fetch data. Please check the logs.');
    }
  } catch (e) {
    Logger.log('ERROR: ' + e.toString());
    SpreadsheetApp.getUi().alert('Error updating dashboard: ' + e.toString());
  }
}

function createV2Dashboard() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('Live Dashboard v2');
  if (!sheet) {
    sheet = ss.insertSheet('Live Dashboard v2');
  }
  ss.setActiveSheet(sheet);
  updateDashboard();
}

/**
 * Executes a BigQuery query and returns results.
 */
function executeBigQuery(query) {
  try {
    const request = {
      query: query,
      useLegacySql: false,
      location: 'US'
    };

    const queryResults = BigQuery.Jobs.query(request, PROJECT_ID);
    const jobId = queryResults.jobReference.jobId;

    let rows = queryResults.rows;
    while (queryResults.pageToken) {
      queryResults = BigQuery.Jobs.getQueryResults(PROJECT_ID, jobId, {
        pageToken: queryResults.pageToken
      });
      rows = rows.concat(queryResults.rows);
    }

    return rows || [];
  } catch (e) {
    Logger.log('BigQuery Error: ' + e.toString());
    return null;
  }
}
