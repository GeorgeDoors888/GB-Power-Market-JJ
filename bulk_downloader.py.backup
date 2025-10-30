#!/usr/bin/env python3
import argparse
import asyncio
import hashlib
import httpx
import json
import math
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

from google.api_core.exceptions import BadRequest, Conflict, NotFound
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from google.cloud import bigquery

# ---- BigQuery schema helpers (nested-aware, robust) ----
_table_locks: dict[str, asyncio.Lock] = {}


def _fq_table_id(table_id: str, default_project: str | None) -> str:
    if table_id.count(".") == 2:
        return table_id
    return f"{default_project}.{table_id}" if default_project else table_id


def _scalar_type(v: Any) -> str:
    if isinstance(v, bool):
        return "BOOL"
    if isinstance(v, int):
        return "INT64"
    if isinstance(v, float):
        return "FLOAT64"
    return "STRING"


def _infer_field(name: str, value: Any) -> bigquery.SchemaField:
    if isinstance(value, dict):
        subfields = [_infer_field(k, v) for k, v in value.items()]
        return bigquery.SchemaField(name, "RECORD", mode="NULLABLE", fields=subfields)
    if isinstance(value, list):
        elem = next((e for e in value if e is not None), None)
        if elem is None:
            return bigquery.SchemaField(name, "STRING", mode="REPEATED")
        if isinstance(elem, dict):
            subfields = [_infer_field(k, v) for k, v in elem.items()]
            return bigquery.SchemaField(name, "RECORD", mode="REPEATED", fields=subfields)
        return bigquery.SchemaField(name, _scalar_type(elem), mode="REPEATED")
    return bigquery.SchemaField(name, _scalar_type(value), mode="NULLABLE")


def _infer_schema(sample: dict) -> list[bigquery.SchemaField]:
    if not sample:
        return []
    return [_infer_field(k, v) for k, v in sample.items()]


def _merge_fields(existing: bigquery.SchemaField, wanted: bigquery.SchemaField) -> bigquery.SchemaField:
    if existing.field_type != "RECORD" or wanted.field_type != "RECORD":
        return existing
    have = {f.name: f for f in existing.fields}
    out_children = []
    for wf in wanted.fields:
        if wf.name in have:
            out_children.append(_merge_fields(have[wf.name], wf))
        else:
            out_children.append(wf)
    existing_only = [f for n, f in have.items() if n not in {c.name for c in out_children}]
    merged_children = list(existing_only) + out_children
    return bigquery.SchemaField(
        name=existing.name,
        field_type="RECORD",
        mode=existing.mode,
        fields=merged_children,
    )


def _add_missing(
    existing: list[bigquery.SchemaField], wanted: list[bigquery.SchemaField]
) -> list[bigquery.SchemaField]:
    have = {f.name: f for f in existing}
    merged: list[bigquery.SchemaField] = []
    for wf in wanted:
        if wf.name in have:
            merged.append(_merge_fields(have[wf.name], wf))
        else:
            merged.append(wf)
    for name, ef in have.items():
        if name not in {f.name for f in merged}:
            merged.append(ef)
    return merged


DEFAULT_CONCURRENCY = int(os.getenv("INSIGHTS_CONCURRENCY", "6"))
BQ_PROJECT = os.getenv("BQ_PROJECT", "jibber-jabber-knowledge")
BQ_DATASET = os.getenv("BQ_DATASET", "uk_energy_prod_test")
BQ_LOCATION = os.getenv("BQ_LOCATION", "EU")
BASE_URL_FALLBACK = "https://data.elexon.co.uk/bmrs/api/v1"


def ensure_bq_table(client, table_id, sample_row, default_project=None):
    """Ensure BigQuery table exists and schema matches sample row."""
    fq = table_id if table_id.count(".") == 2 else f"{default_project}.{table_id}"
    try:
        table = client.get_table(fq)
        existing_fields = {f.name for f in table.schema}
        new_fields = []
        for k, v in sample_row.items():
            if k not in existing_fields:
                new_fields.append(bigquery.SchemaField(k, _infer_bq_type(v)))
        if new_fields:
            print(f"[SCHEMA] Updating schema for {fq}: +{[f.name for f in new_fields]}")
            table.schema = table.schema + new_fields
            table = client.update_table(table, ["schema"])
        return table
    except NotFound:
        schema = [bigquery.SchemaField(k, _infer_bq_type(v)) for k, v in sample_row.items()]
        table = bigquery.Table(fq, schema=schema)
        table = client.create_table(table)
        print(f"[CREATE] Created table {fq} with schema {[f.name for f in schema]}")
        return table


def _infer_bq_type(v):
    if isinstance(v, bool):
        return "BOOL"
    if isinstance(v, int):
        return "INT64"
    if isinstance(v, float):
        return "FLOAT64"
    if isinstance(v, dict):
        return "JSON"
    return "STRING"


async def fetch_dataset(http, base_url, cfg, start, end, auth=None, on_redirect="error"):
    """Fetch dataset with optional windowing."""
    route = cfg["route"]
    window_days = cfg.get("window_days", None)
    rows = []

    if window_days:
        # Loop in windows
        cursor = start
        while cursor < end:
            window_end = min(cursor + timedelta(days=window_days), end)
            chunk = await _fetch_once(http, base_url, route, cursor, window_end, auth, on_redirect)
            rows.extend(chunk)
            cursor = window_end
            await asyncio.sleep(0.2)  # small politeness delay
    else:
        rows = await _fetch_once(http, base_url, route, start, end, auth, on_redirect)

    return rows


