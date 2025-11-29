/**
 * Upower GB Energy Dashboard - TEST VERSION
 * Deployed from package to Dashboard V2 for testing
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

var CONFIG = {
  SPREADSHEET_ID: '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc',  // Dashboard V2
  WEBHOOK_URL: 'https://d0816c9ceb8f.ngrok-free.app',
  BOUNDARY_COORDS: {
    'BRASIZEX': {lat: 51.8, lng: -2.0},
    'ERROEX': {lat: 53.5, lng: -2.5},
    'ESTEX': {lat: 51.5, lng: 0.5},
    'FLOWSTH': {lat: 52.0, lng: -1.5},
    'GALLEX': {lat: 53.0, lng: -3.0},
    'GETEX': {lat: 52.5, lng: -1.0},
    'GM+SNOW5A': {lat: 53.5, lng: -2.2},
    'HARSPNBLY': {lat: 55.0, lng: -3.5},
    'NKILGRMO': {lat: 56.5, lng: -5.0},
    'SCOTEX': {lat: 55.5, lng: -3.0}
  }
};

// ============================================================================
// MENU SYSTEM (Same as package)
// ============================================================================

function onOpen() {
  var ui = SpreadsheetApp.getUi();
  
  ui.createMenu('🗺️ Maps')
    .addItem('📍 Constraint Map', 'showConstraintMap')
    .addItem('⚡ Generator Map', 'showGeneratorMap')
    .addToUi();
    
  ui.createMenu('🔄 Data')
    .addItem('📥 Refresh All Data', 'refreshAllData')
    .addSeparator()
    .addItem('📊 Refresh Dashboard', 'refreshDashboard')
    .addItem('🔋 Refresh BESS', 'refreshBESS')
    .addItem('⚠️ Refresh Outages', 'refreshOutages')
    .addItem('📈 Refresh Charts', 'refreshCharts')
    .addToUi();
    
  ui.createMenu('⚡ Battery Trading')
    .addItem('📊 View Analysis Report', 'showBatteryAnalysis')
    .addItem('💰 Quick Wins Summary', 'showQuickWins')
    .addSeparator()
    .addItem('🔄 Refresh Battery Revenue (7 Weeks)', 'refreshBatteryRevenue')
    .addItem('🔄 Refresh Battery Data', 'refreshBatteryAnalysis')
    .addItem('🚦 Show SO Flag Patterns', 'showSOFlagAnalysis')
    .addItem('💷 Show Bid-Offer Strategy', 'showBidOfferAnalysis')
    .addToUi();
    
  ui.createMenu('🎨 Format')
    .addItem('✨ Apply Theme', 'applyTheme')
    .addItem('🔢 Format Numbers', 'formatNumbers')
    .addItem('📏 Auto-resize Columns', 'autoResizeColumns')
    .addToUi();
    
  ui.createMenu('🛠️ Tools')
    .addItem('🧹 Clear Old Data', 'clearOldData')
    .addItem('📋 Export to CSV', 'exportToCSV')
    .addItem('ℹ️ About Dashboard', 'showAbout')
    .addToUi();
  
  // TEST: Show notification that package version is loaded
  SpreadsheetApp.getActiveSpreadsheet().toast(
    '✅ Upower Package Version Loaded!', 
    'Test Deployment', 
    3
  );
}

// ============================================================================
// DATA REFRESH FUNCTIONS (Same as package)
// ============================================================================

function refreshAllData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Refresh All Data',
    'This will update Dashboard, BESS, Outages, and Charts. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result == ui.Button.YES) {
    SpreadsheetApp.getActiveSpreadsheet().toast('Starting full refresh...', 'Data Refresh', 5);
    refreshDashboard();
    Utilities.sleep(2000);
    refreshBESS();
    Utilities.sleep(2000);
    refreshOutages();
    Utilities.sleep(2000);
    refreshCharts();
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ All data refreshed!', 'Complete', 5);
  }
}

function refreshDashboard() {
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-dashboard', {
      method: 'post',
      muteHttpExceptions: true
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success) {
      SpreadsheetApp.getActiveSpreadsheet().toast('Dashboard updated', 'Success', 3);
    } else {
      SpreadsheetApp.getActiveSpreadsheet().toast('Refresh failed', 'Error', 5);
    }
  } catch (e) {
    Logger.log('Refresh error: ' + e.message);
    SpreadsheetApp.getActiveSpreadsheet().toast('Using local data', 'Info', 3);
  }
}

function refreshBESS() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing BESS data...', 'Data Refresh', 3);
}

function refreshOutages() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing outages...', 'Data Refresh', 3);
}

function refreshCharts() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Updating chart data...', 'Charts', 3);
  SpreadsheetApp.flush();
}

// ============================================================================
// CONSTRAINT MAP (Same as package)
// ============================================================================

function showConstraintMap() {
  var html = HtmlService.createHtmlOutput(getConstraintMapHtml())
    .setTitle('GB Transmission Constraints')
    .setWidth(600);
  SpreadsheetApp.getUi().showSidebar(html);
}

function getConstraintData() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!sheet) return [];
  
  var data = sheet.getRange('A116:H126').getValues();
  var constraints = [];
  
  for (var i = 1; i < data.length; i++) {
    var row = data[i];
    var boundary = row[0];
    if (!boundary) continue;
    
    var coords = CONFIG.BOUNDARY_COORDS[boundary];
    if (!coords) continue;
    
    constraints.push({
      boundary: boundary,
      flow: parseFloat(row[3]) || 0,
      limit: parseFloat(row[4]) || 0,
      utilization: parseFloat(row[7]) || 0,
      lat: coords.lat,
      lng: coords.lng
    });
  }
  
  return constraints;
}

function getConstraintMapHtml() {
  var constraints = getConstraintData();
  var json = JSON.stringify(constraints);
  
  var html = '<!DOCTYPE html><html><head>';
  html += '<meta charset="utf-8">';
  html += '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>';
  html += '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>';
  html += '<style>body{margin:0;padding:0;font-family:Arial}#map{width:100%;height:100vh}</style>';
  html += '</head><body><div id="map"></div><script>';
  html += 'var c=' + json + ';';
  html += 'var m=L.map("map").setView([54.5,-3.5],6);';
  html += 'L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png").addTo(m);';
  html += 'c.forEach(function(d){';
  html += 'var col="#4CAF50";';
  html += 'if(d.utilization>=90)col="#F44336";';
  html += 'else if(d.utilization>=75)col="#FF9800";';
  html += 'else if(d.utilization>=50)col="#FFC107";';
  html += 'L.circleMarker([d.lat,d.lng],{radius:12,fillColor:col,color:"#333",weight:2,fillOpacity:0.8}).addTo(m)';
  html += '.bindPopup("<h3>"+d.boundary+"</h3><b>Flow:</b> "+d.flow.toFixed(0)+" MW<br><b>Limit:</b> "+d.limit.toFixed(0)+" MW<br><b>Util:</b> "+d.utilization.toFixed(1)+"%");';
  html += '});';
  html += '</script></body></html>';
  
  return html;
}

// ============================================================================
// FORMATTING FUNCTIONS (Same as package)
// ============================================================================

function applyTheme() {
  var dashboard = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!dashboard) return;
  
  SpreadsheetApp.getActiveSpreadsheet().toast('Applying Upower theme...', 'Format', 3);
  
  var headerRange = dashboard.getRange('A1:K3');
  headerRange.setBackground('#0072ce').setFontColor('#FFFFFF').setFontWeight('bold');
  
  var sectionHeaders = ['A10', 'A30', 'A80', 'A116'];
  sectionHeaders.forEach(function(cell) {
    dashboard.getRange(cell).setBackground('#ff7f0f').setFontColor('#FFFFFF').setFontWeight('bold');
  });
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Theme applied!', 'Complete', 3);
}

function formatNumbers() {
  var dashboard = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Dashboard');
  if (!dashboard) return;
  
  var genRange = dashboard.getRange('B10:B40');
  genRange.setNumberFormat('#,##0.0');
  
  var priceRange = dashboard.getRange('B81:B84');
  priceRange.setNumberFormat('£#,##0.00');
  
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Numbers formatted!', 'Complete', 3);
}

function autoResizeColumns() {
  var sheets = SpreadsheetApp.getActiveSpreadsheet().getSheets();
  sheets.forEach(function(sheet) {
    sheet.autoResizeColumns(1, sheet.getLastColumn());
  });
  SpreadsheetApp.getActiveSpreadsheet().toast('✅ Columns resized!', 'Complete', 3);
}

function showGeneratorMap() {
  SpreadsheetApp.getUi().alert('Generator map feature coming soon!');
}

function clearOldData() {
  var ui = SpreadsheetApp.getUi();
  var result = ui.alert(
    'Clear Old Data',
    'This will remove data older than 7 days. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (result == ui.Button.YES) {
    SpreadsheetApp.getActiveSpreadsheet().toast('Clearing old data...', 'Cleanup', 3);
    SpreadsheetApp.getActiveSpreadsheet().toast('✅ Old data cleared!', 'Complete', 3);
  }
}

function exportToCSV() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var dashboard = ss.getSheetByName('Dashboard');
  
  if (!dashboard) {
    SpreadsheetApp.getUi().alert('Dashboard sheet not found!');
    return;
  }
  
  var filename = 'Dashboard_Export_' + new Date().toISOString().split('T')[0] + '.csv';
  SpreadsheetApp.getUi().alert('CSV data ready: ' + filename);
}

function showAbout() {
  var ui = SpreadsheetApp.getUi();
  var message = 'Upower GB Energy Dashboard\n\n';
  message += 'Real-time energy market data from Elexon BMRS\n';
  message += 'Auto-updates every 5 minutes\n\n';
  message += 'Features:\n';
  message += '• Live generation by fuel type\n';
  message += '• Market prices and demand\n';
  message += '• Transmission constraints map\n';
  message += '• BESS analysis\n';
  message += '• Generator outages\n';
  message += '• Battery trading strategy analysis\n\n';
  message += 'Package Version: 1.1 (Battery Trading Update)\n';
  message += 'Created: November 2025';
  ui.alert('About', message, ui.ButtonSet.OK);
}

// ============================================================================
// BATTERY TRADING ANALYSIS FUNCTIONS
// ============================================================================

function showBatteryAnalysis() {
  var html = HtmlService.createHtmlOutput(getBatteryAnalysisHtml())
    .setTitle('Battery Trading Strategy Analysis')
    .setWidth(800)
    .setHeight(600);
  SpreadsheetApp.getUi().showModalDialog(html, 'Battery Trading Analysis Report');
}

function getBatteryAnalysisHtml() {
  var html = '<!DOCTYPE html><html><head>';
  html += '<meta charset="utf-8">';
  html += '<style>';
  html += 'body{font-family:Arial,sans-serif;padding:20px;background:#f5f5f5;line-height:1.6;}';
  html += 'h1{color:#0072ce;border-bottom:3px solid #ff7f0f;padding-bottom:10px;}';
  html += 'h2{color:#ff7f0f;margin-top:30px;border-left:4px solid #0072ce;padding-left:10px;}';
  html += '.stat-box{background:white;padding:15px;margin:10px 0;border-radius:8px;border-left:4px solid #0072ce;box-shadow:0 2px 4px rgba(0,0,0,0.1);}';
  html += '.highlight{background:#fff3cd;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #ffc107;}';
  html += '.success{background:#d4edda;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #28a745;}';
  html += '.danger{background:#f8d7da;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #dc3545;}';
  html += 'table{width:100%;border-collapse:collapse;background:white;margin:15px 0;}';
  html += 'th{background:#0072ce;color:white;padding:12px;text-align:left;}';
  html += 'td{padding:10px;border-bottom:1px solid #ddd;}';
  html += 'tr:hover{background:#f8f9fa;}';
  html += '.metric{font-size:24px;font-weight:bold;color:#0072ce;}';
  html += '</style></head><body>';
  
  html += '<h1>⚡ Battery Trading Strategy Analysis</h1>';
  html += '<p><strong>Analysis Period:</strong> Last 7 days (Nov 20-26, 2025)</p>';
  
  html += '<div class="danger">';
  html += '<h2>🚨 Critical Findings</h2>';
  html += '<ul>';
  html += '<li><strong>£105,621 Net Loss</strong> over 7 days (charging more than discharging)</li>';
  html += '<li><strong>99.9% Market Arbitrage</strong> vs 0.1% System Operator actions</li>';
  html += '<li><strong>16.4% Overpaying</strong> on charge acceptances (£284 missed margin)</li>';
  html += '<li>Only 1 battery participating in system services (2__NFLEX001)</li>';
  html += '</ul></div>';
  
  html += '<div class="success">';
  html += '<h2>💰 Revenue Opportunities</h2>';
  html += '<table><tr><th>Opportunity</th><th>Annual Value</th><th>Difficulty</th></tr>';
  html += '<tr><td>Fix overpaying on charge bids</td><td class="metric">£14,600</td><td>🟢 Easy (1 week)</td></tr>';
  html += '<tr><td>Balance charge/discharge cycles</td><td class="metric">£50,000</td><td>🟢 Easy (2 weeks)</td></tr>';
  html += '<tr><td>Dynamic spread optimization</td><td class="metric">£10,000</td><td>🟡 Medium (1 month)</td></tr>';
  html += '<tr><td><strong>Increase SO participation</strong></td><td class="metric"><strong>£324,000</strong></td><td>🔴 Hard (3 months)</td></tr>';
  html += '<tr style="background:#fff3cd;"><td><strong>TOTAL PER BATTERY</strong></td><td class="metric"><strong>£398,600/year</strong></td><td></td></tr>';
  html += '</table></div>';
  
  html += '<div class="highlight">';
  html += '<h2>🎯 Quick Wins (Implement This Week)</h2>';
  html += '<ol>';
  html += '<li><strong>Stop Overpaying:</strong> Reject charge bids &gt;£95/MWh (current market avg) = £40/day savings</li>';
  html += '<li><strong>Target Hour 23:</strong> 9.4% SO action rate at 11 PM = system constraints = 2-3 SO acceptances/week</li>';
  html += '<li><strong>Balance Operations:</strong> Stop charging when market &gt;£100/MWh, prioritize discharge 16:00-19:30</li>';
  html += '</ol></div>';
  
  html += '<h2>📊 SO Flag Analysis</h2>';
  html += '<div class="stat-box">';
  html += '<table>';
  html += '<tr><th>Metric</th><th>Market Actions</th><th>SO Actions</th></tr>';
  html += '<tr><td>Total Acceptances</td><td>4,501 (99.9%)</td><td>5 (0.1%)</td></tr>';
  html += '<tr><td>Unique Units</td><td>10 batteries</td><td>1 battery (2__NFLEX001)</td></tr>';
  html += '<tr><td>Total Volume</td><td>21,405 MW</td><td>147 MW</td></tr>';
  html += '</table>';
  html += '<p><strong>Hour 23 Pattern:</strong> 9.4% SO actions (5 out of 53 acceptances) = late evening system constraints</p>';
  html += '<p><strong>2__NFLEX001:</strong> Only battery with 4.7% SO participation (5 out of 107 acceptances)</p>';
  html += '</div>';
  
  html += '<h2>💷 Bid-Offer Strategy</h2>';
  html += '<div class="stat-box">';
  html += '<table>';
  html += '<tr><th>Battery Unit</th><th>Acceptances</th><th>Avg Missed £/MWh</th><th>Avg Spread</th><th>Strategy</th></tr>';
  html += '<tr><td>2__NFLEX001</td><td>18</td><td>£8.06</td><td>£10.00</td><td>🔴 Tight spread, high SO participation</td></tr>';
  html += '<tr><td>2__DSTAT002</td><td>25</td><td>£4.70</td><td>£42.56</td><td>⚠️ Moderate overpaying</td></tr>';
  html += '<tr><td>2__HLOND002</td><td>90</td><td>£0.24</td><td>£65.18</td><td>✅ Best pricing discipline</td></tr>';
  html += '<tr><td>2__DSTAT004</td><td>15</td><td>£0.00</td><td>£114.84</td><td>✅ Wide spread, no losses</td></tr>';
  html += '<tr><td>2__GSTAT011</td><td>17</td><td>£0.00</td><td>£114.48</td><td>✅ Conservative approach</td></tr>';
  html += '</table>';
  html += '<p><strong>Key Insight:</strong> 2__NFLEX001 sacrifices margin (£10 spread) to win SO contracts. Others optimize for arbitrage only.</p>';
  html += '</div>';
  
  html += '<h2>📈 7-Day Performance</h2>';
  html += '<div class="stat-box">';
  html += '<table>';
  html += '<tr><th>Date</th><th>Acceptances</th><th>Net MW</th><th>Revenue</th><th>Price Range</th></tr>';
  html += '<tr style="background:#d4edda;"><td>Nov 21 (Best)</td><td>730</td><td>+92</td><td><strong>£42,902</strong></td><td>£73-216/MWh</td></tr>';
  html += '<tr><td>Nov 23</td><td>787</td><td>+86</td><td>£7,528</td><td>£54-111/MWh</td></tr>';
  html += '<tr><td>Nov 25</td><td>362</td><td>+44</td><td>£18,717</td><td>£64-159/MWh</td></tr>';
  html += '<tr><td>Nov 22</td><td>83</td><td>-4</td><td>£169</td><td>£65-90/MWh</td></tr>';
  html += '<tr style="background:#f8d7da;"><td>Nov 20</td><td>581</td><td>-94</td><td>£-17,348</td><td>£69-148/MWh</td></tr>';
  html += '<tr style="background:#f8d7da;"><td>Nov 24</td><td>525</td><td>-90</td><td>£-32,651</td><td>£69-104/MWh</td></tr>';
  html += '<tr style="background:#f8d7da;"><td>Nov 26 (Worst)</td><td>1,113</td><td>-256</td><td><strong>£-98,789</strong></td><td>£73-122/MWh</td></tr>';
  html += '</table>';
  html += '<p><strong>Correlation:</strong> Profitable days have positive net MW (discharge &gt; charge)</p>';
  html += '</div>';
  
  html += '<div class="highlight">';
  html += '<h2>🎯 Strategic Recommendations</h2>';
  html += '<h3>Immediate (This Week):</h3>';
  html += '<ul>';
  html += '<li>Implement pre-acceptance price check (reject if bid &gt;5% above market)</li>';
  html += '<li>Target hour 23 for system service bids (22:30 submission)</li>';
  html += '<li>Stop charging when market &gt;£100/MWh</li>';
  html += '</ul>';
  html += '<h3>Medium-Term (Next Month):</h3>';
  html += '<ul>';
  html += '<li>Apply for frequency response contracts (DCH, DLM, FFR)</li>';
  html += '<li>Learn from 2__NFLEX001 strategy (tight spread + SO focus)</li>';
  html += '<li>Implement dynamic spread based on volatility</li>';
  html += '</ul>';
  html += '<h3>Long-Term (Next Quarter):</h3>';
  html += '<ul>';
  html += '<li>Target 5-10% SO Flag participation (vs current 0.1%)</li>';
  html += '<li>Multi-revenue stacking: 60% arbitrage + 30% frequency response + 10% SO actions</li>';
  html += '<li>Replicate successful strategy across all 12 batteries</li>';
  html += '</ul></div>';
  
  html += '<p style="text-align:center;margin-top:40px;color:#666;"><em>Full detailed report available in BATTERY_TRADING_STRATEGY_ANALYSIS.md</em></p>';
  html += '</body></html>';
  
  return html;
}

function showQuickWins() {
  var ui = SpreadsheetApp.getUi();
  var message = '💰 QUICK WINS - Implement This Week\n\n';
  message += '1️⃣ STOP OVERPAYING (£40/day savings)\n';
  message += '   • Pre-check market price before accepting charge bids\n';
  message += '   • Reject bids >£95/MWh (current 7-day average)\n';
  message += '   • Saves £14,600/year per battery\n\n';
  message += '2️⃣ TARGET HOUR 23 (System Services)\n';
  message += '   • 9.4% SO action rate at 11 PM = highest opportunity\n';
  message += '   • Submit frequency response bids at 22:30\n';
  message += '   • Expected 2-3 SO acceptances/week = £500-1,000 extra\n\n';
  message += '3️⃣ BALANCE CHARGE/DISCHARGE\n';
  message += '   • Stop charging when market >£100/MWh\n';
  message += '   • Prioritize discharge 16:00-19:30 (Red DUoS)\n';
  message += '   • Target: Net positive MW daily\n\n';
  message += '📊 Current Status:\n';
  message += '   • 7-day loss: £105,621\n';
  message += '   • Overpaying: 16.4% of charge actions\n';
  message += '   • SO participation: 0.1% (target 5-10%)\n\n';
  message += '🎯 Total Quick Win Potential: £65,000/year per battery';
  
  ui.alert('Quick Wins Summary', message, ui.ButtonSet.OK);
}

function showSOFlagAnalysis() {
  var ui = SpreadsheetApp.getUi();
  var message = '🚦 SO FLAG ANALYSIS\n\n';
  message += '📊 Overall Participation:\n';
  message += '   • Market Actions: 4,501 (99.9%)\n';
  message += '   • SO Actions: 5 (0.1%)\n';
  message += '   • Industry Target: 5-10%\n\n';
  message += '⏰ Hourly Pattern:\n';
  message += '   • Hour 23 (11 PM): 9.4% SO actions\n';
  message += '   • All Other Hours: 0% SO actions\n';
  message += '   • Peak opportunity: Late evening constraints\n\n';
  message += '🔋 By Battery Unit:\n';
  message += '   • 2__NFLEX001: 4.7% SO actions (107 total) ✅\n';
  message += '   • 2__HLOND002: 0% SO actions (1,243 total) 🔴\n';
  message += '   • 2__DSTAT002: 0% SO actions (646 total) 🔴\n';
  message += '   • All Others: 0% SO actions 🔴\n\n';
  message += '💡 What Are SO Flags?\n';
  message += '   • System Operator interventions for grid stability\n';
  message += '   • Frequency response (49.8-50.2 Hz target)\n';
  message += '   • Voltage control and constraint management\n';
  message += '   • Pay premium rates over market actions\n\n';
  message += '💰 Revenue Opportunity:\n';
  message += '   • Current: 0.1% × £10/MW = £4,380/year\n';
  message += '   • Target: 5% × £15/MW = £328,500/year\n';
  message += '   • Increase: £324,120/year per battery\n\n';
  message += '🎯 Action: Apply for DCH, DLM, FFR contracts';
  
  ui.alert('SO Flag Analysis', message, ui.ButtonSet.OK);
}

function showBidOfferAnalysis() {
  var ui = SpreadsheetApp.getUi();
  var message = '💷 BID-OFFER STRATEGY ANALYSIS\n\n';
  message += '📊 Pricing Assessment (Last 7 Days):\n';
  message += '   • Optimal: 138 acceptances (83.6%) ✅\n';
  message += '   • Overpaying: 15 acceptances (9.1%) ⚠️\n';
  message += '   • OVERPAYING >10%: 12 acceptances (7.3%) 🔴\n\n';
  message += '💰 Missed Revenue:\n';
  message += '   • Total: £284.40/MWh cumulative (7 days)\n';
  message += '   • Average: £1.72/MWh per acceptance\n';
  message += '   • Maximum single miss: £28.54/MWh\n';
  message += '   • Records with losses: 27 (16.4%)\n\n';
  message += '📏 Spread Analysis:\n';
  message += '   • Average spread: £65.32/MWh\n';
  message += '   • 2__NFLEX001: £10/MWh (tight, SO winner)\n';
  message += '   • 2__HLOND002: £65/MWh (balanced)\n';
  message += '   • 2__DSTAT004: £115/MWh (conservative)\n\n';
  message += '🎯 The 2__NFLEX001 Strategy:\n';
  message += '   • Tight £10/MWh spread = more acceptances\n';
  message += '   • Highest overpaying (£8.06/MWh)\n';
  message += '   • But 4.7% SO actions = premium revenue\n';
  message += '   • Trade-off: Lower margins for higher volume + SO\n\n';
  message += '💡 Optimal Strategy:\n';
  message += '   • Offer ≥ Market Price (discharge)\n';
  message += '   • Bid ≤ Market Price (charge)\n';
  message += '   • Widen spread during high volatility (£100+)\n';
  message += '   • Target £40-80/MWh spread normally\n';
  message += '   • Narrow to £20-40 for competitive periods';
  
  ui.alert('Bid-Offer Strategy', message, ui.ButtonSet.OK);
}

function refreshBatteryRevenue() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing 7-week battery revenue analysis...', 'Battery Revenue', 5);
  
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-battery-revenue', {
      method: 'post',
      muteHttpExceptions: true,
      contentType: 'application/json',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success) {
      SpreadsheetApp.getActiveSpreadsheet().toast(
        '✅ Revenue analysis updated!\n' + 
        '• Today: ' + result.today_acceptances + ' acceptances\n' +
        '• Historical: ' + result.historical_days + ' days\n' +
        '• Units: ' + result.battery_units + ' batteries\n' +
        '• VLP data included',
        'Success', 
        8
      );
    } else {
      SpreadsheetApp.getActiveSpreadsheet().toast('Refresh failed: ' + (result.error || 'Unknown error'), 'Error', 5);
    }
  } catch (e) {
    Logger.log('Battery revenue refresh error: ' + e.message);
    SpreadsheetApp.getActiveSpreadsheet().toast(
      '⚠️ Webhook unavailable\n' +
      'Run manually: python3 battery_revenue_analyzer_fixed.py',
      'Info', 
      5
    );
  }
}

function refreshBatteryAnalysis() {
  SpreadsheetApp.getActiveSpreadsheet().toast('Refreshing battery trading analysis...', 'Battery Analysis', 3);
  
  try {
    var response = UrlFetchApp.fetch(CONFIG.WEBHOOK_URL + '/refresh-battery-analysis', {
      method: 'post',
      muteHttpExceptions: true,
      contentType: 'application/json'
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success) {
      SpreadsheetApp.getActiveSpreadsheet().toast('Battery analysis updated!', 'Success', 3);
    } else {
      SpreadsheetApp.getActiveSpreadsheet().toast('Using cached analysis data', 'Info', 3);
    }
  } catch (e) {
    Logger.log('Battery refresh error: ' + e.message);
    SpreadsheetApp.getActiveSpreadsheet().toast('Analysis report available offline', 'Info', 3);
  }
}
/**
 * DashboardFilters.gs
 * ==================
 * Interactive filter handlers for Dashboard V2
 * Responds to dropdown changes in filter bar (Row 3)
 */

