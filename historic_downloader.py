import os
import time
import json
import datetime as dt
from typing import Dict, Any
import httpx
from google.cloud import storage

INSIGHTS_API_KEY = os.getenv("BMRS_API_KEY_1")
BMRS_BASE = "https://api.bmreports.com"
GCS_BUCKET = os.getenv("GCS_BUCKET") or "your-bucket-name"  # Set your bucket name

# -------- Utilities --------
def throttle(sleep_seconds: float):
    time.sleep(sleep_seconds)

def daterange(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)

def week_year_iter(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        iso = cur.isocalendar()
        yield iso.year, iso.week
        cur += dt.timedelta(days=7)

# -------- BMRS (legacy) download to GCS --------
def bmrs_get(path: str, params: Dict[str, Any]) -> httpx.Response:
    p = dict(params or {})
    if INSIGHTS_API_KEY:
        p["APIKey"] = INSIGHTS_API_KEY
    with httpx.Client(timeout=httpx.Timeout(45.0, connect=20.0)) as client:
        r = client.get(f"{BMRS_BASE}{path}", params=p)
        r.raise_for_status()
        return r

def upload_to_gcs(blob_name: str, data: dict):
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(data), content_type="application/json")
    print(f"Uploaded to gs://{GCS_BUCKET}/{blob_name}")

def download_B0620_to_gcs(start: dt.date, end: dt.date):
    cur = start
    while cur <= end:
        for sp in range(1, 51):
            throttle(2.2)
            resp = bmrs_get("/BMRS/B0620/v1", {"SettlementDate": cur.isoformat(), "Period": sp, "ServiceType": "json"})
            js = resp.json()
            blob_name = f"bmrs/B0620/{cur.isoformat()}_P{sp:02d}.json"
            upload_to_gcs(blob_name, js)
        cur += dt.timedelta(days=1)

def download_B0630_to_gcs(start: dt.date, end: dt.date):
    for yr, wk in week_year_iter(start, end):
        throttle(2.2)
        resp = bmrs_get("/BMRS/B0630/v1", {"Year": yr, "Week": wk, "ServiceType": "json"})
        js = resp.json()
        blob_name = f"bmrs/B0630/{yr}_W{wk:02d}.json"
        upload_to_gcs(blob_name, js)

# -------- Orchestration --------
def main():
    start_date = dt.date(2016, 1, 1)
    end_date = dt.date(2016, 1, 7)  # Test week
    download_B0620_to_gcs(start_date, end_date)
    download_B0630_to_gcs(start_date, end_date)

if __name__ == "__main__":
    main()
