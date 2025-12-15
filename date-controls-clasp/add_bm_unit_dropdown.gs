/**
 * Add BM Unit dropdown in G66
 */
function addBMUnitDropdown() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  
  // Label in G65
  const label = sheet.getRange('G65');
  label.setValue('BM Unit:');
  label.setFontWeight('bold');
  label.setHorizontalAlignment('right');
  label.setBackground('#e8f4f8');
  
  // Dropdown in G66
  const dropdown = sheet.getRange('G66');
  
  // List of BM Units (add all your BM units here)
  const bmUnits = [
    'All BM Units',  // First option
    'FBPGM002',      // Flexgen battery
    'FFSEN005',      // Battery unit
    'T_DRAXX-1',     // Drax
    'T_DRAXX-2',
    'T_DRAXX-3',
    'T_DRAXX-4',
    'E_WBURB-1',     // West Burton
    'E_WBURB-2',
    'T_DRAXX-5',
    'T_DRAXX-6'
    // Add more units as needed
  ];
  
  // Create dropdown validation
  const rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(bmUnits, true)  // true = show dropdown
    .setAllowInvalid(false)
    .setHelpText('Select BM Unit for filtering')
    .build();
  
  dropdown.setDataValidation(rule);
  dropdown.setValue('All BM Units');  // Default value
  
  // Format cell
  dropdown.setBackground('#ffffff');
  dropdown.setBorder(true, true, true, true, false, false, '#4285f4', SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  dropdown.setHorizontalAlignment('center');
  dropdown.setFontSize(11);
  
  Logger.log('✓ BM Unit dropdown added to G66');
  
  SpreadsheetApp.getUi().alert(
    '✅ BM Unit Dropdown Added!\n\n' +
    'G65: "BM Unit:" label\n' +
    'G66: BM Unit selector\n' +
    'Default: "All BM Units"\n\n' +
    'Click G66 to select specific BM unit'
  );
}
