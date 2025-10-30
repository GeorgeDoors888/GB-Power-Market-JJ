#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modified Elexon data loader to better handle schema changes and duplicates.

This script:
1. Handles schema changes by only loading columns that exist in both source and target
2. Adds metadata to track schema changes
3. Provides deduplication based on source data
4. Adds options for overwriting existing data

Usage:
python ingest_elexon_fixed.py --start 2025-08-28 --end 2025-08-29
python ingest_elexon_fixed.py --start 2025-08-28 --end 2025-08-29 --only TEMP,TSDF
python ingest_elexon_fixed.py --start 2025-08-28 --end 2025-08-29 --overwrite
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Set, Tuple

import google.auth
import google.auth.exceptions
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
from google.api_core.exceptions import BadRequest, Conflict, DeadlineExceeded, NotFound
from google.cloud import bigquery
from tqdm import tqdm

# Integrate ingestion logic from elexon_full_ingest.py
from elexon_full_ingest import fetch_B0620, fetch_B0630, fetch_insights_dataset

# # from schema_handler import get_schema_for_dataset_and_year, get_schema_year_from_date
CORRECTED_SCHEMA_DIR = "schemas/corrected"

# Load environment variables from .env file
load_dotenv()

# Configuration
BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
BQ_PROJECT = "inner-cinema-476211-u9"
BQ_DATASET = "uk_energy_prod"
MAX_RETRIES = 5
RETRY_BACKOFF = 5.0  # seconds
TIMEOUT = (10, 90)  # (connect, read) timeout in seconds
# Set to None to disable sandbox-style auto-expiration of tables
SANDBOX_EXPIRATION_DAYS: Optional[int] = None  # 50
MAX_FRAMES_PER_BATCH = (
    10  # Increased from 1 to 10 to reduce the number of load operations
)
# Time-based flush to avoid losing large in-memory batches on hangs
DEFAULT_FLUSH_SECONDS = 300  # 5 minutes
DEFAULT_BQ_LOAD_TIMEOUT_SEC = 900  # 15 minutes per load job

# Denylist for datetime conversion
DATETIME_CONVERSION_DENYLIST = {
    "publishtime",  # Known to be a string in some datasets like WIND_SOLAR_GEN
}


# Per-dataset max window sizes
CHUNK_RULES = {
    "BOD": "1h",
    "B1770": "1d",
    "BOALF": "1d",
    "COSTS": "1d",  # System Buy/Sell Prices
    "NETBSAD": "1d",
    "DISBSAD": "1d",  # Indicative pricing data
    "IMBALNGC": "7d",
    "PN": "1d",
    "QPN": "1d",
    "QAS": "1d",
    "RDRE": "1d",
    "RDRI": "1d",
    "RURE": "1d",
    "RURI": "1d",
    "FREQ": "1d",
    "FUELINST": "1d",
    "FUELHH": "1d",
    "TEMP": "7d",
    "B1610": "7d",
    "B1630": "1d",
    "NDF": "7d",
    "NDFD": "7d",
    "NDFW": "7d",
    "TSDF": "7d",
    "TSDFD": "7d",
    "TSDFW": "7d",
    "INDDEM": "7d",
    "INDGEN": "7d",
    "ITSDO": "7d",
    "INDO": "7d",
    "MELNGC": "7d",
    "WINDFOR": "7d",
    "WIND": "7d",
    "FOU2T14D": "7d",
    "FOU2T3YW": "7d",
    "NOU2T14D": "7d",
    "NOU2T3YW": "7d",
    "UOU2T14D": "1d",
    "UOU2T3YW": "1d",
    "SEL": "7d",
    "SIL": "7d",
    "OCNMF3Y": "7d",
    "OCNMF3Y2": "7d",
    "OCNMFD": "7d",
    "OCNMFD2": "7d",
    "INTBPT": "7d",
    "MIP": "7d",
    "MID": "7d",
    # MILS/MELS appear stricter with ranges; default to 1d to avoid 400s
    "MILS": "1d",
    "MELS": "1d",
    "MDP": "7d",
    "MDV": "7d",
    "MNZT": "7d",
    "MZT": "7d",
    "NTB": "7d",
    "NTO": "7d",
    "NDZ": "7d",
    "NONBM": "7d",
    "WIND_SOLAR_GEN": "1d",  # Actual or estimated wind and solar generation
    "INTERCONNECTOR_FLOWS": "1d",  # Interconnector imports and exports
    "DEMAND_FORECAST": "1d",  # Rolling system demand and forecasts
    "SURPLUS_MARGIN": "1d",  # Surplus forecast and margin
    "STOR": "1d",  # Short-term operating reserves
    "MARKET_INDEX_PRICES": "1d",  # Market index prices
    "S0621": "1d",  # Total Exempt Supply Volume
}

# Datasets known to be offline or unavailable
LIKELY_OFFLINE = {"MILS", "MELS"}

# Whether to include datasets marked as likely offline; set via CLI
INCLUDE_OFFLINE: bool = False

# API key management (optional; used for unified/physical endpoints if available)
API_KEYS: List[str] = []
_API_KEY_INDEX: int = 0


