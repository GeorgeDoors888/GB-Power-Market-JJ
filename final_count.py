#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv("/app/.env")
import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

bq = bq_client()

# Total count
query = "SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_insights.documents`"
result = bq.query(query).result()
for row in result:
    print(f"✅ TOTAL DOCUMENTS INDEXED: {row.total:,}")

# Breakdown by type
query2 = """
SELECT mime_type, COUNT(*) as count 
FROM `inner-cinema-476211-u9.uk_energy_insights.documents` 
GROUP BY mime_type 
ORDER BY count DESC 
LIMIT 10
"""
print("\n📊 Top 10 File Types:")
result2 = bq.query(query2).result()
for row in result2:
    type_name = row.mime_type.split("/")[-1] if "/" in row.mime_type else row.mime_type
    print(f"  {row.count:>6,} × {type_name}")

# Key file types
query3 = """
SELECT 
  SUM(CASE WHEN mime_type = 'application/pdf' THEN 1 ELSE 0 END) as pdfs,
  SUM(CASE WHEN mime_type = 'application/vnd.google-apps.spreadsheet' THEN 1 ELSE 0 END) as sheets,
  SUM(CASE WHEN mime_type = 'application/vnd.google-apps.document' THEN 1 ELSE 0 END) as docs
FROM `inner-cinema-476211-u9.uk_energy_insights.documents`
"""
print("\n📄 Key Document Types:")
result3 = bq.query(query3).result()
for row in result3:
    print(f"  PDFs: {row.pdfs:,}")
    print(f"  Google Sheets: {row.sheets:,}")
    print(f"  Google Docs: {row.docs:,}")
