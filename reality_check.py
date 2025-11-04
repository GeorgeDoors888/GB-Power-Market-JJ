import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")
from src.auth.google_auth import bq_client

bq = bq_client()

print("📊 REALITY CHECK - TIME ESTIMATE")
print("=" * 70)

# Get counts by type
query1 = """
SELECT mime_type, COUNT(*) as count
FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
WHERE mime_type IN (
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
GROUP BY mime_type
"""

result = bq.query(query1).result()
total = 0
for row in result:
    mime = row.mime_type.split('/')[-1].replace('vnd.openxmlformats-officedocument.', '')
    print(f"  {mime[:50]:<50} {row.count:>8,}")
    total += row.count

print("=" * 70)
print(f"  {'TOTAL DOCUMENTS':<50} {total:>8,}")

# Already processed
query2 = "SELECT COUNT(DISTINCT doc_id) as done FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`"
result2 = bq.query(query2).result()
for row in result2:
    done = row.done
    remaining = total - done
    print(f"  {'Already processed':<50} {done:>8,}")
    print(f"  {'Remaining':<50} {remaining:>8,}")
    
    print("\n⏱️  TIME ESTIMATES:")
    print("-" * 70)
    print(f"  At 12 sec/doc:  {remaining * 12 / 3600:>6.0f} hours  ({remaining * 12 / 3600 / 24:>4.1f} days)")
    print(f"  At 8 sec/doc:   {remaining * 8 / 3600:>6.0f} hours  ({remaining * 8 / 3600 / 24:>4.1f} days)")  
    print(f"  At 5 sec/doc:   {remaining * 5 / 3600:>6.0f} hours  ({remaining * 5 / 3600 / 24:>4.1f} days)")
    print(f"  At 3 sec/doc:   {remaining * 3 / 3600:>6.0f} hours  ({remaining * 3 / 3600 / 24:>4.1f} days)")

print("\n" + "=" * 70)
print("💡 This is just HOW LONG IT TAKES to process PDFs from Drive.")
print("   There's no magic fix - it's limited by API speed & PDF parsing.")
