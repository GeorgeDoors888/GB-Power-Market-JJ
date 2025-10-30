#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Elexon downloader with per-dataset chunking and robust BigQuery loads.

What this does
--------------
• Targets the BMRS REST base (stable + currently working).
• Applies per-dataset date window limits automatically:
    - BOD:           1 hour windows
    - BOAL/BOALF:    1 day windows
    - DISBSAD:       1 day windows
    - NETBSAD:       1 day windows
    - FUELINST/FREQ: 1 day windows (safe)
    - default:       7 day windows (safe for most)
• Retries each chunk a few times, then logs a SKIP with the reason.
• Always converts responses to a pandas DataFrame before loading to BigQuery
  (avoids the CSV header parsing errors you saw).
• Logs “Planned datasets …” and “SKIP (offline/params)” in a clear, compact way.

Usage
-----
python ingest_elexon_all.py --start 2016-01-01 --end 2025-08-26
python ingest_elexon_all.py --start 2025-07-01 --end 2025-07-02 --only BOD,BOAL,DISBSAD
"""

from __future__ import annotations

import argparse
import io
import logging
import os
import signal
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
from google.api_core.exceptions import BadRequest, Conflict, NotFound
from google.cloud import bigquery
from tqdm import tqdm

# ----------------------------
# Config (edit if you need to)
# ----------------------------

BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
BQ_PROJECT = "jibber-jabber-knowledge"
BQ_DATASET = "uk_energy_insights"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.5  # seconds
TIMEOUT = (10, 60)  # (connect, read) timeout in seconds
MAX_FRAMES_PER_BATCH = (
    30  # Load to BQ in batches of this many chunks to avoid single-job limits
)

# Per-dataset max window (from YAML config). Anything not listed falls back to 7 days.
CHUNK_RULES = {
    "BOD": "1h",
    "B1770": "1d",
    "BOALF": "1d",
    "NETBSAD": "1d",
    "DISBSAD": "1d",
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
    "MILS": "7d",
    "MELS": "7d",
    "MDP": "7d",
    "MDV": "7d",
    "MNZT": "7d",
    "MZT": "7d",
    "NTB": "7d",
    "NTO": "7d",
    "NDZ": "7d",
    "NONBM": "7d",
}

# Datasets that need special handling or are consistently failing
LIKELY_OFFLINE = {"MILS", "MELS"}

# --------------------------------
# Helpers
# --------------------------------


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
    cur = end
    while cur > start:
        prev = max(cur - step, start)
        yield prev, cur
        cur = prev


import pickle
import re

# ... (rest of the imports)

# Constants
# ... (rest of the constants)


def _debug_problematic_dataframe(df: pd.DataFrame, ds: str, e: Exception):
    """Saves a problematic DataFrame to disk for debugging."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = "debug_frames"
    os.makedirs(debug_dir, exist_ok=True)

    # Extract column name from the error message if possible
    error_str = str(e)
    col_name_match = re.search(
        r"Error converting Pandas column with name: \"(.*?)\"", error_str
    )
    col_name = col_name_match.group(1) if col_name_match else "unknown_column"

    # Filenames
    base_filename = f"{debug_dir}/{ds}_{col_name}_{timestamp}"
    csv_filename = f"{base_filename}.csv"
    pkl_filename = f"{base_filename}.pkl"
    log_filename = f"{base_filename}.log"

    logging.error(
        f"🚨 Debugging problematic DataFrame for dataset '{ds}'. Saving info to '{base_filename}.*'"
    )

    # Save the full DataFrame
    df.to_csv(csv_filename, index=False)
    with open(pkl_filename, "wb") as f:
        pickle.dump(df, f)

    # Write detailed log
    with open(log_filename, "w") as f:
        f.write(f"Dataset: {ds}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Original Exception: {error_str}\n\n")

        if col_name in df.columns:
            f.write(f"--- Analysis for column: {col_name} ---\n")
            f.write(f"Column Dtype: {df[col_name].dtype}\n\n")

            f.write("Value types in this column:\n")
            f.write(
                df[col_name].apply(lambda x: str(type(x))).value_counts().to_string()
            )
            f.write("\n\n")

            non_scalar = df[col_name].apply(
                lambda x: not isinstance(x, (str, int, float, bool, type(None)))
            )
            if non_scalar.any():
                f.write("Found non-scalar values:\n")
                f.write(df[col_name][non_scalar].to_string())
            else:
                f.write("No non-scalar values detected in this column.\n")
        else:
            f.write(f"Column '{col_name}' not found in DataFrame.\n")

    logging.error(
        f"🔍 Debug files saved. Please inspect '{log_filename}' for analysis."
    )


