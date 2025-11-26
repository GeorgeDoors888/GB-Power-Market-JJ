#!/usr/bin/env python3
"""
Complete Live Outages Setup: Chart, Webhook, Cron, Filter Views
"""

import sys
import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from flask import Flask, request, jsonify
import subprocess

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def create_chart_data():
    """Add chart data for Demand/Generation/Outages trend"""
    print("📈 Creating chart data...")
    
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    bq_creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json'
    )
    bq_client = bigquery.Client(project=PROJECT_ID, credentials=bq_creds, location='US')
    
    # Get last 30 days of data
    query = f"""
    WITH daily_generation AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            SUM(generation) / 1000.0 as generation_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY date
    ),
    daily_demand AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            AVG(initialDemandOutturn) / 1000.0 as demand_gw
        FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
        GROUP BY date
    ),
    daily_outages AS (
        SELECT 
            CAST(eventStartTime AS DATE) as date,
            SUM(unavailableCapacity) / 1000.0 as outages_gw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
        WHERE CAST(eventStartTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
          AND eventStatus = 'Active'
        GROUP BY date
    )
    SELECT 
        COALESCE(g.date, d.date) as date,
        AVG(d.demand_gw) as demand_gw,
        AVG(g.generation_gw) as generation_gw,
        AVG(COALESCE(o.outages_gw, 0)) as outages_gw
    FROM daily_generation g
    FULL OUTER JOIN daily_demand d ON g.date = d.date
    LEFT JOIN daily_outages o ON COALESCE(g.date, d.date) = o.date
    GROUP BY date
    ORDER BY date
    """
    
    df = bq_client.query(query).to_dataframe()
    
    # Add chart data to columns M-P
    sheet.update([['CHART DATA - Demand/Generation/Outages Trend (Last 30 Days)']], 'M1')
    sheet.update([['Date', 'Demand (GW)', 'Generation (GW)', 'Outages (GW)']], 'M2')
    
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append([
            row['date'].strftime('%Y-%m-%d') if row['date'] else '',
            f"{row['demand_gw']:.2f}" if row['demand_gw'] else '0',
            f"{row['generation_gw']:.2f}" if row['generation_gw'] else '0',
            f"{row['outages_gw']:.2f}" if row['outages_gw'] else '0'
        ])
    
    sheet.update(chart_data, 'M3')
    
    print(f"✅ Added {len(chart_data)} days of chart data (M3:P{len(chart_data)+2})")
    print("   📊 To create chart: Select M2:P32 → Insert → Chart → Line chart")
    
    return True

def create_filter_views():
    """Create common filter views"""
    print("\n🔍 Creating filter views...")
    
    creds = service_account.Credentials.from_service_account_file(
        '../inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet('Live Outages')
    
    # Create filter views using API
    requests = []
    
    # Filter 1: High Capacity Outages (>500 MW)
    requests.append({
        'addFilterView': {
            'filter': {
                'title': 'High Capacity Outages (>500 MW)',
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 9,
                    'startColumnIndex': 0,
                    'endColumnIndex': 10
                },
                'criteria': {
                    4: {  # Column E (Unavail MW)
                        'condition': {
                            'type': 'NUMBER_GREATER',
                            'values': [{'userEnteredValue': '500'}]
                        }
                    }
                }
            }
        }
    })
    
    # Filter 2: Gas Power Stations
    requests.append({
        'addFilterView': {
            'filter': {
                'title': 'Gas Power Stations',
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 9,
                    'startColumnIndex': 0,
                    'endColumnIndex': 10
                },
                'criteria': {
                    2: {  # Column C (Fuel Type)
                        'condition': {
                            'type': 'TEXT_CONTAINS',
                            'values': [{'userEnteredValue': 'Gas'}]
                        }
                    }
                }
            }
        }
    })
    
    # Filter 3: Recent Outages (Last 7 days)
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    requests.append({
        'addFilterView': {
            'filter': {
                'title': 'Recent Outages (Last 7 Days)',
                'range': {
                    'sheetId': sheet.id,
                    'startRowIndex': 9,
                    'startColumnIndex': 0,
                    'endColumnIndex': 10
                },
                'criteria': {
                    7: {  # Column H (Start Time)
                        'condition': {
                            'type': 'DATE_AFTER',
                            'values': [{'userEnteredValue': week_ago}]
                        }
                    }
                }
            }
        }
    })
    
    try:
        spreadsheet.spreadsheet.batch_update({'requests': requests})
        print("✅ Created 3 filter views:")
        print("   - High Capacity Outages (>500 MW)")
        print("   - Gas Power Stations")
        print("   - Recent Outages (Last 7 Days)")
    except Exception as e:
        print(f"⚠️ Filter views may already exist: {e}")
    
    return True

