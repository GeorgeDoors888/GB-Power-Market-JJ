from __future__ import annotations
import os
from ..quality.metrics import fetch_metrics

def suggest_settings(dataset: str) -> dict:
    """Suggest new chunk/ocr parameters based on metrics."""
    m = fetch_metrics(dataset)
    size = int(os.getenv("CHUNK_SIZE", "1200"))
    overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    ocr_mode = os.getenv("OCR_MODE", "auto")

    if m.get("avg_chars", 0) < 800:
        size = min(2000, size + 200)
        overlap = max(100, overlap - 50)
    if m.get("ocr_rate", 0) > 0.6 and ocr_mode != "force":
        ocr_mode = "force"
    return {"CHUNK_SIZE": size, "CHUNK_OVERLAP": overlap, "OCR_MODE": ocr_mode}
