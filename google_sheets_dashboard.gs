/********************************************************************
 * GB POWER MARKET - LIVE DASHBOARD (Apps Script)
 * 
 * ✅ CORRECTED VERSION for your actual BigQuery schema
 * 
 * KEY FIXES APPLIED:
 * - Uses /api/proxy-v2 (working endpoint)
 * - camelCase column names (settlementDate, settlementPeriod)
 * - Correct table names (bmrs_mid instead of detsysprices)
 * - Compatible with inner-cinema-476211-u9.uk_energy_prod dataset
 * - Matches your Python dashboard refresh logic
 * 
 * INSTALLATION:
 * 1. Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit
 * 2. Extensions → Apps Script
 * 3. Replace Code.gs with this entire file
 * 4. Save and authorize
 * 5. Refresh page → Menu "⚡ Power Market" appears
 * 6. Run: "Refresh Now (today)" or "Set 5-min Trigger"
 ********************************************************************/

/************  CONFIG  ************/
/**
 * CRITICAL PROJECT CONFIGURATION
 * 
 * This Apps Script lives in: jibber-jabber-knowledge (upowerenergy.uk)
 * But queries BigQuery data in: inner-cinema-476211-u9 (Smart Grid)
 * 
 * DO NOT CHANGE PROJECT to 'jibber-jabber-knowledge' - the BMRS data 
 * is in inner-cinema-476211-u9.uk_energy_prod!
 * 
 * See: PROJECT_IDENTITY_MASTER.md for full explanation
 */
const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2'; // ✅ Vercel proxy
const TZ = 'Europe/London';
const PROJECT = 'inner-cinema-476211-u9';  // ✅ Smart Grid BigQuery (BMRS data lives here)
const DATASET = 'uk_energy_prod';  // ✅ BMRS tables dataset

/************  MENUS  ************/
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('⚡ Power Market')
    .addItem('🔄 Refresh Now (today)', 'refreshDashboardToday')
    .addItem('📊 Rebuild Chart', 'rebuildDashboardChart')
    .addSeparator()
    .addItem('⏰ Set 5-min Auto-Refresh', 'set5MinTrigger')
    .addItem('🛑 Stop Auto-Refresh', 'removeAllTimeTriggers')
    .addSeparator()
    .addItem('🚀 One-Click Setup', 'Setup_Dashboard_AutoRefresh')
    .addToUi();
}

/************  STRUCTURE  ************/
function ensureStructure() {
  const ss = SpreadsheetApp.getActive();
  const needSheets = ['Live Dashboard', 'Chart Data', 'Audit_Log', 'Live_Raw_Prices', 
                      'Live_Raw_Gen', 'Live_Raw_BOA', 'Live_Raw_IC'];
  
  needSheets.forEach(name => { 
    if (!ss.getSheetByName(name)) {
      ss.insertSheet(name);
      stampAudit('info', `Created sheet: ${name}`);
    }
  });

  // Chart Data headers
  const cd = ss.getSheetByName('Chart Data');
  if (cd.getLastRow() < 1) {
    cd.appendRow(['SP','Time','SSP £/MWh','SBP £/MWh','Demand MW','Generation MW','BOALF Actions','BOD Offer £/MWh','BOD Bid £/MWh','IC Net MW']);
  }

  // Named range for today's 48 settlement periods (will be reset on refresh)
  try { 
    ss.setNamedRange('NR_DASH_TODAY', cd.getRange('A2:J49')); 
  } catch (e) {
    stampAudit('warn', 'Named range creation: ' + e);
  }
}

/************  TIME HELPERS  ************/
function todayDateStr_YYYY_MM_DD() {
  const now = new Date();
  return Utilities.formatDate(now, TZ, 'yyyy-MM-dd');
}

function spToClock(sp) {
  // SP1=00:00, SP2=00:30 ... SP48=23:30
  const zeroIdx = sp - 1;
  const hh = Math.floor(zeroIdx / 2);
  const mm = (zeroIdx % 2) ? '30' : '00';
  return String(hh).padStart(2,'0') + ':' + mm;
}

