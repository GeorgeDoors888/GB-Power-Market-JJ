#!/usr/bin/env python3
"""
Working extraction - skips known bad files and randomizes order
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.chunking import into_chunks
from src.storage.bigquery import ensure_tables, load_rows
from src.config import load_settings

ERROR_LOG = "/tmp/extraction_errors_working.log"
SUCCESS_LOG = "/tmp/extraction_success_working.log"

# Known corrupted files to skip
SKIP_FILES = {
    "1zsP5LWPuaeIp-yRK9j9Tpw9KKvwVNSjT",  # 08a02.pdf
    "1vsfXUs1r9Fg5DAxfQmK9KoiOCBy_evJe",  # 08a02.pdf
    "1hwjxyZeYwfH5ttYtVS1stoOAO8CTFA9z",  # 2149u-overhead-line
    "1oruh4NbX6Z6VGKZTw1FPhavADiRESr_P",  # 2149u-overhead-line
    "18W1Gqub_VRGk1NBJbB18SPIZaq5adVJ_",  # 2229u-overhead-line
    "1SjAnGa-LgQVecMyD5g-zAOLKBUZ8ggle",  # 2229u-overhead-line
    "1ZC3f1QdjUs3YAC6sJvHtxH-2FFylhbsn",  # 7386.pdf
    "12dkwVuiq9dR3UIszvGxuHU3eHyxc7qek",  # 7386.pdf
}

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def log_success(doc_id, name, num_chunks):
    with open(SUCCESS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{num_chunks}\n")

def process_document(doc_row, cfg, dataset):
    """Process one document and save immediately"""
    doc_id = doc_row.doc_id
    
    # Skip known bad files
    if doc_id in SKIP_FILES:
        log_error(doc_id, doc_row.name, "SKIPPED - Known corrupted file")
        return {"status": "skipped", "doc_id": doc_id}
    
    try:
        # Download with timeout handling
        file_bytes = download_pdf(doc_id)
        
        # Extract based on type
        if doc_row.mime_type == "application/pdf":
            text, _ = extract_pdf_text(file_bytes, cfg["extract"]["ocr_mode"])
        elif doc_row.mime_type.endswith(".wordprocessingml.document"):
            text = extract_docx_text(file_bytes)
        elif doc_row.mime_type.endswith(".presentationml.presentation"):
            text = extract_pptx_text(file_bytes)
        else:
            return {"status": "skip", "doc_id": doc_id}
        
        if not text or len(text.strip()) == 0:
            log_error(doc_id, doc_row.name, "Empty text after extraction")
            return {"status": "empty", "doc_id": doc_id}
        
        # Create chunks
        chunk_size = int(cfg["chunk"]["size"])
        chunk_overlap = int(cfg["chunk"]["overlap"])
        chunks = []
        
        for i, chunk, tok in into_chunks(text, chunk_size, chunk_overlap):
            chunks.append({
                "doc_id": doc_id,
                "chunk_id": f"{doc_id}:{i}",
                "page_from": None,
                "page_to": None,
                "n_chars": len(chunk),
                "n_tokens_est": tok,
                "text": chunk,
            })
        
        # Save immediately if we got chunks
        if chunks:
            load_rows(dataset, "chunks", chunks)
            log_success(doc_id, doc_row.name, len(chunks))
            return {"status": "success", "doc_id": doc_id, "chunks": len(chunks)}
        else:
            log_error(doc_id, doc_row.name, "No chunks created")
            return {"status": "no_chunks", "doc_id": doc_id}
            
    except Exception as e:
        error_msg = str(e)[:200]  # Truncate long errors
        log_error(doc_id, doc_row.name, error_msg)
        return {"status": "error", "doc_id": doc_id}

def main():
    cfg = load_settings()
    dataset = cfg["dataset"]
    ensure_tables(dataset)
    client = bq_client()
    
    print("🚀 WORKING EXTRACTION")
    print("✅ Skips known corrupted files")
    print("🔀 Randomizes processing order")
    print("=" * 70)
    
    # Initialize logs
    with open(ERROR_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\terror\n")
    with open(SUCCESS_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\tnum_chunks\n")
    
    # Get already processed
    print("\n🔍 Checking processed documents...")
    sql_processed = f"SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`"
    processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
    print(f"✅ {len(processed_ids):,} already processed")
    print(f"🚫 Skipping {len(SKIP_FILES)} known corrupted files")
    
    # Get documents to process - use ORDER BY RAND() to randomize
    sql = f"""
      SELECT doc_id, name, mime_type 
      FROM `{client.project}.{dataset}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
      ORDER BY RAND()
      LIMIT 10000
    """
    print("\n📥 Fetching documents (randomized order)...")
    all_docs = list(client.query(sql).result())
    
    # Filter out processed and bad files
    docs = [d for d in all_docs if d.doc_id not in processed_ids and d.doc_id not in SKIP_FILES]
    print(f"📄 Processing {len(docs):,} documents\n")
    
    if len(docs) == 0:
        print("⚠️  No documents to process!")
        return
    
    # Process with 4 workers
    max_workers = 4
    print(f"⚡ {max_workers} workers | 💾 Immediate save after each doc\n")
    
    stats = {"success": 0, "error": 0, "empty": 0, "skipped": 0, "total_chunks": 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = {executor.submit(process_document, doc, cfg, dataset): doc for doc in docs}
        
        # Process as they complete
        for future in tqdm(as_completed(futures), total=len(docs), unit="doc"):
            try:
                result = future.result(timeout=60)  # 60 second timeout per doc
                
                if result["status"] == "success":
                    stats["success"] += 1
                    stats["total_chunks"] += result.get("chunks", 0)
                elif result["status"] == "error":
                    stats["error"] += 1
                elif result["status"] == "empty":
                    stats["empty"] += 1
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                
                # Print progress every 100 docs
                total = stats["success"] + stats["error"] + stats["empty"] + stats["skipped"]
                if total % 100 == 0 and total > 0:
                    success_rate = (stats["success"] / total * 100) if total > 0 else 0
                    avg_chunks = (stats["total_chunks"] / stats["success"]) if stats["success"] > 0 else 0
                    print(f"\n📊 Progress: {total:,} docs")
                    print(f"   ✅ {stats['success']:,} success ({success_rate:.1f}%)")
                    print(f"   ❌ {stats['error']:,} errors")
                    print(f"   📦 {stats['total_chunks']:,} chunks ({avg_chunks:.0f} avg/doc)")
                    
            except Exception as e:
                print(f"\n⚠️  Future exception: {str(e)[:100]}")
                stats["error"] += 1
    
    print(f"\n✅ BATCH COMPLETE!")
    print(f"   Success: {stats['success']:,} docs")
    print(f"   Errors: {stats['error']:,} docs")
    print(f"   Empty: {stats['empty']:,} docs")
    print(f"   Skipped: {stats['skipped']:,} docs")
    print(f"   Total chunks: {stats['total_chunks']:,}")
    
    if stats['success'] > 0:
        print(f"\n🎉 Successfully saved {stats['total_chunks']:,} chunks to BigQuery!")
        print(f"   Average: {stats['total_chunks'] / stats['success']:.1f} chunks per document")

if __name__ == "__main__":
    main()
