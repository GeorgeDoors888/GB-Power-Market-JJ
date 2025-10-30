#!/bin/bash
# Quick status check for energy data updates

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"

echo "Energy Data Update Status Check"
echo "==============================="
echo "Current Time: $(date)"
echo ""

# Check if update is currently running
if [[ -f "${SCRIPT_DIR}/.energy_update.lock" ]]; then
    echo "🔄 Update currently running (PID: $(cat "${SCRIPT_DIR}/.energy_update.lock"))"
else
    echo "✅ No update currently running"
fi

echo ""

# Show latest log files
echo "Recent Log Files:"
ls -lt "${LOG_DIR}"/energy_update_*.log 2>/dev/null | head -5 || echo "No log files found"

echo ""

# Show last few lines of most recent log
LATEST_LOG=$(ls -t "${LOG_DIR}"/energy_update_*.log 2>/dev/null | head -1)
if [[ -n "${LATEST_LOG}" ]]; then
    echo "Last 10 lines from: $(basename "${LATEST_LOG}")"
    echo "-------------------------------------------"
    tail -10 "${LATEST_LOG}"
else
    echo "No recent log files found"
fi
