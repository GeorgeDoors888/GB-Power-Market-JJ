#!/usr/bin/env python3
"""
Extraction with future timeouts - works with threading
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from tqdm import tqdm
from datetime import datetime
import threading

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.chunking import into_chunks
from src.storage.bigquery import ensure_tables, load_rows
from src.config import load_settings

ERROR_LOG = "/tmp/extraction_errors_simple.log"
SUCCESS_LOG = "/tmp/extraction_success_simple.log"
TIMEOUT_SECONDS = 45  # 45 second timeout per document

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def log_success(doc_id, name, num_chunks):
    with open(SUCCESS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{num_chunks}\n")

def process_document(doc_row, cfg, dataset):
    """Process document - simple version"""
    try:
        # Download
        file_bytes = download_pdf(doc_row.doc_id)
        
        # Extract
        if doc_row.mime_type == "application/pdf":
            text, _ = extract_pdf_text(file_bytes, cfg["extract"]["ocr_mode"])
        elif doc_row.mime_type.endswith(".wordprocessingml.document"):
            text = extract_docx_text(file_bytes)
        elif doc_row.mime_type.endswith(".presentationml.presentation"):
            text = extract_pptx_text(file_bytes)
        else:
            return {"status": "skip", "doc_id": doc_row.doc_id}
        
        if not text or len(text.strip()) == 0:
            log_error(doc_row.doc_id, doc_row.name, "Empty text")
            return {"status": "empty", "doc_id": doc_row.doc_id}
        
        # Chunk
        chunk_size = int(cfg["chunk"]["size"])
        chunk_overlap = int(cfg["chunk"]["overlap"])
        chunks = []
        for i, chunk, tok in into_chunks(text, chunk_size, chunk_overlap):
            chunks.append({
                "doc_id": doc_row.doc_id,
                "chunk_id": f"{doc_row.doc_id}:{i}",
                "page_from": None,
                "page_to": None,
                "n_chars": len(chunk),
                "n_tokens_est": tok,
                "text": chunk,
            })
        
        # SAVE IMMEDIATELY
        if chunks:
            load_rows(dataset, "chunks", chunks)
            log_success(doc_row.doc_id, doc_row.name, len(chunks))
            return {"status": "success", "doc_id": doc_row.doc_id, "chunks": len(chunks)}
        else:
            return {"status": "no_chunks", "doc_id": doc_row.doc_id}
            
    except Exception as e:
        log_error(doc_row.doc_id, doc_row.name, str(e))
        return {"status": "error", "doc_id": doc_row.doc_id, "error": str(e)}

def main():
    cfg = load_settings()
    dataset = cfg["dataset"]
    ensure_tables(dataset)
    client = bq_client()
    
    print("⚡ SIMPLE EXTRACTION WITH FUTURE TIMEOUTS")
    print(f"⏱️  {TIMEOUT_SECONDS}s timeout per document")
    print("=" * 70)
    
    # Clear logs
    with open(ERROR_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\terror\n")
    with open(SUCCESS_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\tnum_chunks\n")
    
    # Get unprocessed documents  
    print("\n🔍 Getting documents...")
    sql_processed = f"SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`"
    processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
    print(f"✅ {len(processed_ids):,} already done")
    
    # Get documents NOT in the processed set
    sql = f"""
      SELECT doc_id, name, mime_type 
      FROM `{client.project}.{dataset}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
      AND doc_id NOT IN (
        SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`
      )
      LIMIT 5000
    """
    docs = list(client.query(sql).result())
    print(f"📄 Processing {len(docs):,} documents\n")
    
    if len(docs) == 0:
        print("✅ No documents to process!")
        return
    
    # Process with 4 workers
    max_workers = 4
    print(f"⚡ {max_workers} workers | ⏱️  {TIMEOUT_SECONDS}s timeout | 💾 Immediate save\n")
    
    stats = {"success": 0, "error": 0, "empty": 0, "timeout": 0, "total_chunks": 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_document, doc, cfg, dataset): doc for doc in docs}
        
        with tqdm(total=len(docs), unit="doc") as pbar:
            for future in as_completed(futures):
                doc = futures[future]
                try:
                    # Wait for result with timeout
                    result = future.result(timeout=TIMEOUT_SECONDS)
                    
                    if result["status"] == "success":
                        stats["success"] += 1
                        stats["total_chunks"] += result.get("chunks", 0)
                    elif result["status"] == "error":
                        stats["error"] += 1
                    elif result["status"] == "empty":
                        stats["empty"] += 1
                    
                except TimeoutError:
                    log_error(doc.doc_id, doc.name, f"TIMEOUT after {TIMEOUT_SECONDS}s")
                    stats["timeout"] += 1
                except Exception as e:
                    log_error(doc.doc_id, doc.name, f"Future error: {str(e)}")
                    stats["error"] += 1
                
                pbar.update(1)
                
                # Print stats every 100 documents
                total_processed = stats["success"] + stats["error"] + stats["empty"] + stats["timeout"]
                if total_processed % 100 == 0 and total_processed > 0:
                    success_rate = (stats["success"] / total_processed * 100)
                    avg_chunks = (stats["total_chunks"] / stats["success"]) if stats["success"] > 0 else 0
                    pbar.write(f"\n📊 {stats['success']} ✅ | {stats['error']} ❌ | {stats['timeout']} ⏱️  | {stats['empty']} ⚠️")
                    pbar.write(f"   {success_rate:.1f}% success | {avg_chunks:.0f} chunks/doc | {stats['total_chunks']:,} total chunks\n")
    
    print(f"\n✅ EXTRACTION COMPLETE!")
    print(f"   Success: {stats['success']:,} docs ({stats['total_chunks']:,} chunks)")
    print(f"   Errors: {stats['error']:,} docs")
    print(f"   Timeouts: {stats['timeout']:,} docs")
    print(f"   Empty: {stats['empty']:,} docs")
    
    # Final database check
    print(f"\n🔍 Verifying database...")
    sql_check = f"SELECT COUNT(DISTINCT doc_id) as doc_count FROM `{client.project}.{dataset}.chunks`"
    result = list(client.query(sql_check).result())[0]
    print(f"✅ Total documents in database: {result.doc_count:,}")

if __name__ == "__main__":
    main()
