#!/usr/bin/env python3
"""
bq_profile_dataset.py
Create human-friendly profiles for all tables in a BigQuery dataset.

Outputs:
- profiles/PROFILE_INDEX.json  (machine-readable)
- profiles/<table_name>.md     (human-readable)
"""
import os, sys, json, math, re, datetime as dt
from pathlib import Path
from typing import Optional, Dict, Any, List

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

OUTDIR = Path("profiles")
SAMPLE_ROWS = 200000            # limit per-table sampling when tables are huge
TOPK = 10                       # top categories to list
DATE_LOOKBACK_DAYS = 365        # coverage window for timeseries summary

UNITS_HINTS = {
    r"\bssp\b|\bsbp\b": "£/MWh",
    r"\bprice\b|\brate\b": "£/MWh",
    r"\bdemand\b|\bload\b|\bmwh\b|\bkwh\b": "MWh",
    r"\bco2\b|\bcarbon\b": "tCO2",
    r"\bvolume\b": "MWh",
    r"\bperiod\b|\bsp\b|\bsettlement_?period\b": "1..48",
}

def guess_units(col_name: str, description: Optional[str]) -> Optional[str]:
    text = f"{col_name} {description or ''}".lower()
    for pat, u in UNITS_HINTS.items():
        if re.search(pat, text):
            return u
    return None

def safe_name(name: str) -> str:
    return name.replace("`","").replace(".","_")

def human(n: int) -> str:
    for unit in ["","K","M","B","T","P"]:
        if abs(n) < 1000:
            return f"{n:.0f}{unit}"
        n /= 1000.0
    return f"{n:.0f}E"

def select_time_col(schema: List[bigquery.SchemaField]) -> Optional[str]:
    # prefer TIMESTAMP/DATE/DATETIME names that look like event/settlement time
    candidates = [f.name for f in schema if f.field_type in ("TIMESTAMP","DATE","DATETIME")]
    order = ["settlement", "event", "start", "datetime", "date", "ts", "time"]
    for want in order:
        for c in candidates:
            if want in c.lower():
                return c
    return candidates[0] if candidates else None

def collist(schema: List[bigquery.SchemaField]) -> str:
    # flatten simple columns only (ignore RECORD for quick profiling)
    cols = []
    for f in schema:
        if f.field_type != "RECORD":
            cols.append(f"`{f.name}`")
    return ", ".join(cols) if cols else "*"