def _safe_table_name(prefix: str, dataset: str) -> str:
    # BQ table names are limited to 1024 characters and can only contain letters, numbers, or underscores.
    safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", dataset.lower())
    return f"{prefix}_{safe_name}"


def _require_gac():
    path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not path or not os.path.exists(path):
        logging.error("Missing or invalid GOOGLE_APPLICATION_CREDENTIALS")
        logging.error("Expected existing file at: %r", path or "<not set>")
        sys.exit(2)


def _ensure_bq_dataset(client: bigquery.Client, dataset_id: str) -> None:
    fq = f"{client.project}.{dataset_id}"
    try:
        client.get_dataset(fq)
        logging.info("BigQuery dataset %r exists.", dataset_id)
    except NotFound:
        ds = bigquery.Dataset(fq)
        ds.location = "EU"
        client.create_dataset(ds)
        logging.info("Created BigQuery dataset %r.", dataset_id)


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


def _csv_to_df(text: str) -> pd.DataFrame:
    # Some endpoints return CSV; use pandas to read.
    if not text or not text.strip():
        return pd.DataFrame()
    return pd.read_csv(io.StringIO(text))


def _fetch_bmrs(dataset: str, from_dt: datetime, to_dt: datetime) -> pd.DataFrame:
    logging.info(f"🌐 Fetching BMRS dataset={dataset} from={from_dt} to={to_dt}")
    """
    Fetch a single window from BMRS dataset.
    We try JSON first (if supported), then CSV as a fallback.
    """
    params = {
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
    }
    url = f"{BMRS_BASE}/{dataset.upper()}"
    # Attempt JSON first
    try:
        rj = requests.get(
            url, params=params, timeout=TIMEOUT, headers={"Accept": "application/json"}
        )
        if rj.status_code == 404:
            # Offline or not supported here
            return pd.DataFrame()
        rj.raise_for_status()
        # If that endpoint serves JSON, flatten:
        try:
            payload = rj.json()
        except ValueError:
            payload = None
        if payload is not None:
            df = _flatten_json_payload(payload)
            if not df.empty:
                return df
    except requests.HTTPError as e:
        # If validation error mentions range, just surface upward (chunker handles it)
        if rj is not None and rj.status_code in (400, 422):
            raise
        # Continue to CSV fallback for other codes
    except Exception:
        pass

    # CSV fallback
    rc = requests.get(
        url,
        params={**params, "format": "csv"},
        timeout=TIMEOUT,
        headers={"Accept": "text/csv"},
    )
    if rc.status_code == 404:
        return pd.DataFrame()
    rc.raise_for_status()
    return _csv_to_df(rc.text)


def _append_metadata_cols(
    df: pd.DataFrame, dataset: str, from_dt: datetime, to_dt: datetime
) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    df = df.copy()

    # Store original column names for tracking schema changes
    original_columns = list(df.columns)

    # Add standard metadata
    df["_dataset"] = dataset.upper()
    df["_window_from_utc"] = from_dt.replace(tzinfo=timezone.utc).isoformat()
    df["_window_to_utc"] = to_dt.replace(tzinfo=timezone.utc).isoformat()
    df["_ingested_utc"] = datetime.now(timezone.utc).isoformat()

    # Add schema metadata
    df["_original_columns"] = str(original_columns)
    df["_source_format"] = "BMRS API"
    df["_source_version"] = "1.0"  # You can update this if the API version changes

    return df


