#!/usr/bin/env python3
"""
Investigate the discrepancy between BMRS website documentation 
and the Insights API we're using
"""

import httpx
from datetime import datetime, timedelta

print('='*80)
print('🔍 BMRS vs INSIGHTS API INVESTIGATION')
print('='*80)

print('\n📚 KEY FINDING:')
print('-'*80)
print('The user found documentation at: https://bmrs.elexon.co.uk/api-documentation')
print('We are using API at: https://data.elexon.co.uk/bmrs/api/v1')
print()
print('THESE ARE DIFFERENT SYSTEMS!')
print()
print('1. BMRS Website (bmrs.elexon.co.uk)')
print('   - Web interface with charts and tables')
print('   - Has its own API endpoints')
print('   - May have different data availability')
print()
print('2. Insights API (data.elexon.co.uk)')  
print('   - RESTful API for programmatic access')
print('   - Different endpoint structure')
print('   - This is what we\'ve been using')

# Test if BMRS API exists
print('\n' + '='*80)
print('🧪 TESTING DIFFERENT API BASES')
print('='*80)

apis_to_test = [
    ('Insights API (current)', 'https://data.elexon.co.uk/bmrs/api/v1'),
    ('BMRS API (legacy?)', 'https://api.bmreports.com/BMRS'),
    ('BMRS Direct', 'https://bmrs.elexon.co.uk/api'),
]

client = httpx.Client(timeout=30.0)

for name, base_url in apis_to_test:
    print(f'\n{name}: {base_url}')
    
    test_endpoints = [
        '/balancing/physical',
        '/balancing/acceptances',
        '/demand/peak/triad'
    ]
    
    for endpoint in test_endpoints:
        url = base_url + endpoint
        try:
            response = client.get(url, params={'format': 'json'}, follow_redirects=True)
            print(f'  {endpoint}: HTTP {response.status_code}')
        except Exception as e:
            print(f'  {endpoint}: Error - {str(e)[:50]}')

client.close()

print('\n' + '='*80)
print('💡 RECOMMENDATIONS')
print('='*80)
print()
print('1. CHECK API DOCUMENTATION:')
print('   Visit: https://data.elexon.co.uk/')
print('   Look for: Official API documentation for Insights API')
print()
print('2. POSSIBLE EXPLANATIONS:')
print('   a) These endpoints exist in BMRS website but not Insights API')
print('   b) Endpoints require BMU-specific parameters (not date ranges)')
print('   c) Different authentication or access required')
print('   d) Data available through different aggregated endpoints')
print()
print('3. NEXT STEPS:')
print('   - Review Insights API documentation carefully')
print('   - Check if BMU-level data needs BMU IDs as parameters')
print('   - Test with single-day requests for NONBM_VOLUMES')
print('   - Consider using dataset stream format: /datasets/{CODE}/stream')
