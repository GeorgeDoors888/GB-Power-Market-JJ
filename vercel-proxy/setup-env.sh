#!/bin/bash
# Automated environment variable setup for Vercel

set -e

echo "⚙️  Setting up Vercel environment variables..."
echo "=============================================="
echo ""

RAILWAY_BASE="https://jibber-jabber-production.up.railway.app"
CODEX_TOKEN="codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

echo "📝 Setting RAILWAY_BASE..."
echo "$RAILWAY_BASE" | vercel env add RAILWAY_BASE production

echo ""
echo "📝 Setting CODEX_TOKEN..."
echo "$CODEX_TOKEN" | vercel env add CODEX_TOKEN production

echo ""
echo "✅ Environment variables set!"
echo ""
echo "🚀 Redeploying to production..."
vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔗 Your proxy is ready. Test it:"
echo ""
echo "   curl \"https://\$(vercel inspect --prod | grep URL | awk '{print \$2}')/api/proxy?path=/health\""
echo ""