/************  PROXY HELPERS  ************/
function proxyGet(sql) {
  const url = VERCEL_PROXY + '?path=/query_bigquery_get&sql=' + encodeURIComponent(sql);
  
  try {
    const resp = UrlFetchApp.fetch(url, { 
      method: 'get', 
      muteHttpExceptions: true,
      validateHttpsCertificates: true
    });
    
    const code = resp.getResponseCode();
    const body = resp.getContentText();
    
    if (code !== 200) {
      throw new Error(`HTTP ${code}: ${body.substring(0, 500)}`);
    }
    
    const json = JSON.parse(body);
    
    if (!json.success) {
      throw new Error(`Query failed: ${json.error || 'Unknown error'}`);
    }
    
    return json;
    
  } catch (e) {
    stampAudit('error', `proxyGet failed: ${e.message}`);
    throw new Error(`BigQuery proxy error: ${e.message}`);
  }
}

function pingHealth() {
  try {
    const url = VERCEL_PROXY + '?path=/health';
    const resp = UrlFetchApp.fetch(url, { method: 'get', muteHttpExceptions: true });
    const code = resp.getResponseCode();
    const body = resp.getContentText();
    return { code: code, body: body, ok: code === 200 };
  } catch (e) {
    return { code: 0, body: e.message, ok: false };
  }
}

/************  SQL QUERIES (CORRECTED FOR YOUR SCHEMA)  ************/

/**
 * System Prices: SSP/SBP from bmrs_mid
 * Uses camelCase: settlementDate, settlementPeriod, dataProvider, price
 */
function sqlSystemPrices(ymd) {
  return `
    WITH prices AS (
      SELECT 
        DATE(settlementDate) AS d, 
        settlementPeriod AS sp,
        dataProvider,
        AVG(price) AS price
      FROM \`${PROJECT}.${DATASET}.bmrs_mid\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
      GROUP BY d, sp, dataProvider
    )
    SELECT 
      sp,
      MAX(CASE WHEN dataProvider = 'N2EXMIDP' THEN price END) AS ssp,
      MAX(CASE WHEN dataProvider = 'APXMIDP' THEN price END) AS sbp
    FROM prices
    GROUP BY sp
    ORDER BY sp
  `;
}

/**
 * Generation & Demand from IRIS tables
 * Uses camelCase: settlementDate, settlementPeriod, boundary, generation, demand
 */
function sqlGenDemand(ymd) {
  return `
    WITH gen AS (
      SELECT 
        settlementPeriod AS sp,
        AVG(generation) AS gen_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_indgen_iris\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
        AND boundary = 'N'  -- National total
      GROUP BY sp
    ),
    dem AS (
      SELECT 
        settlementPeriod AS sp,
        ABS(AVG(demand)) AS demand_mw  -- Demand is negative, take absolute value
      FROM \`${PROJECT}.${DATASET}.bmrs_inddem_iris\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
        AND boundary = 'N'  -- National total
      GROUP BY sp
    )
    SELECT 
      COALESCE(gen.sp, dem.sp) AS sp,
      gen.gen_mw,
      dem.demand_mw
    FROM gen
    FULL OUTER JOIN dem ON gen.sp = dem.sp
    ORDER BY sp
  `;
}

/**
 * BOALF: Accepted balancing offers/bids
 * Uses camelCase: settlementDate, settlementPeriodFrom, levelFrom, levelTo
 */
function sqlBOALF(ymd) {
  return `
    SELECT 
      settlementPeriodFrom AS sp,
      COUNT(*) AS boalf_count,
      AVG(ABS(levelTo - levelFrom)) AS boalf_avg_mw
    FROM \`${PROJECT}.${DATASET}.bmrs_boalf\`
    WHERE DATE(settlementDate) = DATE('${ymd}')
    GROUP BY sp
    ORDER BY sp
  `;
}

/**
 * BOD: Bid-Offer Data (price pairs)
 * Uses camelCase: settlementDate, settlementPeriod, bid, offer
 */
function sqlBOD(ymd) {
  return `
    SELECT 
      settlementPeriod AS sp,
      AVG(CASE WHEN offer > 0 AND offer < 9000 THEN offer END) AS bod_offer,
      AVG(CASE WHEN bid > 0 AND bid < 9000 THEN bid END) AS bod_bid
    FROM \`${PROJECT}.${DATASET}.bmrs_bod\`
    WHERE DATE(settlementDate) = DATE('${ymd}')
    GROUP BY sp
    ORDER BY sp
  `;
}

/**
 * Interconnector Net Flow: Generation - Demand
 * Positive = net export, Negative = net import
 */
