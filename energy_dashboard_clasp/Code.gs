/**
 * GB Power Market Energy Dashboard - Main Code
 * Connects to Python backend for BESS optimization data
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Energy Tools')
    .addItem('🔁 Refresh Dashboard', 'refreshDashboard')
    .addItem('📊 Rebuild Charts', 'rebuildCharts')
    .addSeparator()
    .addSubMenu(ui.createMenu('💰 VLP Revenue')
      .addItem('📊 Create VLP Dashboard', 'createVlpRevenueSheet')
      .addItem('🔄 Refresh VLP Data', 'refreshVlpDashboard')
      .addItem('⚡ Update Live Ticker', 'updateLiveTicker')
      .addSeparator()
      .addItem('📈 Show Stacking Analysis', 'showStackingAnalysis')
      .addItem('🧩 Show Compatibility Matrix', 'showCompatibilityMatrix'))
    .addSeparator()
    .addItem('⏱ Enable Auto-Refresh', 'enableAutoRefresh')
    .addItem('❌ Disable Auto-Refresh', 'disableAutoRefresh')
    .addToUi();
}

function enableAutoRefresh() {
  disableAutoRefresh();
  
  // Main dashboard refresh every 5 minutes
  ScriptApp.newTrigger('refreshDashboard')
    .timeBased()
    .everyMinutes(5)
    .create();
  
  // VLP live ticker every 5 minutes
  ScriptApp.newTrigger('updateLiveTicker')
    .timeBased()
    .everyMinutes(5)
    .create();
  
  // Full VLP dashboard every 30 minutes
  ScriptApp.newTrigger('refreshVlpDashboard')
    .timeBased()
    .everyMinutes(30)
    .create();
  
  SpreadsheetApp.getUi().alert('✅ Auto-refresh enabled\n\n' +
    '• Dashboard: every 5 minutes\n' +
    '• VLP Ticker: every 5 minutes\n' +
    '• VLP Full: every 30 minutes');
}

function disableAutoRefresh() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (['refreshDashboard', 'updateLiveTicker', 'refreshVlpDashboard'].includes(t.getHandlerFunction())) {
      ScriptApp.deleteTrigger(t);
    }
  });
  
  SpreadsheetApp.getUi().alert('❌ Auto-refresh disabled');
}

/**
 * Execute BigQuery query and return results
 */
function runBigQuery(query) {
  const projectId = 'inner-cinema-476211-u9';
  
  try {
    const request = {
      query: query,
      useLegacySql: false,
      maxResults: 1000
    };
    
    const queryResults = BigQuery.Jobs.query(request, projectId);
    const jobId = queryResults.jobReference.jobId;
    
    // Wait for query to complete
    let sleepTimeMs = 500;
    while (!queryResults.jobComplete) {
      Utilities.sleep(sleepTimeMs);
      sleepTimeMs *= 2;
      queryResults = BigQuery.Jobs.getQueryResults(projectId, jobId);
    }
    
    // Get all rows of results
    let rows = queryResults.rows;
    while (queryResults.pageToken) {
      queryResults = BigQuery.Jobs.getQueryResults(projectId, jobId, {
        pageToken: queryResults.pageToken
      });
      rows = rows.concat(queryResults.rows);
    }
    
    if (!rows) {
      return [];
    }
    
    // Convert to array of objects
    const headers = queryResults.schema.fields.map(field => field.name);
    return rows.map(row => {
      const obj = {};
      row.f.forEach((cell, i) => {
        obj[headers[i]] = cell.v;
      });
      return obj;
    });
    
  } catch (e) {
    console.error('BigQuery error: ' + e.toString());
    throw new Error('BigQuery query failed: ' + e.toString());
  }
}

/**
 * Show stacking analysis dialog
 */
function showStackingAnalysis() {
  const scenarios = getStackingScenarios();
  let html = '<h2>VLP Revenue Stacking Analysis</h2>';
  
  scenarios.forEach(s => {
    html += `<h3>${s.scenario} (£${s.revenue_per_mwh.toFixed(2)}/MWh)</h3>`;
    html += `<p><strong>Services:</strong> ${s.services}</p>`;
    html += `<p><strong>Annual Revenue:</strong> £${s.annual_revenue.toLocaleString()}</p>`;
    html += `<p><strong>Risk Level:</strong> ${s.risk}</p>`;
    html += `<p><em>${s.description}</em></p><hr>`;
  });
  
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(500)
    .setHeight(600);
  
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, '💰 VLP Stacking Scenarios');
}

/**
 * Show compatibility matrix dialog
 */
function showCompatibilityMatrix() {
  const compat = getServiceCompatibility();
  let html = '<h2>🧩 Service Compatibility Matrix</h2>';
  html += '<table border="1" style="border-collapse: collapse; width: 100%;">';
  html += '<tr><th>Service 1</th><th>Service 2</th><th>Compatible?</th><th>Notes</th></tr>';
  
  compat.forEach(c => {
    const icon = c.compatible ? '✓' : '✗';
    const color = c.compatible ? '#c8e6c9' : '#ffcdd2';
    html += `<tr style="background-color: ${color};">`;
    html += `<td>${c.service1}</td>`;
    html += `<td>${c.service2}</td>`;
    html += `<td style="text-align: center; font-size: 18px;">${icon}</td>`;
    html += `<td>${c.note}</td>`;
    html += '</tr>';
  });
  
  html += '</table>';
  
  const htmlOutput = HtmlService.createHtmlOutput(html)
    .setWidth(600)
    .setHeight(500);
  
  SpreadsheetApp.getUi().showModalDialog(htmlOutput, '🧩 Service Compatibility');
}
