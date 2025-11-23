/**
 * GB Power Market - Automatic Map Updates for Google Sheets
 * ===========================================================
 * This Apps Script automatically:
 * 1. Fetches map data from BigQuery via your existing API
 * 2. Generates static map images using Google Maps Static API
 * 3. Inserts them into Dashboard sheet using IMAGE() formulas
 * 
 * Setup:
 * 1. Extensions → Apps Script → Paste this code
 * 2. Run updateMapsInDashboard() to test
 * 3. Set up time-based trigger: Edit → Current project's triggers → Add trigger
 *    - Function: updateMapsInDashboard
 *    - Event source: Time-driven
 *    - Type: Hour timer
 *    - Every 6 hours (or your preference)
 */

// ============================================================================
// Configuration
// ============================================================================

const CONFIG = {
  RAILWAY_API: 'https://jibber-jabber-production.up.railway.app',
  VERCEL_API: 'https://gb-power-market-jj.vercel.app/api/proxy-v2',
  DASHBOARD_SHEET: 'Dashboard',
  
  // Map positions in Dashboard sheet
  MAPS: {
    GENERATORS: { row: 20, col: 10 },  // J20
    GSP_REGIONS: { row: 36, col: 10 },  // J36
    TRANSMISSION: { row: 52, col: 10 }  // J52
  }
};

// ============================================================================
// Data Fetching from BigQuery
// ============================================================================

/**
 * Query BigQuery via Vercel proxy
 */
function queryBigQuery(sql) {
  try {
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify({ sql: sql }),
      muteHttpExceptions: true
    };
    
    const response = UrlFetchApp.fetch(CONFIG.VERCEL_API + '?path=/query_bigquery_get', options);
    const data = JSON.parse(response.getContentText());
    
    if (data.error) {
      Logger.log('BigQuery error: ' + data.error);
      return null;
    }
    
    return data.results || data.rows || [];
  } catch (e) {
    Logger.log('Query failed: ' + e.toString());
    return null;
  }
}

/**
 * Get SVA generators with coordinates
 */
function getGenerators() {
  const sql = `
    SELECT 
      name as generator_name,
      technology,
      capacity_mw,
      lat as latitude,
      lng as longitude,
      fuel_type
    FROM \`inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords\`
    WHERE lat IS NOT NULL 
      AND lng IS NOT NULL
      AND capacity_mw > 1
    LIMIT 500
  `;
  
  return queryBigQuery(sql);
}

/**
 * Get GSP group summary
 */
function getGSPSummary() {
  const sql = `
    SELECT 
      gspgroupid as gsp_group,
      gspgroupname as gsp_name,
      COUNT(DISTINCT nationalgridbmunit) as num_generators,
      ROUND(SUM(generationcapacity), 0) as total_capacity_mw
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data\`
    WHERE gspgroupid IS NOT NULL
      AND generationcapacity > 0
    GROUP BY gspgroupid, gspgroupname
    ORDER BY total_capacity_mw DESC
    LIMIT 14
  `;
  
  return queryBigQuery(sql);
}

/**
 * Get transmission boundary generation
 */
function getTransmissionBoundaries() {
  const sql = `
    WITH latest AS (
      SELECT MAX(settlementDate) as max_date
      FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris\`
    )
    SELECT 
      boundary,
      ROUND(AVG(generation), 0) as avg_generation_mw
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris\`
    CROSS JOIN latest
    WHERE DATE(settlementDate) = DATE(latest.max_date)
      AND boundary != 'N'
    GROUP BY boundary
    ORDER BY avg_generation_mw DESC
    LIMIT 10
  `;
  
  return queryBigQuery(sql);
}

// ============================================================================
// Google Maps Static API Integration
// ============================================================================

/**
 * Generate Google Maps Static API URL for generators
 */
function generateGeneratorsMapURL(generators) {
  // Group generators by fuel type
  const fuelColors = {
    'Wind': '0x00a86b',
    'Solar': '0xffd700',
    'Hydro': '0x4169e1',
    'Gas': '0xffa500',
    'Nuclear': '0xff6b6b',
    'Battery': '0x9400d3',
    'Biomass': '0x9acd32',
    'Other': '0x808080'
  };
  
  let markers = [];
  
  // Add up to 100 generators (API limit)
  for (let i = 0; i < Math.min(generators.length, 100); i++) {
    const gen = generators[i];
    const fuel = gen.fuel_type || 'Other';
    const color = fuelColors[fuel] ? fuelColors[fuel].replace('0x', '') : '808080';
    
    // size: tiny, small, mid (default)
    const size = gen.capacity_mw > 50 ? 'mid' : gen.capacity_mw > 10 ? 'small' : 'tiny';
    
    markers.push(`color:0x${color}|size:${size}|${gen.latitude},${gen.longitude}`);
  }
  
  const baseUrl = 'https://maps.googleapis.com/maps/api/staticmap';
  const params = [
    'center=54.5,-3.5',  // UK center
    'zoom=6',
    'size=600x400',
    'maptype=roadmap',
    'style=feature:poi|visibility:off',  // Hide points of interest for cleaner map
    markers.slice(0, 50).map(m => 'markers=' + encodeURIComponent(m)).join('&')  // Limit to 50 markers
  ];
  
  // Note: You need a Google Maps API key
  // Get one at: https://console.cloud.google.com/apis/credentials
  const apiKey = PropertiesService.getScriptProperties().getProperty('GOOGLE_MAPS_API_KEY');
  
  if (!apiKey) {
    Logger.log('⚠️ Google Maps API key not set. Run setupMapsAPIKey() first.');
    return null;
  }
  
  return baseUrl + '?' + params.join('&') + '&key=' + apiKey;
}

