#!/usr/bin/env python3
"""
Add Threshold Alerts with Conditional Formatting
Highlights critical values: SIP >£100/MWh, Frequency <49.8Hz, etc.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

def get_current_values():
    """Get latest values for threshold checking"""

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Get latest SIP from historical table (iris not available), frequency from iris
    sql = f"""
    WITH latest_sip AS (
      SELECT systemSellPrice as sip
      FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
      ORDER BY settlementDate DESC, settlementPeriod DESC
      LIMIT 1
    ),
    latest_freq AS (
      SELECT frequency
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
      ORDER BY measurementTime DESC
      LIMIT 1
    )
    SELECT
      (SELECT sip FROM latest_sip) as sip,
      (SELECT frequency FROM latest_freq) as frequency
    """

    result = client.query(sql).to_dataframe()
    return result.iloc[0] if len(result) > 0 else None

def apply_conditional_formatting(sheet):
    """Apply conditional formatting rules to dashboard"""

    print("\n🎨 Applying conditional formatting...")

    # Rule 1: SIP > £100/MWh (red background)
    sip_rule = {
        "requests": [{
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet.id,
                        "startRowIndex": 12,  # Row 13 (0-indexed)
                        "endRowIndex": 13,
                        "startColumnIndex": 11,  # Column L
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_GREATER",
                            "values": [{"userEnteredValue": "100"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.957, "green": 0.8, "blue": 0.8},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 0.6, "green": 0, "blue": 0}}
                        }
                    }
                },
                "index": 0
            }
        }]
    }

    # Rule 2: Frequency < 49.8 Hz (red background)
    freq_rule = {
        "requests": [{
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet.id,
                        "startRowIndex": 19,  # Row 20
                        "endRowIndex": 20,
                        "startColumnIndex": 11,  # Column L
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_LESS",
                            "values": [{"userEnteredValue": "49.8"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 0.957, "green": 0.8, "blue": 0.8},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 0.6, "green": 0, "blue": 0}}
                        }
                    }
                },
                "index": 0
            }
        }]
    }

    # Rule 3: Arbitrage capture < 50% (yellow warning)
    arb_rule = {
        "requests": [{
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet.id,
                        "startRowIndex": 30,  # Row 31
                        "endRowIndex": 31,
                        "startColumnIndex": 11,  # Column L
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_LESS",
                            "values": [{"userEnteredValue": "50"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 1, "green": 0.949, "blue": 0.8},
                            "textFormat": {"bold": True}
                        }
                    }
                },
                "index": 0
            }
        }]
    }

    # Rule 4: VaR 99% > £150/MWh (orange alert)
    var_rule = {
        "requests": [{
            "addConditionalFormatRule": {
                "rule": {
                    "ranges": [{
                        "sheetId": sheet.id,
                        "startRowIndex": 37,  # Row 38
                        "endRowIndex": 38,
                        "startColumnIndex": 11,  # Column L
                        "endColumnIndex": 12
                    }],
                    "booleanRule": {
                        "condition": {
                            "type": "NUMBER_GREATER",
                            "values": [{"userEnteredValue": "150"}]
                        },
                        "format": {
                            "backgroundColor": {"red": 1, "green": 0.9, "blue": 0.698},
                            "textFormat": {"bold": True, "foregroundColor": {"red": 0.6, "green": 0.2, "blue": 0}}
                        }
                    }
                },
                "index": 0
            }
        }]
    }

    # Apply all rules
    spreadsheet = sheet.spreadsheet

    try:
        spreadsheet.batch_update(sip_rule)
        print("  ✅ SIP >£100 alert (red)")
    except Exception as e:
        print(f"  ⚠️  SIP rule: {str(e)[:50]}")

    try:
        spreadsheet.batch_update(freq_rule)
        print("  ✅ Frequency <49.8Hz alert (red)")
    except Exception as e:
        print(f"  ⚠️  Frequency rule: {str(e)[:50]}")

    try:
        spreadsheet.batch_update(arb_rule)
        print("  ✅ Low arbitrage <50% warning (yellow)")
    except Exception as e:
        print(f"  ⚠️  Arbitrage rule: {str(e)[:50]}")

    try:
        spreadsheet.batch_update(var_rule)
        print("  ✅ High VaR >£150 alert (orange)")
    except Exception as e:
        print(f"  ⚠️  VaR rule: {str(e)[:50]}")

def create_apps_script_emailer():
    """Generate Apps Script code for email notifications"""

    script = """
/**
 * Threshold Alert Email Notifications
 * Checks dashboard values and sends alerts if thresholds breached
 */

