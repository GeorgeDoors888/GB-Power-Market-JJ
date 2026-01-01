/**
 * Dynamic Dropdown Population via Apps Script
 * Uses BigQuery API instead of sheet ranges for better performance
 * Caches results in PropertiesService for 6 hours
 */

// Configuration
var VERCEL_PROXY_URL = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
var CACHE_DURATION = 6 * 60 * 60; // 6 hours in seconds

/**
 * Get dropdown data with caching
 */
function getDropdownData(dataType) {
  var cache = PropertiesService.getScriptProperties();
  var cacheKey = 'dropdown_' + dataType;
  
  // Check cache first
  var cached = cache.getProperty(cacheKey);
  if (cached) {
    try {
      var parsed = JSON.parse(cached);
      var age = (new Date().getTime() - parsed.timestamp) / 1000;
      if (age < CACHE_DURATION) {
        Logger.log('📦 Cache hit for ' + dataType + ' (age: ' + Math.round(age/60) + ' min)');
        return parsed.data;
      }
    } catch (e) {
      Logger.log('⚠️ Cache parse error: ' + e.message);
    }
  }
  
  // Cache miss - fetch from BigQuery
  Logger.log('🔍 Cache miss for ' + dataType + ' - fetching from BigQuery...');
  var data = fetchDropdownData(dataType);
  
  // Store in cache
  if (data && data.length > 0) {
    var cacheData = {
      data: data,
      timestamp: new Date().getTime()
    };
    cache.setProperty(cacheKey, JSON.stringify(cacheData));
    Logger.log('✅ Cached ' + data.length + ' items for ' + dataType);
  }
  
  return data;
}

/**
 * Fetch dropdown data from BigQuery via Vercel proxy
 */
function fetchDropdownData(dataType) {
  var queries = {
    'bmu_ids': 'SELECT DISTINCT bmu_id FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` WHERE is_active = TRUE ORDER BY bmu_id',
    'organizations': 'SELECT DISTINCT lead_party_name FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` WHERE is_active = TRUE AND lead_party_name IS NOT NULL ORDER BY lead_party_name',
    'fuel_types': 'SELECT DISTINCT fuel_type_category FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` WHERE is_active = TRUE AND fuel_type_category IS NOT NULL ORDER BY fuel_type_category',
    'gsp_groups': 'SELECT DISTINCT gsp_group FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` WHERE is_active = TRUE AND gsp_group IS NOT NULL ORDER BY gsp_group',
    'dno_operators': 'SELECT DISTINCT dno_name FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` WHERE dno_name IS NOT NULL ORDER BY dno_name'
  };
  
  var sql = queries[dataType];
  if (!sql) {
    Logger.log('❌ Unknown data type: ' + dataType);
    return [];
  }
  
  try {
    var response = UrlFetchApp.fetch(VERCEL_PROXY_URL + '?path=/query_bigquery_get', {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({ sql: sql }),
      muteHttpExceptions: true,
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    });
    
    var result = JSON.parse(response.getContentText());
    
    if (result.success && result.results) {
      // Extract first column from results
      var data = result.results.map(function(row) {
        return row[0];
      });
      return data;
    } else {
      Logger.log('❌ Query failed: ' + (result.error || 'Unknown error'));
      return [];
    }
  } catch (e) {
    Logger.log('❌ Fetch error: ' + e.message);
    return [];
  }
}

/**
 * Apply data validations using dynamic lists
 */
