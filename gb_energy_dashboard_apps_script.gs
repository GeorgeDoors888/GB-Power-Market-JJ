/**
 * GB Energy Dashboard maintenance script - ENHANCED VERSION
 * - Renames "Sheet1" -> "Dashboard"
 * - Keeps "Dashboard" updated (copies values from legacy "Sheet1" if present)
 * - Fixes garbled interconnector flag labels (e.g., �🇴 NSL -> 🇳🇴 NSL)
 * - Inserts/updates a line chart with: System Sell Price (£/MWh), Demand (GW),
 *   Generation (GW), Wind Generation (GW), Expected Wind Generation (GW).
 * - Adds a 15-minute time-driven trigger to refresh data.
 * - Adds a custom menu with manual refresh button.
 * - Audit logging with color-coded status tracking
 * - User and source provenance tracking
 *
 * HOW TO USE:
 * 1) Extensions → Apps Script → New project, paste this whole file.
 * 2) From the dropdown, run setupDashboard() once and grant permissions.
 * 3) The auto-refresh trigger will run refreshData() every 15 minutes.
 * 4) Use the "Dashboard" menu → "Refresh Data" button to manually refresh.
 * 5) View "Audit Log" sheet to see all update history.
 */

// ============================================
// CONFIGURATION
// ============================================

const CONFIG = {
  // Sheet names
  DASHBOARD_TAB: 'Dashboard',
  SOURCE_TAB: 'Sheet1',
  AUDIT_LOG_TAB: 'Audit_Log',
  
  // Metadata tracking
  META_CELLS: {
    LAST_UPDATED: 'B1',
    UPDATED_BY: 'C1',
    SOURCE: 'D1'
  },
  
  // Chart settings
  CHART: {
    TITLE: 'Market Overview',
    POSITION_ROW: 2,
    POSITION_COL: 8,
    LEGEND: 'bottom'
  },
  
  // Trigger settings
  REFRESH_INTERVAL_MINUTES: 15,
  
  // Audit log colors
  LOG_COLORS: {
    SUCCESS: '#b7e1cd',  // Light green
    ERROR: '#f4c7c3',    // Light red
    WARNING: '#fce8b2',  // Light yellow
    INFO: '#d9ead3',     // Light blue-green
    SETUP: '#cfe2f3'     // Light blue
  },
  
  // Maximum audit log entries
  MAX_LOG_ENTRIES: 1000
};

// ============================================
// LOGGING & AUDIT FUNCTIONS
// ============================================

/**
 * Logs an action to the Audit Log sheet with color-coding
 * @param {string} action - Action type (REFRESH, SETUP, ERROR, etc.)
 * @param {string} status - Status (SUCCESS, ERROR, WARNING, INFO)
 * @param {string} details - Detailed message
 * @param {string} source - Source of the action (manual, trigger, api, etc.)
 */
function logAction(action, status, details, source = 'manual') {
  try {
    const ss = SpreadsheetApp.getActive();
    let logSheet = ss.getSheetByName(CONFIG.AUDIT_LOG_TAB);
    
    // Create Audit Log sheet if it doesn't exist
    if (!logSheet) {
      logSheet = ss.insertSheet(CONFIG.AUDIT_LOG_TAB);
      // Initialize with headers
      logSheet.getRange('A1:E1').setValues([['Timestamp', 'User', 'Action', 'Status', 'Details']]);
      logSheet.getRange('A1:E1').setBackground('#4285f4').setFontColor('white').setFontWeight('bold');
      logSheet.setFrozenRows(1);
      logSheet.setColumnWidth(1, 150); // Timestamp
      logSheet.setColumnWidth(2, 200); // User
      logSheet.setColumnWidth(3, 120); // Action
      logSheet.setColumnWidth(4, 100); // Status
      logSheet.setColumnWidth(5, 400); // Details
    }
    
    // Get current user
    const user = Session.getActiveUser().getEmail() || Session.getEffectiveUser().getEmail() || 'system';
    const timestamp = new Date();
    
    // Insert new row at top (after header)
    logSheet.insertRowAfter(1);
    const newRow = logSheet.getRange('A2:E2');
    newRow.setValues([[
      Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
      user,
      action,
      status,
      details
    ]]);
    
    // Apply color based on status
    const color = CONFIG.LOG_COLORS[status] || '#ffffff';
    newRow.setBackground(color);
    
    // Trim log if too long
    const maxRows = CONFIG.MAX_LOG_ENTRIES;
    if (logSheet.getLastRow() > maxRows + 1) {
      logSheet.deleteRows(maxRows + 2, logSheet.getLastRow() - maxRows - 1);
    }
    
    // Update metadata in Dashboard
    updateMetadata(source, user);
    
  } catch (error) {
    console.error('Failed to log action:', error);
    // Don't throw - logging failures shouldn't break the main function
  }
}

