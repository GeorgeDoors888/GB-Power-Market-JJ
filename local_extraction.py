#!/usr/bin/env python3
"""
Local extraction script for running during off-hours (midnight-8am)
Uses coordination to avoid competing with remote server
"""
import sys
import os
from pathlib import Path

# Add the drive-bq-indexer to path
project_root = Path(__file__).parent / "drive-bq-indexer"
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime, time as dt_time
import time

from auth.google_auth import bq_client
from extraction.pdf import download_pdf, extract_pdf_text
from extraction.docx_parser import extract_docx_text
from extraction.pptx_parser import extract_pptx_text
from chunking import into_chunks
from storage.bigquery import ensure_tables, load_rows
from config import load_settings

ERROR_LOG = "extraction_errors_local.log"
SUCCESS_LOG = "extraction_success_local.log"
PROGRESS_LOG = "extraction_progress_local.log"

# Known corrupted files to skip
SKIP_FILES = {
    "1zsP5LWPuaeIp-yRK9j9Tpw9KKvwVNSjT",
    "1vsfXUs1r9Fg5DAxfQmK9KoiOCBy_evJe",
    "1hwjxyZeYwfH5ttYtVS1stoOAO8CTFA9z",
    "1oruh4NbX6Z6VGKZTw1FPhavADiRESr_P",
    "18W1Gqub_VRGk1NBJbB18SPIZaq5adVJ_",
    "1SjAnGa-LgQVecMyD5g-zAOLKBUZ8ggle",
    "1ZC3f1QdjUs3YAC6sJvHtxH-2FFylhbsn",
    "12dkwVuiq9dR3UIszvGxuHU3eHyxc7qek",
}

# Local settings - use 6 workers (your Mac has 8 cores, leave 2 for system)
LOCAL_WORKERS = 6
BATCH_SIZE = 5000  # Smaller batches for local runs

