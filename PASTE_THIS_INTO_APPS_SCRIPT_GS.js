/**
 * Geographic Map Sidebar for Google Sheets
 * Shows DNO boundaries and GSP regions on interactive map
 * Data sourced from BigQuery: neso_dno_boundaries, neso_gsp_boundaries
 * 
 * @OnlyCurrentDoc - Limits access to current spreadsheet only
 */

/**
 * Show map sidebar when user clicks menu item
 */
function showMapSidebar() {
  try {
    // Use V2 file to break cache
    var html = HtmlService.createHtmlOutputFromFile('map_sidebar_v2')
        .setTitle('GB Power Geographic Map')
        .setWidth(400);
    SpreadsheetApp.getUi().showSidebar(html);
  } catch (e) {
    SpreadsheetApp.getUi().alert('Error: ' + e.message + '\n\nPlease run the function again to authorize permissions.');
  }
}

/**
 * Get Google Maps API key from Script Properties
 * Set this via: File > Project Properties > Script Properties
 * Add key: GOOGLE_MAPS_API_KEY, value: your API key
 */
function getMapsApiKey() {
  var props = PropertiesService.getScriptProperties();
  var key = props.getProperty('GOOGLE_MAPS_API_KEY');
  
  if (!key) {
    Logger.log('⚠️ No GOOGLE_MAPS_API_KEY found in Script Properties');
  }
  
  return key;
}

/**
 * Fetch GeoJSON data from BigQuery for specified layer
 * @param {string} layer - 'dno' or 'gsp'
 * @returns {object} GeoJSON FeatureCollection
 */
function getGeoJson(layer) {
  var PROJECT_ID = 'inner-cinema-476211-u9';
  var DATASET = 'uk_energy_prod';
  
  var query;
  
  if (layer === 'dno') {
    // DNO boundaries - using PRE-COMPUTED simplified table (much faster!)
    query = `
      SELECT 
        dno_id,
        dno_full_name as dno_name,
        dno_code as dno_short_code,
        gsp_group as gsp_group_id,
        area_name as region_name,
        geojson_string as geometry_json
      FROM \`${PROJECT_ID}.${DATASET}.neso_dno_boundaries_simplified\`
    `;
  } else if (layer === 'gsp') {
    // GSP boundaries - using PRE-COMPUTED simplified table (much faster!)
    query = `
      SELECT 
        gsp_id,
        gsp_name,
        gsp_group,
        region_name,
        area_sqkm,
        geojson_string as geometry_json
      FROM \`${PROJECT_ID}.${DATASET}.neso_gsp_boundaries_simplified\`
      LIMIT 100
    `;
  } else {
    throw new Error('Invalid layer. Use "dno" or "gsp"');
  }
  
  try {
    // Run BigQuery query with timeout handling
    var request = {
      query: query,
      useLegacySql: false,
      location: 'US',
      timeoutMs: 20000, // 20 second timeout
      maxResults: 1000  // Limit results for safety
    };
    
    Logger.log('Starting BigQuery query for layer: ' + layer);
    var queryResults = BigQuery.Jobs.query(request, PROJECT_ID);
    
    // Check if query completed immediately
    if (!queryResults.jobComplete) {
      var jobId = queryResults.jobReference.jobId;
      Logger.log('Query not complete, job ID: ' + jobId);
      
      // Wait for query to complete (max 15 seconds total)
      var maxWaitTime = 15000; // 15 seconds
      var elapsedTime = 0;
      var sleepTimeMs = 500;
      
      while (!queryResults.jobComplete && elapsedTime < maxWaitTime) {
        Utilities.sleep(sleepTimeMs);
        elapsedTime += sleepTimeMs;
        sleepTimeMs = Math.min(sleepTimeMs * 1.5, 2000); // Cap at 2 seconds
        
        try {
          queryResults = BigQuery.Jobs.getQueryResults(PROJECT_ID, jobId);
        } catch (e) {
          Logger.log('Error getting query results: ' + e.toString());
          throw new Error('Query status check failed: ' + e.message);
        }
      }
      
      if (!queryResults.jobComplete) {
        throw new Error('Query timeout after ' + (elapsedTime/1000) + ' seconds');
      }
    }
    
    Logger.log('Query completed successfully');
    
    // Get results
    var rows = queryResults.rows;
    
    if (!rows || rows.length === 0) {
      Logger.log('⚠️ No rows returned for layer: ' + layer);
      return {
        type: 'FeatureCollection',
        features: []
      };
    }
    
    // Build GeoJSON FeatureCollection
    var features = [];
    
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var properties = {};
      var geometryJson = null;
      
      // Extract properties from row
      for (var j = 0; j < queryResults.schema.fields.length; j++) {
        var field = queryResults.schema.fields[j];
        var value = row.f[j].v;
        
        if (field.name === 'geometry_json') {
          geometryJson = value;
        } else {
          properties[field.name] = value;
        }
      }
      
      // Parse geometry JSON
      if (geometryJson) {
        var geometry = JSON.parse(geometryJson);
        
        features.push({
          type: 'Feature',
          properties: properties,
          geometry: geometry
        });
      }
    }
    
    Logger.log(`✅ Loaded ${features.length} ${layer} features`);
    
    return {
      type: 'FeatureCollection',
      features: features
    };
    
  } catch (e) {
    Logger.log('❌ Error fetching GeoJSON: ' + e.toString());
    throw new Error('BigQuery error: ' + e.message);
  }
}

