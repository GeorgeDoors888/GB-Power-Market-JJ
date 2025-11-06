#!/usr/bin/env python3
"""
Continuous extraction - FIXED VERSION
- Processes ALL 153K documents (not just 10K random sample)
- Better performance monitoring
- Memory leak prevention with periodic restarts
- Real-time progress tracking
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
import time
import psutil
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
PERFORMANCE_LOG = "/tmp/extraction_performance.log"

# Known corrupted files to skip
SKIP_FILES = {
    "1zsP5LWPuaeIp-yRK9j9Tpw9KKvwVNSjT", "1vsfXUs1r9Fg5DAxfQmK9KoiOCBy_evJe",
    "1hwjxyZeYwfH5ttYtVS1stoOAO8CTFA9z", "1oruh4NbX6Z6VGKZTw1FPhavADiRESr_P",
    "18W1Gqub_VRGk1NBJbB18SPIZaq5adVJ_", "1SjAnGa-LgQVecMyD5g-zAOLKBUZ8ggle",
    "1ZC3f1QdjUs3YAC6sJvHtxH-2FFylhbsn", "12dkwVuiq9dR3UIszvGxuHU3eHyxc7qek",
}

BATCH_SIZE = 500  # Smaller batches for better progress tracking
MAX_WORKERS = 6  # Optimal for 4-core server
RESTART_AFTER_DOCS = 5000  # Restart process every 5K docs to prevent memory leaks

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
    print(log_msg, flush=True)
    with open(PROGRESS_LOG, "a") as f:
        f.write(log_msg + "\n")

def log_performance(processed, total, elapsed, docs_per_sec, eta_hours, memory_mb, cpu_percent):
    """Log performance metrics"""
    timestamp = datetime.now().isoformat()
    log_msg = f"{timestamp}|{processed}|{total}|{elapsed:.1f}|{docs_per_sec:.3f}|{eta_hours:.1f}|{memory_mb:.1f}|{cpu_percent:.1f}"
    with open(PERFORMANCE_LOG, "a") as f:
        f.write(log_msg + "\n")

def get_system_stats():
    """Get current memory and CPU usage"""
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent(interval=0.1)
    return memory_mb, cpu_percent

def process_document(doc_row, cfg, dataset):
    """Process one document and save immediately"""
    doc_id = doc_row.doc_id
    
    if doc_id in SKIP_FILES:
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
        return {"status": "error", "doc_id": doc_id, "error": error_msg}

def get_documents_to_process(client, dataset, batch_size):
    """Get next batch of unprocessed documents - processes ALL documents in order"""
    
    # Get already processed
    sql_processed = f"SELECT DISTINCT doc_id FROM `{client.project}.{dataset}.chunks`"
    processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
    log_progress(f"✅ Already processed: {len(processed_ids):,} documents")
    
    # Get ALL documents (not just 10K random sample!)
    sql = f"""
      SELECT doc_id, name, mime_type 
      FROM `{client.project}.{dataset}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
      ORDER BY doc_id
    """
    
    log_progress(f"📊 Fetching all documents from documents_clean...")
    all_docs = list(client.query(sql).result())
    log_progress(f"📊 Total documents in database: {len(all_docs):,}")
    
    # Filter to unprocessed only
    docs_to_process = [d for d in all_docs if d.doc_id not in processed_ids and d.doc_id not in SKIP_FILES]
    log_progress(f"📊 Documents remaining to process: {len(docs_to_process):,}")
    
    # Return next batch
    return docs_to_process[:batch_size], len(docs_to_process), len(all_docs)

def process_batch(cfg, dataset, client, batch_num):
    """Process one batch of documents"""
    
    docs, remaining, total = get_documents_to_process(client, dataset, BATCH_SIZE)
    
    if len(docs) == 0:
        log_progress("🎉 ALL DOCUMENTS PROCESSED!")
        return 0, {}, True  # Done
    
    processed = total - remaining
    log_progress(f"\n{'='*70}")
    log_progress(f"📦 BATCH {batch_num}")
    log_progress(f"📊 Overall Progress: {processed:,}/{total:,} docs ({(processed/total)*100:.1f}%)")
    log_progress(f"📄 Processing {len(docs):,} documents in this batch")
    log_progress(f"⏳ Remaining: {remaining:,} documents")
    log_progress(f"{'='*70}\n")
    
    # Process with workers
    stats = {"success": 0, "error": 0, "empty": 0, "skipped": 0, "total_chunks": 0}
    start_time = time.time()
    batch_start = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_document, doc, cfg, dataset): doc for doc in docs}
        
        with tqdm(total=len(docs), desc=f"Batch {batch_num}", unit="doc") as pbar:
            for future in as_completed(futures):
                result = future.result()
                
                if result["status"] == "success":
                    stats["success"] += 1
                    stats["total_chunks"] += result.get("chunks", 0)
                elif result["status"] == "error":
                    stats["error"] += 1
                elif result["status"] == "empty":
                    stats["empty"] += 1
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                
                pbar.update(1)
                
                # Update progress every 50 docs
                if (stats["success"] + stats["error"]) % 50 == 0:
                    elapsed = time.time() - start_time
                    docs_done = stats["success"] + stats["error"] + stats["empty"] + stats["skipped"]
                    if docs_done > 0:
                        docs_per_sec = docs_done / elapsed
                        docs_per_hour = docs_per_sec * 3600
                        eta_hours = remaining / docs_per_hour if docs_per_hour > 0 else 0
                        
                        memory_mb, cpu_percent = get_system_stats()
                        
                        # Log performance
                        log_performance(processed + docs_done, total, elapsed, docs_per_sec, 
                                      eta_hours, memory_mb, cpu_percent)
                        
                        pbar.set_postfix({
                            "success": stats["success"],
                            "errors": stats["error"],
                            "chunks": stats["total_chunks"],
                            "rate": f"{docs_per_hour:.0f}/hr",
                            "mem": f"{memory_mb:.0f}MB"
                        })
    
    batch_elapsed = time.time() - batch_start
    batch_docs_per_sec = len(docs) / batch_elapsed if batch_elapsed > 0 else 0
    
    log_progress(f"\n✅ Batch {batch_num} complete:")
    log_progress(f"   Success: {stats['success']:,} docs")
    log_progress(f"   Errors: {stats['error']:,} docs")
    log_progress(f"   Empty: {stats['empty']:,} docs")
    log_progress(f"   Chunks created: {stats['total_chunks']:,}")
    log_progress(f"   Time: {batch_elapsed/60:.1f} minutes")
    log_progress(f"   Rate: {batch_docs_per_sec*3600:.0f} docs/hour")
    
    return len(docs), stats, False  # Not done

def main():
    """Main extraction loop"""
    log_progress("🚀 Starting FIXED continuous extraction")
    log_progress(f"   MAX_WORKERS: {MAX_WORKERS}")
    log_progress(f"   BATCH_SIZE: {BATCH_SIZE}")
    log_progress(f"   Target: Process ALL 153K documents")
    
    # Initialize performance log
    with open(PERFORMANCE_LOG, "w") as f:
        f.write("timestamp|processed|total|elapsed_sec|docs_per_sec|eta_hours|memory_mb|cpu_percent\n")
    
    # Load config
    cfg = load_settings()
    client = bq_client()
    dataset = "uk_energy_insights"
    
    # Ensure tables exist
    ensure_tables(dataset)
    
    batch_num = 0
    docs_since_restart = 0
    
    while True:
        batch_num += 1
        docs_processed, stats, done = process_batch(cfg, dataset, client, batch_num)
        
        if done:
            log_progress("🎉🎉🎉 EXTRACTION COMPLETE! 🎉🎉🎉")
            break
        
        docs_since_restart += docs_processed
        
        # Restart if processed too many (prevent memory leaks)
        if docs_since_restart >= RESTART_AFTER_DOCS:
            log_progress(f"♻️  Processed {docs_since_restart} docs, restarting to clear memory...")
            os.execv(sys.executable, ['python'] + sys.argv)
        
        # Small delay between batches
        time.sleep(2)

if __name__ == "__main__":
    main()
