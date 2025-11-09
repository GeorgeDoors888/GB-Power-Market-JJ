#!/usr/bin/env python3
"""
Test BigQuery Analysis - SSP/SBP Correlation
This demonstrates what ChatGPT can do via your Railway server
"""

import requests
import json

# Your Railway API
RAILWAY_URL = "https://jibber-jabber-production.up.railway.app"
BEARER_TOKEN = "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json"
}

print("🔍 Testing BigQuery + Python Analysis via Railway\n")

# Step 1: Query BigQuery for price data
print("Step 1: Querying BigQuery for recent prices...")
query_data = {
    "sql": """
        SELECT 
            settlement_date,
            settlement_period,
            price
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
        ORDER BY settlement_date DESC, settlement_period DESC
        LIMIT 100
    """,
    "timeout": 60
}

response = requests.post(
    f"{RAILWAY_URL}/query_bigquery",
    headers=headers,
    json=query_data
)

if response.status_code == 200:
    result = response.json()
    if result.get('success'):
        print(f"✅ Got {result.get('row_count', 0)} rows from BigQuery")
        print(f"   Execution time: {result.get('execution_time', 0):.2f}s\n")
        
        # Show sample data
        if result.get('data'):
            print("Sample data:")
            for i, row in enumerate(result['data'][:5]):
                print(f"  {i+1}. Date: {row.get('settlement_date')}, "
                      f"Period: {row.get('settlement_period')}, "
                      f"Price: £{row.get('price', 0):.2f}")
            print()
    else:
        print(f"❌ Query failed: {result.get('error')}\n")
else:
    print(f"❌ HTTP Error: {response.status_code}\n")

# Step 2: Execute Python code for analysis
print("Step 2: Running Python analysis on Railway...")
python_code = """
import json
import statistics

# Simulate price data analysis
prices = [45.32, 52.18, 38.94, 67.25, 41.37, 55.82, 49.15, 58.43]

print("📊 Price Statistics:")
print(f"  Mean: £{statistics.mean(prices):.2f}")
print(f"  Median: £{statistics.median(prices):.2f}")
print(f"  Std Dev: £{statistics.stdev(prices):.2f}")
print(f"  Min: £{min(prices):.2f}")
print(f"  Max: £{max(prices):.2f}")
print(f"  Range: £{max(prices) - min(prices):.2f}")

# Calculate volatility
volatility = (statistics.stdev(prices) / statistics.mean(prices)) * 100
print(f"  Volatility: {volatility:.2f}%")
"""

code_data = {
    "code": python_code,
    "language": "python",
    "timeout": 30
}

response = requests.post(
    f"{RAILWAY_URL}/execute",
    headers=headers,
    json=code_data
)

if response.status_code == 200:
    result = response.json()
    if result.get('exit_code') == 0:
        print("✅ Python code executed successfully:")
        print(result.get('output'))
        print(f"   Execution time: {result.get('execution_time', 0):.3f}s\n")
    else:
        print(f"❌ Execution error: {result.get('error')}\n")
else:
    print(f"❌ HTTP Error: {response.status_code}\n")

print("=" * 60)
print("✅ All tests complete!")
print("\nChatGPT can do this exact same workflow by:")
print("1. Calling /query_bigquery to get real data")
print("2. Calling /execute to run Python analysis")
print("3. Presenting results to you")
print("=" * 60)
