#!/usr/bin/env python3
from google.cloud import bigquery
from google.oauth2 import service_account

creds = service_account.Credentials.from_service_account_file("/secrets/sa.json")
client = bigquery.Client(project="inner-cinema-476211-u9", credentials=creds)

query = """
SELECT 
  COUNT(*) as total_docs,
  COUNT(DISTINCT mime_type) as file_types
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""

result = list(client.query(query).result())
print(f"✅ Documents indexed: {result[0].total_docs}")
print(f"📋 File types: {result[0].file_types}")

# Show breakdown by type
query2 = """
SELECT mime_type, COUNT(*) as count
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
GROUP BY mime_type
ORDER BY count DESC
"""
results = list(client.query(query2).result())
print("\nBreakdown by type:")
for row in results:
    print(f"  - {row.mime_type}: {row.count} files")