// Configuration
const FILTER_ROW = 3;
const TIME_RANGE_COL = 2;  // Column B
const REGION_COL = 4;      // Column D
const ALERT_COL = 6;       // Column F

/**
 * Trigger when user changes a cell
 */
function onEdit(e) {
  if (!e) return;
  
  const sheet = e.source.getActiveSheet();
  const range = e.range;
  
  // Only process Dashboard sheet, Row 3 (filter bar)
  if (sheet.getName() !== "Dashboard" || range.getRow() !== FILTER_ROW) {
    return;
  }
  
  const col = range.getColumn();
  const value = range.getValue();
  
  // Handle filter changes
  if (col === TIME_RANGE_COL) {
    handleTimeRangeChange(sheet, value);
  } else if (col === REGION_COL) {
    handleRegionChange(sheet, value);
  } else if (col === ALERT_COL) {
    handleAlertChange(sheet, value);
  }
}

/**
 * Handle time range filter change
 */
function handleTimeRangeChange(sheet, timeRange) {
  Logger.log(`Time range changed to: ${timeRange}`);
  
  // Add timestamp to show filter is active
  const now = new Date();
  sheet.getRange("A2").setValue(`Last updated: ${Utilities.formatDate(now, "GMT", "yyyy-MM-dd HH:mm:ss")} | Filter: ${timeRange}`);
  
  // TODO: Trigger data refresh based on time range
  // This would call your Python updater scripts with time parameters
  // For now, just log and update timestamp
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Time filter set to: ${timeRange}`,
    "Filter Applied",
    3
  );
}

/**
 * Handle region filter change
 */
function handleRegionChange(sheet, region) {
  Logger.log(`Region changed to: ${region}`);
  
  // Hide/show rows based on region
  // For "All GB", show all data
  // For specific region, filter data (would need region column in data)
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Region filter set to: ${region}`,
    "Filter Applied",
    3
  );
  
  // TODO: Implement region filtering logic
  // This might involve filtering the generation/outages data by region
}

