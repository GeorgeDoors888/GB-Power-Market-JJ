#!/usr/bin/env python3
"""
Simple webhook server that Apps Script can call to trigger DNO lookup
Run this in the background: python3 dno_webhook_server.py
"""

from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

# Change to your project directory
PROJECT_DIR = "/home/george/GB-Power-Market-JJ"

# Set BigQuery credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/.config/google-cloud/bigquery-credentials.json'

@app.route('/trigger-dno-lookup', methods=['POST'])
def trigger_dno_lookup():
    """
    Endpoint that Apps Script calls to trigger the Python DNO lookup
    
    Expected payload:
    {
        "postcode": "LS1 2TW",  # Optional
        "mpan_id": 23,          # Optional
        "voltage": "HV"         # Optional
    }
    """
    try:
        data = request.get_json() or {}
        
        postcode = data.get('postcode', '').strip()
        mpan_id = data.get('mpan_id')
        voltage = data.get('voltage', 'LV')
        
        # Build command
        # dno_lookup_python.py reads from BESS sheet when called with no args
        # It expects: python3 dno_lookup_python.py [mpan_id] [voltage]
        # But for postcode lookup, it reads directly from sheet (no args)
        cmd = ['python3', 'dno_lookup_python.py']
        
        # Only pass MPAN if explicitly provided (not from postcode)
        if mpan_id and not postcode:
            cmd.append(str(mpan_id))
            cmd.append(voltage)
        # Otherwise, let script read from sheet (A6 postcode, A10 voltage)
        
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/generate-hh-profile', methods=['POST'])
def generate_hh_profile():
    """
    Endpoint to generate HH profile data
    
    Expected payload:
    {
        "min_kw": 500,
        "avg_kw": 1500,
        "max_kw": 2500,
        "days": 365
    }
    """
    try:
        data = request.get_json() or {}
        
        min_kw = data.get('min_kw', 500)
        avg_kw = data.get('avg_kw', 1500)
        max_kw = data.get('max_kw', 2500)
        days = data.get('days', 365)
        
        # Validate parameters
        if min_kw >= avg_kw or avg_kw >= max_kw:
            return jsonify({
                'status': 'error',
                'message': 'Invalid parameters: min_kw < avg_kw < max_kw required'
            }), 400
        
        # Build command
        cmd = [
            'python3', 
            'generate_hh_profile.py',
            str(min_kw),
            str(avg_kw),
            str(max_kw),
            str(days)
        ]
        
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout (may take time for large datasets)
        )
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'message': f'Generated HH profile with {days} days of data'
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'HH generation timeout (>2 minutes)'
        }), 504
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'DNO Webhook Server running'})

@app.route('/refresh-dashboard', methods=['POST'])
def refresh_dashboard():
    """
    Dashboard refresh endpoint
    Triggers complete BESS data update + dashboard rebuild
    
    Usage:
    POST http://localhost:5001/refresh-dashboard
    """
    try:
        print("🔄 Dashboard refresh triggered...")
        
        # Run complete refresh pipeline
        result = subprocess.run(
            ['python3', 'refresh_dashboard_complete.py'],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        return jsonify({
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'message': 'Dashboard refresh completed'
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'status': 'error',
            'message': 'Dashboard refresh timeout (>5 minutes)'
        }), 504
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("⚡ Starting DNO Webhook Server...")
    print(f"📁 Project directory: {PROJECT_DIR}")
    print(f"🌐 Listening on http://localhost:5001")
    print(f"📡 Endpoints:")
    print(f"   POST http://localhost:5001/trigger-dno-lookup")
    print(f"   POST http://localhost:5001/generate-hh-profile")
    print(f"   POST http://localhost:5001/refresh-dashboard")
    print(f"   GET  http://localhost:5001/health")
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)
