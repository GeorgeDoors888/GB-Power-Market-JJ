#!/usr/bin/env python3
import pathlib
from whoosh import index
from whoosh.fields import Schema, ID, TEXT
from whoosh.analysis import StemmingAnalyzer
from whoosh.writing import AsyncWriter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX_DIR = pathlib.Path(__file__).resolve().parent / "indexdir"

INCLUDE_EXT = {
   ".py",".md",".rst",".txt",".toml",".yaml",".yml",".json",".ini",".cfg",
   ".sh",".ps1",".sql",".html",".css",".js",".ts"
}
SKIP_DIRS = {".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".mypy_cache", ".ruff_cache"}

schema = Schema(path=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))
INDEX_DIR.mkdir(parents=True, exist_ok=True)

def iter_files():
   for p in ROOT.rglob("*"):
       if p.is_dir():
           if p.name in SKIP_DIRS:
               continue
       else:
           if p.suffix.lower() in INCLUDE_EXT and not any(part in SKIP_DIRS for part in p.parts):
               yield p

def read_text(p: pathlib.Path) -> str:
   for enc in ("utf-8", "latin-1"):
       try:
           return p.read_text(encoding=enc, errors="ignore")
       except Exception:
           continue
   return ""

def build_index():
   if not index.exists_in(INDEX_DIR):
       ix = index.create_in(INDEX_DIR, schema)
   else:
       ix = index.open_dir(INDEX_DIR)
   writer = AsyncWriter(ix)
   count = 0
   for fp in iter_files():
       txt = read_text(fp)
       writer.update_document(path=str(fp.relative_to(ROOT)), content=txt)
       count += 1
   writer.commit()
   print(f"Indexed {count} files into {INDEX_DIR}")

if __name__ == "__main__":
   build_index()