/**
 * Updates metadata (Last Updated, User, Source) in Dashboard sheet
 * @param {string} source - Source of the update
 * @param {string} user - User who triggered the update
 */
function updateMetadata(source, user) {
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName(CONFIG.DASHBOARD_TAB);
    if (!dashboard) return;
    
    const timestamp = new Date();
    const timeStr = Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss z');
    
    // Set metadata
    dashboard.getRange(CONFIG.META_CELLS.LAST_UPDATED).setValue(timeStr);
    dashboard.getRange(CONFIG.META_CELLS.UPDATED_BY).setValue(user || 'system');
    dashboard.getRange(CONFIG.META_CELLS.SOURCE).setValue(source || 'unknown');
    
    // Format metadata cells
    dashboard.getRange('A1:D1').setFontWeight('bold').setBackground('#f3f3f3');
    
  } catch (error) {
    console.error('Failed to update metadata:', error);
  }
}

// ============================================
// MENU FUNCTIONS
// ============================================

/**
 * Called automatically when the spreadsheet opens.
 * Creates a custom menu with refresh button.
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔄 Dashboard')
    .addItem('Refresh Data Now', 'manualRefresh')
    .addSeparator()
    .addItem('Setup Dashboard', 'setupDashboard')
    .addItem('View Audit Log', 'showAuditLog')
    .addItem('View Status', 'showLogs')
    .addToUi();
  
  // Log the open event
  logAction('OPEN', 'INFO', 'Spreadsheet opened', 'user');
}

/**
 * Manual refresh function - can be called from menu button or API
 */
function manualRefresh() {
  const ui = SpreadsheetApp.getUi();
  const startTime = new Date();
  
  try {
    logAction('MANUAL_REFRESH', 'INFO', 'Manual refresh started', 'user');
    
    refreshData();
    
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    const message = `Dashboard refreshed successfully at ${new Date().toLocaleString()}\n\nDuration: ${duration} seconds`;
    
    logAction('MANUAL_REFRESH', 'SUCCESS', `Completed in ${duration}s`, 'user');
    ui.alert('✅ Success!', message, ui.ButtonSet.OK);
    
  } catch (e) {
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    logAction('MANUAL_REFRESH', 'ERROR', `Failed after ${duration}s: ${e.message}`, 'user');
    ui.alert('❌ Error', 'Failed to refresh: ' + e.message, ui.ButtonSet.OK);
    throw e;
  }
}

/**
 * Opens and displays the Audit Log sheet
 */