function checkThresholdsAndEmail() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Live Dashboard v2');

  // Get current values
  var sip = parseFloat(sheet.getRange('L13').getValue());
  var frequency = parseFloat(sheet.getRange('L20').getValue());
  var arbitrage = parseFloat(sheet.getRange('L31').getValue().replace('%', ''));
  var var99 = parseFloat(sheet.getRange('L38').getValue().replace('£', '').replace('/MWh', ''));

  var alerts = [];

  // Check thresholds
  if (sip > 100) {
    alerts.push('🚨 HIGH SIP: £' + sip.toFixed(2) + '/MWh (threshold: £100)');
  }

  if (frequency < 49.8) {
    alerts.push('⚡ LOW FREQUENCY: ' + frequency.toFixed(2) + ' Hz (threshold: 49.8 Hz)');
  }

  if (arbitrage < 50) {
    alerts.push('⚠️ LOW ARBITRAGE: ' + arbitrage.toFixed(1) + '% (threshold: 50%)');
  }

  if (var99 > 150) {
    alerts.push('📊 HIGH RISK: VaR 99% = £' + var99.toFixed(2) + '/MWh (threshold: £150)');
  }

  // Send email if any alerts
  if (alerts.length > 0) {
    var recipient = 'george@upowerenergy.uk';  // Change to your email
    var subject = '🚨 GB Power Market Alert - ' + alerts.length + ' threshold(s) breached';

    var body = 'GB Power Market Dashboard Alerts\\n';
    body += '================================\\n\\n';
    body += 'Time: ' + new Date().toLocaleString('en-GB') + '\\n\\n';
    body += alerts.join('\\n') + '\\n\\n';
    body += 'Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA\\n';

    MailApp.sendEmail(recipient, subject, body);
    Logger.log('Sent alert email: ' + alerts.length + ' alerts');
  } else {
    Logger.log('No threshold breaches detected');
  }
}

/**
 * Install time-based trigger (runs every 15 minutes)
 * Run this function once to set up automatic checking
 */
function installTrigger() {
  // Delete existing triggers
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'checkThresholdsAndEmail') {
      ScriptApp.deleteTrigger(trigger);
    }
  });

  // Create new trigger (every 15 minutes)
  ScriptApp.newTrigger('checkThresholdsAndEmail')
    .timeBased()
    .everyMinutes(15)
    .create();

  Logger.log('Trigger installed: check every 15 minutes');
}

/**
 * Uninstall trigger
 */
function uninstallTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(function(trigger) {
    if (trigger.getHandlerFunction() === 'checkThresholdsAndEmail') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  Logger.log('Trigger removed');
}
"""

    with open('threshold_alerts_apps_script.gs', 'w') as f:
        f.write(script)

    print("\n📧 Created Apps Script email notification code")
    print("   File: threshold_alerts_apps_script.gs")
    print("\n   Installation:")
    print("   1. Open dashboard → Extensions → Apps Script")
    print("   2. Create new file 'ThresholdAlerts.gs'")
    print("   3. Paste code from threshold_alerts_apps_script.gs")
    print("   4. Run 'installTrigger()' once to enable")
    print("   5. Emails sent to: george@upowerenergy.uk")

def main():
    print("="*80)
    print("THRESHOLD ALERTS & CONDITIONAL FORMATTING")
    print("="*80)

    # Check current values
    print("\n📊 Current values:")
    values = get_current_values()
    if values is not None:
        print(f"   SIP: £{values['sip']:.2f}/MWh")
        print(f"   Frequency: {values['frequency']:.2f} Hz")

        # Check thresholds
        alerts = []
        if values['sip'] > 100:
            alerts.append(f"🚨 SIP above £100 (currently £{values['sip']:.2f})")
        if values['frequency'] < 49.8:
            alerts.append(f"⚡ Frequency below 49.8 Hz (currently {values['frequency']:.2f})")

        if alerts:
            print("\n🚨 ALERTS TRIGGERED:")
            for alert in alerts:
                print(f"   {alert}")
        else:
            print("\n✅ All values within normal thresholds")

    # Connect to Sheets
    print("\n🔗 Connecting to Google Sheets...")
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'inner-cinema-credentials.json', scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).worksheet('Live Dashboard v2')

    # Apply conditional formatting
    apply_conditional_formatting(sheet)

    # Create email script
    create_apps_script_emailer()

    print("\n" + "="*80)
    print("✅ THRESHOLD ALERTS CONFIGURED")
    print("="*80)
    print("\nConditional Formatting Rules:")
    print("  • SIP >£100/MWh → Red background")
    print("  • Frequency <49.8Hz → Red background")
    print("  • Arbitrage <50% → Yellow warning")
    print("  • VaR 99% >£150 → Orange alert")
    print("\nEmail Notifications:")
    print("  • Apps Script code generated")
    print("  • Install manually in dashboard (see instructions above)")

if __name__ == "__main__":
    main()
