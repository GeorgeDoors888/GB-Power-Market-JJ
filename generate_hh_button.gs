/**
 * BESS Sheet - HH Profile Generator Button Handler
 * 
 * Adds "Generate HH Data" button to trigger synthetic load profile generation
 * Reads demand parameters from sheet cells and generates realistic HH data
 * 
 * Installation:
 * 1. Open BESS sheet in Google Sheets
 * 2. Extensions → Apps Script
 * 3. Paste this code into a new file: generate_hh_button.gs
 * 4. Save and refresh sheet
 * 5. Insert button: Insert → Drawing → Create button shape → Save & Close
 * 6. Click three dots on button → Assign script → Enter: generateHHData
 */

/**
 * Main function called by button click
 * Reads demand parameters from sheet and calls webhook to generate HH profile
 */
function generateHHData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('BESS');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: BESS sheet not found');
    return;
  }
  
  // Show loading indicator
  const statusCell = sheet.getRange('A17:D17');
  statusCell.merge();
  statusCell.setValue('⏳ Generating HH profile...');
  statusCell.setBackground('#FFF3CD');
  statusCell.setFontWeight('bold');
  SpreadsheetApp.flush();
  
  try {
    // Read demand parameters from cells F17:F19 (labels in E17:E19)
    // E17: "Minimum Demand kW", F17: value
    // E18: "Average Demand kW", F18: value
    // E19: "Maximum Demand kW", F19: value
    
    let minKW = sheet.getRange('G17').getValue();
    let avgKW = sheet.getRange('G18').getValue();
    let maxKW = sheet.getRange('G19').getValue();
    
    // Validate and use defaults if empty
    minKW = minKW || 500;
    avgKW = avgKW || 1500;
    maxKW = maxKW || 2500;
    
    // Validate parameters
    if (minKW >= avgKW || avgKW >= maxKW) {
      throw new Error('Invalid demand parameters: Min < Avg < Max required');
    }
    
    // Update status
    statusCell.setValue(`⏳ Generating profile (Min: ${minKW}kW, Avg: ${avgKW}kW, Max: ${maxKW}kW)...`);
    SpreadsheetApp.flush();
    
    // Call webhook to trigger Python script
    const webhookUrl = 'YOUR_NGROK_URL_HERE/generate-hh-profile';  // TODO: Update with actual ngrok URL
    
    const payload = {
      min_kw: minKW,
      avg_kw: avgKW,
      max_kw: maxKW,
      days: 365  // Generate 1 year of data
    };
    
    const options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    };
    
    Logger.log('Calling webhook: ' + webhookUrl);
    Logger.log('Payload: ' + JSON.stringify(payload));
    
    const response = UrlFetchApp.fetch(webhookUrl, options);
    const responseCode = response.getResponseCode();
    const responseText = response.getContentText();
    
    Logger.log('Response code: ' + responseCode);
    Logger.log('Response: ' + responseText);
    
    if (responseCode === 200) {
      // Success
      statusCell.setValue('✅ HH profile generated successfully!');
      statusCell.setBackground('#D4EDDA');
      
      // Auto-clear success message after 5 seconds
      Utilities.sleep(5000);
      statusCell.clearContent();
      statusCell.setBackground(null);
      
    } else {
      throw new Error('Webhook failed: ' + responseText);
    }
    
  } catch (error) {
    // Error handling
    statusCell.setValue('❌ Error: ' + error.message);
    statusCell.setBackground('#F8D7DA');
    Logger.log('Error generating HH data: ' + error);
    
    SpreadsheetApp.getUi().alert(
      'HH Generation Failed',
      'Error: ' + error.message + '\n\nCheck demand parameters in cells G17:G19',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

/**
 * Setup function to initialize demand parameter cells
 * Run once to set up the sheet structure
 */
function setupHHSection() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('BESS');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: BESS sheet not found');
    return;
  }
  
  // Set up parameter labels and default values in row 17-19
  sheet.getRange('F17').setValue('Minimum Demand kW');
  sheet.getRange('G17').setValue(500);
  
  sheet.getRange('F18').setValue('Average Demand kW');
  sheet.getRange('G18').setValue(1500);
  
  sheet.getRange('F19').setValue('Maximum Demand kW');
  sheet.getRange('G19').setValue(2500);
  
  // Format parameter cells
  const paramRange = sheet.getRange('F17:G19');
  paramRange.setFontWeight('bold');
  sheet.getRange('G17:G19').setBackground('#E3F2FD');
  
  // Add instruction text
  sheet.getRange('F16').setValue('HH Profile Parameters:');
  sheet.getRange('F16').setFontWeight('bold').setFontSize(12);
  
  SpreadsheetApp.getUi().alert(
    'Setup Complete',
    'HH profile parameter cells initialized!\n\n' +
    'F17-G17: Minimum Demand kW (default: 500)\n' +
    'F18-G18: Average Demand kW (default: 1500)\n' +
    'F19-G19: Maximum Demand kW (default: 2500)\n\n' +
    'Now add a button and assign the generateHHData() function.',
    SpreadsheetApp.getUi().ButtonSet.OK
  );
}

