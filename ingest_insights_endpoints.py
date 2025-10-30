#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import copy
import io
import itertools
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import requests
import yaml
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from tqdm import tqdm

# --- Config ---
MAX_RETRIES = 3
RETRY_BACKOFF = 2.5  # seconds
TIMEOUT = (10, 120)  # (connect, read) timeout in seconds
MAX_FRAMES_PER_BATCH = 90  # Load to BQ in batches of this many chunks


# --- Helpers ---
def _log():
    return logging.getLogger(__name__)


class TqdmLoggingHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg, file=sys.stderr)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def _parse_iso_date(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except ValueError:
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


def _iter_windows(
    start: datetime, end: datetime, step: timedelta
) -> Iterable[Tuple[datetime, datetime]]:
    cur = start
    while cur < end:
        nxt = min(cur + step, end)
        yield cur, nxt
        cur = nxt


def _flatten_json_payload(obj, records_path: Optional[str]) -> pd.DataFrame:
    if obj is None:
        return pd.DataFrame()
    if records_path:
        data = obj.get(records_path, [])
        return pd.json_normalize(data)
    if isinstance(obj, list):
        return pd.json_normalize(obj)
    if isinstance(obj, dict):
        for key in ["data", "items", "records", "rows", "results", "features"]:
            if key in obj and isinstance(obj[key], list):
                return pd.json_normalize(obj[key])
        return pd.json_normalize([obj])
    return pd.DataFrame()


def _csv_to_df(text: str) -> pd.DataFrame:
    if not text or not text.strip():
        return pd.DataFrame()
    # Handle potential JSON-in-CSV by checking first line
    if text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
            return _flatten_json_payload(data, None)
        except json.JSONDecodeError:
            pass  # Fallback to CSV
    return pd.read_csv(io.StringIO(text))


def _fetch_endpoint(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    fmt: str,
    records_path: Optional[str],
) -> pd.DataFrame:
    r = requests.get(url, params=params, timeout=TIMEOUT, headers=headers)
    r.raise_for_status()
    if fmt == "json":
        return _flatten_json_payload(r.json(), records_path)
    return _csv_to_df(r.text)


def _append_metadata(
    df: pd.DataFrame,
    table_name: str,
    from_dt: datetime,
    to_dt: datetime,
    params: Dict[str, Any],
) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["_table"] = table_name
    df["_window_from_utc"] = from_dt.replace(tzinfo=timezone.utc)
    df["_window_to_utc"] = to_dt.replace(tzinfo=timezone.utc)
    df["_ingested_utc"] = datetime.now(timezone.utc)
    for k, v in params.items():
        if k not in ["from", "to", "format"]:
            df[f"_param_{k}"] = v
    return df


def _load_dataframe(
    client: bigquery.Client,
    df: pd.DataFrame,
    project: str,
    dataset: str,
    table_name: str,
):
    if df.empty:
        _log().info(f"No data to load for {table_name}")
        return
    table_id = f"{project}.{dataset}.{table_name}"
    _log().info(f"Loading {len(df)} rows to {table_id}")
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND", autodetect=True
    )
    load_job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    load_job.result()
    _log().info(f"Load complete for {table_id}")


def _ensure_dataset_exists(client: bigquery.Client, project: str, dataset: str):
    dataset_id = f"{project}.{dataset}"
    try:
        client.get_dataset(dataset_id)
        _log().info(f"BigQuery dataset '{dataset_id}' already exists.")
    except NotFound:
        _log().info(f"Creating BigQuery dataset '{dataset_id}'...")
        client.create_dataset(dataset_id)
        _log().info(f"Dataset '{dataset_id}' created.")


