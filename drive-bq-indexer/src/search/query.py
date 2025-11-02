from __future__ import annotations
from .embed import embed_texts
from .vector_index import topk
from ..config import load_settings

def search(q: str, k: int = 5):
    cfg = load_settings()
    vec = embed_texts([q])[0]
    return topk(cfg["dataset"], vec, k=k)