def profile_table(bq: bigquery.Client, project: str, dataset: str, table: bigquery.Table) -> Dict[str, Any]:
    full = f"{project}.{dataset}.{table.table_id}"
    info: Dict[str, Any] = {
        "table": full,
        "type": table.table_type,
        "rows": int(table.num_rows or 0),
        "size_bytes": int(getattr(table, "num_bytes", 0) or 0),
        "last_modified": table.modified.isoformat() if table.modified else None,
        "partitioning": None,
        "clustering": getattr(table, "clustering_fields", None) or [],
        "schema": [],
        "notes": [],
        "suggested_primary_keys": [],
        "time_column": None,
        "date_coverage": None,
        "columns": {},
    }

    # schema
    for f in table.schema or []:
        info["schema"].append({
            "name": f.name,
            "type": f.field_type,
            "mode": f.mode,
            "description": f.description,
            "guess_units": guess_units(f.name, f.description)
        })

    # partitioning
    tp = getattr(table, "time_partitioning", None)
    if tp:
        info["partitioning"] = {"type": str(tp.type_), "field": tp.field or "_PARTITIONTIME"}
    # clustering is already added

    # choose a time column
    tcol = select_time_col(table.schema or [])
    if tcol:
        info["time_column"] = tcol

    # quick rowcount/coverage
    if info["rows"] > 0:
        # date coverage (last year) if time column exists
        if tcol:
            if any(f.field_type == "DATE" and f.name == tcol for f in table.schema):
                date_expr = f"`{tcol}`"
            else:
                date_expr = f"DATE(`{tcol}`)"
            sql = f"""
            SELECT
              MIN({date_expr}) AS min_date,
              MAX({date_expr}) AS max_date,
              COUNT(*) AS rows_last_year
            FROM `{full}`
            WHERE {date_expr} >= DATE_SUB(CURRENT_DATE(), INTERVAL {DATE_LOOKBACK_DAYS} DAY)
            """
            try:
                row = next(bq.query(sql).result())
                info["date_coverage"] = {
                    "min_date": row["min_date"].isoformat() if row["min_date"] else None,
                    "max_date": row["max_date"].isoformat() if row["max_date"] else None,
                    "rows_last_year": int(row["rows_last_year"] or 0),
                }
            except BadRequest as e:
                info["notes"].append(f"date_coverage_failed: {getattr(e,'message',str(e))}")

        # basic column stats with sampling for huge tables
        # build a temporary sampling clause
        sample_clause = ""
        if info["rows"] > SAMPLE_ROWS:
            # use TABLESAMPLE SYSTEM for large tables if supported: BigQuery supports TABLESAMPLE SYSTEM (<percent>)
            # choose a percentage roughly matching SAMPLE_ROWS
            pct = max(0.1, min(100.0, 100.0 * SAMPLE_ROWS / max(1, info["rows"])))
            sample_clause = f" TABLESAMPLE SYSTEM ({pct:.3f} PERCENT) "
        # gather stats per column
        simple_cols = [f for f in table.schema if f.field_type != "RECORD"]
        for f in simple_cols:
            cname = f.name
            qname = f"`{cname}`"
            col = {"type": f.field_type, "mode": f.mode, "description": f.description, "guess_units": guess_units(cname, f.description)}
            try:
                if f.field_type in ("INT64","NUMERIC","BIGNUMERIC","FLOAT","FLOAT64"):
                    sql = f"""
                      SELECT
                        COUNT(1) AS n,
                        COUNTIF({qname} IS NULL) AS n_null,
                        MIN({qname}) AS min_val,
                        MAX({qname}) AS max_val,
                        AVG(CAST({qname} AS FLOAT64)) AS avg_val,
                        APPROX_QUANTILES(CAST({qname} AS FLOAT64), 5)[OFFSET(1)] AS p25,
                        APPROX_QUANTILES(CAST({qname} AS FLOAT64), 5)[OFFSET(2)] AS p50,
                        APPROX_QUANTILES(CAST({qname} AS FLOAT64), 5)[OFFSET(3)] AS p75
                      FROM `{full}` {sample_clause}
                    """
                    r = next(bq.query(sql).result())
                    col.update({
                        "n": int(r["n"]), "nulls": int(r["n_null"]),
                        "min": r["min_val"], "max": r["max_val"], "avg": r["avg_val"],
                        "p25": r["p25"], "p50": r["p50"], "p75": r["p75"],
                    })
                    # quality flags
                    flags = []
                    if col["min"] is not None and col["max"] is not None and col["min"] == col["max"]:
                        flags.append("CONSTANT_COLUMN")
                    if col["min"] is not None and col["min"] < 0 and "price" in cname.lower():
                        flags.append("NEGATIVE_PRICE")
                    col["flags"] = flags
                elif f.field_type in ("BOOL","BOOLEAN"):
                    sql = f"""
                      SELECT
                        COUNT(1) AS n,
                        COUNTIF({qname} IS NULL) AS n_null,
                        COUNTIF({qname} = TRUE) AS n_true,
                        COUNTIF({qname} = FALSE) AS n_false
                      FROM `{full}` {sample_clause}
                    """
                    r = next(bq.query(sql).result())
                    col.update({
                        "n": int(r["n"]), "nulls": int(r["n_null"]),
                        "true": int(r["n_true"]), "false": int(r["n_false"])
                    })
                elif f.field_type in ("STRING","BYTES"):
                    sql = f"""
                      SELECT
                        COUNT(1) AS n,
                        COUNTIF({qname} IS NULL OR {qname} = '') AS n_empty,
                        APPROX_COUNT_DISTINCT({qname}) AS approx_cardinality
                      FROM `{full}` {sample_clause}
                    """
                    r = next(bq.query(sql).result())
                    col.update({
                        "n": int(r["n"]), "empty_or_null": int(r["n_empty"]),
                        "approx_cardinality": int(r["approx_cardinality"])
                    })
                    # top categories
                    sql = f"""
                      SELECT {qname} AS value, COUNT(*) AS cnt
                      FROM `{full}` {sample_clause}
                      WHERE {qname} IS NOT NULL AND {qname} != ''
                      GROUP BY value
                      ORDER BY cnt DESC
                      LIMIT {TOPK}
                    """
                    tops = [{"value": rr["value"], "count": int(rr["cnt"])} for rr in bq.query(sql).result()]
                    col["top_values"] = tops
                elif f.field_type in ("TIMESTAMP","DATE","DATETIME"):
                    expr = qname if f.field_type == "DATE" else f"DATE({qname})"
                    sql = f"""
                      SELECT
                        COUNT(1) AS n,
                        COUNTIF({qname} IS NULL) AS n_null,
                        MIN({expr}) AS min_date,
                        MAX({expr}) AS max_date,
                        COUNTIF({expr} >= DATE_SUB(CURRENT_DATE(), INTERVAL {DATE_LOOKBACK_DAYS} DAY)) AS rows_last_year
                      FROM `{full}` {sample_clause}
                    """
                    r = next(bq.query(sql).result())
                    col.update({
                        "n": int(r["n"]), "nulls": int(r["n_null"]),
                        "min_date": r["min_date"].isoformat() if r["min_date"] else None,
                        "max_date": r["max_date"].isoformat() if r["max_date"] else None,
                        "rows_last_year": int(r["rows_last_year"])
                    })
                else:
                    # fallback: just null count
                    sql = f"SELECT COUNT(1) AS n, COUNTIF({qname} IS NULL) AS n_null FROM `{full}` {sample_clause}"
                    r = next(bq.query(sql).result())
                    col.update({"n": int(r["n"]), "nulls": int(r["n_null"])})
            except BadRequest as e:
                col["error"] = getattr(e, "message", str(e))
            info["columns"][cname] = col
    else:
        info["notes"].append("TABLE_EMPTY")

    # simple join-key guesses: any column ending with _id or named id with high distinctness
    id_candidates = [c for c in info["columns"].items()
                     if c[1].get("type") in ("STRING","INT64","NUMERIC","BIGNUMERIC") and
                        (c[0].lower().endswith("_id") or c[0].lower() == "id")]
    for name, col in id_candidates:
        card = col.get("approx_cardinality")
        n = col.get("n", info["rows"])
        if card and n and card >= 0.7 * n:
            info["suggested_primary_keys"].append(name)

    return info