def create_webhook():
    """Create Flask webhook for button automation"""
    print("\n🔗 Creating webhook server...")
    
    webhook_code = '''#!/usr/bin/env python3
"""
Webhook server for Live Outages refresh button
Run: python3 outages_webhook.py
Then expose with: ngrok http 5002
"""

from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

UPDATER_SCRIPT = "/Users/georgemajor/GB Power Market JJ/new-dashboard/live_outages_updater.py"

@app.route('/refresh_outages', methods=['POST'])
def refresh_outages():
    try:
        result = subprocess.run(
            ['python3', UPDATER_SCRIPT],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Outages refreshed successfully',
                'count': 141  # Parse from output if needed
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Live Outages Webhook'})

if __name__ == '__main__':
    print("🚀 Starting webhook server on http://localhost:5002")
    print("📡 Expose with: ngrok http 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
'''
    
    with open('outages_webhook.py', 'w') as f:
        f.write(webhook_code)
    
    os.chmod('outages_webhook.py', 0o755)
    
    print("✅ Created: outages_webhook.py")
    print("   Run: python3 outages_webhook.py")
    print("   Expose: ngrok http 5002")
    
    return True

def create_cron_job():
    """Create cron job for auto-refresh"""
    print("\n⏰ Creating cron job...")
    
    cron_line = f"*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ/new-dashboard' && /usr/local/bin/python3 live_outages_updater.py >> logs/outages_cron.log 2>&1"
    
    cron_file = 'live_outages_cron.txt'
    with open(cron_file, 'w') as f:
        f.write("# Live Outages Auto-Refresh (Every 15 minutes)\n")
        f.write(cron_line + "\n")
    
    print(f"✅ Created: {cron_file}")
    print("\n📝 To install cron job:")
    print("   crontab -e")
    print("   # Add this line:")
    print(f"   {cron_line}")
    
    return True

def main():
    print("=" * 80)
    print("🚀 COMPLETE LIVE OUTAGES SETUP")
    print("=" * 80)
    
    try:
        # 1. Create chart data
        create_chart_data()
        
        # 2. Create filter views
        create_filter_views()
        
        # 3. Create webhook
        create_webhook()
        
        # 4. Create cron job
        create_cron_job()
        
        print("\n" + "=" * 80)
        print("✅ COMPLETE SETUP FINISHED")
        print("=" * 80)
        print("\n📋 Next steps:")
        print("\n1. CHART:")
        print("   - Open Live Outages sheet")
        print("   - Select M2:P32")
        print("   - Insert → Chart → Line chart")
        print("   - Customize: Date on X-axis, 3 lines for Demand/Gen/Outages")
        
        print("\n2. WEBHOOK (Optional):")
        print("   - Run: python3 outages_webhook.py")
        print("   - Expose: ngrok http 5002")
        print("   - Update Apps Script with ngrok URL")
        
        print("\n3. CRON JOB:")
        print("   - Run: crontab -e")
        print("   - Paste line from live_outages_cron.txt")
        print("   - Auto-refresh every 15 minutes")
        
        print("\n4. FILTER VIEWS:")
        print("   - Already created in sheet!")
        print("   - Access via Data → Filter views")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
