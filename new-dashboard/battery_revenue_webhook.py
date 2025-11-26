#!/usr/bin/env python3
"""
Battery Revenue Analysis Webhook Server
Receives refresh requests from Google Sheets Apps Script
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import logging
import os

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Path to the analyzer script
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'battery_revenue_analyzer_fixed.py')

@app.route('/refresh-battery-revenue', methods=['POST', 'OPTIONS'])
def refresh_battery_revenue():
    """Trigger battery revenue analysis refresh"""
    
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    try:
        logging.info("📞 Webhook called: refresh-battery-revenue")
        
        # Run the analyzer script
        result = subprocess.run(
            ['python3', SCRIPT_PATH],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            # Parse output for summary stats
            output = result.stdout
            
            # Extract key metrics from log output
            today_acceptances = None
            historical_days = None
            battery_units = None
            
            for line in output.split('\n'):
                if 'Retrieved' in line and 'battery acceptances today' in line:
                    today_acceptances = line.split('Retrieved')[1].split('battery')[0].strip()
                elif 'Retrieved' in line and 'days of historical' in line:
                    historical_days = line.split('Retrieved')[1].split('days')[0].strip()
                elif 'Retrieved performance metrics for' in line and 'battery units' in line:
                    battery_units = line.split('for')[1].split('battery')[0].strip()
            
            logging.info("✅ Battery revenue analysis completed successfully")
            
            return jsonify({
                'success': True,
                'message': 'Battery revenue analysis updated',
                'today_acceptances': today_acceptances or 'N/A',
                'historical_days': historical_days or 'N/A',
                'battery_units': battery_units or 'N/A',
                'timestamp': subprocess.check_output(['date', '+%Y-%m-%d %H:%M:%S']).decode().strip()
            }), 200
        else:
            logging.error(f"❌ Script failed with return code {result.returncode}")
            logging.error(f"STDERR: {result.stderr}")
            
            return jsonify({
                'success': False,
                'error': f'Script failed: {result.stderr[:200]}'
            }), 500
            
    except subprocess.TimeoutExpired:
        logging.error("⏱️ Script execution timed out")
        return jsonify({
            'success': False,
            'error': 'Script execution timed out (>2 minutes)'
        }), 504
        
    except Exception as e:
        logging.error(f"❌ Webhook error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'battery-revenue-webhook',
        'script_path': SCRIPT_PATH,
        'script_exists': os.path.exists(SCRIPT_PATH)
    }), 200

@app.route('/refresh-battery-analysis', methods=['POST', 'OPTIONS'])
def refresh_battery_analysis():
    """Legacy endpoint for trading strategy analysis"""
    
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    return jsonify({
        'success': True,
        'message': 'Trading strategy analysis available in Battery Revenue Analysis sheet'
    }), 200

if __name__ == '__main__':
    print("=" * 80)
    print("🔋 Battery Revenue Webhook Server")
    print("=" * 80)
    print(f"📍 Script path: {SCRIPT_PATH}")
    print(f"✅ Script exists: {os.path.exists(SCRIPT_PATH)}")
    print()
    print("🌐 Endpoints:")
    print("   POST /refresh-battery-revenue  - Trigger 7-week revenue analysis")
    print("   POST /refresh-battery-analysis - Legacy endpoint (stub)")
    print("   GET  /health                   - Health check")
    print()
    print("🚀 Starting server on http://0.0.0.0:5002")
    print("=" * 80)
    
    app.run(host='0.0.0.0', port=5002, debug=True)
