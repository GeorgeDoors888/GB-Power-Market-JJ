#!/bin/bash
# Skip BOD Dataset Temporarily to Unblock Pipeline

echo "=========================================="
echo "WORKAROUND: Skip BOD Dataset"
echo "$(date)"
echo "=========================================="
echo ""

echo "Problem: BOD table has permission errors blocking entire pipeline"
echo "Solution: Temporarily move BOD files aside so other datasets can process"
echo ""

ssh root@94.237.55.234 '
cd /opt/iris-pipeline/iris-clients/python/iris_data

echo "1️⃣ Stopping uploader..."
killall python3 2>/dev/null
pkill -f iris_to_bigquery 2>/dev/null
sleep 3

echo ""
echo "2️⃣ Moving BOD files aside..."
if [ -d BOD ]; then
    mv BOD BOD_SKIP
    echo "   ✅ BOD moved to BOD_SKIP"
    ls -ld BOD_SKIP
else
    echo "   ℹ️  BOD directory not found or already moved"
fi

echo ""
echo "3️⃣ Checking files remaining:"
for dir in MELS MILS INDO INDDEM INDGEN; do
    if [ -d "$dir" ]; then
        count=$(find "$dir" -name "*.json" 2>/dev/null | wc -l)
        echo "   $dir: $count files"
    fi
done

echo ""
echo "4️⃣ Restarting uploader (without BOD)..."
cd /opt/iris-pipeline
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json
export BQ_PROJECT=inner-cinema-476211-u9
source .venv/bin/activate

nohup bash -c "while true; do python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1; sleep 30; done" > /dev/null 2>&1 &

sleep 3
echo "   Process started: PID $!"

echo ""
echo "5️⃣ Verifying:"
ps aux | grep iris_to_bigquery | grep -v grep

echo ""
echo "6️⃣ Monitoring first cycle..."
sleep 10
tail -20 logs/iris_uploader.log

echo ""
echo "=========================================="
echo "✅ BOD SKIPPED - Pipeline should now process MELS/MILS/INDO"
echo "=========================================="
echo ""
echo "Expected behavior:"
echo "  - MELS will process (~176K files remaining)"
echo "  - Then MILS (~91K files)"
echo "  - Then INDO (344 files) ← YOUR TARGET!"
echo ""
echo "BOD can be processed later after fixing permissions."
'
