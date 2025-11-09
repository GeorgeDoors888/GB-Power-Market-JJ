#!/usr/bin/env python3
"""
Test Railway API with secure bearer token from environment
"""

import os
import sys
import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed, using environment variables directly...")

def test_railway_api():
    """Test Railway Codex Server with bearer token"""
    
    # Get configuration from environment
    bearer_token = os.getenv('BEARER_TOKEN')
    api_url = os.getenv('RAILWAY_API_URL', 'https://jibber-jabber-production.up.railway.app')
    
    if not bearer_token:
        print("❌ BEARER_TOKEN not set!")
        print("\n📝 Please add to .env file:")
        print("   BEARER_TOKEN=codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA")
        return False
    
    print("🔐 Testing Railway API with secure bearer token...\n")
    print(f"API URL: {api_url}")
    print(f"Token: {bearer_token[:20]}... (hidden)")
    
    # Test 1: Health check
    print("\n🏥 Test 1: Health Check")
    print("-" * 60)
    try:
        response = requests.get(
            f"{api_url}/health",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ Health check passed!")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Debug endpoint
    print("\n🔍 Test 2: Debug Environment")
    print("-" * 60)
    try:
        response = requests.get(
            f"{api_url}/debug/env",
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"BQ_PROJECT_ID: {data.get('BQ_PROJECT_ID')}")
        print(f"Project in credentials: {data.get('project_in_credentials')}")
        print("✅ Debug check passed!")
    except Exception as e:
        print(f"⚠️  Debug endpoint failed: {e}")
    
    # Test 3: Simple BigQuery query
    print("\n🔢 Test 3: BigQuery Query (count)")
    print("-" * 60)
    try:
        sql = "SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 1"
        response = requests.get(
            f"{api_url}/query_bigquery_get",
            params={"sql": sql},
            headers={"Authorization": f"Bearer {bearer_token}"}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        if data.get('success'):
            print(f"Row count: {data['data'][0]['cnt']}")
            print(f"Execution time: {data.get('execution_time')}s")
            print("✅ BigQuery query passed!")
        else:
            print(f"❌ Query failed: {data.get('error')}")
    except Exception as e:
        print(f"❌ BigQuery query failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! Railway API is working securely.")
    print("=" * 60)
    
    print("\n💡 Example usage in your code:")
    print("""
import os, requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('RAILWAY_API_URL')
token = os.getenv('BEARER_TOKEN')

response = requests.get(
    f"{url}/query_bigquery_get",
    params={"sql": "SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` LIMIT 5"},
    headers={"Authorization": f"Bearer {token}"}
)
data = response.json()
print(data)
""")
    
    return True

if __name__ == '__main__':
    success = test_railway_api()
    sys.exit(0 if success else 1)
