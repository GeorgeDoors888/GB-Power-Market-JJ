#!/usr/bin/env python3
"""
Flask webhook server for Apps Script integration
Apps Script calls this endpoint, triggering Python backend
"""

from flask import Flask, request, jsonify
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from python_backend import refresh_data, apply_formatting

app = Flask(__name__)

@app.route('/api/refresh', methods=['POST'])
def handle_refresh():
    """
    Endpoint called by Apps Script triggerPythonRefresh()
    """
    try:
        data = request.get_json()
        spreadsheet_id = data.get('spreadsheetId')
        action = data.get('action')
        
        print(f"📥 Received request: {action} for sheet {spreadsheet_id}")
        
        if action == 'refresh_data':
            result = refresh_data()
            return jsonify(result)
        
        elif action == 'format_sheet':
            sheet_name = data.get('sheetName', 'Data')
            result = apply_formatting(sheet_name)
            return jsonify(result)
        
        else:
            return jsonify({
                'success': False,
                'message': f'Unknown action: {action}'
            }), 400
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'python-backend'})

if __name__ == '__main__':
    # Run on port 5002 (adjust as needed)
    app.run(host='0.0.0.0', port=5002, debug=True)