async def _fetch_once(http, base_url, route, start, end, auth, on_redirect):
    params = {
        "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "format": "json",
    }
    r = await http.get(f"{base_url}{route}", params=params, auth=auth)
    if r.status_code in (301, 302):
        if on_redirect == "skip":
            print(f"[SKIP] Redirected {route} → {r.headers.get('location')}")
            return []
        elif on_redirect == "follow":
            new_url = r.headers.get("location")
            r = await http.get(new_url, auth=auth)
        else:
            raise RuntimeError(f"Endpoint moved: {r.url} → {r.headers.get('location')}")
    r.raise_for_status()
    js = r.json()
    return js.get("data", js)


async def worker(code, cfg, http, bq, base_url, start, end, default_project, auth=None, on_redirect="error"):
    """Worker to fetch dataset and upload to BigQuery."""
    rows = await fetch_dataset(http, base_url, cfg, start, end, auth, on_redirect)
    if not rows:
        print(f"[SKIP] {code}: no rows")
        return

    table_id = cfg["table"]
    fq = table_id if table_id.count(".") == 2 else f"{default_project}.{table_id}"

    # Ensure table exists and schema is correct
    ensure_bq_table(bq, table_id, rows[0], default_project=default_project)

    # Insert rows
    errors = bq.insert_rows_json(fq, rows)
    if errors:
        raise RuntimeError(f"BigQuery insert errors for {code}: {errors}")
    print(f"[OK] {code}: {len(rows)} rows {fq}")


async def main():
    # ---- Auth and HTTP setup ----
    auth = None
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Auto-authenticate if running on Google Cloud
        credentials = service_account.Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        )
        credentials.refresh(Request())
        auth = credentials
    else:
        # Otherwise, use service account key file
        key_path = os.getenv("SERVICE_ACCOUNT_FILE")
        if key_path and os.path.exists(key_path):
            credentials = service_account.Credentials.from_service_account_file(key_path)
            credentials.refresh(Request())
            auth = credentials
        else:
            print("No valid authentication method found.")
            sys.exit(1)

    async with httpx.AsyncClient() as http:
        # ---- Manifest loading ----
        manifest_path = os.getenv("MANIFEST_PATH", "manifest.json")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # ---- Dataset selection ----
        selected = {}
        available = [k for k in manifest.keys()]
        if args.datasets:
            requested = [c.strip().upper() for c in args.datasets]
            missing = [c for c in requested if c not in manifest]
            if missing:
                print("ERROR: No dataset codes matched for: " + ", ".join(missing))
                print("Available codes:\n  - " + "\n  - ".join(available))
                sys.exit(1)
            selected = {c: manifest[c] for c in requested}
        else:
            selected = dict(manifest)

        sem = asyncio.Semaphore(DEFAULT_CONCURRENCY)

        async def worker(code, cfg):
            async with sem:
                # Print sample row and schema for debugging if table creation fails
                table = cfg.get("table") or cfg.get("bq_table") or f"uk_energy_prod.{code.lower()}"
                start_str = args.start_date
                end_str = args.end_date
                rows = await fetch_dataset(
                    http, str(base_url), cfg, start_str, end_str, auth=auth, on_redirect=args.on_redirect
                )
                if code in ("SYSTEM_WARNINGS", "INDO", "SYSTEM_FREQUENCY"):
                    print(f"[DEBUG] Sample row for {code}: {rows[0] if rows else None}")
                    from google.cloud import bigquery as _bq

                    def to_bq_type(v):
                        if isinstance(v, bool):
                            return "BOOL"
                        if isinstance(v, int):
                            return "INT64"
                        if isinstance(v, float):
                            return "FLOAT64"
                        if isinstance(v, dict):
                            return "JSON"
                        return "STRING"

                    schema = [_bq.SchemaField(k, to_bq_type(v)) for k, v in (rows[0] or {}).items()]
                    print(f"[DEBUG] Inferred schema for {code}: {[(f.name, f.field_type) for f in schema]}")
                if not rows:
                    print(f"[SKIP] {code}: no rows")
                    return
                id_fields = cfg.get("id_fields") or cfg.get("id_keys")
                # Only call ensure_bq_table and bq_stream_rows if rows is not empty
                await ensure_bq_table(bq, table, rows[0], default_project=default_project)
                bq_stream_rows(bq, table, code, rows, id_fields=id_fields, default_project=default_project)
                fq = _fq_table_id(table, default_project)
                print(f"[OK] {code}: {len(rows)} rows {fq}")

        await asyncio.gather(*(worker(code, cfg) for code, cfg in selected.items()))


# Argument parsing setup
parser = argparse.ArgumentParser(description="Bulk Downloader Script")
parser.add_argument("--datasets", nargs="*", help="List of datasets to process")
parser.add_argument("--start-date", required=True, help="Start date in YYYY-MM-DD format")
parser.add_argument("--end-date", required=True, help="End date in YYYY-MM-DD format")
parser.add_argument("--on-redirect", choices=["skip", "follow", "error"], default="error", help="Action on redirect")
args = parser.parse_args()

# Ensure GOOGLE_APPLICATION_CREDENTIALS is set to a valid path
service_account_path = "/Users/georgemajor/service-account-key.json"  # Update this path as needed
if not os.path.exists(service_account_path):
    raise FileNotFoundError(f"Service account key file not found at {service_account_path}")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path

# Initialize BigQuery client with the service account credentials
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(service_account_path)
bq = bigquery.Client(credentials=credentials)


def bq_stream_rows(bq, table, code, rows, id_fields=None, default_project=None):
    # Placeholder for the actual implementation of bq_stream_rows
    pass


# Define missing variables
base_url = "https://api.example.com"  # Replace with the actual base URL
default_project = "jibber-jabber-knowledge"  # Replace with your Google Cloud project ID

if __name__ == "__main__":
    asyncio.run(main())
