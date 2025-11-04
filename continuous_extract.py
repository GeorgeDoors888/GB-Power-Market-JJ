#!/usr/bin/env python3
"""
Continuous extraction - automatically restarts until all documents are done
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
import random
import time
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

ERROR_LOG = "/tmp/extraction_errors_continuous.log"
SUCCESS_LOG = "/tmp/extraction_success_continuous.log"
PROGRESS_LOG = "/tmp/extraction_progress.log"

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

BATCH_SIZE = 10000  # Process 10k documents per batch
MAX_WORKERS = 8  # Increased from 4 to 8 for better throughput

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
    
    # Skip known bad files
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
    
    # Get documents to process - randomized
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
    
    log_progress(f"📄 Processing batch of {len(docs):,} documents")
    
    # Process with workers
    stats = {"success": 0, "error": 0, "empty": 0, "skipped": 0, "total_chunks": 0}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_document, doc, cfg, dataset): doc for doc in docs}
        
        for future in tqdm(as_completed(futures), total=len(docs), unit="doc"):
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
                
                # Print progress every 100 docs
                total = stats["success"] + stats["error"] + stats["empty"] + stats["skipped"]
                if total % 100 == 0 and total > 0:
                    elapsed = time.time() - start_time
                    rate = total / elapsed if elapsed > 0 else 0
                    success_rate = (stats["success"] / total * 100) if total > 0 else 0
                    avg_chunks = (stats["total_chunks"] / stats["success"]) if stats["success"] > 0 else 0
                    
                    log_progress(f"📊 {total:,}/{len(docs):,} docs | {success_rate:.1f}% success | {stats['total_chunks']:,} chunks | {rate:.2f} docs/sec")
                    
            except Exception as e:
                log_progress(f"⚠️  Future exception: {str(e)[:100]}")
                stats["error"] += 1
    
    elapsed = time.time() - start_time
    return len(docs), stats

def main():
    cfg = load_settings()
    dataset = cfg["dataset"]
    ensure_tables(dataset)
    client = bq_client()
    
    log_progress("=" * 70)
    log_progress("🚀 CONTINUOUS EXTRACTION STARTED")
    log_progress("Will run until all documents are processed")
    log_progress(f"Batch size: {BATCH_SIZE:,} | Workers: {MAX_WORKERS}")
    log_progress("=" * 70)
    
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
    
    while True:
        log_progress(f"\n{'='*70}")
        log_progress(f"📦 BATCH {batch_num} STARTING")
        log_progress(f"{'='*70}")
        
        # Check how many documents remain
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
        log_progress(f"📊 {remaining:,} documents remaining to process")
        
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
        log_progress(f"✅ BATCH {batch_num} COMPLETE")
        log_progress(f"   Processed: {docs_in_batch:,} docs in {batch_elapsed/60:.1f} minutes")
        log_progress(f"   Success: {stats['success']:,} ({success_rate:.1f}%)")
        log_progress(f"   Errors: {stats['error']:,}")
        log_progress(f"   Chunks: {stats['total_chunks']:,}")
        log_progress(f"   Avg time: {avg_time:.1f} sec/doc")
        log_progress(f"")
        log_progress(f"📈 TOTAL PROGRESS")
        log_progress(f"   Batches: {batch_num}")
        log_progress(f"   Documents: {total_success:,} successful")
        log_progress(f"   Chunks: {total_chunks:,}")
        log_progress(f"   Remaining: ~{remaining - docs_in_batch:,}")
        log_progress(f"{'='*70}")
        
        batch_num += 1
        
        # Small delay between batches
        log_progress("⏸️  Waiting 10 seconds before next batch...")
        time.sleep(10)
    
    log_progress("\n" + "="*70)
    log_progress("🏁 EXTRACTION COMPLETE!")
    log_progress(f"   Total batches: {batch_num - 1}")
    log_progress(f"   Total successful: {total_success:,}")
    log_progress(f"   Total chunks: {total_chunks:,}")
    log_progress("="*70)

if __name__ == "__main__":
    main()
