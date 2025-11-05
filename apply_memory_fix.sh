#!/bin/bash
# Apply memory fix to IRIS uploader

echo "=========================================="
echo "APPLYING MEMORY FIX"
echo "$(date)"
echo "=========================================="
echo ""

echo "🔧 Connecting to server..."
ssh root@94.237.55.234 '
cd /opt/iris-pipeline

echo "1️⃣ Creating backup..."
cp iris_to_bigquery_unified.py iris_to_bigquery_unified.py.pre_500_fix
echo "   ✅ Backup saved as iris_to_bigquery_unified.py.pre_500_fix"
echo ""

echo "2️⃣ Applying memory fix..."
sed -i "s/MAX_FILES_PER_SCAN = 1000/MAX_FILES_PER_SCAN = 500/" iris_to_bigquery_unified.py
sed -i "s/BATCH_SIZE = 5000/BATCH_SIZE = 2000/" iris_to_bigquery_unified.py
echo "   ✅ Configuration updated"
echo ""

echo "3️⃣ Verifying changes..."
grep -E "MAX_FILES_PER_SCAN|BATCH_SIZE" iris_to_bigquery_unified.py | head -3
echo ""

echo "4️⃣ Stopping old uploader..."
screen -S iris_uploader -X quit 2>/dev/null
killall python3 2>/dev/null
sleep 2
echo "   ✅ Old process stopped"
echo ""

echo "5️⃣ Starting uploader with new settings..."
screen -dmS iris_uploader bash -c "
  export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json;
  export BQ_PROJECT=inner-cinema-476211-u9;
  source .venv/bin/activate;
  while true; do 
    python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1;
    sleep 30;
  done
"
sleep 3
echo "   ✅ Uploader started"
echo ""

echo "6️⃣ Verifying process is running..."
ps aux | grep iris_to_bigquery | grep -v grep
echo ""

echo "7️⃣ Showing last 10 log lines..."
tail -10 logs/iris_uploader.log
echo ""

echo "=========================================="
echo "✅ MEMORY FIX APPLIED"
echo "=========================================="
echo ""
echo "New settings:"
echo "  - MAX_FILES_PER_SCAN: 500 (was 1000)"
echo "  - BATCH_SIZE: 2000 (was 5000)"
echo "  - Memory safe for 1.8 GB RAM server"
echo ""
echo "Monitor progress:"
echo "  ssh root@94.237.55.234 \"tail -f /opt/iris-pipeline/logs/iris_uploader.log\""
'

echo ""
echo "🎯 Done! Check progress in a few minutes:"
echo "   bash check_after_restart.sh"