/**
 * Generate static map URL for GSP regions
 */
function generateGSPMapURL(gspData) {
  const gspCenters = {
    '_A': [51.5, -0.1],   // Eastern
    '_B': [52.5, 1.0],    // East Anglia
    '_C': [51.3, -0.8],   // South East
    '_D': [51.0, -1.3],   // Southern
    '_E': [50.8, -1.8],   // South Western
    '_F': [52.3, -1.5],   // West Midlands
    '_G': [52.8, -2.0],   // North West
    '_H': [54.0, -2.0],   // Cumbria
    '_J': [53.8, -1.5],   // Yorkshire
    '_K': [54.5, -1.5],   // North East
    '_L': [55.8, -4.2],   // South Scotland
    '_M': [56.5, -3.5],   // Mid Scotland
    '_N': [57.5, -4.0],   // North Scotland
    '_P': [51.5, -3.0]    // South Wales
  };
  
  const colors = ['red', 'green', 'yellow', 'blue', 'orange', 'purple', 'pink'];
  let markers = [];
  
  gspData.forEach((gsp, idx) => {
    const gspId = gsp.gsp_group;
    if (gspCenters[gspId]) {
      const coords = gspCenters[gspId];
      const color = colors[idx % colors.length];
      const size = gsp.total_capacity_mw > 10000 ? 'mid' : 'small';
      
      markers.push(`color:${color}|size:${size}|label:${gspId.replace('_', '')}|${coords[0]},${coords[1]}`);
    }
  });
  
  const apiKey = PropertiesService.getScriptProperties().getProperty('GOOGLE_MAPS_API_KEY');
  
  if (!apiKey) return null;
  
  const baseUrl = 'https://maps.googleapis.com/maps/api/staticmap';
  const params = [
    'center=54.5,-3.5',
    'zoom=6',
    'size=600x400',
    'maptype=roadmap',
    markers.map(m => 'markers=' + encodeURIComponent(m)).join('&')
  ];
  
  return baseUrl + '?' + params.join('&') + '&key=' + apiKey;
}

// ============================================================================
// Alternative: Use Chart API for Simple Maps
// ============================================================================

/**
 * Generate map using Google Charts API (no API key needed!)
 */
function generateChartMapURL(generators) {
  // Google Charts can create simple maps
  // Format: https://chart.googleapis.com/chart?cht=map&chs=600x400&chd=t:lat1,lat2|lon1,lon2
  
  const lats = generators.slice(0, 100).map(g => g.latitude).join(',');
  const lons = generators.slice(0, 100).map(g => g.longitude).join(',');
  
  return `https://chart.googleapis.com/chart?cht=map&chs=600x400&chd=t:${lats}|${lons}`;
}

/**
 * Generate simple visualization using Google Charts
 */
function generateSimpleMapVisualization(data, title) {
  // Create a simple scatter chart that looks like a map
  const baseUrl = 'https://quickchart.io/chart';
  
  const config = {
    type: 'scatter',
    data: {
      datasets: [{
        label: title,
        data: data.slice(0, 50).map(d => ({
          x: d.longitude || d.lng,
          y: d.latitude || d.lat
        })),
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgba(54, 162, 235, 1)',
        pointRadius: 5
      }]
    },
    options: {
      title: { display: true, text: title },
      scales: {
        xAxes: [{ scaleLabel: { display: true, labelString: 'Longitude' }}],
        yAxes: [{ scaleLabel: { display: true, labelString: 'Latitude' }}]
      }
    }
  };
  
  return baseUrl + '?c=' + encodeURIComponent(JSON.stringify(config)) + '&w=600&h=400';
}

// ============================================================================
// Sheet Update Functions
// ============================================================================

/**
 * Update Dashboard with map images
 */
