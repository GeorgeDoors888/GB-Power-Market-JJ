const PYTHON_API_URL = 'https://jibber-jabber-production.up.railway.app';
const SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8';

function updateOutagesFromPython() {
  try {
    Logger.log('🔄 Fetching outages from Python API...');
    const url = `${PYTHON_API_URL}/outages/names`;
    const response = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
    const responseCode = response.getResponseCode();
    
    if (responseCode !== 200) {
      Logger.log(`❌ API returned status ${responseCode}`);
      return;
    }
    
    const data = JSON.parse(response.getContentText());
    if (data.status !== 'success') {
      Logger.log('❌ API returned error status');
      return;
    }
    
    Logger.log(`✅ Fetched ${data.count} outages`);
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('Dashboard');
    
    if (!sheet) {
      Logger.log('❌ Dashboard sheet not found');
      return;
    }
    
    const outages = data.outages || [];
    const values = [];
    for (let i = 0; i < 14; i++) {
      if (i < outages.length) {
        values.push([outages[i].station_name]);
      } else {
        values.push(['']);
      }
    }
    
    sheet.getRange('A23:A36').setValues(values);
    Logger.log('✅ Updated outages list (A23:A36)');
    
    const now = new Date();
    const timestamp = Utilities.formatDate(now, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
    sheet.getRange('B2').setValue(`⏰ Last Updated: ${timestamp}`);
    Logger.log('✅ Updated timestamp (B2)');
    
  } catch (error) {
    Logger.log(`❌ Error: ${error.toString()}`);
  }
}

function setupTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  ScriptApp.newTrigger('updateOutagesFromPython')
    .timeBased()
    .everyMinutes(1)
    .create();
  
  Logger.log('✅ Trigger created: updateOutagesFromPython() every 1 minute');
}

function testUpdate() {
  Logger.log('🧪 Running manual test...');
  updateOutagesFromPython();
}

function removeTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateOutagesFromPython') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  Logger.log('✅ Trigger removed');
}