function sqlInterconnector(ymd) {
  return `
    WITH gen AS (
      SELECT 
        settlementPeriod AS sp,
        AVG(generation) AS gen_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_indgen_iris\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
        AND boundary = 'N'
      GROUP BY sp
    ),
    dem AS (
      SELECT 
        settlementPeriod AS sp,
        ABS(AVG(demand)) AS demand_mw
      FROM \`${PROJECT}.${DATASET}.bmrs_inddem_iris\`
      WHERE DATE(settlementDate) = DATE('${ymd}')
        AND boundary = 'N'
      GROUP BY sp
    )
    SELECT 
      gen.sp,
      (gen.gen_mw - dem.demand_mw) AS ic_net_mw
    FROM gen
    INNER JOIN dem ON gen.sp = dem.sp
    ORDER BY sp
  `;
}

/************  REFRESH (TODAY)  ************/
function refreshDashboardToday() {
  ensureStructure();
  const ss = SpreadsheetApp.getActive();
  const cd = ss.getSheetByName('Chart Data');
  const ymd = todayDateStr_YYYY_MM_DD();
  const started = new Date();

  // Health check
  let healthMsg = '';
  try {
    const h = pingHealth();
    healthMsg = h.ok ? `✅ health OK` : `⚠️ health ${h.code}`;
  } catch (e) {
    healthMsg = `❌ health fail: ${e.message}`;
  }

  stampAudit('info', `Starting refresh for ${ymd} (${healthMsg})`);

  try {
    // Run all queries
    stampAudit('info', 'Querying system prices...');
    const qPrices = proxyGet(sqlSystemPrices(ymd));
    
    stampAudit('info', 'Querying generation/demand...');
    const qGenDem = proxyGet(sqlGenDemand(ymd));
    
    stampAudit('info', 'Querying BOALF...');
    const qBOALF = proxyGet(sqlBOALF(ymd));
    
    stampAudit('info', 'Querying BOD...');
    const qBOD = proxyGet(sqlBOD(ymd));
    
    stampAudit('info', 'Querying interconnector...');
    const qIC = proxyGet(sqlInterconnector(ymd));

    // Write raw data tabs
    writeQueryToSheet('Live_Raw_Prices', qPrices);
    writeQueryToSheet('Live_Raw_Gen', qGenDem);
    writeQueryToSheet('Live_Raw_BOA', qBOALF);
    writeQueryToSheet('Live_Raw_IC', qIC);

    // Index all data by settlement period
    const bySP = {};
    function indexData(query, mapping) {
      (query.data || []).forEach(row => {
        const sp = Number(row.sp || row.SP);
        if (!bySP[sp]) bySP[sp] = { sp: sp };
        Object.keys(mapping).forEach(key => {
          const val = row[key];
          bySP[sp][mapping[key]] = (val != null && val !== '') ? Number(val) : null;
        });
      });
    }

    indexData(qPrices, { ssp: 'ssp', sbp: 'sbp' });
    indexData(qGenDem, { gen_mw: 'gen_mw', demand_mw: 'demand_mw' });
    indexData(qBOALF, { boalf_count: 'boalf_count', boalf_avg_mw: 'boalf_avg_mw' });
    indexData(qBOD, { bod_offer: 'bod_offer', bod_bid: 'bod_bid' });
    indexData(qIC, { ic_net_mw: 'ic_net_mw' });

    // Build 48 rows for chart
    const rows = [];
    for (let sp = 1; sp <= 48; sp++) {
      const d = bySP[sp] || {};
      rows.push([
        sp,
        spToClock(sp),
        d.ssp ?? null,
        d.sbp ?? null,
        d.demand_mw ?? null,
        d.gen_mw ?? null,
        d.boalf_count ?? null,
        d.bod_offer ?? null,
        d.bod_bid ?? null,
        d.ic_net_mw ?? null
      ]);
    }

    // Write to Chart Data sheet
    cd.clear({ contentsOnly: true });
    cd.getRange(1, 1, 1, 10).setValues([[
      'SP', 'Time', 'SSP £/MWh', 'SBP £/MWh', 'Demand MW', 'Generation MW', 
      'BOALF Actions', 'BOD Offer £/MWh', 'BOD Bid £/MWh', 'IC Net MW'
    ]]);
    cd.getRange(2, 1, rows.length, rows[0].length).setValues(rows);

    // Reset named range to A2:J49 (header + 48 SPs)
    ss.setNamedRange('NR_DASH_TODAY', cd.getRange(2, 1, 48, 10));

    // Write to Live Dashboard (tidy format)
    const dash = ss.getSheetByName('Live Dashboard');
    dash.clear({ contentsOnly: true });
    dash.getRange(1, 1, 1, 10).setValues([[
      'SP', 'Time', 'SSP £/MWh', 'SBP £/MWh', 'Demand MW', 'Generation MW', 
      'BOALF Actions', 'BOD Offer £/MWh', 'BOD Bid £/MWh', 'IC Net MW'
    ]]);
    dash.getRange(2, 1, rows.length, rows[0].length).setValues(rows);

    const elapsed = (new Date() - started) / 1000;
    stampAudit('ok', `✅ Refresh complete for ${ymd} (${elapsed.toFixed(1)}s, ${rows.length} rows)`);
    
    SpreadsheetApp.getUi().alert(`✅ Dashboard refreshed!\n\nDate: ${ymd}\nRows: ${rows.length}\nTime: ${elapsed.toFixed(1)}s\n${healthMsg}`);
    
  } catch (e) {
    stampAudit('error', `❌ Refresh failed: ${e.message}`);
    SpreadsheetApp.getUi().alert(`❌ Error refreshing dashboard:\n\n${e.message}\n\nCheck Audit_Log for details.`);
    throw e;
  }
}