def _load_all_api_keys() -> List[str]:
    """Load Elexon API keys from environment variables or api.env file.
    Returns a list (possibly empty). Does not log key material.
    """
    keys: List[str] = []
    # Environment variables BMRS_API_KEY_1..20
    for i in range(1, 21):
        val = os.getenv(f"BMRS_API_KEY_{i}")
        if val and val.strip():
            keys.append(val.strip())
    # Fallback: try local api.env in repo root
    if not keys:
        for candidate in ("api.env", os.path.join("old_project", "api.env")):
            try:
                if os.path.exists(candidate):
                    with open(candidate, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if line.startswith("BMRS_API_KEY_") and "=" in line:
                                _, rhs = line.split("=", 1)
                                rhs = rhs.strip()
                                if rhs:
                                    keys.append(rhs)
            except Exception:
                # Ignore file read issues; simply return whatever we have
                pass
    # De-duplicate while keeping order
    seen = set()
    uniq: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    return uniq


def _get_next_api_key() -> Optional[str]:
    global API_KEYS, _API_KEY_INDEX
    if not API_KEYS:
        API_KEYS = _load_all_api_keys()
    if not API_KEYS:
        return None
    key = API_KEYS[_API_KEY_INDEX]
    _API_KEY_INDEX = (_API_KEY_INDEX + 1) % len(API_KEYS)
    return key


def _with_api_key_header(headers: Dict[str, str]) -> Dict[str, str]:
    """Attach x-api-key header if a key is available; do not modify input dict in-place."""
    try:
        key = _get_next_api_key()
    except Exception:
        key = None
    if not key:
        return headers.copy()
    new_h = headers.copy()
    # Elexon unified API expects 'x-api-key'
    new_h.setdefault("x-api-key", key)
    return new_h


# Helper classes
class TimeoutException(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutException


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


# Date and time helpers
def _parse_iso_date(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
        # Support YYYY-MM-DD only
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _chunk_to_delta(spec: str) -> timedelta:
    spec = spec.strip().lower()
    if spec.endswith("h"):
        return timedelta(hours=int(spec[:-1]))
    if spec.endswith("d"):
        return timedelta(days=int(spec[:-1]))
    if spec.endswith("w"):
        return timedelta(weeks=int(spec[:-1]))
    raise ValueError(f"Bad chunk spec '{spec}'")


def _max_window_for(dataset: str) -> timedelta:
    ds = dataset.upper()
    spec = CHUNK_RULES.get(ds, "7d")
    return _chunk_to_delta(spec)


def _iter_windows(
    start: datetime, end: datetime, step: timedelta
) -> Iterable[Tuple[datetime, datetime]]:
    """Iterate through time windows from most recent to oldest."""
    current_start = start
    while current_start < end:
        current_end = min(current_start + step, end)
        yield current_start, current_end
        current_start = current_end


# BigQuery helpers
def _ensure_bq_dataset(client: bigquery.Client, dataset_id: str) -> None:
    fq = f"{client.project}.{dataset_id}"
    try:
        dataset = client.get_dataset(fq)
        logging.info("BigQuery dataset %r exists.", dataset_id)

        fields_to_update = []
        if SANDBOX_EXPIRATION_DAYS is not None:
            if dataset.default_table_expiration_ms is None:
                dataset.default_table_expiration_ms = (
                    SANDBOX_EXPIRATION_DAYS * 24 * 60 * 60 * 1000
                )
                fields_to_update.append("default_table_expiration_ms")
                logging.info(
                    f"Setting default table expiration for dataset {dataset_id} to {SANDBOX_EXPIRATION_DAYS} days."
                )

            if dataset.default_partition_expiration_ms is None:
                dataset.default_partition_expiration_ms = (
                    SANDBOX_EXPIRATION_DAYS * 24 * 60 * 60 * 1000
                )
                fields_to_update.append("default_partition_expiration_ms")
                logging.info(
                    f"Setting default partition expiration for dataset {dataset_id} to {SANDBOX_EXPIRATION_DAYS} days."
                )
        else:
            # If sandbox mode is off, ensure expiration is disabled
            if dataset.default_table_expiration_ms is not None:
                dataset.default_table_expiration_ms = None
                fields_to_update.append("default_table_expiration_ms")
                logging.info(
                    f"Disabling default table expiration for dataset {dataset_id}."
                )
            if dataset.default_partition_expiration_ms is not None:
                dataset.default_partition_expiration_ms = None
                fields_to_update.append("default_partition_expiration_ms")
                logging.info(
                    f"Disabling default partition expiration for dataset {dataset_id}."
                )

        if fields_to_update:
            client.update_dataset(dataset, fields_to_update)

    except NotFound:
        ds = bigquery.Dataset(fq)
        ds.location = "EU"
        if SANDBOX_EXPIRATION_DAYS is not None:
            ds.default_table_expiration_ms = (
                SANDBOX_EXPIRATION_DAYS * 24 * 60 * 60 * 1000
            )
            ds.default_partition_expiration_ms = (
                SANDBOX_EXPIRATION_DAYS * 24 * 60 * 60 * 1000
            )
            client.create_dataset(ds)
            logging.info(
                f"Created BigQuery dataset %r with default table and partition expiration of {SANDBOX_EXPIRATION_DAYS} days.",
                dataset_id,
            )
        else:
            client.create_dataset(ds)
            logging.info(
                "Created BigQuery dataset %r with no default expiration.",
                dataset_id,
            )


def _get_existing_windows(
    client: bigquery.Client,
    dataset_id: str,
    table_name: str,
    start: datetime,
    end: datetime,
) -> set[datetime]:
    table_id = f"{client.project}.{dataset_id}.{table_name}"
    windows = set()
    logging.info(
        f"🔎 Querying existing windows for {table_id} between {start} and {end}"
    )
    try:
        client.get_table(table_id)
    except NotFound:
        logging.info(f"Table {table_id} does not exist, skipping window query.")
        return windows
    query = f"""
    SELECT DISTINCT _window_from_utc FROM `{table_id}`
    WHERE _window_from_utc IS NOT NULL
      AND _window_from_utc >= '{start.isoformat()}'
      AND _window_from_utc < '{end.isoformat()}'
    """
    try:
        logging.debug(f"Running BQ query: {query}")
        query_job = client.query(query, timeout=60.0)
        for row in query_job.result(timeout=60.0):
            if row[0] is not None:
                windows.add(row[0])
        logging.info("Found %d existing windows for %s", len(windows), table_name)
    except Exception as e:
        logging.warning("⚠️  Could not query existing windows for %s: %s", table_name, e)
    return windows


def get_corrected_schema_for_dataset(
    dataset_code: str,
) -> Optional[List[bigquery.SchemaField]]:
    """
    Loads a corrected BigQuery schema from the 'schemas/corrected' directory.
    """
    # This mapping is simplified as the new schema files are named more consistently.
    # It may need to be adjusted if filenames are not direct matches.
    filename_base = f"bmrs_{dataset_code.lower()}"
    if dataset_code == "RDRI":
        filename_base = "bmrs_rdri_new_schema"

    schema_path = os.path.join(CORRECTED_SCHEMA_DIR, f"{filename_base}.json")

    if not os.path.exists(schema_path):
        logging.warning(
            f"No corrected schema file found for dataset '{dataset_code}' at '{schema_path}'."
        )
        return None

    try:
        with open(schema_path, "r") as f:
            schema_json = json.load(f)

        # Convert the JSON schema to a list of SchemaField objects
        return [bigquery.SchemaField.from_api_repr(field) for field in schema_json]
    except (json.JSONDecodeError, KeyError) as e:
        logging.error(
            f"Error loading or parsing corrected schema file '{schema_path}': {e}"
        )
        return None


def clear_bq_date_range(
    client: bigquery.Client,
    dataset_id: str,
    table_name: str,
    from_dt: datetime,
    to_dt: datetime,
):
    """Clear a date range from a BigQuery table."""
    try:
        table_ref = client.dataset(dataset_id).table(table_name)

        # Get the table to check for existence and schema
        table = client.get_table(table_ref)

        # Find the primary timestamp column, looking for common patterns
        ts_col = None
        for field in table.schema:
            if field.field_type in ("TIMESTAMP", "DATETIME") and (
                "settlementDate" in field.name
                or "startTime" in field.name
                or "time" in field.name
                or "date" in field.name
            ):
                ts_col = field.name
                break

        if not ts_col:
            # Fallback to the first TIMESTAMP/DATETIME column if specific names aren't found
            ts_col = next(
                (
                    f.name
                    for f in table.schema
                    if f.field_type in ("TIMESTAMP", "DATETIME")
                ),
                None,
            )

        if not ts_col:
            logging.warning(
                f"⚠️ No suitable TIMESTAMP/DATETIME column found for {table_name}, cannot clear range."
            )
            return

        from_ts = from_dt.isoformat()
        to_ts = to_dt.isoformat()

        query = f"DELETE FROM `{table_ref.project}.{table_ref.dataset_id}.{table_ref.table_id}` WHERE `{ts_col}` >= TIMESTAMP('{from_ts}') AND `{ts_col}` < TIMESTAMP('{to_ts}')"

        logging.warning(
            f"🔥 Deleting data from {table_ref.path} for range {from_ts} to {to_ts}"
        )

        job = client.query(query)
        job.result()  # Wait for the job to complete

        if job.errors:
            raise RuntimeError(job.errors)

        logging.info(f"✅ Successfully cleared date range for {table_name}")

    except NotFound:
        logging.info(
            f"ℹ️ Table {table_name} does not exist, skipping date range clearing."
        )
        return
    except Exception as e:
        logging.error(f"❌ {table_name.upper()}: Failed to clear date range: {e}")
        # Re-raise the exception to be caught by the main loop
        raise


# Data processing helpers
def _flatten_json_payload(obj) -> pd.DataFrame:
    """
    Accepts either:
      • dict with 'data' key (list of dicts)
      • list[dict]
      • scalar -> becomes 0-row df
    Returns pandas DataFrame (possibly empty).
    """
    if obj is None:
        return pd.DataFrame()
    if isinstance(obj, dict):
        if "data" in obj and isinstance(obj["data"], list):
            return pd.json_normalize(obj["data"])
        if "results" in obj and isinstance(obj["results"], list):
            return pd.json_normalize(obj["results"])
        # If dict of fields (single row), wrap it:
        return pd.json_normalize([obj])
    if isinstance(obj, list):
        return pd.json_normalize(obj)
    # Unknown -> empty
    return pd.DataFrame()


def _convert_datetime_columns(df: pd.DataFrame, dataset: str = None) -> pd.DataFrame:
    """
    Convert known date/time columns to UTC-aware datetime objects.
    Handles various source formats and standardizes them.
    """
    df = df.copy()
    for col in df.columns:
        # Skip any column in the denylist
        if col in DATETIME_CONVERSION_DENYLIST:
            logging.info(f"Skipping datetime conversion for denylisted column '{col}'.")
            continue

        # Skip the problematic column for the specific dataset
        if dataset == "WIND_SOLAR_GEN" and col == "publishtime":
            logging.info(
                f"Skipping datetime conversion for 'publishtime' in WIND_SOLAR_GEN dataset."
            )
            continue

        if col.lower().endswith("time") or col.lower().endswith("date"):
            # Only attempt conversion if not already a datetime type
            if not pd.api.types.is_datetime64_any_dtype(df[col]):
                try:
                    # Use a flexible parser that can handle various formats
                    df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                    logging.info(f"Converting column '{col}' to pandas datetime (UTC)")
                except (ValueError, TypeError) as e:
                    logging.warning(
                        f"⚠️ Could not convert column '{col}' to datetime: {e}"
                    )
    return df


def _csv_to_df(text: str) -> pd.DataFrame:
    # Some endpoints return CSV; use pandas to read.
    if not text or not text.strip():
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(text))


def _fetch_system_prices(from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
    """
    Fetch System Buy/Sell Prices data from BMRS API.
    Uses the balancing/settlement/system-prices endpoint.
    """
    import requests

    # Format dates for the API (YYYY-MM-DD)
    start_date = from_dt.strftime("%Y-%m-%d")
    end_date = to_dt.strftime("%Y-%m-%d")

    # System prices API endpoint
    base_url = (
        "https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/system-prices"
    )

    # Try to get API key
    api_key = None
    try:
        api_key = _get_next_api_key()
    except Exception:
        pass

    all_data = []
    current_date = from_dt.date()
    end_date_obj = to_dt.date()

    while current_date <= end_date_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        url = f"{base_url}/{date_str}"

        params = {}
        if api_key:
            params["apiKey"] = api_key

        headers = {"Accept": "application/json"}

        try:
            response = requests.get(
                url, params=params, headers=headers, timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]:
                    for item in data["data"]:
                        # Add metadata columns
                        item["_dataset"] = "COSTS"
                        item["_window_from_utc"] = from_dt.isoformat()
                        item["_window_to_utc"] = to_dt.isoformat()
                        item["_ingested_utc"] = datetime.utcnow().isoformat()
                        all_data.append(item)

            elif response.status_code == 404:
                logging.debug(f"No system prices data for {date_str}")
            else:
                logging.warning(
                    f"Failed to fetch system prices for {date_str}: {response.status_code}"
                )

        except Exception as e:
            logging.warning(f"Error fetching system prices for {date_str}: {e}")

        current_date += timedelta(days=1)

    if all_data:
        return pd.DataFrame(all_data)
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(
            columns=[
                "settlementDate",
                "settlementPeriod",
                "systemSellPrice",
                "systemBuyPrice",
                "priceCategory",
                "_dataset",
                "_window_from_utc",
                "_window_to_utc",
                "_ingested_utc",
            ]
        )


def _fetch_bmrs(
    dataset: str,
    from_dt: datetime,
    to_dt: datetime,
    bm_units: Optional[List[str]] = None,
    data_dir: Optional[str] = None,
) -> pd.DataFrame:
    logging.info(f"🌐 Fetching BMRS dataset={dataset} from={from_dt} to={to_dt}")
    """
    Fetch a single window from BMRS dataset.
    Strategy:
      - Always try primary JSON endpoint first.
      - For MILS/MELS, try unified /api endpoints (including /stream and /data) BEFORE treating primary 400/422 as fatal.
      - Only if all attempts fail with HTTP errors do we surface the last 400/422; otherwise return an empty frame.
    """
    ds = dataset.upper()

    # Special handling for COSTS dataset (System Buy/Sell Prices)
    if ds == "COSTS":
        return _fetch_system_prices(from_dt, to_dt)

    # Special handling for datasets that might be on the insights API
    if ds in ("WIND_SOLAR_GEN", "DEMAND_FORECAST", "SURPLUS_MARGIN"):
        logging.debug(f"Attempting to fetch {ds} using Insights API logic.")
        try:
            insights_paths = {
                "WIND_SOLAR_GEN": "/generation/actual/per-type/wind-and-solar",
                "DEMAND_FORECAST": "/forecast/demand/total/day-ahead",
                "SURPLUS_MARGIN": "/forecast/surplus/daily",
            }
            if ds in insights_paths:
                path = insights_paths[ds]
                params = {
                    "from": from_dt.strftime("%Y-%m-%d"),
                    "to": to_dt.strftime("%Y-%m-%d"),
                    "format": "json",
                }

                # Using the insights_get function from elexon_full_ingest
                from elexon_full_ingest import insights_get

                resp = insights_get(path, params)

                js = resp.json()
                data = js.get("data", js)
                df = pd.DataFrame(data)

                if not df.empty:
                    logging.info(
                        f"Successfully fetched {len(df)} records for {ds} from Insights API."
                    )
                    # The data is now in `df`, so we can return it to the main processing loop
                    return df
                else:
                    logging.debug(f"Insights API returned no data for {ds}.")

            # If we are here, it means no data was fetched.
            # Fall through to the standard BMRS logic.

        except Exception as e:
            logging.warning(f"Could not fetch {ds} using Insights API logic: {e}")

        logging.debug(f"Falling back to standard _fetch_bmrs logic for {ds}")

    def rfc3339_z(dt: datetime) -> str:
        # Ensure UTC with trailing 'Z' per RFC3339 examples in Elexon docs
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def date_only(dt: datetime) -> str:
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")

    # Primary path uses BMRS base with from/to as RFC3339 with trailing Z
    primary_url = f"{BMRS_BASE}/{ds}"
    if ds == "BOD":
        primary_url = f"{BMRS_BASE}/{ds}/stream"
    primary_params = {"from": rfc3339_z(from_dt), "to": rfc3339_z(to_dt)}

    # Fix for BOD based on documentation
    if ds == "BOD":
        primary_params["settlementPeriodFrom"] = "1"
        primary_params["settlementPeriodTo"] = "50"

    # If we have an API key, pass it for BMRS base as 'apiKey'
    try:
        _k = _get_next_api_key()
        if _k:
            primary_params["apiKey"] = _k
    except Exception:
        pass

    # Alt dataset endpoints under BMRS base (per local OpenAPI metadata)
    alt_url_root = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
    # params can include strings or lists (e.g., bmUnit repeated params); allow object values
    alt_variants: List[Tuple[str, Dict[str, object], Dict[str, str]]] = []
    if ds in {"MILS", "MELS", "PN", "QPN"}:
        # Base variants
        # Build a helper with apiKey query param when available
        _ak = None
        try:
            _ak = _get_next_api_key()
        except Exception:
            _ak = None

        alt_variants.extend(
            [
                (
                    f"{alt_url_root}/{ds}",
                    {
                        "from": rfc3339_z(from_dt),
                        "to": rfc3339_z(to_dt),
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
                (
                    f"{alt_url_root}/{ds}/stream",
                    {
                        "from": rfc3339_z(from_dt),
                        "to": rfc3339_z(to_dt),
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
                (
                    f"{alt_url_root}/{ds}/data",
                    {
                        "startTime": rfc3339_z(from_dt),
                        "endTime": rfc3339_z(to_dt),
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
            ]
        )
        # Settlement period constrained variants (helps on strict validation)
        alt_variants.extend(
            [
                (
                    f"{alt_url_root}/{ds}",
                    {
                        "from": rfc3339_z(from_dt),
                        "to": rfc3339_z(to_dt),
                        "settlementPeriodFrom": "1",
                        "settlementPeriodTo": "50",
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
                (
                    f"{alt_url_root}/{ds}/stream",
                    {
                        "from": rfc3339_z(from_dt),
                        "to": rfc3339_z(to_dt),
                        "settlementPeriodFrom": "1",
                        "settlementPeriodTo": "50",
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
                # Date-only window with settlement period constraints (explicit per docs)
                (
                    f"{alt_url_root}/{ds}/stream",
                    {
                        "from": date_only(from_dt),
                        "to": date_only(to_dt - timedelta(days=1)),
                        "settlementPeriodFrom": "1",
                        "settlementPeriodTo": "50",
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                ),
            ]
        )

        # Also try BMRS dataset endpoints filtered by BM Unit if provided
        if bm_units:
            alt_variants.append(
                (
                    f"{alt_url_root}/{ds}",
                    {
                        "from": rfc3339_z(from_dt),
                        "to": rfc3339_z(to_dt),
                        "bmUnit": bm_units,
                        **({"apiKey": _ak} if _ak else {}),
                    },
                    {"Accept": "application/json"},
                )
            )

    last_http_err: Optional[requests.HTTPError] = None

    # Helper to process a response: return DataFrame (possibly empty) or None to keep trying
    def process_response(resp: requests.Response) -> Optional[pd.DataFrame]:
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            nonlocal last_http_err
            last_http_err = e
            return None
        # 200 OK here

        if data_dir:
            try:
                day_str = from_dt.strftime("%Y-%m-%d")
                # Use a unique filename to avoid overwrites if chunking is less than a day
                time_str = from_dt.strftime("%H%M%S")
                save_path = os.path.join(
                    data_dir, dataset.upper(), f"{day_str}_{time_str}.json"
                )
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    try:
                        json.dump(resp.json(), f, indent=2)
                    except (json.JSONDecodeError, AttributeError):
                        f.write(resp.text)
                logging.info(f"💾 Saved raw data to {save_path}")
            except Exception as save_e:
                logging.warning(f"⚠️ Failed to save raw data for {dataset}: {save_e}")

        try:
            payload = resp.json()
        except ValueError:
            payload = None
        if payload is not None:
            df = _flatten_json_payload(payload)
            return df  # may be empty
        txt = resp.text or ""
        if txt.strip():
            return _csv_to_df(txt)
        return pd.DataFrame()

    # 1) Primary JSON
    try:
        rj = requests.get(
            primary_url,
            params=primary_params,
            timeout=TIMEOUT,
            headers={"Accept": "application/json"},
        )
        if rj.status_code == 404:
            # Not available on this path — keep trying others
            pass
        else:
            df = process_response(rj)
            if df is not None:
                return df
    except Exception:
        # Ignore and keep trying
        pass

    # 2) For MILS/MELS, try unified API variants before CSV fallback
    if alt_variants:
        for url, params, headers in alt_variants:
            try:
                r = requests.get(
                    url, params=params, timeout=TIMEOUT, headers=headers  # type: ignore[arg-type]
                )
                if r.status_code == 404:
                    continue
                df = process_response(r)
                if df is not None:
                    return df
            except Exception:
                continue

        # If unified dataset endpoints yielded no results, try the physical API as a stronger fallback
        # Strategy: for each day in [from_dt, to_dt), query settlement periods 1..50 via /balancing/physical/all
        # Optionally filter by BM Units if provided.
        try:
            phys_base = "https://data.elexon.co.uk/bmrs/api/v1/balancing/physical/all"
            # API key for physical fallback if available
            ak_phys = None
            try:
                ak_phys = _get_next_api_key()
            except Exception:
                ak_phys = None
            frames: List[pd.DataFrame] = []
            cur_day = from_dt.astimezone(timezone.utc).date()
            end_day = (to_dt - timedelta(seconds=1)).astimezone(timezone.utc).date()
            while cur_day <= end_day:
                for sp in range(1, 51):
                    params: Dict[str, object] = {
                        "dataset": ds,
                        "settlementDate": cur_day.strftime("%Y-%m-%d"),
                        "settlementPeriod": str(sp),
                    }
                    # Support optional BMU filters using repeated bmUnit parameters
                    if bm_units:
                        # requests allows lists to become repeated params if we pass a list
                        params["bmUnit"] = bm_units
                    try:
                        pr = requests.get(
                            phys_base,
                            params={
                                **params,
                                **({"apiKey": ak_phys} if ak_phys else {}),
                            },  # type: ignore[arg-type]
                            timeout=TIMEOUT,
                            headers={"Accept": "application/json"},
                        )
                        if pr.status_code == 404:
                            continue
                        pr.raise_for_status()
                        payload = None
                        try:
                            payload = pr.json()
                        except ValueError:
                            payload = None
                        if payload is not None:
                            dfp = _flatten_json_payload(payload)
                            if not dfp.empty:
                                # Some physical endpoints may return multiple datasets; filter to desired one
                                if "dataset" in dfp.columns:
                                    dfp = dfp[
                                        dfp["dataset"].astype(str).str.upper() == ds
                                    ]
                                frames.append(dfp)
                    except requests.HTTPError as e:
                        # Treat 400/422 as no-data for offline datasets; otherwise continue trying other SPs
                        if (
                            getattr(e.response, "status_code", None) in (400, 422)
                            and ds in LIKELY_OFFLINE
                        ):
                            continue
                        # For other HTTP errors, continue to next SP/day
                        continue
                    except Exception:
                        # Network or parse error; move on
                        continue
                cur_day = cur_day + timedelta(days=1)
            if frames:
                try:
                    return pd.concat(frames, ignore_index=True)
                except Exception:
                    # If concat fails for any reason, fall back to first non-empty
                    for fdf in frames:
                        if not fdf.empty:
                            return fdf
        except Exception:
            # Physical fallback failed entirely; proceed to CSV fallback
            pass

    # 3) CSV fallback on primary URL
    try:
        rc = requests.get(
            primary_url,
            params={**primary_params, "format": "csv"},
            timeout=TIMEOUT,
            headers={"Accept": "text/csv"},
        )
        if rc.status_code != 404:
            df = process_response(rc)
            if df is not None:
                return df
    except Exception:
        pass

    # If we reach here: if all attempts failed with HTTP errors and the last is 400/422, surface it
    if last_http_err is not None and getattr(
        last_http_err.response, "status_code", None
    ) in (400, 422):
        raise last_http_err

    # Otherwise, treat as no data for this window
    return pd.DataFrame()


def _sanitize_for_bq(
    df: pd.DataFrame, schema: Optional[List[bigquery.SchemaField]] = None
) -> pd.DataFrame:
    """
    Final, robust sanitization before BQ load. This is the last step.
    - Force-converts object columns to strings.
    - Force-converts datetime columns to timezone-naive.
    - Converts numeric types to nullable pandas types.
    - Uses the provided schema to apply correct types.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    logging.info(
        f"--- Starting final sanitization for BQ load on DataFrame with {len(df.columns)} columns ---"
    )

    schema_types = {field.name: field.field_type for field in schema} if schema else {}

    for col in df.columns:
        dtype = str(df[col].dtype)
        bq_type = schema_types.get(col)
        logging.debug(
            f"Sanitizing column '{col}' of type '{dtype}' with BQ type '{bq_type}'"
        )

        if bq_type in ("FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC", "INTEGER", "INT64"):
            # This is a numeric column according to the schema.
            # First, replace string 'None' with actual NaN before converting.
            if df[col].dtype == "object":
                df[col] = df[col].replace(["None", "null", ""], np.nan)

            # Coerce to numeric, turning any remaining non-numeric values into NaN.
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if bq_type in ("INTEGER", "INT64"):
                df[col] = df[col].astype("Int64")
                logging.info(
                    f" -> Converted integer column '{col}' to nullable Int64 based on schema."
                )
            else:
                df[col] = df[col].astype("Float64")
                logging.info(
                    f" -> Converted float column '{col}' to nullable Float64 based on schema."
                )

        elif bq_type == "TIMESTAMP":
            # Always convert to pandas datetime (UTC) for TIMESTAMP columns, even if dtype is object
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                logging.info(
                    f" -> Converted column '{col}' to pandas datetime (UTC) for TIMESTAMP schema."
                )
            except Exception as e:
                logging.warning(
                    f" -> Failed to convert column '{col}' to datetime for TIMESTAMP: {e}. Forcing to string."
                )
                df[col] = df[col].astype(str)

        elif "datetime" in dtype:
            try:
                # Ensure UTC, then make naive for pyarrow
                df[col] = pd.to_datetime(
                    df[col], errors="coerce", utc=True
                ).dt.tz_convert(None)
                logging.info(
                    f" -> Converted datetime column '{col}' to timezone-naive."
                )
            except Exception as e:
                logging.warning(
                    f" -> Failed to convert datetime column '{col}', forcing to string. Error: {e}"
                )
                df[col] = df[col].astype(str)
        elif dtype == "object":
            # For object columns not explicitly typed as numeric or TIMESTAMP in the schema,
            # force them to string to be safe.
            df[col] = df[col].astype(str)
            logging.info(f" -> Forced object column '{col}' to string.")
        elif "int" in dtype:
            df[col] = df[col].astype("Int64")
            logging.info(f" -> Converted integer column '{col}' to nullable Int64.")
        elif "float" in dtype:
            df[col] = df[col].astype("Float64")
            logging.info(f" -> Converted float column '{col}' to nullable Float64.")

    logging.info("--- Final sanitization complete ---")
    return df


def _generate_dedup_key(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a deterministic deduplication key from source data.
    This ensures records can be uniquely identified even if metadata changes.
    Uses content fields (non-metadata) to create a consistent hash.
    """
    df = df.copy()

    # Filter out metadata columns that start with "_"
    content_cols = [col for col in df.columns if not col.startswith("_")]

    if not content_cols:
        # If no content columns, use all columns
        content_cols = df.columns.tolist()

    # Track which columns were used for the hash key
    df["_hash_source_cols"] = str(content_cols)

    # Create a consistent hash of key content fields
    try:
        import hashlib
        import json

        def hash_row(row):
            """Create a stable hash from row values, handling NaN values."""
            # Filter out NaN values and convert to a stable representation
            row_dict = {}
            for k, v in row.items():
                if pd.notna(v):  # Skip NaN/None values
                    if isinstance(v, (int, float, bool)):
                        row_dict[k] = v
                    else:
                        row_dict[k] = str(v)

            # Create a deterministic hash
            row_json = json.dumps(row_dict, sort_keys=True)
            return hashlib.md5(row_json.encode()).hexdigest()

        df["_hash_key"] = df[content_cols].apply(hash_row, axis=1)
        logging.info(
            f"Created hash keys for {len(df)} rows using {len(content_cols)} content columns"
        )
    except Exception as e:
        logging.warning(f"⚠️ Failed to generate hash keys: {e}")
        # Fallback to a simple concatenated string
        df["_hash_key"] = df[content_cols].astype(str).sum(axis=1)

    return df


def _append_metadata_cols(
    df: pd.DataFrame, dataset: str, from_dt: datetime, to_dt: datetime
) -> pd.DataFrame:
    """
    Add standard metadata columns for tracking source, time windows, etc.
    """
    if df is None or df.empty:
        return df
    df = df.copy()

    # Convert date/time columns first
    df = _convert_datetime_columns(df, dataset=dataset)
    # Ensure BOD timeFrom/timeTo are pandas datetime for BQ TIMESTAMP compatibility
    if dataset.upper() == "BOD":
        for col in ["timeFrom", "timeTo"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

    # Save original columns as metadata
    original_cols = df.columns.tolist()

    # Add standard metadata
    df["_dataset"] = dataset.upper()
    df["_window_from_utc"] = from_dt.replace(tzinfo=timezone.utc).isoformat()
    df["_window_to_utc"] = to_dt.replace(tzinfo=timezone.utc).isoformat()
    df["_ingested_utc"] = datetime.now(timezone.utc).isoformat()

    # Add metadata tracking source schema
    df["_source_columns"] = str(original_cols)
    df["_source_api"] = "BMRS"

    # Before returning, sanitize all data types for BQ
    schema = get_corrected_schema_for_dataset(dataset.upper())
    df = _sanitize_for_bq(df, schema=schema)

    return df


def _safe_table_name(prefix: str, dataset: str) -> str:
    """Create a safe BigQuery table name."""
    import re

    # BQ table names are limited to 1024 characters and can only contain letters, numbers, or underscores.
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", dataset.lower())
    return f"{prefix}_{safe_name}"


from bigquery_utils import BigQueryQuotaManager, load_dataframe_with_retry
from bigquery_utils import (
    load_dataframe_with_schema_adaptation as bq_load_dataframe_with_schema_adaptation,
)
from rate_limit_monitor import BigQueryQuotaMonitor, RateLimitMonitor
from schema_validator import get_schema_for_year, validate_schema_compatibility


def local_load_dataframe_with_schema_adaptation(
    client: bigquery.Client,
    df: pd.DataFrame,
    dataset_id: str,
    table_name: str,
    write_disposition: str = "WRITE_APPEND",
    load_timeout_sec: int = DEFAULT_BQ_LOAD_TIMEOUT_SEC,
    auto_add_schema_fields: bool = True,
) -> bool:
    """
    Load a DataFrame to BigQuery with smart handling of schema changes.

    IMPORTANT: Parameter ordering is critical for correct table path construction!
    - client: The BigQuery client
    - df: The DataFrame to load
    - dataset_id: The dataset ID (e.g., 'uk_energy_insights')
    - table_name: The table name (e.g., 'bmrs_freq')

    DO NOT pass client.project as dataset_id as this will cause duplicate project IDs
    in the table path (e.g., 'project.project.table').

    The function constructs the table_id as: f"{client.project}.{dataset_id}.{table_name}"

    Returns True if successful, False otherwise.
    """
    if df is None or df.empty:
        logging.info(f"🟡 No data to load for {table_name}")
        return True

    # Use the validation function to check and construct the table_id
    table_id = _validate_table_path(client, dataset_id, table_name)
    if table_id is None:
        return False

    logging.info(f"⬆️ Loading {len(df)} rows to {table_id}")

    # Check if table exists and get schema if it does
    table_exists = True
    try:
        table = client.get_table(table_id)
        existing_columns = {field.name for field in table.schema}
        existing_schema = {field.name: field.field_type for field in table.schema}
        logging.info(
            f"Found existing table {table_id} with {len(existing_columns)} columns"
        )
    except NotFound:
        table_exists = False
        existing_columns = set()
        existing_schema = {}
        logging.info(f"Table {table_id} does not exist, will create it")
    except Exception as e:
        logging.warning(f"⚠️ Failed to inspect table {table_id}: {e}")
        table_exists = False
        existing_columns = set()
        existing_schema = {}

    # For new tables, just load the data directly
    if not table_exists:
        try:
            # Define schema based on DataFrame
            schema = []
            for col, dtype in df.dtypes.items():
                field_type = "STRING"  # Default
                if pd.api.types.is_integer_dtype(dtype):
                    field_type = "INTEGER"
                elif pd.api.types.is_float_dtype(dtype):
                    field_type = "FLOAT"
                elif pd.api.types.is_bool_dtype(dtype):
                    field_type = "BOOLEAN"
                elif pd.api.types.is_datetime64_any_dtype(dtype):
                    field_type = "TIMESTAMP"
                schema.append(bigquery.SchemaField(str(col), field_type))

            # Create table with expiration if in sandbox mode
            table = bigquery.Table(table_id, schema=schema)
            table = client.create_table(table, exists_ok=True)

            job_config = bigquery.LoadJobConfig(
                schema=schema,
                write_disposition=write_disposition,
            )

            # Use quota-aware loading with retries
            quota_manager = BigQueryQuotaManager(client)
            try:
                load_job = load_dataframe_with_retry(
                    client=client,
                    df=df,
                    table_id=table_id,
                    job_config=job_config,
                    quota_manager=quota_manager,
                )
            except Exception as e:
                logging.error(f"Failed to load data after retries: {e}")
                return False
            logging.info(f"✅ Created new table {table_id} and loaded {len(df)} rows")
            return True
        except Exception as e:
            logging.error(f"❌ Failed to create and load new table {table_id}: {e}")
            return False

    # For existing tables, only include columns that exist in the table
    df_columns = set(df.columns)

    # Columns allowed to load = intersection only
    common_columns = df_columns & existing_columns
    if not common_columns:
        logging.error(f"❌ No common columns between DataFrame and table {table_id}")
        return False

    filtered_df = df[list(common_columns)].copy()
    logging.info(
        f"Filtered DataFrame from {len(df_columns)} to {len(common_columns)} columns"
    )

    # Cast DataFrame columns to match existing table schema
    def _cast_series_to_bq_type(series: pd.Series, bq_type: str) -> pd.Series:
        # Always convert to string first to handle mixed types, then to the target type.
        # This is safer for pyarrow.
        series_str = series.astype(str)
        try:
            if bq_type in ("STRING", "GEOGRAPHY"):
                return series_str
            if bq_type in ("FLOAT", "FLOAT64", "NUMERIC", "BIGNUMERIC"):
                return pd.to_numeric(series_str, errors="coerce")
            if bq_type in ("INTEGER", "INT64"):
                return pd.to_numeric(series_str, errors="coerce").astype("Int64")
            if bq_type == "BOOLEAN":
                return (
                    series_str.str.lower()
                    .map(
                        {
                            "true": True,
                            "1": True,
                            "t": True,
                            "yes": True,
                            "nan": None,
                            "<NA>": None,
                            "false": False,
                            "0": False,
                            "f": False,
                            "no": False,
                        }
                    )
                    .astype("boolean")
                )
            if bq_type == "TIMESTAMP":
                dt_series = pd.to_datetime(series_str, errors="coerce", utc=True)
                return dt_series
            if bq_type == "DATE":
                return pd.to_datetime(series_str, errors="coerce", utc=True).dt.date
            if bq_type == "DATETIME":
                return pd.to_datetime(series_str, errors="coerce", utc=True)
            if bq_type == "TIME":
                return pd.to_datetime(series_str, errors="coerce", utc=True).dt.time
        except Exception as e:
            logging.warning(
                f"⚠️ Casting to {bq_type} failed for series {series.name}: {e}. Falling back to string."
            )
            return series_str
        return series_str

    # Apply casting for each common column to match table schema
    for col in list(common_columns):
        bq_type = existing_schema.get(col)
        if not bq_type:
            continue
        try:
            filtered_df[col] = _cast_series_to_bq_type(filtered_df[col], bq_type)
        except Exception as cast_e:
            logging.warning(
                f"⚠️ Failed to cast column '{col}' to {bq_type} for {table_id}: {cast_e} — using string fallback"
            )
            try:
                filtered_df[col] = filtered_df[col].astype(str)
            except Exception:
                # If even that fails, drop the column from this batch
                logging.warning(
                    f"⚠️ Dropping column '{col}' from load due to irrecoverable casting error"
                )
                filtered_df = filtered_df.drop(columns=[col])
                common_columns.discard(col)

    # Load the filtered DataFrame
    try:
        job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
        )

        # Attempt the load with limited retries on quota errors
        MAX_LOAD_RETRIES = 5  # Increased from 3 to 5
        for attempt in range(1, MAX_LOAD_RETRIES + 1):
            try:
                load_job = client.load_table_from_dataframe(
                    filtered_df, table_id, job_config=job_config
                )
                try:
                    load_job.result(timeout=load_timeout_sec)
                except DeadlineExceeded as te:
                    # Try to cancel and fall back to splitting the batch to reduce risk
                    try:
                        load_job.cancel()
                    except Exception:
                        pass
                    if len(filtered_df.index) > 1:
                        logging.warning(
                            "⏳ Load timed out for %s (rows=%d). Splitting batch and retrying...",
                            table_id,
                            len(filtered_df.index),
                        )
                        mid = len(filtered_df.index) // 2
                        part_a = filtered_df.iloc[:mid]
                        part_b = filtered_df.iloc[mid:]
                        # Recursively load smaller parts with same timeout
                        ok_a = local_load_dataframe_with_schema_adaptation(
                            client,
                            part_a,
                            dataset_id,
                            table_name,
                            write_disposition=write_disposition,
                            load_timeout_sec=load_timeout_sec,
                        )
                        ok_b = local_load_dataframe_with_schema_adaptation(
                            client,
                            part_b,
                            dataset_id,
                            table_name,
                            write_disposition=write_disposition,
                            load_timeout_sec=load_timeout_sec,
                        )
                        if ok_a and ok_b:
                            logging.info(
                                "✅ Successfully loaded split batches to %s (rows=%d)",
                                table_id,
                                len(filtered_df.index),
                            )
                            return True
                        # If split didn't help, raise to outer handler
                    raise te
                logging.info(
                    f"✅ Successfully loaded {len(filtered_df)} rows to {table_id}"
                )
                # Add a small delay between batch loads to avoid hitting quota limits
                time.sleep(2.0)
                return True
            except Exception as e:
                msg = str(e)
                # Backoff specifically for BigQuery quotaExceeded
                if "quotaExceeded" in msg or "Quota exceeded" in msg:
                    # More aggressive exponential backoff with jitter for quota issues
                    import random

                    base_wait = 30 * (2 ** (attempt - 1))  # 30s, 60s, 120s, 240s, 480s
                    jitter = random.uniform(0.5, 1.5)  # Add 50% randomness
                    wait_s = min(900, base_wait * jitter)  # Cap at 15 minutes
                    logging.warning(
                        f"⏳ Quota exceeded while loading {table_id} (attempt {attempt}/{MAX_LOAD_RETRIES}). Sleeping {wait_s:.1f}s before retry"
                    )
                    time.sleep(wait_s)
                    continue
                else:
                    raise
        # If we reach here, all retries exhausted
        raise Exception(
            f"Load retries exhausted for {table_id} after {MAX_LOAD_RETRIES} attempts due to quotaExceeded"
        )
    except Exception as e:
        logging.error(f"❌ Failed to load data to {table_id}: {e}")

        # Try one more time with just the basic metadata columns if they exist
        try:
            # Only include metadata columns that are present in the existing table
            metadata_columns = {
                "_dataset",
                "_window_from_utc",
                "_window_to_utc",
                "_ingested_utc",
            }
            minimal_columns = list((metadata_columns & df_columns) & existing_columns)
            if minimal_columns:
                minimal_df = df[minimal_columns]
                job_config = bigquery.LoadJobConfig(
                    write_disposition=write_disposition,
                )
                load_job = client.load_table_from_dataframe(
                    minimal_df, table_id, job_config=job_config
                )
                load_job.result()
                logging.info(
                    f"✅ Loaded minimal data ({len(minimal_columns)} columns) to {table_id}"
                )
                return True
        except Exception as min_e:
            logging.error(f"❌ Final attempt failed: {min_e}")

        return False


def _validate_table_path(client, dataset_id, table_name):
    return f"{client.project}.{dataset_id}.{table_name}"


def _load_to_staging_table(
    client: bigquery.Client,
    df: pd.DataFrame,
    dataset_id: str,
    final_table_name: str,
    load_timeout_sec: int = DEFAULT_BQ_LOAD_TIMEOUT_SEC,
) -> bool:
    """
    Load data to a staging table, then merge into the final table.
    This reduces the number of load operations on the final table.
    """
    if df is None or df.empty:
        logging.info(f"🟡 No data to load for staging table of {final_table_name}")
        return True

    # Determine the year from the data to select appropriate schema
    year = None
    try:
        # Look for date columns in the DataFrame
        date_cols = [
            "_window_from_utc",
            "_window_to_utc",
            "settlementDate",
            "timeFrom",
            "timeTo",
        ]
        for col in date_cols:
            if col in df.columns:
                # Get the first date value and extract year
                first_date = df[col].iloc[0]
                if isinstance(first_date, pd.Timestamp) or isinstance(
                    first_date, datetime
                ):
                    year = first_date.year
                    break
                elif isinstance(first_date, str):
                    # Try to parse string date
                    try:
                        parsed_date = pd.to_datetime(first_date)
                        year = parsed_date.year
                        break
                    except:
                        # Try using schema_handler for date parsing
                        try:
                            year = get_schema_year_from_date(first_date)
                            break
                        except:
                            pass

        if not year:
            # Fallback to current year if we can't determine
            year = datetime.now().year
            logging.warning(
                f"⚠️ Could not determine year from data, using current year: {year}"
            )
        else:
            logging.info(f"🔍 Detected year {year} from data for {final_table_name}")
    except Exception as e:
        logging.warning(f"⚠️ Could not determine year from data: {e}")
        # Fallback to current year
        year = datetime.now().year

    # Extract dataset code from final_table_name (e.g., "bmrs_bod" -> "BOD")
    dataset_code = final_table_name.replace("bmrs_", "").upper()

    # Create a staging table name with timestamp to avoid conflicts
    staging_table_name = f"{final_table_name}_staging_{int(time.time())}"
    staging_table_id = f"{client.project}.{dataset_id}.{staging_table_name}"
    final_table_id = f"{client.project}.{dataset_id}.{final_table_name}"

    logging.info(
        f"⬆️ Loading {len(df)} rows to staging table {staging_table_id} (Year: {year})"
    )

    try:
        # Get schema for the specific dataset and year using schema_handler
        schema_fields = get_schema_for_dataset_and_year(dataset_code, year)

        if not schema_fields:
            logging.warning(
                f"⚠️ No schema found for {dataset_code} ({year}). Using auto-detection."
            )

        # 1. Load data to the staging table with WRITE_TRUNCATE
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",  # Always replace staging table
        )

        # Add schema if available from schema_handler
        if schema_fields:
            # Convert schema format from list of dicts to BigQuery SchemaField objects
            table_schema = []
            for field in schema_fields:
                table_schema.append(
                    bigquery.SchemaField(
                        name="column_name", field_type="STRING"  # Example arguments
                    )
                )

            job_config.schema = table_schema

        # Load the data to the staging table
        load_job = client.load_table_from_dataframe(
            df, staging_table_id, job_config=job_config
        )
        load_job.result(timeout=load_timeout_sec)

        logging.info(
            f"✅ Successfully loaded {len(df)} rows to staging table {staging_table_id}"
        )

        # 2. Merge staging table into final table
        try:
            merge_query = f"""
            MERGE `{final_table_id}` T
            USING `{staging_table_id}` S
            ON T._hash_key = S._hash_key
            WHEN MATCHED THEN
              UPDATE SET
                T.settlementDate = S.settlementDate,
                T.settlementPeriod = S.settlementPeriod,
                T.systemSellPrice = S.systemSellPrice,
                T.systemBuyPrice = S.systemBuyPrice,
                T.priceCategory = S.priceCategory,
                T._window_from_utc = S._window_from_utc,
                T._window_to_utc = S._window_to_utc,
                T._ingested_utc = S._ingested_utc
            WHEN NOT MATCHED THEN
              INSERT (
                settlementDate,
                settlementPeriod,
                systemSellPrice,
                systemBuyPrice,
                priceCategory,
                _window_from_utc,
                _window_to_utc,
                _ingested_utc
              ) VALUES (
                S.settlementDate,
                S.settlementPeriod,
                S.systemSellPrice,
                S.systemBuyPrice,
                S.priceCategory,
                S._window_from_utc,
                S._window_to_utc,
                S._ingested_utc
              )
            """
            merge_job = client.query(merge_query)
            merge_job.result(timeout=load_timeout_sec)

            logging.info(
                f"✅ Successfully merged {len(df)} rows from staging to final table {final_table_name}"
            )
        except Exception as e:
            logging.error(f"❌ Failed to merge data into final table: {e}")
            return False

        return True
    except Exception as e:
        logging.error(f"❌ Error in staging load: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Elexon BMRS Data Ingester")
    parser.add_argument(
        "--start",
        type=str,
        default=(date.today() - timedelta(days=2)).isoformat(),
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=date.today().isoformat(),
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--only",
        type=str,
        help="Comma-separated list of datasets to ingest (e.g., BOD,FUELINST)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing data in the specified date range.",
    )
    parser.add_argument(
        "--include-offline",
        action="store_true",
        help="Include datasets that are likely to be offline (e.g., MILS, MELS).",
    )
    parser.add_argument(
        "--bm-units",
        type=str,
        help="Comma-separated list of BM units to filter by (for supported datasets like MILS/MELS)",
        default=None,
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="If provided, save raw JSON/CSV responses to this directory.",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[TqdmLoggingHandler()],
    )

    global INCLUDE_OFFLINE
    if args.include_offline:
        INCLUDE_OFFLINE = True
        logging.warning("Including likely offline datasets (MILS, MELS).")

    start_dt = _parse_iso_date(args.start)
    end_dt = _parse_iso_date(args.end)

    try:
        credentials, project_id = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        client = bigquery.Client(credentials=credentials, project=project_id or BQ_PROJECT)  # type: ignore
    except google.auth.exceptions.DefaultCredentialsError:
        logging.error(
            "GCP authentication failed. Please configure credentials.", exc_info=True
        )
        sys.exit(1)

    _ensure_bq_dataset(client, BQ_DATASET)

    # Get all datasets from CHUNK_RULES
    all_datasets = sorted(list(CHUNK_RULES.keys()))

    # Filter datasets if --only is specified
    if args.only:
        only_datasets = {d.strip().upper() for d in args.only.split(",")}
        datasets_to_run = [ds for ds in all_datasets if ds in only_datasets]
    else:
        datasets_to_run = all_datasets

    # BM Units filter
    bm_units_list = (
        [u.strip() for u in args.bm_units.split(",")] if args.bm_units else None
    )

    # Main loop
    with tqdm(total=len(datasets_to_run), desc="All Datasets") as pbar_datasets:
        for dataset in datasets_to_run:
            pbar_datasets.set_description(f"Dataset: {dataset}")

            if dataset in LIKELY_OFFLINE and not INCLUDE_OFFLINE:
                logging.info(f"Skipping likely offline dataset: {dataset}")
                pbar_datasets.update(1)
                continue

            table_name = _safe_table_name("bmrs", dataset)

            # Clear the entire date range for the dataset if overwrite is enabled
            if args.overwrite:
                try:
                    logging.info(
                        f"Overwrite enabled. Clearing data for {table_name} between {start_dt} and {end_dt}"
                    )
                    clear_bq_date_range(
                        client, BQ_DATASET, table_name, start_dt, end_dt
                    )
                except Exception as e:
                    logging.error(
                        f"Failed to clear date range for {table_name}, stopping for this dataset: {e}"
                    )
                    pbar_datasets.update(1)
                    continue

            # Determine the appropriate chunk size for the dataset
            window_step = _max_window_for(dataset)

            # Create a progress bar for the time windows of the current dataset
            num_windows = (
                end_dt - start_dt
            ).total_seconds() / window_step.total_seconds()
            with tqdm(
                total=num_windows, desc=f"Windows for {dataset}", leave=False
            ) as pbar_windows:
                for window_start, window_end in _iter_windows(
                    start_dt, end_dt, window_step
                ):
                    pbar_windows.set_description(
                        f"Fetching {dataset} from {window_start.date()} to {window_end.date()}"
                    )

                    # Fetch data for the smaller window
                    try:
                        df = _fetch_bmrs(
                            dataset,
                            window_start,
                            window_end,
                            bm_units=bm_units_list,
                            data_dir=args.data_dir,
                        )
                    except Exception as e:
                        logging.error(
                            f"❌ Failed to fetch data for {dataset} in window {window_start}-{window_end}: {e}"
                        )
                        pbar_windows.update(1)
                        continue

                    if df is None or df.empty:
                        logging.info(
                            f"No data returned for {dataset} in window {window_start}-{window_end}"
                        )
                        pbar_windows.update(1)
                        continue

                    # Add metadata and generate hash key
                    df = _append_metadata_cols(df, dataset, window_start, window_end)
                    df = _generate_dedup_key(df)

                    # Load to BigQuery
                    if not df.empty:
                        try:
                            table_id = f"{client.project}.{BQ_DATASET}.{table_name}"
                            job_config = bigquery.LoadJobConfig()
                            job_config.write_disposition = "WRITE_APPEND"

                            schema = get_corrected_schema_for_dataset(dataset)
                            if schema:
                                job_config.schema = schema
                                logging.info(f"Loaded corrected schema for {dataset}")
                            else:
                                job_config.autodetect = True
                                logging.warning(
                                    f"Could not find corrected schema for {dataset}. Using autodetect."
                                )

                            load_job = client.load_table_from_dataframe(
                                df, table_id, job_config=job_config
                            )
                            load_job.result()
                            logging.info(
                                f"✅ Successfully loaded {len(df)} rows to {table_id} for window {window_start.date()}"
                            )

                        except Exception as e:
                            logging.error(
                                f"❌ Failed to load data for {dataset} in window {window_start}-{window_end}: {e}",
                                exc_info=True,
                            )

                    pbar_windows.update(1)

            pbar_datasets.update(1)

    logging.info("✅ Ingestion run completed.")


if __name__ == "__main__":
    main()
