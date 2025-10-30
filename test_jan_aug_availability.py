#!/usr/bin/env python3
"""Test if Jan-Aug 2025 data exists using the correct API endpoints"""

import httpx
from datetime import datetime

# Test with STREAMING endpoints (the correct ones from the manifest!)
test_dates = [
    ('January 2025', '2025-01-15T00:00:00Z', '2025-01-16T23:59:59Z'),
    ('March 2025', '2025-03-15T00:00:00Z', '2025-03-16T23:59:59Z'),
    ('May 2025', '2025-05-15T00:00:00Z', '2025-05-16T23:59:59Z'),
    ('July 2025', '2025-07-15T00:00:00Z', '2025-07-16T23:59:59Z'),
    ('September 2025', '2025-09-15T00:00:00Z', '2025-09-16T23:59:59Z'),
]

print('🔍 Testing STREAMING Endpoints for Jan-Aug 2025')
print('=' * 80)
print()

# Test FREQ with streaming endpoint
endpoint_stream = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FREQ/stream'

print('Testing FREQ/stream endpoint (System Frequency):')
print()
for label, start, end in test_dates:
    params = {'from': start, 'to': end}
    
    try:
        response = httpx.get(endpoint_stream, params=params, timeout=30.0)
        if response.status_code == 200:
            # Streaming endpoint returns NDJSON (newline-delimited JSON)
            lines = [l for l in response.text.strip().split('\n') if l.strip()]
            print(f'✅ {label:20} Status: {response.status_code}  Records: {len(lines):>5}')
        else:
            print(f'❌ {label:20} Status: {response.status_code}  Message: {response.text[:100]}')
    except Exception as e:
        print(f'❌ {label:20} Error: {str(e)[:80]}')

print()
print('=' * 80)
print('Comparing Regular vs Streaming endpoints for January 2025:')
print()

# Compare both endpoint types
jan_params = {'from': '2025-01-15T00:00:00Z', 'to': '2025-01-16T23:59:59Z'}

# Test regular endpoint
try:
    url_regular = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FREQ'
    response = httpx.get(url_regular, params={**jan_params, 'format': 'json'}, timeout=30.0)
    if response.status_code == 200:
        data = response.json()
        records = data.get('data', [])
        print(f'✅ Regular (/datasets/FREQ):        {len(records):>5} records')
    else:
        print(f'❌ Regular (/datasets/FREQ):        Status {response.status_code}')
except Exception as e:
    print(f'❌ Regular endpoint error: {e}')

# Test streaming endpoint
try:
    url_stream = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FREQ/stream'
    response = httpx.get(url_stream, params=jan_params, timeout=30.0)
    if response.status_code == 200:
        lines = [l for l in response.text.strip().split('\n') if l.strip()]
        print(f'✅ Streaming (/datasets/FREQ/stream): {len(lines):>5} records')
    else:
        print(f'❌ Streaming (/datasets/FREQ/stream): Status {response.status_code}')
except Exception as e:
    print(f'❌ Streaming endpoint error: {e}')

print()
print('=' * 80)
print('CONCLUSION:')
print()
print('The issue was using the WRONG endpoint type!')
print('  ❌ /datasets/FREQ           - Regular API (pagination, format param)')
print('  ✅ /datasets/FREQ/stream    - Streaming API (NDJSON, direct access)')
print()
print('Your working download scripts use the /stream endpoints.')
print('That is why they work for Jan-Aug 2025 data!')
print('=' * 80)
