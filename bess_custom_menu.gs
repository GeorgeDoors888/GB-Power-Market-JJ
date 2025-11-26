
/**
 * BESS Sheet - Custom Menu
 * Add this to Apps Script editor
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 BESS Tools')
    .addItem('🔄 Refresh DNO Data', 'refreshDnoData')
    .addSeparator()
    .addItem('✅ Validate MPAN', 'validateMpan')
    .addItem('📍 Validate Postcode', 'validatePostcode')
    .addSeparator()
    .addItem('📊 Generate HH Profile', 'generateHhProfile')
    .addItem('📈 Show Metrics Dashboard', 'showMetrics')
    .addSeparator()
    .addItem('📥 Export to CSV', 'exportToCsv')
    .addItem('📄 Generate PDF Report', 'generatePdfReport')
    .addSeparator()
    .addItem('⚙️ Settings', 'showSettings')
    .addToUi();
}

function refreshDnoData() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  // Check if manualRefreshDno exists (from bess_auto_trigger.gs)
  try {
    if (typeof manualRefreshDno === 'function') {
      manualRefreshDno();
    } else {
      // Manual trigger via webhook
      const postcode = sheet.getRange('A6').getValue();
      let mpan = sheet.getRange('B6').getValue();
      const voltage = sheet.getRange('A10').getValue();
      
      // Extract MPAN value if it's in dropdown format "ID - CODE"
      if (typeof mpan === 'string' && mpan.includes(' - ')) {
        mpan = mpan.split(' - ')[0];
      }
      
      if (!postcode || !mpan || !voltage) {
        Browser.msgBox('⚠️ Missing Data', 'Please enter Postcode (A6), MPAN (B6), and Voltage (A10)', Browser.Buttons.OK);
        return;
      }
      
      sheet.getRange('A4:H4').setValues([[
        '🔄 Refreshing...', '', '', '', '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#FFEB3B');
      
      // Call webhook server on UpCloud
      const webhookUrl = 'http://94.237.55.234:5001/trigger-dno-lookup';
      const payload = {
        'postcode': postcode,
        'mpan_id': mpan,
        'voltage': voltage
      };
      
      const options = {
        'method': 'post',
        'contentType': 'application/json',
        'payload': JSON.stringify(payload),
        'muteHttpExceptions': true
      };
      
      try {
        const response = UrlFetchApp.fetch(webhookUrl, options);
        if (response.getResponseCode() === 200) {
          sheet.getRange('A4:H4').setValues([[
            '✅ Refresh triggered successfully', '', '', '', '', '', '', ''
          ]]);
          sheet.getRange('A4:H4').setBackground('#4CAF50');
        } else {
          throw new Error('Webhook returned: ' + response.getResponseCode());
        }
      } catch(e) {
        Browser.msgBox('⚠️ Manual Refresh Required', 
          'Run this command in your terminal:\n\n' +
          'python3 dno_lookup_python.py ' + mpan + ' "' + voltage + '"\n\n' +
          'Or start the webhook server:\n' +
          'python3 dno_webhook_server.py', 
          Browser.Buttons.OK);
      }
    }
  } catch(e) {
    sheet.getRange('A4:H4').setValues([[
      '❌ Error: ' + e.message, '', '', '', '', '', '', ''
    ]]);
    sheet.getRange('A4:H4').setBackground('#FF5252');
  }
}

function validateMpan() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const mpan = sheet.getRange('B6').getValue();
  
  // Extract MPAN value if it's in "ID - CODE" format from dropdown
  let mpanValue = mpan;
  if (typeof mpan === 'string' && mpan.includes(' - ')) {
    mpanValue = mpan.split(' - ')[0];
  }
  
  if (!mpanValue || mpanValue.toString().length < 2) {
    Browser.msgBox('❌ Invalid MPAN', 'MPAN must be at least 2 digits (Distributor ID)', Browser.Buttons.OK);
    return;
  }
  
  // Extract distributor ID (first 2 digits)
  const distributorId = mpanValue.toString().substring(0, 2);
  const validIds = ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23'];
  
  if (validIds.includes(distributorId)) {
    Browser.msgBox('✅ MPAN Valid', 
      'MPAN: ' + mpanValue + '\n' +
      'Distributor ID: ' + distributorId + '\n\n' +
      'Click "🔄 Refresh DNO Data" to lookup details', 
      Browser.Buttons.OK);
  } else {
    Browser.msgBox('❌ Invalid Distributor ID', 
      'First 2 digits must be 10-23.\n' +
      'Found: ' + distributorId, 
      Browser.Buttons.OK);
  }
}

function validatePostcode() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  
  if (!postcode) {
    Browser.msgBox('❌ No Postcode', 'Please enter a postcode in A6', Browser.Buttons.OK);
    return;
  }
  
  // UK postcode regex
  const regex = /^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})$/i;
  const normalized = postcode.toString().trim().toUpperCase();
  
  if (regex.test(normalized)) {
    Browser.msgBox('✅ Postcode Valid', 'Normalized: ' + normalized, Browser.Buttons.OK);
  } else {
    Browser.msgBox('❌ Invalid Postcode', 'Please check the format', Browser.Buttons.OK);
  }
}

function generateHhProfile() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const minKw = sheet.getRange('B17').getValue() || 500;
  const avgKw = sheet.getRange('B18').getValue() || 1500;
  const maxKw = sheet.getRange('B19').getValue() || 2500;
  
  Browser.msgBox('📊 Generate HH Profile', 
    'Run this command in your terminal:\n\n' +
    'python3 generate_hh_profile.py\n\n' +
    'Current parameters:\n' +
    '• Min: ' + minKw + ' kW\n' +
    '• Avg: ' + avgKw + ' kW\n' +
    '• Max: ' + maxKw + ' kW', 
    Browser.Buttons.OK);
}

function showMetrics() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const html = HtmlService.createHtmlOutput('<h3>Network Metrics</h3><p>View metrics in row 22+</p>')
    .setWidth(300)
    .setHeight(200);
  SpreadsheetApp.getUi().showModalDialog(html, '📈 Metrics Dashboard');
}

function exportToCsv() {
  Browser.msgBox('📥 Export to CSV', 
    'Run this command in your terminal:\n\n' +
    'python3 bess_export_reports.py --format csv\n\n' +
    'Export all formats:\n' +
    'python3 bess_export_reports.py --format all', 
    Browser.Buttons.OK);
}

function generatePdfReport() {
  Browser.msgBox('📄 Generate PDF Report', 
    'Run this command in your terminal:\n\n' +
    'python3 bess_export_reports.py --format txt\n\n' +
    'Then convert TXT to PDF:\n' +
    'enscript -B -p output.ps bess_report_*.txt && ps2pdf output.ps report.pdf', 
    Browser.Buttons.OK);
}

function showSettings() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 15px; }
      h3 { color: #1976D2; margin-bottom: 10px; }
      .setting { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px; }
      .label { font-weight: bold; color: #555; }
      .value { color: #000; margin-left: 10px; }
      code { background: #e0e0e0; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
    <h3>⚙️ BESS System Settings</h3>
    
    <div class="setting">
      <div class="label">📍 Auto-Monitor Status:</div>
      <div class="value">Check with: <code>python3 bess_auto_monitor.py --stats</code></div>
    </div>
    
    <div class="setting">
      <div class="label">🔄 Auto-Refresh Interval:</div>
      <div class="value">30 seconds (configurable in bess_auto_monitor.py)</div>
    </div>
    
    <div class="setting">
      <div class="label">💾 Cache TTL:</div>
      <div class="value">1 hour (3600 seconds)</div>
    </div>
    
    <div class="setting">
      <div class="label">📊 Export Formats:</div>
      <div class="value">CSV, JSON, TXT</div>
    </div>
    
    <div class="setting">
      <div class="label">📋 Data Validation:</div>
      <div class="value">Dropdowns on A10 (Voltage), B6 (DNO), E10 (Profile), F10 (Meter), H10 (DUoS)</div>
    </div>
    
    <div class="setting">
      <div class="label">🌐 Webhook Server:</div>
      <div class="value">Port 5001 (start with: <code>python3 dno_webhook_server.py</code>)</div>
    </div>
    
    <div class="setting">
      <div class="label">📖 Documentation:</div>
      <div class="value">See BESS_INSTALLATION_GUIDE.md</div>
    </div>
  `)
    .setWidth(500)
    .setHeight(450);
  SpreadsheetApp.getUi().showModalDialog(html, '⚙️ BESS Settings');
}
