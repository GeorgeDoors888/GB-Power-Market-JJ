#!/usr/bin/env python3
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")
from src.auth.google_auth import bq_client

bq = bq_client()
print("🔍 Testing documents_clean table access...")

# Test 1: Count rows
query1 = "SELECT COUNT(*) as count FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`"
result = bq.query(query1).result()
for row in result:
    print(f"✅ Total unique files: {row.count:,}")

# Test 2: Sample data
query2 = """
SELECT name, mime_type, size_bytes 
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean` 
LIMIT 3
"""
result = bq.query(query2).result()
print("\n📄 Sample files:")
for row in result:
    print(f"  - {row.name[:50]:<50} | {row.mime_type[:30]:<30} | {row.size_bytes:>10,} bytes")

print("\n✅ documents_clean table is working correctly!")