def write_markdown(table_profile: Dict[str, Any]):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    t = table_profile
    fname = OUTDIR / f"{t['table'].split('.')[-1]}.md"
    lines = []
    lines.append(f"# {t['table']}")
    lines.append("")
    lines.append(f"- **Type:** {t['type']}")
    lines.append(f"- **Rows:** {t['rows']:,}")
    lines.append(f"- **Size:** {human(t['size_bytes'])}")
    if t.get("last_modified"):
        lines.append(f"- **Last modified:** {t['last_modified']}")
    if t.get("partitioning"):
        p = t["partitioning"]
        lines.append(f"- **Partitioning:** {p.get('type')} on `{p.get('field')}`")
    if t.get("clustering"):
        lines.append(f"- **Clustering:** {', '.join(t['clustering'])}")
    if t.get("time_column"):
        lines.append(f"- **Time column (detected):** `{t['time_column']}`")
    if t.get("date_coverage"):
        dc = t["date_coverage"]
        lines.append(f"- **Coverage (last {DATE_LOOKBACK_DAYS}d):** {dc['min_date']} → {dc['max_date']} ({human(dc['rows_last_year'])} rows)")
    if t.get("suggested_primary_keys"):
        lines.append(f"- **Suggested key(s):** {', '.join(t['suggested_primary_keys'])}")
    if t.get("notes"):
        lines.append(f"- **Notes:** {', '.join(t['notes'])}")
    lines.append("\n## Schema")
    lines.append("| Column | Type | Mode | Units | Description |")
    lines.append("|---|---|---|---|---|")
    for f in t["schema"]:
        lines.append(f"| `{f['name']}` | {f['type']} | {f['mode']} | {f.get('guess_units') or ''} | {f.get('description') or ''} |")
    lines.append("\n## Column profiles (sampled)")
    for name, col in t["columns"].items():
        lines.append(f"### `{name}`  ({col.get('type')})")
        if "error" in col:
            lines.append(f"- ⚠️ Error: {col['error']}")
            continue
        if col["type"] in ("INT64","NUMERIC","BIGNUMERIC","FLOAT","FLOAT64"):
            lines.append(f"- Non-null: {human(col.get('n',0) - col.get('nulls',0))} / {human(col.get('n',0))}")
            lines.append(f"- Min/Median/Max: {col.get('min')} / {col.get('p50')} / {col.get('max')}")
            lines.append(f"- Mean: {col.get('avg')}")
            if col.get("flags"):
                lines.append(f"- Flags: {', '.join(col['flags'])}")
        elif col["type"] in ("STRING","BYTES"):
            lines.append(f"- Non-empty: {human(col.get('n',0) - col.get('empty_or_null',0))} / {human(col.get('n',0))}")
            lines.append(f"- Approx. distinct: {human(col.get('approx_cardinality',0))}")
            tv = col.get("top_values", [])
            if tv:
                lines.append("- Top values:")
                for v in tv:
                    lines.append(f"  - `{v['value']}` ({human(v['count'])})")
        elif col["type"] in ("TIMESTAMP","DATE","DATETIME"):
            lines.append(f"- Range: {col.get('min_date')} → {col.get('max_date')}")
            lines.append(f"- Rows last {DATE_LOOKBACK_DAYS}d: {human(col.get('rows_last_year',0))}")
        else:
            lines.append(f"- Non-null: {human(col.get('n',0) - col.get('nulls',0))} / {human(col.get('n',0))}")
        lines.append("")
    fname.write_text("\n".join(lines), encoding="utf-8")

