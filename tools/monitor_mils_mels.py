#!/usr/bin/env python3
"""
Quick progress monitor for MILS/MELS backfills.
Prints row counts and recent ingestion windows to help track progress.

Usage:
  GOOGLE_APPLICATION_CREDENTIALS=./jibber_jabber_key.json \
  python tools/monitor_mils_mels.py --project jibber-jabber-knowledge --dataset uk_energy_insights
"""
from __future__ import annotations

import argparse
import datetime as dt

from google.cloud import bigquery


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--limit", type=int, default=10, help="Show last N windows")
    ap.add_argument(
        "--start", help="Optional ISO date (YYYY-MM-DD) to compute progress"
    )
    ap.add_argument("--end", help="Optional ISO date (YYYY-MM-DD) to compute progress")
    args = ap.parse_args()

    client = bigquery.Client(project=args.project)

    start = None
    end = None
    if args.start and args.end:
        start = dt.datetime.fromisoformat(args.start).date()
        end = dt.datetime.fromisoformat(args.end).date()

    for tbl in ("bmrs_mils", "bmrs_mels"):
        table_id = f"{args.project}.{args.dataset}.{tbl}"
        try:
            t = client.get_table(table_id)
        except Exception as e:
            print(f"\nTable: {table_id} (not found: {e})")
            continue
        print(f"\nTable: {t.full_table_id}")
        print(f"  Rows: {t.num_rows}")
        print(f"  Modified: {t.modified}")
        # Progress vs expected windows
        if start and end:
            total_days = (end - start).days
            q_prog = f"""
      SELECT COUNT(DISTINCT _window_from_utc) AS windows,
           MIN(_window_from_utc) AS min_w,
           MAX(_window_from_utc) AS max_w
      FROM `{args.project}.{args.dataset}.{tbl}`
      WHERE _window_from_utc IS NOT NULL
        AND CAST(_window_from_utc AS DATE) >= DATE('{start}')
        AND CAST(_window_from_utc AS DATE) < DATE('{end}')
      """
            r = list(client.query(q_prog).result())[0]
            done = int(r.windows or 0)
            pct = (done / total_days * 100.0) if total_days else 0.0
            print(f"  Windows loaded: {done}/{total_days} (~{pct:.1f}%)")
            if r.min_w and r.max_w:
                print(f"  Range observed: {r.min_w} → {r.max_w}")

        # Recent windows
        q = f"""
    SELECT _window_from_utc, _window_to_utc, COUNT(*) AS rows
    FROM `{args.project}.{args.dataset}.{tbl}`
    WHERE _window_from_utc IS NOT NULL
    GROUP BY 1,2
    ORDER BY _window_from_utc DESC
    LIMIT {args.limit}
    """
        rows = client.query(q).result()
        print("  Recent windows:")
        for r in rows:
            print(f"    {r._window_from_utc} → {r._window_to_utc}  rows={r.rows}")


if __name__ == "__main__":
    main()