# This function has been replaced with a more robust approach that uses source data as the source of truth
# and tracks schema changes in metadata columns.
def _ensure_schema_matches(client: bigquery.Client, df: pd.DataFrame, table_id: str):
    """Deprecated: This function is kept for backward compatibility but is no longer used."""
    logging.info(
        f"Schema matching bypassed for {table_id} - using source data as source of truth."
    )
    return


def _clear_bq_date_range(
    client: bigquery.Client,
    dataset_id: str,
    table_name: str,
    start: datetime,
    end: datetime,
) -> None:
    """Deletes rows from a BQ table within a given date range based on our metadata col."""
    table_id = f"{client.project}.{dataset_id}.{table_name}"
    logging.warning(
        "🔥 Deleting data from %s for range %s to %s",
        table_id,
        start.isoformat(),
        end.isoformat(),
    )

    # Check if table exists first
    try:
        client.get_table(table_id)
    except Exception:
        logging.info("Table %s does not exist, skipping delete.", table_id)
        return

    query = f"""
    DELETE FROM `{table_id}`
    WHERE TIMESTAMP(_window_from_utc) >= @start_ts AND TIMESTAMP(_window_from_utc) < @end_ts
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_ts", "TIMESTAMP", start),
            bigquery.ScalarQueryParameter("end_ts", "TIMESTAMP", end),
        ]
    )
    query_job = client.query(query, job_config=job_config)
    query_job.result()  # Wait for completion
    logging.info("✅ Delete complete for %s.", table_id)


def _sanitize_df_for_bq(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitizes a DataFrame for BigQuery loading by ensuring data types are compatible.
    - Converts 'object' columns to 'string' to handle mixed types.
    - Explicitly handles special fields with known types.
    - Ensures `_window_from_utc` remains a `TIMESTAMP`.
    - Ensures metadata columns are handled consistently.
    """
    df = df.copy()

    # Store original schema information for metadata tracking
    schema_before = {col: str(df[col].dtype) for col in df.columns}

    for col in df.columns:
        if col == "elbow2" or col == "elbow3":
            logging.info(f"Ensuring column '{col}' is treated as STRING.")
            df[col] = df[col].astype(str)
        elif col == "_window_from_utc":
            logging.info(
                f"Ensuring column '{col}' is treated as STRING to avoid type conflicts."
            )
            # Convert to string format instead of timestamp to avoid schema conflicts
            if isinstance(df[col].iloc[0], (str)):
                pass  # Already a string, leave it
            else:
                df[col] = df[col].dt.strftime("%Y-%m-%dT%H:%M:%S%z")
        elif col == "rate2":
            logging.info(f"Ensuring column '{col}' remains as FLOAT.")
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif df[col].dtype == "object":
            logging.info(
                f"Sanitizing column '{col}' (dtype: object) by converting to string."
            )
            df[col] = df[col].astype(str)

    # Add schema change tracking metadata
    schema_after = {col: str(df[col].dtype) for col in df.columns}
    df["_schema_before"] = str(schema_before)
    df["_schema_after"] = str(schema_after)

    return df


