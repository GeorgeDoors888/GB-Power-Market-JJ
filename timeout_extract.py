#!/usr/bin/env python3
"""
Extraction with timeouts to prevent hanging
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from tqdm import tqdm
from datetime import datetime
from contextlib import contextmanager

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.chunking import into_chunks
from src.storage.bigquery import ensure_tables, load_rows
from src.config import load_settings

ERROR_LOG = "/tmp/extraction_errors_timeout.log"
SUCCESS_LOG = "/tmp/extraction_success_timeout.log"
TIMEOUT_SECONDS = 30  # 30 second timeout per document

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")

@contextmanager
def time_limit(seconds):
    """Context manager for timeout"""
    def signal_handler(signum, frame):
        raise TimeoutException(f"Timed out after {seconds} seconds")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def log_success(doc_id, name, num_chunks):
    with open(SUCCESS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{num_chunks}\n")

def process_with_timeout(doc_row, cfg, dataset):
    """Process document with timeout protection"""
    try:
        with time_limit(TIMEOUT_SECONDS):
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
                
    except TimeoutException as e:
        log_error(doc_row.doc_id, doc_row.name, f"TIMEOUT: {str(e)}")
        return {"status": "timeout", "doc_id": doc_row.doc_id}
    except Exception as e:
        log_error(doc_row.doc_id, doc_row.name, str(e))
        return {"status": "error", "doc_id": doc_row.doc_id, "error": str(e)}

def main():
    cfg = load_settings()
    dataset = cfg["dataset"]
    ensure_tables(dataset)
    client = bq_client()
    
    print("🚀 EXTRACTION WITH TIMEOUTS")
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
    
    sql = f"""
      SELECT doc_id, name, mime_type FROM `{client.project}.{dataset}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
      LIMIT 1000
    """
    all_docs = list(client.query(sql).result())
    docs = [d for d in all_docs if d.doc_id not in processed_ids]
    print(f"📄 Processing {len(docs):,} documents\n")
    
    # Process with 4 workers
    max_workers = 4
    print(f"⚡ {max_workers} workers | ⏱️  {TIMEOUT_SECONDS}s timeout | 💾 Immediate save\n")
    
    stats = {"success": 0, "error": 0, "empty": 0, "timeout": 0, "total_chunks": 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_with_timeout, doc, cfg, dataset): doc for doc in docs}
        
        for future in tqdm(as_completed(futures), total=len(docs), unit="doc"):
            try:
                result = future.result(timeout=TIMEOUT_SECONDS + 5)  # Extra 5s for safety
                
                if result["status"] == "success":
                    stats["success"] += 1
                    stats["total_chunks"] += result.get("chunks", 0)
                elif result["status"] == "error":
                    stats["error"] += 1
                elif result["status"] == "timeout":
                    stats["timeout"] += 1
                elif result["status"] == "empty":
                    stats["empty"] += 1
                
                # Print stats every 50 documents
                total_processed = stats["success"] + stats["error"] + stats["empty"] + stats["timeout"]
                if total_processed % 50 == 0 and total_processed > 0:
                    success_rate = (stats["success"] / total_processed * 100)
                    avg_chunks = (stats["total_chunks"] / stats["success"]) if stats["success"] > 0 else 0
                    print(f"\n📊 {stats['success']} ✅ | {stats['error']} ❌ | {stats['timeout']} ⏱️  | {stats['empty']} ⚠️")
                    print(f"   {success_rate:.1f}% success | {avg_chunks:.0f} chunks/doc | {stats['total_chunks']:,} total chunks")
                    
            except TimeoutError:
                doc = futures[future]
                log_error(doc.doc_id, doc.name, "Future timeout")
                stats["timeout"] += 1
    
    print(f"\n✅ EXTRACTION COMPLETE!")
    print(f"   Success: {stats['success']:,} docs ({stats['total_chunks']:,} chunks)")
    print(f"   Errors: {stats['error']:,} docs")
    print(f"   Timeouts: {stats['timeout']:,} docs")
    print(f"   Empty: {stats['empty']:,} docs")

if __name__ == "__main__":
    main()
