#!/usr/bin/env python3
"""
download_all_bmrs_endpoints.py
Downloads all BMRS endpoints for all dates from 2016-01-01 to today using endpoints.csv.
Saves results ONLY to Google Cloud Storage (no local saving).
Reports progress every 15 minutes: files processed, files remaining, GB processed, GB outstanding, elapsed time, and ETA.
"""
import os
import sys
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
from datetime import datetime, timedelta
from google.cloud import storage
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import List

# --- CONFIG ---
API_ENV_FILE = 'api.env'
ENDPOINTS_CSV = 'endpoints.csv'
BUCKET_NAME = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
ROOT_PREFIX = 'bmrs_data_all'
START_DATE = datetime(2016, 1, 1)
END_DATE = datetime.now()
PROGRESS_INTERVAL = 15 * 60  # seconds

# --- UTILS ---
def load_api_key():
    if not Path(API_ENV_FILE).exists():
        return None
    with open(API_ENV_FILE) as f:
        for line in f:
            if line.startswith('BMRS_API_KEY='):
                return line.split('=',1)[1].strip().strip('"\'')
    return None

def init_storage():
    return storage.Client()

def list_existing_blobs(client, prefix):
    bucket = client.bucket(BUCKET_NAME)
    return {b.name for b in bucket.list_blobs(prefix=prefix)}

# --- PARAM SANITISATION ---
def sanitise_params(params):
    """Clean up ambiguous or invalid sample params from endpoints.csv.
    - ServiceType like 'csv/xml' -> 'csv'
    - Period of '*' or 'ALL' removed (API may reject wildcard)
    - Strip whitespace
    """
    p = {}
    for k, v in params.items():
        if isinstance(v, str):
            v = v.strip()
        if k.lower() == 'servicetype' and isinstance(v, str) and '/' in v:
            v = v.split('/')[0].lower()
        if k.lower() == 'period' and (v in ('*', 'ALL', 'all')):
            # Remove wildcard period; downstream logic may supply specific periods if required
            v = ''
        p[k] = v
    return p

# --- Parallel Download Worker ---
def download_worker(args):
    eid, version, params, day, rel_path, url, api_key, client, max_retries, session, request_timeout = args
    print(f"Downloading: {url} -> {rel_path}")
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            r = session.get(url, timeout=request_timeout)
            latency = time.time() - t0
            if r.status_code == 200:
                payload = {
                    'endpoint': eid,
                    'date': day.strftime('%Y-%m-%d'),
                    'url': url,
                    'status': r.status_code,
                    'latency_s': round(latency, 3),
                    'download_timestamp': datetime.utcnow().isoformat()+'Z',
                    'data': r.text
                }
                sz = upload_json_to_gcs(client, rel_path, payload)
                return (rel_path, True, sz, None)
            else:
                payload = {
                    'endpoint': eid,
                    'date': day.strftime('%Y-%m-%d'),
                    'url': url,
                    'status': r.status_code,
                    'error': r.text,
                    'latency_s': round(latency, 3),
                    'download_timestamp': datetime.utcnow().isoformat()+'Z'
                }
                upload_json_to_gcs(client, rel_path, payload)
                return (rel_path, False, 0, r.text)
        except Exception as e:
            if attempt == max_retries - 1:
                return (rel_path, False, 0, str(e))
            time.sleep(2 ** attempt)  # Exponential backoff
def upload_json_to_gcs(client, rel_path, payload):
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(rel_path)
    blob.upload_from_string(json.dumps(payload, separators=(',', ':'), ensure_ascii=False))
    return blob.size if hasattr(blob, 'size') else len(json.dumps(payload))

def daterange(start, end):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def build_param_dict(df, endpoint_id):
    # Get all request params for this endpoint
    params = {}
    for _, row in df[(df['id']==endpoint_id) & (df['direction']=='request')].iterrows():
        params[row['Field Name']] = row['Sample Data'] if pd.notnull(row['Sample Data']) else ''
    return sanitise_params(params)

