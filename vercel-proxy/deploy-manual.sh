#!/bin/bash
# Manual Vercel Deployment - Step by Step

set -e

echo "🚀 Vercel Deployment Guide"
echo "=========================="
echo ""
echo "✅ Vercel CLI is installed and you're logged in!"
echo ""
echo "📋 Follow these steps:"
echo ""

echo "Step 1: Deploy the project"
echo "-------------------------"
echo "Run: vercel"
echo ""
echo "When prompted, answer:"
echo "  • Set up and deploy? → Y"
echo "  • Which scope? → (Choose your account)"
echo "  • Link to existing project? → N"
echo "  • What's your project's name? → railway-codex-proxy"
echo "  • In which directory is your code located? → ./"
echo "  • Want to modify settings? → N"
echo ""
echo "Press ENTER when ready to run 'vercel'..."
read

vercel

echo ""
echo "✅ Initial deployment complete!"
echo ""
echo "Step 2: Set environment variables"
echo "---------------------------------"
echo ""
echo "Run these commands one at a time:"
echo ""
echo "1. Set RAILWAY_BASE:"
echo "   vercel env add RAILWAY_BASE production"
echo "   When prompted, enter: https://jibber-jabber-production.up.railway.app"
echo ""
echo "2. Set CODEX_TOKEN:"
echo "   vercel env add CODEX_TOKEN production"
echo "   When prompted, enter: codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"
echo ""
echo "Press ENTER when ready to set RAILWAY_BASE..."
read

echo "https://jibber-jabber-production.up.railway.app" | vercel env add RAILWAY_BASE production

echo ""
echo "Press ENTER when ready to set CODEX_TOKEN..."
read

echo "codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA" | vercel env add CODEX_TOKEN production

echo ""
echo "✅ Environment variables set!"
echo ""
echo "Step 3: Redeploy with environment variables"
echo "-------------------------------------------"
echo "Press ENTER to run final deployment..."
read

vercel --prod

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo ""
echo "Get your URL:"
vercel inspect --prod | grep "URL:" | awk '{print $2}'
echo ""
