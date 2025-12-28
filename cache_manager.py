"""
Google Sheets API Caching Manager
Implements 4-layer caching strategy:
1. Worksheet object caching (avoid re-opening sheets)
2. Batch operations queue (reduce API calls)
3. Service account rotation (5x quota increase)
4. Redis caching for data reads (instant lookups)
"""

import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account as google_service_account
from googleapiclient.discovery import build
import threading
import time
from datetime import datetime, timedelta
from collections import defaultdict
import json
import os

# Redis imports (optional, fallback to dict if unavailable)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available, using in-memory cache (restart will clear)")

class CacheManager:
    """Thread-safe caching manager for Google Sheets API"""

    def __init__(self, credentials_files=None, redis_host='localhost', redis_port=6379):
        self.lock = threading.Lock()

        # Layer 1: Worksheet object cache
        self.worksheet_cache = {}  # key: (sheet_id, worksheet_name), value: (worksheet_obj, timestamp)
        self.worksheet_cache_ttl = 300  # 5 minutes

        # Layer 2: Batch operations queue
        self.batch_queue = defaultdict(list)  # key: (sheet_id, worksheet_name), value: [(range, values, timestamp)]
        self.batch_flush_interval = 60  # Flush every 60 seconds
        self.batch_max_size = 50  # Or when 50 operations queued
        self.last_flush = defaultdict(lambda: time.time())

        # Layer 3: Service account rotation
        if credentials_files is None:
            # Default: try to find multiple credential files
            credentials_files = [
                'inner-cinema-credentials.json',
                'inner-cinema-credentials-2.json',
                'inner-cinema-credentials-3.json',
                'inner-cinema-credentials-4.json',
                'inner-cinema-credentials-5.json'
            ]
        self.credentials_files = [f for f in credentials_files if os.path.exists(f)]
        if not self.credentials_files:
            raise FileNotFoundError("No credential files found")

        self.current_account_idx = 0
        self.account_request_counts = [0] * len(self.credentials_files)
        self.account_reset_times = [time.time()] * len(self.credentials_files)
        self.requests_per_minute = 55  # Conservative (API limit is 60)

        # Initialize first client
        self.client = self._get_client(0)

        # Initialize FAST API v4 service for writes (255x faster!)
        self.fast_services = []
        for cred_file in self.credentials_files:
            try:
                scopes = ['https://www.googleapis.com/auth/spreadsheets']
                creds = google_service_account.Credentials.from_service_account_file(cred_file, scopes=scopes)
                service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
                self.fast_services.append(service)
            except Exception as e:
                print(f"⚠️  Failed to init fast API for {cred_file}: {e}")

        if self.fast_services:
            print(f"⚡ Fast API v4 enabled: {len(self.fast_services)} services (255x faster writes!)")
        else:
            print("⚠️  Fast API v4 not available, falling back to gspread")

        # Layer 4: Redis cache for data reads
        self.redis_client = None
        self.redis_ttl = 60  # 1 minute for data reads
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
                self.redis_client.ping()
                print(f"✅ Redis connected: {redis_host}:{redis_port}")
            except:
                print(f"⚠️  Redis connection failed, using in-memory cache")
                self.redis_client = None

        # In-memory fallback for data cache
        self.memory_cache = {}  # key: cache_key, value: (data, timestamp)

        # Start background batch flusher
        self.flusher_thread = threading.Thread(target=self._batch_flusher, daemon=True)
        self.flusher_thread.start()

        print(f"✅ CacheManager initialized: {len(self.credentials_files)} accounts, Redis={'enabled' if self.redis_client else 'disabled'}")

    def _get_client(self, account_idx):
        """Get gspread client for specific service account"""
        cred_file = self.credentials_files[account_idx]
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_file, scope)
        return gspread.authorize(creds)

    def _rotate_account(self):
        """Rotate to next service account if current one near rate limit"""
        with self.lock:
            current_time = time.time()
            current_idx = self.current_account_idx

            # Check if current account needs cooldown
            time_since_reset = current_time - self.account_reset_times[current_idx]
            if time_since_reset < 60 and self.account_request_counts[current_idx] >= self.requests_per_minute:
                # Current account at limit, try to rotate
                for i in range(1, len(self.credentials_files)):
                    next_idx = (current_idx + i) % len(self.credentials_files)
                    next_reset_time = self.account_reset_times[next_idx]
                    next_count = self.account_request_counts[next_idx]

                    # Reset counter if minute passed
                    if current_time - next_reset_time >= 60:
                        self.account_request_counts[next_idx] = 0
                        self.account_reset_times[next_idx] = current_time
                        next_count = 0

                    # Use this account if available
                    if next_count < self.requests_per_minute:
                        print(f"🔄 Rotating to service account {next_idx + 1}/{len(self.credentials_files)}")
                        self.current_account_idx = next_idx
                        self.client = self._get_client(next_idx)
                        return

                # All accounts at limit, wait and reset current
                wait_time = 60 - time_since_reset + 1
                print(f"⏳ All accounts at limit, waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
                self.account_request_counts[current_idx] = 0
                self.account_reset_times[current_idx] = time.time()

            # Reset counter if minute passed
            if time_since_reset >= 60:
                self.account_request_counts[current_idx] = 0
                self.account_reset_times[current_idx] = current_time

    def _increment_request_count(self):
        """Track API request and rotate if needed"""
        with self.lock:
            self.account_request_counts[self.current_account_idx] += 1
        self._rotate_account()

    def get_worksheet(self, sheet_id, worksheet_name, use_cache=True):
        """
        Get worksheet object with caching (Layer 1)
        ⚠️ DEPRECATED: This is SLOW (60s+) and can HANG due to gspread loading entire spreadsheet.
        Use direct API v4 via fast_sheets_helper.py instead for 255x faster performance.
        Only kept for backward compatibility with legacy scripts.
        """
        print("⚠️  WARNING: get_worksheet() is DEPRECATED - use FastSheetsAPI instead!")
        print("   This method is 255x slower and can hang. See fast_sheets_helper.py")

        cache_key = (sheet_id, worksheet_name)
        current_time = time.time()

        # Check cache
        if use_cache and cache_key in self.worksheet_cache:
            ws, timestamp = self.worksheet_cache[cache_key]
            if current_time - timestamp < self.worksheet_cache_ttl:
                return ws

        # Cache miss or expired, fetch from API (SLOW - 60s+ and can HANG!)
        try:
            import signal
            import platform

            # Timeout only works on Unix-like systems
            use_timeout = platform.system() != 'Windows'

            if use_timeout:
                def timeout_handler(signum, frame):
                    raise TimeoutError("gspread open_by_key() timed out after 15s - use FastSheetsAPI instead!")

                # Set 15s timeout
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(15)

            self._increment_request_count()
            sheet = self.client.open_by_key(sheet_id)
            self._increment_request_count()
            ws = sheet.worksheet(worksheet_name)

            if use_timeout:
                signal.alarm(0)  # Cancel timeout

        except TimeoutError as e:
            print(f"❌ {e}")
            print("   Migrate your script to use: from fast_sheets_helper import FastSheetsAPI")
            raise
        except Exception as e:
            # Catch other errors (network, auth, etc.)
            print(f"❌ gspread error: {e}")
            print("   Consider using FastSheetsAPI for better reliability")
            raise

        # Cache it
        if use_cache:
            with self.lock:
                self.worksheet_cache[cache_key] = (ws, current_time)

        return ws

    def queue_update(self, sheet_id, worksheet_name, range_name, values, flush_now=False):
        """Queue batch update (Layer 2) - writes happen in background"""
        queue_key = (sheet_id, worksheet_name)

        with self.lock:
            self.batch_queue[queue_key].append({
                'range': range_name,
                'values': values,
                'timestamp': time.time()
            })

            queue_size = len(self.batch_queue[queue_key])
            time_since_flush = time.time() - self.last_flush[queue_key]

        # Flush if max size reached or explicitly requested
        if flush_now or queue_size >= self.batch_max_size:
            self._flush_queue(sheet_id, worksheet_name)
        elif time_since_flush >= self.batch_flush_interval:
            # Will be handled by background thread, but we can do it now
            self._flush_queue(sheet_id, worksheet_name)

    def _flush_queue(self, sheet_id, worksheet_name):
        """Flush batch queue for specific worksheet - FAST API VERSION"""
        queue_key = (sheet_id, worksheet_name)

        with self.lock:
            if not self.batch_queue[queue_key]:
                return

            operations = self.batch_queue[queue_key][:]
            self.batch_queue[queue_key].clear()
            self.last_flush[queue_key] = time.time()

        if not operations:
            return

        try:
            # Use Sheets API directly instead of slow gspread

            # Get access token from current service account
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_files[self.current_account_idx],
                ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            )
            access_token = creds.get_access_token().access_token

            # Build batch update request
            data_list = []
            for op in operations:
                full_range = f"{worksheet_name}!{op['range']}" if '!' not in op['range'] else op['range']
                data_list.append({
                    'range': full_range,
                    'values': op['values']
                })
                # Debug K13:L22 specifically (sparklines)
                if 'K13:L22' in full_range or 'K13:L22' in op['range']:
                    print(f"🔍 DEBUG K13:L22: range={full_range}")
                    print(f"  First row: {op['values'][0]}")
                    print(f"  First row col 2 (sparkline) length: {len(op['values'][0][1]) if len(op['values'][0]) > 1 else 'N/A'}")
                    print(f"  First row col 2 (sparkline) first 80 chars: {op['values'][0][1][:80] if len(op['values'][0]) > 1 else 'N/A'}")
                # Debug A7 specifically
                if 'A7' in full_range:
                    print(f"🔍 DEBUG A7: range={full_range}, values={op['values']}, len={len(str(op['values']))}")

            # Single fast API call
            url = f'https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values:batchUpdate'
            headers = {'Authorization': f'Bearer {access_token}'}
            body = {
                'valueInputOption': 'USER_ENTERED',  # Interprets formulas (was 'RAW')
                'data': data_list
            }

            self._increment_request_count()
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()

            # Debug response
            result = response.json()
            if 'A7' in worksheet_name or any('A7' in op.get('range', '') for op in operations):
                print(f"🔍 DEBUG A7 Response: {result}")

            print(f"✅ Flushed {len(data_list)} queued updates to {worksheet_name}")

        except Exception as e:
            print(f"❌ Batch flush error: {e}")
            # Re-queue operations
            with self.lock:
                self.batch_queue[queue_key].extend(operations)

    def _batch_flusher(self):
        """Background thread to flush queues periodically"""
        while True:
            time.sleep(self.batch_flush_interval)

            with self.lock:
                queue_keys = list(self.batch_queue.keys())

            for queue_key in queue_keys:
                sheet_id, worksheet_name = queue_key
                time_since_flush = time.time() - self.last_flush[queue_key]

                if time_since_flush >= self.batch_flush_interval:
                    self._flush_queue(sheet_id, worksheet_name)

    def flush_all(self):
        """Manually flush all queued operations"""
        with self.lock:
            queue_keys = list(self.batch_queue.keys())

        for queue_key in queue_keys:
            sheet_id, worksheet_name = queue_key
            self._flush_queue(sheet_id, worksheet_name)

    def cache_data(self, key, data, ttl=None):
        """Cache data with Redis or in-memory fallback (Layer 4)"""
        if ttl is None:
            ttl = self.redis_ttl

        # Serialize data (handle DataFrames)
        try:
            import pandas as pd
            if isinstance(data, pd.DataFrame):
                data_str = data.to_json()
            else:
                data_str = json.dumps(data)
        except:
            data_str = json.dumps(data)

        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, data_str)
                return
            except:
                pass

        # Fallback to in-memory
        with self.lock:
            self.memory_cache[key] = (data, time.time() + ttl)

    def get_cached_data(self, key):
        """Retrieve cached data (Layer 4)"""
        # Try Redis first
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    # Try to deserialize as DataFrame first
                    try:
                        import pandas as pd
                        return pd.read_json(cached)
                    except:
                        return json.loads(cached)
            except:
                pass

        # Fallback to in-memory
        with self.lock:
            if key in self.memory_cache:
                data, expiry = self.memory_cache[key]
                if time.time() < expiry:
                    return data
                else:
                    del self.memory_cache[key]

        return None

    def read_range_cached(self, sheet_id, worksheet_name, range_name, use_cache=True):
        """Read range with caching"""
        cache_key = f"sheet:{sheet_id}:{worksheet_name}:{range_name}"

        # Check cache
        if use_cache:
            cached = self.get_cached_data(cache_key)
            if cached is not None:
                return cached

        # Cache miss, fetch from API
        ws = self.get_worksheet(sheet_id, worksheet_name)
        self._increment_request_count()
        values = ws.get(range_name)

        # Cache it
        if use_cache:
            self.cache_data(cache_key, values)

        return values

    def update_immediate(self, sheet_id, worksheet_name, range_name, values):
        """Immediate update (bypass batch queue) - use sparingly"""
        ws = self.get_worksheet(sheet_id, worksheet_name)
        self._increment_request_count()
        ws.update(range_name, values, value_input_option='RAW')

    def get_stats(self):
        """Get cache statistics"""
        with self.lock:
            stats = {
                'service_accounts': len(self.credentials_files),
                'current_account': self.current_account_idx + 1,
                'request_counts': self.account_request_counts[:],
                'worksheet_cache_size': len(self.worksheet_cache),
                'batch_queue_size': sum(len(q) for q in self.batch_queue.values()),
                'memory_cache_size': len(self.memory_cache),
                'redis_enabled': self.redis_client is not None
            }
        return stats


# Global singleton instance
_cache_manager = None

def get_cache_manager(credentials_files=None):
    """Get or create global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(credentials_files=credentials_files)
    return _cache_manager
