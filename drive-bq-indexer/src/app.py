from __future__ import annotations
from fastapi import FastAPI, Query
from .search.query import search

app = FastAPI(title="Drive→BigQuery Search API")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/search")
def api_search(q: str = Query(..., min_length=2), k: int = 5):
    results = search(q, k=k)
    return {"query": q, "k": k, "results": results}