def _get_existing_param_windows(
    client: bigquery.Client,
    project: str,
    dataset: str,
    table: str,
    from_dt: datetime,
    to_dt: datetime,
    param_key: Optional[str],
) -> Dict[Any, set]:
    table_id = f"{project}.{dataset}.{table}"
    windows = {}
    try:
        client.get_table(table_id)
    except NotFound:
        return windows

    if not param_key:
        # If there's no parameter to check, just get the window start times
        query = f"""
        SELECT DISTINCT _window_from_utc
        FROM `{table_id}`
        WHERE _window_from_utc >= @start AND _window_from_utc < @end
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start", "TIMESTAMP", from_dt),
                bigquery.ScalarQueryParameter("end", "TIMESTAMP", to_dt),
            ]
        )
        try:
            # For no params, we use a special key `None` in our dictionary
            windows[None] = {
                row[0]
                for row in client.query(query, job_config=job_config).result()
                if row[0] is not None
            }
        except Exception as e:
            _log().warning(f"Could not query existing windows for {table}: {e}")
        return windows

    # If there is a parameter, query for both window and param value
    query = f"""
    SELECT DISTINCT _window_from_utc, _param_{param_key}
    FROM `{table_id}`
    WHERE _window_from_utc >= @start AND _window_from_utc < @end
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start", "TIMESTAMP", from_dt),
            bigquery.ScalarQueryParameter("end", "TIMESTAMP", to_dt),
        ]
    )
    try:
        for row in client.query(query, job_config=job_config).result():
            if row[0] is not None and row[1] is not None:
                windows.setdefault(row[1], set()).add(row[0])
    except Exception as e:
        _log().warning(f"Could not query existing windows for {table}: {e}")
    return windows


def ingest_endpoints(
    client: bigquery.Client,
    cfg: Dict[str, Any],
    start: datetime,
    end: datetime,
    project: str,
    dataset_id: str,
):
    base_urls = cfg["base_urls"]
    api_key = os.getenv("ELEXON_API_KEY", "")
    # Top-level param lists for fan-out (e.g., bm_unit)
    all_param_lists = cfg.get("param_lists", {})
    defaults = cfg.get("defaults", {})

    endpoints_to_process = cfg.get("endpoints", [])
    if not endpoints_to_process:
        _log().warning(
            "No endpoints selected to process. Check --groups or --only flags."
        )
        return

    for endpoint in tqdm(endpoints_to_process, desc="Endpoints", unit="endpoint"):
        name = (
            endpoint.get("_name")
            or endpoint.get("name")
            or endpoint.get("code")
            or "unnamed"
        )
        base_key = endpoint.get("base", "insights")
        base_url = base_urls.get(base_key)

        if not base_url:
            _log().warning(
                f"Skipping endpoint '{name}' due to missing base_url for key '{base_key}'"
            )
            continue

        path = endpoint.get("path")
        if not path:
            # Legacy BMRS support via dataset code
            code = endpoint.get("code")
            if code:
                path = f"/{code}"
            else:
                _log().warning(f"Skipping endpoint with no path: {name}")
                continue

        # Normalise table name across schemas
        table = (
            endpoint.get("bq_table")
            or endpoint.get("table_name")
            or endpoint.get("table")
        )
        if not table:
            # Reasonable fallback
            table = f"ins_{name}"

        # Windowing and date params
        window = _chunk_to_delta(
            endpoint.get("max_window")
            or endpoint.get("chunk")
            or defaults.get("chunk", "7d")
        )
        has_from_to = endpoint.get("has_from_to", True)
        from_param = endpoint.get("from_param", "from")
        to_param = endpoint.get("to_param", "to")

        # Format handling: Insights default JSON, BMRS default CSV
        fmt = endpoint.get("format") or (
            "json" if base_key == "insights" else defaults.get("format", "csv")
        )
        records_path = endpoint.get("records_path")

        # Parameter fan-out
        param_lists_keys: List[str] = []
        # 1) Explicit endpoint-level param_lists mapping
        if isinstance(endpoint.get("param_lists"), dict):
            param_lists_keys.extend(list(endpoint["param_lists"].keys()))
        # 2) `requires` section (e.g., bm_unit)
        if isinstance(endpoint.get("requires"), list):
            for req in endpoint["requires"]:
                key = req.get("key")
                if key:
                    param_lists_keys.append(key)
        # De-duplicate keys
        param_lists_keys = list(dict.fromkeys(param_lists_keys))

        # --- Build task list (windows × param fan-outs) ---
        all_windows = (
            list(_iter_windows(start, end, window)) if has_from_to else [(start, end)]
        )
        tasks = []
        if not param_lists_keys:
            tasks = [(w_from, w_to, {}) for w_from, w_to in all_windows]
        else:
            # Cartesian product of all param lists
            values: List[List[Any]] = []
            for k in param_lists_keys:
                v = all_param_lists.get(k, [])
                if not v:
                    _log().warning(
                        f"Endpoint '{name}' requires param '{k}' but no values found in top-level param_lists."
                    )
                values.append(v)
            param_combos = list(itertools.product(*values))
            for combo in param_combos:
                params = dict(zip(param_lists_keys, combo))
                for w_from, w_to in all_windows:
                    tasks.append((w_from, w_to, params))

        if not tasks:
            _log().info(f"No tasks to run for endpoint {name} (check param_lists).")
            continue

        # --- Check for existing data to skip tasks ---
        existing_windows = _get_existing_param_windows(
            client,
            project,
            dataset_id,
            table,
            start,
            end,
            param_lists_keys[0] if param_lists_keys else None,
        )

        def should_skip(w_from, params):
            if not existing_windows:
                return False
            param_val = list(params.values())[0] if params else None
            if param_val in existing_windows:
                return w_from in existing_windows[param_val]
            # Special case for no-param endpoints
            if None in existing_windows:
                return w_from in existing_windows[None]
            return False

        tasks_to_run = [(wf, wt, p) for wf, wt, p in tasks if not should_skip(wf, p)]
        _log().info(
            f"Endpoint '{name}': {len(tasks)} total tasks, {len(tasks_to_run)} to run after checking cache."
        )

        # --- Execute tasks ---
        frames_batch: List[pd.DataFrame] = []
        for w_from, w_to, extra_params in tqdm(
            tasks_to_run, desc=f"  - {name}", leave=False
        ):
            url = f"{base_url}{path}"
            # Ensure correct date formatting for params
            req_params: Dict[str, Any] = {}
            if has_from_to:
                req_params[from_param] = w_from.isoformat()
                req_params[to_param] = w_to.isoformat()
            # Add static params from config and fan-out params
            req_params.update(endpoint.get("params", {}))
            req_params.update(extra_params)
            # Translate param names for Insights API (expects camelCase)
            if base_key == "insights":
                # Known mappings
                mapping = {
                    "bm_unit": "bmUnit",
                }
                for k_src, k_dst in list(mapping.items()):
                    if k_src in req_params and k_dst not in req_params:
                        req_params[k_dst] = req_params.pop(k_src)
            # The API expects a 'format' parameter for CSV, but not for JSON
            if fmt == "csv":
                req_params["format"] = "csv"

            headers = {"Accept": f"application/{fmt}"}
            if api_key:
                headers["X-API-Key"] = api_key

            df = None
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    df = _fetch_endpoint(url, req_params, headers, fmt, records_path)
                    break
                except Exception as e:
                    _log().warning(
                        f"Attempt {attempt} failed for {name} ({w_from} {extra_params}): {e}"
                    )
                    if attempt == MAX_RETRIES:
                        _log().error(
                            f"Skipping chunk for {name} after all retries failed."
                        )
                    else:
                        time.sleep(RETRY_BACKOFF * attempt)

            if df is not None and not df.empty:
                # For non-windowed endpoints, use the overall range for metadata
                meta_from = w_from if has_from_to else start
                meta_to = w_to if has_from_to else end
                df_meta = _append_metadata(df, table, meta_from, meta_to, extra_params)
                frames_batch.append(df_meta)

            if len(frames_batch) >= MAX_FRAMES_PER_BATCH:
                batch_df = pd.concat(frames_batch, ignore_index=True)
                _load_dataframe(client, batch_df, project, dataset_id, table)
                frames_batch.clear()

        if frames_batch:
            batch_df = pd.concat(frames_batch, ignore_index=True)
            _load_dataframe(client, batch_df, project, dataset_id, table)
            frames_batch.clear()


