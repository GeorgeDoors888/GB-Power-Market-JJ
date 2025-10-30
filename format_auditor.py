#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

try:
    import geopandas as gpd  # type: ignore

    GEOSPATIAL_OK = True
except Exception:
    GEOSPATIAL_OK = False

try:
    from google.cloud import bigquery

    BIGQUERY_OK = True
except ImportError:
    BIGQUERY_OK = False


def detect_file_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".csv", ".tsv"]:
        return "csv"
    if ext == ".json":
        try:
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
                return "geojson"
        except Exception:
            pass
        return "json"
    if ext in [".geojson", ".topojson"]:
        return "geojson"
    return "unknown"


def load_csv(path: str) -> pd.DataFrame:
    for enc in [None, "utf-8-sig", "latin-1", "cp1252"]:
        try:
            if enc is None:
                return pd.read_csv(path)
            return pd.read_csv(path, encoding=enc)
        except Exception:
            continue
    return pd.read_csv(path)


def json_to_dataframe(obj: Any) -> pd.DataFrame:
    if isinstance(obj, list):
        try:
            return pd.json_normalize(obj, max_level=1)
        except Exception:
            return pd.DataFrame(obj)
    elif isinstance(obj, dict):
        for key in ["data", "items", "records", "rows", "results", "features"]:
            if key in obj and isinstance(obj[key], list):
                return pd.json_normalize(obj[key], max_level=1)
        return pd.json_normalize(obj, max_level=1)
    else:
        raise ValueError("Unsupported JSON structure")