/**
 * Get DNO regions in batches (for pagination)
 * @param {number} offset - Starting row number
 * @param {number} limit - Number of regions per batch
 * @returns {object} GeoJSON FeatureCollection
 */
function getDnoBatch(offset, limit) {
  var PROJECT_ID = 'inner-cinema-476211-u9';
  var DATASET = 'uk_energy_prod';
  
  var query = `
    SELECT 
      dno_id,
      dno_full_name as dno_name,
      dno_code as dno_short_code,
      gsp_group as gsp_group_id,
      area_name as region_name,
      geojson_string as geometry_json
    FROM \`${PROJECT_ID}.${DATASET}.neso_dno_boundaries_simplified\`
    ORDER BY dno_id
    LIMIT ${limit} OFFSET ${offset}
  `;
  
  try {
    var request = {
      query: query,
      useLegacySql: false,
      location: 'US'
    };
    
    var queryResults = BigQuery.Jobs.query(request, PROJECT_ID);
    var jobId = queryResults.jobReference.jobId;
    
    // Wait for query to complete
    var sleepTimeMs = 500;
    var maxWait = 15000; // 15 seconds max
    var totalWait = 0;
    
    while (!queryResults.jobComplete && totalWait < maxWait) {
      Utilities.sleep(sleepTimeMs);
      totalWait += sleepTimeMs;
      sleepTimeMs = Math.min(sleepTimeMs * 2, 5000);
      queryResults = BigQuery.Jobs.getQueryResults(PROJECT_ID, jobId);
    }
    
    if (!queryResults.jobComplete) {
      throw new Error('Query timeout after ' + (totalWait/1000) + ' seconds');
    }
    
    var rows = queryResults.rows;
    
    if (!rows || rows.length === 0) {
      return {
        type: 'FeatureCollection',
        features: [],
        hasMore: false
      };
    }
    
    var features = [];
    
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i];
      var properties = {};
      var geometryJson = null;
      
      for (var j = 0; j < queryResults.schema.fields.length; j++) {
        var field = queryResults.schema.fields[j];
        var value = row.f[j].v;
        
        if (field.name === 'geometry_json') {
          geometryJson = value;
        } else {
          properties[field.name] = value;
        }
      }
      
      if (geometryJson) {
        var geometry = JSON.parse(geometryJson);
        features.push({
          type: 'Feature',
          properties: properties,
          geometry: geometry
        });
      }
    }
    
    Logger.log(`✅ Batch loaded ${features.length} DNO features (offset ${offset})`);
    
    return {
      type: 'FeatureCollection',
      features: features,
      hasMore: rows.length === limit // If we got full batch, there might be more
    };
    
  } catch (e) {
    Logger.log('❌ Error in getDnoBatch: ' + e.toString());
    throw e;
  }
}

/**
 * Add menu item to show map
 * This should be added to MASTER_onOpen.gs or called from there
 */
function addMapMenuItem() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Geographic Map')
      .addItem('Show DNO & GSP Boundaries', 'showMapSidebar')
      .addToUi();
}

/**
 * Test function - run this to verify BigQuery access
 */
function testGeoJsonFetch() {
  Logger.log('Testing DNO GeoJSON fetch...');
  try {
    var dnoData = getGeoJson('dno');
    Logger.log('✅ DNO features: ' + dnoData.features.length);
    return {success: true, count: dnoData.features.length, message: 'DNO loaded successfully'};
  } catch (e) {
    Logger.log('❌ DNO Error: ' + e.toString());
    Logger.log('   Stack: ' + e.stack);
    return {success: false, error: e.toString(), stack: e.stack};
  }
}

