#!/usr/bin/env python3
"""
Cloud-Based BMRS Data Downloader
===============================
Downloads BMRS data directly to Google Cloud Storage
Designed for Cloud Run deployment
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter, Retry
from google.cloud import storage
# from google.cloud import scheduler_v1
# from google.cloud.scheduler_v1.types import Job

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
INSIGHTS_BASE = os.getenv('ELEXON_API_BASE', 'https://data.elexon.co.uk/bmrs/api/v1/')
ELEXON_API_KEY = os.getenv('ELEXON_API_KEY', None)  # Set your API key here or via env var
BUCKET_NAME = os.getenv('BUCKET_NAME', 'jibber-jabber-knowledge-bmrs-data')
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'jibber-jabber-knowledge')

# Dataset configuration
# NOTE: Endpoints may be deprecated. Update these as soon as new Elexon API documentation is available.
DATASETS = json.loads(os.getenv('ELEXON_DATASETS_JSON', json.dumps({
    "FUELINST": {
        "endpoint": "datasets/FUELINST",
        "default_params": {},
        "filename_hint": "FUELINST",
        "supports_csv": True,
    },
    "PN": {
        "endpoint": "datasets/PN",
        "default_params": {},
        "filename_hint": "PN",
        "supports_csv": True,
    },
    "MELNGC": {
        "endpoint": "datasets/MELNGC",
        "default_params": {},
        "filename_hint": "MELNGC",
        "supports_csv": True,
    },
    "DISBSAD": {
        "endpoint": "datasets/DISBSAD",
        "default_params": {},
        "filename_hint": "DISBSAD",
        "supports_csv": True,
    },
    "B1610": {
        "endpoint": "datasets/B1610/stream",
        "default_params": {},
        "filename_hint": "B1610_stream",
        "supports_csv": False,
    },
    "DCI": {
        "endpoint": "datasets/DCI/stream",
        "default_params": {},
        "filename_hint": "DCI_stream",
        "supports_csv": False,
    },
    "INTERCONNECTORS": {
        "endpoint": "generation/outturn/interconnectors",
        "default_params": {},
        "filename_hint": "INTERCONNECTORS",
        "supports_csv": True,
    },
    "RATES": {
        "endpoint": "balancing/dynamic/rates",
        "default_params": {},
        "filename_hint": "DYNAMIC_RATES",
        "supports_csv": True,
    },
    "BOALF": {
        "endpoint": "balancing/bid-offer-acceptances/all",
        "default_params": {},
        "filename_hint": "BOALF",
        "supports_csv": True,
    },
})))

def build_session(timeout=30, retries=5, backoff=0.6) -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"User-Agent": "Upowerenergy-ElexonDownloader/1.0"})
    if ELEXON_API_KEY:
        s.headers.update({"Authorization": f"Bearer {ELEXON_API_KEY}"})
    # Add any other required headers here
    return s

def fetch_dataset_stream(sess: requests.Session, code: str, endpoint: str, params: dict) -> List[dict]:
    url = requests.compat.urljoin(INSIGHTS_BASE, endpoint)
    r = sess.get(url, params=params)
    if r.status_code == 404:
        logger.error(f"Endpoint not found: {url} (404). This endpoint may be deprecated. Check Elexon API docs.")
        return []
    if r.status_code == 400:
        logger.error(f"Bad request for {url} (400). Params: {params}")
        return []
    try:
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return []
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data
    for k in ("records", "dataset", "datasets"):
        if k in data and isinstance(data[k], list):
            return data[k]
    return [data]

def fetch_dataset_csv(sess: requests.Session, code: str, endpoint: str, params: dict) -> bytes:
    url = requests.compat.urljoin(INSIGHTS_BASE, endpoint)
    q = dict(params or {})
    q["format"] = "csv"
    r = sess.get(url, params=q)
    if r.status_code == 404:
        logger.error(f"Endpoint not found: {url} (404). This endpoint may be deprecated. Check Elexon API docs.")
        return b''
    if r.status_code == 400:
        logger.error(f"Bad request for {url} (400). Params: {q}")
        return b''
    if r.status_code == 415:
        r.raise_for_status()
    r.raise_for_status()
    return r.content

def upload_to_gcs(data: bytes, blob_path: str):
    """Upload data to Google Cloud Storage"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_path)
    blob.upload_from_string(data)
    logger.info(f"Uploaded {blob_path} to {BUCKET_NAME}")

