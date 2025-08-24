#!/usr/bin/env python3
import argparse, pathlib
from whoosh import index
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.highlight import ContextFragmenter, UppercaseFormatter

ROOT = pathlib.Path(__file__).resolve().parents[2]
INDEX_DIR = pathlib.Path(__file__).resolve().parent / "indexdir"
OUT_DIR = ROOT / "context"
OUT_DIR.mkdir(exist_ok=True)

def search(query: str, k: int = 10):
   if not index.exists_in(INDEX_DIR):
       print("Index not found. Run: python tools/ai_memory/index_repo.py")
       return
   ix = index.open_dir(INDEX_DIR)
   qp = MultifieldParser(["content"], schema=ix.schema, group=OrGroup)
   q = qp.parse(query)
   with ix.searcher() as s:
       results = s.search(q, limit=k)
       results.fragmenter = ContextFragmenter(maxchars=200, surround=60)
       results.formatter = UppercaseFormatter()
       out_md = [f"# Context for: {query}", ""]
       print(f"\nTop {min(k, len(results))} results:\n")
       for i, hit in enumerate(results):
           path = hit["path"]
           snippet = hit.highlights("content") or ""
           print(f"{i+1}. {path}\n   {snippet}\n")
           out_md.append(f"## {i+1}. {path}\n\n{snippet}\n")
       out_path = OUT_DIR / "context.md"
       out_path.write_text("\n".join(out_md), encoding="utf-8")
       print(f"\nSaved combined context to {out_path}")

if __name__ == "__main__":
   ap = argparse.ArgumentParser()
   ap.add_argument("query", help="What are you looking for?")
   ap.add_argument("-k", type=int, default=10, help="How many results")
   args = ap.parse_args()
   search(args.query, args.k)
