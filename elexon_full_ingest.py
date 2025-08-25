from __future__ import annotations
import os, time, math, json, itertools, datetime as dt
from typing import Dict, Any, Iterable, List, Tuple, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from google.cloud import bigquery
import pandas as pd

INSIGHTS_API_KEY = os.getenv("BMRS_API_KEY_1")  # works for Insights too
INSIGHTS_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
BMRS_BASE = "https://api.bmreports.com"

# -------- Utilities --------

class ClientError(Exception): ...
class RedirectError(Exception): ...
class NotFoundError(Exception): ...

def daterange_chunks(start: dt.date, end: dt.date, days: int) -> Iterable[Tuple[dt.date, dt.date]]:
    cur = start
    while cur <= end:
        nxt = min(cur + dt.timedelta(days=days-1), end)
        yield cur, nxt
        cur = nxt + dt.timedelta(days=1)

def week_year_iter(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        iso = cur.isocalendar()
        yield iso.year, iso.week
        cur += dt.timedelta(days=7)

def ensure_bq_table(client: bigquery.Client, table_id: str, df_sample: pd.DataFrame):
    proj, dataset, table = table_id.split(".")
    ds_ref = bigquery.Dataset(f"{proj}.{dataset}")
    try:
        client.get_dataset(ds_ref)
    except Exception:
        client.create_dataset(ds_ref, exists_ok=True)
    try:
        client.get_table(table_id)
    except Exception:
        schema = []
        for col, dtype in df_sample.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                field_type = "INT64"
            elif pd.api.types.is_float_dtype(dtype):
                field_type = "FLOAT"
            elif pd.api.types.is_bool_dtype(dtype):
                field_type = "BOOL"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                field_type = "TIMESTAMP"
            else:
                field_type = "STRING"
            schema.append(bigquery.SchemaField(col, field_type))
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)

def upload_bq(client: bigquery.Client, table_id: str, df: pd.DataFrame):
    if df.empty:
        return
    ensure_bq_table(client, table_id, df.head(100).copy())
    rows = json.loads(df.to_json(orient="records", date_unit="s"))
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors: {errors}")

# -------- Insights (REST) --------

@retry(reraise=True, stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=60),
       retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ReadTimeout)))
def insights_get(path: str, params: Dict[str, Any]) -> httpx.Response:
    with httpx.Client(timeout=httpx.Timeout(30.0, connect=15.0)) as client:
        p = dict(params or {})
        if INSIGHTS_API_KEY:
            p["apiKey"] = INSIGHTS_API_KEY
        r = client.get(f"{INSIGHTS_BASE}{path}", params=p, follow_redirects=False)
        if r.status_code == 301:
            loc = r.headers.get("Location")
            if not loc:
                raise RedirectError("301 without Location")
            r = client.get(loc, timeout=httpx.Timeout(30.0, connect=15.0))
        if r.status_code == 404:
            raise NotFoundError(r.text)
        r.raise_for_status()
        return r

def fetch_insights_dataset(code: str, path: str, start: dt.date, end: dt.date,
                           chunk_days: int, static_params: Dict[str, Any], table_id: str):
    bq = bigquery.Client()
    frames: List[pd.DataFrame] = []
    for s, e in daterange_chunks(start, end, days=chunk_days):
        params = static_params.copy()
        params.setdefault("from", s.isoformat())
        params.setdefault("to", e.isoformat())
        params.setdefault("format", "json")
        resp = insights_get(path, params)
        js = resp.json()
        data = js.get("data", js)
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = [c.replace(" ", "_").lower() for c in df.columns]
            frames.append(df)
    if not frames:
        return
    df_all = pd.concat(frames, ignore_index=True)
    upload_bq(bq, table_id, df_all)

# -------- BMRS (legacy) --------

def throttle(sleep_seconds: float):
    time.sleep(sleep_seconds)

