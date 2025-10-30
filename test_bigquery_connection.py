#!/usr/bin/env python3
"""
Test BigQuery connection and authentication
"""
import os
from google.cloud import bigquery

# Set project
os.environ["GOOGLE_CLOUD_PROJECT"] = "jibber-jabber-knowledge"

print("🔐 Testing BigQuery Connection...")
print("=" * 50)

try:
    # Initialize client
    client = bigquery.Client(project="jibber-jabber-knowledge")
    
    print(f"✅ Client initialized")
    print(f"   Project: {client.project}")
    print(f"   Location: {client.location}")
    
    # Test query
    print("\n📊 Testing query access...")
    query = """
        SELECT table_name, creation_time
        FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
        ORDER BY creation_time DESC
        LIMIT 5
    """
    
    results = client.query(query)
    
    print("✅ Query successful!")
    print("\nRecent tables:")
    for row in results:
        print(f"   - {row.table_name} (created: {row.creation_time})")
    
    print("\n🎉 BigQuery connection working perfectly!")
    print("   Ready to run bulk_downloader.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Complete the authentication in your browser")
    print("2. Run: gcloud auth application-default login")
    print("3. Run: gcloud config set project jibber-jabber-knowledge")
    exit(1)
