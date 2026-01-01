/**
 * QUICK FIX TEST - Run this in Apps Script to diagnose sidebar issue
 */

function testMapSidebarDetailed() {
  Logger.log('='.repeat(80));
  Logger.log('DETAILED MAP SIDEBAR TEST');
  Logger.log('='.repeat(80));
  
  // Test 1: Check API key
  Logger.log('\n[1] Testing API key retrieval...');
  var props = PropertiesService.getScriptProperties();
  var key = props.getProperty('GOOGLE_MAPS_API_KEY');
  
  if (!key) {
    Logger.log('❌ FAIL: No API key found!');
    Logger.log('FIX: Set GOOGLE_MAPS_API_KEY in Script Properties');
    return;
  }
  
  Logger.log('✅ API key found: ' + key.substring(0, 20) + '...');
  
  // Test 2: Check BigQuery
  Logger.log('\n[2] Testing BigQuery access...');
  try {
    var dnoQuery = {
      query: 'SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`',
      useLegacySql: false,
      location: 'US'
    };
    var result = BigQuery.Jobs.query(dnoQuery, 'inner-cinema-476211-u9');
    Logger.log('✅ BigQuery working: ' + result.rows[0].f[0].v + ' DNO regions');
  } catch (e) {
    Logger.log('❌ BigQuery error: ' + e.message);
  }
  
  // Test 3: Check HTML file
  Logger.log('\n[3] Testing HTML file...');
  try {
    var html = HtmlService.createHtmlOutputFromFile('map_sidebarh');
    var content = html.getContent();
    Logger.log('✅ HTML file exists: ' + content.length + ' characters');
    
    // Check for key elements
    var hasInitMap = content.indexOf('function initMap()') > -1;
    var hasLoadLayer = content.indexOf('function loadLayer') > -1;
    var hasGetMapsApiKey = content.indexOf('getMapsApiKey') > -1;
    var hasGoogleMaps = content.indexOf('google.maps') > -1;
    
    Logger.log('  - initMap() function: ' + (hasInitMap ? '✅' : '❌'));
    Logger.log('  - loadLayer() function: ' + (hasLoadLayer ? '✅' : '❌'));
    Logger.log('  - getMapsApiKey() call: ' + (hasGetMapsApiKey ? '✅' : '❌'));
    Logger.log('  - google.maps references: ' + (hasGoogleMaps ? '✅' : '❌'));
    
    // Check if callback is set correctly
    var hasCallback = content.indexOf('callback=initMap') > -1;
    Logger.log('  - Maps API callback set: ' + (hasCallback ? '✅' : '❌'));
    
  } catch (e) {
    Logger.log('❌ HTML file error: ' + e.message);
  }
  
  // Test 4: Test Maps API URL (should work since curl succeeded)
  Logger.log('\n[4] Testing Maps API endpoint from Apps Script...');
  try {
    var testUrl = 'https://maps.googleapis.com/maps/api/js?key=' + key + '&v=weekly';
    var response = UrlFetchApp.fetch(testUrl, {
      muteHttpExceptions: true,
      followRedirects: true
    });
    
    var code = response.getResponseCode();
    var content = response.getContentText();
    
    Logger.log('Response code: ' + code);
    
    if (code === 200 && content.indexOf('google.maps') > -1) {
      Logger.log('✅ Maps API responds correctly');
    } else if (content.indexOf('RefererNotAllowedMapError') > -1) {
      Logger.log('⚠️ WARNING: Referrer restrictions detected');
      Logger.log('   Your API key may block script.google.com');
      Logger.log('   FIX: Remove referrer restrictions on API key');
    } else {
      Logger.log('⚠️ Unexpected response (first 200 chars):');
      Logger.log(content.substring(0, 200));
    }
  } catch (e) {
    Logger.log('❌ UrlFetch error: ' + e.message);
  }
  
  // Test 5: Open sidebar and check
  Logger.log('\n[5] Opening sidebar...');
  try {
    var html = HtmlService.createHtmlOutputFromFile('map_sidebarh')
        .setTitle('GB Power Geographic Map')
        .setWidth(400);
    SpreadsheetApp.getUi().showSidebar(html);
    Logger.log('✅ Sidebar opened successfully');
    Logger.log('');
    Logger.log('🔍 NOW CHECK IN GOOGLE SHEETS:');
    Logger.log('   1. Sidebar should be visible on right side');
    Logger.log('   2. Press F12 to open browser Developer Tools');
    Logger.log('   3. Go to Console tab');
    Logger.log('   4. Look for ANY errors (red text)');
    Logger.log('   5. Try clicking "Show DNO Regions" button');
    Logger.log('   6. Watch console for errors when clicking');
    Logger.log('');
    Logger.log('📋 Copy ANY console errors and share them!');
  } catch (e) {
    Logger.log('❌ Failed to open sidebar: ' + e.message);
  }
  
  Logger.log('\n' + '='.repeat(80));
  Logger.log('TEST COMPLETE - Check Google Sheets browser console (F12)');
  Logger.log('='.repeat(80));
}