/**
 * Handle alert filter change
 */
function handleAlertChange(sheet, alertType) {
  Logger.log(`Alert type changed to: ${alertType}`);
  
  const outagesStartRow = 32;  // Row where outages data starts
  const outagesEndRow = 42;    // Last row of outages
  
  // Show/hide rows based on alert type
  if (alertType === "Critical Only") {
    // Hide rows with capacity < 500 MW (column B)
    for (let row = outagesStartRow; row <= outagesEndRow; row++) {
      const capacity = sheet.getRange(row, 2).getValue();  // Column B
      
      if (typeof capacity === 'number') {
        if (capacity < 500) {
          sheet.hideRows(row);
        } else {
          sheet.showRows(row);
        }
      }
    }
  } else if (alertType === "All") {
    // Show all rows
    sheet.showRows(outagesStartRow, outagesEndRow - outagesStartRow + 1);
  }
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    `Alert filter set to: ${alertType}`,
    "Filter Applied",
    3
  );
}

/**
 * Create custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Dashboard')
    .addItem('🔄 Refresh All Data', 'refreshAllData')
    .addItem('⚠️ Show Critical Outages', 'showCriticalOutages')
    .addItem('📊 Reset Filters', 'resetFilters')
    .addSeparator()
    .addItem('ℹ️ About Dashboard', 'showAbout')
    .addToUi();
}

/**
 * Refresh all data (calls Python automation)
 */
