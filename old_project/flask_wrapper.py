#!/usr/bin/env python3
"""
Flask wrapper for scheduled_data_ingestion.py
This allows the script to be triggered via HTTP for Cloud Run and Cloud Scheduler integration
"""

import os
import sys
import json
import logging
from flask import Flask, request, jsonify
import scheduled_data_ingestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "UK Energy Data Ingestion",
        "version": "1.0.0"
    })

@app.route('/run', methods=['POST'])
def run_ingestion():
    """Endpoint to trigger data ingestion"""
    try:
        # Get request data
        request_data = request.get_json() or {}
        
        # Extract parameters
        mode = request_data.get('mode', 'incremental')
        days = request_data.get('days', 30)
        
        logger.info(f"Received ingestion request: mode={mode}, days={days}")
        
        # Initialize clients
        bq_client, storage_client = scheduled_data_ingestion.init_clients()
        if not bq_client or not storage_client:
            return jsonify({"status": "error", "message": "Failed to initialize clients"}), 500
        
        # Run the appropriate ingestion mode
        if mode == 'backfill':
            scheduled_data_ingestion.run_backfill(bq_client, days)
        else:
            scheduled_data_ingestion.run_incremental(bq_client)
        
        return jsonify({
            "status": "success",
            "message": f"Data ingestion ({mode}) completed successfully"
        })
    
    except Exception as e:
        logger.error(f"Error running data ingestion: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable or default to 8080
    port = int(os.environ.get('PORT', 8080))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port)
