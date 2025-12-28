#!/bin/bash
# Create 4 additional service accounts for 5x Google Sheets API quota
# Run this on your local machine with gcloud CLI configured

PROJECT_ID="inner-cinema-476211-u9"

echo "Creating 4 additional service accounts for quota rotation..."
echo "Project: $PROJECT_ID"
echo ""

for i in {2..5}; do
    SA_NAME="sheets-api-account-${i}"
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
    KEY_FILE="inner-cinema-credentials-${i}.json"

    echo "[$i/4] Creating service account: $SA_NAME"

    # Create service account
    gcloud iam service-accounts create $SA_NAME \
        --display-name="Google Sheets API Account ${i}" \
        --project=$PROJECT_ID

    # Grant necessary roles
    echo "  → Granting BigQuery roles..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/bigquery.user" \
        --condition=None

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="roles/bigquery.dataViewer" \
        --condition=None

    # Create and download key
    echo "  → Creating key file: $KEY_FILE"
    gcloud iam service-accounts keys create $KEY_FILE \
        --iam-account=$SA_EMAIL \
        --project=$PROJECT_ID

    echo "  ✅ Service account ${i} created"
    echo "  📧 Email: $SA_EMAIL"
    echo "  🔑 Key saved: $KEY_FILE"
    echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "✅ All 4 service accounts created!"
echo ""
echo "NEXT STEPS:"
echo "1. Share Google Sheets with each service account email:"
echo "   sheets-api-account-2@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   sheets-api-account-3@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   sheets-api-account-4@${PROJECT_ID}.iam.gserviceaccount.com"
echo "   sheets-api-account-5@${PROJECT_ID}.iam.gserviceaccount.com"
echo ""
echo "2. Upload credential files to server:"
echo "   scp inner-cinema-credentials-*.json root@94.237.55.234:/home/george/GB-Power-Market-JJ/"
echo ""
echo "3. Verify files on server:"
echo "   ls -la /home/george/GB-Power-Market-JJ/inner-cinema-credentials-*.json"
echo ""
echo "4. The cache manager will automatically detect and use all accounts!"
echo "   Quota: 60 req/min × 5 accounts = 300 req/min"
echo "═══════════════════════════════════════════════════════════════"