function applyDynamicValidations() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var searchSheet = ss.getSheetByName('Search');
  
  if (!searchSheet) {
    SpreadsheetApp.getUi().alert('❌ Error: Search sheet not found!');
    return;
  }
  
  SpreadsheetApp.getUi().alert('⏳ Fetching dropdown data from BigQuery...\n\nThis may take 10-20 seconds on first run.\nSubsequent runs will be instant (cached).');
  
  // Fetch data with caching
  var bmuIds = getDropdownData('bmu_ids');
  var organizations = getDropdownData('organizations');
  var fuelTypes = getDropdownData('fuel_types');
  var gspGroups = getDropdownData('gsp_groups');
  var dnoOperators = getDropdownData('dno_operators');
  
  // Predefined lists
  var voltages = ['HV', 'LV', 'EHV'];
  var recordTypes = ['Generator', 'Supplier', 'Interconnector', 'BSC Party', 'TEC Project'];
  var roles = ['VLP', 'VTP', 'Supplier', 'Generator', 'None', 'All'];
  
  Logger.log('📊 Data fetched:');
  Logger.log('  • BMU IDs: ' + bmuIds.length);
  Logger.log('  • Organizations: ' + organizations.length);
  Logger.log('  • Fuel Types: ' + fuelTypes.length);
  Logger.log('  • GSP Groups: ' + gspGroups.length);
  Logger.log('  • DNO Operators: ' + dnoOperators.length);
  
  // Apply validations using requireValueInList (faster than sheet ranges)
  
  // B6: Record Type
  var recordTypeRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(recordTypes, true)
    .setAllowInvalid(false)
    .setHelpText('Select record type')
    .build();
  searchSheet.getRange('B6').setDataValidation(recordTypeRule);
  
  // B7: CUSC Role
  var roleRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(roles, true)
    .setAllowInvalid(false)
    .setHelpText('Select CUSC/BSC role')
    .build();
  searchSheet.getRange('B7').setDataValidation(roleRule);
  
  // B8: Fuel Type
  if (fuelTypes.length > 0) {
    var fuelRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(fuelTypes, true)
      .setAllowInvalid(false)
      .setHelpText('Select fuel type (' + fuelTypes.length + ' options)')
      .build();
    searchSheet.getRange('B8').setDataValidation(fuelRule);
  }
  
  // B9: BMU ID (use autocomplete for 1,403 items)
  if (bmuIds.length > 0) {
    // For large lists, use requireValueInList with show dropdown = false (autocomplete only)
    var bmuRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(bmuIds, false)  // false = autocomplete only
      .setAllowInvalid(true)  // Allow typing
      .setHelpText('Type to search ' + bmuIds.length + ' BMU IDs')
      .build();
    searchSheet.getRange('B9').setDataValidation(bmuRule);
  }
  
  // B10: Organization
  if (organizations.length > 0) {
    var orgRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(organizations, true)
      .setAllowInvalid(false)
      .setHelpText('Select organization (' + organizations.length + ' parties)')
      .build();
    searchSheet.getRange('B10').setDataValidation(orgRule);
  }
  
  // B15: GSP Region
  if (gspGroups.length > 0) {
    var gspRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(gspGroups, true)
      .setAllowInvalid(false)
      .setHelpText('Select GSP region (' + gspGroups.length + ' groups)')
      .build();
    searchSheet.getRange('B15').setDataValidation(gspRule);
  }
  
  // B16: DNO Operator
  if (dnoOperators.length > 0) {
    var dnoRule = SpreadsheetApp.newDataValidation()
      .requireValueInList(dnoOperators, true)
      .setAllowInvalid(false)
      .setHelpText('Select DNO operator (' + dnoOperators.length + ' operators)')
      .build();
    searchSheet.getRange('B16').setDataValidation(dnoRule);
  }
  
  // B17: Voltage Level
  var voltageRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(voltages, true)
    .setAllowInvalid(false)
    .setHelpText('Select voltage level')
    .build();
  searchSheet.getRange('B17').setDataValidation(voltageRule);
  
  SpreadsheetApp.getUi().alert('✅ Dynamic Validations Applied!\n\n' +
    'Dropdowns now active with BigQuery data:\n' +
    '• Record Type (5 options)\n' +
    '• CUSC Role (6 options)\n' +
    '• Fuel Type (' + fuelTypes.length + ' categories)\n' +
    '• BMU ID (' + bmuIds.length + ' units - autocomplete)\n' +
    '• Organization (' + organizations.length + ' parties)\n' +
    '• GSP Region (' + gspGroups.length + ' groups)\n' +
    '• DNO Operator (' + dnoOperators.length + ' operators)\n' +
    '• Voltage Level (3 levels)\n\n' +
    '⚡ Data cached for 6 hours - next refresh will be instant!');
}

/**
 * Clear dropdown cache
 */
function clearDropdownCache() {
  var cache = PropertiesService.getScriptProperties();
  var keys = ['dropdown_bmu_ids', 'dropdown_organizations', 'dropdown_fuel_types', 
              'dropdown_gsp_groups', 'dropdown_dno_operators'];
  
  keys.forEach(function(key) {
    cache.deleteProperty(key);
  });
  
  SpreadsheetApp.getUi().alert('🗑️ Cache Cleared!\n\nNext validation refresh will fetch fresh data from BigQuery.');
}

/**
 * Refresh dropdowns (clear cache + re-apply)
 */
function refreshDropdowns() {
  clearDropdownCache();
  applyDynamicValidations();
}

/**
 * Show cache status
 */
function showCacheStatus() {
  var cache = PropertiesService.getScriptProperties();
  var keys = ['dropdown_bmu_ids', 'dropdown_organizations', 'dropdown_fuel_types', 
              'dropdown_gsp_groups', 'dropdown_dno_operators'];
  
  var status = '📦 Dropdown Cache Status:\n\n';
  var now = new Date().getTime();
  
  keys.forEach(function(key) {
    var cached = cache.getProperty(key);
    if (cached) {
      try {
        var parsed = JSON.parse(cached);
        var ageMin = Math.round((now - parsed.timestamp) / 60000);
        var dataType = key.replace('dropdown_', '');
        status += dataType + ': ' + parsed.data.length + ' items (age: ' + ageMin + ' min)\n';
      } catch (e) {
        status += key + ': ERROR\n';
      }
    } else {
      status += key.replace('dropdown_', '') + ': NOT CACHED\n';
    }
  });
  
  status += '\n⏱️ Cache TTL: ' + (CACHE_DURATION / 3600) + ' hours';
  
  SpreadsheetApp.getUi().alert(status);
}

/**
 * Menu creation
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🔧 Dropdown Manager')
    .addItem('⚡ Apply Dynamic Validations', 'applyDynamicValidations')
    .addItem('🔄 Refresh Dropdowns', 'refreshDropdowns')
    .addSeparator()
    .addItem('📊 Show Cache Status', 'showCacheStatus')
    .addItem('🗑️ Clear Cache', 'clearDropdownCache')
    .addToUi();
}