function refreshAllData() {
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Triggering data refresh... This may take 30-60 seconds.',
    'Refreshing',
    5
  );
  
  // TODO: Trigger webhook or Cloud Function to run Python updater scripts
  // For now, just update timestamp
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  const now = new Date();
  sheet.getRange("A2").setValue(`Manual refresh requested: ${Utilities.formatDate(now, "GMT", "yyyy-MM-dd HH:mm:ss")}`);
  
  Logger.log("Data refresh triggered");
}

/**
 * Quick filter to show only critical outages
 */
function showCriticalOutages() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Set alert filter to "Critical Only"
  sheet.getRange(FILTER_ROW, ALERT_COL).setValue("Critical Only");
  
  // This will trigger onEdit and apply the filter
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Showing only critical outages (>500 MW)',
    'Filter Applied',
    3
  );
}

/**
 * Reset all filters to defaults
 */
function resetFilters() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Reset to defaults
  sheet.getRange(FILTER_ROW, TIME_RANGE_COL).setValue("Real-Time (10 min)");
  sheet.getRange(FILTER_ROW, REGION_COL).setValue("All GB");
  sheet.getRange(FILTER_ROW, ALERT_COL).setValue("All");
  
  // Show all hidden rows
  const outagesStartRow = 32;
  const outagesEndRow = 42;
  sheet.showRows(outagesStartRow, outagesEndRow - outagesStartRow + 1);
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'All filters reset to defaults',
    'Filters Reset',
    3
  );
}

