#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
from typing import List, Set, Optional, Dict, Any

from google.cloud import bigquery
from google.api_core.exceptions import NotFound
import yaml

BM_CANDIDATE_COLS = [
    "bm_unit", "bmunit", "bm_unit_id", "bmunitid", "bm_unit_name",
    "bm_unit_identifier", "bm_unit_code", "unit_id", "unitname", "unit",
    "bmUnit", "bmUnitId", "bmUnitID"
]

DEFAULT_TABLES = [
    "bmrs_bod", "bmrs_boalf",
    "ins_bod", "ins_boalf"
]

UNIT_ENDPOINT_TEMPLATES = [
    {
        "name": "balancing_physical_by_unit",
        "path": "/balancing/physical",
        "from_param": "from",
        "to_param": "to",
        "max_window": "1d",
        "format": "json",
        "records_path": "data",
        "table": "ins_balancing_physical",
    },
    {
        "name": "balancing_bid_offer_by_unit",
        "path": "/balancing/bid-offer",
        "from_param": "from",
        "to_param": "to",
        "max_window": "1d",
        "format": "json",
        "records_path": "data",
        "table": "ins_balancing_bid_offer",
    },
    {
        "name": "balancing_acceptances_by_unit",
        "path": "/balancing/acceptances",
        "from_param": "from",
        "to_param": "to",
        "max_window": "1d",
        "format": "json",
        "records_path": "data",
        "table": "ins_balancing_acceptances",
    },
]

def _log(msg: str):
    print(msg, file=sys.stderr)