/**
 * Alternative: Create debug version with console logging
 */
function createDebugSidebar() {
  var html = HtmlService.createHtmlOutput(`
<!DOCTYPE html>
<html>
<head>
  <title>Map Debug Test</title>
  <style>
    body { font-family: Arial; padding: 20px; }
    #status { background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px; }
    .success { color: green; }
    .error { color: red; }
    .info { color: blue; }
  </style>
</head>
<body>
  <h3>🔍 Map Debug Test</h3>
  <div id="status">Initializing...</div>
  <button onclick="testMapLoad()">Test Map Load</button>
  <div id="log" style="margin-top: 20px; font-family: monospace; font-size: 11px;"></div>
  
  <script>
    let logDiv = document.getElementById('log');
    let statusDiv = document.getElementById('status');
    
    function log(msg, type = 'info') {
      console.log(msg);
      const color = type === 'error' ? 'red' : type === 'success' ? 'green' : 'blue';
      logDiv.innerHTML += '<div style="color:' + color + '">' + msg + '</div>';
    }
    
    function testMapLoad() {
      log('🔍 Starting map load test...', 'info');
      statusDiv.innerHTML = '⏳ Testing...';
      
      // Test 1: Check if google.script.run is available
      if (typeof google !== 'undefined' && google.script && google.script.run) {
        log('✅ google.script.run available', 'success');
      } else {
        log('❌ google.script.run NOT available', 'error');
        statusDiv.innerHTML = '❌ Apps Script API not available';
        return;
      }
      
      // Test 2: Try to get API key
      log('📡 Requesting Maps API key...', 'info');
      google.script.run
        .withSuccessHandler((key) => {
          if (!key) {
            log('❌ No API key returned', 'error');
            statusDiv.innerHTML = '❌ No API key in Script Properties';
            return;
          }
          log('✅ API key received: ' + key.substring(0, 20) + '...', 'success');
          
          // Test 3: Try to load Maps API
          log('📡 Loading Maps JavaScript API...', 'info');
          const script = document.createElement('script');
          script.src = 'https://maps.googleapis.com/maps/api/js?key=' + key + '&callback=onMapsLoaded&v=weekly';
          script.async = true;
          script.defer = true;
          script.onerror = () => {
            log('❌ Failed to load Maps API script', 'error');
            statusDiv.innerHTML = '❌ Maps API script failed to load';
          };
          document.head.appendChild(script);
          log('✅ Maps API script tag added to page', 'success');
          statusDiv.innerHTML = '⏳ Loading Maps API...';
        })
        .withFailureHandler((err) => {
          log('❌ Error getting API key: ' + err.message, 'error');
          statusDiv.innerHTML = '❌ Error: ' + err.message;
        })
        .getMapsApiKey();
    }
    
    // Callback when Maps API loads
    window.onMapsLoaded = function() {
      log('✅ Maps API loaded successfully!', 'success');
      log('✅ google.maps object available: ' + (typeof google.maps !== 'undefined'), 'success');
      statusDiv.innerHTML = '✅ Maps API working!';
      
      // Check if we can create a map
      try {
        const mapDiv = document.createElement('div');
        mapDiv.style.width = '100%';
        mapDiv.style.height = '200px';
        document.body.appendChild(mapDiv);
        
        const map = new google.maps.Map(mapDiv, {
          center: { lat: 54.5, lng: -3.5 },
          zoom: 6
        });
        log('✅ Map created successfully!', 'success');
      } catch (e) {
        log('❌ Error creating map: ' + e.message, 'error');
      }
    };
    
    // Auto-start test on page load
    setTimeout(() => {
      log('🚀 Page loaded, starting auto-test...', 'info');
      testMapLoad();
    }, 500);
  </script>
</body>
</html>
  `)
    .setTitle('Map Debug Test')
    .setWidth(400);
  
  SpreadsheetApp.getUi().showSidebar(html);
  Logger.log('✅ Debug sidebar opened - check browser console');
}
