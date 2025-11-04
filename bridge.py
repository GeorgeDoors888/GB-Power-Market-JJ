import os
import io
import sys
import time
import json
import base64
import hashlib
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional

from dotenv import load_dotenv
from tqdm import tqdm
from github import Github, ContentFile
from google.cloud import bigquery
from openai import OpenAI

# -----------------
# Config & Clients
# -----------------
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
BQ_DATASET = os.getenv("BQ_DATASET", "document_index")
BQ_TABLE = os.getenv("BQ_TABLE", "repo_chunks")

# Initialize lazy to allow "download only" mode without GCP/OpenAI
gh = Github(GITHUB_TOKEN) if GITHUB_TOKEN else None
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
bq_client = bigquery.Client(project=GCP_PROJECT_ID) if GCP_PROJECT_ID else None

TEXT_EXTS = {
    ".py",".js",".ts",".tsx",".jsx",".json",".yml",".yaml",".md",".txt",
    ".toml",".ini",".cfg",".xml",".html",".css",".sql",".ipynb",".sh",".ps1",
    ".cfg",".env",".dockerfile",".Dockerfile"
}
MAX_FILE_BYTES = 400_000  # ~400 KB guard to avoid massive blobs inline


# -----------------
# Helpers
# -----------------
def is_text_path(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXTS: return True
    # Heuristic: treat unknown small files as text, skip obvious binaries
    return ext == "" and not any(path.lower().endswith(x) for x in [".png",".jpg",".jpeg",".gif",".pdf",".mp4",".mov",".zip",".gz",".tar",".rar",".7z",".woff",".ttf",".eot"])

def safe_decode(cf: ContentFile.ContentFile) -> Optional[str]:
    try:
        if cf.size and cf.size > MAX_FILE_BYTES:
            return None
        if cf.encoding == "base64":
            return base64.b64decode(cf.content).decode("utf-8", errors="ignore")
        # PyGithub usually gives base64; fallback:
        return cf.decoded_content.decode("utf-8", errors="ignore")
    except Exception:
        return None

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


# -----------------
# GitHub fetch
# -----------------
def fetch_repo_tree(repo_full: str, branch: str) -> List[Dict]:
    repo = gh.get_repo(repo_full)
    commit = repo.get_commit(branch)
    tree = repo.get_git_tree(commit.sha, recursive=True).tree
    files = [t.path for t in tree if t.type == "blob"]
    return files

def download_text_files(repo_full: str, branch: str, include_hidden=False) -> List[Dict]:
    repo = gh.get_repo(repo_full)
    paths = fetch_repo_tree(repo_full, branch)
    out = []
    for p in tqdm(paths, desc="Downloading files"):
        if not include_hidden and any(seg.startswith(".") for seg in p.split("/")):
            continue
        if not is_text_path(p):
            continue
        try:
            cf = repo.get_contents(p, ref=branch)
            text = safe_decode(cf)
            if text is None:
                continue
            out.append({
                "repo": repo_full,
                "branch": branch,
                "path": p,
                "sha": cf.sha,
                "size": cf.size,
                "text": text
            })
        except Exception:
            # ignore individual fetch errors
            continue
    return out


# -----------------
# OpenAI analysis
# -----------------
def summarize_file(path: str, text: str, model: str = "gpt-4o-mini") -> str:
    """
    Short, structured summary for code or docs.
    """
    if not openai_client:
        return ""
    prompt = f"""Provide a concise, structured summary of the following file to help search and onboarding.

File path: {path}

Please include:
- Purpose / responsibilities
- Key functions/classes or sections
- Inputs/outputs or side effects
- Notable dependencies or config flags
- Risks / TODOs

Text:
{text[:12000]}
"""
    resp = openai_client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role":"system","content":"You are a precise software documentation assistant."},
            {"role":"user","content":prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

def summarize_repo(files: List[Dict], model: str = "gpt-4o-mini") -> str:
    if not openai_client:
        return ""
    index = "\n".join(f"- {f['path']} (sha:{f['sha'][:7]})" for f in files[:200])
    prompt = f"""Create an executive summary of this repository for a technical audience.

Include:
- What the system does and main components
- Runtime (CLI/server), entrypoints, dev workflow
- External services (APIs, BigQuery, Drive) and credentials needed
- How to deploy / run locally
- Key risks / gaps

File inventory (subset):
{index}
"""
    resp = openai_client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role":"system","content":"You write crisp, actionable technical docs."},
            {"role":"user","content":prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

def embed_text(text: str, model: str = "text-embedding-3-small") -> List[float]:
    if not openai_client:
        return []
    r = openai_client.embeddings.create(model=model, input=text[:8000])
    return r.data[0].embedding


# -----------------
# BigQuery sync
# -----------------
def ensure_bq_table():
    assert bq_client, "BigQuery client not configured"
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    schema = [
        bigquery.SchemaField("repo", "STRING"),
        bigquery.SchemaField("branch", "STRING"),
        bigquery.SchemaField("path", "STRING"),
        bigquery.SchemaField("sha", "STRING"),
        bigquery.SchemaField("summary", "STRING"),
        bigquery.SchemaField("content", "STRING"),
        bigquery.SchemaField("embedding", "FLOAT", mode="REPEATED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP"),
        bigquery.SchemaField("content_sha1", "STRING"),
    ]
    try:
        bq_client.get_table(table_id)
    except Exception:
        dataset_ref = bigquery.Dataset(f"{GCP_PROJECT_ID}.{BQ_DATASET}")
        try:
            bq_client.get_dataset(dataset_ref)
        except Exception:
            bq_client.create_dataset(dataset_ref, exists_ok=True)
        bq_client.create_table(bigquery.Table(table_id, schema=schema), exists_ok=True)

def upsert_rows(rows: List[Dict]):
    assert bq_client, "BigQuery client not configured"
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    errors = bq_client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

def chunk(s: List, n: int):
    for i in range(0, len(s), n):
        yield s[i:i+n]

def sync_to_bigquery(files: List[Dict], do_embeddings=True) -> int:
    ensure_bq_table()
    now = datetime.now(timezone.utc).isoformat()
    total = 0
    for batch in tqdm(list(chunk(files, 100)), desc="Syncing to BigQuery"):
        rows = []
        for f in batch:
            content_sha1 = sha1(f["text"])
            summary = f.get("summary","")
            emb = embed_text(summary or f["text"]) if do_embeddings else []
            rows.append({
                "repo": f["repo"],
                "branch": f["branch"],
                "path": f["path"],
                "sha": f["sha"],
                "summary": summary,
                "content": f["text"][:20000],  # store head; full text can be large
                "embedding": emb,
                "updated_at": now,
                "content_sha1": content_sha1
            })
        upsert_rows(rows)
        total += len(rows)
    return total


# -----------------
# Diagnostics
# -----------------
def diagnose():
    print("\n=== Diagnostics Mode ===")

    # 1. GitHub check
    if gh:
        try:
            repo = gh.get_repo(GITHUB_REPO)
            _ = repo.description
            print(f"🔍 GitHub API: ✅ OK ({GITHUB_REPO} accessible)")
        except Exception as e:
            print(f"🔍 GitHub API: ❌ FAILED → {e}")
    else:
        print("🔍 GitHub API: ⚠️ No token configured")

    # 2. OpenAI API check
    if openai_client:
        try:
            test = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":"test"}],
                max_tokens=10
            )
            print("🧠 OpenAI API: ✅ OK (GPT-4 responding)")
        except Exception as e:
            print(f"🧠 OpenAI API: ❌ FAILED → {e}")
    else:
        print("🧠 OpenAI API: ⚠️ No API key configured")

    # 3. BigQuery check
    if bq_client:
        try:
            dataset_ref = bigquery.Dataset(f"{GCP_PROJECT_ID}.{BQ_DATASET}")
            bq_client.get_dataset(dataset_ref)
            print(f"🪣 BigQuery: ✅ OK (Dataset {BQ_DATASET} reachable)")
            try:
                bq_client.get_table(f"{GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}")
                print(f"   └─ Table {BQ_TABLE}: ✅ Found")
            except Exception:
                print(f"   └─ Table {BQ_TABLE}: ⚠️ Missing (will auto-create)")
        except Exception as e:
            print(f"🪣 BigQuery: ❌ FAILED → {e}")
    else:
        print("🪣 BigQuery: ⚠️ Client not configured")

    print("\nDiagnostics complete.\n")


# -----------------
# CLI
# -----------------
def main():
    ap = argparse.ArgumentParser(description="GitHub → GPT → BigQuery bridge")
    ap.add_argument("--diagnose", action="store_true", help="run connectivity diagnostics only")
    ap.add_argument("--repo", default=GITHUB_REPO, help="owner/name")
    ap.add_argument("--branch", default=GITHUB_BRANCH)
    ap.add_argument("--include-hidden", action="store_true", help="include dotfiles")
    ap.add_argument("--no-summarise", action="store_true")
    ap.add_argument("--no-embed", action="store_true")
    ap.add_argument("--no-bq", action="store_true")
    ap.add_argument("--save-repo-summary", default="REPO_SUMMARY.md")
    args = ap.parse_args()

    if args.diagnose:
        diagnose()
        return

    if not gh:
        print("ERROR: GITHUB_TOKEN missing.")
        sys.exit(1)

    print(f"Fetching {args.repo}@{args.branch} …")
    files = download_text_files(args.repo, args.branch, include_hidden=args.include_hidden)

    if not args.no_summarise:
        print("Summarising files with GPT…")
        for f in tqdm(files, desc="Summarising"):
            # keep context small to control cost
            head = f["text"][:30_000]
            f["summary"] = summarize_file(f["path"], head)

        print("Creating repository executive summary…")
        repo_summary = summarize_repo(files)
        with open(args.save_repo_summary, "w", encoding="utf-8") as w:
            w.write(repo_summary)
        print(f"Wrote {args.save_repo_summary}")

    if not args.no_bq:
        if not bq_client:
            print("WARN: BigQuery not configured; skipping BQ sync.")
        else:
            print("Syncing rows to BigQuery…")
            count = sync_to_bigquery(files, do_embeddings=not args.no_embed)
            print(f"Upserted {count} rows to {GCP_PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}")

    print("Done.")

if __name__ == "__main__":
    main()
