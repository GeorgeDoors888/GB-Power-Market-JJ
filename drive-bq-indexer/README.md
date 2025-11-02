# Drive→BigQuery Search Indexer

Index Google Drive → extract/OCR PDFs **+ DOCX/PPTX** → chunk → BigQuery (eu-west2) → vector search API.

## Features
- Full Drive crawl with change detection (no duplicates)
- PDF text extraction (pdfminer) + OCR fallback (Tesseract or Cloud Vision)
- **DOCX** (`python-docx`) and **PPTX** (`python-pptx`) extraction
- Token-aware chunking with overlap
- BigQuery tables: `documents`, `chunks`, `chunk_embeddings`
- Quality checks + self-tuning (chunk size, overlap, OCR rate)
- FastAPI search service (vector or BM25 fallback)
- Dev in GitHub Codespaces (light), prod on UpCloud (systemd + Docker)
- **Vertex AI embeddings** (default) with `textembedding-gecko`

## Quick start
1. **GCP**: project `jibber-jabber-knowledge`, dataset `uk_energy_insights` (region `europe-west2`).
2. Service account JSON with Drive + BigQuery (+ Vision optional). Share files if needed.
3. Copy `.env.sample` → `.env` and adjust if needed.
4. Build & run:
   ```bash
   # Full backfill
   python -m src.cli index-drive
   python -m src.cli extract
   python -m src.cli build-embeddings
   python -m src.cli quality-check --auto-tune

   # Search API
   uvicorn src.app:app --host 0.0.0.0 --port 8080
   ```
5. Query:
   ```bash
   GET https://your-domain/search?q=contract%20for%20difference&k=5
   ```