def _load_dataframe(
    client: bigquery.Client,
    df: pd.DataFrame,
    dataset_id: str,
    table_name: str,
    write_disposition: str = "WRITE_APPEND",
) -> None:
    if df is None or df.empty:
        logging.info(f"🟡 No data to load for {table_name}")
        return
    table_id = f"{client.project}.{dataset_id}.{table_name}"
    logging.info(
        f"⬆️ Loading {len(df)} rows to {table_id} (write_disposition={write_disposition})"
    )

    # Add a deduplication key to help identify duplicates
    if "_dedup_key" not in df.columns:
        try:
            # Create a deterministic deduplication key from source data fields
            # This will help identify duplicates even if they arrive with different metadata
            key_cols = [col for col in df.columns if not col.startswith("_")]
            if key_cols:
                df["_dedup_key"] = (
                    df[key_cols]
                    .apply(
                        lambda row: hash(tuple(str(row[c]) for c in key_cols)), axis=1
                    )
                    .astype(str)
                )
            else:
                # Fallback if no non-metadata columns exist
                df["_dedup_key"] = pd.util.hash_pandas_object(df).astype(str)
        except Exception as e:
            logging.warning(f"⚠️ Failed to create deduplication key: {e}")
            # Continue without the key

    # Define schema based on what's in the DataFrame - source data as source of truth
    schema = []
    for col_name, dtype in df.dtypes.items():
        # Default to STRING for any type that isn't cleanly mappable
        bq_type = "STRING"
        if pd.api.types.is_integer_dtype(dtype):
            bq_type = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            bq_type = "FLOAT"
        elif pd.api.types.is_bool_dtype(dtype):
            bq_type = "BOOLEAN"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            bq_type = "TIMESTAMP"

        schema.append(bigquery.SchemaField(str(col_name), bq_type))

    logging.debug(
        f"Defined BQ schema for {table_name} from DataFrame: {len(schema)} columns"
    )

    # Create a temporary table for new data
    temp_table_id = f"{table_id}_temp_{int(time.time())}"

    # Check if the main table exists
    table_exists = True
    try:
        client.get_table(table_id)
    except NotFound:
        table_exists = False
        logging.info(f"Target table {table_id} does not exist, will be created.")

    # Load data to temporary table first
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",  # Always overwrite the temp table
        schema=schema,
    )

    # Load via DataFrame to temp table
    try:
        temp_load_job = client.load_table_from_dataframe(
            df, temp_table_id, job_config=job_config
        )
        temp_load_job.result()
        logging.info(f"✅ Data loaded to temporary table {temp_table_id}")
    except Exception as e:
        logging.error(f"❌ Failed to load to temporary table: {e}")
        return

    # If target table doesn't exist, just rename the temp table
    if not table_exists:
        # Create a copy job to move the temp table to the final destination
        copy_job_config = bigquery.CopyJobConfig()
        copy_job = client.copy_table(
            temp_table_id, table_id, job_config=copy_job_config
        )
        copy_job.result()
        logging.info(f"✅ Temporary table renamed to {table_id}")
        # Delete the temp table (no longer needed)
        client.delete_table(temp_table_id)
        return

    # Otherwise, merge data using a deduplication strategy
    merge_query = f"""
    MERGE `{table_id}` T
    USING `{temp_table_id}` S
    ON T._dedup_key = S._dedup_key AND T._dataset = S._dataset
    WHEN MATCHED THEN
      UPDATE SET {", ".join([f"T.{col} = S.{col}" for col in df.columns])}
    WHEN NOT MATCHED THEN
      INSERT ({", ".join([f"{col}" for col in df.columns])})
      VALUES ({", ".join([f"S.{col}" for col in df.columns])})
    """

    try:
        merge_job = client.query(merge_query)
        merge_job.result()
        logging.info(f"✅ Data merged into {table_id} with deduplication")
    except Exception as e:
        logging.error(f"❌ Failed to merge data: {e}")
        logging.warning(f"⚠️ Falling back to direct load to final table")

        # Fall back to direct load if merge fails
        direct_job_config = bigquery.LoadJobConfig(
            write_disposition=write_disposition,
            schema=schema,
        )
        direct_load_job = client.load_table_from_dataframe(
            df, table_id, job_config=direct_job_config
        )
        direct_load_job.result()
        logging.info(f"✅ Direct load complete for {table_id} (fallback method)")

    # Clean up temporary table
    try:
        client.delete_table(temp_table_id)
    except Exception as e:
        logging.warning(f"⚠️ Failed to delete temporary table {temp_table_id}: {e}")

    logging.info(f"✅ Load complete for {table_id}")


@dataclass
class IngestResult:
    dataset: str
    status: str
    rows: int = 0
    note: str = ""
    endpoint: str = "BMRS"


