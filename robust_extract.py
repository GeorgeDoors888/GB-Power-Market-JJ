#!/usr/bin/env python3
"""
Robust parallel extraction with comprehensive error handling
Logs all errors but continues processing
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

from src.auth.google_auth import bq_client
from src.extraction.pdf import download_pdf, extract_pdf_text
from src.extraction.docx_parser import extract_docx_text
from src.extraction.pptx_parser import extract_pptx_text
from src.chunking import into_chunks
from src.storage.bigquery import ensure_tables, load_rows
from src.config import load_settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger("robust_extract")

# Error log file
ERROR_LOG = "/tmp/extraction_errors.log"

def log_error(doc_id, name, error):
    """Log errors to file for later review"""
    with open(ERROR_LOG, "a") as f:
        timestamp = datetime.now().isoformat()
        f.write(f"{timestamp}\t{doc_id}\t{name}\t{str(error)}\n")

def process_document_robust(doc_row, cfg):
    """Process a single document with comprehensive error handling"""
    doc_id = doc_row.doc_id
    name = doc_row.name
    mime_type = doc_row.mime_type
    
    try:
        # Step 1: Download
        try:
            file_bytes = download_pdf(doc_id)
        except Exception as e:
            log_error(doc_id, name, f"Download failed: {e}")
            return []
        
        # Step 2: Extract text
        try:
            if mime_type == "application/pdf":
                text, _ = extract_pdf_text(file_bytes, cfg["extract"]["ocr_mode"])
            elif mime_type.endswith(".wordprocessingml.document"):
                text = extract_docx_text(file_bytes)
            elif mime_type.endswith(".presentationml.presentation"):
                text = extract_pptx_text(file_bytes)
            else:
                log_error(doc_id, name, f"Unsupported mime type: {mime_type}")
                return []
        except Exception as e:
            log_error(doc_id, name, f"Extraction failed: {e}")
            return []
        
        # Step 3: Check if we got text
        if not text or len(text.strip()) == 0:
            log_error(doc_id, name, "Empty text extracted")
            return []
        
        # Step 4: Chunk the text
        try:
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
            
            return chunks
        except Exception as e:
            log_error(doc_id, name, f"Chunking failed: {e}")
            return []
            
    except Exception as e:
        # Catch-all for any unexpected errors
        log_error(doc_id, name, f"Unexpected error: {e}")
        return []

def main():
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    client = bq_client()
    
    print("⚡ ROBUST PARALLEL EXTRACTION")
    print("=" * 70)
    
    # Clear error log
    with open(ERROR_LOG, "w") as f:
        f.write("timestamp\tdoc_id\tname\terror\n")
    
    # Get documents to process
    print("\n🔍 Checking for already processed documents...")
    sql_processed = f"""
      SELECT DISTINCT doc_id FROM `{client.project}.{cfg['dataset']}.chunks`
    """
    try:
        processed_ids = {r.doc_id for r in client.query(sql_processed).result()}
        print(f"✅ Found {len(processed_ids):,} already processed documents")
    except:
        processed_ids = set()
        print("⚠️  Chunks table empty, processing all documents")
    
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
    print(f"📄 Processing {len(docs):,} documents ({len(all_docs)-len(docs):,} already done)")
    
    # Process in parallel
    max_workers = int(os.getenv("EXTRACT_WORKERS", "16"))
    batch_size = int(os.getenv("EXTRACT_BATCH_SIZE", "500"))
    
    print(f"⚡ Using {max_workers} parallel workers")
    print(f"📦 Batch size: {batch_size} chunks")
    print(f"🔐 Domain-wide delegation: {os.getenv('GOOGLE_WORKSPACE_ADMIN_EMAIL')}")
    print()
    
    chunk_rows = []
    success_count = 0
    error_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {
            executor.submit(process_document_robust, doc, cfg): doc 
            for doc in docs
        }
        
        for future in tqdm(as_completed(future_to_doc), total=len(docs), unit="docs"):
            chunks = future.result()
            
            if chunks:
                chunk_rows.extend(chunks)
                success_count += 1
            else:
                error_count += 1
            
            # Save in batches
            if len(chunk_rows) >= batch_size:
                try:
                    load_rows(cfg["dataset"], "chunks", chunk_rows)
                    chunk_rows = []
                except Exception as e:
                    log.error(f"Failed to save batch: {e}")
    
    # Save remaining chunks
    if chunk_rows:
        try:
            load_rows(cfg["dataset"], "chunks", chunk_rows)
        except Exception as e:
            log.error(f"Failed to save final batch: {e}")
    
    print(f"\n✅ EXTRACTION COMPLETE!")
    print("=" * 70)
    print(f"   Successful: {success_count:,} documents")
    print(f"   Failed: {error_count:,} documents")
    print(f"   Success rate: {success_count/(success_count+error_count)*100:.1f}%")
    print(f"\n📋 Error log saved to: {ERROR_LOG}")
    print("=" * 70)

if __name__ == "__main__":
    main()
