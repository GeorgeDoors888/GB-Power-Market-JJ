#!/bin/bash
# Deploy BigQuery Views and Run BtM PPA Revenue Analysis

set -e

echo "======================================================================"
echo "DEPLOYING BIGQUERY VIEWS & RUNNING BtM PPA ANALYSIS"
echo "======================================================================"

PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"

# Deploy views using bq command
echo ""
echo "📝 Deploying BigQuery views..."
echo ""

for view in sql/*.sql; do
    echo "Deploying $(basename $view)..."
    bq query --project_id=$PROJECT_ID --use_legacy_sql=false < "$view"
    if [ $? -eq 0 ]; then
        echo "   ✅ Success"
    else
        echo "   ⚠️  Warning: May already exist or syntax issue"
    fi
done

echo ""
echo "======================================================================"
echo "RUNNING REVENUE ANALYSIS"
echo "======================================================================"
echo ""

# Run the Python script
python3 update_btm_ppa_from_bigquery.py

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT COMPLETE"
echo "======================================================================"
echo ""
echo "Check your Google Sheets:"
echo "  - Dashboard Row 7: BtM PPA Profit KPI"
echo "  - Dashboard Row 8: Curtailment Revenue KPI"
echo "  - BESS Sheet: Detailed breakdown (rows 45, 60-66)"
echo ""