def build_url(endpoint_id, version, params, api_key):
    base = f'https://api.bmreports.com/BMRS/{endpoint_id}/v{version}'
    params = params.copy()
    params['APIKey'] = api_key
    if 'ServiceType' in params and not params['ServiceType']:
        params['ServiceType'] = 'csv'  # default
    q = '&'.join(f"{k}={v}" for k,v in params.items() if v)
    return f"{base}?{q}"


def parse_periods(spec: str) -> List[int]:
    """Parse env var BMRS_ITERATE_PERIODS like '1-48' or '1-50' or '1,2,3,10-12'.
    Returns sorted unique ints."""
    out = set()
    if not spec:
        return []
    for token in spec.split(','):
        token = token.strip()
        if not token:
            continue
        if '-' in token:
            try:
                a,b = token.split('-',1)
                a=int(a); b=int(b)
                if a<=b and a>0:
                    for p in range(a,b+1):
                        out.add(p)
            except ValueError:
                continue
        else:
            try:
                out.add(int(token))
            except ValueError:
                continue
    return sorted(out)


def main():
    global START_DATE, END_DATE
    # --- TEST PATCH REMOVED: Now respects only shell environment variables ---
    # Environment overrides for date window (quick tests)
    sd_env = os.getenv('BMRS_START_DATE')
    ed_env = os.getenv('BMRS_END_DATE')
    def parse_dt(s):
        if not s:
            return None
        for fmt in ('%Y-%m-%d','%Y/%m/%d'):
            try:
                return datetime.strptime(s, fmt)
            except Exception:
                continue
        return None
    sd_parsed = parse_dt(sd_env)
    ed_parsed = parse_dt(ed_env)
    if sd_parsed:
        START_DATE = sd_parsed
    if ed_parsed:
        END_DATE = ed_parsed
    api_key = load_api_key()
    if not api_key:
        print('❌ Missing BMRS_API_KEY in api.env')
        sys.exit(1)
    df = pd.read_csv(ENDPOINTS_CSV)
    endpoint_ids = sorted(df['id'].unique())
    endpoint_filter_env = os.getenv('BMRS_ENDPOINT_FILTER')
    if endpoint_filter_env:
        allowed = {e.strip() for e in endpoint_filter_env.split(',') if e.strip()}
        endpoint_ids = [e for e in endpoint_ids if e in allowed]
        print(f"Applying endpoint filter -> {endpoint_ids}")
    client = init_storage()
    total_files = 0
    # --- Tuning ---
    # Allow override via env
    try:
        max_workers = int(os.getenv('BMRS_MAX_WORKERS', '1'))
    except ValueError:
        max_workers = 1
    if max_workers < 1:
        max_workers = 1
    dry_run_cap_env = os.getenv('BMRS_DRY_RUN_MAX_TASKS')
    dry_run_cap = None
    if dry_run_cap_env:
        try:
            dry_run_cap = int(dry_run_cap_env)
        except ValueError:
            dry_run_cap = None
    iterate_periods_spec = os.getenv('BMRS_ITERATE_PERIODS')
    period_list = parse_periods(iterate_periods_spec) if iterate_periods_spec else []
    if period_list:
        print(f"Period iteration active over {len(period_list)} periods (sample first 5: {period_list[:5]})")
    # Request timeout & retries overrides
    try:
        request_timeout = int(os.getenv('BMRS_TIMEOUT', '180'))
    except ValueError:
        request_timeout = 180
    try:
        max_retries = int(os.getenv('BMRS_RETRIES', '5'))
    except ValueError:
        max_retries = 5
    print(f"Configured max_workers={max_workers} dry_run_cap={dry_run_cap} timeout={request_timeout}s retries={max_retries} endpoint_filter={endpoint_filter_env} date_window={START_DATE.date()}→{END_DATE.date()}")
    # Endpoints for which we should explicitly keep/use Period=* (some endpoints accept wildcard for all 48 periods and may hang if omitted)
    force_period_star = {e.strip() for e in os.getenv('BMRS_PERIOD_STAR_ENDPOINTS', 'B0610,B0620').split(',') if e.strip()}
    period_iterate_endpoints = {e.strip() for e in os.getenv('BMRS_PERIOD_ITERATE_ENDPOINTS', '').split(',') if e.strip()}
    # Optional cap of days for daily endpoints for debugging
    try:
        limit_days = int(os.getenv('BMRS_LIMIT_DAYS','0'))
    except ValueError:
        limit_days = 0
    # max_retries already possibly overridden
    lock = threading.Lock()
    # Shared HTTP session with retry adapter for connection reuse & transient error resilience
    session = requests.Session()
    retry_cfg = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504], raise_on_status=False)
    adapter = HTTPAdapter(max_retries=retry_cfg, pool_connections=10, pool_maxsize=10)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    # --- Monthly download support ---
    endpoints_monthly = set([
        'B1790', # Financial Expenses and Income For Balancing
        'B0630', # Week-Ahead Total Load Forecast per Bidding Zone (by week, but can be grouped by month)
        'B0640', # Month-Ahead Total Load Forecast Per Bidding Zone
        'B0650', # Year Ahead Total Load Forecast per Bidding Zone
        'B0810', # Year Ahead Forecast Margin
        'B1410', # Installed Generation Capacity Aggregated
        'B1420', # Installed Generation Capacity per Unit
        'B0910', # Expansion and Dismantling Projects
        'B1330', # Congestion Management Measures Costs of Congestion Management
    ])
    # --- Range-based download support (can be fetched monthly) ---
    endpoints_range = set([
        'TEMP', # Temperature Data
        'SYSWARN', # System Warnings
        'DEVINDOD', # Daily Energy Volume Data
        'NONBM', # Non BM STOR Instructed Volume Data
        'FUELHH', # Half Hourly Outturn Generation by Fuel Type
        'MELIMBALNGC', # Forecast Day and Day Ahead Margin and Imbalance Data
        'FORDAYDEM', # Forecast Day and Day Ahead Demand Data
        'SYSDEM', # System Demand
        'WINDFORFUELHH', # Wind Generation Forecast and Out-turn Data
        'LOLPDRM', # Loss of Load Probability and De-rated Margin
        'DERSYSDATA', # Derived System Wide Data
        'ROLSYSDEM', # Rolling System Demand
        'FREQ', # Rolling System Frequency
        'MID', # Market Index Data
    ])

    # --- Build all download tasks ---
    print("Building download tasks...")
    
    tasks = []
    processed_files = 0
    processed_bytes = 0
    start_time = time.time()
    last_report = start_time

    skip_blob_list = bool(os.getenv('BMRS_SKIP_BLOB_LIST')) and dry_run_cap is not None
    if skip_blob_list:
        print("Skipping existing blob listing due to BMRS_SKIP_BLOB_LIST for dry run.")
        existing_blobs = set()
    else:
        print("Listing existing blobs in GCS (this may take a while)...")
        existing_blobs = list_existing_blobs(client, ROOT_PREFIX)
    
    if period_iterate_endpoints:
        print(f"Endpoints set for per-period iteration: {sorted(period_iterate_endpoints)}")
    for eid in endpoint_ids:
        version = str(df[df['id']==eid]['version'].iloc[0])
        params = build_param_dict(df, eid)
        # If explicitly iterating periods, blank out Period so iteration logic triggers
        if eid in period_iterate_endpoints and 'Period' in params:
            params['Period'] = ''
        # Reapply Period='*' if required for this endpoint (unless iterating)
        if eid in force_period_star and eid not in period_iterate_endpoints and 'Period' in params and not params['Period']:
            params['Period'] = '*'
        # Special handling: if B0610 and iteration requested, clear Period so iteration loop engages
        if eid == 'B0610' and period_list and 'Period' in params:
            params['Period'] = ''
        
        # Monthly batching for endpoints with Year/Month params
        if eid in endpoints_monthly:
            for year in range(START_DATE.year, END_DATE.year + 1):
                for month in range(1, 13):
                    if year == END_DATE.year and month > END_DATE.month:
                        break
                    
                    rel_path = f"{ROOT_PREFIX}/{eid}/v{version}/{year}/{month:02d}.json"
                    if rel_path in existing_blobs:
                        continue

                    params_month = params.copy()
                    params_month['Year'] = str(year)
                    if 'Month' in params_month:
                         params_month['Month'] = datetime(year, month, 1).strftime('%b') # MMM format like 'Jan'
                    
                    # For weekly data, we can just use the year and download the whole year.
                    if 'Week' in params_month:
                        del params_month['Week']

                    url = build_url(eid, version, params_month, api_key)
                    tasks.append((eid, version, params_month, f"{year}-{month:02d}", rel_path, url, api_key, client, max_retries, session, request_timeout))
        # Monthly batching for endpoints with FromDate/ToDate or FromDateTime/ToDateTime params
        elif eid in endpoints_range:
            cur = START_DATE
            while cur <= END_DATE:
                month_start = cur.replace(day=1)
                next_month_start = (month_start + timedelta(days=32)).replace(day=1)
                month_end = next_month_start - timedelta(days=1)
                
                if month_end > END_DATE:
                    month_end = END_DATE

                rel_path = f"{ROOT_PREFIX}/{eid}/v{version}/{month_start.strftime('%Y/%m')}.json"
                if rel_path in existing_blobs:
                    cur = next_month_start
                    continue

                params_month = params.copy()
                
                date_format = '%Y-%m-%d'
                datetime_format = '%Y-%m-%d %H:%M:%S'

                if 'FromDateTime' in params_month:
                    params_month['FromDateTime'] = month_start.strftime(datetime_format)
                    params_month['ToDateTime'] = month_end.strftime(datetime_format)
                elif 'FromDate' in params_month:
                    params_month['FromDate'] = month_start.strftime(date_format)
                    params_month['ToDate'] = month_end.strftime(date_format)

                url = build_url(eid, version, params_month, api_key)
                tasks.append((eid, version, params_month, month_start.strftime('%Y-%m'), rel_path, url, api_key, client, max_retries, session, request_timeout))
                cur = next_month_start
        # Daily downloads for the rest
        else:
            day_counter = 0
            for day in daterange(START_DATE, END_DATE):
                day_counter += 1
                if limit_days and day_counter > limit_days:
                    break
                base_rel = f"{ROOT_PREFIX}/{eid}/v{version}/{day.strftime('%Y/%m/%d')}"
                params_day = params.copy()
                if 'SettlementDate' in params_day:
                    params_day['SettlementDate'] = day.strftime('%Y-%m-%d')
                # If Period iteration requested & endpoint has Period param blank/unspecified
                if period_list and 'Period' in params_day and (not str(params_day['Period']).strip()):
                    for p in period_list:
                        params_period = params_day.copy()
                        params_period['Period'] = str(p)
                        rel_path = f"{base_rel}/period_{p:02d}.json"
                        if rel_path in existing_blobs:
                            continue
                        url = build_url(eid, version, params_period, api_key)
                        tasks.append((eid, version, params_period, day, rel_path, url, api_key, client, max_retries, session, request_timeout))
                        if dry_run_cap is not None and os.getenv('BMRS_FAST_DRY_RUN') and len(tasks) >= dry_run_cap:
                            break
                    if dry_run_cap is not None and os.getenv('BMRS_FAST_DRY_RUN') and len(tasks) >= dry_run_cap:
                        break
                else:
                    rel_path = f"{base_rel}.json"
                    if rel_path in existing_blobs:
                        continue
                    url = build_url(eid, version, params_day, api_key)
                    tasks.append((eid, version, params_day, day, rel_path, url, api_key, client, max_retries, session, request_timeout))
                    if dry_run_cap is not None and os.getenv('BMRS_FAST_DRY_RUN') and len(tasks) >= dry_run_cap:
                        break
            if dry_run_cap is not None and os.getenv('BMRS_FAST_DRY_RUN') and len(tasks) >= dry_run_cap:
                # Stop iterating further endpoints (since filtered list usually small)
                break

    # Apply dry run cap if set
    if dry_run_cap is not None and len(tasks) > dry_run_cap:
        tasks = tasks[:dry_run_cap]
        print(f"Dry run active: truncated tasks to first {len(tasks)}")
    total_files = len(tasks)
    if os.getenv('BMRS_DEBUG') and tasks:
        print("Debug: showing up to first 5 task URLs:")
        for t in tasks[:5]:
            print(f"  {t[4]} -> {t[5]}")
    if total_files == 0:
        print("No new files to download.")
        return
        
    print(f"Starting parallel download of {total_files} files with {max_workers} workers...")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_worker, task): task for task in tasks}
        for i, future in enumerate(as_completed(futures)):
            rel_path, success, sz, err = future.result()
            with lock:
                processed_files += 1
                if success:
                    processed_bytes += sz
                if not success:
                    print(f"[ERROR] {rel_path}: {err}")
                    if err and ("rate limit" in str(err).lower() or "quota" in str(err).lower()):
                        print("[RATE LIMIT/QUOTA WARNING] Consider reducing max_workers or checking your API quotas.")
                
                now = time.time()
                if (now - last_report > PROGRESS_INTERVAL) or processed_files == total_files or (processed_files % 200 == 0):
                    elapsed = now - start_time
                    rate = processed_files / elapsed if elapsed > 0 else 0
                    eta = (total_files - processed_files) / rate if rate > 0 else float('inf')
                    print(f"[PROGRESS] {processed_files}/{total_files} files | {processed_bytes/1e9:.2f} GB | Rate: {rate:.2f} files/s | ETA: {eta/3600:.2f}h | Elapsed: {elapsed/3600:.2f}h")
                    last_report = now
    
    # Final report
    elapsed = time.time() - start_time
    print(f"[COMPLETE] {processed_files}/{total_files} files | {processed_bytes/1e9:.2f} GB | Elapsed: {elapsed/3600:.2f}h")

