#!/usr/bin/env python3
"""
Write a detailed text inventory of a BigQuery dataset, including:
- Project and dataset info
- Table list with metadata (rows, bytes, partitioning, clustering, labels, created/modified/expires)
- Schema headers (name, type, mode, description)
- Quickstart: how to access via Console, bq CLI, and Python

Usage:
  GOOGLE_APPLICATION_CREDENTIALS=./jibber_jabber_key.json \
  python tools/bq_write_inventory.py --project jibber-jabber-knowledge --dataset uk_energy_insights \
    --out BIGQUERY_DATASET_INVENTORY.txt
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import os
from typing import List, Optional

from google.cloud import bigquery


def human_bytes(num: int | float | None) -> str:
    if num is None:
        return "-"
    n = float(num)
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if n < 1024.0:
            return f"{n:3.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} EB"


def fmt_dt(ts: Optional[dt.datetime]) -> str:
    if not ts:
        return "-"
    # Ensure UTC ISO8601
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dump_dataset(
    project: str,
    dataset_id: str,
    fast: bool = False,
    workers: int = 1,
) -> str:
    client = bigquery.Client(project=project)
    ds_ref = bigquery.DatasetReference(project, dataset_id)
    ds = client.get_dataset(ds_ref)

    lines: List[str] = []
    lines.append("BigQuery Dataset Inventory")
    lines.append("===========================")
    lines.append("")
    lines.append(f"Project: {project}")
    lines.append(f"Dataset: {dataset_id}")
    lines.append(f"Location: {ds.location or '-'}")
    lines.append(f"Description: {ds.description or '-'}")
    if ds.labels:
        labels = ", ".join(f"{k}={v}" for k, v in sorted(ds.labels.items()))
    else:
        labels = "-"
    lines.append(f"Labels: {labels}")
    lines.append("")

    lines.append("Tables")
    lines.append("------")
    tables = list(client.list_tables(ds))
    if not tables:
        lines.append("(No tables found)")

    if fast:
        query = f"""
        SELECT table_name, row_count, size_bytes, creation_time, last_modified_time
        FROM `{project}.{dataset_id}.INFORMATION_SCHEMA.TABLES`
        """
        query_job = client.query(query)
        for row in query_job:
            lines.append("")
            lines.append(f"- Table: {row.table_name}")
            lines.append(f"  Rows: {row.row_count}")
            lines.append(f"  Size: {human_bytes(row.size_bytes)}")
            lines.append(f"  Created: {fmt_dt(row.creation_time)}")
            lines.append(f"  Modified: {fmt_dt(row.last_modified_time)}")
    else:

        def fetch_table_metadata(t):
            table = client.get_table(t.reference)
            metadata = [
                f"- Table: {table.table_id}",
                f"  Full ID: {table.project}.{table.dataset_id}.{table.table_id}",
                f"  Type: {table.table_type}",
                f"  Rows: {table.num_rows}",
                f"  Size: {human_bytes(table.num_bytes)}",
                f"  Created: {fmt_dt(table.created)}",
                f"  Modified: {fmt_dt(table.modified)}",
                f"  Expires: {fmt_dt(table.expires)}",
            ]
            return "\n".join(metadata)

        if workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                results = list(executor.map(fetch_table_metadata, tables))
            lines.extend(results)
        else:
            for t in tables:
                lines.append("")
                lines.append(fetch_table_metadata(t))

    # Quickstart section
    lines.append("")
    lines.append("How to access")
    lines.append("-------------")
    lines.append(
        "- Web Console: https://console.cloud.google.com/bigquery?project={}".format(
            project
        )
    )
    lines.append("- Python (google-cloud-bigquery):")
    lines.append("    from google.cloud import bigquery")
    lines.append('    client = bigquery.Client(project="{}")'.format(project))
    lines.append(
        '    table = client.get_table("{}.{}.<table_name>")'.format(project, dataset_id)
    )
    lines.append("    rows = client.list_rows(table, max_results=10)")
    lines.append("    for r in rows: print(dict(r))")
    lines.append("- bq CLI:")
    lines.append(
        "    bq show --schema --format=prettyjson {}:{}.<table_name>".format(
            project, dataset_id
        )
    )
    lines.append(
        "    bq head --max_rows 10 {}:{}.<table_name>".format(project, dataset_id)
    )
    lines.append("")
    lines.append("Example query")
    lines.append("-------------")
    lines.append(
        "    SELECT *\n    FROM `{}.{}`.`<table_name>`\n    ORDER BY _ingested_utc DESC\n    LIMIT 100;".format(
            project, dataset_id
        )
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--out", default="BIGQUERY_DATASET_INVENTORY.txt")
    ap.add_argument(
        "--fast",
        action="store_true",
        help="Use INFORMATION_SCHEMA for faster inventory",
    )
    ap.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel workers for metadata fetch",
    )
    args = ap.parse_args()

    content = dump_dataset(
        args.project, args.dataset, fast=args.fast, workers=args.workers
    )
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    # Ensure creds present
    gac = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not gac or not os.path.exists(gac):
        print(
            "WARNING: GOOGLE_APPLICATION_CREDENTIALS not set or file missing. "
            "Set it to your service account JSON (e.g., export GOOGLE_APPLICATION_CREDENTIALS=./jibber_jabber_key.json)."
        )
    main()
