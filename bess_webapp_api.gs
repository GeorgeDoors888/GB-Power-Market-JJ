/**
 * BESS Sheet - DNO Lookup Web App
 * Deploy this as a Web App to enable Python → Apps Script → Sheets updates
 */

const API_SECRET = 'gb_power_dno_lookup_2025';  // Change this!

function doPost(e) {
  try {
    if (!e.postData || !e.postData.contents) {
      return _json({ status: 'error', message: 'No body' }, 400);
    }

    const data = JSON.parse(e.postData.contents);

    // Simple auth
    if (data.secret !== API_SECRET) {
      return _json({ status: 'error', message: 'Unauthorized' }, 401);
    }

    const action = data.action;
    const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');

    if (!sheet) {
      return _json({ status: 'error', message: 'BESS sheet not found' }, 404);
    }

    // Action: update_dno_info
    if (action === 'update_dno_info') {
      const dnoData = data.dno_data;  // { dno_key, dno_name, ... }
      
      // Update A6:H6 with postcode, MPAN and DNO info
      if (data.postcode) {
        sheet.getRange('A6').setValue(data.postcode);
      }
      sheet.getRange('B6').setValue(data.mpan_id || '');
      sheet.getRange('C6').setValue(dnoData.dno_key || '');
      sheet.getRange('D6').setValue(dnoData.dno_name || '');
      sheet.getRange('E6').setValue(dnoData.dno_short_code || '');
      sheet.getRange('F6').setValue(dnoData.market_participant_id || '');
      sheet.getRange('G6').setValue(dnoData.gsp_group_id || '');
      sheet.getRange('H6').setValue(dnoData.gsp_group_name || '');
      
      return _json({ status: 'ok', message: 'DNO info updated' });
    }

    // Action: update_duos_rates
    if (action === 'update_duos_rates') {
      const rates = data.rates;  // { red, amber, green }
      
      // Update B9:E9 with rates
      sheet.getRange('B9').setValue(rates.red || 0);
      sheet.getRange('C9').setValue(rates.amber || 0);
      sheet.getRange('D9').setValue(rates.green || 0);
      sheet.getRange('E9').setValue((rates.red || 0) + (rates.amber || 0) + (rates.green || 0));
      
      return _json({ status: 'ok', message: 'DUoS rates updated' });
    }

    // Action: update_status
    if (action === 'update_status') {
      const status = data.status_data;  // array of 8 values for A4:H4
      
      sheet.getRange('A4:H4').setValues([status]);
      sheet.getRange('A4:H4').setBackground('#90EE90');  // Light green
      sheet.getRange('A4:H4').setFontWeight('bold');
      
      return _json({ status: 'ok', message: 'Status updated' });
    }

    // Action: read_inputs
    if (action === 'read_inputs') {
      const postcode = sheet.getRange('A6').getValue();
      const mpanId = sheet.getRange('B6').getValue();
      const voltage = sheet.getRange('A9').getValue();
      
      return _json({ 
        status: 'ok', 
        inputs: { 
          postcode: postcode,
          mpan_id: mpanId,
          voltage: voltage
        }
      });
    }

    // Action: full_update (combined update)
    if (action === 'full_update') {
      const dnoData = data.dno_data;
      const rates = data.rates;
      const statusText = data.status_text;
      
      // Update DNO info
      sheet.getRange('C6:H6').setValues([[
        dnoData.dno_key || '',
        dnoData.dno_name || '',
        dnoData.dno_short_code || '',
        dnoData.market_participant_id || '',
        dnoData.gsp_group_id || '',
        dnoData.gsp_group_name || ''
      ]]);
      
      // Update rates
      sheet.getRange('B9:E9').setValues([[
        rates.red || 0,
        rates.amber || 0,
        rates.green || 0,
        (rates.red || 0) + (rates.amber || 0) + (rates.green || 0)
      ]]);
      
      // Update status
      const timestamp = Utilities.formatDate(new Date(), 'Europe/London', 'HH:mm:ss');
      sheet.getRange('A4:H4').setValues([[
        statusText || '✅ Updated',
        `${dnoData.dno_name}`,
        `MPAN ${data.mpan_id || ''}`,
        `Updated: ${timestamp}`,
        '', '', '', ''
      ]]);
      sheet.getRange('A4:H4').setBackground('#90EE90');
      sheet.getRange('A4:H4').setFontWeight('bold');
      
      return _json({ status: 'ok', message: 'Full update complete', timestamp: timestamp });
    }

    return _json({ status: 'error', message: 'Unknown action' }, 400);
    
  } catch (err) {
    return _json({ status: 'error', message: String(err) }, 500);
  }
}

function _json(obj, statusCode) {
  const output = ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);

  if (statusCode) {
    obj.httpStatus = statusCode;
  }

  return output;
}

// Health check endpoint
function doGet(e) {
  return _json({ 
    status: 'ok', 
    message: 'BESS DNO Lookup API',
    timestamp: new Date().toISOString()
  });
}