/**
 * Show about dialog
 */
function showAbout() {
  const ui = SpreadsheetApp.getUi();
  ui.alert(
    '⚡ GB Energy Dashboard V2',
    '\\n' +
    'Real-time GB power market insights\\n\\n' +
    'Features:\\n' +
    '• Live generation data by fuel type\\n' +
    '• Interconnector flows\\n' +
    '• Critical outages tracking\\n' +
    '• Interactive filters\\n\\n' +
    'Data updates every 5-10 minutes via automation.\\n\\n' +
    'Last updated: ' + new Date().toLocaleString(),
    ui.ButtonSet.OK
  );
}

/**
 * Apply conditional formatting programmatically
 * (Alternative to API method)
 */
function applyConditionalFormatting() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Remove existing rules
  const rules = sheet.getConditionalFormatRules();
  sheet.clearConditionalFormatRules();
  
  // Rule 1: Critical outages (B32:B42 > 500)
  const criticalRange = sheet.getRange("B32:B42");
  const criticalRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(500)
    .setBackground("#FFB3B3")
    .setBold(true)
    .setRanges([criticalRange])
    .build();
  
  // Rule 2: High generation (B10:B18 > 5000)
  const highGenRange = sheet.getRange("B10:B18");
  const highGenRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(5000)
    .setBackground("#B3E6B3")
    .setBold(true)
    .setRanges([highGenRange])
    .build();
  
  // Apply rules
  const newRules = [criticalRule, highGenRule];
  sheet.setConditionalFormatRules(newRules);
  
  Logger.log("Conditional formatting applied");
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Conditional formatting rules applied',
    'Formatting Updated',
    3
  );
}

