from __future__ import annotations
import os
import json
import argparse
import logging
from tqdm import tqdm
from .logger import setup_logging
from .config import load_settings
from .auth.google_auth import bq_client
from .indexing.drive_crawler import iter_drive_files
from .extraction.pdf import download_pdf, extract_pdf_text
from .extraction.docx_parser import extract_docx_text
from .extraction.pptx_parser import extract_pptx_text
from .chunking import into_chunks
from .storage.bigquery import ensure_tables, load_rows
from .quality.auto_tune import suggest_settings

log = logging.getLogger("cli")

SUPPORTED = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.google-apps.document": "gdoc",
    "application/vnd.google-apps.spreadsheet": "gsheet",
    "application/vnd.google-apps.presentation": "gslides",
}

def cmd_index_drive(args):
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    rows = []
    for f in tqdm(iter_drive_files(cfg["drive"]["query"])):
        if f.get("mimeType") not in SUPPORTED:
            continue
        rows.append({
            "doc_id": f["id"],
            "drive_id": f["id"],
            "name": f.get("name"),
            "path": "/" + "/".join((f.get("parents") or [])),
            "mime_type": f.get("mimeType"),
            "sha1": None,
            "size_bytes": int(f.get("size", 0)),
            "created": f.get("createdTime"),
            "updated": f.get("modifiedTime"),
            "web_view_link": f.get("webViewLink"),
            "owners": json.dumps(f.get("owners", [])),
        })
        if len(rows) >= 1000:
            load_rows(cfg["dataset"], "documents", rows)
            rows = []
    if rows:
        load_rows(cfg["dataset"], "documents", rows)

def _download_drive_file(file_id: str) -> bytes:
    return download_pdf(file_id)

def _process_one_doc(doc_row, cfg):
    """Process a single document with error handling"""
    try:
        b = _download_drive_file(doc_row.doc_id)
        if doc_row.mime_type == "application/pdf":
            text, _ = extract_pdf_text(b, cfg["extract"]["ocr_mode"])
        elif doc_row.mime_type.endswith(".wordprocessingml.document"):
            text = extract_docx_text(b)
        elif doc_row.mime_type.endswith(".presentationml.presentation"):
            text = extract_pptx_text(b)
        else:
            return []
        
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

def cmd_extract(args):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    client = bq_client()
    
    # Skip already processed documents
    print("🔍 Checking for already processed documents...")
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
    
    # Use threading for I/O-bound parallel processing
    max_workers = int(os.environ.get("EXTRACT_WORKERS", "10"))
    print(f"⚡ Using {max_workers} concurrent workers")
    
    chunk_rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_doc = {executor.submit(_process_one_doc, doc, cfg): doc for doc in docs}
        
        for future in tqdm(as_completed(future_to_doc), total=len(docs)):
            chunks = future.result()
            chunk_rows.extend(chunks)
            
            if len(chunk_rows) >= 500:
                load_rows(cfg["dataset"], "chunks", chunk_rows)
                chunk_rows = []
    
    if chunk_rows:
        load_rows(cfg["dataset"], "chunks", chunk_rows)

def cmd_build_embeddings(args):
    from .search.embed import embed_texts
    cfg = load_settings()
    ensure_tables(cfg["dataset"])
    client = bq_client()
    sql = f"""
      SELECT doc_id, chunk_id, text FROM `{client.project}.{cfg['dataset']}.chunks`
      WHERE CONCAT(doc_id,':',chunk_id) NOT IN (
        SELECT CONCAT(doc_id,':',chunk_id) FROM `{client.project}.{cfg['dataset']}.chunk_embeddings`
      )
    """
    rows = list(client.query(sql).result())
    if not rows:
        print("No new chunks to embed.")
        return
    vectors = embed_texts([r.text for r in rows])
    out = []
    for r, v in zip(rows, vectors):
        out.append({
            "doc_id": r.doc_id,
            "chunk_id": r.chunk_id,
            "provider": os.getenv("EMBED_PROVIDER", "stub"),
            "embed_dim": len(v),
            "vector": v,
        })
        if len(out) >= 200:
            load_rows(cfg["dataset"], "chunk_embeddings", out)
            out = []
    if out:
        load_rows(cfg["dataset"], "chunk_embeddings", out)

def cmd_quality_check(args):
    cfg = load_settings()
    from .quality.metrics import fetch_metrics
    m = fetch_metrics(cfg["dataset"])
    print(json.dumps(m, indent=2))
    if args.auto_tune:
        s = suggest_settings(cfg["dataset"])
        print("Suggested:", s)

def make_parser():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("index-drive").set_defaults(func=cmd_index_drive)
    sub.add_parser("extract").set_defaults(func=cmd_extract)
    sub.add_parser("build-embeddings").set_defaults(func=cmd_build_embeddings)
    q = sub.add_parser("quality-check")
    q.add_argument("--auto-tune", action="store_true")
    q.set_defaults(func=cmd_quality_check)
    return p

def main():
    setup_logging()
    args = make_parser().parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
