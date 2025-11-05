#!/bin/bash
# Grant BigQuery Data Editor permissions to service account
# Fixes: 403 Permission bigquery.tables.updateData denied

PROJECT_ID="inner-cinema-476211-u9"
SERVICE_ACCOUNT="all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
ROLE="roles/bigquery.dataEditor"

echo ""
echo "======================================================================"
echo "  BigQuery Permissions Grant Tool"
echo "======================================================================"
echo ""
echo "🔐 Granting BigQuery permissions..."
echo "   Project: $PROJECT_ID"
echo "   Service Account: $SERVICE_ACCOUNT"
echo "   Role: $ROLE"
echo ""

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    echo "❌ ERROR: gcloud CLI not installed"
    echo ""
    echo "Install gcloud:"
    echo "   https://cloud.google.com/sdk/docs/install"
    echo ""
    exit 1
fi

# Check if authenticated
if ! gcloud auth list 2>&1 | grep -q "ACTIVE"; then
    echo "⚠️  Not authenticated with gcloud"
    echo ""
    echo "Authenticating..."
    gcloud auth login
fi

# Set project
echo "📋 Setting project..."
gcloud config set project $PROJECT_ID

echo ""
echo "➕ Adding IAM policy binding..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="$ROLE" \
    --condition=None

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Permissions granted:"
    echo "   ✓ $SERVICE_ACCOUNT"
    echo "   ✓ Can now insert/update BigQuery tables"
    echo "   ✓ bigquery.tables.updateData permission active"
    echo ""
    echo "🔄 Note: May take 1-2 minutes to propagate"
    echo ""
    
    # Verify
    echo "🔍 Verifying permissions..."
    echo ""
    gcloud projects get-iam-policy $PROJECT_ID \
        --flatten="bindings[].members" \
        --filter="bindings.members:serviceAccount:$SERVICE_ACCOUNT" \
        --format="table(bindings.role)"
    
    echo ""
else
    echo ""
    echo "❌ FAILED to grant permissions"
    echo ""
    echo "📝 Manual steps:"
    echo "   1. Open: https://console.cloud.google.com/iam-admin/iam?project=$PROJECT_ID"
    echo "   2. Find: $SERVICE_ACCOUNT"
    echo "   3. Click: Edit (pencil icon)"
    echo "   4. Click: ADD ANOTHER ROLE"
    echo "   5. Select: BigQuery Data Editor"
    echo "   6. Click: SAVE"
    echo ""
fi

echo "======================================================================"
echo ""
