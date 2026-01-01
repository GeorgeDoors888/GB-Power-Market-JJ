/**
 * GSP-DNO Dynamic Linking for Search Sheet
 * Auto-link GSP regions with DNO operators
 */

// GSP to DNO mapping from neso_dno_reference table
var GSP_DNO_MAPPING = {
  '_A': 'UK Power Networks - Eastern',
  '_B': 'UK Power Networks - London',
  '_C': 'UK Power Networks - South Eastern',
  '_D': 'Electricity North West',
  '_E': 'Northern Powergrid - Yorkshire',
  '_F': 'Scottish & Southern - Southern',
  '_G': 'Scottish Power - Manweb',
  '_H': 'Scottish Power - Central & Southern Scotland',
  '_J': 'Scottish & Southern - SEPD',
  '_K': 'National Grid - South Wales',
  '_L': 'Scottish & Southern - SHEPD',
  '_M': 'National Grid - Midlands',
  '_N': 'Northern Powergrid - North East',
  '_P': 'National Grid - East Midlands'
};

// DNO to GSP mapping (reverse)
var DNO_GSP_MAPPING = {
  'UK Power Networks - Eastern': '_A',
  'UK Power Networks - London': '_B',
  'UK Power Networks - South Eastern': '_C',
  'Electricity North West': '_D',
  'Northern Powergrid - Yorkshire': '_E',
  'Scottish & Southern - Southern': '_F',
  'Scottish Power - Manweb': '_G',
  'Scottish Power - Central & Southern Scotland': '_H',
  'Scottish & Southern - SEPD': '_J',
  'National Grid - South Wales': '_K',
  'Scottish & Southern - SHEPD': '_L',
  'National Grid - Midlands': '_M',
  'Northern Powergrid - North East': '_N',
  'National Grid - East Midlands': '_P'
};

/**
 * On edit trigger - link GSP and DNO selections
 */
function onEdit(e) {
  var sheet = e.source.getActiveSheet();
  var range = e.range;
  
  // Only act on Search sheet
  if (sheet.getName() !== 'Search') return;
  
  var row = range.getRow();
  var col = range.getColumn();
  
  // B15 = GSP Region, B16 = DNO Operator
  
  // If GSP region changed (B15)
  if (row === 15 && col === 2) {
    var gspValue = range.getValue();
    if (gspValue && gspValue !== 'None' && gspValue !== 'All') {
      var dno = GSP_DNO_MAPPING[gspValue];
      if (dno) {
        sheet.getRange('B16').setValue(dno);
        sheet.getRange('C15').setValue('🔗'); // Link indicator
        SpreadsheetApp.getActiveSpreadsheet().toast('Auto-selected DNO: ' + dno, 'GSP-DNO Linked', 3);
      }
    } else {
      sheet.getRange('C15').clearContent();
    }
  }
  
  // If DNO operator changed (B16)
  if (row === 16 && col === 2) {
    var dnoValue = range.getValue();
    if (dnoValue && dnoValue !== 'None' && dnoValue !== 'All') {
      var gsp = DNO_GSP_MAPPING[dnoValue];
      if (gsp) {
        sheet.getRange('B15').setValue(gsp);
        sheet.getRange('C16').setValue('🔗'); // Link indicator
        SpreadsheetApp.getActiveSpreadsheet().toast('Auto-selected GSP: ' + gsp, 'DNO-GSP Linked', 3);
      }
    } else {
      sheet.getRange('C16').clearContent();
    }
  }
}

/**
 * Install trigger for onEdit
 */
function installGspDnoTrigger() {
  // Remove existing triggers
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'onEdit') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Install new trigger
  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(SpreadsheetApp.getActive())
    .onEdit()
    .create();
  
  SpreadsheetApp.getUi().alert('✅ GSP-DNO linking installed!\n\nNow when you select a GSP region, the DNO will auto-populate (and vice versa).');
}
