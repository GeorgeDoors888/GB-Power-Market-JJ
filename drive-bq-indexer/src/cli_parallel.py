"""
Parallel extraction CLI - processes multiple documents concurrently
"""
from __future__ import annotations
import os
import json
import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from .logger import setup_logging
from .config import load_settings
from .auth.google_auth import bq_client
from .extraction.pdf import download_pdf, extract_pdf_text
from .extraction.docx_parser import extract_docx_text
from .extraction.pptx_parser import extract_pptx_text
from .chunking import into_chunks
from .storage.bigquery import ensure_tables, load_rows

log = logging.getLogger("cli_parallel")

def process_document(doc_row, cfg):
    """Process a single document - download, extract, chunk"""
    try:
        # Download file
        file_bytes = download_pdf(doc_row.doc_id)
        
        # Extract text based on mime type
        if doc_row.mime_type == "application/pdf":
            text, _ = extract_pdf_text(file_bytes, cfg["extract"]["ocr_mode"])
        elif doc_row.mime_type.endswith(".wordprocessingml.document"):
            text = extract_docx_text(file_bytes)
        elif doc_row.mime_type.endswith(".presentationml.presentation"):
            text = extract_pptx_text(file_bytes)
        else:
            return []
        
        # Chunk the text
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
        
        return chunks
    except Exception as e:
        log.warning(f"Failed to process {doc_row.doc_id} ({doc_row.name}): {e}")
        return []

def cmd_extract_parallel(args):
    """Extract text from documents using parallel processing"""
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    client = bq_client()
    
    # Get all documents to process
    print("🔍 Querying documents to process...")
    sql = f"""
      SELECT doc_id, name, mime_type FROM `{client.project}.{cfg['dataset']}.documents_clean`
      WHERE mime_type IN (
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
      )
    """
    docs = list(client.query(sql).result())
    print(f"📄 Found {len(docs):,} documents to process")
    
    # Process in parallel with configurable workers
    max_workers = int(os.getenv("EXTRACT_WORKERS", "10"))
    batch_size = int(os.getenv("EXTRACT_BATCH_SIZE", "500"))
    
    print(f"⚡ Using {max_workers} parallel workers")
    print(f"🔐 Using domain-wide delegation (impersonating: {os.getenv('GOOGLE_WORKSPACE_ADMIN_EMAIL')})")
    
    chunk_rows = []
    processed = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_doc = {
            executor.submit(process_document, doc, cfg): doc 
            for doc in docs
        }
        
        # Process completed tasks with progress bar
        for future in tqdm(as_completed(future_to_doc), total=len(docs), unit="docs"):
            chunks = future.result()
            chunk_rows.extend(chunks)
            processed += 1
            
            # Save in batches
            if len(chunk_rows) >= batch_size:
                load_rows(cfg["dataset"], "chunks", chunk_rows)
                chunk_rows = []
    
    # Save remaining chunks
    if chunk_rows:
        load_rows(cfg["dataset"], "chunks", chunk_rows)
    
    print(f"\n✅ Extraction complete!")
    print(f"   Processed: {processed:,} documents")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel workers")
    args = parser.parse_args()
    
    os.environ["EXTRACT_WORKERS"] = str(args.workers)
    
    setup_logging()
    cmd_extract_parallel(args)

if __name__ == "__main__":
    main()
