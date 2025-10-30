import argparse
import json
from typing import Dict, List, Optional

from google.cloud import bigquery


def get_tables(
    client: bigquery.Client, dataset_id: str, only: Optional[List[str]] = None
) -> List[str]:
    tables = []
    for tbl in client.list_tables(dataset_id):
        name = tbl.table_id
        if only and name not in only:
            continue
        tables.append(name)
    return tables


def fetch_metadata_via_api(
    client: bigquery.Client, dataset_fqn: str
) -> Dict[str, Dict]:
    info: Dict[str, Dict] = {}
    for t in client.list_tables(dataset_fqn):
        tbl = client.get_table(t.reference)
        info[tbl.table_id] = {
            "row_count": int(tbl.num_rows or 0),
            "size_bytes": int(getattr(tbl, "num_bytes", 0) or 0),
            "creation_time": (
                str(tbl.created) if getattr(tbl, "created", None) else None
            ),
            "last_modified_time": (
                str(tbl.modified) if getattr(tbl, "modified", None) else None
            ),
        }
    return info


def has_column(client: bigquery.Client, table_id: str, column: str) -> bool:
    table = client.get_table(table_id)
    return any(s.name == column for s in table.schema)


def safe_agg(
    client: bigquery.Client, table_id: str, col: str, fn: str
) -> Optional[str]:
    if not has_column(client, table_id, col):
        return None
    sql = f"SELECT {fn}({col}) AS v FROM `{table_id}`"
    rows = list(client.query(sql).result())
    if not rows:
        return None
    v = rows[0].get("v")
    return str(v) if v is not None else None


def main():
    p = argparse.ArgumentParser(
        description="Report BigQuery watermarks for selected tables"
    )
    p.add_argument("--project", required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument(
        "--tables",
        help="Comma-separated list of table names. If omitted, all tables will be scanned (metadata only).",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="When set, compute watermarks (aggregates) for all tables in the dataset.",
    )
    p.add_argument("--out", help="Optional path to write JSON output")
    args = p.parse_args()

    client = bigquery.Client(project=args.project)
    dataset_fqn = f"{args.project}.{args.dataset}"

    only_tables = [t.strip() for t in args.tables.split(",")] if args.tables else None

    info_schema = fetch_metadata_via_api(client, dataset_fqn)

    results = {}
    tables = get_tables(client, dataset_fqn, only=only_tables)
    for name in tables:
        table_id = f"{dataset_fqn}.{name}"
        meta = info_schema.get(name, {})
        entry = {
            "table": name,
            "row_count": meta.get("row_count"),
            "size_bytes": meta.get("size_bytes"),
            "creation_time": meta.get("creation_time"),
            "last_modified_time": meta.get("last_modified_time"),
            "max__ingested_utc": None,
            "min__window_from_utc": None,
            "max__window_to_utc": None,
        }
        # Detailed watermarks: either explicit tables or all tables if --all
        if only_tables or args.all:
            entry["max__ingested_utc"] = safe_agg(
                client, table_id, "_ingested_utc", "MAX"
            )
            entry["min__window_from_utc"] = safe_agg(
                client, table_id, "_window_from_utc", "MIN"
            )
            entry["max__window_to_utc"] = safe_agg(
                client, table_id, "_window_to_utc", "MAX"
            )
        results[name] = entry

    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
