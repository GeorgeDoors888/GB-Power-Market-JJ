#!/bin/bash
# Setup script for NESO Constraint Data System

echo "🔌 GB Transmission Constraint System Setup"
echo "=========================================="
echo ""

# Check Python dependencies
echo "1️⃣ Checking Python dependencies..."
pip3 install --user google-cloud-bigquery pandas pyarrow requests beautifulsoup4 gspread oauth2client db-dtypes

# Create BigQuery dataset
echo ""
echo "2️⃣ Creating BigQuery dataset uk_constraints..."
bq mk --location=US --dataset inner-cinema-476211-u9:uk_constraints 2>/dev/null || echo "   Dataset already exists"

# Test credentials
echo ""
echo "3️⃣ Testing BigQuery connection..."
python3 -c "from google.cloud import bigquery; import os; os.environ['GOOGLE_APPLICATION_CREDENTIALS']='inner-cinema-credentials.json'; client = bigquery.Client(project='inner-cinema-476211-u9'); print('   ✅ BigQuery connection OK')"

# Test Sheets connection
echo ""
echo "4️⃣ Testing Google Sheets connection..."
python3 -c "import gspread; from oauth2client.service_account import ServiceAccountCredentials; scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']; creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope); gc = gspread.authorize(creds); print('   ✅ Sheets connection OK')"

# Run initial ingestion (dry-run mode)
echo ""
echo "5️⃣ Running initial constraint data ingestion..."
echo "   This will download CSV files from NESO and load into BigQuery"
echo "   Press Ctrl+C to cancel, or wait 10 seconds to continue..."
sleep 10

python3 ingest_neso_constraints.py

# Add to crontab
echo ""
echo "6️⃣ Setting up cron jobs..."
echo ""
echo "   Add these lines to your crontab (crontab -e):"
echo ""
echo "   # NESO Constraint Data - Every 6 hours"
echo "   0 */6 * * * cd \"$PWD\" && python3 ingest_neso_constraints.py >> logs/constraint_ingest.log 2>&1"
echo ""
echo "   # Dashboard Update - Every 5 minutes"
echo "   */5 * * * * cd \"$PWD\" && python3 update_constraints_dashboard.py >> logs/constraint_dashboard.log 2>&1"
echo ""
echo "   Run this command to add them:"
echo "   (crontab -l 2>/dev/null; echo ''; echo '# NESO Constraint Data'; echo '0 */6 * * * cd \"$PWD\" && python3 ingest_neso_constraints.py >> logs/constraint_ingest.log 2>&1'; echo '*/5 * * * * cd \"$PWD\" && python3 update_constraints_dashboard.py >> logs/constraint_dashboard.log 2>&1') | crontab -"

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo "   1. Review BigQuery dataset: bq ls inner-cinema-476211-u9:uk_constraints"
echo "   2. Check Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=0&range=A110"
echo "   3. Monitor logs: tail -f logs/constraint_ingest.log"
echo "   4. Add cron jobs (see above)"
echo ""
echo "📖 Documentation: See next_steps.txt for detailed explanation"
