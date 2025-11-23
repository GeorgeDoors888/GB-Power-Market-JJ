#!/usr/bin/env python3
"""
Simple HTTP health check server for UpCloud monitoring
Deploy on UpCloud server, exposes health status on port 8080
"""

from flask import Flask, jsonify
import subprocess
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    """Return server health status"""
    
    checks = {
        'iris_pipeline': check_iris_service(),
        'cron': check_cron_service(),
        'disk_space': check_disk_space(),
        'memory': check_memory()
    }
    
    # Overall status
    all_healthy = all(checks.values())
    status = 'healthy' if all_healthy else 'degraded'
    
    response = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'server': 'upcloud-gb-power-market',
        'checks': {
            'iris_pipeline': 'pass' if checks['iris_pipeline'] else 'fail',
            'cron': 'pass' if checks['cron'] else 'fail',
            'disk_space': 'pass' if checks['disk_space'] else 'fail',
            'memory': 'pass' if checks['memory'] else 'fail'
        }
    }
    
    return jsonify(response), 200 if all_healthy else 503

def check_iris_service():
    """Check if IRIS pipeline service is running"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'iris-pipeline'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_cron_service():
    """Check if cron is running"""
    try:
        result = subprocess.run(
            ['pgrep', 'cron'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_disk_space():
    """Check if disk space > 20% free"""
    try:
        result = subprocess.run(
            ['df', '-h', '/'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 5:
                use_pct = int(parts[4].replace('%', ''))
                return use_pct < 80  # Less than 80% used
        return False
    except:
        return False

def check_memory():
    """Check if memory usage < 80%"""
    try:
        result = subprocess.run(
            ['free', '-m'],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 3:
                total = int(parts[1])
                used = int(parts[2])
                use_pct = (used / total * 100) if total > 0 else 0
                return use_pct < 80
        return False
    except:
        return False

@app.route('/')
def index():
    """Simple status page"""
    return """
    <html>
    <head><title>UpCloud Health Check</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>UpCloud Server Health Check</h1>
        <p>Monitoring endpoint for failover system</p>
        <p><a href="/health">Check Health Status</a></p>
        <hr>
        <p><small>GB Power Market - Dual Server Architecture</small></p>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("="*60)
    print("🏥 UPCLOUD HEALTH CHECK SERVER")
    print("="*60)
    print("Starting on port 8080...")
    print("Endpoints:")
    print("  / - Status page")
    print("  /health - JSON health check")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
