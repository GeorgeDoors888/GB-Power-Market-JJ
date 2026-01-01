/**
 * COMPREHENSIVE DIAGNOSTIC FOR MAP SIDEBAR & SEARCH ISSUES
 * Run this in Apps Script to diagnose both problems
 */

function diagnosticComplete() {
  var results = [];
  
  results.push('='.repeat(80));
  results.push('🔍 DIAGNOSTIC REPORT - MAP SIDEBAR & SEARCH FUNCTION');
  results.push('='.repeat(80));
  results.push('');
  
  // ============================================================================
  // TEST 1: Maps API Key
  // ============================================================================
  results.push('TEST 1: Google Maps API Key');
  results.push('-'.repeat(80));
  
  try {
    var props = PropertiesService.getScriptProperties();
    var apiKey = props.getProperty('GOOGLE_MAPS_API_KEY');
    
    if (!apiKey) {
      results.push('❌ FAIL: No GOOGLE_MAPS_API_KEY found in Script Properties');
      results.push('   FIX: File > Project Settings > Script Properties');
      results.push('        Add key: GOOGLE_MAPS_API_KEY');
      results.push('        Value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0');
    } else {
      results.push('✅ PASS: API key found');
      results.push('   Key: ' + apiKey.substring(0, 20) + '...' + apiKey.substring(apiKey.length - 5));
      
      // Test if key works by making a request
      results.push('');
      results.push('   Testing API key validity...');
      try {
        var testUrl = 'https://maps.googleapis.com/maps/api/js?key=' + apiKey + '&v=weekly';
        var response = UrlFetchApp.fetch(testUrl, {
          muteHttpExceptions: true,
          followRedirects: false
        });
        var code = response.getResponseCode();
        var content = response.getContentText();
        
        results.push('   Response code: ' + code);
        
        if (content.indexOf('ApiNotActivatedMapError') !== -1) {
          results.push('   ❌ ERROR: Maps JavaScript API NOT ENABLED');
          results.push('   FIX: https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9');
          results.push('        Click ENABLE button');
        } else if (content.indexOf('RefererNotAllowedMapError') !== -1) {
          results.push('   ❌ ERROR: Domain restrictions blocking script.google.com');
          results.push('   FIX: https://console.cloud.google.com/apis/credentials?project=inner-cinema-476211-u9');
          results.push('        Click your API key → Application restrictions → None');
          results.push('        OR add script.google.com to allowed referrers');
        } else if (content.indexOf('InvalidKeyMapError') !== -1) {
          results.push('   ❌ ERROR: Invalid API key');
          results.push('   FIX: Create new API key in Google Cloud Console');
        } else if (code === 200 || content.indexOf('google.maps') !== -1) {
          results.push('   ✅ API key is VALID and Maps API responds');
        } else {
          results.push('   ⚠️ UNKNOWN: Unexpected response (see below)');
          results.push('   First 200 chars: ' + content.substring(0, 200));
        }
      } catch (e) {
        results.push('   ⚠️ Could not test API key: ' + e.message);
        results.push('   This is normal if Maps API not enabled yet');
      }
    }
  } catch (e) {
    results.push('❌ ERROR: ' + e.message);
  }
  
  results.push('');
  
  // ============================================================================
  // TEST 2: BigQuery API
  // ============================================================================
  results.push('TEST 2: BigQuery API for Map Data');
  results.push('-'.repeat(80));
  
  try {
    // Check if BigQuery service is enabled
    var projectId = 'inner-cinema-476211-u9';
    
    results.push('Testing DNO boundaries query...');
    var dnoQuery = {
      query: 'SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`',
      useLegacySql: false,
      location: 'US'
    };
    
    try {
      var dnoResults = BigQuery.Jobs.query(dnoQuery, projectId);
      var dnoCount = dnoResults.rows[0].f[0].v;
      results.push('✅ PASS: DNO boundaries accessible (' + dnoCount + ' regions)');
    } catch (e) {
      results.push('❌ FAIL: Cannot query DNO boundaries');
      results.push('   Error: ' + e.message);
      results.push('   FIX: Enable BigQuery API in Apps Script Services');
    }
    
    results.push('');
    results.push('Testing GSP boundaries query...');
    var gspQuery = {
      query: 'SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries`',
      useLegacySql: false,
      location: 'US'
    };
    
    try {
      var gspResults = BigQuery.Jobs.query(gspQuery, projectId);
      var gspCount = gspResults.rows[0].f[0].v;
      results.push('✅ PASS: GSP boundaries accessible (' + gspCount + ' regions)');
    } catch (e) {
      results.push('❌ FAIL: Cannot query GSP boundaries');
      results.push('   Error: ' + e.message);
    }
    
  } catch (e) {
    results.push('❌ ERROR: ' + e.message);
    results.push('   FIX: Resources > Advanced Google Services > BigQuery API (ON)');
  }
  
  results.push('');
  
  // ============================================================================
  // TEST 3: HTML File Existence
  // ============================================================================
  results.push('TEST 3: Map Sidebar HTML File');
  results.push('-'.repeat(80));
  
  try {
    var html = HtmlService.createHtmlOutputFromFile('map_sidebarh');
    var content = html.getContent();
    results.push('✅ PASS: map_sidebarh.html exists');
    results.push('   File size: ' + content.length + ' characters');
    
    // Check for critical elements
    if (content.indexOf('initMap') === -1) {
      results.push('   ⚠️ WARNING: initMap() function not found in HTML');
    }
    if (content.indexOf('loadLayer') === -1) {
      results.push('   ⚠️ WARNING: loadLayer() function not found in HTML');
    }
    if (content.indexOf('google.maps') === -1) {
      results.push('   ⚠️ WARNING: Google Maps references not found in HTML');
    }
    if (content.indexOf('getMapsApiKey') === -1) {
      results.push('   ⚠️ WARNING: getMapsApiKey() call not found in HTML');
    }
    
    // Check if file seems complete (should be ~7500+ characters)
    if (content.length < 7000) {
      results.push('   ⚠️ WARNING: File may be truncated (expected ~7500+ chars)');
    } else {
      results.push('   ✅ File size looks complete');
    }
    
  } catch (e) {
    results.push('❌ FAIL: map_sidebarh.html not found or cannot be loaded');
    results.push('   Error: ' + e.message);
  }
  
  results.push('');
  
  // ============================================================================
  // TEST 4: Search Interface
  // ============================================================================
  results.push('TEST 4: Search Interface');
  results.push('-'.repeat(80));
  
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
    
    if (!sheet) {
      results.push('❌ FAIL: "Search" sheet not found');
      results.push('   FIX: Create a sheet named "Search" in your spreadsheet');
    } else {
      results.push('✅ PASS: Search sheet exists');
      
      // Test reading search criteria
      try {
        var fromDate = sheet.getRange('B4').getValue();
        var toDate = sheet.getRange('D4').getValue();
        var partyName = sheet.getRange('B5').getValue();
        
        results.push('   Sample criteria values:');
        results.push('     From Date (B4): ' + fromDate);
        results.push('     To Date (D4): ' + toDate);
        results.push('     Party Name (B5): ' + partyName);
        
        // Test API endpoint
        results.push('');
        results.push('   Testing search API endpoint...');
        
        // Read API_ENDPOINT from search_interface.gs
        var apiEndpoint = 'https://a92f6deceb5e.ngrok-free.app/search';
        results.push('   API Endpoint: ' + apiEndpoint);
        
        try {
          var testResponse = UrlFetchApp.fetch(apiEndpoint, {
            method: 'post',
            contentType: 'application/json',
            payload: JSON.stringify({ test: true }),
            muteHttpExceptions: true
          });
          
          var statusCode = testResponse.getResponseCode();
          results.push('   Response code: ' + statusCode);
          
          if (statusCode === 200) {
            results.push('   ✅ API endpoint is accessible');
          } else if (statusCode === 404) {
            results.push('   ❌ API endpoint returns 404 (not found)');
            results.push('   FIX: Check if backend server is running');
          } else {
            results.push('   ⚠️ API returned unexpected status: ' + statusCode);
          }
        } catch (e) {
          results.push('   ❌ Cannot reach API endpoint');
          results.push('   Error: ' + e.message);
          results.push('   FIX: Start backend server or update API_ENDPOINT in search_interface.gs');
        }
        
      } catch (e) {
        results.push('   ⚠️ Cannot read search criteria: ' + e.message);
        results.push('   This may indicate incorrect cell layout');
      }
    }
    
  } catch (e) {
    results.push('❌ ERROR: ' + e.message);
  }
  
  results.push('');
  
  // ============================================================================
  // TEST 5: OAuth Scopes
  // ============================================================================
  results.push('TEST 5: OAuth Scopes & Permissions');
  results.push('-'.repeat(80));
  
  // This will show what scopes are currently authorized
  try {
    // Test spreadsheet access
    var ss = SpreadsheetApp.getActiveSpreadsheet();
    results.push('✅ Spreadsheet access: OK');
    
    // Test UI access
    var ui = SpreadsheetApp.getUi();
    results.push('✅ UI access: OK');
    
    // Test UrlFetch (for external API calls)
    try {
      UrlFetchApp.fetch('https://www.google.com', { muteHttpExceptions: true });
      results.push('✅ UrlFetchApp access: OK');
    } catch (e) {
      results.push('❌ UrlFetchApp access: DENIED');
      results.push('   FIX: Add scope "https://www.googleapis.com/auth/script.external_request"');
    }
    
    // Test BigQuery (already tested above)
    results.push('✅ BigQuery access: Already tested above');
    
  } catch (e) {
    results.push('❌ Permission error: ' + e.message);
  }
  
  results.push('');
  results.push('='.repeat(80));
  results.push('DIAGNOSTIC COMPLETE');
  results.push('='.repeat(80));
  
  // Log results
  var output = results.join('\n');
  Logger.log(output);
  
  // Also show in UI
  var ui = SpreadsheetApp.getUi();
  ui.alert('Diagnostic Complete', 
           'See Execution Log (View > Logs) for full report.\n\n' +
           'Key checks:\n' +
           '• Maps API Key\n' +
           '• BigQuery Access\n' +
           '• HTML File Status\n' +
           '• Search Interface\n' +
           '• OAuth Permissions',
           ui.ButtonSet.OK);
  
  return output;
}

