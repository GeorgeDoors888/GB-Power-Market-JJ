#!/bin/bash
# Copy IRIS scripts from repo to deployment package

echo "📦 Copying IRIS scripts from repo..."
echo ""

REPO_DIR="/Users/georgemajor/repo/GB Power Market JJ"
DEPLOY_DIR="/Users/georgemajor/GB Power Market JJ/iris_windows_deployment"

# Copy IRIS client
echo "1. Copying IRIS client..."
if [ -d "$REPO_DIR/iris-clients/python" ]; then
    cp -r "$REPO_DIR/iris-clients/python" "$DEPLOY_DIR/iris_client"
    echo "   ✅ IRIS client copied"
else
    echo "   ❌ IRIS client not found at: $REPO_DIR/iris-clients/python"
fi

# Copy BigQuery processor
echo "2. Copying iris_to_bigquery_unified.py..."
if [ -f "$REPO_DIR/iris_to_bigquery_unified.py" ]; then
    cp "$REPO_DIR/iris_to_bigquery_unified.py" "$DEPLOY_DIR/scripts/"
    echo "   ✅ BigQuery processor copied"
else
    echo "   ❌ BigQuery processor not found at: $REPO_DIR/iris_to_bigquery_unified.py"
fi

# Copy monitoring scripts
echo "3. Copying monitoring scripts..."
if [ -f "$REPO_DIR/check_iris_health.sh" ]; then
    cp "$REPO_DIR/check_iris_health.sh" "$DEPLOY_DIR/scripts/"
    echo "   ✅ Health check script copied"
fi

if [ -f "$REPO_DIR/test_iris_batch.py" ]; then
    cp "$REPO_DIR/test_iris_batch.py" "$DEPLOY_DIR/scripts/"
    echo "   ✅ Test script copied"
fi

echo ""
echo "✅ Done! Now re-creating ZIP archive..."
cd "/Users/georgemajor/GB Power Market JJ"
rm -f iris_windows_deployment.zip
zip -r iris_windows_deployment.zip iris_windows_deployment

echo ""
echo "✅ Package ready: iris_windows_deployment.zip"
echo "📦 Package now includes:"
ls -lh "$DEPLOY_DIR/iris_client/client.py" 2>/dev/null && echo "   ✅ IRIS client"
ls -lh "$DEPLOY_DIR/scripts/iris_to_bigquery_unified.py" 2>/dev/null && echo "   ✅ BigQuery processor"
ls -lh "$DEPLOY_DIR/scripts/check_iris_health.sh" 2>/dev/null && echo "   ✅ Health monitor"
echo ""
