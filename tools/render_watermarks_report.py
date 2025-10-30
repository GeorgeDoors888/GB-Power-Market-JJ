import argparse
import datetime as dt
import json
from typing import Any, Dict, Tuple


def fmt_int(n: int) -> str:
    return f"{n:,}"


def pick(d: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    return {k: d.get(k) for k in keys}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Render Markdown report from watermarks JSON"
    )
    p.add_argument(
        "--inp", required=True, help="Input JSON file (from bq_watermarks.py --all)"
    )
    p.add_argument("--out", required=True, help="Output Markdown file path")
    p.add_argument(
        "--top", type=int, default=15, help="Top-N tables by row_count to list"
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    with open(args.inp, "r", encoding="utf-8") as f:
        data: Dict[str, Dict[str, Any]] = json.load(f)

    # Aggregate
    total_tables = len(data)
    non_empty = {t: m for t, m in data.items() if (m.get("row_count") or 0) > 0}
    empty_count = total_tables - len(non_empty)
    total_rows = sum(int(m.get("row_count") or 0) for m in data.values())

    # Sort by row_count desc
    top_items = sorted(
        non_empty.items(), key=lambda kv: int(kv[1].get("row_count") or 0), reverse=True
    )[: args.top]

    # Focus set
    focus_tables = [
        "bmrs_bod",
        "bmrs_boalf",
        "bmrs_freq",
        "bmrs_fuelinst",
        "bmrs_mels",
        "bmrs_mils",
        "iris_stream_data",
    ]
    focus = [(t, data[t]) for t in focus_tables if t in data]

    now = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    lines: list[str] = []
    lines.append(f"# Ingestion Report\n")
    lines.append(f"Generated: {now}\n")
    lines.append("")
    lines.append("## Summary\n")
    lines.append(f"- Total tables: {total_tables}")
    lines.append(f"- Non-empty tables: {len(non_empty)}")
    lines.append(f"- Empty tables: {empty_count}")
    lines.append(f"- Total rows across all tables: {fmt_int(total_rows)}\n")

    if focus:
        lines.append("## Key tables\n")
        for name, m in focus:
            row_count = fmt_int(int(m.get("row_count") or 0))
            min_w = m.get("min__window_from_utc")
            max_w = m.get("max__window_to_utc")
            last_ing = m.get("max__ingested_utc")
            lines.append(
                f"- {name}: rows {row_count}; window [{min_w} → {max_w}]; last_ingested {last_ing}"
            )
        lines.append("")

    lines.append("## Top tables by row count\n")
    for name, m in top_items:
        row_count = fmt_int(int(m.get("row_count") or 0))
        max_w = m.get("max__window_to_utc")
        last_ing = m.get("max__ingested_utc")
        size_b = int(m.get("size_bytes") or 0)
        lines.append(
            f"- {name}: rows {row_count}; size {fmt_int(size_b)} bytes; max_window {max_w}; last_ingested {last_ing}"
        )
    lines.append("")

    # Recent activity: last_modified_time desc for non-empty
    recent = sorted(
        non_empty.items(),
        key=lambda kv: str(kv[1].get("last_modified_time") or ""),
        reverse=True,
    )[: args.top]
    lines.append("## Recently modified tables\n")
    for name, m in recent:
        row_count = fmt_int(int(m.get("row_count") or 0))
        last_mod = m.get("last_modified_time")
        last_ing = m.get("max__ingested_utc")
        lines.append(
            f"- {name}: rows {row_count}; last_modified {last_mod}; last_ingested {last_ing}"
        )
    lines.append("")

    # Zero row tables summary by count only
    lines.append("## Empty tables (count only)\n")
    lines.append(f"- Count: {empty_count}\n")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
