#!/bin/bash
# Simple refresh script - just run this!

cd "$(dirname "$0")"

echo "🔄 Refreshing Analysis BI Enhanced sheet..."
echo ""

python3 update_analysis_bi_enhanced.py

echo ""
echo "✅ Done! Refresh your browser to see updated data."
