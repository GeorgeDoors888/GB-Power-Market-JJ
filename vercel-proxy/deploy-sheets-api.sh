#!/bin/bash

# Google Sheets API Proxy - Automated Setup Script
# Author: George Major
# Date: 1 December 2025

set -e

echo "🚀 Google Sheets API Proxy - Automated Setup"
echo "=========================================="
echo ""

# Check prerequisites
echo "✅ Checking prerequisites..."

if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Install with: npm install -g vercel"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "❌ jq not found. Install with: brew install jq"
    exit 1
fi

if [ ! -f "../inner-cinema-credentials.json" ]; then
    echo "❌ inner-cinema-credentials.json not found in parent directory"
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Extract credentials
echo "📋 Extracting Google service account credentials..."

PRIVATE_KEY_ID=$(cat ../inner-cinema-credentials.json | jq -r '.private_key_id')
PRIVATE_KEY=$(cat ../inner-cinema-credentials.json | jq -r '.private_key')
CLIENT_EMAIL=$(cat ../inner-cinema-credentials.json | jq -r '.client_email')
CLIENT_ID=$(cat ../inner-cinema-credentials.json | jq -r '.client_id')

echo "   Private Key ID: ${PRIVATE_KEY_ID:0:20}..."
echo "   Client Email: $CLIENT_EMAIL"
echo "   Client ID: $CLIENT_ID"
echo ""

# Set environment variables
echo "🔐 Setting Vercel environment variables..."

# Remove existing vars if they exist
vercel env rm GOOGLE_PRIVATE_KEY_ID production --yes 2>/dev/null || true
vercel env rm GOOGLE_PRIVATE_KEY production --yes 2>/dev/null || true
vercel env rm GOOGLE_CLIENT_EMAIL production --yes 2>/dev/null || true
vercel env rm GOOGLE_CLIENT_ID production --yes 2>/dev/null || true

# Add new vars
echo "$PRIVATE_KEY_ID" | vercel env add GOOGLE_PRIVATE_KEY_ID production
echo "$PRIVATE_KEY" | vercel env add GOOGLE_PRIVATE_KEY production
echo "$CLIENT_EMAIL" | vercel env add GOOGLE_CLIENT_EMAIL production
echo "$CLIENT_ID" | vercel env add GOOGLE_CLIENT_ID production

echo "✅ Environment variables set"
echo ""

# Deploy
echo "🚀 Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""

# Test endpoints
VERCEL_URL="https://gb-power-market-jj.vercel.app"

echo "🧪 Testing endpoints..."
echo ""

echo "1️⃣ Health Check..."
HEALTH_RESPONSE=$(curl -s "$VERCEL_URL/api/sheets?action=health")
if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
    echo "   Response: $HEALTH_RESPONSE"
fi
echo ""

echo "2️⃣ List Sheets..."
SHEETS_RESPONSE=$(curl -s "$VERCEL_URL/api/sheets?action=get_sheets")
SHEET_COUNT=$(echo "$SHEETS_RESPONSE" | jq -r '.count // 0')
if [ "$SHEET_COUNT" -gt 0 ]; then
    echo "   ✅ Found $SHEET_COUNT sheets"
    echo "$SHEETS_RESPONSE" | jq -r '.sheets[]' | head -5 | sed 's/^/      - /'
else
    echo "   ❌ Failed to list sheets"
    echo "   Response: $SHEETS_RESPONSE"
fi
echo ""

echo "3️⃣ Read Test (Dashboard A1:C3)..."
READ_RESPONSE=$(curl -s "$VERCEL_URL/api/sheets?action=read&sheet=Dashboard&range=A1:C3")
ROW_COUNT=$(echo "$READ_RESPONSE" | jq -r '.row_count // 0')
if [ "$ROW_COUNT" -gt 0 ]; then
    echo "   ✅ Read $ROW_COUNT rows"
    echo "$READ_RESPONSE" | jq -r '.values[0][]' | head -3 | sed 's/^/      - /'
else
    echo "   ❌ Failed to read data"
    echo "   Response: $READ_RESPONSE"
fi
echo ""

# Summary
echo "📊 Setup Summary"
echo "================"
echo ""
echo "✅ Vercel deployment: $VERCEL_URL"
echo "✅ API endpoint: $VERCEL_URL/api/sheets"
echo "✅ Spreadsheet: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
echo ""
echo "📚 Next Steps:"
echo "   1. Test endpoints manually (see SHEETS_API_SETUP.md)"
echo "   2. Update ChatGPT custom instructions"
echo "   3. Try asking ChatGPT: 'Show me data from the Dashboard sheet'"
echo ""
echo "🎉 Setup complete!"