def download_dataset(
    code: str,
    date_from: Optional[str],
    date_to: Optional[str],
    want_csv: bool = True,
    extra_params: Dict[str, str] = None
) -> None:
    """Download a single dataset and upload to GCS"""
    
    sess = build_session()
    cfg = DATASETS.get(code)
    if not cfg:
        logger.warning(f"Unknown dataset code '{code}'")
        return

    params = dict(cfg.get("default_params", {}))
    params.update(extra_params or {})

    # Add date parameters based on endpoint type
    if "/stream" in cfg["endpoint"]:
        if date_from:
            params.setdefault("from", date_from)
        if date_to:
            params.setdefault("to", date_to)
    else:
        if date_from:
            params.setdefault("publishDateTimeFrom", date_from)
        if date_to:
            params.setdefault("publishDateTimeTo", date_to)

    hint = cfg.get("filename_hint", code)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    
    try:
        if want_csv and cfg.get("supports_csv", False):
            content = fetch_dataset_csv(sess, code, cfg["endpoint"], params)
            blob_path = f"bmrs/{hint}/{timestamp}.csv"
            upload_to_gcs(content, blob_path)
        else:
            records = fetch_dataset_stream(sess, code, cfg["endpoint"], params)
            content = "\n".join(json.dumps(r) for r in records)
            blob_path = f"bmrs/{hint}/{timestamp}.jsonl"
            upload_to_gcs(content.encode('utf-8'), blob_path)
            
        logger.info(f"Successfully processed {code}")
        
    except Exception as e:
        logger.error(f"Error processing {code}: {str(e)}")
        raise

def create_scheduler_job(
    schedule: str = "0 */3 * * *",  # Every 3 hours
    time_window_hours: int = 4
) -> None:
    """Create or update Cloud Scheduler job for regular data collection"""
    
    client = scheduler_v1.CloudSchedulerClient()
    parent = f"projects/{PROJECT_ID}/locations/us-central1"
    job_name = f"{parent}/jobs/bmrs-data-collection"
    
    # Calculate time window for each run
    time_window = {
        "from": "{{ date.now().isoformat() }}",
        "to": "{{ date.now().add(hours=time_window_hours).isoformat() }}"
    }
    
    # HTTP target for Cloud Run
    job = Job(
        name=job_name,
        schedule=schedule,
        http_target=scheduler_v1.HttpTarget(
            uri=f"https://{PROJECT_ID}.a.run.app/collect",
            http_method="POST",
            body=json.dumps(time_window).encode(),
        )
    )
    
    try:
        client.create_job(request={"parent": parent, "job": job})
        logger.info(f"Created scheduler job: {job_name}")
    except Exception as e:
        if "already exists" in str(e):
            client.update_job(request={"job": job})
            logger.info(f"Updated existing scheduler job: {job_name}")
        else:
            raise

import argparse

def run_local_download(date_from: str, date_to: str):
    """Function to run downloads from the command line."""
    logger.info(f"Starting local download from {date_from} to {date_to}")
    summary = {"success": [], "fail": []}
    for code in DATASETS.keys():
        try:
            logger.info(f"Downloading dataset: {code}")
            download_dataset(
                code=code,
                date_from=date_from,
                date_to=date_to,
                want_csv=True
            )
            summary["success"].append(code)
        except Exception as e:
            logger.error(f"Failed to download {code}: {e}")
            summary["fail"].append(code)
        time.sleep(0.5) # Be nice
    logger.info(f"Local download process finished. Success: {summary['success']}, Fail: {summary['fail']}")
    if len(summary["fail"]) == len(DATASETS):
        logger.error("All dataset downloads failed. Check API endpoints and authentication.")
        exit(1)
"""
==================== IMPORTANT ====================
Elexon BMRS API endpoints may have changed or been deprecated.
All endpoint URLs and authentication should be checked against the latest Elexon API documentation.
Update the INSIGHTS_BASE, DATASETS, and authentication as soon as new information is available.
==================================================
"""


def main(request):
    """Cloud Run entry point"""
    try:
        request_json = request.get_json() if request.is_json else {}
        date_from = request_json.get('from')
        date_to = request_json.get('to')
        
        # Initialize stats tracker
        # stats = CollectionStats(BUCKET_NAME) # Commented out due to undefined CollectionStats
        
        # Download each dataset
        for code in DATASETS.keys():
            try:
                records = download_dataset(
                    code=code,
                    date_from=date_from,
                    date_to=date_to,
                    want_csv=True
                )
                
                # Update statistics
                # if records:
                #     stats.update_stats(
                #         dataset=code,
                #         num_records=len(records) if isinstance(records, list) else 1,
                #         start_date=date_from,
                #         end_date=date_to
                #     )
                
            except Exception as dataset_error:
                logger.error(f"Error downloading {code}: {str(dataset_error)}")
                continue
                
            time.sleep(0.5)  # Be nice to the API
        
        # Get collection summary
        # summary = stats.get_summary()
        
        return {
            "status": "success",
            "message": "Data collection completed",
            # "statistics": summary
        }
        
    except Exception as e:
        logger.error(f"Error in main handler: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BMRS Data Downloader")
    parser.add_argument("--date-from", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--date-to", help="End date in YYYY-MM-DD format")
    args = parser.parse_args()

    to_date = args.date_to or datetime.utcnow().strftime("%Y-%m-%d")
    from_date = args.date_from or (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")

    run_local_download(date_from=from_date, date_to=to_date)
