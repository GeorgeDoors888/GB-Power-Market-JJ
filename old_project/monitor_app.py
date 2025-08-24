#!/usr/bin/env python3
"""
BMRS Collection Progress Monitor
Provides a simple web interface to check download progress
"""

from flask import Flask, jsonify
from collection_stats import CollectionStats
import os

app = Flask(__name__)
BUCKET_NAME = os.getenv('BUCKET_NAME', 'jibber-jabber-knowledge-bmrs-data')

@app.route('/status')
def get_status():
    """Get current collection status"""
    stats = CollectionStats(BUCKET_NAME)
    return jsonify(stats.get_summary())

@app.route('/health')
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
