import sys
sys.path.insert(0, "/app")
from src.auth.google_auth import bq_client

client = bq_client()

query = """
WITH processed_docs AS (
  SELECT DISTINCT doc_id FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`
)
SELECT 
  CASE 
    WHEN size_bytes < 100000 THEN '< 100KB'
    WHEN size_bytes < 500000 THEN '100KB - 500KB'
    WHEN size_bytes < 1000000 THEN '500KB - 1MB'
    WHEN size_bytes < 5000000 THEN '1MB - 5MB'
    WHEN size_bytes < 10000000 THEN '5MB - 10MB'
    WHEN size_bytes < 50000000 THEN '10MB - 50MB'
    ELSE '> 50MB'
  END as size_range,
  COUNT(*) as doc_count,
  ROUND(AVG(size_bytes)/1024/1024, 2) as avg_mb,
  ROUND(MIN(size_bytes)/1024/1024, 2) as min_mb,
  ROUND(MAX(size_bytes)/1024/1024, 2) as max_mb
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
WHERE mime_type IN (
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
AND id NOT IN (SELECT doc_id FROM processed_docs)
GROUP BY size_range
ORDER BY 
  CASE size_range
    WHEN '< 100KB' THEN 1
    WHEN '100KB - 500KB' THEN 2
    WHEN '500KB - 1MB' THEN 3
    WHEN '1MB - 5MB' THEN 4
    WHEN '5MB - 10MB' THEN 5
    WHEN '10MB - 50MB' THEN 6
    ELSE 7
  END
"""

print("\n📊 FILE SIZE DISTRIBUTION OF REMAINING DOCUMENTS:\n")
print(f"{'Size Range':<15} {'Count':<10} {'Avg MB':<10} {'Min MB':<10} {'Max MB':<10}")
print("=" * 60)

for row in client.query(query):
    print(f"{row.size_range:<15} {row.doc_count:<10} {row.avg_mb:<10} {row.min_mb:<10} {row.max_mb:<10}")

total_query = """
WITH processed_docs AS (
  SELECT DISTINCT doc_id FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`
)
SELECT 
  COUNT(*) as total_remaining,
  ROUND(AVG(size_bytes)/1024/1024, 2) as avg_mb,
  ROUND(SUM(size_bytes)/1024/1024/1024, 2) as total_gb
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
WHERE mime_type IN (
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
AND id NOT IN (SELECT doc_id FROM processed_docs)
"""

print("\n" + "=" * 60)
for row in client.query(total_query):
    print(f"\n📈 TOTAL REMAINING: {row.total_remaining:,} documents")
    print(f"📏 AVERAGE SIZE: {row.avg_mb} MB per document")
    print(f"💾 TOTAL DATA: {row.total_gb} GB to process")
