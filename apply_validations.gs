/**
 * Auto-Apply Data Validations to Search Sheet (ENHANCED VERSION)
 * Updated for new dropdown structure:
 * - B6: Search Scope (was duplicate Record Type)
 * - B7: Entity Type (renamed from Record Type for clarity)
 * - B8: Fuel Types (expanded to 6 types)
 * - B10: Organizations (expanded to 731 parties)
 * - B12: TEC Projects (placeholder)
 * - B15: GSP Locations (dual system: 14 Groups + 333 GSPs = 347 total)
 * - B16: DNO Operators (enhanced with MPAN IDs and GSP codes)
 */

function applyDataValidations() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var searchSheet = ss.getSheetByName('Search');
  var dropdownSheet = ss.getSheetByName('Dropdowns');
  
  if (!dropdownSheet) {
    SpreadsheetApp.getUi().alert('❌ Error: Dropdowns sheet not found!\n\nPlease run populate_search_dropdowns.py first.');
    return;
  }
  
  // Get data ranges from Dropdowns sheet (UPDATED)
  var bmuRange = dropdownSheet.getRange('A2:A1406');           // 1,403 BMU IDs
  var orgRange = dropdownSheet.getRange('B2:B734');            // 731 Organizations
  var fuelRange = dropdownSheet.getRange('C2:C9');             // 6 Fuel Types (+ None/All)
  var gspRange = dropdownSheet.getRange('D2:D350');            // 347 GSP Locations (14 Groups + 333 GSPs)
  var dnoRange = dropdownSheet.getRange('E2:E17');             // 14 DNO Operators (enhanced)
  var voltageRange = dropdownSheet.getRange('F2:F6');          // 3 Voltage Levels
  var searchScopeRange = dropdownSheet.getRange('G2:G6');      // 5 Search Scopes (NEW)
  var entityTypeRange = dropdownSheet.getRange('H2:H10');      // 7 Entity Types (RENAMED)
  var roleRange = dropdownSheet.getRange('I2:I4');             // Roles
  var tecRange = dropdownSheet.getRange('J2:J4');              // TEC Projects (placeholder)
  
  // Apply validations to Search sheet cells
  
  // B6: Search Scope dropdown (NEW - replaces duplicate Record Type)
  var searchScopeRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(searchScopeRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select search scope: All Records, Active Only, Historical, etc.')
    .build();
  searchSheet.getRange('B6').setDataValidation(searchScopeRule);
  
  // B7: Entity Type dropdown (RENAMED from "Record Type" for clarity)
  var entityTypeRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(entityTypeRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select entity type: BM Unit, BSC Party, Generator, Supplier, etc.')
    .build();
  searchSheet.getRange('B7').setDataValidation(entityTypeRule);
  
  // B8: Fuel Type dropdown (EXPANDED - 6 types)
  var fuelRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(fuelRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select fuel type: BIOMASS, CCGT, NPSHYD, OCGT, WIND, OTHER')
    .build();
  searchSheet.getRange('B8').setDataValidation(fuelRule);
  
  // B9: BMU ID dropdown (1,403 options)
  var bmuRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(bmuRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select BMU ID from 1,403 active units')
    .build();
  searchSheet.getRange('B9').setDataValidation(bmuRule);
  
  // B10: Organization dropdown (EXPANDED - 731 parties)
  var orgRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(orgRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select organization from 731 BSC parties + BMU owners (includes Flexitricity)')
    .build();
  searchSheet.getRange('B10').setDataValidation(orgRule);
  
  // B12: TEC Project dropdown (NEW - placeholder)
  var tecRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(tecRange, true)
    .setAllowInvalid(false)
    .setHelpText('TEC projects (requires NESO Connections 360 data ingest)')
    .build();
  searchSheet.getRange('B12').setDataValidation(tecRule);
  
  // B15: GSP Location dropdown (ENHANCED - dual system)
  var gspRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(gspRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select GSP: 14 Groups (e.g. "Group: London (_C)") or 333 Individual GSPs (e.g. "GSP: GSP_133")')
    .build();
  searchSheet.getRange('B15').setDataValidation(gspRule);
  
  // B16: DNO Operator dropdown (ENHANCED - with MPAN IDs and GSP codes)
  var dnoRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(dnoRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select DNO: Format "DNO 12: UK Power Networks (London) [GSP: _C]"')
    .build();
  searchSheet.getRange('B16').setDataValidation(dnoRule);
  
  // B17: Voltage Level dropdown (3 levels)
  var voltageRule = SpreadsheetApp.newDataValidation()
    .requireValueInRange(voltageRange, true)
    .setAllowInvalid(false)
    .setHelpText('Select voltage level: EHV (132 kV+), HV (11-33 kV), LV (<11 kV)')
    .build();
  searchSheet.getRange('B17').setDataValidation(voltageRule);
  
  SpreadsheetApp.getUi().alert('✅ Data Validations Applied! (ENHANCED VERSION)\n\n' +
    'Dropdowns now active for:\n' +
    '• B6 Search Scope (5 options) - NEW\n' +
    '• B7 Entity Type (7 types) - RENAMED\n' +
    '• B8 Fuel Type (6 categories) - EXPANDED\n' +
    '• B9 BMU ID (1,403 units)\n' +
    '• B10 Organization (731 parties) - EXPANDED\n' +
    '• B12 TEC Project (placeholder) - NEW\n' +
    '• B15 GSP Location (347 entries) - DUAL SYSTEM\n' +
    '• B16 DNO Operator (14 with codes) - ENHANCED\n' +
    '• B17 Voltage Level (3 levels)\n\n' +
    'Try selecting cells to see new dropdowns!');
}

/**
 * Add menu item for applying validations
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔧 Setup')
    .addItem('Apply Data Validations', 'applyDataValidations')
    .addItem('Install GSP-DNO Linking', 'installGspDnoTrigger')
    .addToUi();
}