def load_json(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    return json_to_dataframe(obj)


def load_geojson(path: str):
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    features = obj.get("features", [])
    props = [feat.get("properties", {}) for feat in features if isinstance(feat, dict)]
    df = pd.json_normalize(props, max_level=1) if props else pd.DataFrame()
    gdf = None
    if GEOSPATIAL_OK:
        try:
            gdf = gpd.read_file(path)
        except Exception:
            gdf = None
    return df, gdf


def infer_dtype(series: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "text"


def try_parse_dates(series: pd.Series, dayfirst: bool) -> float:
    s = pd.to_datetime(series, errors="coerce", dayfirst=dayfirst)
    denom = max(1, len(series))
    return float(s.notna().sum()) / float(denom)


def try_parse_numeric(series: pd.Series) -> float:
    s = (
        series.astype(str)
        .str.replace(r"[,\s]", "", regex=True)
        .str.replace("%", "", regex=False)
    )
    s = pd.to_numeric(s, errors="coerce")
    denom = max(1, len(series))
    return float(s.notna().sum()) / float(denom)


def profile_dataframe(df: pd.DataFrame, config: Dict[str, Any], filename: str):
    dayfirst = bool(config.get("dayfirst", True))
    key_cols = config.get("key_cols") or []

    rows = []
    for col in df.columns:
        s = df[col]
        dtype = infer_dtype(s)
        nulls = int(s.isna().sum())
        null_pct = 100.0 * nulls / max(1, len(s))
        distinct = int(s.nunique(dropna=True))
        sample_values = list(s.dropna().astype(str).head(5).values)

        date_parse_rate = None
        num_parse_rate = None
        if dtype == "text":
            date_parse_rate = try_parse_dates(s, dayfirst)
            num_parse_rate = try_parse_numeric(s)
        elif dtype == "numeric":
            num_parse_rate = 1.0
        elif dtype == "datetime":
            date_parse_rate = 1.0

        row = {
            "file": filename,
            "column": col,
            "dtype_inferred": dtype,
            "rows": len(s),
            "nulls": nulls,
            "null_pct": round(null_pct, 2),
            "distinct": distinct,
            "date_parse_rate": (
                None if date_parse_rate is None else round(100.0 * date_parse_rate, 2)
            ),
            "numeric_parse_rate": (
                None if num_parse_rate is None else round(100.0 * num_parse_rate, 2)
            ),
            "sample_values": "; ".join(sample_values),
        }
        rows.append(row)

    dup_count = None
    if key_cols and all(k in df.columns for k in key_cols):
        dup_count = int(df.duplicated(subset=key_cols).sum())

    summary = {
        "file": filename,
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "empty_columns": [c for c in df.columns if df[c].notna().sum() == 0],
        "potential_date_columns": [
            c for c in df.columns if re.search(r"(date|timestamp|_at)$", c, re.I)
        ],
        "duplicate_key_count": dup_count,
        "key_columns": key_cols or None,
    }

    return pd.DataFrame(rows), summary


def audit_path(in_path: str, out_dir: str, config: Dict[str, Any]):
    os.makedirs(out_dir, exist_ok=True)
    all_profiles = []
    summaries = []

    def handle_file(path: str):
        ftype = detect_file_type(path)
        base = os.path.basename(path)
        try:
            if ftype == "csv":
                df = load_csv(path)
                prof, summ = profile_dataframe(df, config, base)
                all_profiles.append(prof)
                summaries.append(summ)
            elif ftype == "json":
                df = load_json(path)
                prof, summ = profile_dataframe(df, config, base)
                all_profiles.append(prof)
                summaries.append(summ)
            elif ftype == "geojson":
                df, gdf = load_geojson(path)
                prof, summ = profile_dataframe(df, config, base)
                if gdf is not None and GEOSPATIAL_OK:
                    summ["geoms"] = int(len(gdf))
                    try:
                        summ["geom_invalid"] = int((~gdf.is_valid).sum())
                        summ["geom_empty"] = int(gdf.geometry.is_empty.sum())
                        summ["crs"] = str(gdf.crs)
                    except Exception:
                        pass
                all_profiles.append(prof)
                summaries.append(summ)
            else:
                summaries.append({"file": base, "error": "unsupported file type"})
        except Exception as e:
            summaries.append({"file": base, "error": str(e)})

    if os.path.isdir(in_path):
        for root, _, files in os.walk(in_path):
            for name in files:
                if name.startswith("."):
                    continue
                handle_file(os.path.join(root, name))
    else:
        handle_file(in_path)

    merged = (
        pd.concat(all_profiles, ignore_index=True) if all_profiles else pd.DataFrame()
    )

    prof_csv = os.path.join(out_dir, "issues_profile.csv")
    merged.to_csv(prof_csv, index=False)

    summ_json = os.path.join(out_dir, "issues_summary.json")
    with open(summ_json, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    return merged, summaries


def audit_bigquery(
    project: str,
    dataset: str,
    prefix: str,
    sample_rows: int,
    out_dir: str,
    config: Dict[str, Any],
):
    """Audits tables in a BigQuery dataset."""
    if not BIGQUERY_OK:
        print(
            "[error] google-cloud-bigquery is not installed. Please `pip install google-cloud-bigquery pandas-gbq`"
        )
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)
    all_profiles = []
    summaries = []

    client = bigquery.Client(project=project)
    dataset_ref = client.dataset(dataset)
    all_tables = list(client.list_tables(dataset_ref))
    tables_to_audit = sorted(
        [t for t in all_tables if t.table_id.startswith(prefix)],
        key=lambda t: t.table_id,
    )

    print(
        f"Found {len(tables_to_audit)} tables in {project}.{dataset} with prefix '{prefix}'"
    )

    for table in tables_to_audit:
        table_id = f"{project}.{dataset}.{table.table_id}"
        print(f" - Auditing {table.table_id} (sampling {sample_rows} rows)...")
        try:
            # Get total rows for summary before sampling
            table_obj = client.get_table(table)
            total_rows = table_obj.num_rows

            # Sample the table to avoid downloading huge amounts of data
            query = f"SELECT * FROM `{table_id}` LIMIT {sample_rows}"
            # Use pandas-gbq to read the data
            df = pd.read_gbq(query, project_id=project)

            if df.empty:
                summaries.append(
                    {
                        "file": table.table_id,
                        "rows": total_rows,
                        "cols": len(table_obj.schema),
                        "error": "Table is empty or sample returned no rows.",
                    }
                )
                continue

            prof, summ = profile_dataframe(df, config, table.table_id)
            summ["total_rows_in_table"] = total_rows
            summ["rows_sampled"] = len(df)
            all_profiles.append(prof)
            summaries.append(summ)

        except Exception as e:
            summaries.append({"file": table.table_id, "error": str(e)})

    merged = (
        pd.concat(all_profiles, ignore_index=True) if all_profiles else pd.DataFrame()
    )

    prof_csv = os.path.join(out_dir, "bq_issues_profile.csv")
    merged.to_csv(prof_csv, index=False)

    summ_json = os.path.join(out_dir, "bq_issues_summary.json")
    with open(summ_json, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

    return merged, summaries


def load_config(path: Optional[str]) -> Dict[str, Any]:
    cfg = {"dayfirst": True, "key_cols": None}
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        if isinstance(user_cfg, dict):
            cfg.update(user_cfg)
    return cfg


def main():
    ap = argparse.ArgumentParser(
        description="Audit CSV/JSON/GeoJSON or BigQuery tables for common data issues."
    )
    ap.add_argument(
        "--in", dest="in_path", help="Input file or folder (for file audit)"
    )
    ap.add_argument(
        "--out", dest="out_dir", required=True, help="Output report directory"
    )
    ap.add_argument(
        "--config",
        dest="config_path",
        help="Optional JSON config (e.g., key_cols, dayfirst)",
    )
    # BigQuery arguments
    ap.add_argument("--bq-project", help="BigQuery Project ID")
    ap.add_argument("--bq-dataset", help="BigQuery Dataset")
    ap.add_argument("--bq-table-prefix", help="Prefix for tables to audit in dataset")
    ap.add_argument(
        "--bq-sample-rows",
        type=int,
        default=50000,
        help="Number of rows to sample from each BigQuery table (default: 50000)",
    )
    args = ap.parse_args()

    cfg = load_config(args.config_path)

    if args.bq_project and args.bq_dataset and args.bq_table_prefix:
        print("Running in BigQuery audit mode.")
        _, summaries = audit_bigquery(
            args.bq_project,
            args.bq_dataset,
            args.bq_table_prefix,
            args.bq_sample_rows,
            args.out_dir,
            cfg,
        )
        report_profile = "bq_issues_profile.csv"
        report_summary = "bq_issues_summary.json"
    elif args.in_path:
        print("Running in file audit mode.")
        _, summaries = audit_path(args.in_path, args.out_dir, cfg)
        report_profile = "issues_profile.csv"
        report_summary = "issues_summary.json"
    else:
        print(
            "[error] You must provide either --in (for files) or --bq-project, --bq-dataset, and --bq-table-prefix (for BigQuery)."
        )
        sys.exit(1)

    print(f"[ok] Audit completed. Wrote {report_profile} and {report_summary}")
    for s in summaries[:5]:
        if "error" in s:
            print(" -", s.get("file"), ":", "error=" + s["error"])
        else:
            print(" -", s.get("file"), f"rows={s.get('rows')} cols={s.get('cols')}")


if __name__ == "__main__":
    main()
