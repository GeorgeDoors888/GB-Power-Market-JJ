#!/usr/bin/env python3
"""
DNO Webhook Server for UpCloud
===============================
Flask server that receives webhook calls from Google Apps Script
and triggers DNO lookup scripts

Endpoints:
- POST /trigger-dno-lookup - Trigger DNO lookup
- POST /generate-hh-profile - Generate HH profile
- GET /health - Health check
- GET /status - System status

Run: python3 dno_webhook_server_upcloud.py
"""

from flask import Flask, request, jsonify
import subprocess
import os
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
PROJECT_DIR = "/opt/bess"
CREDENTIALS_PATH = "/root/.google-credentials/inner-cinema-credentials.json"
LOG_DIR = "/var/log/bess"

# Set BigQuery credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_PATH


def log_request(endpoint: str, data: dict, result: dict):
    """Log webhook requests"""
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, 'webhook_requests.log')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'request_data': data,
            'result': result
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Warning: Failed to log request: {e}")


@app.route('/trigger-dno-lookup', methods=['POST'])
def trigger_dno_lookup():
    """
    Trigger DNO lookup from BESS sheet data
    
    Expected payload:
    {
        "postcode": "RH19 4LX",  # Optional
        "mpan_id": "14",         # Optional
        "voltage": "HV"          # Optional
    }
    """
    try:
        data = request.get_json() or {}
        
        postcode = data.get('postcode', '').strip()
        mpan_id = data.get('mpan_id', '14').strip()
        voltage = data.get('voltage', 'HV').strip()
        
        print(f"\n🔔 DNO Lookup Request")
        print(f"   Postcode: {postcode}")
        print(f"   MPAN: {mpan_id}")
        print(f"   Voltage: {voltage}")
        
        # Build command
        cmd = [
            'python3',
            os.path.join(PROJECT_DIR, 'dno_lookup_python.py'),
            mpan_id,
            voltage
        ]
        
        # Run the script
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        response = {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'timestamp': datetime.now().isoformat()
        }
        
        log_request('/trigger-dno-lookup', data, response)
        
        if result.returncode == 0:
            print("  ✅ DNO lookup completed")
        else:
            print(f"  ❌ DNO lookup failed: {result.stderr}")
        
        return jsonify(response)
        
    except subprocess.TimeoutExpired:
        error_response = {
            'status': 'error',
            'message': 'DNO lookup timeout (>60 seconds)',
            'timestamp': datetime.now().isoformat()
        }
        log_request('/trigger-dno-lookup', data, error_response)
        return jsonify(error_response), 504
        
    except Exception as e:
        error_response = {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        log_request('/trigger-dno-lookup', data, error_response)
        return jsonify(error_response), 500


@app.route('/generate-hh-profile', methods=['POST'])
def generate_hh_profile():
    """
    Generate HH profile data
    
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
        
        print(f"\n📊 HH Profile Request")
        print(f"   Min: {min_kw} kW")
        print(f"   Avg: {avg_kw} kW")
        print(f"   Max: {max_kw} kW")
        print(f"   Days: {days}")
        
        # Validate parameters
        if min_kw >= avg_kw or avg_kw >= max_kw:
            return jsonify({
                'status': 'error',
                'message': 'Invalid parameters: min_kw < avg_kw < max_kw required'
            }), 400
        
        # Build command
        cmd = [
            'python3',
            os.path.join(PROJECT_DIR, 'generate_hh_profile.py'),
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
            timeout=120
        )
        
        response = {
            'status': 'success' if result.returncode == 0 else 'error',
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'message': f'Generated HH profile with {days} days of data',
            'timestamp': datetime.now().isoformat()
        }
        
        log_request('/generate-hh-profile', data, response)
        
        if result.returncode == 0:
            print("  ✅ HH profile generated")
        else:
            print(f"  ❌ HH profile failed: {result.stderr}")
        
        return jsonify(response)
        
    except subprocess.TimeoutExpired:
        error_response = {
            'status': 'error',
            'message': 'HH generation timeout (>2 minutes)',
            'timestamp': datetime.now().isoformat()
        }
        log_request('/generate-hh-profile', data, error_response)
        return jsonify(error_response), 504
        
    except Exception as e:
        error_response = {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }
        log_request('/generate-hh-profile', data, error_response)
        return jsonify(error_response), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'DNO Webhook Server running',
        'timestamp': datetime.now().isoformat(),
        'project_dir': PROJECT_DIR,
        'credentials': 'configured' if os.path.exists(CREDENTIALS_PATH) else 'missing'
    })


@app.route('/status', methods=['GET'])
def status():
    """System status endpoint"""
    try:
        # Check if monitor is running
        monitor_running = False
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'bess_auto_monitor'],
                capture_output=True,
                text=True
            )
            monitor_running = result.returncode == 0
        except:
            pass
        
        # Check files
        scripts_exist = {
            'dno_lookup_python.py': os.path.exists(os.path.join(PROJECT_DIR, 'dno_lookup_python.py')),
            'generate_hh_profile.py': os.path.exists(os.path.join(PROJECT_DIR, 'generate_hh_profile.py')),
            'bess_auto_monitor.py': os.path.exists(os.path.join(PROJECT_DIR, 'bess_auto_monitor_upcloud.py')),
            'credentials': os.path.exists(CREDENTIALS_PATH)
        }
        
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'monitor_running': monitor_running,
            'project_dir': PROJECT_DIR,
            'scripts': scripts_exist,
            'log_dir': LOG_DIR
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


if __name__ == '__main__':
    print("="*60)
    print("🚀 DNO WEBHOOK SERVER FOR UPCLOUD")
    print("="*60)
    print(f"📁 Project directory: {PROJECT_DIR}")
    print(f"🔑 Credentials: {CREDENTIALS_PATH}")
    print(f"📝 Log directory: {LOG_DIR}")
    print(f"🌐 Listening on http://0.0.0.0:5001")
    print("\nEndpoints:")
    print("  POST /trigger-dno-lookup - Trigger DNO lookup")
    print("  POST /generate-hh-profile - Generate HH profile")
    print("  GET  /health - Health check")
    print("  GET  /status - System status")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    # Create log directory
    os.makedirs(LOG_DIR, exist_ok=True)
    
    app.run(host='0.0.0.0', port=5001, debug=False)
