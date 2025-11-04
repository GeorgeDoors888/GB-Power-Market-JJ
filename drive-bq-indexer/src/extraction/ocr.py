import logging
import io
import tempfile
import os
import subprocess
from PIL import Image
import pytesseract

log = logging.getLogger(__name__)

def _pdftoppm_available():
    return subprocess.call(["which", "pdftoppm"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL) == 0

def ocr_pdf_image(pdf_bytes: bytes, dpi: int = 300, langs: str | None = None) -> str:
    langs = langs or os.getenv("TESSERACT_LANGS", "eng")
    if _pdftoppm_available():
        with tempfile.TemporaryDirectory() as d:
            pdf_path = os.path.join(d, "in.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            subprocess.check_call(["pdftoppm", "-r", str(dpi),
                                   pdf_path, os.path.join(d, "page"), "-jpeg"])
            text_parts = []
            for name in sorted(os.listdir(d)):
                if name.startswith("page-") and name.endswith(".jpg"):
                    img = Image.open(os.path.join(d, name))
                    text_parts.append(pytesseract.image_to_string(img, lang=langs))
            return "\n".join(text_parts)
    img = Image.open(io.BytesIO(pdf_bytes))
    return pytesseract.image_to_string(img, lang=langs)