/************  HELPER: WRITE QUERY RESULTS TO SHEET  ************/
function writeQueryToSheet(sheetName, queryResult) {
  const ss = SpreadsheetApp.getActive();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) return;
  
  sheet.clear({ contentsOnly: true });
  
  if (!queryResult.data || queryResult.data.length === 0) {
    sheet.getRange(1, 1).setValue('No data');
    return;
  }
  
  // Headers from first row keys
  const headers = Object.keys(queryResult.data[0]);
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  
  // Data rows
  const rows = queryResult.data.map(row => headers.map(h => row[h] ?? ''));
  if (rows.length > 0) {
    sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  }
}

/************  CHART  ************/
function rebuildDashboardChart() {
  ensureStructure();
  const ss = SpreadsheetApp.getActive();
  const dash = ss.getSheetByName('Live Dashboard');
  
  // Remove existing charts
  dash.getCharts().forEach(c => dash.removeChart(c));

  const dataRange = ss.getRangeByName('NR_DASH_TODAY');
  if (!dataRange) {
    SpreadsheetApp.getUi().alert('❌ Named range NR_DASH_TODAY not found. Run refresh first.');
    return;
  }

  // Build combo chart with multiple series
  const chart = dash.newChart()
    .asComboChart()
    .addRange(dataRange)
    .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_ROWS)
    .setOption('title', 'GB Power Market - Live Dashboard (Today)')
    .setOption('width', 1200)
    .setOption('height', 600)
    .setOption('hAxis', { 
      title: 'Settlement Period (HH:MM)',
      slantedText: true,
      slantedTextAngle: 45
    })
    .setOption('vAxes', {
      0: { title: 'MW / £/MWh (Primary)', minValue: 0 },
      1: { title: '£/MWh (Secondary)', minValue: 0 }
    })
    .setOption('series', {
      0: { targetAxisIndex: 1, type: 'line', lineWidth: 2, color: '#FF6B6B' },  // SSP
      1: { targetAxisIndex: 1, type: 'line', lineWidth: 2, color: '#4ECDC4' },  // SBP
      2: { targetAxisIndex: 0, type: 'area', color: '#95E1D3', areaOpacity: 0.3 }, // Demand
      3: { targetAxisIndex: 0, type: 'area', color: '#F38181', areaOpacity: 0.3 }, // Generation
      4: { targetAxisIndex: 0, type: 'line', lineWidth: 1, color: '#AA96DA' },  // BOALF
      5: { targetAxisIndex: 1, type: 'line', lineWidth: 1, color: '#FCBAD3', lineDashStyle: [4, 4] }, // BOD Offer
      6: { targetAxisIndex: 1, type: 'line', lineWidth: 1, color: '#FFFFD2', lineDashStyle: [4, 4] }, // BOD Bid
      7: { targetAxisIndex: 0, type: 'line', lineWidth: 1, color: '#A8D8EA' }   // IC Net
    })
    .setOption('legend', { position: 'bottom', maxLines: 2 })
    .setOption('chartArea', { width: '80%', height: '70%' })
    .setPosition(1, 1, 0, 0)
    .build();

  dash.insertChart(chart);
  stampAudit('ok', '✅ Chart rebuilt');
  SpreadsheetApp.getUi().alert('✅ Chart rebuilt successfully!');
}