/**
 * Quick test: Open map sidebar and check for errors
 */
function testMapSidebarQuick() {
  try {
    var html = HtmlService.createHtmlOutputFromFile('map_sidebarh')
        .setTitle('GB Power Geographic Map')
        .setWidth(400);
    SpreadsheetApp.getUi().showSidebar(html);
    Logger.log('✅ Sidebar opened successfully');
    Logger.log('⚠️ Check browser console (F12) for JavaScript errors');
    Logger.log('   Look for: ApiNotActivatedMapError, RefererNotAllowedMapError');
  } catch (e) {
    Logger.log('❌ Error opening sidebar: ' + e.message);
  }
}

/**
 * Test Maps API URL directly
 */
function testMapsApiUrl() {
  var props = PropertiesService.getScriptProperties();
  var key = props.getProperty('GOOGLE_MAPS_API_KEY');
  
  if (!key) {
    Logger.log('❌ No API key set');
    return;
  }
  
  var url = 'https://maps.googleapis.com/maps/api/js?key=' + key + '&v=weekly';
  Logger.log('Testing URL: ' + url);
  
  try {
    var response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    var content = response.getContentText();
    var code = response.getResponseCode();
    
    Logger.log('Response code: ' + code);
    
    if (content.indexOf('ApiNotActivatedMapError') !== -1) {
      Logger.log('❌ Maps JavaScript API NOT ENABLED');
      Logger.log('FIX: https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9');
    } else if (content.indexOf('RefererNotAllowedMapError') !== -1) {
      Logger.log('❌ Domain restrictions blocking');
      Logger.log('FIX: https://console.cloud.google.com/apis/credentials?project=inner-cinema-476211-u9');
    } else if (content.indexOf('google.maps') !== -1) {
      Logger.log('✅ Maps API is working!');
    } else {
      Logger.log('⚠️ Unexpected response:');
      Logger.log(content.substring(0, 500));
    }
  } catch (e) {
    Logger.log('❌ Error: ' + e.message);
  }
}

/**
 * Test search function
 */
function testSearchFunction() {
  Logger.log('Testing search interface...');
  
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
  if (!sheet) {
    Logger.log('❌ Search sheet not found');
    return;
  }
  
  Logger.log('✅ Search sheet exists');
  
  // Test API endpoint
  var apiEndpoint = 'https://a92f6deceb5e.ngrok-free.app/search';
  Logger.log('Testing API: ' + apiEndpoint);
  
  try {
    var response = UrlFetchApp.fetch(apiEndpoint, {
      method: 'get',
      muteHttpExceptions: true
    });
    
    Logger.log('API Response code: ' + response.getResponseCode());
    
    if (response.getResponseCode() === 200) {
      Logger.log('✅ Search API is accessible');
    } else {
      Logger.log('⚠️ API returned: ' + response.getResponseCode());
    }
  } catch (e) {
    Logger.log('❌ Cannot reach search API: ' + e.message);
    Logger.log('FIX: Check if backend is running and update API_ENDPOINT');
  }
}