def ingest_dataset(
    client: bigquery.Client,
    dataset: str,
    start: datetime,
    end: datetime,
    dataset_id: str = BQ_DATASET,
    overwrite: bool = False,
) -> IngestResult:
    ds = dataset.upper()

    if ds in LIKELY_OFFLINE:
        return IngestResult(
            dataset=ds, status="SKIP", rows=0, note="offline/params", endpoint="BMRS"
        )

    window = _max_window_for(ds)
    if ds == "RDRI":
        table_name = "bmrs_rdri_new"  # Use the new table for RDRI
    else:
        table_name = _safe_table_name("bmrs", ds)

    existing_windows = set()
    if overwrite:
        logging.info(f"🧹 Overwrite enabled, clearing BQ date range for {table_name}")
        try:
            _clear_bq_date_range(client, dataset_id, table_name, start, end)
        except Exception as e:
            logging.error("❌ %s: Failed to clear date range: %s", ds, e)
            return IngestResult(
                dataset=ds,
                status="ERR",
                rows=0,
                note=f"BQ clear failed: {e}",
                endpoint="BMRS",
            )
    else:
        logging.info(f"🔄 Checking for existing windows for {table_name}")
        # Resuming: find out what's already there
        existing_windows = _get_existing_windows(
            client, dataset_id, table_name, start, end
        )

    frames_batch: List[pd.DataFrame] = []
    failed_windows = 0
    total_rows_loaded = 0
    any_data_loaded = False

    all_windows = list(_iter_windows(start, end, window))
    # Correctly filter out windows that have already been ingested
    windows_to_fetch = [
        (w_from, w_to)
        for w_from, w_to in all_windows
        if overwrite or w_from.isoformat() not in existing_windows
    ]

    if not windows_to_fetch:
        if not overwrite:
            logging.info("✅ %s: already complete, skipping.", ds)
            # Return OK but with 0 rows, as no new work was done.
            return IngestResult(
                dataset=ds, status="OK", rows=0, note="Already complete"
            )
        return IngestResult(
            dataset=ds, status="SKIP", rows=0, note="No windows in date range"
        )

    logging.info(f"🧮 Total windows to fetch for {ds}: {len(windows_to_fetch)}")
    for w_from, w_to in tqdm(
        windows_to_fetch, desc=f"  - {ds} ({window})", leave=False, unit="chunk"
    ):
        logging.debug(f"➡️ Processing window {w_from} to {w_to} for {ds}")
        # retry loop
        last_err = None
        for attempt in range(1, MAX_RETRIES + 1):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(
                int(TIMEOUT[1] + 30)
            )  # Set alarm for read timeout + 30s buffer
            try:
                df = _fetch_bmrs(ds, w_from, w_to)
                if df is not None and not df.empty:
                    df = _append_metadata_cols(df, ds, w_from, w_to)
                    frames_batch.append(df)
                last_err = None  # Clear error on success or empty response
                break  # success (or empty) – leave retry loop
            except TimeoutException:
                last_err = TimeoutException(f"Hard timeout after {TIMEOUT[1] + 30}s")
                logging.error(
                    f"❌ {ds}: window {w_from}..{w_to} hit hard timeout. URL was likely {BMRS_BASE}/{ds.upper()}?from={w_from.isoformat()}&to={w_to.isoformat()}"
                )
                # This is a hard failure for this chunk, break the retry loop
                break
            except requests.HTTPError as e:
                last_err = e
                # Validation errors that mention window size won’t be fixed by retry; abort early.
                if getattr(e.response, "status_code", None) in (400, 422):
                    logging.error(
                        "❌ %s: window %s..%s rejected by API: %s",
                        ds,
                        w_from,
                        w_to,
                        str(e),
                    )
                    break
                time.sleep(RETRY_BACKOFF * attempt)  # exponential-ish backoff
            except Exception as e:
                last_err = e
                time.sleep(RETRY_BACKOFF * attempt)
            finally:
                signal.alarm(0)  # Disable the alarm

        if last_err:
            failed_windows += 1
            # Continue to next window; we will mark partial success later.
            logging.error(
                "⚠️  %s: failed window %s..%s after retries: %s",
                ds,
                w_from,
                w_to,
                last_err,
            )

        # Load to BQ if batch is full
        if len(frames_batch) >= MAX_FRAMES_PER_BATCH:
            logging.info(
                f"📦 Batch full ({len(frames_batch)} frames), loading to BQ for {ds}"
            )
            try:
                batch_df = pd.concat(frames_batch, ignore_index=True)
                batch_df = _sanitize_df_for_bq(batch_df)
                _load_dataframe(
                    client,
                    batch_df,
                    dataset_id,
                    table_name,
                    write_disposition="WRITE_APPEND",
                )
                total_rows_loaded += len(batch_df.index)
                any_data_loaded = True
                frames_batch.clear()
            except Exception as e:
                if "pyarrow" in str(e):
                    _debug_problematic_dataframe(batch_df, ds, e)
                logging.error("❌ %s: BigQuery sub-batch load failed: %s", ds, e)
                # This is a fatal error for this dataset, so we stop.
                return IngestResult(
                    dataset=ds,
                    status="ERR",
                    rows=total_rows_loaded,
                    note=f"BQ load failed: {e}",
                    endpoint="BMRS",
                )

    # Load any remaining frames
    if frames_batch:
        logging.info(
            f"📦 Loading final batch ({len(frames_batch)} frames) to BQ for {ds}"
        )
        try:
            batch_df = pd.concat(frames_batch, ignore_index=True)
            batch_df = _sanitize_df_for_bq(batch_df)
            _load_dataframe(
                client,
                batch_df,
                dataset_id,
                table_name,
                write_disposition="WRITE_APPEND",
            )
            total_rows_loaded += len(batch_df.index)
            any_data_loaded = True
            frames_batch.clear()
        except Exception as e:
            if "pyarrow" in str(e):
                _debug_problematic_dataframe(batch_df, ds, e)
            logging.error("❌ %s: BigQuery final batch load failed: %s", ds, e)
            # Even if the final batch fails, some data might have been loaded.
            # The status will be determined by the presence of any loaded data.
            status = "PARTIAL" if any_data_loaded else "ERR"
            return IngestResult(
                dataset=ds,
                status=status,
                rows=total_rows_loaded,
                note=f"BQ final load failed: {e}",
                endpoint="BMRS",
            )
            return IngestResult(
                dataset=ds,
                status="ERR",
                rows=total_rows_loaded,
                note=f"BQ load failed: {e}",
                endpoint="BMRS",
            )

    status = "OK" if failed_windows == 0 else "PARTIAL"
    note = f"{failed_windows} windows failed" if failed_windows > 0 else ""
    logging.info(
        f"🏁 Finished ingest for {ds}: status={status}, rows={total_rows_loaded}, note={note}"
    )
    return IngestResult(
        dataset=ds, status=status, rows=total_rows_loaded, note=note, endpoint="BMRS"
    )


