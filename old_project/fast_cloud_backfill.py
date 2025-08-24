#!/usr/bin/env python3
"""Fast Cloud Backfill for BMRS Data (Client Library Version)
-----------------------------------------------------------------
Uses google-cloud-storage client (no gsutil) to avoid interactive auth prompts.

Features:
    * Resume-safe (checks existing blobs by prefix listing cache)
    * Concurrency with ThreadPoolExecutor
    * Progress, ETA, failure tracking
    * Daily aggregation (one JSON per day / data_type)
    * Bid/Offer acceptances: 48 SP calls merged

Auth (Option B recommended):
    export GOOGLE_APPLICATION_CREDENTIALS=sa-key.json
Then run script.
"""
import os
import sys
import json
import time
import math
import queue
import signal
import subprocess
import threading
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
from google.cloud import storage
from datetime import datetime, timedelta, date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

API_BASE = 'https://data.elexon.co.uk/bmrs/api/v1'
DATA_TYPES = ['bid_offer_acceptances', 'generation_outturn', 'demand_outturn']
BUCKET_NAME = os.getenv('BMRS_BUCKET', 'jibber-jabber-knowledge-bmrs-data')
API_KEYS = []
API_ENV_FILE = 'api.env'
MAX_WORKERS = 12
RATE_SLEEP_ACCEPTANCES = 0.02
MAX_RETRIES = int(os.getenv('BMRS_MAX_RETRIES', '3'))
BACKOFF_BASE = float(os.getenv('BMRS_BACKOFF_BASE', '0.5'))  # seconds
ROOT_PREFIX = 'bmrs_data'

lock = Lock()
STATS = {
    'tasks_total': 0,
    'tasks_done': 0,
    'tasks_skipped': 0,
    'tasks_failed': 0,
    'acceptance_sp_requests': 0,
    'records_total': 0,
    'start_time': None
}
INTERRUPTED = False

# -------- Utility ---------

