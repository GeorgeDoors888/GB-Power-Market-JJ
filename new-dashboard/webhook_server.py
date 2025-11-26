#!/usr/bin/env python3
"""
Dashboard V2 - Python Webhook Server
Flask server that Apps Script calls to read/write data
Avoids permission issues by using service account for all Sheets operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import gspread
from google.oauth2 import service_account
from google.cloud import bigquery
import json

app = Flask(__name__)
CORS(app)

# Configuration
CREDS_FILE = "../inner-cinema-credentials.json"
OLD_SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
NEW_SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
BESS_SHEET_ID = "1MOwnQtDEMiXCYuaeR5JA4Avz_M-xYzu_iQ20pRLXdsHMTwo4qJ0Cn6wx"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Initialize clients
creds = service_account.Credentials.from_service_account_file(
    CREDS_FILE,
    scopes=[
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/bigquery'
    ]
)
gc = gspread.authorize(creds)
bq_client = bigquery.Client(project=PROJECT_ID, credentials=creds)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Dashboard V2 Webhook'})

@app.route('/copy-dashboard-data', methods=['POST'])
def copy_dashboard_data():
    """Copy KPIs and constraints from old dashboard to new"""
    try:
        old_sheet = gc.open_by_key(OLD_SHEET_ID)
        old_dashboard = old_sheet.worksheet('Dashboard')
        
        # Read data
        kpis = old_dashboard.get('A1:H10')
        constraints = old_dashboard.get('A116:H126')
        
        # Write to new sheet (need to share it first)
        try:
            new_sheet = gc.open_by_key(NEW_SHEET_ID)
            
            # Get or create Dashboard sheet
            try:
                new_dashboard = new_sheet.worksheet('Dashboard')
            except gspread.exceptions.WorksheetNotFound:
                # Rename Sheet1 to Dashboard
                first_sheet = new_sheet.get_worksheet(0)
                first_sheet.update_title('Dashboard')
                new_dashboard = first_sheet
            
            if kpis:
                new_dashboard.update('A1', kpis)
            if constraints:
                new_dashboard.update('A116', constraints)
                
            return jsonify({
                'success': True,
                'rows_copied': {
                    'kpis': len(kpis),
                    'constraints': len(constraints)
                }
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Cannot access new sheet: {str(e)}',
                'hint': f'Share {NEW_SHEET_ID} with {creds.service_account_email}'
            }), 403
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/copy-bess-data', methods=['POST'])
def copy_bess_data():
    """Copy BESS sheet structure"""
    try:
        bess_sheet = gc.open_by_key(BESS_SHEET_ID)
        bess_src = bess_sheet.sheet1
        bess_data = bess_src.get('A1:T100')
        
        new_sheet = gc.open_by_key(NEW_SHEET_ID)
        
        # Create BESS worksheet if doesn't exist
        try:
            new_bess = new_sheet.worksheet('BESS')
        except:
            new_bess = new_sheet.add_worksheet(title='BESS', rows=100, cols=20)
        
        new_bess.update('A1', bess_data)
        
        return jsonify({
            'success': True,
            'rows_copied': len(bess_data)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get-constraints', methods=['GET'])
def get_constraints():
    """Get current constraint data for map"""
    try:
        new_sheet = gc.open_by_key(NEW_SHEET_ID)
        dashboard = new_sheet.worksheet('Dashboard')
        data = dashboard.get('A116:H126')
        
        constraints = []
        for row in data[1:]:  # Skip header
            if row[0]:  # Has boundary name
                constraints.append({
                    'boundary': row[0],
                    'flow': float(row[3]) if len(row) > 3 else 0,
                    'limit': float(row[4]) if len(row) > 4 else 0,
                    'utilization': float(row[7]) if len(row) > 7 else 0,
                    'status': row[6] if len(row) > 6 else 'Unknown',
                    'direction': row[5] if len(row) > 5 else '—'
                })
        
        return jsonify({'success': True, 'constraints': constraints})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/refresh-dashboard', methods=['POST'])
def refresh_dashboard():
    """Query BigQuery and update dashboard"""
    try:
        # Query BigQuery for latest data
        queries = {
            'demand': f"""
                SELECT ROUND(SUM(demand)/1000,2) AS value 
                FROM `{PROJECT_ID}.{DATASET}.bmrs_inddem_iris` 
                WHERE DATE(publishTime)=CURRENT_DATE()
            """,
            'generation': f"""
                SELECT ROUND(SUM(generation)/1000,2) AS value
                FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
                WHERE DATE(publishTime)=CURRENT_DATE()
            """
        }
        
        results = {}
        for key, sql in queries.items():
            query_job = bq_client.query(sql)
            rows = list(query_job.result())
            results[key] = rows[0].value if rows else 0
        
        # Update sheet
        new_sheet = gc.open_by_key(NEW_SHEET_ID)
        dashboard = new_sheet.worksheet('Dashboard')
        
        # Update KPI values (adjust ranges as needed)
        updates = [
            ['Demand', results['demand'], 'GW'],
            ['Generation', results['generation'], 'GW']
        ]
        
        dashboard.update('B2', updates)
        
        return jsonify({
            'success': True,
            'updated': results,
            'timestamp': str(query_job.ended)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 80)
    print("DASHBOARD V2 WEBHOOK SERVER")
    print("=" * 80)
    print(f"\nService Account: {creds.service_account_email}")
    print(f"\n⚠️  IMPORTANT: Share these spreadsheets with the service account:")
    print(f"   - New Dashboard: {NEW_SHEET_ID}")
    print(f"\nStarting server on http://localhost:5001")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
