#!/bin/bash
# Simple IRIS fix - just run: bash quick_fix.sh

echo "Fixing IRIS mapping..."

ssh root@94.237.55.234 << 'EOF'
cd /opt/iris-pipeline
cp iris_to_bigquery_unified.py iris_to_bigquery_unified.py.backup

cat > /tmp/fix.py << 'PYEOF'
import re
with open('/opt/iris-pipeline/iris_to_bigquery_unified.py', 'r') as f:
    content = f.read()
new = """DATASET_TABLE_MAPPING = {
    'BOALF': 'bmrs_boalf_iris', 'BOD': 'bmrs_bod_iris', 'MILS': 'bmrs_mils_iris',
    'MELS': 'bmrs_mels_iris', 'FREQ': 'bmrs_freq_iris', 'FUELINST': 'bmrs_fuelinst_iris',
    'REMIT': 'bmrs_remit_iris', 'MID': 'bmrs_mid_iris', 'BEB': 'bmrs_beb_iris',
    'BOAV': 'bmrs_boav_iris', 'DISEBSP': 'bmrs_disebsp_iris', 'DISPTAV': 'bmrs_disptav_iris',
    'EBOCF': 'bmrs_ebocf_iris', 'ISPSTACK': 'bmrs_ispstack_iris', 'SMSG': 'bmrs_smsg_iris',
    'INDO': 'bmrs_indo_iris', 'INDGEN': 'bmrs_indgen_iris', 'INDDEM': 'bmrs_inddem_iris', 'WINDFOR': 'bmrs_windfor_iris',
}"""
content = re.sub(r"DATASET_TABLE_MAPPING = \{[^}]+\}", new, content, flags=re.DOTALL)
with open('/opt/iris-pipeline/iris_to_bigquery_unified.py', 'w') as f:
    f.write(content)
PYEOF

python3 /tmp/fix.py
echo "✅ Mapping updated"

grep "'INDO'" iris_to_bigquery_unified.py > /dev/null && echo "✅ INDO confirmed" || echo "❌ FAILED"

screen -S iris_uploader -X quit
sleep 2
screen -dmS iris_uploader bash -c 'export GOOGLE_APPLICATION_CREDENTIALS="/opt/iris-pipeline/service_account.json"; export BQ_PROJECT="inner-cinema-476211-u9"; cd /opt/iris-pipeline; source .venv/bin/activate; while true; do python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1; sleep 300; done'
echo "✅ Uploader restarted"

tail -10 logs/iris_uploader.log
EOF

echo ""
echo "✅ DONE! Monitor with: ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'"
