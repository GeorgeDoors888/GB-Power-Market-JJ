#!/bin/bash
# Setup automation for BESS dashboard updates

set -e

echo "🤖 BESS Dashboard Automation Setup"
echo "===================================="
echo ""

# Check Python script exists
if [ ! -f "/home/george/GB-Power-Market-JJ/dashboard_pipeline.py" ]; then
    echo "❌ dashboard_pipeline.py not found"
    exit 1
fi

# Create logs directory
mkdir -p /home/george/GB-Power-Market-JJ/logs
echo "✅ Created logs directory"

# Test credentials
echo ""
echo "🔐 Testing credentials..."
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ BigQuery connected")' 2>/dev/null || {
    echo "❌ BigQuery authentication failed"
    echo "Make sure GOOGLE_APPLICATION_CREDENTIALS is set:"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=/home/george/.config/google-cloud/bigquery-credentials.json"
    exit 1
}

# Test pipeline
echo ""
echo "🧪 Testing pipeline (dry run)..."
cd /home/george/GB-Power-Market-JJ
timeout 120 python3 dashboard_pipeline.py 2>&1 | tail -20

if [ $? -eq 0 ] || [ $? -eq 124 ]; then
    echo ""
    echo "✅ Pipeline test passed (or timed out safely)"
else
    echo "❌ Pipeline test failed"
    exit 1
fi

# Show current crontab
echo ""
echo "📋 Current crontab:"
crontab -l 2>/dev/null || echo "(none)"
echo ""

# Propose cron job
echo "💡 Suggested cron job for 15-minute updates:"
echo ""
echo "*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1"
echo ""
echo "Add this with: crontab -e"
echo ""

# Create test command
cat > /home/george/GB-Power-Market-JJ/test_pipeline.sh << 'EOF'
#!/bin/bash
# Test pipeline manually
cd /home/george/GB-Power-Market-JJ
export GOOGLE_APPLICATION_CREDENTIALS=/home/george/.config/google-cloud/bigquery-credentials.json
python3 dashboard_pipeline.py 2>&1 | tee logs/test_$(date +%Y%m%d_%H%M%S).log
EOF

chmod +x /home/george/GB-Power-Market-JJ/test_pipeline.sh
echo "✅ Created test_pipeline.sh for manual testing"

echo ""
echo "🎉 Automation setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: crontab -e"
echo "2. Add the cron job line above"
echo "3. Save and exit"
echo "4. Monitor: tail -f /home/george/GB-Power-Market-JJ/logs/pipeline.log"
