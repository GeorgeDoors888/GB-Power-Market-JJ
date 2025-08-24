#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
research_to_gdoc_plus.py  —  Cleaned & improved

Creates a Google Doc with REAL tables + a JSON sidecar summarizing datasets/APIs.
- SerpAPI primary search, Google CSE fallback (deduped, polite pacing)
- GitHub metadata + README (if provided)
- OpenAI synthesis including "publish vs event timing"
- True Google Docs tables (insertTable + targeted cell writes)
- JSON sidecar includes structured summary + links used (provenance)
- Keys auto-load from ./8_august_jibber_jabber then env
- Optional --test to run quickly on two targets

Run:
  pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 \
              requests tenacity python-dotenv
  python research_to_gdoc_plus.py --title "Energy Data Sources – Live & Settlement" --export-pdf
"""

from __future__ import annotations
import os, io, json, time, base64, argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# ---------- Load keys from ./8_august_jibber_jabber then env ----------
KEY_DIR = Path("./8_august_jibber_jabber")
if KEY_DIR.is_dir():
    env_path = KEY_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    for name, envvar in [
        ("openai.key", "OPENAI_API_KEY"),
        ("serpapi.key", "SERPAPI_KEY"),
        ("google_cse_key.key", "GOOGLE_SEARCH_API_KEY"),
        ("google_cse_cx.key", "GOOGLE_SEARCH_CX"),
    ]:
        f = KEY_DIR / name
        if f.exists() and not os.environ.get(envvar):
            os.environ[envvar] = f.read_text().strip()
    sa = KEY_DIR / "service_account.json"
    if sa.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(sa.resolve())

# ---------- Config ----------
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX = os.environ.get("GOOGLE_SEARCH_CX")
SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# ---------- Google APIs ----------
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

def build_google_clients():
    if not SERVICE_ACCOUNT_FILE or not Path(SERVICE_ACCOUNT_FILE).exists():
        raise RuntimeError(
            "Missing Google service account file. "
            "Set GOOGLE_APPLICATION_CREDENTIALS or place service_account.json in ./8_august_jibber_jabber"
        )
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return build("docs", "v1", credentials=creds), build("drive", "v3", credentials=creds)

# ---------- Search ----------
def serpapi_search(query: str, num: int = 7) -> List[Dict[str, Any]]:
    if not SERPAPI_KEY:
        return []
    url = "https://serpapi.com/search.json"
    params = {"engine": "google", "q": query, "num": min(10, max(1, num)), "api_key": SERPAPI_KEY}
    r = requests.get(url, params=params, timeout=40)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for it in data.get("organic_results", []):
        out.append({"title": it.get("title"), "link": it.get("link"), "snippet": it.get("snippet")})
    return out

def google_cse_search(query: str, num: int = 7) -> List[Dict[str, Any]]:
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX:
        return []
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_SEARCH_API_KEY, "cx": GOOGLE_SEARCH_CX, "q": query, "num": min(10, max(1, num))}
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        return []
    data = r.json()
    return [{"title": it.get("title"), "link": it.get("link"), "snippet": it.get("snippet")} for it in data.get("items", [])]

def blended_search(query: str, take: int = 7) -> List[Dict[str, Any]]:
    primary = serpapi_search(query, num=take)
    results = primary
    if len(primary) < 3:  # fallback if poor coverage
        time.sleep(0.5)
        secondary = google_cse_search(query, num=take)
        # dedupe
        seen, merged = set(), []
        for src in (primary + secondary):
            link = src.get("link")
            if link and link not in seen:
                seen.add(link)
                merged.append(src)
        results = merged
    time.sleep(0.4)  # polite pacing per query
    return results[:take]

# ---------- GitHub ----------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

def gh_headers() -> Dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h

def parse_owner_repo(url: str) -> Optional[Tuple[str, str]]:
    try:
        p = urlparse(url)
        parts = [x for x in p.path.split("/") if x]
        if len(parts) >= 2:
            return parts[0], parts[1]
    except Exception:
        pass
    return None

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_github_repo(owner: str, repo: str) -> Dict[str, Any]:
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=gh_headers(), timeout=30)
    r.raise_for_status()
    return r.json()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_github_readme(owner: str, repo: str) -> Optional[str]:
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}/readme", headers=gh_headers(), timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    j = r.json()
    if "content" in j and j.get("encoding") == "base64":
        return base64.b64decode(j["content"]).decode("utf-8", errors="ignore")
    return None

# ---------- OpenAI ----------
def openai_summarize(raw: str, label: str) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        return {
            "dataset_name": label,
            "description": "OpenAI key missing; summary not generated.",
            "access": "unspecified",
            "cost": "unspecified",
            "auth": "unspecified",
            "rate_limits": "unspecified",
            "data_formats": "unspecified",
            "endpoints_examples": "unspecified",
            "publish_vs_event_timing": "unspecified",
            "licensing": "unspecified",
            "notes": "unspecified",
        }
    prompt = f"""
