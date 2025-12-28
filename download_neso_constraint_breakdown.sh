#!/bin/bash
# Download NESO Constraint Breakdown (2017-2026)
# Dataset: Constraint Breakdown Costs and Volume
# ID: fb56b46e-cef3-4eb8-9294-0ca19769b7eb
# 
# Categories: Thermal, Voltage, Inertia constraints (costs & volumes)
# Time: ~1 hour (9 files @ 5 min each with rate limits)

set -e

PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
TABLE_BASE="neso_constraint_breakdown"

echo "📥 NESO Constraint Breakdown Download (2017-2026)"
echo "================================================================"
echo "Project: $PROJECT_ID"
echo "Dataset: $DATASET"
echo "Table: ${TABLE_BASE}_YYYY"
echo ""

# Array of resource IDs and years
declare -A RESOURCES=(
  ["2017-2018"]="3651e9e3-52a8-46b6-a675-3a4c2aedc813"
  ["2018-2019"]="26af8438-1824-4436-9bbd-d397a9a517e2"
  ["2019-2020"]="c4d2be3a-4c05-4fac-be7e-56368ca46142"
  ["2020-2021"]="87088ac4-72d5-48ff-9ee1-f2a99e18277a"
  ["2021-2022"]="419337fb-f609-45e3-9097-798a41b4b3de"
  ["2022-2023"]="efb633ae-f6d7-444b-8759-449ac0539dd0"
  ["2023-2024"]="24d067d8-1328-452a-9720-21cb691e491e"
  ["2024-2025"]="748557ef-2bb3-41c0-8181-5f1a148c1ff4"
  ["2025-2026"]="6afe1c2b-6d70-4e76-8e74-0952b0a2beab"
)

# Download each year
COUNT=1
TOTAL=${#RESOURCES[@]}

for year in "${!RESOURCES[@]}"; do
  uuid=${RESOURCES[$year]}
  table_name="${TABLE_BASE}_${year//-/_}"  # Replace hyphen with underscore
  
  echo ""
  echo "[$COUNT/$TOTAL] Processing $year..."
  echo "  Resource ID: $uuid"
  echo "  Table: $table_name"
  
  # Run ingestion
  python3 ingest_neso_api.py \
    --resource-id "$uuid" \
    --table-name "$table_name"
  
  if [ $? -eq 0 ]; then
    echo "  ✅ Success: $year"
  else
    echo "  ❌ Failed: $year"
    exit 1
  fi
  
  # Rate limit: Wait 60 seconds between downloads
  if [ $COUNT -lt $TOTAL ]; then
    echo "  ⏳ Waiting 60 seconds (rate limit)..."
    sleep 60
  fi
  
  COUNT=$((COUNT + 1))
done

echo ""
echo "================================================================"
echo "✅ COMPLETE: All 9 years downloaded"
echo ""
echo "Verify in BigQuery:"
echo "  python3 -c \"from google.cloud import bigquery; client = bigquery.Client(project='$PROJECT_ID', location='US'); [print(f'✅ {t.table_id}: {t.num_rows:,} rows') for t in client.list_tables('$PROJECT_ID.$DATASET') if t.table_id.startswith('$TABLE_BASE')]\""
echo ""
echo "Next: Search for MBSS and Skip Rate datasets"
echo "  python3 ingest_neso_api.py --search 'MBSS'"
echo "  python3 ingest_neso_api.py --search 'skip rate'"
