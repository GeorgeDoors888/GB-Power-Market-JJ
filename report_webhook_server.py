#!/usr/bin/env python3
"""
Webhook server for Analysis Report Generation
Allows Google Sheets button to trigger Python script via HTTP POST
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import sys

app = Flask(__name__)
CORS(app)  # Allow requests from Google Sheets

SCRIPT_DIR = '/home/george/GB-Power-Market-JJ'

@app.route('/generate-report', methods=['POST', 'GET'])
def generate_report():
    """
    Endpoint: POST /generate-report
    Trigger: Google Sheets CALCULATE button
    Action: Run generate_analysis_report.py
    """
    try:
        if request.method == 'GET':
            return jsonify({
                'status': 'ready',
                'message': 'Report webhook server is running',
                'endpoint': '/generate-report (POST)'
            })

        # Get selections from request
        data = request.get_json() or {}

        print(f"\n🔔 Webhook triggered!")
        print(f"📊 Report Category: {data.get('report_category', 'N/A')}")
        print(f"📅 Date Range: {data.get('from_date')} → {data.get('to_date')}")
        print(f"📋 Type: {data.get('report_type', 'N/A')}")
        print(f"📈 Graph: {data.get('graph_type', 'N/A')}")

        # Run the Python script
        script_path = os.path.join(SCRIPT_DIR, 'generate_analysis_report.py')

        print(f"\n▶️  Executing: python3 {script_path}")

        result = subprocess.run(
            ['python3', script_path],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✅ Script completed successfully")
            return jsonify({
                'status': 'success',
                'message': 'Report generated successfully!\nCheck Analysis sheet row 18+',
                'output': result.stdout[-500:] if result.stdout else ''  # Last 500 chars
            })
        else:
            print(f"❌ Script failed with code {result.returncode}")
            print(f"Error: {result.stderr}")
            return jsonify({
                'status': 'error',
                'message': f'Script failed: {result.stderr[-200:]}',
                'returncode': result.returncode
            }), 500

    except subprocess.TimeoutExpired:
        print("⏰ Script timeout (60s)")
        return jsonify({
            'status': 'error',
            'message': 'Script timeout after 60 seconds'
        }), 504

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Analysis Report Webhook',
        'version': '1.0'
    })

if __name__ == '__main__':
    print("⚡ Starting Analysis Report Webhook Server...")
    print(f"📁 Script directory: {SCRIPT_DIR}")
    print(f"🌐 Endpoint: http://localhost:5000/generate-report")
    print(f"💡 Trigger from Google Sheets CALCULATE button")
    print(f"\n⏸️  Press Ctrl+C to stop\n")

    # Run on localhost:5000
    app.run(host='0.0.0.0', port=5000, debug=False)
