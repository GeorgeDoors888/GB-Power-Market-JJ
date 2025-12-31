
/**
 * Threshold Alert Email Notifications
 * Checks dashboard values and sends alerts if thresholds breached
 */

function checkThresholdsAndEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Live Dashboard v2');
  
  // Get current values
  var sip = parseFloat(sheet.getRange('L13').getValue());
  var frequency = parseFloat(sheet.getRange('L20').getValue());
  var arbitrage = parseFloat(sheet.getRange('L31').getValue().replace('%', ''));
  var var99 = parseFloat(sheet.getRange('L38').getValue().replace('£', '').replace('/MWh', ''));
  
  var alerts = [];
  
  // Check thresholds
  if (sip > 100) {
    alerts.push('🚨 HIGH SIP: £' + sip.toFixed(2) + '/MWh (threshold: £100)');
  }
  
  if (frequency < 49.8) {
    alerts.push('⚡ LOW FREQUENCY: ' + frequency.toFixed(2) + ' Hz (threshold: 49.8 Hz)');
  }
  
  if (arbitrage < 50) {
    alerts.push('⚠️ LOW ARBITRAGE: ' + arbitrage.toFixed(1) + '% (threshold: 50%)');
  }
  
  if (var99 > 150) {
    alerts.push('📊 HIGH RISK: VaR 99% = £' + var99.toFixed(2) + '/MWh (threshold: £150)');
  }
  
  // Send email if any alerts
  if (alerts.length > 0) {
    var recipient = 'george@upowerenergy.uk';  // Change to your email
    var subject = '🚨 GB Power Market Alert - ' + alerts.length + ' threshold(s) breached';
    
    var body = 'GB Power Market Dashboard Alerts\n';
    body += '================================\n\n';
    body += 'Time: ' + new Date().toLocaleString('en-GB') + '\n\n';
    body += alerts.join('\n') + '\n\n';
    body += 'Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA\n';
    
    MailApp.sendEmail(recipient, subject, body);
    Logger.log('Sent alert email: ' + alerts.length + ' alerts');
  } else {
    Logger.log('No threshold breaches detected');
  }
}

/**
 * Install time-based trigger (runs every 15 minutes)
 * Run this function once to set up automatic checking
 */
function installTrigger() {
  // Delete existing triggers
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'checkThresholdsAndEmail') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger (every 15 minutes)
  ScriptApp.newTrigger('checkThresholdsAndEmail')
    .timeBased()
    .everyMinutes(15)
    .create();
  
  Logger.log('Trigger installed: check every 15 minutes');
}

/**
 * Uninstall trigger
 */
function uninstallTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'checkThresholdsAndEmail') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  Logger.log('Trigger removed');
}