function updateMapsInDashboard() {
  Logger.log('🗺️ Starting map update...');
  
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dashboard = ss.getSheetByName(CONFIG.DASHBOARD_SHEET);
  
  if (!dashboard) {
    Logger.log('❌ Dashboard sheet not found');
    return;
  }
  
  try {
    // Fetch data
    Logger.log('📊 Fetching data from BigQuery...');
    const generators = getGenerators();
    const gspData = getGSPSummary();
    const boundaries = getTransmissionBoundaries();
    
    if (!generators || generators.length === 0) {
      Logger.log('⚠️ No generator data received');
      return;
    }
    
    Logger.log(`✅ Loaded ${generators.length} generators, ${gspData ? gspData.length : 0} GSP groups`);
    
    // Generate map URLs using QuickChart (no API key needed)
    const genMapUrl = generateSimpleMapVisualization(generators, 'GB Generators');
    
    // Update cells with IMAGE formulas
    const maps = CONFIG.MAPS;
    
    // Generators Map
    dashboard.getRange(maps.GENERATORS.row, maps.GENERATORS.col - 1).setValue('🗺️ Generators Map');
    dashboard.getRange(maps.GENERATORS.row, maps.GENERATORS.col).setFormula(
      `=IMAGE("${genMapUrl}", 4, 500, 350)`
    );
    dashboard.getRange(maps.GENERATORS.row, maps.GENERATORS.col + 1).setValue(
      `${generators.length} generators | Updated: ${new Date().toLocaleString()}`
    );
    
    // GSP Regions Map
    if (gspData && gspData.length > 0) {
      const gspMapUrl = generateGSPMapURL(gspData);
      
      if (gspMapUrl) {
        dashboard.getRange(maps.GSP_REGIONS.row, maps.GSP_REGIONS.col - 1).setValue('🗺️ GSP Regions');
        dashboard.getRange(maps.GSP_REGIONS.row, maps.GSP_REGIONS.col).setFormula(
          `=IMAGE("${gspMapUrl}", 4, 500, 350)`
        );
        dashboard.getRange(maps.GSP_REGIONS.row, maps.GSP_REGIONS.col + 1).setValue(
          `${gspData.length} regions | ${gspData.reduce((sum, g) => sum + (g.total_capacity_mw || 0), 0).toLocaleString()} MW`
        );
      }
    }
    
    // Transmission Map (data table for now)
    if (boundaries && boundaries.length > 0) {
      dashboard.getRange(maps.TRANSMISSION.row, maps.TRANSMISSION.col - 1).setValue('⚡ Transmission Boundaries');
      
      // Create a simple data table
      let tableData = [['Boundary', 'Generation (MW)']];
      boundaries.slice(0, 10).forEach(b => {
        tableData.push([b.boundary, b.avg_generation_mw]);
      });
      
      dashboard.getRange(
        maps.TRANSMISSION.row, 
        maps.TRANSMISSION.col, 
        tableData.length, 
        2
      ).setValues(tableData);
    }
    
    Logger.log('✅ Maps updated successfully!');
    
  } catch (e) {
    Logger.log('❌ Error updating maps: ' + e.toString());
    Logger.log(e.stack);
  }
}

/**
 * Setup Google Maps API key (one-time setup)
 */
function setupMapsAPIKey() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.prompt(
    'Google Maps API Key Setup',
    'Enter your Google Maps API key (get one at https://console.cloud.google.com/apis/credentials):',
    ui.ButtonSet.OK_CANCEL
  );
  
  if (response.getSelectedButton() == ui.Button.OK) {
    const apiKey = response.getResponseText();
    PropertiesService.getScriptProperties().setProperty('GOOGLE_MAPS_API_KEY', apiKey);
    ui.alert('✅ API key saved! You can now run updateMapsInDashboard()');
  }
}

/**
 * Create time-based trigger (run once to set up auto-updates)
 */
function createAutoUpdateTrigger() {
  // Delete existing triggers
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateMapsInDashboard') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // Create new trigger - every 6 hours
  ScriptApp.newTrigger('updateMapsInDashboard')
    .timeBased()
    .everyHours(6)
    .create();
  
  Logger.log('✅ Auto-update trigger created (runs every 6 hours)');
  SpreadsheetApp.getUi().alert('✅ Auto-update enabled! Maps will refresh every 6 hours.');
}

/**
 * Remove auto-update trigger
 */
function removeAutoUpdateTrigger() {
  ScriptApp.getProjectTriggers().forEach(trigger => {
    if (trigger.getHandlerFunction() === 'updateMapsInDashboard') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  Logger.log('✅ Auto-update trigger removed');
  SpreadsheetApp.getUi().alert('✅ Auto-update disabled');
}

/**
 * Add custom menu to spreadsheet
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🗺️ Power Maps')
    .addItem('🔄 Update Maps Now', 'updateMapsInDashboard')
    .addSeparator()
    .addItem('⚙️ Setup Maps API Key', 'setupMapsAPIKey')
    .addItem('⏰ Enable Auto-Updates (6h)', 'createAutoUpdateTrigger')
    .addItem('🛑 Disable Auto-Updates', 'removeAutoUpdateTrigger')
    .addToUi();
}

/**
 * Test function - run this first
 */
function testMapGeneration() {
  Logger.log('🧪 Testing map generation...');
  
  const generators = getGenerators();
  Logger.log(`Generators: ${generators ? generators.length : 0}`);
  
  const gsp = getGSPSummary();
  Logger.log(`GSP groups: ${gsp ? gsp.length : 0}`);
  
  const boundaries = getTransmissionBoundaries();
  Logger.log(`Boundaries: ${boundaries ? boundaries.length : 0}`);
  
  if (generators && generators.length > 0) {
    const mapUrl = generateSimpleMapVisualization(generators, 'Test Map');
    Logger.log('Map URL: ' + mapUrl);
  }
  
  Logger.log('✅ Test complete - check logs above');
}
