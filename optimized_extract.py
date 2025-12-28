#!/usr/bin/env python3
"""
Optimized extraction - fewer workers, better throughput
Uses 4 workers instead of 16 to avoid API rate limits and contention
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
import time

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.chunking import into_chunks
from src.storage.bigquery import ensure_tables, load_rows
from src.config import load_settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
log = logging.getLogger("optimized_extract")

ERROR_LOG = "/tmp/extraction_errors.log"
stats = {"success": 0, "failed": 0, "empty": 0}

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def process_document(doc_row, cfg):
    """Process with minimal overhead"""
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
            stats["empty"] += 1
            return []
        
        if not text or len(text.strip()) == 0:
            stats["empty"] += 1
            log_error(doc_row.doc_id, doc_row.name, "Empty text")
            return []
        
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
        
        stats["success"] += 1
        return chunks
    except Exception as e:
        stats["failed"] += 1
        log_error(doc_row.doc_id, doc_row.name, str(e))
        return []

def main():
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    client = bq_client()
    
    print("⚡ OPTIMIZED EXTRACTION (4 WORKERS)")
    print("=" * 70)
    
    # Clear error log
    with open(ERROR_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\terror\n")
    
    # Get unprocessed documents
    print("\n🔍 Getting documents to process...")
    sql_processed = f"""
      SELECT DISTINCT doc_id FROM `{client.project}.{cfg['dataset']}.chunks`
    """
    processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
    print(f"✅ {len(processed_ids):,} already processed")
    
    sql = f"""
      SELECT doc_id, name, mime_type FROM `{client.project}.{cfg['dataset']}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
    """
    all_docs = list(client.query(sql).result())
    docs = [d for d in all_docs if d.doc_id not in processed_ids]
    print(f"📄 {len(docs):,} documents to process\n")
    
    # Use only 4 workers to avoid rate limits
    max_workers = 4
    batch_size = 1000  # Larger batches, less frequent saves
    
    print(f"⚡ Using {max_workers} workers (optimized for API limits)")
    print(f"📦 Batch size: {batch_size}")
    print()
    
    chunk_rows = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {executor.submit(process_document, doc, cfg): doc for doc in docs}
        
        for future in tqdm(as_completed(future_to_doc), total=len(docs), unit="doc"):
            chunks = future.result()
            chunk_rows.extend(chunks)
            
            # Save in large batches
            if len(chunk_rows) >= batch_size:
                load_rows(cfg["dataset"], "chunks", chunk_rows)
                chunk_rows = []
                
                # Print stats every batch
                elapsed = time.time() - start_time
                total_processed = stats["success"] + stats["failed"] + stats["empty"]
                rate = total_processed / elapsed if elapsed > 0 else 0
                print(f"\n📊 Rate: {rate:.1f} docs/sec | Success: {stats['success']} | Failed: {stats['failed']} | Empty: {stats['empty']}")
    
    # Save remaining
    if chunk_rows:
        load_rows(cfg["dataset"], "chunks", chunk_rows)
    
    print(f"\n✅ COMPLETE!")
    print(f"   Success: {stats['success']:,}")
    print(f"   Failed: {stats['failed']:,}")
    print(f"   Empty: {stats['empty']:,}")
    print(f"   Errors logged to: {ERROR_LOG}")

if __name__ == "__main__":
    main()
