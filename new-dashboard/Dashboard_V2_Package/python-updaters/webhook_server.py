#!/usr/bin/env python3
"""
Dashboard V2 Webhook Server
Flask server for handling dashboard operations
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2 import service_account

app = Flask(__name__)
CORS(app)

SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE'
SA_FILE = 'inner-cinema-credentials.json'

creds = service_account.Credentials.from_service_account_file(
    SA_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
gc = gspread.authorize(creds)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Dashboard V2 Webhook"})

@app.route('/refresh-dashboard', methods=['POST'])
def refresh_dashboard():
    try:
        sheet = gc.open_by_key(SPREADSHEET_ID)
        # Add refresh logic here
        return jsonify({"success": True, "message": "Dashboard refreshed"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("Starting Dashboard V2 Webhook Server on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
