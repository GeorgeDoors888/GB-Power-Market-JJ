
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
  sheet.getRange('A4:H4').setValues([[
    '🔄 Refreshing...', '', '', '', '', '', '', ''
  ]]);
  sheet.getRange('A4:H4').setBackground('#FFEB3B');
  
  // Trigger Python script
  try {
    manualRefreshDno();  // Calls existing function in bess_auto_trigger.gs
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
  
  if (!mpan || mpan.toString().length !== 13) {
    Browser.msgBox('❌ Invalid MPAN', 'MPAN must be 13 digits', Browser.Buttons.OK);
    return;
  }
  
  // Check digit validation would go here
  Browser.msgBox('✅ MPAN Format Valid', 'MPAN: ' + mpan, Browser.Buttons.OK);
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
  Browser.msgBox('📊 HH Profile', 'Run: python3 generate_hh_profile.py', Browser.Buttons.OK);
}

function showMetrics() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const html = HtmlService.createHtmlOutput('<h3>Network Metrics</h3><p>View metrics in row 22+</p>')
    .setWidth(300)
    .setHeight(200);
  SpreadsheetApp.getUi().showModalDialog(html, '📈 Metrics Dashboard');
}

function exportToCsv() {
  Browser.msgBox('📥 Export', 'CSV export feature coming soon!', Browser.Buttons.OK);
}

function generatePdfReport() {
  Browser.msgBox('📄 PDF Report', 'PDF generation feature coming soon!', Browser.Buttons.OK);
}

function showSettings() {
  Browser.msgBox('⚙️ Settings', 'Settings panel coming soon!', Browser.Buttons.OK);
}