/**
 * Simple function that ALWAYS succeeds - for testing HTML communication
 */
function testSimpleReturn() {
  Logger.log('testSimpleReturn called from HTML');
  return {
    success: true,
    message: "Hello from Apps Script!",
    timestamp: new Date().toISOString()
  };
}

/**
 * Test search API connection
 * Tests if UrlFetchApp can reach the ngrok endpoint
 */
function testSearchAPI() {
  var API_ENDPOINT = 'https://a92f6deceb5e.ngrok-free.app/search';
  
  try {
    Logger.log('Testing API connection to: ' + API_ENDPOINT);
    
    var options = {
      method: 'get',
      muteHttpExceptions: true,
      headers: {
        'ngrok-skip-browser-warning': 'true'
      }
    };
    
    // Test health endpoint
    var healthUrl = API_ENDPOINT.replace('/search', '/health');
    var response = UrlFetchApp.fetch(healthUrl, options);
    var statusCode = response.getResponseCode();
    var body = response.getContentText();
    
    Logger.log('✅ Response Code: ' + statusCode);
    Logger.log('✅ Response Body: ' + body);
    
    if (statusCode === 200) {
      return {
        success: true,
        message: 'API Connection Successful!',
        statusCode: statusCode,
        body: body
      };
    } else {
      return {
        success: false,
        message: 'API returned status ' + statusCode,
        statusCode: statusCode,
        body: body
      };
    }
  } catch (e) {
    Logger.log('❌ Connection Failed: ' + e.message);
    return {
      success: false,
      message: 'Connection Failed',
      error: e.message,
      endpoint: API_ENDPOINT
    };
  }
}

/**
 * Diagnostic test - checks BigQuery service availability
 */
function testBigQueryService() {
  var PROJECT_ID = 'inner-cinema-476211-u9';
  
  Logger.log('='.repeat(60));
  Logger.log('BIGQUERY SERVICE DIAGNOSTIC TEST');
  Logger.log('='.repeat(60));
  
  // Test 1: Check if BigQuery service is available
  Logger.log('\n[Test 1] Checking BigQuery Advanced Service...');
  if (typeof BigQuery === 'undefined') {
    Logger.log('❌ FAIL: BigQuery service not enabled!');
    Logger.log('   Go to: Resources > Advanced Google Services');
    Logger.log('   Enable: BigQuery API v2');
    return;
  }
  Logger.log('✅ PASS: BigQuery service is available');
  
  // Test 2: Simple query test
  Logger.log('\n[Test 2] Testing simple query...');
  try {
    var simpleQuery = 'SELECT 1 as test';
    var request = {
      query: simpleQuery,
      useLegacySql: false,
      timeoutMs: 10000
    };
    
    var result = BigQuery.Jobs.query(request, PROJECT_ID);
    
    if (result && result.jobComplete) {
      Logger.log('✅ PASS: Simple query executed');
    } else {
      Logger.log('⚠️ WARNING: Query started but not complete');
    }
  } catch (e) {
    Logger.log('❌ FAIL: ' + e.toString());
    Logger.log('   Error details: ' + JSON.stringify(e));
    return;
  }
  
  // Test 3: Check simplified table exists
  Logger.log('\n[Test 3] Checking simplified DNO table...');
  try {
    var checkQuery = 'SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries_simplified`';
    var request = {
      query: checkQuery,
      useLegacySql: false,
      timeoutMs: 10000
    };
    
    var result = BigQuery.Jobs.query(request, PROJECT_ID);
    
    if (result && result.jobComplete && result.rows) {
      var count = result.rows[0].f[0].v;
      Logger.log('✅ PASS: Simplified DNO table exists with ' + count + ' rows');
    } else {
      Logger.log('⚠️ WARNING: Table check incomplete');
    }
  } catch (e) {
    Logger.log('❌ FAIL: ' + e.toString());
    Logger.log('   The simplified table may not exist');
    Logger.log('   Run: python3 create_simplified_boundaries.py');
    return;
  }
  
  // Test 4: Fetch actual data
  Logger.log('\n[Test 4] Fetching 1 DNO region...');
  try {
    var dataQuery = `
      SELECT 
        dno_id,
        dno_full_name,
        geojson_string
      FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries_simplified\`
      LIMIT 1
    `;
    var request = {
      query: dataQuery,
      useLegacySql: false,
      timeoutMs: 15000
    };
    
    var result = BigQuery.Jobs.query(request, PROJECT_ID);
    
    if (result && result.jobComplete && result.rows && result.rows.length > 0) {
      var row = result.rows[0];
      var dnoId = row.f[0].v;
      var dnoName = row.f[1].v;
      var geojsonLen = row.f[2].v ? row.f[2].v.length : 0;
      
      Logger.log('✅ PASS: Retrieved data successfully');
      Logger.log('   DNO ID: ' + dnoId);
      Logger.log('   DNO Name: ' + dnoName);
      Logger.log('   GeoJSON length: ' + geojsonLen + ' characters');
      
      if (geojsonLen === 0) {
        Logger.log('⚠️ WARNING: GeoJSON string is empty!');
      }
    } else {
      Logger.log('❌ FAIL: No data returned');
    }
  } catch (e) {
    Logger.log('❌ FAIL: ' + e.toString());
    Logger.log('   Full error: ' + JSON.stringify(e));
  }
  
  Logger.log('\n' + '='.repeat(60));
  Logger.log('DIAGNOSTIC COMPLETE - Review results above');
  Logger.log('='.repeat(60));
}