@retry(reraise=True, stop=stop_after_attempt(7), wait=wait_exponential(multiplier=1, min=2, max=120),
       retry=retry_if_exception_type((httpx.ConnectTimeout, httpx.ReadTimeout)))
def bmrs_get(path: str, params: Dict[str, Any]) -> httpx.Response:
    p = dict(params or {})
    if INSIGHTS_API_KEY:
        p["APIKey"] = INSIGHTS_API_KEY
    with httpx.Client(timeout=httpx.Timeout(45.0, connect=20.0)) as client:
        r = client.get(f"{BMRS_BASE}{path}", params=p)
        r.raise_for_status()
        return r

def fetch_B0620(start: dt.date, end: dt.date, table_id: str):
    bq = bigquery.Client()
    frames = []
    cur = start
    while cur <= end:
        for sp in range(1, 51):
            throttle(2.2)
            resp = bmrs_get("/BMRS/B0620/v1", {"SettlementDate": cur.isoformat(), "Period": sp, "ServiceType": "json"})
            js = resp.json()
            data = js.get("data", js)
            df = pd.DataFrame(data)
            if not df.empty:
                frames.append(df)
        cur += dt.timedelta(days=1)
    if frames:
        df_all = pd.concat(frames, ignore_index=True)
        upload_bq(bq, table_id, df_all)

def fetch_B0630(start: dt.date, end: dt.date, table_id: str):
    bq = bigquery.Client()
    frames = []
    for yr, wk in week_year_iter(start, end):
        throttle(2.2)
        resp = bmrs_get("/BMRS/B0630/v1", {"Year": yr, "Week": wk, "ServiceType": "json"})
        js = resp.json()
        df = pd.DataFrame(js.get("data", js))
        if not df.empty:
            frames.append(df)
    if frames:
        upload_bq(bq, table_id, pd.concat(frames, ignore_index=True))

# -------- Roadmap mapping (BMRS -> Insights) --------

ROADMAP_XLS = "https://www.elexon.co.uk/documents/insights-solution/roadmap/insights-solution-roadmap.xlsx"

def load_roadmap_mapping() -> pd.DataFrame:
    df = pd.read_excel(ROADMAP_XLS)
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

# -------- IRIS live consumer (skeleton) --------

"""
IRIS is Azure Service Bus. Your env already has:
INSIGHTS_TENANT_ID, INSIGHTS_CLIENT_ID, INSIGHTS_CLIENT_SECRET,
INSIGHTS_NAMESPACE, INSIGHTS_QUEUE_NAME, INSIGHTS_QUEUE_URL.

Use azure-identity + azure-servicebus to receive JSON payloads and
append to the corresponding BigQuery tables with the same schema.
Elexon’s page describes IRIS as near real-time push with automatic
outage recovery.  (See product page)
"""

# -------- Orchestration --------

def main():
    start_date = dt.date(2016, 1, 1)
    end_date = dt.date.today()

    insights_jobs = [
        ("DEMAND_OUTTURN", "/demand/outturn", 31, "jibber-jabber-knowledge.uk_energy_prod.demand_outturn"),
        ("SYSWARN", "/datasets/SYSWARN", 31, "jibber-jabber-knowledge.uk_energy_prod.system_warnings"),
        ("FREQ", "/datasets/FREQ", 7, "jibber-jabber-knowledge.uk_energy_prod.system_frequency"),
        ("FUELINST", "/datasets/FUELINST", 7, "jibber-jabber-knowledge.uk_energy_prod.generation_outturn")
    ]
    for code, path, chunk_days, table in insights_jobs:
        fetch_insights_dataset(code, path, start_date, end_date, chunk_days, {}, table)

    fetch_B0620(start_date, end_date, "jibber-jabber-knowledge.uk_energy_prod.B0620")
    fetch_B0630(start_date, end_date, "jibber-jabber-knowledge.uk_energy_prod.B0630")

if __name__ == "__main__":
    main()