def run(project: str, dataset: str, location: Optional[str], out_json: Path):
    OUTDIR.mkdir(parents=True, exist_ok=True)
    bq = bigquery.Client(project=project, location=location)
    ds_ref = bigquery.DatasetReference(project, dataset)
    try:
        tables = list(bq.list_tables(ds_ref))
    except NotFound:
        print(f"Dataset not found: {project}.{dataset}")
        sys.exit(2)

    index: Dict[str, Any] = {
        "project": project,
        "dataset": dataset,
        "location": location,
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "tables": []
    }

    for t in tables:
        tbl = bq.get_table(t.reference)
        prof = profile_table(bq, project, dataset, tbl)
        write_markdown(prof)
        index["tables"].append(prof)

    out_json.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"✓ Wrote {out_json} and {len(tables)} Markdown profiles in {OUTDIR}/")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bq_profile_dataset.py <PROJECT_ID> <DATASET> [<LOCATION>] [--out profiles/PROFILE_INDEX.json]")
        sys.exit(1)
    project = sys.argv[1]
    dataset = sys.argv[2]
    location = None
    out_path = OUTDIR / "PROFILE_INDEX.json"
    # parse optional args
    for i, arg in enumerate(sys.argv[3:], start=3):
        if arg == "--out" and i + 1 < len(sys.argv):
            out_path = Path(sys.argv[i + 1])
        elif arg != "--out" and not arg.startswith("--"):
            location = arg
    run(project, dataset, location, out_path)