/**
 * Simple test - just check if API key retrieval works
 */
function testApiKeySimple() {
  Logger.log('Testing getMapsApiKey()...');
  try {
    var key = getMapsApiKey();
    if (key) {
      Logger.log('✅ SUCCESS: API key retrieved: ' + key.substring(0, 20) + '...');
      Logger.log('Key length: ' + key.length + ' characters');
      
      // Also test if we can call it from UI
      SpreadsheetApp.getUi().alert('✅ API Key Test Passed\n\n' +
                                   'Key: ' + key.substring(0, 25) + '...\n' +
                                   'Length: ' + key.length + ' chars\n\n' +
                                   'Try createDebugSidebar() again now.');
    } else {
      Logger.log('❌ FAIL: No key returned');
      SpreadsheetApp.getUi().alert('❌ No API key found\n\nCheck Script Properties');
    }
  } catch (e) {
    Logger.log('❌ ERROR: ' + e.message);
    SpreadsheetApp.getUi().alert('❌ Error: ' + e.message);
  }
}

/**
 * Debug sidebar - shows exactly what's happening with map loading
 */
function createDebugSidebar() {
  var html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <title>Map Debug Test</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    #status { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px; font-weight: bold; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
    button { padding: 10px 20px; margin: 10px 0; font-size: 14px; cursor: pointer; }
    #log { margin-top: 20px; font-family: monospace; font-size: 11px; max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
  </style>
</head>
<body>
  <h2>🔍 Map Debug Test</h2>
  <div id="status">⏳ Ready to test...</div>
  <button onclick="testMapLoad()" style="background:#4285f4; color:white; border:none; border-radius:4px;">🚀 Start Map Test</button>
  <div id="log"></div>
  
  <script>
    let logDiv = document.getElementById('log');
    let statusDiv = document.getElementById('status');
    
    function log(msg, type = 'info') {
      console.log(msg);
      const timestamp = new Date().toLocaleTimeString();
      const color = type === 'error' ? 'red' : type === 'success' ? 'green' : 'blue';
      logDiv.innerHTML += '<div style="color:' + color + '; margin: 2px 0;">[' + timestamp + '] ' + msg + '</div>';
      logDiv.scrollTop = logDiv.scrollHeight;
    }
    
    function testMapLoad() {
      log('═══════════════════════════════════════════', 'info');
      log('🔍 STARTING MAP DIAGNOSTIC TEST', 'info');
      log('═══════════════════════════════════════════', 'info');
      statusDiv.innerHTML = '⏳ Running diagnostic...';
      logDiv.innerHTML = '';
      
      // Test 1: Check google.script.run
      log('', 'info');
      log('[TEST 1] Checking Apps Script API...', 'info');
      if (typeof google !== 'undefined' && google.script && google.script.run) {
        log('✅ google.script.run is available', 'success');
      } else {
        log('❌ google.script.run NOT available (critical error)', 'error');
        statusDiv.innerHTML = '❌ Apps Script API not available';
        return;
      }
      
      // Test 2: Get API key
      log('', 'info');
      log('[TEST 2] Requesting Maps API key from Script Properties...', 'info');
      google.script.run
        .withSuccessHandler((key) => {
          if (!key) {
            log('❌ No API key returned (check Script Properties)', 'error');
            statusDiv.innerHTML = '❌ No API key found';
            return;
          }
          log('✅ API key received: ' + key.substring(0, 25) + '...', 'success');
          
          // Test 3: Load Maps API
          log('', 'info');
          log('[TEST 3] Loading Google Maps JavaScript API...', 'info');
          log('   Building script URL...', 'info');
          const scriptUrl = 'https://maps.googleapis.com/maps/api/js?key=' + key + '&callback=onMapsApiLoaded&v=weekly';
          log('   URL: ' + scriptUrl.substring(0, 80) + '...', 'info');
          
          const script = document.createElement('script');
          script.src = scriptUrl;
          script.async = true;
          script.defer = true;
          
          script.onload = () => {
            log('✅ Maps API script loaded (onload event fired)', 'success');
          };
          
          script.onerror = (e) => {
            log('❌ Maps API script failed to load (network error or CORS issue)', 'error');
            log('   Check browser console for detailed error', 'error');
            statusDiv.innerHTML = '❌ Maps API script load failed';
          };
          
          document.head.appendChild(script);
          log('✅ Script tag added to document head', 'success');
          log('   Waiting for Maps API to initialize...', 'info');
          statusDiv.innerHTML = '⏳ Loading Maps JavaScript API...';
        })
        .withFailureHandler((err) => {
          log('❌ Error calling getMapsApiKey(): ' + err.message, 'error');
          statusDiv.innerHTML = '❌ Error: ' + err.message;
        })
        .getMapsApiKey();
    }
    
    // Callback when Maps API successfully loads
    window.onMapsApiLoaded = function() {
      log('', 'info');
      log('[TEST 4] Maps API callback fired!', 'info');
      log('✅ google.maps object exists: ' + (typeof google.maps !== 'undefined'), 'success');
      log('✅ google.maps.Map exists: ' + (typeof google.maps.Map !== 'undefined'), 'success');
      
      // Test 4: Create a map
      log('', 'info');
      log('[TEST 5] Creating test map...', 'info');
      try {
        const mapDiv = document.createElement('div');
        mapDiv.id = 'test-map';
        mapDiv.style.width = '100%';
        mapDiv.style.height = '200px';
        mapDiv.style.border = '2px solid #4285f4';
        mapDiv.style.marginTop = '10px';
        document.body.appendChild(mapDiv);
        
        const map = new google.maps.Map(mapDiv, {
          center: { lat: 54.5, lng: -3.5 },
          zoom: 6,
          mapTypeId: 'roadmap'
        });
        
        log('✅ Map object created successfully!', 'success');
        log('✅ Map center: 54.5°N, 3.5°W (UK)', 'success');
        log('✅ Map zoom level: 6', 'success');
        
        // Add a marker
        const marker = new google.maps.Marker({
          position: { lat: 54.5, lng: -3.5 },
          map: map,
          title: 'Test Marker - GB Center'
        });
        log('✅ Test marker added to map', 'success');
        
        statusDiv.innerHTML = '✅ SUCCESS! Maps API fully working!';
        log('', 'info');
        log('═══════════════════════════════════════════', 'success');
        log('🎉 ALL TESTS PASSED - MAPS API WORKING!', 'success');
        log('═══════════════════════════════════════════', 'success');
        log('', 'info');
        log('📋 NEXT STEPS:', 'info');
        log('1. The main sidebar should now work', 'info');
        log('2. Try: Menu > 🗺️ Geographic Map > Show DNO & GSP Boundaries', 'info');
        log('3. If still not working, copy ALL console messages (F12 > Console)', 'info');
        
      } catch (e) {
        log('❌ Error creating map: ' + e.message, 'error');
        log('   Error stack: ' + (e.stack || 'not available'), 'error');
        statusDiv.innerHTML = '❌ Error creating map';
      }
    };
    
    // Auto-start test after 1 second
    log('Page loaded. Click "Start Map Test" button or wait for auto-start...', 'info');
    setTimeout(() => {
      log('🚀 Auto-starting diagnostic in 1 second...', 'info');
      testMapLoad();
    }, 1000);
  </script>
</body>
</html>
  `)
    .setTitle('🔍 Map Debug Test')
    .setWidth(500);
  
  SpreadsheetApp.getUi().showSidebar(html);
  Logger.log('✅ Debug sidebar opened');
  Logger.log('📋 Watch the debug output in the sidebar');
  Logger.log('📋 Also check browser console (F12) for any additional errors');
}