# --- AUDIT FUNCTION ---
def audit_download_and_bigquery():
    """
    Audit which datasets from endpoints.csv are present in GCS and BigQuery.
    Prints a summary table.
    """
    import os
    import pandas as pd
    from google.cloud import storage, bigquery

    # Load endpoints
    df = pd.read_csv('endpoints.csv')
    dataset_names = sorted(set(df['name'].dropna()))

    # GCS setup
    bucket_name = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
    prefix = 'bmrs_data_all/'
    storage_client = storage.Client()
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except Exception as e:
        print(f"❌ Could not access GCS bucket: {e}")
        return

    # BigQuery setup
    bq_client = bigquery.Client()
    bq_dataset = os.getenv('BMRS_BQ_DATASET', 'bmrs_data')
    try:
        tables = list(bq_client.list_tables(bq_dataset))
        bq_table_names = set([t.table_id for t in tables])
    except Exception as e:
        print(f"❌ Could not access BigQuery dataset: {e}")
        bq_table_names = set()

    print(f"\n{'Dataset':30} | {'GCS':8} | {'BigQuery':8}")
    print('-'*55)
    for name in dataset_names:
        # Check GCS
        gcs_blobs = list(bucket.list_blobs(prefix=f"{prefix}{name}"))
        gcs_status = '✅' if gcs_blobs else '❌'
        # Check BigQuery
        bq_status = '✅' if name in bq_table_names else '❌'
        print(f"{name:30} | {gcs_status:^8} | {bq_status:^8}")

if __name__ == "__main__":
    import sys
    if '--audit' in sys.argv:
        audit_download_and_bigquery()
    else:
        main()
