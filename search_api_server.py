#!/usr/bin/env python3
"""
Search API Server
Flask endpoint for Apps Script to execute searches without manual terminal commands
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

app = Flask(__name__)
CORS(app)  # Allow requests from Google Apps Script

# ============================================================================
# CONFIGURATION
# ============================================================================

SEARCH_SCRIPT = "advanced_search_tool_enhanced.py"
PORT = 5002  # Different from DNO webhook (5001)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Search API Server',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/search', methods=['POST'])
def execute_search():
    """
    Execute search and return results
    
    Request Body:
    {
        "party": "Drax",
        "type": "BM Unit",
        "role": "VLP",
        "bmu": "E_FARNB-1",
        "organization": "Flexgen",
        "from": "2025-01-01",
        "to": "2025-12-31",
        "cap_min": 10,
        "cap_max": 100,
        "gsp": "_A - Eastern (EPN)",
        "dno": "EPN - UK Power Networks Eastern",
        "voltage": "HV (11 kV)"
    }
    
    Response:
    {
        "success": true,
        "results": [...],
        "count": 15,
        "timestamp": "2025-12-31T10:30:00"
    }
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No search criteria provided'
            }), 400
        
        # Build command arguments
        args = ['python3', SEARCH_SCRIPT]
        
        # Add search parameters
        if data.get('party'):
            args.extend(['--party', data['party']])
        
        if data.get('type'):
            args.extend(['--type', data['type']])
        
        if data.get('role'):
            args.extend(['--role', data['role']])
        
        if data.get('bmu'):
            args.extend(['--bmu', data['bmu']])
        
        if data.get('organization'):
            args.extend(['--org', data['organization']])
        
        if data.get('from'):
            args.extend(['--from', data['from']])
        
        if data.get('to'):
            args.extend(['--to', data['to']])
        
        if data.get('cap_min'):
            args.extend(['--cap-min', str(data['cap_min'])])
        
        if data.get('cap_max'):
            args.extend(['--cap-max', str(data['cap_max'])])
        
        if data.get('gsp'):
            args.extend(['--gsp', data['gsp']])
        
        if data.get('dno'):
            args.extend(['--dno', data['dno']])
        
        if data.get('voltage'):
            args.extend(['--voltage', data['voltage']])
        
        # Add output format flag
        args.append('--json')  # Request JSON output
        
        # Execute search
        print(f"🔍 Executing: {' '.join(args)}")
        
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Search failed: {result.stderr}',
                'command': ' '.join(args)
            }), 500
        
        # Parse results
        # Note: advanced_search_tool_enhanced.py needs --json flag support
        # For now, parse stdout as text
        
        lines = result.stdout.strip().split('\n')
        results = []
        
        for line in lines:
            if line.startswith('✅') or line.startswith('🔍') or not line.strip():
                continue
            
            # Try to parse as JSON
            try:
                row = json.loads(line)
                results.append(row)
            except json.JSONDecodeError:
                # Parse as CSV-like output
                parts = line.split('\t')
                if len(parts) >= 11:
                    results.append({
                        'type': parts[0],
                        'id': parts[1],
                        'name': parts[2],
                        'role': parts[3],
                        'organization': parts[4],
                        'extra': parts[5],
                        'capacity': parts[6],
                        'fuel': parts[7],
                        'status': parts[8],
                        'source': parts[9],
                        'score': parts[10]
                    })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'timestamp': datetime.now().isoformat(),
            'command': ' '.join(args)
        })
    
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Search timeout (>30s)'
        }), 504
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/search/validate', methods=['POST'])
def validate_criteria():
    """
    Validate search criteria without executing
    
    Returns:
    {
        "valid": true,
        "warnings": [],
        "command": "python3 advanced_search_tool_enhanced.py ..."
    }
    """
    try:
        data = request.get_json()
        
        warnings = []
        
        # Check for common issues
        if not any([
            data.get('party'),
            data.get('type'),
            data.get('role'),
            data.get('bmu'),
            data.get('organization')
        ]):
            warnings.append('No search criteria specified - will return all results')
        
        # Check date format
        if data.get('from'):
            try:
                datetime.strptime(data['from'], '%d/%m/%Y')
            except ValueError:
                warnings.append('Invalid "from" date format (expected DD/MM/YYYY)')
        
        if data.get('to'):
            try:
                datetime.strptime(data['to'], '%d/%m/%Y')
            except ValueError:
                warnings.append('Invalid "to" date format (expected DD/MM/YYYY)')
        
        # Build command preview
        args = ['python3', SEARCH_SCRIPT]
        
        if data.get('party'):
            args.extend(['--party', f'"{data["party"]}"'])
        if data.get('type'):
            args.extend(['--type', f'"{data["type"]}"'])
        if data.get('role'):
            args.extend(['--role', f'"{data["role"]}"'])
        
        command = ' '.join(args)
        
        return jsonify({
            'valid': len(warnings) == 0,
            'warnings': warnings,
            'command': command
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    print("🚀 Search API Server Starting...")
    print(f"📍 Endpoint: http://localhost:{PORT}/search")
    print(f"🔍 Search script: {SEARCH_SCRIPT}")
    print(f"💚 Health check: http://localhost:{PORT}/health")
    print()
    print("📋 Usage from Apps Script:")
    print("   UrlFetchApp.fetch('http://localhost:5002/search', {")
    print("     method: 'post',")
    print("     contentType: 'application/json',")
    print("     payload: JSON.stringify({party: 'Drax', type: 'BM Unit'})")
    print("   })")
    print()
    print("⚠️  Note: For production, deploy on public server with ngrok or cloud hosting")
    print()
    
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=True
    )
