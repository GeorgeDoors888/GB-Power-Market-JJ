#!/usr/bin/env python3
"""
elexon_catalogue_plus.py
All-in-one:
- Crawl Elexon GitHub + doc seeds
- Scrape BMRS docs to export BMRS code metadata
- Discover endpoints + ping
- Build mapping sheet (BMRS item -> Insights dataset family -> example path) with fuzzy matching
- Export MkDocs skeleton + data_dictionary.md
- Generate a Streamlit UI to explore + re-ping endpoints

Dependencies:
  pip install requests beautifulsoup4 markdownify pyyaml pandas rapidfuzz streamlit
"""

import os, re, sys, json, time, hashlib, textwrap, csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import requests
import pandas as pd
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from rapidfuzz import process as fuzzproc, fuzz
import yaml

# --------------------
# Config & constants
# --------------------
TITLE = "Upowerenergy - George vJJ0.1"
ORG = "elexon-data"
OUT_DIR = Path("_elexon_catalogue")
DOCS_DIR = OUT_DIR / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
INSIGHTS_API_KEY = os.getenv("INSIGHTS_API_KEY", "").strip()
INSIGHTS_DOC_HINTS = [u for u in os.getenv("INSIGHTS_DOC_HINTS","").split(",") if u.strip()]
PING_METHOD = os.getenv("PING_METHOD","head").lower().strip()  # head|get

# Seeds (you can add more via INSIGHTS_DOC_HINTS env var)
DOC_SEEDS = [
    # Insights overview:
    "https://www.elexon.co.uk/kinnect-product/insights-solution/",
    # BMRS data directory (historic index):
    "https://www.elexon.co.uk/guidance_note/bmrs-data-directory/",
    # BMRS API doc search (broad):
    "https://bmrs.elexon.co.uk/api-documentation/search-results?query=all",
]
# Simple URL detectors
URL_RX = re.compile(r'https?://[^\s)>\]"}]+', re.IGNORECASE)
API_RX = re.compile(r'/api(?:/|\?)|/datasets/|swagger|openapi|/services/|/odata', re.IGNORECASE)

# Basic classifier (tweak as needed)
def canonical_class(u: str) -> str:
    lu = u.lower()
    if any(x in lu for x in ["insights", "kinnect", "elexon.co.uk/odata", "/datasets/", "/services/"]):
        return "current"
    if any(x in lu for x in ["bmrs.elexon", "bmreports"]):
        return "historic"
    return "other"

# --------------------
# HTTP helpers
# --------------------
def gh_headers():
    h = {"Accept":"application/vnd.github+json", "User-Agent":"elexon-catalog"}
    if GITHUB_TOKEN:
        h["Authorization"]=f"Bearer {GITHUB_TOKEN}"
    return h