/**
 * Alternative: Generate HH data directly (without webhook)
 * Use this if you want to generate simple data without Python backend
 */
function generateHHDataDirect() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName('BESS');
  
  if (!sheet) {
    SpreadsheetApp.getUi().alert('Error: BESS sheet not found');
    return;
  }
  
  // Show loading
  sheet.getRange('A17').setValue('⏳ Generating HH profile...');
  SpreadsheetApp.flush();
  
  try {
    // Read parameters
    const minKW = sheet.getRange('G17').getValue() || 500;
    const avgKW = sheet.getRange('G18').getValue() || 1500;
    const maxKW = sheet.getRange('G19').getValue() || 2500;
    const days = 7;  // Generate 1 week for speed (7 days × 48 periods = 336 rows)
    
    // Clear existing data
    sheet.getRange('A20:D10000').clearContent();
    
    // Write headers
    sheet.getRange('A19:D19').setValues([['Timestamp', 'Demand (kW)', 'Notes', 'Calculated']]);
    sheet.getRange('A19:D19').setFontWeight('bold').setBackground('#4A86E8').setFontColor('#FFFFFF');
    
    // Generate data
    const startDate = new Date('2025-01-01T00:00:00');
    const data = [];
    
    for (let d = 0; d < days; d++) {
      for (let hh = 0; hh < 48; hh++) {
        const timestamp = new Date(startDate.getTime() + (d * 24 * 60 + hh * 30) * 60 * 1000);
        const hour = timestamp.getHours();
        
        // Simple pattern: higher during day, lower at night
        let factor = 0.6;  // Base (night)
        if (hour >= 6 && hour < 9) factor = 0.9;    // Morning
        if (hour >= 9 && hour < 17) factor = 1.2;   // Day
        if (hour >= 17 && hour < 21) factor = 1.3;  // Evening peak
        if (hour >= 21 && hour < 23) factor = 0.9;  // Late evening
        
        // Add randomness
        factor *= (0.9 + Math.random() * 0.2);
        
        let kw = avgKW * factor;
        kw = Math.max(minKW, Math.min(maxKW, kw));
        
        data.push([
          Utilities.formatDate(timestamp, Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss'),
          Math.round(kw * 100) / 100,
          '',
          ''
        ]);
      }
    }
    
    // Write data
    sheet.getRange(20, 1, data.length, 4).setValues(data);
    
    // Update summary
    sheet.getRange('A17').setValue('✅ HH profile generated: ' + data.length + ' periods');
    sheet.getRange('A17').setBackground('#D4EDDA');
    
  } catch (error) {
    sheet.getRange('A17').setValue('❌ Error: ' + error.message);
    sheet.getRange('A17').setBackground('#F8D7DA');
  }
}
