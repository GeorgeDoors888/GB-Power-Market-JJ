#!/bin/bash
# Quick deployment script for Vercel proxy

set -e

echo "🚀 Deploying Vercel Proxy for Railway Codex Server"
echo "=================================================="
echo ""

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

echo "✅ Vercel CLI found"
echo ""

# Login check
echo "📝 Checking Vercel login status..."
if ! vercel whoami &> /dev/null; then
    echo "❌ Not logged in. Please login:"
    vercel login
fi

echo "✅ Logged in to Vercel"
echo ""

# Deploy
echo "🚀 Deploying to Vercel..."
vercel --yes

echo ""
echo "✅ Initial deployment complete!"
echo ""
echo "⚙️  Now you need to set environment variables:"
echo ""
echo "1️⃣  Set RAILWAY_BASE:"
echo "   vercel env add RAILWAY_BASE"
echo "   → Enter: https://jibber-jabber-production.up.railway.app"
echo ""
echo "2️⃣  Set CODEX_TOKEN:"
echo "   vercel env add CODEX_TOKEN"
echo "   → Enter: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
echo ""
echo "3️⃣  Redeploy with environment variables:"
echo "   vercel --prod"
echo ""
echo "📋 Or run the automated setup:"
echo "   ./setup-env.sh"
echo ""