def _get_columns(client: bigquery.Client, project: str, dataset: str, table: str) -> List[str]:
    """Return list of column names for table using INFORMATION_SCHEMA."""
    ds = f"`{project}.{dataset}`"
    # BigQuery commonly stores table_name uppercase in INFORMATION_SCHEMA; check both.
    query = f"""
    SELECT column_name
    FROM {ds}.INFORMATION_SCHEMA.COLUMNS
    WHERE table_name = @t_upper OR table_name = @t_exact
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("t_upper", "STRING", table.upper()),
                bigquery.ScalarQueryParameter("t_exact", "STRING", table),
            ]
        ),
    )
    cols = [row[0] for row in job.result()]
    return cols

def _pick_bm_col(cols: List[str]) -> Optional[str]:
    lower = {c.lower(): c for c in cols}
    for want in BM_CANDIDATE_COLS:
        if want.lower() in lower:
            return lower[want.lower()]
    return None

def _distinct_units(client: bigquery.Client, project: str, dataset: str, table: str, bm_col: str, min_count: int = 0) -> Set[str]:
    """Return distinct BM units, optionally requiring at least min_count appearances."""
    table_id = f"`{project}.{dataset}.{table}`"
    col_quoted = f"`{bm_col}`"
    if min_count > 1:
        query = f"""
        SELECT CAST({col_quoted} AS STRING) AS unit
        FROM (
          SELECT {col_quoted}, COUNT(*) AS c
          FROM {table_id}
          WHERE {col_quoted} IS NOT NULL AND CAST({col_quoted} AS STRING) != ""
          GROUP BY {col_quoted}
          HAVING c >= @minc
        )
        """
        params = [bigquery.ScalarQueryParameter("minc", "INT64", min_count)]
    else:
        query = f"""
        SELECT DISTINCT CAST({col_quoted} AS STRING) AS unit
        FROM {table_id}
        WHERE {col_quoted} IS NOT NULL AND CAST({col_quoted} AS STRING) != ""
        """
        params = []

    job = client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
    return {row["unit"] for row in job.result() if row["unit"] is not None}

def _table_exists(client: bigquery.Client, project: str, dataset: str, table: str) -> bool:
    try:
        client.get_table(f"{project}.{dataset}.{table}")
        return True
    except NotFound:
        return False

def collect_bm_units(project: str, dataset: str, tables: List[str], min_count: int) -> List[str]:
    client = bigquery.Client(project=project)
    units: Set[str] = set()

    for t in tables:
        if not _table_exists(client, project, dataset, t):
            _log(f"ℹ️  Table not found, skipping: {project}.{dataset}.{t}")
            continue
        cols = _get_columns(client, project, dataset, t)
        if not cols:
            _log(f"ℹ️  No columns visible for {t}, skipping.")
            continue
        bm_col = _pick_bm_col(cols)
        if not bm_col:
            _log(f"⚠️  No BM Unit column detected in {t}. Columns={cols}")
            continue
        _log(f"🔎 Using BM column `{bm_col}` in {t}")
        found = _distinct_units(client, project, dataset, t, bm_col, min_count=min_count)
        _log(f"✅ {t}: found {len(found)} unit(s)")
        units.update(found)

    ordered = sorted(units)
    _log(f"🎯 Total distinct BM units collected: {len(ordered)}")
    return ordered

def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(doc: Dict[str, Any], path: str):
    class Dumper(yaml.SafeDumper):
        pass
    # Represent lists in block style for readability
    def _repr_list(dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
    Dumper.add_representer(list, _repr_list)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(doc, f, Dumper=Dumper, sort_keys=False, width=120)

def ensure_unit_endpoints(cfg: Dict[str, Any], bm_units: List[str]) -> Dict[str, Any]:
    if "endpoints" not in cfg or not isinstance(cfg["endpoints"], list):
        cfg["endpoints"] = []

    endpoints = cfg["endpoints"]
    names = {e.get("name"): i for i, e in enumerate(endpoints) if isinstance(e, dict) and "name" in e}

    for tpl in UNIT_ENDPOINT_TEMPLATES:
        e = None
        if tpl["name"] in names:
            e = endpoints[names[tpl["name"]]]
        else:
            e = {}
            endpoints.append(e)

        e["name"] = tpl["name"]
        e["path"] = tpl["path"]
        e["from_param"] = tpl["from_param"]
        e["to_param"] = tpl["to_param"]
        e["max_window"] = tpl["max_window"]
        e["format"] = tpl["format"]
        e["records_path"] = tpl["records_path"]
        e["table"] = tpl["table"]
        e["param_lists"] = e.get("param_lists", {})
        e["param_lists"]["bm_unit"] = bm_units

    cfg["endpoints"] = endpoints
    return cfg

def main():
    ap = argparse.ArgumentParser(description="Populate bm_unit lists from BigQuery and update Insights YAML.")
    ap.add_argument("--project", default="jibber-jabber-knowledge")
    ap.add_argument("--dataset", default="uk_energy_prod")
    ap.add_argument("--tables", default=",".join(DEFAULT_TABLES),
                    help="Comma-separated table names to scan for BM units.")
    ap.add_argument("--min-count", type=int, default=0,
                    help="Only include units with at least this many rows (default 0).")
    ap.add_argument("--config", required=True, help="Path to existing insights_endpoints.yml")
    ap.add_argument("--output", default=None,
                    help="Output YAML path (default: <config>.with_units.yml)")
    ap.add_argument("--units-out", default="bm_units.tsv",
                    help="Path to dump plain unit list (default: bm_units.tsv)")
    args = ap.parse_args()

    tables = [t.strip() for t in args.tables.split(",") if t.strip()]
    bm_units = collect_bm_units(args.project, args.dataset, tables, args.min_count)

    if not bm_units:
        _log("❌ No BM units found. Aborting YAML update.")
        sys.exit(2)

    # write plain list
    with open(args.units_out, "w", encoding="utf-8") as f:
        for u in bm_units:
            f.write(f"{u}\n")
    _log(f"📝 Wrote unit list: {args.units_out}")

    cfg = load_yaml(args.config)
    cfg2 = ensure_unit_endpoints(cfg, bm_units)

    outpath = args.output or (args.config.rsplit(".", 1)[0] + ".with_units.yml")
    save_yaml(cfg2, outpath)
    _log(f"💾 Wrote updated YAML with bm_unit fanout: {outpath}")
    _log("✅ Done.")

if __name__ == "__main__":
    main()
