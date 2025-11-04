from __future__ import annotations
import re

def tokenize_est(s: str) -> int:
    return max(1, len(s) // 4)

def into_chunks(text: str, size: int = 1200, overlap: int = 200):
    words = re.split(r"(\s+)", text)
    out, buf, count = [], [], 0
    for w in words:
        buf.append(w)
        count += len(w)
        if count >= size:
            chunk = "".join(buf)
            out.append(chunk)
            keep = chunk[-overlap:]
            buf = [keep]
            count = len(keep)
    if buf:
        out.append("".join(buf))
    return [(i, c, tokenize_est(c)) for i, c in enumerate(out)]
