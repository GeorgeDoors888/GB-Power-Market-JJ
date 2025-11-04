#!/usr/bin/env python3
"""
Identify and log problematic files that fail extraction
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.config import load_settings
from tqdm import tqdm

cfg = load_settings()
client = bq_client()

print("🔍 IDENTIFYING PROBLEMATIC FILES")
print("=" * 70)

# Get first 100 documents to test
print("\n1. Getting first 100 unprocessed documents...")
sql = f"""
SELECT doc_id, name, mime_type 
FROM `{client.project}.{cfg['dataset']}.documents_clean`
WHERE mime_type IN (
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation'
)
AND doc_id NOT IN (
  SELECT DISTINCT doc_id FROM `{client.project}.{cfg['dataset']}.chunks`
)
LIMIT 100
"""

docs = list(client.query(sql).result())
print(f"✅ Found {len(docs)} documents to test\n")

# Test each file
print("2. Testing file extraction...")
failed_files = []
success_count = 0

for doc in tqdm(docs, desc="Testing"):
    try:
        # Download
        file_bytes = download_pdf(doc.doc_id)
        
        # Extract based on type
        if doc.mime_type == "application/pdf":
            text, _ = extract_pdf_text(file_bytes, cfg["extract"]["ocr_mode"])
        elif doc.mime_type.endswith(".wordprocessingml.document"):
            text = extract_docx_text(file_bytes)
        elif doc.mime_type.endswith(".presentationml.presentation"):
            text = extract_pptx_text(file_bytes)
        else:
            continue
        
        if text and len(text) > 0:
            success_count += 1
        else:
            failed_files.append({
                "doc_id": doc.doc_id,
                "name": doc.name,
                "error": "Empty text extracted"
            })
    except Exception as e:
        failed_files.append({
            "doc_id": doc.doc_id,
            "name": doc.name,
            "error": str(e)
        })

# Results
print(f"\n📊 Results:")
print(f"   ✅ Successful: {success_count}")
print(f"   ❌ Failed: {len(failed_files)}")

if failed_files:
    print(f"\n⚠️  Problematic Files:")
    print("-" * 70)
    for i, f in enumerate(failed_files[:10], 1):
        print(f"\n{i}. {f['name'][:50]}")
        print(f"   ID: {f['doc_id']}")
        print(f"   Error: {f['error'][:100]}")
    
    if len(failed_files) > 10:
        print(f"\n... and {len(failed_files) - 10} more failed files")
    
    # Save to file
    with open("/tmp/failed_files.txt", "w") as f:
        for failed in failed_files:
            f.write(f"{failed['doc_id']}\t{failed['name']}\t{failed['error']}\n")
    
    print(f"\n💾 Full list saved to /tmp/failed_files.txt")
else:
    print("\n✅ All test files extracted successfully!")

print("\n" + "=" * 70)
print(f"💡 Success rate: {success_count}/{len(docs)} ({success_count/len(docs)*100:.1f}%)")
