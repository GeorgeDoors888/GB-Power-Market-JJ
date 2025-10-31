#!/bin/bash
# Quick utility to check BigQuery table date coverage
# Usage: ./check_table_coverage.sh TABLE_NAME

set -e

PROJECT="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
TABLE="${1:-bmrs_bod}"

echo "=============================================="
echo "📊 Table Coverage Check: $TABLE"
echo "=============================================="
echo "Project: $PROJECT"
echo "Dataset: $DATASET"
echo ""

# Check if table exists
if ! bq show "${PROJECT}:${DATASET}.${TABLE}" > /dev/null 2>&1; then
    echo "❌ Error: Table '${TABLE}' not found in ${DATASET}"
    echo ""
    echo "Available tables:"
    bq ls --max_results=200 "${PROJECT}:${DATASET}" | grep "^${TABLE:0:5}" || echo "No matching tables found"
    exit 1
fi

echo "✅ Table exists"
echo ""

# Get schema of date column
echo "📋 Checking date column schema..."
DATE_COLUMN=$(bq show --schema --format=prettyjson "${PROJECT}:${DATASET}.${TABLE}" | \
    grep -E '"name".*"(settlement|publish|measurement)' -A 2 | \
    grep '"name"' | head -1 | cut -d'"' -f4)

if [ -z "$DATE_COLUMN" ]; then
    echo "⚠️  Could not auto-detect date column"
    echo "Common date columns: settlementDate, publishTime, measurementTime"
    echo ""
    read -p "Enter date column name: " DATE_COLUMN
fi

echo "Using date column: $DATE_COLUMN"

DATE_TYPE=$(bq show --schema --format=prettyjson "${PROJECT}:${DATASET}.${TABLE}" | \
    grep -A 1 "\"name\": \"${DATE_COLUMN}\"" | \
    grep '"type"' | cut -d'"' -f4)

echo "Date type: $DATE_TYPE"
echo ""

# Check date range
echo "📅 Checking date range..."

# Build query based on data type
if [ "$DATE_TYPE" = "STRING" ]; then
    QUERY="
    SELECT 
      '${TABLE}' as table_name,
      '${DATE_TYPE}' as date_type,
      MIN(${DATE_COLUMN}) as min_date,
      MAX(${DATE_COLUMN}) as max_date,
      COUNT(DISTINCT ${DATE_COLUMN}) as unique_days,
      COUNT(*) as total_records,
      ROUND(COUNT(*) / COUNT(DISTINCT ${DATE_COLUMN}), 0) as avg_records_per_day
    FROM \`${PROJECT}.${DATASET}.${TABLE}\`
    WHERE ${DATE_COLUMN} IS NOT NULL
    "
else
    QUERY="
    SELECT 
      '${TABLE}' as table_name,
      '${DATE_TYPE}' as date_type,
      CAST(MIN(${DATE_COLUMN}) AS STRING) as min_date,
      CAST(MAX(${DATE_COLUMN}) AS STRING) as max_date,
      COUNT(DISTINCT CAST(${DATE_COLUMN} AS DATE)) as unique_days,
      COUNT(*) as total_records,
      ROUND(COUNT(*) / COUNT(DISTINCT CAST(${DATE_COLUMN} AS DATE)), 0) as avg_records_per_day
    FROM \`${PROJECT}.${DATASET}.${TABLE}\`
    WHERE ${DATE_COLUMN} IS NOT NULL
    "
fi

bq query --use_legacy_sql=false --format=pretty "$QUERY"

echo ""
echo "=============================================="
echo "✅ Coverage check complete"
echo "=============================================="
echo ""
echo "💡 To check another table:"
echo "   ./check_table_coverage.sh TABLE_NAME"
echo ""
echo "📚 Common tables to check:"
echo "   - bmrs_bod (Bid-Offer Data)"
echo "   - bmrs_fuelinst (Generation Mix)"
echo "   - bmrs_freq (System Frequency)"
echo "   - bmrs_mid (Market Prices)"
echo "   - demand_outturn (Demand)"
echo "   - bmrs_bod_iris (Bid-Offer IRIS)"
echo "   - bmrs_fuelinst_iris (Generation IRIS)"
echo ""
