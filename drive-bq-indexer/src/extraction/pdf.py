from __future__ import annotations
import io, logging
from pdfminer.high_level import extract_text
from googleapiclient.http import MediaIoBaseDownload
from ..auth.google_auth import drive_client
from .ocr import ocr_pdf_image

log = logging.getLogger(__name__)

def download_pdf(file_id: str) -> bytes:
    """Download file bytes from Drive."""
    svc = drive_client()
    req = svc.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    return buf.getvalue()

def extract_pdf_text(pdf_bytes: bytes, ocr_mode: str = "auto") -> tuple[str, bool]:
    """Extract text; OCR if needed."""
    text = extract_text(io.BytesIO(pdf_bytes)) or ""
    ocred = False
    if ocr_mode in ("auto", "force"):
        if ocr_mode == "force" or len(text.strip()) < 50:
            text = ocr_pdf_image(pdf_bytes)
            ocred = True
    return text, ocred
