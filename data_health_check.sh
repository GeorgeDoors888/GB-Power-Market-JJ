#!/bin/bash
# Quick Data Health Check - Run this before any analysis
# Usage: ./data_health_check.sh

echo "=============================================================================="
echo "GB POWER MARKET - DATA HEALTH CHECK"
echo "=============================================================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check if credentials exist
if [ ! -f "inner-cinema-credentials.json" ]; then
    echo "❌ ERROR: inner-cinema-credentials.json not found"
    exit 1
fi

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/inner-cinema-credentials.json"

echo "Checking critical tables (last 7 days freshness)..."
echo ""

# Define critical tables and their time columns
declare -A TABLES
TABLES=(
    ["bmrs_bod"]="settlementDate"
    ["bmrs_boalf_complete"]="timeFrom"
    ["bmrs_costs"]="settlementDate"
    ["bmrs_fuelinst"]="startTime"
    ["bmrs_mid"]="settlementDate"
    ["bmrs_indgen_iris"]="startTime"
    ["bmrs_fuelinst_iris"]="startTime"
)

for table in "${!TABLES[@]}"; do
    time_col="${TABLES[$table]}"

    echo "Checking: $table"

    result=$(bq query --use_legacy_sql=false --format=csv --max_rows=1 \
        "SELECT
            MAX(DATE($time_col)) as latest_date,
            COUNT(*) as total_records,
            DATE_DIFF(CURRENT_DATE(), MAX(DATE($time_col)), DAY) as days_behind
        FROM \`inner-cinema-476211-u9.uk_energy_prod.$table\`" 2>&1)

    if echo "$result" | grep -q "Not found"; then
        echo "  ❌ Table does not exist"
    elif echo "$result" | grep -q "Error"; then
        echo "  ⚠️  Error querying table"
    else
        # Parse result (skip header, get data row)
        data=$(echo "$result" | tail -n 1)
        latest=$(echo "$data" | cut -d',' -f1)
        records=$(echo "$data" | cut -d',' -f2)
        days_behind=$(echo "$data" | cut -d',' -f3)

        if [ "$days_behind" -le 2 ]; then
            echo "  ✅ Latest: $latest ($records records, $days_behind days behind)"
        elif [ "$days_behind" -le 7 ]; then
            echo "  ⚠️  Latest: $latest ($records records, $days_behind days behind)"
        else
            echo "  ❌ Latest: $latest ($records records, $days_behind days behind - STALE!)"
        fi
    fi
    echo ""
done

echo "=============================================================================="
echo "IRIS Pipeline Status"
echo "=============================================================================="

# Check IRIS processes on server (if accessible)
if command -v ssh &> /dev/null; then
    echo "Checking IRIS pipeline on server..."
    ssh -o ConnectTimeout=5 root@94.237.55.234 'ps aux | grep -E "(client.py|iris_to_bigquery)" | grep -v grep' 2>/dev/null || echo "⚠️  Cannot connect to IRIS server"
else
    echo "⚠️  SSH not available, skipping IRIS process check"
fi

echo ""
echo "=============================================================================="
echo "Quick Recommendations"
echo "=============================================================================="
echo ""
echo "For comprehensive data audit, run:"
echo "  python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py"
echo ""
echo "For detailed guide, read:"
echo "  GB_POWER_DATA_COMPREHENSIVE_GUIDE_DEC20_2025.md"
echo ""
echo "To check specific table coverage:"
echo "  ./check_table_coverage.sh TABLE_NAME"
echo ""
echo "=============================================================================="