def main():
    ap = argparse.ArgumentParser(
        description="Ingest data from Elexon Insights API based on YAML config."
    )
    ap.add_argument("--config", required=True, help="Path to insights_endpoints.yml")
    ap.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    ap.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    ap.add_argument("--project", help="BigQuery Project ID (overrides config)")
    ap.add_argument("--dataset", help="BigQuery Dataset (overrides config)")
    ap.add_argument("--only", help="Comma-separated list of endpoint names to run")
    ap.add_argument("--groups", help="Comma-separated list of group names to run")
    ap.add_argument(
        "--param",
        action="append",
        help="Override a fan-out parameter as key=value. Can be repeated. Example: --param bm_unit=T_DRAXX-1",
    )
    ap.add_argument(
        "--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    args = ap.parse_args()

    # Setup logging
    log = logging.getLogger()
    log.setLevel(args.log_level)
    handler = TqdmLoggingHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log.addHandler(handler)

    # Load config
    try:
        with open(args.config, "r") as f:
            cfg_source = yaml.safe_load(f)
    except Exception as e:
        _log().error(f"Failed to load config {args.config}: {e}")
        sys.exit(1)

    # Determine project and dataset
    defaults = cfg_source.get("defaults", {})
    project = args.project or defaults.get("project")
    dataset = args.dataset or defaults.get("dataset")
    if not project or not dataset:
        _log().error(
            "Missing required configuration: 'project' and 'dataset' must be specified in the YAML defaults or via command-line arguments."
        )
        sys.exit(1)

    # Consolidate all endpoints from groups into a single list
    all_endpoints = []
    for group_name, endpoints_in_group in cfg_source.get("groups", {}).items():
        # The new config format is a dict of dicts, the old was a dict of lists.
        # Handle both by checking if the inner item is a dictionary.
        if isinstance(endpoints_in_group, dict):
            # New format: iterate over values
            for endpoint_name, endpoint_config in endpoints_in_group.items():
                endpoint_config["_group"] = group_name
                endpoint_config["_name"] = endpoint_name  # The key is the name
                all_endpoints.append(endpoint_config)
        elif isinstance(endpoints_in_group, list):
            # Old format: iterate over list items
            for endpoint in endpoints_in_group:
                endpoint["_group"] = group_name
                all_endpoints.append(endpoint)

    # Also include any root-level endpoints defined under 'endpoints'
    for endpoint in cfg_source.get("endpoints", []) or []:
        if isinstance(endpoint, dict):
            ep = copy.deepcopy(endpoint)
            ep.setdefault("_group", "root")
            # Preserve the explicit name if present; otherwise use code/path
            ep.setdefault(
                "_name", ep.get("name") or ep.get("code") or ep.get("path") or "unnamed"
            )
            all_endpoints.append(ep)

    # Filter endpoints if --only or --groups is used
    endpoints_to_run = all_endpoints
    if args.only:
        wanted = {s.strip() for s in args.only.split(",")}
        endpoints_to_run = [
            e
            for e in all_endpoints
            if e.get("_name") in wanted
            or e.get("name") in wanted
            or e.get("code") in wanted
        ]
        _log().info(f"Running only for specified endpoints: {', '.join(wanted)}")
    elif args.groups:
        wanted_groups = {s.strip() for s in args.groups.split(",")}
        endpoints_to_run = [
            e for e in all_endpoints if e.get("_group") in wanted_groups
        ]
        _log().info(f"Running for groups: {', '.join(wanted_groups)}")

    # Build a run config without losing global param lists defined at the root or in
    # the standalone 'endpoints' section. Group endpoints will use 'requires' to
    # reference keys such as 'bm_unit', and we'll resolve values from here.
    run_cfg = {}
    # Shallow copy core sections
    for key in ["base_urls", "defaults"]:
        if key in cfg_source:
            run_cfg[key] = copy.deepcopy(cfg_source[key])

    # Merge top-level param_lists if present
    merged_param_lists: Dict[str, List[Any]] = {}
    top_param_lists = cfg_source.get("param_lists", {}) or {}
    if isinstance(top_param_lists, dict):
        for k, v in top_param_lists.items():
            if isinstance(v, list):
                merged_param_lists[k] = list(v)

    # Also harvest any param_lists from the root 'endpoints' array (templates)
    for ep in cfg_source.get("endpoints", []) or []:
        pls = ep.get("param_lists") if isinstance(ep, dict) else None
        if isinstance(pls, dict):
            for k, v in pls.items():
                if not isinstance(v, list):
                    continue
                if k not in merged_param_lists or not merged_param_lists[k]:
                    merged_param_lists[k] = list(v)
                else:
                    # Merge unique values while preserving order
                    seen = set(merged_param_lists[k])
                    merged_param_lists[k].extend([x for x in v if x not in seen])

    # Apply --param overrides (restrict fan-out to a specific value)
    if args.param:
        for item in args.param:
            if "=" in item:
                k, v = item.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    merged_param_lists[k] = [v]

    if merged_param_lists:
        run_cfg["param_lists"] = merged_param_lists

    # Set the specific endpoints to run (from groups filtering)
    run_cfg["endpoints"] = endpoints_to_run

    start = _parse_iso_date(args.start)
    end = _parse_iso_date(args.end)
    client = bigquery.Client(project=project)

    _ensure_dataset_exists(client, project, dataset)

    ingest_endpoints(client, run_cfg, start, end, project, dataset)
    _log().info("✅ All endpoints processed.")


if __name__ == "__main__":
    main()