You are auditing an energy dataset/API. Produce STRICT JSON with keys:
dataset_name, description, access, cost, auth, rate_limits, data_formats, endpoints_examples,
publish_vs_event_timing, licensing, notes.
- publish_vs_event_timing MUST quantify latency/lead where possible (e.g. "T+5 min", "day-ahead", "T+29 days").
- If unknown, write "unspecified". Do not invent numbers.
Context for {label}:
---
{raw[:9000]}
"""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": OPENAI_MODEL,
        "messages": [{"role": "system", "content": "Be precise and concise."},
                     {"role": "user", "content": prompt}],
        "temperature": 0.1,
    }
    r = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body, timeout=60)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
        # Ensure all keys present
        for k in ["dataset_name","description","access","cost","auth","rate_limits","data_formats",
                  "endpoints_examples","publish_vs_event_timing","licensing","notes"]:
            data.setdefault(k, "unspecified")
        return data
    except Exception:
        return {
            "dataset_name": label,
            "description": content[:800],
            "access": "unspecified", "cost": "unspecified", "auth": "unspecified",
            "rate_limits": "unspecified", "data_formats": "unspecified",
            "endpoints_examples": "unspecified", "publish_vs_event_timing": "unspecified",
            "licensing": "unspecified", "notes": "unspecified",
        }

# ---------- Google Docs helpers (append-at-end; robust table fill) ----------
def create_doc(docs, title: str) -> str:
    return docs.documents().create(body={"title": title}).execute()["documentId"]

def get_end_index(docs, doc_id: str) -> int:
    doc = docs.documents().get(documentId=doc_id).execute()
    return doc["body"]["content"][-1]["endIndex"]

def insert_text(docs, doc_id: str, text: str, style: Optional[str] = None) -> None:
    idx = get_end_index(docs, doc_id)
    requests_body = [{"insertText": {"location": {"index": idx-1}, "text": text}}]
    if style:
        requests_body.append({
            "updateParagraphStyle": {
                "range": {"startIndex": idx-1, "endIndex": idx-1 + len(text)},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType",
            }
        })
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests_body}).execute()

def insert_table(docs, doc_id: str, rows: List[List[str]]) -> None:
    start_idx = get_end_index(docs, doc_id) - 1
    rows_n, cols_n = len(rows), len(rows[0]) if rows else 2
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": [{
        "insertTable": {"rows": rows_n, "columns": cols_n, "location": {"index": start_idx}}
    }]}).execute()

    doc = docs.documents().get(documentId=doc_id).execute()
    content = doc.get("body", {}).get("content", [])
    target = None
    for elem in content:
        if "table" in elem and elem["startIndex"] >= start_idx:
            target = elem["table"]
            break
    if target is None:
        target = [c["table"] for c in content if "table" in c][-1]

    reqs = []
    for r_i, row in enumerate(target["tableRows"]):
        for c_i, cell in enumerate(row["tableCells"]):
            cell_start = cell["startIndex"] + 1
            txt = rows[r_i][c_i]
            reqs.append({"insertText": {"location": {"index": cell_start}, "text": txt}})
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": reqs}).execute()

def add_dataset_section(docs, doc_id: str, title: str, summary: Dict[str, Any]) -> None:
    insert_text(docs, doc_id, "\n")
    insert_text(docs, doc_id, f"{title}\n", "HEADING_2")
    def get(k: str) -> str:
        v = summary.get(k, "unspecified")
        if isinstance(v, list):  # formats might be list
            return ", ".join(v)
        return str(v)
    rows = [
        ["Dataset name", get("dataset_name")],
        ["Description", get("description")],
        ["Access", get("access")],
        ["Cost", get("cost")],
        ["Auth", get("auth")],
        ["Rate limits", get("rate_limits")],
        ["Formats", get("data_formats")],
        ["Endpoints (examples)", get("endpoints_examples")],
        ["Publish vs event timing", get("publish_vs_event_timing")],
        ["Licensing", get("licensing")],
        ["Notes", get("notes")],
    ]
    insert_table(docs, doc_id, rows)

def export_pdf(drive, doc_id: str, out_name: str) -> Optional[str]:
    try:
        data = drive.files().export(fileId=doc_id, mimeType="application/pdf").execute()
        media = MediaIoBaseUpload(io.BytesIO(data), mimetype="application/pdf", resumable=False)
        uploaded = drive.files().create(body={"name": out_name, "mimeType": "application/pdf"}, media_body=media).execute()
        return uploaded.get("id")
    except Exception:
        return None

# ---------- Targets (pre‑mapped; still researched) ----------
TARGETS: List[Dict[str, Any]] = [
    # Real-time / near-real-time
    {"label": "BMRS IRIS streaming (near-real-time market data)",
     "queries": [
         "Elexon BMRS IRIS streaming API AMQP websocket documentation",
         "Elexon Insights IRIS topics latency frequency demand interconnectors"
     ]},
    {"label": "Elexon – Interconnector flows (Insights/FUELINST)",
     "queries": [
         "Elexon interconnector flows API FUELINST generation outturn interconnectors endpoint",
         "site:bmrs.elexon.co.uk interconnectors API documentation"
     ]},
    {"label": "ESO Operational Data Portal (near-real-time)",
     "queries": [
         "ESO National Grid data portal API demand forecast generation mix interconnector flows JSON CSV",
         "site:data.nationalgrideso.com api"
     ]},

    # Settlement / historical
    {"label": "Elexon Open Settlement Data (CSV zips)",
     "queries": [
         "site:elexon.co.uk Open Settlement Data CSV CDCA-I029 CDCA-I030 I042 SAA-I014 download",
         "Elexon settlement data timing II SF R1 R2 RF publication schedule"
     ]},
    {"label": "Elexon Market Domain Data (MDD)",
     "queries": [
         "Elexon Market Domain Data MDD download portal schedule",
         "MDD release schedule Elexon"
     ]},

    # Prices / system metrics
    {"label": "SBP/SSP (System Prices) – Insights (B1770 family)",
     "queries": [
         "Elexon system buy price system sell price dataset code B1770 API",
         "BMRS system prices indicative vs final publication timing"
     ]},
    {"label": "NIV (Net Imbalance Volume) – Insights",
     "queries": [
         "Elexon Net Imbalance Volume NIV dataset API code documentation",
         "BMRS NIV indicative vs final timing"
     ]},
    {"label": "BOA / Bid-Offer Acceptances – Insights",
     "queries": [
         "Elexon BOA bid offer acceptance dataset API documentation",
         "DISBSAD BOALF BMRS API timing publication"
     ]},

    # GitHub repos you cited
    {"label": "Elexon GitHub org", "queries": ["site:github.com elexon-data"], "explicit_url": "https://github.com/elexon-data"},
    {"label": "Nord Pool – public intraday API (GitHub)", "queries": ["NordPool public intraday api github"], "explicit_url": "https://github.com/NordPool/public-intraday-api"},
    {"label": "goEpexSpot (EPEX spot prices) – GitHub", "queries": ["timebis goEpexSpot github"], "explicit_url": "https://github.com/timebis/goEpexSpot"},
    {"label": "NESO (UK System Operator) – GitHub", "queries": ["neso-io github"], "explicit_url": "https://github.com/neso-io"},
]

# ---------- Research & compose ----------
def collect_context(target: Dict[str, Any]) -> Tuple[str, List[str]]:
    """Return (context_text, links_used)."""
    pieces: List[str] = []
    links: List[str] = []

    for q in target.get("queries", []):
        res = blended_search(q, take=7)
        if res:
            pieces.append(f"Search: {q}")
            for it in res[:5]:
                link = it.get("link", "")
                links.append(link)
                pieces.append(f"- {it.get('title','')} :: {link}\n  {it.get('snippet','')}")
    url = target.get("explicit_url")
    if url and "github.com" in url:
        owner_repo = parse_owner_repo(url)
        if owner_repo:
            owner, repo = owner_repo
            try:
                meta = fetch_github_repo(owner, repo)
                pieces.append(f"GitHub: {meta.get('full_name')} ⭐{meta.get('stargazers_count')} :: {meta.get('html_url')}")
                if meta.get("license"):
                    pieces.append(f"License: {meta['license'].get('spdx_id')}")
                readme = fetch_github_readme(owner, repo)
                if readme:
                    pieces.append("\nREADME (truncated):\n" + readme[:4000])
                links.append(meta.get("html_url", url))
            except Exception as e:
                pieces.append(f"GitHub fetch failed: {e}")
    # de-dup links and limit
    dedup = []
    seen = set()
    for L in links:
        if L and L not in seen:
            seen.add(L)
            dedup.append(L)
    return "\n".join(pieces), dedup[:8]

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="Energy Data Sources – Live & Settlement")
    ap.add_argument("--export-pdf", action="store_true")
    ap.add_argument("--json-out", default="research_summary.json")
    ap.add_argument("--test", action="store_true", help="Run only the first two targets and mark doc as (TEST)")
    args = ap.parse_args()

    if args.test:
        targets = TARGETS[:2]
        args.title = args.title + " (TEST)"
    else:
        targets = TARGETS

    docs, drive = build_google_clients()
    doc_id = create_doc(docs, args.title)

    # Title & intro
    insert_text(docs, doc_id, args.title + "\n", "HEADING_1")
    insert_text(docs, doc_id,
                "Auto-generated research. Focus: live/near-real-time + settlement datasets; timing vs event; access & cost.\n")

    # Settlement timing reference
    insert_text(docs, doc_id, "\nSettlement Run Timing (Reference)\n", "HEADING_2")
    ref_rows = [
        ["Run", "Description", "Publish time after event"],
        ["II", "Initial Interim", "≈ T+5–6 hours"],
        ["SF", "Initial Settlement", "≈ T+29 days"],
        ["R1", "First Reconciliation", "≈ T+3 months"],
        ["R2", "Second Reconciliation", "≈ T+8 months"],
        ["RF", "Final Reconciliation", "≈ T+14 months"],
    ]
    insert_table(docs, doc_id, ref_rows)
    insert_text(docs, doc_id, "\n")

    # Met Office DataPoint (seed)
    insert_text(docs, doc_id, "Met Office DataPoint (Free)\n", "HEADING_2")
    dp_rows = [
        ["Base URL", "http://datapoint.metoffice.gov.uk/public/data/"],
        ["Access", "Free with API key (registration)"],
        ["Products", "Forecasts (5 days, 3‑hourly/daily); hourly observations; textual forecasts; charts; map overlays"],
        ["Latency/Updates", "Forecasts hourly; obs hourly; overlays hourly/15 min"],
        ["Formats", "XML, JSON, PNG"],
        ["Notes", "Use sitelist/capabilities feeds; include key=YOUR_API_KEY"],
    ]
    insert_table(docs, doc_id, dp_rows)
    insert_text(docs, doc_id, "\n")

    # Research
    summaries: List[Dict[str, Any]] = []
    for t in targets:
        label = t["label"]
        ctx, links_used = collect_context(t)
        summary = openai_summarize(ctx, label)
        summaries.append({"label": label, "summary": summary, "links_used": links_used})
        add_dataset_section(docs, doc_id, label, summary)

    # JSON sidecar
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    insert_text(docs, doc_id, f"\nJSON sidecar saved: {args.json_out}\n")

    print(f"Created Google Doc: https://docs.google.com/document/d/{doc_id}/edit")
    if args.export_pdf:
        pdf_id = export_pdf(drive, doc_id, args.title + ".pdf")
        if pdf_id:
            print(f"Exported PDF fileId: {pdf_id}")

if __name__ == "__main__":
    main()
