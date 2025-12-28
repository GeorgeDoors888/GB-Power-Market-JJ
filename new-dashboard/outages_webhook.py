#!/usr/bin/env python3
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
    print("⚡ Starting webhook server on http://localhost:5002")
    print("📡 Expose with: ngrok http 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
