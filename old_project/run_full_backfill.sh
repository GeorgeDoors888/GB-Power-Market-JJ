#!/usr/bin/env bash
set -euo pipefail

# Full historical backfill orchestrator
# Years: 2016-2025 (2025 partial to today-1)
# Uses fast_cloud_backfill.py (resume-safe)

YEARS=(2016 2017 2018 2019 2020 2021 2022 2023 2024)
CURRENT_YEAR=2025
TODAY=$(date -u +%Y-%m-%d)
END_2025=$(date -u -v -1d +%Y-%m-%d 2>/dev/null || date -u -d 'yesterday' +%Y-%m-%d)

PY=python3
SCRIPT=fast_cloud_backfill.py
SUMMARY=generate_collection_summary.py
WORKERS=${WORKERS:-10}

if ! command -v $PY >/dev/null 2>&1; then
  echo "❌ python3 not found" >&2; exit 1
fi

if [ ! -f api.env ]; then
  echo "❌ api.env missing (needs BMRS_API_KEY)" >&2; exit 2
fi

echo "🚀 Starting FULL HISTORICAL BACKFILL at $(date -u)" 
echo "🧵 Workers: $WORKERS" 

echo "ℹ️  2025 partial range: 2025-01-01 -> $END_2025"

month_last_day() {
  # Args: YEAR MONTH -> prints YYYY-MM-DD last day of month
  $PY - <<'PY'
import sys, calendar
Y=int(sys.argv[1]); M=int(sys.argv[2])
print(f"{Y}-{M:02d}-{calendar.monthrange(Y,M)[1]:02d}")
PY
}

run_month() {
  local Y=$1
  local M=$2
  local START="${Y}-${M}-01"
  local LAST=$(month_last_day "$Y" "$M")
  local END=$LAST
    echo "\n—— 📆 ${Y}-${M} (${START} -> ${END}) ——" 
  $PY $SCRIPT $START $END --workers $WORKERS || echo "⚠️ Month ${Y}-${M} run ended with non-zero exit; continuing"
  $PY $SUMMARY || echo "⚠️ Summary generation failed (month ${Y}-${M})"
}

run_year_monthly() {
  local Y=$1
  echo "\n==== 📅 YEAR $Y (monthly segments) ===="
  for M in 01 02 03 04 05 06 07 08 09 10 11 12; do
    run_month "$Y" "$M"
    echo "⏱️  Short pause (3s)"; sleep 3
  done
  echo "🧮 Year $Y complete (monthly). Latest summary generated."
}

# Historical complete years (monthly granularity for frequent summaries)
for Y in "${YEARS[@]}"; do
  run_year_monthly "$Y"
  echo "⏱️  Pause 5s before next year to reduce API burst"; sleep 5
done

echo "\n==== 📅 YEAR $CURRENT_YEAR (partial, monthly) ===="
CUR_MONTH=$(date -u +%m)
for M in 01 02 03 04 05 06 07 08 09 10 11 12; do
  # Stop if month is in future relative to END_2025
  if [ "${CURRENT_YEAR}-${M}-01" \> "$END_2025" ]; then
    break
  fi
  # Compute end date constrained by END_2025
  local_last=$(month_last_day "$CURRENT_YEAR" "$M")
  if [ "$local_last" \> "$END_2025" ]; then
    local_last=$END_2025
  fi
  echo "\n—— 📆 ${CURRENT_YEAR}-${M} (${CURRENT_YEAR}-${M}-01 -> $local_last) ——" 
  $PY $SCRIPT ${CURRENT_YEAR}-${M}-01 $local_last --workers $WORKERS || echo "⚠️ Month ${CURRENT_YEAR}-${M} partial run ended with non-zero exit; continuing"
  $PY $SUMMARY || echo "⚠️ Summary generation failed (month ${CURRENT_YEAR}-${M})"
  [ "$local_last" = "$END_2025" ] && break
  echo "⏱️  Short pause (3s)"; sleep 3
done

echo "\n🏁 FULL BACKFILL ORCHESTRATION COMPLETE at $(date -u)"
echo "📊 Latest summary: collection_summary.json (uploaded to bucket)"
echo "🔁 Safe to re-run this script anytime; already-present objects skipped."
