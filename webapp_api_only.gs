/**
 * Web App API - receives updates from Python
 * Add this as a SECOND file in Apps Script
 */

const API_SECRET = 'gb_power_dno_lookup_2025';

function doPost(e) {
  try {
    if (!e.postData || !e.postData.contents) {
      return _json({ status: 'error', message: 'No body' }, 400);
    }

    const data = JSON.parse(e.postData.contents);

    if (data.secret !== API_SECRET) {
      return _json({ status: 'error', message: 'Unauthorized' }, 401);
    }

    const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');

    if (!sheet) {
      return _json({ status: 'error', message: 'BESS sheet not found' }, 404);
    }

    if (data.action === 'update_dno_info') {
      const dnoData = data.dno_data;
      
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

    if (data.action === 'update_duos_rates') {
      const rates = data.rates;
      
      sheet.getRange('B9').setValue(rates.red || 0);
      sheet.getRange('C9').setValue(rates.amber || 0);
      sheet.getRange('D9').setValue(rates.green || 0);
      
      return _json({ status: 'ok', message: 'DUoS rates updated' });
    }

    if (data.action === 'update_status') {
      const status = data.status_data;
      
      sheet.getRange('A4:H4').setValues([status]);
      sheet.getRange('A4:H4').setBackground('#90EE90');
      sheet.getRange('A4:H4').setFontWeight('bold');
      
      return _json({ status: 'ok', message: 'Status updated' });
    }

    if (data.action === 'read_inputs') {
      const postcode = sheet.getRange('A6').getValue();
      const mpanId = sheet.getRange('B6').getValue();
      const voltage = sheet.getRange('A9').getValue();
      
      return _json({ 
        status: 'ok',
        inputs: {
          postcode: postcode || '',
          mpan_id: mpanId || null,
          voltage: voltage || 'LV'
        }
      });
    }

    return _json({ status: 'error', message: 'Unknown action' }, 400);
    
  } catch (err) {
    return _json({ status: 'error', message: String(err) }, 500);
  }
}

function _json(obj, statusCode) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  return _json({ 
    status: 'ok', 
    message: 'BESS DNO Lookup API',
    timestamp: new Date().toISOString()
  });
}
