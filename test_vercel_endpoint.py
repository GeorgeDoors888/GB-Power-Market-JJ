#!/usr/bin/env python3
"""
Test the Vercel API endpoint directly to see what error we're getting
"""

import requests
import json
from datetime import datetime

VERCEL_ENDPOINT = "https://gb-power-market-jj.vercel.app/api/proxy-v2"

# Test query - simplified version of what Apps Script should send
test_query = """
SELECT 
  settlementDate,
  settlementPeriod,
  imbalancePriceAmountGBP as ssp,
  netImbalanceVolumeMAW as niv
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate = CURRENT_DATE('Europe/London')
ORDER BY settlementPeriod
LIMIT 5
"""

print("=" * 70)
print("🧪 TESTING VERCEL API ENDPOINT")
print("=" * 70)
print()
print(f"Endpoint: {VERCEL_ENDPOINT}")
print()
print("Query:")
print(test_query)
print()

try:
    print("📋 Sending request...")
    response = requests.post(
        VERCEL_ENDPOINT,
        json={"query": test_query},
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print()
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print()
        print("Response:")
        print(json.dumps(data, indent=2)[:1000])  # First 1000 chars
    else:
        print("❌ ERROR!")
        print()
        print("Response:")
        print(response.text[:1000])
        
except Exception as e:
    print(f"❌ Exception: {e}")
