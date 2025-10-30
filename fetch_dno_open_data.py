#!/usr/bin/env python3
"""
Fetch & normalise GB DNO open data (DUoS/capacity/outage/assets/etc.)
- Discovers datasets across Opendatasoft portals (UKPN, SPEN, NPg, ENWL)
- Integrates NGED (ex-WPD) via CKAN API (token required)
- Scrapes SSEN portal for CSV resources
- Downloads CSV/JSON, loads to Pandas, writes Parquet + SQLite, and logs a catalog

Env:
  NGED_API_TOKEN    = <your CKAN token from connecteddata.nationalgrid.co.uk>
  DNO_OUT_DIR       = ./dno_data          (optional)
  DNO_DB_PATH       = ./dno_data/dno.sqlite
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import logging
import math
import os
import re
import sqlite3
import sys
import time
import urllib.parse as up
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry

# -------------------------
# Config & constants
# -------------------------

OPENDATASOFT_PORTALS = {
    "UKPN": "https://ukpowernetworks.opendatasoft.com",
    "SPEN": "https://spenergynetworks.opendatasoft.com",
    "NPg": "https://northernpowergrid.opendatasoft.com",
    "ENWL": "https://electricitynorthwest.opendatasoft.com",
    # SSEN handled separately (portal is mixed content, not pure ODS API)
}

# DNO ID map (your list)
DNO_ID_MAP = {
    12: "UKPN-LPN",
    10: "UKPN-EPN",
    19: "UKPN-SPN",
    16: "ENWL",
    15: "NPg-NE",
    23: "NPg-Y",
    18: "SP-Distribution",
    13: "SP-Manweb",
    17: "SSE-SHEPD",
    20: "SSE-SEPD",
    14: "NGED-WM",
    11: "NGED-EM",
    22: "NGED-SW",
    21: "NGED-SWales",
}

SEARCH_TERMS = [
    "duos",
    "distribution use of system",
    "annex",
    "cdcm",
    "pcdm",
    "dso",
    "flexibility",
    "flex",
    "headroom",
    "capacity",
    "dfes",
    "outage",
    "fault",
    "incident",
    "asset",
    "substation",
    "bsp",
    "gsp",
    "primary",
    "demand",
    "generation",
    "embedded",
    "ev",
    "connection",
]

# NGED CKAN
NGED_BASE = "https://connecteddata.nationalgrid.co.uk"
NGED_API = f"{NGED_BASE}/api/3/action"

# SSEN portal
SSEN_BASE = "https://data.ssen.co.uk"

# Output
OUT_DIR = Path(os.environ.get("DNO_OUT_DIR", "./dno_data")).resolve()
DB_PATH = Path(os.environ.get("DNO_DB_PATH", str(OUT_DIR / "dno.sqlite")))

# Logging
OUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT_DIR / "run.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)


# HTTP session with retries
def make_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update({"User-Agent": "Upowerenergy-DNO-Collector/1.0"})
    return s


SESSION = make_session()

# -------------------------
# Helpers
# -------------------------


def safe_slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s.strip())[:160]


def hash_str(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def write_parquet(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def append_sqlite(df: pd.DataFrame, table: str, db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        df.to_sql(table, con, if_exists="append", index=False)


def save_bytes(content: bytes, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def read_csv_bytes(b: bytes) -> pd.DataFrame:
    from io import BytesIO, StringIO

    # Try UTF-8 first, then fallback to latin-1
    try:
        return pd.read_csv(StringIO(b.decode("utf-8")), low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(StringIO(b.decode("latin-1")), low_memory=False)


# -------------------------
# Opendatasoft (UKPN, SPEN, NPg, ENWL)
# Docs: Explore API v2.1 (records/export CSV)
# -------------------------


def ods_search_datasets(base: str, query: str, rows: int = 200) -> List[dict]:
    url = f"{base}/api/v2/catalog/datasets"
    params = {"search": query, "rows": rows}
    r = SESSION.get(url, params=params, timeout=40)
    r.raise_for_status()
    return r.json().get("datasets", [])


def ods_dataset_endpoints(base: str, dataset_id: str) -> Dict[str, str]:
    base = base.rstrip("/")
    return {
        "records_json": f"{base}/api/explore/v2.1/catalog/datasets/{dataset_id}/records",
        "csv_export": f"{base}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv",
        "parquet_export": f"{base}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/parquet",
    }


def fetch_ods_csv(csv_url: str) -> Optional[pd.DataFrame]:
    r = SESSION.get(csv_url, timeout=120)
    if r.status_code == 200 and r.headers.get("Content-Type", "").lower().startswith(
        ("text/csv", "application/octet-stream")
    ):
        return read_csv_bytes(r.content)
    # Try anyway if 200 w/ another content type
    if r.status_code == 200:
        try:
            return read_csv_bytes(r.content)
        except Exception:
            logging.warning("CSV parse failed for %s", csv_url)
            return None
    logging.warning("CSV fetch failed %s (%s)", csv_url, r.status_code)
    return None


# -------------------------
# NGED (CKAN)
# Requires API token (free). See portal guidance.
# -------------------------


def nged_ckan_search(q: str, rows: int = 100) -> List[dict]:
    token = os.environ.get("NGED_API_TOKEN")
    if not token:
        logging.warning("NGED_API_TOKEN not set; skipping NGED CKAN search for '%s'", q)
        return []
    headers = {"Authorization": token}
    r = SESSION.get(
        f"{NGED_API}/package_search",
        params={"q": q, "rows": rows},
        headers=headers,
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("result", {}).get("results", [])


def nged_package_show(pkg_id: str) -> dict:
    token = os.environ.get("NGED_API_TOKEN")
    headers = {"Authorization": token}
    r = SESSION.get(
        f"{NGED_API}/package_show", params={"id": pkg_id}, headers=headers, timeout=60
    )
    r.raise_for_status()
    return r.json().get("result", {})


def fetch_nged_resource(url: str) -> Optional[pd.DataFrame]:
    # Expect CSV/JSON resources
    r = SESSION.get(url, timeout=120)
    if r.status_code != 200:
        logging.warning("NGED resource fetch failed %s (%s)", url, r.status_code)
        return None
    ctype = r.headers.get("Content-Type", "").lower()
    if "json" in ctype or url.lower().endswith(".json"):
        try:
            js = r.json()
            # Flatten simple JSON arrays of objects
            if isinstance(js, list):
                return pd.DataFrame(js)
            elif (
                isinstance(js, dict)
                and "result" in js
                and isinstance(js["result"], list)
            ):
                return pd.DataFrame(js["result"])
            else:
                # Attempt to coerce dict-of-lists or dict to rows
                return pd.json_normalize(js)
        except Exception:
            logging.exception("Failed to parse JSON from %s", url)
            return None
    else:
        try:
            return read_csv_bytes(r.content)
        except Exception:
            logging.exception("Failed to parse CSV from %s", url)
            return None


# -------------------------
# SSEN scraper (find CSV links on portal)
# -------------------------


def ssen_search_pages(terms: List[str], max_pages: int = 5) -> List[str]:
    """
    Very light-touch: hits SSEN homepage then tries simple search endpoints if present.
    Falls back to scanning the home and a few 'usecases' pages for CSV links.
    """
    found_urls = set()
    seeds = [SSEN_BASE, f"{SSEN_BASE}/usecases/connected"]
    for seed in seeds[:max_pages]:
        try:
            r = SESSION.get(seed, timeout=40)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = up.urljoin(SSEN_BASE, a["href"])
                if href.lower().endswith(".csv") or "format=csv" in href.lower():
                    found_urls.add(href)
        except Exception:
            logging.exception("SSEN scan failed on %s", seed)
    # Also probe simple term-based paths (some data portals do /?q=)
    for term in terms:
        try:
            url = f"{SSEN_BASE}/?q={up.quote(term)}"
            r = SESSION.get(url, timeout=40)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = up.urljoin(SSEN_BASE, a["href"])
                if href.lower().endswith(".csv") or "format=csv" in href.lower():
                    found_urls.add(href)
        except Exception:
            pass
    return sorted(found_urls)


# -------------------------
# Core pipeline
# -------------------------


def normalise_and_store(df: pd.DataFrame, dno: str, dataset_id: str, label: str):
    # basic clean
    df = df.copy()
    # standardise column names (snake-ish)
    df.columns = [re.sub(r"\s+", "_", c.strip()).lower() for c in df.columns]
    # write parquet & sqlite
    base = OUT_DIR / "parquet" / dno
    pq_path = base / f"{safe_slug(dataset_id or label)}.parquet"
    write_parquet(df, pq_path)
    append_sqlite(df, table=f"{safe_slug(dno)}__{safe_slug(dataset_id or label)}")
    logging.info("Stored %s rows for %s / %s", len(df), dno, dataset_id or label)


def run_opendatasoft():
    catalog_rows = []
    for dno, base in OPENDATASOFT_PORTALS.items():
        logging.info("=== Discovering on %s (%s) ===", dno, base)
        seen = set()
        for term in SEARCH_TERMS:
            try:
                datasets = ods_search_datasets(base, term, rows=200)
            except Exception:
                logging.exception("Search failed on %s term '%s'", dno, term)
                continue
            for ds in datasets:
                meta = ds.get("dataset", {})
                dsid = meta.get("dataset_id")
                if not dsid or dsid in seen:
                    continue
                seen.add(dsid)
                title = meta.get("metas", {}).get("title", "")
                endpoints = ods_dataset_endpoints(base, dsid)
                # Save catalog entry
                catalog_rows.append(
                    {
                        "dno": dno,
                        "dataset_id": dsid,
                        "title": title,
                        "records_json": endpoints["records_json"],
                        "csv_export": endpoints["csv_export"],
                    }
                )
                # Try to fetch CSV immediately (full export)
                df = fetch_ods_csv(endpoints["csv_export"])
                if df is not None and not df.empty:
                    normalise_and_store(df, dno, dsid, title)
                time.sleep(0.15)  # be nice
    # Write catalog
    if catalog_rows:
        cat_df = pd.DataFrame(catalog_rows).sort_values(["dno", "dataset_id"])
        normalise_and_store(
            cat_df, "CATALOG", "opendatasoft_catalog", "opendatasoft_catalog"
        )


def run_nged():
    # If no token, we already warn in nged_ckan_search
    catalog = []
    for term in SEARCH_TERMS:
        results = nged_ckan_search(term, rows=100)
        for pkg in results:
            pkg_id = pkg.get("id")
            title = pkg.get("title")
            name = pkg.get("name")
            catalog.append(
                {"package_id": pkg_id, "title": title, "name": name, "term": term}
            )
            # get resources (CSV/JSON)
            try:
                full = nged_package_show(pkg_id)
            except Exception:
                continue
            for res in full.get("resources", []) or []:
                url = res.get("url") or ""
                fmt = (res.get("format") or "").lower()
                if not url:
                    continue
                df = fetch_nged_resource(url)
                if df is not None and not df.empty:
                    label = f"{name}__{safe_slug(res.get('name') or fmt or 'resource')}"
                    normalise_and_store(df, "NGED", label, label)
            time.sleep(0.1)
    if catalog:
        cat = pd.DataFrame(catalog)
        normalise_and_store(cat, "CATALOG", "nged_ckan_catalog", "nged_ckan_catalog")


def run_ssen():
    csv_links = ssen_search_pages(SEARCH_TERMS, max_pages=5)
    catalog = []
    for url in csv_links:
        logging.info("SSEN CSV: %s", url)
        try:
            r = SESSION.get(url, timeout=90)
            if r.status_code != 200:
                continue
            df = read_csv_bytes(r.content)
            if df is not None and not df.empty:
                label = f"SSEN__{hash_str(url)}"
                normalise_and_store(df, "SSEN", label, label)
                catalog.append({"url": url, "rows": len(df)})
        except Exception:
            logging.exception("SSEN fetch failed for %s", url)
    if catalog:
        cat = pd.DataFrame(catalog)
        normalise_and_store(cat, "CATALOG", "ssen_catalog", "ssen_catalog")


def main():
    logging.info("Output folder: %s", OUT_DIR)
    run_opendatasoft()
    run_nged()
    run_ssen()
    logging.info("Done. Parquet under %s, SQLite at %s", OUT_DIR / "parquet", DB_PATH)


if __name__ == "__main__":
    main()
