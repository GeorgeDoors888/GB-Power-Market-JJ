"""Utilities for monitoring and managing API rate limits"""

import logging
import threading
import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class RateLimitMonitor:
    def __init__(self, window_seconds: int = 60, max_calls: int = 100):
        self.window_seconds = window_seconds
        self.max_calls = max_calls
        self.calls = deque()
        self.lock = threading.Lock()

    def check_rate_limit(self) -> tuple[bool, Optional[float]]:
        """Check if we're within rate limits"""
        now = time.time()

        with self.lock:
            # Remove old calls
            while self.calls and self.calls[0] < now - self.window_seconds:
                self.calls.popleft()

            # Check if we're at the limit
            if len(self.calls) >= self.max_calls:
                wait_time = self.calls[0] + self.window_seconds - now
                return True, max(0, wait_time)

            # Record this call
            self.calls.append(now)
            return False, None

    def wait_if_needed(self):
        """Wait if we're over the rate limit"""
        is_limited, wait_time = self.check_rate_limit()
        if is_limited and wait_time:
            logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")
            time.sleep(wait_time)


class BigQueryQuotaMonitor:
    def __init__(self, client):
        self.client = client
        self.last_check = 0
        self.check_interval = 60  # Check every 60 seconds
        self.quotas = {}

    def check_quotas(self) -> Dict[str, float]:
        """Check BigQuery quota usage"""
        now = time.time()
        if now - self.last_check < self.check_interval:
            return self.quotas

        query = """
        SELECT
            quota_name,
            SAFE_DIVIDE(quota_current, quota_limit) as usage_ratio
        FROM region-eu.INFORMATION_SCHEMA.QUOTA_USAGE
        WHERE quota_name IN (
            'LoadDataIngestBytes',
            'StorageBytes',
            'concurrent_queries'
        )
        """

        try:
            df = self.client.query(query).to_dataframe()
            self.quotas = df.set_index("quota_name")["usage_ratio"].to_dict()
            self.last_check = now

            # Log if any quota is high
            for quota, usage in self.quotas.items():
                if usage > 0.8:
                    logger.warning(f"High quota usage for {quota}: {usage:.1%}")

            return self.quotas

        except Exception as e:
            logger.error(f"Failed to check quotas: {e}")
            return {}