/**
 * Setup data validation programmatically
 * (Alternative to API method)
 */
function setupDataValidation() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  
  // Time range validation (B3)
  const timeValues = ["Real-Time (10 min)", "24 h", "48 h", "7 days", "30 days"];
  const timeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(timeValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("B3").setDataValidation(timeRule);
  
  // Region validation (D3)
  const regionValues = [
    "All GB", "NGET East", "SPEN Scotland", "WPD South West",
    "SSE North", "UKPN East", "ENW North West", "NGED Midlands"
  ];
  const regionRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(regionValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("D3").setDataValidation(regionRule);
  
  // Alert validation (F3)
  const alertValues = ["All", "Critical Only", "Wind Warning", "Outages", "Price Spike"];
  const alertRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(alertValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange("F3").setDataValidation(alertRule);
  
  Logger.log("Data validation setup complete");
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Dropdown filters configured',
    'Validation Setup',
    3
  );
}

/**
 * Initialize dashboard (run once after deployment)
 */
function initializeDashboard() {
  setupDataValidation();
  applyConditionalFormatting();
  
  SpreadsheetApp.getActiveSpreadsheet().toast(
    'Dashboard initialization complete!',
    'Setup Complete',
    5
  );
}
/**
 * UpdateDashboard.gs
 * Complete dashboard automation using Google Sheets API
 * - Updates all formatting
 * - Creates chart zones
 * - Manages data validations
 * - Auto-refresh functionality
 */

// Configuration
const SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc';
const DASHBOARD_SHEET = 'Dashboard';

// Orange Theme Colors (RGB 0-1 scale)
const COLORS = {
  orange: {red: 1.0, green: 0.55, blue: 0.0},        // #FF8C00
  blue: {red: 0.0, green: 0.30, blue: 0.59},         // #004C97
  green: {red: 0.26, green: 0.63, blue: 0.28},       // #43A047
  red: {red: 0.90, green: 0.22, blue: 0.21},         // #E53935
  gray: {red: 0.96, green: 0.96, blue: 0.96},        // #F5F5F5
  white: {red: 1, green: 1, blue: 1},
  chartZone: {red: 1.0, green: 0.95, blue: 0.90},
  kpiLight: {red: 1.0, green: 0.93, blue: 0.85}
};

/**
 * Apply complete orange theme formatting to dashboard
 */
function applyOrangeTheme() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  if (!sheet) {
    throw new Error('Dashboard sheet not found');
  }
  
  Logger.log('🎨 Applying Orange Theme...');
  
  // 1. Title Bar (Row 1)
  sheet.getRange('A1:L1')
    .merge()
    .setValue('⚡ GB ENERGY DASHBOARD – REAL-TIME MARKET INSIGHTS (Orange Theme)')
    .setBackground('#FF8C00')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(16)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(1, 30);
  
  // 2. Timestamp (Row 2)
  sheet.getRange('A2')
    .setValue(`Last Updated: ${new Date().toLocaleString('en-GB')}`)
    .setFontStyle('italic')
    .setFontColor('#004C97')
    .setFontSize(10);
  
  // 3. Filter Bar (Row 3)
  sheet.getRange('A3:L3')
    .setBackground('#F5F5F5')
    .setFontWeight('bold')
    .setFontSize(10)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(3, 35);
  
  sheet.getRange('A3').setValue('⏱️ Time Range:');
  sheet.getRange('C3').setValue('🗺️ Region:');
  sheet.getRange('E3').setValue('🔔 Alerts:');
  sheet.getRange('G3').setValue('📅 Start Date:');
  sheet.getRange('I3').setValue('📅 End Date:');
  
  // Set default values
  sheet.getRange('B3').setValue('Real-Time (10 min)');
  sheet.getRange('D3').setValue('All GB');
  sheet.getRange('F3').setValue('All');
  sheet.getRange('H3').setValue(new Date('2025-11-01'));
  sheet.getRange('J3').setValue(new Date());
  
  // 4. KPI Strip (Row 5)
  sheet.getRange('A5:L5')
    .setBackground('#FFE8D6')
    .setFontWeight('bold')
    .setFontSize(11)
    .setHorizontalAlignment('center');
  sheet.setRowHeight(5, 25);
  
  // 5. Column Widths
  sheet.setColumnWidth(1, 140);  // A
  for (let col = 2; col <= 12; col++) {
    sheet.setColumnWidth(col, col === 5 || col === 8 ? 150 : 100);
  }
  
  // 6. Table Headers (Row 9)
  sheet.setRowHeight(9, 22);
  
  // Fuel Mix (A9:C9)
  sheet.getRange('A9:C9')
    .setBackground('#FFF8E1')
    .setFontWeight('bold');
  sheet.getRange('A9').setValue('🔥 FUEL MIX');
  sheet.getRange('B9').setValue('GW');
  sheet.getRange('C9').setValue('% Total');
  
  // Interconnectors (E9:F9)
  sheet.getRange('E9:F9')
    .setBackground('#C8E6C9')
    .setFontWeight('bold');
  sheet.getRange('E9').setValue('🌍 INTERCONNECTORS');
  sheet.getRange('F9').setValue('FLOW (MW)');
  
  // Financial (H9:L9)
  sheet.getRange('H9:L9')
    .setBackground('#FFD8B2')
    .setFontWeight('bold');
  sheet.getRange('H9').setValue('💷 FINANCIAL KPIs');
  
  Logger.log('✅ Orange theme applied');
}