def is_off_hours():
    """Check if current time is between midnight and 8am"""
    now = datetime.now().time()
    return dt_time(0, 0) <= now < dt_time(8, 0)

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def log_success(doc_id, name, num_chunks):
    with open(SUCCESS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{num_chunks}\n")

def log_progress(message):
    """Log progress to file and print"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    with open(PROGRESS_LOG, "a") as f:
        f.write(log_msg + "\n")

def process_document(doc_row, cfg, dataset):
    """Process one document and save immediately"""
    doc_id = doc_row.doc_id
    
    if doc_id in SKIP_FILES:
        log_error(doc_id, doc_row.name, "SKIPPED - Known corrupted file")
        return {"status": "skipped", "doc_id": doc_id}
    
    try:
        # Download
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
        
        # Save immediately
        if chunks:
            load_rows(dataset, "chunks", chunks)
            log_success(doc_id, doc_row.name, len(chunks))
            return {"status": "success", "doc_id": doc_id, "chunks": len(chunks)}
        else:
            log_error(doc_id, doc_row.name, "No chunks created")
            return {"status": "no_chunks", "doc_id": doc_id}
            
    except Exception as e:
        error_msg = str(e)[:200]
        log_error(doc_id, doc_row.name, error_msg)
        return {"status": "error", "doc_id": doc_id}

def process_batch(cfg, dataset, client):
    """Process one batch of documents"""
    
    # Get already processed
    sql_processed = f"SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`"
    processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
    
    # Get documents to process - randomized to avoid conflicts with server
    sql = f"""
      SELECT doc_id, name, mime_type 
      FROM `{client.project}.{dataset}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
      ORDER BY RAND()
      LIMIT {BATCH_SIZE}
    """
    
    all_docs = list(client.query(sql).result())
    docs = [d for d in all_docs if d.doc_id not in processed_ids and d.doc_id not in SKIP_FILES]
    
    if len(docs) == 0:
        return 0, {}
    
    log_progress(f"📄 Processing batch of {len(docs):,} documents on local Mac")
    
    # Process with workers
    stats = {"success": 0, "error": 0, "empty": 0, "skipped": 0, "total_chunks": 0}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=LOCAL_WORKERS) as executor:
        futures = {executor.submit(process_document, doc, cfg, dataset): doc for doc in docs}
        
        for future in tqdm(as_completed(futures), total=len(docs), unit="doc", desc="Local extraction"):
            try:
                result = future.result(timeout=60)
                
                if result["status"] == "success":
                    stats["success"] += 1
                    stats["total_chunks"] += result.get("chunks", 0)
                elif result["status"] == "error":
                    stats["error"] += 1
                elif result["status"] == "empty":
                    stats["empty"] += 1
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                
                # Check if we should stop (8am)
                if not is_off_hours():
                    log_progress("⏰ 8am reached - stopping local extraction")
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
                
                # Print progress every 50 docs
                total = stats["success"] + stats["error"] + stats["empty"] + stats["skipped"]
                if total % 50 == 0 and total > 0:
                    elapsed = time.time() - start_time
                    rate = total / elapsed if elapsed > 0 else 0
                    success_rate = (stats["success"] / total * 100) if total > 0 else 0
                    
                    log_progress(f"📊 {total:,}/{len(docs):,} docs | {success_rate:.1f}% success | {stats['total_chunks']:,} chunks | {rate:.2f} docs/sec")
                    
            except Exception as e:
                log_progress(f"⚠️  Future exception: {str(e)[:100]}")
                stats["error"] += 1
    
    elapsed = time.time() - start_time
    return len(docs), stats

def main():
    log_progress("=" * 70)
    log_progress("🌙 LOCAL OFF-HOURS EXTRACTION")
    log_progress(f"Running on: {os.uname().nodename}")
    log_progress(f"Workers: {LOCAL_WORKERS} (8-core Mac)")
    log_progress("=" * 70)
    
    # Check if it's off-hours
    if not is_off_hours():
        log_progress("⚠️  Not off-hours (must be between midnight and 8am)")
        log_progress("   Current time: " + datetime.now().strftime("%I:%M %p"))
        return
    
    cfg = load_settings()
    dataset = cfg["dataset"]
    ensure_tables(dataset)
    client = bq_client()
    
    # Initialize logs if they don't exist
    if not os.path.exists(ERROR_LOG):
        with open(ERROR_LOG, "w") as f:
            f.write("timestamp\tdoc_id\tname\terror\n")
    if not os.path.exists(SUCCESS_LOG):
        with open(SUCCESS_LOG, "w") as f:
            f.write("timestamp\tdoc_id\tname\tnum_chunks\n")
    
    batch_num = 1
    total_processed = 0
    total_success = 0
    total_chunks = 0
    
    # Run until 8am or no more documents
    while is_off_hours():
        log_progress(f"\n{'='*70}")
        log_progress(f"📦 LOCAL BATCH {batch_num}")
        log_progress(f"{'='*70}")
        
        # Check remaining documents
        sql_check = f"""
          SELECT COUNT(*) as remaining
          FROM `{client.project}.{dataset}.documents_clean` d
          LEFT JOIN (SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`) c
            ON d.doc_id = c.doc_id
          WHERE c.doc_id IS NULL
            AND d.mime_type IN (
              'application/pdf',
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
              'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            )
        """
        remaining = list(client.query(sql_check).result())[0].remaining
        log_progress(f"📊 {remaining:,} documents remaining in database")
        
        if remaining == 0:
            log_progress("🎉 ALL DOCUMENTS PROCESSED!")
            break
        
        # Process batch
        batch_start = time.time()
        docs_in_batch, stats = process_batch(cfg, dataset, client)
        batch_elapsed = time.time() - batch_start
        
        if docs_in_batch == 0:
            log_progress("⚠️  No more documents to process")
            break
        
        # Update totals
        total_processed += docs_in_batch
        total_success += stats["success"]
        total_chunks += stats["total_chunks"]
        
        # Log batch summary
        success_rate = (stats["success"] / docs_in_batch * 100) if docs_in_batch > 0 else 0
        avg_time = batch_elapsed / docs_in_batch if docs_in_batch > 0 else 0
        
        log_progress(f"\n{'='*70}")
        log_progress(f"✅ LOCAL BATCH {batch_num} COMPLETE")
        log_progress(f"   Processed: {docs_in_batch:,} docs in {batch_elapsed/60:.1f} minutes")
        log_progress(f"   Success: {stats['success']:,} ({success_rate:.1f}%)")
        log_progress(f"   Chunks: {stats['total_chunks']:,}")
        log_progress(f"   Avg time: {avg_time:.1f} sec/doc")
        log_progress(f"{'='*70}")
        
        batch_num += 1
        
        # Check time again
        if not is_off_hours():
            log_progress("⏰ 8am reached - stopping")
            break
        
        # Small delay between batches
        log_progress("⏸️  Waiting 5 seconds before next batch...")
        time.sleep(5)
    
    log_progress("\n" + "="*70)
    log_progress("🌅 LOCAL EXTRACTION SESSION COMPLETE")
    log_progress(f"   Time: {datetime.now().strftime('%I:%M %p')}")
    log_progress(f"   Batches: {batch_num - 1}")
    log_progress(f"   Successful: {total_success:,}")
    log_progress(f"   Chunks: {total_chunks:,}")
    log_progress("="*70)

if __name__ == "__main__":
    main()
