# Architecture

- **Indexer**: paginates Drive Files API, collects metadata, avoids duplicates
- **Extractor**: pdfminer text; OCR via Tesseract/Cloud Vision if needed; DOCX & PPTX parsers
- **Chunker**: token-ish splitter (character window + overlap)
- **Embeddings**: Vertex AI `textembedding-gecko` (region: europe-west2)
- **Quality loop**: BigQuery metrics → auto-tune chunk size/overlap/OCR mode
- **Search API**: FastAPI `/search` returning top-k chunks with dot-product scoring

**Ops**: Long runs on UpCloud; Codespaces for PRs/tests only.
