#!/usr/bin/env python3
"""
Immediate feedback extraction - saves after every successful document
This way you can see progress in real-time
"""
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")

import os
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

ERROR_LOG = "/tmp/extraction_errors_immediate.log"
SUCCESS_LOG = "/tmp/extraction_success.log"

def log_error(doc_id, name, error):
    with open(ERROR_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{str(error)}\n")

def log_success(doc_id, name, num_chunks):
    with open(SUCCESS_LOG, "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{doc_id}\t{name}\t{num_chunks}\n")

def process_and_save_immediately(doc_row, cfg, dataset):
    """Process document and save immediately"""
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
    
    print("⚡ IMMEDIATE FEEDBACK EXTRACTION")
    print("Saves after EVERY successful document")
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
      LIMIT 10000
    """
    all_docs = list(client.query(sql).result())
    docs = [d for d in all_docs if d.doc_id not in processed_ids]
    print(f"📄 Processing {len(docs):,} documents\n")
    
    # Process with 4 workers
    max_workers = 4
    print(f"⚡ {max_workers} workers | 💾 Saving after EACH document\n")
    
    stats = {"success": 0, "error": 0, "empty": 0, "total_chunks": 0}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_and_save_immediately, doc, cfg, dataset): doc for doc in docs}
        
        for future in tqdm(as_completed(futures), total=len(docs), unit="doc"):
            result = future.result()
            
            if result["status"] == "success":
                stats["success"] += 1
                stats["total_chunks"] += result.get("chunks", 0)
            elif result["status"] == "error":
                stats["error"] += 1
            elif result["status"] == "empty":
                stats["empty"] += 1
            
            # Print stats every 10 documents
            if (stats["success"] + stats["error"] + stats["empty"]) % 10 == 0:
                total = stats["success"] + stats["error"] + stats["empty"]
                success_rate = (stats["success"] / total * 100) if total > 0 else 0
                print(f"\n📊 {stats['success']} ✅ | {stats['error']} ❌ | {stats['empty']} ⚠️  | {success_rate:.0f}% success | {stats['total_chunks']} chunks")
    
    print(f"\n✅ BATCH COMPLETE!")
    print(f"   Success: {stats['success']:,} docs")
    print(f"   Failed: {stats['error']:,} docs")
    print(f"   Empty: {stats['empty']:,} docs")
    print(f"   Total chunks: {stats['total_chunks']:,}")

if __name__ == "__main__":
    main()