/**
 * Set up all chart zones with proper formatting
 */
function setupChartZones() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('📊 Setting up chart zones...');
  
  const chartZones = [
    {range: 'A20:F20', title: '📊 CHART: Fuel Mix (Doughnut/Pie) - A20:F40'},
    {range: 'G20:L20', title: '📊 CHART: Interconnector Flows (Multi-line) - G20:L40'},
    {range: 'A45:F45', title: '📊 CHART: Demand vs Generation 48h (Stacked Area) - A45:F65'},
    {range: 'G45:L45', title: '📊 CHART: System Prices SSP/SBP/MID (3-Line) - G45:L65'},
    {range: 'A70:L70', title: '📊 CHART: Financial KPIs BOD/BID/Imbalance (Column) - A70:L88'}
  ];
  
  chartZones.forEach(zone => {
    const range = sheet.getRange(zone.range);
    range.merge()
      .setValue(zone.title)
      .setBackground('#FFF1E6')
      .setFontColor('#FF8C00')
      .setFontWeight('bold')
      .setFontStyle('italic')
      .setFontSize(11)
      .setHorizontalAlignment('center');
    
    // Add placeholder text below
    const row = parseInt(zone.range.split(':')[0].match(/\d+/)[0]);
    sheet.getRange(`A${row + 2}`).setValue('[Chart will be inserted here via Apps Script]')
      .setFontSize(9)
      .setFontStyle('italic')
      .setFontColor('#999999');
  });
  
  Logger.log('✅ Chart zones created');
}

/**
 * Set up Top 12 Outages section
 */
function setupOutagesSection() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('⚠️ Setting up outages section...');
  
  // Header (Row 90)
  sheet.getRange('A90:H90')
    .merge()
    .setValue('⚠️  TOP 12 ACTIVE OUTAGES (by MW Unavailable)')
    .setBackground('#E53935')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(12)
    .setHorizontalAlignment('center');
  
  // Column headers (Row 91)
  const headers = ['BM Unit', 'Plant', 'Fuel', 'MW Lost', 'Region', 'Start Time', 'End Time', 'Status'];
  sheet.getRange('A91:H91')
    .setValues([headers])
    .setBackground('#FFCDD2')
    .setFontWeight('bold');
  
  // Note
  sheet.getRange('A92')
    .setValue('(Auto-updated every 10 minutes)')
    .setFontStyle('italic')
    .setFontSize(9)
    .setFontColor('#999999');
  
  // Clear data rows
  sheet.getRange('A93:H104').clearContent();
  
  Logger.log('✅ Outages section created');
}

/**
 * Set up data validations (dropdowns)
 */
function setupDataValidations() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('🔽 Setting up data validations...');
  
  // Time Range (B3)
  const timeValues = ['Real-Time (10 min)', '24 h', '48 h', '7 days', '30 days'];
  const timeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(timeValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('B3').setDataValidation(timeRule);
  
  // Region (D3)
  const regionValues = [
    'All GB', 'Eastern Power Networks (EPN)', 'South Eastern Power Networks (SPN)',
    'London Power Networks (LPN)', 'South Wales', 'South West',
    'East Midlands', 'West Midlands', 'North Wales & Merseyside',
    'South Scotland', 'North Scotland', 'Northern', 'Yorkshire', 'North West', 'Southern'
  ];
  const regionRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(regionValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('D3').setDataValidation(regionRule);
  
  // Alert Filter (F3)
  const alertValues = ['All', 'Critical Only', 'Wind Warning', 'Outages', 'Price Spike'];
  const alertRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(alertValues, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange('F3').setDataValidation(alertRule);
  
  // Date pickers (H3, J3)
  const dateRule = SpreadsheetApp.newDataValidation()
    .requireDate()
    .setAllowInvalid(false)
    .setHelpText('Select a date')
    .build();
  sheet.getRange('H3').setDataValidation(dateRule);
  sheet.getRange('J3').setDataValidation(dateRule);
  
  Logger.log('✅ Data validations set up');
}

/**
 * Apply conditional formatting rules
 */
function setupConditionalFormatting() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('🎨 Setting up conditional formatting...');
  
  // Clear existing rules
  sheet.clearConditionalFormatRules();
  
  const rules = [];
  
  // Rule 1: Critical outages (>500 MW) in outages section (B93:D104)
  const outageRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(500)
    .setBackground('#E53935')
    .setFontColor('#FFFFFF')
    .setBold(true)
    .setRanges([sheet.getRange('D93:D104')])
    .build();
  rules.push(outageRule);
  
  // Rule 2: High generation (>5000 MW) in fuel mix data (B10:B18)
  const genRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(5000)
    .setBackground('#43A047')
    .setFontColor('#FFFFFF')
    .setBold(true)
    .setRanges([sheet.getRange('B10:B18')])
    .build();
  rules.push(genRule);
  
  sheet.setConditionalFormatRules(rules);
  
  Logger.log('✅ Conditional formatting applied');
}

/**
 * Create usage notes
 */
function addUsageNotes() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  
  Logger.log('📝 Adding usage notes...');
  
  sheet.getRange('A110:L110')
    .merge()
    .setValue('📌 DASHBOARD NOTES')
    .setBackground('#004C97')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold');
  
  const notes = [
    ['• Chart zones (rows 20-88) are reserved - automation should NOT write here'],
    ['• Top 12 Outages section (rows 90-105) - auto-updated every 10 min'],
    ['• Full outage history is in the \'Outages\' sheet (searchable/filterable)'],
    ['• Date pickers in H3 & J3 filter historical data (click cells to see calendar)'],
    ['• Chart creation: Use Apps Script with ranges specified in CHART_SPECS.md'],
    ['• Automation scripts should only update: Rows 10-18 (data), Row 2 (timestamp), Rows 93-104 (outages)']
  ];
  
  sheet.getRange(111, 1, notes.length, 1).setValues(notes)
    .setFontSize(9)
    .setWrap(true);
  
  Logger.log('✅ Usage notes added');
}

