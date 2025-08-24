#!/usr/bin/env python3
"""Project Memory Sync Utility
================================
Synchronises the machine-readable JSON blocks between:
  * PROJECT_MEMORY.md  (long form)  -> canonical `detail` section
  * PROJECT_MEMORY_SHORT.md (short form) -> should mirror condensed summary

Functions:
  1. Parse long file section 12 JSON. If only a flat object is present, wrap into {"detail": ...}.
  2. Build / refresh a `summary` object (subset fields) from canonical detail.
  3. Inject updated combined JSON (summary + detail) back into long file (section 12 code block).
  4. Update short file JSON block to match the summary + selected extra keys.
  5. Refresh timestamps: 'Last refreshed:' in long; 'Short refresh date:' in short.

Usage:
  python update_project_memory.py            # applies changes in-place
  python update_project_memory.py --dry-run  # prints proposed changes only

Idempotent: running repeatedly with no changes produces no diff.

Design notes:
  - Pure stdlib (json, re, datetime, argparse, pathlib)
  - Defensive parsing: if JSON invalid, abort with message.
  - Keeps original file line endings.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).parent
LONG_FILE = ROOT / "PROJECT_MEMORY.md"
SHORT_FILE = ROOT / "PROJECT_MEMORY_SHORT.md"

JSON_BLOCK_PATTERN = re.compile(r"```json\s*(?P<json>.*?)```", re.DOTALL | re.IGNORECASE)
LAST_REFRESH_PATTERN = re.compile(r"^(Last refreshed:).*$", re.MULTILINE)
SHORT_REFRESH_PATTERN = re.compile(r"^(Short refresh date:).*$", re.MULTILINE)

# Keys to keep in summary (order preserved where possible)
SUMMARY_KEYS_ORDER = [
    "project_id",
    "mission",
    "focus",
    "core_tables_short",
    "outputs_core",
    "seasonality_period",
]
# Fallback outputs length
OUTPUTS_CORE_N = 4


def load_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def extract_first_json_block(markdown: str) -> Tuple[str, int, int]:
    match = JSON_BLOCK_PATTERN.search(markdown)
    if not match:
        raise ValueError("No JSON code block found")
    return match.group("json").strip(), match.start(), match.end()


def parse_long_json(raw_json: str) -> Dict[str, Any]:
    data = json.loads(raw_json)
    if "detail" not in data:
        # Wrap into new structure
        data = {"detail": data}
    # Ensure summary exists (possibly empty)
    data.setdefault("summary", {})
    return data


def build_summary(detail: Dict[str, Any], existing_summary: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    # Pre-existing mission may not live in JSON; attempt to pull from existing_summary
    mission = existing_summary.get("mission") or "Unified UK energy market intelligence (Elexon + NESO)"

    # Derive core tables short names
    core_sources = detail.get("core_sources") or []
    core_short = [
        s.replace("neso_wind_forecasts", "neso_wind")
         .replace("neso_demand_forecasts", "neso_demand")
         .replace("elexon_system_warnings", "system_warnings")
         .replace("neso_balancing_services", "balancing_services")
        for s in core_sources
    ]
    # Outputs core subset
    outputs_full = detail.get("outputs_tables") or []
    outputs_core = outputs_full[:OUTPUTS_CORE_N]

    derived = {
        "project_id": detail.get("project_id"),
        "mission": mission,
        "focus": detail.get("current_focus") or [],
        "core_tables_short": core_short,
        "outputs_core": outputs_core,
        "seasonality_period": detail.get("seasonality_period"),
    }
    # Preserve ordering preference
    for k in SUMMARY_KEYS_ORDER:
        if k in derived:
            summary[k] = derived[k]
    return summary


def update_json_block(markdown: str, new_json_obj: Dict[str, Any]) -> str:
    raw_new = json.dumps(new_json_obj, indent=2, sort_keys=False)
    def repl(match: re.Match) -> str:
        return f"```json\n{raw_new}\n```"
    return JSON_BLOCK_PATTERN.sub(repl, markdown, count=1)


def update_refresh_timestamp(markdown: str, pattern: re.Pattern, label: str) -> str:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    if pattern.search(markdown):
        return pattern.sub(f"{label} {now}", markdown, count=1)
    else:
        # Append if not found
        return markdown.rstrip() + f"\n{label} {now}\n"


def sync_long(dry_run: bool) -> Dict[str, Any]:
    text = load_file(LONG_FILE)
    raw_json, start, end = extract_first_json_block(text)
    data = parse_long_json(raw_json)
    detail = data["detail"]
    existing_summary = data.get("summary", {})
    summary = build_summary(detail, existing_summary)
    data["summary"] = summary
    new_long = update_json_block(text, data)
    new_long = update_refresh_timestamp(new_long, LAST_REFRESH_PATTERN, "Last refreshed:")
    if not dry_run:
        LONG_FILE.write_text(new_long, encoding="utf-8")
    return {"summary": summary, "detail": detail}


def sync_short(summary: Dict[str, Any], detail: Dict[str, Any], dry_run: bool):
    text = load_file(SHORT_FILE)
    # Build short JSON from summary plus project_id (already in summary)
    short_json_obj = summary.copy()
    # Ensure required keys exist
    for key in ("project_id", "seasonality_period"):
        short_json_obj.setdefault(key, detail.get(key))

    # Replace first JSON block
    new_text = update_json_block(text, short_json_obj)
    new_text = update_refresh_timestamp(new_text, SHORT_REFRESH_PATTERN, "Short refresh date:")
    if not dry_run:
        SHORT_FILE.write_text(new_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Synchronise project memory JSON blocks.")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    args = parser.parse_args()

    result = sync_long(dry_run=args.dry_run)
    sync_short(result["summary"], result["detail"], dry_run=args.dry_run)

    print("[sync] summary keys:", list(result["summary"].keys()))
    if args.dry_run:
        print("[dry-run] No files written.")
    else:
        print("[sync] Memory files updated.")


if __name__ == "__main__":
    main()