function showAuditLog() {
  const ss = SpreadsheetApp.getActive();
  let logSheet = ss.getSheetByName(CONFIG.AUDIT_LOG_TAB);
  
  if (!logSheet) {
    SpreadsheetApp.getUi().alert('ℹ️ No Audit Log',
      'Audit log will be created when you run Setup Dashboard or first refresh.',
      SpreadsheetApp.getUi().ButtonSet.OK);
    return;
  }
  
  logSheet.activate();
  
  const lastRow = logSheet.getLastRow();
  const message = `Audit Log contains ${lastRow - 1} entries.\n\n` +
                  `Use column filters to:\n` +
                  `• Filter by date/time\n` +
                  `• Filter by user\n` +
                  `• Filter by action type\n` +
                  `• Filter by status\n\n` +
                  `Colors indicate:\n` +
                  `🟢 Green = Success\n` +
                  `🔴 Red = Error\n` +
                  `🟡 Yellow = Warning\n` +
                  `🔵 Blue = Info/Setup`;
  
  SpreadsheetApp.getUi().alert('📋 Audit Log', message, SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Show dashboard status and configuration
 */
function showLogs() {
  const ui = SpreadsheetApp.getUi();
  const ss = SpreadsheetApp.getActive();
  const dashboard = ss.getSheetByName(CONFIG.DASHBOARD_TAB);
  
  if (!dashboard) {
    ui.alert('ℹ️ No Dashboard', 'Dashboard sheet not found. Run Setup Dashboard first.', ui.ButtonSet.OK);
    return;
  }
  
  // Get metadata
  const lastUpdated = dashboard.getRange(CONFIG.META_CELLS.LAST_UPDATED).getValue();
  const updatedBy = dashboard.getRange(CONFIG.META_CELLS.UPDATED_BY).getValue();
  const source = dashboard.getRange(CONFIG.META_CELLS.SOURCE).getValue();
  
  // Count triggers
  const triggers = ScriptApp.getProjectTriggers();
  const refreshTriggers = triggers.filter(t => t.getHandlerFunction() === 'refreshData');
  
  // Get audit log stats
  const logSheet = ss.getSheetByName(CONFIG.AUDIT_LOG_TAB);
  const logEntries = logSheet ? logSheet.getLastRow() - 1 : 0;
  
  const msg = `📊 Dashboard Status\n\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `Sheet: ${CONFIG.DASHBOARD_TAB}\n` +
              `Total Rows: ${dashboard.getLastRow()}\n` +
              `Total Columns: ${dashboard.getLastColumn()}\n\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `Last Updated: ${lastUpdated || 'Never'}\n` +
              `Updated By: ${updatedBy || 'Unknown'}\n` +
              `Source: ${source || 'Unknown'}\n\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `Auto-refresh: Every ${CONFIG.REFRESH_INTERVAL_MINUTES} minutes\n` +
              `Active Triggers: ${refreshTriggers.length}\n\n` +
              `━━━━━━━━━━━━━━━━━━━━━━\n` +
              `Audit Log Entries: ${logEntries}\n` +
              `Max Entries: ${CONFIG.MAX_LOG_ENTRIES}`;
  
  ui.alert('📊 Dashboard Status', msg, ui.ButtonSet.OK);
}

function setupDashboard() {
  const ss = SpreadsheetApp.getActive();
  const startTime = new Date();
  
  try {
    logAction('SETUP', 'INFO', 'Dashboard setup started', 'manual');
    
    // Create audit log first
    let logSheet = ss.getSheetByName(CONFIG.AUDIT_LOG_TAB);
    if (!logSheet) {
      logSheet = ss.insertSheet(CONFIG.AUDIT_LOG_TAB);
      logSheet.getRange('A1:E1').setValues([['Timestamp', 'User', 'Action', 'Status', 'Details']]);
      logSheet.getRange('A1:E1').setBackground('#4285f4').setFontColor('white').setFontWeight('bold');
      logSheet.setFrozenRows(1);
    }
    
    renameSheet1ToDashboard_(ss);
    logAction('SETUP', 'INFO', 'Sheet renamed to Dashboard', 'setup');
    
    // Keep a one-time copy to Dashboard if legacy Sheet1 exists
    copySheet1IntoDashboardIfNeeded_(ss);
    logAction('SETUP', 'INFO', 'Data copied to Dashboard', 'setup');
    
    // Fix labels (garbled emojis / flags)
    fixInterconnectorFlags_(ss);
    logAction('SETUP', 'INFO', 'Interconnector flags fixed', 'setup');
    
    // Create or update the chart
    upsertDashboardChart_(ss);
    logAction('SETUP', 'INFO', 'Chart created/updated', 'setup');
    
    // Ensure a periodic trigger exists
    ensureAutoRefreshTrigger_();
    logAction('SETUP', 'INFO', `Auto-refresh trigger set to ${CONFIG.REFRESH_INTERVAL_MINUTES} minutes`, 'setup');
    
    // Stamp last updated
    stampLastUpdated_(CONFIG.DASHBOARD_TAB);
    
    SpreadsheetApp.flush();
    
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    logAction('SETUP', 'SUCCESS', `Setup completed in ${duration}s`, 'setup');
    
    // Show success message
    const ui = SpreadsheetApp.getUi();
    ui.alert('✅ Setup Complete!',
      `Dashboard setup completed successfully!\n\n` +
      `Duration: ${duration} seconds\n\n` +
      `Features enabled:\n` +
      `• Dashboard sheet created/updated\n` +
      `• Chart created with 5 metrics\n` +
      `• Auto-refresh every ${CONFIG.REFRESH_INTERVAL_MINUTES} minutes\n` +
      `• Audit log initialized\n` +
      `• Custom menu added\n\n` +
      `Use "🔄 Dashboard" menu to refresh manually!`,
      ui.ButtonSet.OK);
    
  } catch (error) {
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    logAction('SETUP', 'ERROR', `Setup failed after ${duration}s: ${error.message}`, 'setup');
    throw error;
  }
}

function refreshData() {
  const ss = SpreadsheetApp.getActive();
  const startTime = new Date();
  
  try {
    // Determine if called by trigger or manually
    const source = 'trigger'; // Triggers call this directly
    
    logAction('REFRESH', 'INFO', 'Auto-refresh started', source);
    
    // If your pipeline still writes to "Sheet1", keep Dashboard synced.
    copySheet1IntoDashboardIfNeeded_(ss);
    
    // Fix labels again (in case new rows appeared)
    fixInterconnectorFlags_(ss);
    
    // Keep the chart pointing at current data region
    upsertDashboardChart_(ss);
    
    // Stamp last updated
    stampLastUpdated_(CONFIG.DASHBOARD_TAB);
    
    SpreadsheetApp.flush();
    
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    logAction('REFRESH', 'SUCCESS', `Completed in ${duration}s`, source);
    
  } catch (error) {
    const duration = ((new Date() - startTime) / 1000).toFixed(2);
    logAction('REFRESH', 'ERROR', `Failed after ${duration}s: ${error.message}`, 'trigger');
    throw error;
  }
}

/** --- Helpers --- */

function renameSheet1ToDashboard_(ss) {
  const sheet1 = ss.getSheetByName(CONFIG.SOURCE_TAB);
  if (sheet1) {
    let dst = ss.getSheetByName(CONFIG.DASHBOARD_TAB);
    if (dst) {
      // If "Dashboard" already exists, we keep it and remove the old "Sheet1" after copy.
      return;
    }
    sheet1.setName(CONFIG.DASHBOARD_TAB);
  }
}

function copySheet1IntoDashboardIfNeeded_(ss) {
  const src = ss.getSheetByName(CONFIG.SOURCE_TAB);
  const dst = ss.getSheetByName(CONFIG.DASHBOARD_TAB) || ss.insertSheet(CONFIG.DASHBOARD_TAB);
  if (!src) return;

  // Clear destination and copy values-only
  const srcRange = src.getDataRange();
  const values = srcRange.getValues();
  dst.clear({contentsOnly: true});
  if (values.length && values[0].length) {
    dst.getRange(1, 1, values.length, values[0].length).setValues(values);
  }
}

/**
 * Replace garbled flag sequences and normalize labels for interconnectors.
 * Strategy:
 *  - Scan the sheet for strings matching interconnector patterns (NSL, IFA, IFA2, Nemo, BritNed, EWIC, Moyle, etc.)
 *  - Force-correct the flag emoji by mapping country names to flags.
 *  - Remove stray replacement chars (�).
 */
function fixInterconnectorFlags_(ss) {
  const sh = ss.getSheetByName(CONFIG.DASHBOARD_TAB);
  if (!sh) return;
  const rng = sh.getDataRange();
  const values = rng.getValues();
  const mapCountryToFlag = {
    "Norway": "🇳🇴",
    "France": "🇫🇷",
    "Belgium": "🇧🇪",
    "Netherlands": "🇳🇱",
    "Ireland": "🇮🇪",
    "Northern Ireland": "🇬🇧", // often represented with GB flag in GB dashboards
    "Denmark": "🇩🇰",
    "Germany": "🇩🇪"
  };

  function normalizeLabel(s) {
    if (typeof s !== 'string') return s;
    if (!s) return s;
    // Remove stray replacement character
    s = s.replace(/\uFFFD/g, "");
    // Known interconnector names to normalize
    // Examples: "NSL (Norway)", "IFA (France)", "IFA2 (France)", "Nemo Link (Belgium)"
    const m = s.match(/^([A-Za-z0-9\s\-]+)\s*\(([^)]+)\)\s*$/);
    if (m) {
      const name = m[1].trim();
      const country = m[2].trim();
      const flag = mapCountryToFlag[country] || "";
      if (flag) return `${flag} ${name} (${country})`;
      return `${name} (${country})`;
    }
    // Fallback: common fixes for when country is abbreviated
    s = s.replace(/\bNSL\b/g, "NSL");
    s = s.replace(/\bIFA2?\b/g, (x)=>x); // keep IFA / IFA2
    // Remove stray single regional indicator chars that show up as half-flags
    s = s.replace(/[\uD83C][\uDDE6-\uDDFF](?![\uD83C][\uDDE6-\uDDFF])/g, "");
    return s;
  }

  let changed = false;
  for (let r = 0; r < values.length; r++) {
    for (let c = 0; c < values[r].length; c++) {
      const v = values[r][c];
      const nv = normalizeLabel(v);
      if (nv !== v) {
        values[r][c] = nv;
        changed = true;
      }
    }
  }
  if (changed) rng.setValues(values);
}

/**
 * Find a header by (case-insensitive) starts-with or includes.
 */
function findColumnIndexByHeader_(sheet, candidates) {
  const header = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const lower = header.map(h => (h+"").toLowerCase());
  for (let i = 0; i < lower.length; i++) {
    const h = lower[i];
    for (const cand of candidates) {
      const needle = cand.toLowerCase();
      if (h === needle || h.startsWith(needle) || h.includes(needle)) return i;
    }
  }
  return -1;
}

/**
 * Insert or update a multi-series line chart on "Dashboard" using columns:
 * Time (x-axis), System Sell Price (£/MWh), Demand (GW), Generation, Wind Generation, Expected Wind Generation.
 * It will search the header row to find the right columns regardless of exact phrasing.
 */
function upsertDashboardChart_(ss) {
  const sh = ss.getSheetByName(CONFIG.DASHBOARD_TAB);
  if (!sh) return;

  const lastRow = sh.getLastRow();
  const lastCol = sh.getLastColumn();
  if (lastRow < 2 || lastCol < 2) return;

  // Guess a time column
  const timeCol = findColumnIndexByHeader_(sh, ["datetime", "timestamp", "settlement", "period start", "time"]);
  if (timeCol === -1) return; // can't build chart without x-axis

  // Series columns
  const colSSP   = findColumnIndexByHeader_(sh, ["system sell price", "ssp", "sell price"]);
  const colDem   = findColumnIndexByHeader_(sh, ["demand", "demand gw"]);
  const colGen   = findColumnIndexByHeader_(sh, ["generation total", "total generation", "generation"]);
  const colWind  = findColumnIndexByHeader_(sh, ["wind generation", "wind (gw)", "wind"]);
  const colWindX = findColumnIndexByHeader_(sh, ["expected wind generation", "forecast wind", "exp wind"]);

  // Build the ranges dynamically (only columns we find)
  const ranges = [];
  function pushColRange(colIndexZero) {
    if (colIndexZero === -1) return;
    const range = sh.getRange(1, colIndexZero + 1, lastRow, 1);
    ranges.push(range);
  }
  // X axis first
  pushColRange(timeCol);
  // Then series
  pushColRange(colSSP);
  pushColRange(colDem);
  pushColRange(colGen);
  pushColRange(colWind);
  pushColRange(colWindX);

  if (!ranges.length || ranges.length === 1) return;

  // Delete existing chart with same title to avoid duplicates
  const existingCharts = sh.getCharts();
  for (const ch of existingCharts) {
    const opt = ch.getOptions();
    if (opt && opt.get("title") === "Market Overview") {
      sh.removeChart(ch);
    }
  }

  const builder = sh.newChart()
    .asLineChart()
    .addRange(ranges[0]); // x-axis

  for (let i = 1; i < ranges.length; i++) {
    builder.addRange(ranges[i]);
  }

  builder
    .setOption("title", CONFIG.CHART.TITLE)
    .setOption("legend", { position: CONFIG.CHART.LEGEND })
    .setNumHeaders(1)
    .setPosition(CONFIG.CHART.POSITION_ROW, CONFIG.CHART.POSITION_COL, 0, 0);

  sh.insertChart(builder.build());
}

function ensureAutoRefreshTrigger_() {
  // Remove duplicates, keep one trigger for refreshData()
  const triggers = ScriptApp.getProjectTriggers();
  let hasTrigger = false;
  
  for (const t of triggers) {
    if (t.getHandlerFunction() === "refreshData" && t.getEventType() === ScriptApp.EventType.CLOCK) {
      if (hasTrigger) {
        // Delete duplicate triggers
        ScriptApp.deleteTrigger(t);
      } else {
        hasTrigger = true;
      }
    }
  }
  
  // Create trigger if none exists
  if (!hasTrigger) {
    ScriptApp.newTrigger("refreshData")
      .timeBased()
      .everyMinutes(CONFIG.REFRESH_INTERVAL_MINUTES)
      .create();
  }
}

function stampLastUpdated_(sheetName) {
  const sh = SpreadsheetApp.getActive().getSheetByName(sheetName);
  if (!sh) return;
  
  // Set headers in A1:D1 if not already present
  const a1 = sh.getRange("A1").getValue();
  if (!a1 || a1.toString().toLowerCase().indexOf("file") === -1) {
    sh.getRange("A1").setValue("File: " + sheetName);
  }
  
  const b1 = sh.getRange("B1").getValue();
  if (!b1 || b1.toString().toLowerCase().indexOf("updated") === -1) {
    sh.getRange("B1").setValue("Last Updated");
  }
  
  const c1 = sh.getRange("C1").getValue();
  if (!c1 || c1.toString().toLowerCase().indexOf("by") === -1) {
    sh.getRange("C1").setValue("Updated By");
  }
  
  const d1 = sh.getRange("D1").getValue();
  if (!d1 || d1.toString().toLowerCase().indexOf("source") === -1) {
    sh.getRange("D1").setValue("Source");
  }
  
  // Format header row
  sh.getRange("A1:D1").setFontWeight("bold").setBackground("#f3f3f3");
  
  // The actual timestamp will be set by updateMetadata()
}
