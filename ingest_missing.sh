#!/usr/bin/env bash
set -euo pipefail

# --- Defaults you can override with flags ---
START="2016-01-01"
END="$(date -u +%Y-%m-%d)"
DATASETS="BOAL,BOALF,NETBSAD,BOD,DISBSAD"
PROJECT="jibber-jabber-knowledge"
BQDATASET="uk_energy_prod"
LOGLEVEL="INFO"
OVERWRITE="0"

usage() {
  cat <<EOF
Usage: $0 [-s START] [-e END] [-d DATASETS] [-p PROJECT] [-t BQDATASET] [-l LOGLEVEL] [-o]

Runs ingest_elexon_all.py in safe yearly slices and produces a TXT report.

Options:
  -s START       ISO date (default: ${START})
  -e END         ISO date (default: ${END})
  -d DATASETS    Comma-separated list (default: ${DATASETS})
  -p PROJECT     BigQuery project (default: ${PROJECT})
  -t BQDATASET   BigQuery dataset (default: ${BQDATASET})
  -l LOGLEVEL    DEBUG|INFO|WARNING|ERROR (default: ${LOGLEVEL})
  -o             Overwrite range in BigQuery (delete+reload)
Examples:
  $0 -d BOAL,BOALF -s 2019-01-01 -e 2020-01-01
EOF
}

while getopts "s:e:d:p:t:l:oh" opt; do
  case "$opt" in
    s) START="$OPTARG" ;;
    e) END="$OPTARG" ;;
    d) DATASETS="$OPTARG" ;;
    p) PROJECT="$OPTARG" ;;
    t) BQDATASET="$OPTARG" ;;
    l) LOGLEVEL="$OPTARG" ;;
    o) OVERWRITE="1" ;;
    h) usage; exit 0 ;;
    *) usage; exit 2 ;;
  esac
done

# --- Sanity checks ---
if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
  echo "ERROR: GOOGLE_APPLICATION_CREDENTIALS is not set." >&2
  exit 2
fi
if [[ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]]; then
  echo "ERROR: GOOGLE_APPLICATION_CREDENTIALS points to a non-existent file: $GOOGLE_APPLICATION_CREDENTIALS" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$SCRIPT_DIR/ingest_elexon_all.py"
if [[ ! -f "$PY" ]]; then
  echo "ERROR: ingest_elexon_all.py not found next to this script." >&2
  exit 2
fi

mkdir -p "$SCRIPT_DIR/logs" "$SCRIPT_DIR/reports"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT="$SCRIPT_DIR/reports/ingest_report_${STAMP}.txt"

# Header
{
  echo "=================================================="
  echo "Elexon Ingestion Run Report"
  echo "=================================================="
  echo "Project: $PROJECT"
  echo "Dataset: $BQDATASET"
  echo "Period : $START to $END"
  echo "Datasets: $DATASETS"
  echo "UTC Started: $(date -u +%FT%T%:z)"
  echo "--------------------------------------------------"
} > "$REPORT"

# Build yearly slices using Python (portable on macOS/Linux)
export START END # Make variables available to python subprocess
SLICES=()
while IFS= read -r line; do
  [[ -n "$line" ]] && SLICES+=("$line")
done < <(python3 - <<PY
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import os, sys

start = datetime.fromisoformat(os.environ["START"] + "T00:00:00")
end   = datetime.fromisoformat(os.environ["END"]   + "T00:00:00")

cur = start
out = []
while cur < end:
    nxt = min(cur + relativedelta(years=1), end)
    out.append(f"{cur.date()} {nxt.date()}")
    cur = nxt

print("\n".join(out))
PY
)

# Iterate datasets × slices
IFS=',' read -r -a DS_ARR <<< "$DATASETS"

for ds in "${DS_ARR[@]}"; do
  ds_trimmed="$(echo "$ds" | xargs)"
  echo "" | tee -a "$REPORT"
  echo "== Dataset: ${ds_trimmed} ==" | tee -a "$REPORT"
  for line in "${SLICES[@]}"; do
    s="${line%% *}"
    e="${line##* }"
    LOG="$SCRIPT_DIR/logs/${ds_trimmed}_${s}_${e}.log"
    echo "-- ${s} → ${e}" | tee -a "$REPORT"

    # Assemble flags
    extra=()
    [[ "$OVERWRITE" == "1" ]] && extra+=(--overwrite)

    # Run and tee logs per slice
    set +e
    python3 "$PY" \
      --start "$s" --end "$e" \
      --only "$ds_trimmed" \
      --project "$PROJECT" \
      --dataset "$BQDATASET" \
      --log-level "$LOGLEVEL" \
      "${extra[@]}" 2>&1 | tee "$LOG"
    rc="${PIPESTATUS[0]}"
    set -e

    # Extract a one-line outcome for the report
    # Prefer the per-dataset finish line, fall back to final summary
    status_line="$(grep -E 'Finished ingest for '"$ds_trimmed"'|loaded [0-9]+ rows|PARTIAL|SKIP|ERR' "$LOG" | tail -n 1 || true)"
    if [[ -z "$status_line" ]]; then
      status_line="(no status line found, exit=$rc)"
    fi
    echo "   -> ${status_line}" | tee -a "$REPORT"
  done
done

{
  echo "--------------------------------------------------"
  echo "UTC Finished: $(date -u +%FT%T%:z)"
  echo "Report saved: $REPORT"
  echo "Logs in: $SCRIPT_DIR/logs/"
  echo "=================================================="
} >> "$REPORT"

echo ""
echo "✅ Done. Report: $REPORT"