# --------------------------------
# Main
# --------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Elexon BMRS chunked downloader → BigQuery"
    )
    parser.add_argument(
        "--start", required=True, help="ISO date (YYYY-MM-DD) or full ISO8601"
    )
    parser.add_argument(
        "--end",
        required=True,
        help="ISO date (YYYY-MM-DD) or full ISO8601 (exclusive upper bound is fine)",
    )
    parser.add_argument(
        "--only",
        default="",
        help="Comma-separated dataset codes, e.g. BOD,BOAL,DISBSAD",
    )
    parser.add_argument("--project", default=BQ_PROJECT, help="BigQuery project id")
    parser.add_argument("--dataset", default=BQ_DATASET, help="BigQuery dataset id")
    parser.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="If set, delete data in the given date range before loading.",
    )
    args = parser.parse_args()

    # Use TQDM-aware logger
    log = logging.getLogger()
    log.setLevel(getattr(logging, args.log_level))
    handler = TqdmLoggingHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)

    _require_gac()

    start = _parse_iso_date(args.start)
    end = _parse_iso_date(args.end)
    if end <= start:
        logging.error("End must be after start.")
        sys.exit(2)

    client = bigquery.Client(project=args.project)
    logging.info("✅ Initialized BigQuery Client for project: %s", client.project)

    _ensure_bq_dataset(client, args.dataset)

    # Build dataset list
    if args.only.strip():
        wanted = [s.strip().upper() for s in args.only.split(",") if s.strip()]
    else:
        # Ingest all datasets from insights_datasets.csv
        wanted = [
            "METADATA",
            "BOAL",
            "BOD",
            "DISBSAD",
            "FOU2T14D",
            "FOU2T3YW",
            "FOUT2T14D",
            "FREQ",
            "FUELHH",
            "FUELINST",
            "IMBALNGC",
            "INDDEM",
            "INDGEN",
            "INDO",
            "ITSDO",
            "MELNGC",
            "MID",
            "MILS",
            "MELS",
            "MDP",
            "MDV",
            "MNZT",
            "MZT",
            "NETBSAD",
            "NDF",
            "NDFD",
            "NDFW",
            "NONBM",
            "NOU2T14D",
            "NOU2T3YW",
            "NTB",
            "NTO",
            "NDZ",
            "OCNMF3Y",
            "OCNMF3Y2",
            "OCNMFD",
            "OCNMFD2",
            "PN",
            "QAS",
            "QPN",
            "RDRE",
            "RDRI",
            "RURE",
            "RURI",
            "SEL",
            "SIL",
            "TEMP",
            "TSDF",
            "TSDFD",
            "TSDFW",
            "UOU2T14D",
            "UOU2T3YW",
            "WINDFOR",
        ]

    # Move UOU2T3YW to the end if present, to avoid blocking other datasets
    if "UOU2T3YW" in wanted:
        wanted = [ds for ds in wanted if ds != "UOU2T3YW"] + ["UOU2T3YW"]

    # Log the planned list
    logging.info("📝 Planned datasets (%d): %s", len(wanted), ", ".join(wanted))
    logging.info("🚀 Starting ingestion for %d datasets...", len(wanted))

    results: List[IngestResult] = []
    for ds in tqdm(wanted, desc="Overall Progress", unit="dataset"):
        try:
            # logging.info("📥 Fetching %s ...", ds)
            res = ingest_dataset(
                client,
                ds,
                start,
                end,
                dataset_id=args.dataset,
                overwrite=args.overwrite,
            )
            if res.status == "OK":
                logging.info("✅ %s: loaded %d rows", ds, res.rows)
            elif res.status == "PARTIAL":
                logging.warning(
                    "⚠️  %s: PARTIAL load, %d rows (%s)", ds, res.rows, res.note
                )
            elif res.status == "SKIP":
                logging.info("⏭️  %s: SKIP (%s)", ds, res.note or "offline/params")
            else:
                logging.error("❌ %s: %s", ds, res.note or "failed")
            results.append(res)
        except Exception as e:
            logging.error("❌ %s: unexpected error: %s", ds, e)
            results.append(IngestResult(dataset=ds, status="ERR", rows=0, note=str(e)))

    # Summary
    ok = sum(1 for r in results if r.status == "OK")
    partial = sum(1 for r in results if r.status == "PARTIAL")
    skipped = [r.dataset for r in results if r.status == "SKIP"]
    failed = [r for r in results if r.status == "ERR"]
    logging.info("🎉 All datasets processed.")
    logging.info(
        "   OK=%d, PARTIAL=%d, SKIP=%d, ERR=%d", ok, partial, len(skipped), len(failed)
    )
    if skipped:
        logging.info("   SKIPPED: %s", ", ".join(skipped))
    if failed:
        logging.info(
            "   ERR: %s", ", ".join(f"{r.dataset}({r.note})" for r in failed if r.note)
        )


if __name__ == "__main__":
    main()
