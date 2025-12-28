#!/usr/bin/env python3
"""
VLP Dashboard Webhook Server
Receives refresh requests from Apps Script menu and runs pipeline
"""

from flask import Flask, request, jsonify
import subprocess
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/refresh-vlp', methods=['POST'])
def refresh_vlp():
    """Refresh VLP dashboard data"""
    
    try:
        data = request.get_json()
        spreadsheet_id = data.get('spreadsheet_id')
        date_range = data.get('date_range', 'last_7_days')
        
        print(f"[{datetime.now()}] Refresh request: {date_range}")
        
        # Run vlp_dashboard_simple.py
        result = subprocess.run(
            ['python3', 'vlp_dashboard_simple.py'],
            cwd='/home/george/GB-Power-Market-JJ',
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        if result.returncode == 0:
            return jsonify({
                'status': 'success',
                'message': 'Dashboard refreshed',
                'output': result.stdout
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Dashboard refresh failed',
                'error': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/run-full-pipeline', methods=['POST'])
def run_full_pipeline():
    """Run full pipeline: data + formatting + charts"""
    
    try:
        print(f"[{datetime.now()}] Full pipeline request")
        
        # 1. Fetch data
        result1 = subprocess.run(
            ['python3', 'vlp_dashboard_simple.py'],
            cwd='/home/george/GB-Power-Market-JJ',
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result1.returncode != 0:
            return jsonify({
                'status': 'error',
                'step': 'data_fetch',
                'error': result1.stderr
            }), 500
        
        # 2. Apply formatting
        result2 = subprocess.run(
            ['python3', 'format_vlp_dashboard.py'],
            cwd='/home/george/GB-Power-Market-JJ',
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # 3. Create charts (skip if formatting failed)
        if result2.returncode == 0:
            result3 = subprocess.run(
                ['python3', 'create_vlp_charts.py'],
                cwd='/home/george/GB-Power-Market-JJ',
                capture_output=True,
                text=True,
                timeout=60
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Full pipeline completed',
            'steps': {
                'data_fetch': 'OK' if result1.returncode == 0 else 'FAILED',
                'formatting': 'OK' if result2.returncode == 0 else 'FAILED',
                'charts': 'OK' if result3.returncode == 0 else 'FAILED'
            }
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'vlp-webhook'})

if __name__ == '__main__':
    print("⚡ VLP Webhook Server")
    print("=" * 60)
    print("Endpoints:")
    print("  POST /refresh-vlp       - Refresh dashboard data")
    print("  POST /run-full-pipeline - Run full pipeline")
    print("  GET  /health            - Health check")
    print("\nListening on http://localhost:5002")
    print("Expose via: ngrok http 5002")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