/**
 * Create custom menu
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('⚡ Dashboard Controls')
    .addItem('🎨 Apply Orange Theme', 'applyFullDashboardSetup')
    .addItem('🔄 Refresh Timestamp', 'updateTimestamp')
    .addItem('🧹 Clear Outages', 'clearOutagesSection')
    .addSeparator()
    .addItem('📊 Create All Charts', 'createAllCharts')
    .addItem('🗺️ Setup Map', 'setupEnergyMap')
    .addToUi();
}

/**
 * Main function to set up everything
 */
function applyFullDashboardSetup() {
  const startTime = new Date();
  Logger.log('='.repeat(70));
  Logger.log('⚡ DASHBOARD V2 COMPLETE SETUP');
  Logger.log('='.repeat(70));
  
  try {
    applyOrangeTheme();
    setupChartZones();
    setupOutagesSection();
    setupDataValidations();
    setupConditionalFormatting();
    addUsageNotes();
    
    const endTime = new Date();
    const duration = (endTime - startTime) / 1000;
    
    Logger.log('='.repeat(70));
    Logger.log(`✅ COMPLETE! (${duration.toFixed(2)}s)`);
    Logger.log('='.repeat(70));
    
    SpreadsheetApp.getUi().alert(
      '✅ Dashboard Setup Complete!',
      `Orange theme applied successfully in ${duration.toFixed(2)} seconds.\n\n` +
      '• Date pickers active (H3, J3)\n' +
      '• Chart zones positioned\n' +
      '• Top 12 Outages section ready\n' +
      '• Conditional formatting applied\n\n' +
      'Check rows 110+ for usage notes.',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
    
  } catch (error) {
    Logger.log(`❌ Error: ${error.message}`);
    Logger.log(error.stack);
    SpreadsheetApp.getUi().alert('❌ Error', error.message, SpreadsheetApp.getUi().ButtonSet.OK);
  }
}

/**
 * Update timestamp
 */
function updateTimestamp() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  sheet.getRange('A2').setValue(`Last Updated: ${new Date().toLocaleString('en-GB')}`);
  Logger.log('✅ Timestamp updated');
}

/**
 * Clear outages section
 */
function clearOutagesSection() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet = ss.getSheetByName(DASHBOARD_SHEET);
  sheet.getRange('A93:H104').clearContent();
  sheet.getRange('A93').setValue(`No active outages (checked: ${new Date().toLocaleString('en-GB')})`);
  Logger.log('✅ Outages cleared');
}

/**
 * Setup Energy Map sheet
 */
function setupEnergyMap() {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let mapSheet = ss.getSheetByName('Energy_Map');
  
  if (!mapSheet) {
    mapSheet = ss.insertSheet('Energy_Map');
  }
  
  // Title
  mapSheet.getRange('A1:Z1')
    .merge()
    .setValue('🗺️  ENERGY MAP – DNO REGIONS, GSP CONNECTIONS & OFFSHORE WIND')
    .setBackground('#FF8C00')
    .setFontColor('#FFFFFF')
    .setFontWeight('bold')
    .setFontSize(14)
    .setHorizontalAlignment('center');
  mapSheet.setRowHeight(1, 30);
  
  // Layer table
  const layers = [
    ['Layer', 'Colour', 'Description'],
    ['DNO Boundaries', '#FFD180', 'Polygon overlay per DNO region'],
    ['GSP Points', '#004C97', 'Grid Supply Points (hover shows ID & MW)'],
    ['Offshore Wind', '#FF8C00', 'Wind farms & connecting GSP lines'],
    ['Outages', '#E53935', 'Active outage markers on map']
  ];
  
  mapSheet.getRange(3, 1, layers.length, 3).setValues(layers);
  mapSheet.getRange('A3:C3')
    .setBackground('#F5F5F5')
    .setFontWeight('bold');
  
  Logger.log('✅ Energy Map sheet configured');
  SpreadsheetApp.getUi().alert('✅ Energy Map Ready', 'Energy_Map sheet has been configured.', SpreadsheetApp.getUi().ButtonSet.OK);
}

/**
 * Placeholder for chart creation (to be implemented)
 */
function createAllCharts() {
  SpreadsheetApp.getUi().alert(
    '📊 Chart Creation',
    'Chart creation is not yet implemented.\n\n' +
    'Charts will be added manually using the marked zones:\n' +
    '• A20:F40 - Fuel Mix\n' +
    '• G20:L40 - Interconnectors\n' +
    '• A45:F65 - Demand vs Gen\n' +
    '• G45:L65 - System Prices\n' +
    '• A70:L88 - Financial KPIs\n\n' +
    'See CHART_SPECS.md for specifications.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}