def load_api_keys():
    """Loads one or more API keys from the environment file."""
    if not Path(API_ENV_FILE).exists():
        return []
    
    keys = []
    with open(API_ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line.startswith('BMRS_API_KEY'):
                try:
                    key = line.split('=', 1)[1].strip().strip('\'"')
                    if key:
                        keys.append(key)
                except IndexError:
                    continue # Ignore lines without a value
    return keys

storage_client = None
bucket = None
LIST_CACHE = {}
LIST_CACHE_LOCK = Lock()
CREDS_ERROR_EMITTED = False

def init_storage():
    global storage_client, bucket, CREDS_ERROR_EMITTED
    if storage_client is not None:
        return True
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        return True
    except Exception as e:
        if not CREDS_ERROR_EMITTED:
            CREDS_ERROR_EMITTED = True
            print(f"❌ GCS credential init failed: {e}\n   Check GOOGLE_APPLICATION_CREDENTIALS path and permissions.")
        return False

def list_existing_prefix(prefix: str):
    """Return set of blob names (full path) under prefix (cached)."""
    with LIST_CACHE_LOCK:
        if prefix in LIST_CACHE:
            return LIST_CACHE[prefix]
    init_storage()
    if not init_storage():
        return set()
    blobs = storage_client.list_blobs(BUCKET_NAME, prefix=prefix)
    names = {b.name for b in blobs}
    with LIST_CACHE_LOCK:
        LIST_CACHE[prefix] = names
    return names

# -------- Download Logic ---------

def fetch_json(url: str):
    """Fetch JSON with retry + exponential backoff + jitter."""
    attempt = 0
    while attempt <= MAX_RETRIES:
        r = subprocess.run(['curl','-sS', '--max-time', '30', url], capture_output=True, text=True)
        success = (r.returncode == 0)
        data = None
        if success:
            try:
                data = json.loads(r.stdout)
            except Exception:
                success = False
        if success:
            return data
        attempt += 1
        if attempt > MAX_RETRIES:
            break
        backoff = BACKOFF_BASE * (2 ** (attempt - 1))
        jitter = random.uniform(0, BACKOFF_BASE)
        time.sleep(backoff + jitter)
    return None

def build_endpoint(data_type, settlement_period=None):
    if data_type == 'bid_offer_acceptances':
        ep = 'balancing/acceptances/all'
    elif data_type == 'generation_outturn':
        ep = 'generation/outturn/summary'
    elif data_type == 'demand_outturn':
        ep = 'demand/outturn/summary'
    else:
        return None
    return ep

def download_day(data_type: str, day: date, api_key: str):
    day_str = day.strftime('%Y-%m-%d')
    year = day.strftime('%Y')
    month = day.strftime('%m')
    cloud_rel = f'{ROOT_PREFIX}/{data_type}/{year}/{month}/{data_type}_{day_str}.json'

    # Existence check (list once per month prefix)
    month_prefix = f'{ROOT_PREFIX}/{data_type}/{year}/{month}/'
    existing = list_existing_prefix(month_prefix)
    if cloud_rel in existing:
        with lock:
            STATS['tasks_skipped'] += 1
            STATS['tasks_done'] += 1
        return 'skipped'

    endpoint = build_endpoint(data_type)
    if not endpoint:
        with lock:
            STATS['tasks_failed'] += 1
            STATS['tasks_done'] += 1
        return 'unknown-type'

    aggregated = []
    if data_type == 'bid_offer_acceptances':
        # 48 settlement periods
        for sp in range(1, 49):
            if INTERRUPTED: break
            url = f"{API_BASE}/{endpoint}?apikey={api_key}&settlementDate={day_str}&settlementPeriod={sp}"
            data = fetch_json(url)
            if data and 'data' in data:
                recs = data.get('data', [])
                for r_ in recs:
                    r_['settlement_period'] = sp
                aggregated.extend(recs)
                with lock:
                    STATS['acceptance_sp_requests'] += 1
            time.sleep(RATE_SLEEP_ACCEPTANCES)
    else:
        url = f"{API_BASE}/{endpoint}?apikey={api_key}&settlementDate={day_str}"
        data = fetch_json(url)
        if data and 'data' in data:
            aggregated = data.get('data', [])

    payload = {
        'date': day_str,
        'data_type': data_type,
        'record_count': len(aggregated),
        'download_timestamp': datetime.utcnow().isoformat()+'Z',
        'source': 'fast_cloud_backfill',
        'data': aggregated
    }
    # Upload via client
    if not init_storage():
        with lock:
            STATS['tasks_failed'] += 1
            STATS['tasks_done'] += 1
        return 'no-credentials'
    try:
        blob = bucket.blob(cloud_rel)
        blob.upload_from_string(json.dumps(payload, separators=(',', ':'), ensure_ascii=False))
    except Exception as e:
        with lock:
            STATS['tasks_failed'] += 1
            STATS['tasks_done'] += 1
        return f'upload-fail:{e.__class__.__name__}'

    with lock:
        STATS['tasks_done'] += 1
        STATS['records_total'] += len(aggregated)
    return 'ok'

# -------- Control / Scheduling ---------

def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def build_task_list(start_date: str, end_date: str):
    s = datetime.strptime(start_date, '%Y-%m-%d').date()
    e = datetime.strptime(end_date, '%Y-%m-%d').date()
    tasks = []
    for d in daterange(s, e):
        for t in DATA_TYPES:
            tasks.append((t, d))
    return tasks

# Graceful interrupt

def _handle_sigint(signum, frame):
    global INTERRUPTED
    INTERRUPTED = True
    print('\n⚠️  Interrupt received, finishing in-flight tasks...')

signal.signal(signal.SIGINT, _handle_sigint)

# -------- Main ---------

def main():
    global API_KEYS
    if len(sys.argv) < 3:
        print('Usage: python fast_cloud_backfill.py START_DATE END_DATE [--workers N] [--summary-every MINUTES] [--summary-min-tasks N] [--http-port PORT]')
        print('Example: python fast_cloud_backfill.py 2016-01-01 2016-12-31 --workers 12 --summary-every 15 --summary-min-tasks 500 --http-port 8080')
        return 1

    start_date, end_date = sys.argv[1], sys.argv[2]
    workers = MAX_WORKERS
    summary_interval_mins = None
    summary_min_tasks = 0
    http_port = None
    if '--workers' in sys.argv:
        idx = sys.argv.index('--workers')
        if idx+1 < len(sys.argv):
            workers = int(sys.argv[idx+1])
    if '--summary-every' in sys.argv:
        idx = sys.argv.index('--summary-every')
        if idx+1 < len(sys.argv):
            try:
                summary_interval_mins = float(sys.argv[idx+1])
            except ValueError:
                print('⚠️ Invalid --summary-every value (must be number of minutes)')
                return 3
    if '--summary-min-tasks' in sys.argv:
        idx = sys.argv.index('--summary-min-tasks')
        if idx+1 < len(sys.argv):
            try:
                summary_min_tasks = int(sys.argv[idx+1])
            except ValueError:
                print('⚠️ Invalid --summary-min-tasks value (must be integer)')
                return 4
    if '--http-port' in sys.argv:
        idx = sys.argv.index('--http-port')
        if idx+1 < len(sys.argv):
            try:
                http_port = int(sys.argv[idx+1])
            except ValueError:
                print('⚠️ Invalid --http-port value (must be integer)')
                return 5

    API_KEYS = load_api_keys()
    if not API_KEYS:
        print('❌ Missing BMRS_API_KEY in api.env')
        return 2

    task_list = build_task_list(start_date, end_date)
    STATS['tasks_total'] = len(task_list)
    STATS['start_time'] = time.time()

    print(f'🚀 Fast Backfill Start: {start_date} → {end_date}')
    print(f'🔑 Found {len(API_KEYS)} API key(s).')
    print(f'📦 Bucket: gs://{BUCKET_NAME}')
    print(f'🧩 Tasks (date × data_type): {STATS['tasks_total']}')
    print(f'⚙️  Workers: {workers}')

    last_report = 0

    # HTTP stats server (optional)
    stop_flag = threading.Event()
    stats_last_dump = {'done': 0}

    class StatsHandler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return  # quiet
        def _json(self, code, payload):
            body = json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header('Content-Type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.send_header('Cache-Control','no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            if self.path not in ('/stats','/healthz','/'):  # simple 404
                self._json(404, {'error':'not_found'})
                return
            with lock:
                done = STATS['tasks_done']
                total = STATS['tasks_total']
                elapsed = time.time() - STATS['start_time'] if STATS['start_time'] else 0
                rate = done/elapsed if elapsed>0 else 0
                remaining = max(0,total-done)
                eta_sec = remaining/rate if rate>0 else None
                payload = {
                    'tasks_done': done,
                    'tasks_total': total,
                    'skipped': STATS['tasks_skipped'],
                    'failed': STATS['tasks_failed'],
                    'records_total': STATS['records_total'],
                    'acceptance_sp_requests': STATS['acceptance_sp_requests'],
                    'start_time': STATS['start_time'],
                    'elapsed_sec': elapsed,
                    'rate_tasks_per_sec': rate,
                    'eta_sec': eta_sec,
                    'eta_human': f"{eta_sec/3600:.2f}h" if eta_sec else None,
                    'percent': round((done/total)*100,2) if total else 0,
                    'interval_summary_enabled': bool(summary_interval_mins)
                }
            self._json(200, payload)

    def http_server_thread(port:int):
        try:
            server = HTTPServer(('0.0.0.0', port), StatsHandler)
            while not stop_flag.is_set():
                server.timeout = 1
                server.handle_request()
        except Exception:
            pass
    def summary_worker():
        if not summary_interval_mins:
            return
        interval = max(1.0, summary_interval_mins) * 60.0
        last_tasks = 0
        while not stop_flag.wait(interval):
            with lock:
                done_now = STATS['tasks_done']
            if done_now - last_tasks < summary_min_tasks:
                continue  # throttle based on task delta
            last_tasks = done_now
            try:
                subprocess.run([sys.executable, 'generate_collection_summary.py'], timeout=300, check=False)
            except Exception:
                pass
    if summary_interval_mins:
        print(f'🧮 Periodic summaries every {summary_interval_mins} minute(s) enabled')
        threading.Thread(target=summary_worker, daemon=True).start()
    if http_port:
        print(f'🌐 HTTP stats endpoint on :{http_port} (paths: /stats, /healthz)')
        threading.Thread(target=http_server_thread, args=(http_port,), daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Assign a key to each task, cycling through the available keys
        future_map = {
            executor.submit(download_day, t, d, API_KEYS[i % len(API_KEYS)]): (t, d) 
            for i, (t, d) in enumerate(task_list)
        }
        for fut in as_completed(future_map):
            t, d = future_map[fut]
            status = 'ERR'
            try:
                status = fut.result()
            except Exception as e:
                status = f'exception: {e}'
                with lock:
                    STATS['tasks_failed'] += 1
                    STATS['tasks_done'] += 1
            now = time.time()
            if now - last_report > 10:  # report every ~10s
                with lock:
                    done = STATS['tasks_done']
                    total = STATS['tasks_total']
                    elapsed = now - STATS['start_time']
                    rate = done/elapsed if elapsed>0 else 0
                    remaining = total - done
                    eta = remaining / rate if rate>0 else float('inf')
                    print(f"⏱️  {done}/{total} ({done/total*100:.1f}%) | fails {STATS['tasks_failed']} | skips {STATS['tasks_skipped']} | records {STATS['records_total']:,} | ETA {eta/60:.1f}m")
                last_report = now
            if INTERRUPTED:
                break

    if summary_interval_mins:
        try:
            subprocess.run([sys.executable, 'generate_collection_summary.py'], timeout=300, check=False)
        except Exception:
            pass
    stop_flag.set()

    elapsed = time.time() - STATS['start_time']
    print('\n🏁 Backfill Complete')
    print(f"✅ Done: {STATS['tasks_done']}  Skipped: {STATS['tasks_skipped']}  Failed: {STATS['tasks_failed']}")
    print(f"📊 Records: {STATS['records_total']:,}")
    print(f"⏱️ Duration: {elapsed/60:.1f} minutes")
    if STATS['tasks_failed']:
        print('⚠️ Re-run for failed days; existing objects skipped automatically.')

    return 0

if __name__ == '__main__':
    sys.exit(main())