def get_json(url, params=None, headers=None, timeout=30):
    h = headers or {}
    try:
        r = requests.get(url, params=params or {}, headers=h or {}, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        return None
    return None

def get_text(url, headers=None, timeout=30):
    try:
        r = requests.get(url, headers=headers or {}, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except requests.RequestException:
        return ""
    return ""

def ping_endpoint(url: str, method: str = "head") -> Optional[int]:
    hdr={}
    if INSIGHTS_API_KEY:
        # common header (adjust if your gateway uses a different header)
        hdr["x-api-key"]=INSIGHTS_API_KEY
        # some gateways use Authorization: Bearer
        # hdr["Authorization"]=f"Bearer {INSIGHTS_API_KEY}"
    try:
        if method == "get":
            r = requests.get(url, headers=hdr, timeout=12, allow_redirects=True)
        else:
            r = requests.head(url, headers=hdr, timeout=12, allow_redirects=True)
        return r.status_code
    except requests.RequestException:
        return None

# --------------------
# Discovery
# --------------------
def crawl_github_org(org: str) -> pd.DataFrame:
    repos=[]
    page=1
    while True:
        js=get_json(f"https://api.github.com/orgs/{org}/repos", {"per_page":100,"page":page}, headers=gh_headers())
        if not js:
            break
        repos+=js
        if len(js)<100:
            break
        page+=1

    url_hits=[]
    for r in repos:
        readme = get_json(f"https://api.github.com/repos/{org}/{r['name']}/readme", headers=gh_headers())
        if readme and readme.get("download_url"):
            markdown = get_text(readme["download_url"])
            for u in set(URL_RX.findall(markdown)):
                if API_RX.search(u):
                    url_hits.append(dict(
                        source="github-readme",
                        repo=r["html_url"],
                        url=u,
                        cls=canonical_class(u)
                    ))
    return pd.DataFrame(url_hits)

def scrape_doc_seeds(seeds: List[str]) -> pd.DataFrame:
    hits=[]
    for url in seeds:
        html=get_text(url)
        for u in set(URL_RX.findall(html)):
            if API_RX.search(u):
                hits.append(dict(source="doc-site", repo="", url=u, cls=canonical_class(u)))
    return pd.DataFrame(hits)

# --------------------
# BMRS code extraction (names -> codes -> doc URLs)
# --------------------
def scrape_bmrs_codes(search_url: str) -> pd.DataFrame:
    """
    Attempts to parse BMRS API documentation search page(s) to extract
    BMRS 'data item' codes & names + links for provenance.
    This is heuristic; it tries:
      - explicit tables listing code/name
      - anchor/link patterns with item codes like Bnnnn
    """
    html = get_text(search_url)
    print("\n[DEBUG] First 500 chars of HTML fetched from", search_url)
    print(html[:500])
    soup = BeautifulSoup(html, "html.parser")
    rows=[]

    # 1) table scan: <table> ... <tr><td>Code</td><td>Name</td>...
    for tbl in soup.find_all("table"):
        headers=[(th.get_text(strip=True) or "").lower() for th in tbl.find_all("th")]
        # naive guess: look for 'code' & 'name'
        if any("code" in h for h in headers) and any("name" in h for h in headers):
            for tr in tbl.find_all("tr"):
                tds=[td.get_text(strip=True) for td in tr.find_all("td")]
                if len(tds)>=2:
                    code = tds[0]
                    name = tds[1]
                    if re.match(r'^[A-Z]\d{3,4}', code):
                        rows.append(dict(code=code, name=name, doc_url=search_url))
    # 2) link text like "B1770 – Imbalance Prices"
    for a in soup.find_all("a"):
        txt=(a.get_text(" ", strip=True) or "")
        m=re.match(r'([A-Z]\d{3,4})\s*[–-]\s*(.+)$', txt)
        if m:
            rows.append(dict(code=m.group(1).strip(), name=m.group(2).strip(), doc_url=urljoin(search_url, a.get("href") or "")))

    print(f"[DEBUG] Found {len(rows)} code/name rows:")
    for row in rows[:10]:
        print("  ", row)
    if len(rows) > 10:
        print(f"  ...and {len(rows)-10} more rows")

    df=pd.DataFrame(rows)
    # Only deduplicate/sort if columns exist
    if not df.empty and set(["code","name"]).issubset(df.columns):
        df = df.drop_duplicates(subset=["code","name"]).sort_values(["code","name"])
    else:
        print("[WARNING] No code/name columns found in BMRS code scrape. DataFrame columns:", df.columns.tolist())
    return df

def expand_bmrs_from_follow_links(df_codes: pd.DataFrame, max_follow: int=25) -> pd.DataFrame:
    """
    Follow up to 'max_follow' doc_url pages to extract deeper BMRS code/name pairs.
    """
    seen=set()
    extra=[]
    for i, row in df_codes.head(max_follow).iterrows():
        url=row.get("doc_url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        html=get_text(url)
        if not html:
            continue
        soup=BeautifulSoup(html,"html.parser")
        for a in soup.find_all("a"):
            txt=(a.get_text(" ", strip=True) or "")
            m=re.match(r'([A-Z]\d{3,4})\s*[–-]\s*(.+)$', txt)
            if m:
                extra.append(dict(code=m.group(1).strip(), name=m.group(2).strip(), doc_url=urljoin(url, a.get("href") or "")))
    if extra:
        dfx=pd.DataFrame(extra).drop_duplicates(subset=["code","name"])
        return pd.concat([df_codes, dfx], ignore_index=True).drop_duplicates(subset=["code","name"])
    return df_codes

# --------------------
# Mapping builder
# --------------------
def derive_family_from_url(u: str) -> str:
    """
    Heuristic family name from URL path segments.
    """
    p=urlparse(u)
    seg=[s for s in p.path.split("/") if s]
    for s in reversed(seg):
        if re.search(r'[a-z]', s):
            return s.replace("-", "_").lower()
    return (p.netloc or "unknown").lower()

def auto_map_bmrs_to_endpoints(df_bmrs: pd.DataFrame, df_endpoints: pd.DataFrame) -> pd.DataFrame:
    """
    Fuzzy match BMRS names to endpoint 'families' derived from URLs.
    Produces: bmrs_code, bmrs_name, insights_family, example_url, match_score
    """
    if df_endpoints.empty or df_bmrs.empty:
        return pd.DataFrame(columns=["bmrs_code","bmrs_name","insights_family","example_url","match_score"])

    df_endpoints = df_endpoints.copy()
    df_endpoints["family"] = df_endpoints["url"].apply(derive_family_from_url)

    # Build candidates: family -> example url
    fam_to_example = {}
    for fam, grp in df_endpoints.groupby("family"):
        sample = grp.iloc[0]["url"]
        fam_to_example[fam] = sample

    families = list(fam_to_example.keys())
    out_rows=[]
    for _, r in df_bmrs.iterrows():
        code = r.get("code","").strip()
        name = r.get("name","").strip()
        if not name:
            continue
        # Fuzzy match BMRS name against derived families (string), and also try full URLs
        fam_match, fam_score, _ = fuzzproc.extractOne(name, families, scorer=fuzz.token_sort_ratio)
        example = fam_to_example.get(fam_match, "")
        out_rows.append(dict(
            bmrs_code=code,
            bmrs_name=name,
            insights_family=fam_match,
            example_url=example,
            match_score=int(fam_score)
        ))
    df=pd.DataFrame(out_rows).sort_values(["bmrs_code","match_score"], ascending=[True, False])
    return df

# --------------------
# MkDocs export
# --------------------
def write_mkdocs_site(df_endpoints: pd.DataFrame):
    site_yml = {
        "site_name": f"{TITLE} — Data Dictionary",
        "theme": {"name":"material"},
        "nav": [
            {"Home": "index.md"},
            {"Data Dictionary": "data_dictionary.md"},
            {"How to use": "howto.md"},
        ],
        "markdown_extensions": ["tables","toc","admonition","attr_list","def_list"]
    }
    (DOCS_DIR/"index.md").write_text(f"# {TITLE}\n\nWelcome to the internal data dictionary generated from Elexon endpoints.\n", encoding="utf-8")
    (DOCS_DIR/"howto.md").write_text(textwrap.dedent("""
        # How to use this dictionary

        - **Data Dictionary**: lists discovered endpoints, grouped by classification.
        - Use the Streamlit app (`streamlit_app.py`) for interactive filtering, tag search, and re-pinging endpoints.
        - Update seed URLs or set `INSIGHTS_DOC_HINTS` environment variable to add more documentation sources before regenerating.
        - Set `INSIGHTS_API_KEY` to test authenticated endpoints.

        ## Re-generate
        ```bash
        python elexon_catalogue_plus.py
        ```

        ## Serve locally with MkDocs
        ```bash
        pip install mkdocs mkdocs-material
        mkdocs serve
        ```
    """).strip()+"\n", encoding="utf-8")

    # Build data_dictionary.md
    lines=["# Data Dictionary (Endpoints)\n"]
    if df_endpoints.empty:
        lines.append("_No endpoints discovered._\n")
    else:
        for family, grp in df_endpoints.groupby("cls"):
            lines.append(f"## {family.capitalize()}\n")
            lines.append("| URL | Source | Classification | HTTP Status |")
            lines.append("|---|---|---:|---:|")
            for _, r in grp.iterrows():
                lines.append(f"| `{r.url}` | {r.source or ''} | {r.cls} | {r.get('status') if not pd.isna(r.get('status')) else ''} |")
            lines.append("")
    (DOCS_DIR/"data_dictionary.md").write_text("\n".join(lines), encoding="utf-8")

    # mkdocs.yml at project root (inside OUT_DIR so we don't overwrite your repo root)
    with open(OUT_DIR/"mkdocs.yml","w",encoding="utf-8") as f:
        yaml.safe_dump(site_yml, f, sort_keys=False)

# --------------------
# Streamlit UI writer
# --------------------
def write_streamlit_app():
    code = textwrap.dedent(f"""
    import os
    import pandas as pd
    import requests
    import streamlit as st

    st.set_page_config(page_title="{TITLE} — Endpoint Explorer", layout="wide")

    st.title("{TITLE} — Endpoint Explorer")

    endpoints_fp = "{(OUT_DIR/'endpoints_catalogue.csv').as_posix()}"
    mapping_fp   = "{(OUT_DIR/'bmrs_to_insights_mapping.csv').as_posix()}"
    bmrs_fp      = "{(OUT_DIR/'bmrs_codes.csv').as_posix()}"

    @st.cache_data
    def load_df(fp):
        try:
            return pd.read_csv(fp)
        except Exception:
            return pd.DataFrame()

    df_end = load_df(endpoints_fp)
    df_map = load_df(mapping_fp)
    df_bmrs= load_df(bmrs_fp)

    st.subheader("Discovered Endpoints")
    if df_end.empty:
        st.info("No endpoints CSV found. Run the generator script first.")
    else:
        cls_sel = st.multiselect("Filter by classification", sorted(df_end["cls"].dropna().unique().tolist()), default=[])
        q = st.text_input("Search URL contains", "")
        v = df_end.copy()
        if cls_sel:
            v = v[v["cls"].isin(cls_sel)]
        if q:
            v = v[v["url"].str.contains(q, case=False, na=False)]
        st.dataframe(v, use_container_width=True, hide_index=True)

    st.subheader("BMRS Codes & Names")
    if df_bmrs.empty:
        st.info("No BMRS codes found. Run the generator script first.")
    else:
        st.dataframe(df_bmrs, use_container_width=True, hide_index=True)

    st.subheader("Auto Mapping (BMRS → Family → Example URL)")
    if df_map.empty:
        st.info("No mapping produced yet.")
    else:
        min_score = st.slider("Minimum fuzzy match score", 0, 100, 70, 1)
        mv = df_map[df_map["match_score"] >= min_score]
        st.dataframe(mv, use_container_width=True, hide_index=True)

    st.divider()
    st.caption("Tip: To re-ping endpoints, re-run the generator script. The app is read-only.")
    """).strip()
    (OUT_DIR/"streamlit_app.py").write_text(code, encoding="utf-8")

# --------------------
# Main pipeline
# --------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("1) Discover endpoints from GitHub org...")
    df_git = crawl_github_org(ORG)
    df_git.to_csv(OUT_DIR/"github_endpoint_hits.csv", index=False)

    print("2) Discover endpoints from doc seeds...")
    df_docs = scrape_doc_seeds(DOC_SEEDS + INSIGHTS_DOC_HINTS)

    print("3) Combine & dedupe endpoints...")
    df_all = pd.concat([df_git, df_docs], ignore_index=True) if not df_git.empty else df_docs
    if df_all.empty:
        df_all = pd.DataFrame(columns=["source","repo","url","cls"])
    df_all = df_all.drop_duplicates(subset=["url"]).reset_index(drop=True)

    print("4) Ping endpoints...")
    if not df_all.empty:
        df_all["status"] = df_all["url"].apply(lambda u: ping_endpoint(u, method=PING_METHOD))
    df_all.to_csv(OUT_DIR/"endpoints_catalogue.csv", index=False)

    print("5) Scrape BMRS code directory & expand...")
    bmrs_search_url = "https://bmrs.elexon.co.uk/api-documentation/search-results?query=all"
    df_bmrs = scrape_bmrs_codes(bmrs_search_url)
    df_bmrs = expand_bmrs_from_follow_links(df_bmrs, max_follow=25)
    df_bmrs = df_bmrs.drop_duplicates(subset=["code","name"]).sort_values(["code","name"])
    df_bmrs.to_csv(OUT_DIR/"bmrs_codes.csv", index=False)

    print("6) Build auto mapping BMRS → endpoint family...")
    df_mapping = auto_map_bmrs_to_endpoints(df_bmrs, df_all)
    # Keep best match per code
    if not df_mapping.empty:
        df_mapping = df_mapping.sort_values(["bmrs_code","match_score"], ascending=[True, False]) \
                               .groupby("bmrs_code", as_index=False).first()
    df_mapping.to_csv(OUT_DIR/"bmrs_to_insights_mapping.csv", index=False)

    print("7) MkDocs export...")
    write_mkdocs_site(df_all)

    print("8) Write Streamlit app...")
    write_streamlit_app()

    print("\n=== DONE ===")
    print(f"- Endpoints catalogue: {OUT_DIR/'endpoints_catalogue.csv'}")
    print(f"- BMRS codes:          {OUT_DIR/'bmrs_codes.csv'}")
    print(f"- Mapping sheet:       {OUT_DIR/'bmrs_to_insights_mapping.csv'}")
    print(f"- MkDocs site:         {OUT_DIR/'mkdocs.yml'} + {DOCS_DIR/'data_dictionary.md'}")
    print(f"- Streamlit app:       {OUT_DIR/'streamlit_app.py'}")
    print("\nRun MkDocs locally:")
    print(f"  cd {OUT_DIR} && mkdocs serve")
    print("\nRun Streamlit UI:")
    print(f"  streamlit run {(OUT_DIR/'streamlit_app.py').as_posix()}")
    print("\nEnv options:")
    print("  - GITHUB_TOKEN=... for higher GitHub rate limits")
    print("  - INSIGHTS_API_KEY=... to test authenticated endpoints")
    print("  - INSIGHTS_DOC_HINTS='https://...openapi.json,https://.../docs'")
    print("  - PING_METHOD=head|get")

if __name__=="__main__":
    main()