/************  TRIGGERS  ************/
function set5MinTrigger() {
  removeAllTimeTriggers();
  ScriptApp.newTrigger('refreshDashboardToday')
    .timeBased()
    .everyMinutes(5)
    .create();
  stampAudit('ok', '⏰ Set 5-min auto-refresh trigger');
  SpreadsheetApp.getUi().alert('✅ Auto-refresh enabled!\n\nDashboard will update every 5 minutes.\nUse "Stop Auto-Refresh" to disable.');
}

function removeAllTimeTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => ScriptApp.deleteTrigger(t));
  const count = triggers.length;
  stampAudit('ok', `🛑 Removed ${count} trigger(s)`);
  if (count > 0) {
    SpreadsheetApp.getUi().alert(`✅ Auto-refresh stopped!\n\nRemoved ${count} trigger(s).`);
  }
}

/************  AUDIT LOG  ************/
function stampAudit(status, msg) {
  try {
    const sh = SpreadsheetApp.getActive().getSheetByName('Audit_Log');
    if (!sh) return;
    
    if (sh.getLastRow() < 1) {
      sh.appendRow(['Timestamp', 'Status', 'Message', 'User']);
      sh.getRange(1, 1, 1, 4).setFontWeight('bold');
    }
    
    const user = Session.getActiveUser().getEmail() || Session.getEffectiveUser().getEmail() || 'unknown';
    sh.appendRow([new Date(), status, msg, user]);
    
    // Keep only last 1000 rows
    if (sh.getLastRow() > 1001) {
      sh.deleteRows(2, sh.getLastRow() - 1001);
    }
  } catch (e) {
    Logger.log('Audit log failed: ' + e);
  }
}

/************  ONE-CLICK SETUP  ************/
function Setup_Dashboard_AutoRefresh() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert(
    '🚀 One-Click Dashboard Setup',
    'This will:\n\n' +
    '1. Create all required sheets\n' +
    '2. Refresh today\'s data from BigQuery\n' +
    '3. Build the live chart\n' +
    '4. Enable 5-minute auto-refresh\n\n' +
    'Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response !== ui.Button.YES) {
    return;
  }
  
  try {
    stampAudit('info', '🚀 Starting one-click setup...');
    
    ensureStructure();
    refreshDashboardToday();
    rebuildDashboardChart();
    set5MinTrigger();
    
    ui.alert(
      '✅ Setup Complete!',
      'Your live dashboard is ready:\n\n' +
      '✅ All sheets created\n' +
      '✅ Data refreshed from BigQuery\n' +
      '✅ Chart built and linked\n' +
      '✅ Auto-refresh enabled (every 5 min)\n\n' +
      'Check the "Live Dashboard" tab!'
    );
    
  } catch (e) {
    ui.alert('❌ Setup failed:\n\n' + e.message + '\n\nCheck Audit_Log for details.');
    throw e;
  }
}

/************  TESTING  ************/
function testHealthCheck() {
  const h = pingHealth();
  Logger.log('Health check: ' + JSON.stringify(h));
  SpreadsheetApp.getUi().alert(`Health Check:\n\nStatus: ${h.code}\nOK: ${h.ok}\n\nResponse:\n${h.body.substring(0, 200)}`);
}

function testSingleQuery() {
  const ymd = todayDateStr_YYYY_MM_DD();
  const sql = sqlSystemPrices(ymd);
  Logger.log('SQL: ' + sql);
  
  try {
    const result = proxyGet(sql);
    Logger.log('Result: ' + JSON.stringify(result));
    SpreadsheetApp.getUi().alert(`✅ Query successful!\n\nRows: ${result.data.length}\n\nSample:\n${JSON.stringify(result.data[0], null, 2)}`);
  } catch (e) {
    SpreadsheetApp.getUi().alert(`❌ Query failed:\n\n${e.message}`);
  }
}
