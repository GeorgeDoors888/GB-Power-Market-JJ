#!/bin/bash
# organize_docs.sh - Reorganize documentation into logical folder structure
# Created: November 10, 2025

set -e

echo "📚 GB Power Market JJ - Documentation Organization Script"
echo "=========================================================="
echo ""

# Create folder structure
echo "📁 Creating folder structure..."

folders=(
    "docs/00-START-HERE"
    "docs/01-DASHBOARD"
    "docs/02-BIGQUERY"
    "docs/03-IRIS-PIPELINE"
    "docs/04-CHATGPT"
    "docs/05-BESS-VLP"
    "docs/06-MAPS"
    "docs/07-ANALYSIS"
    "docs/08-API-DEPLOYMENT"
    "docs/09-ARCHITECTURE"
    "docs/10-ARCHIVE"
)

for folder in "${folders[@]}"; do
    mkdir -p "$folder"
    echo "   ✅ Created: $folder"
done

echo ""
echo "🔄 Moving files to appropriate folders..."
echo ""

# 00-START-HERE (Core references)
echo "📂 00-START-HERE..."
mv -n README.md docs/00-START-HERE/ 2>/dev/null || true
mv -n PROJECT_CONFIGURATION.md docs/00-START-HERE/ 2>/dev/null || true
mv -n COMPLETE_REFERENCE_GUIDE.md docs/00-START-HERE/ 2>/dev/null || true
mv -n QUICK_START_GUIDE.md docs/00-START-HERE/ 2>/dev/null || true
mv -n SETUP_QUICK_REFERENCE.md docs/00-START-HERE/ 2>/dev/null || true
mv -n QUICK_START_ANALYSIS.md docs/00-START-HERE/ 2>/dev/null || true
echo "   ✅ Moved core reference files"

# 01-DASHBOARD
echo "📂 01-DASHBOARD..."
mv -n COMPREHENSIVE_REDESIGN_COMPLETE.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n DASHBOARD_*.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n AUTO_FLAG_VERIFICATION_COMPLETE.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n AUTO_VERIFICATION_SUMMARY.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n FLAG_FIX_TECHNICAL_GUIDE.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n AUTO_REFRESH_COMPLETE.md docs/01-DASHBOARD/ 2>/dev/null || true
mv -n REALTIME_DASHBOARD_UPDATER_GUIDE.md docs/01-DASHBOARD/ 2>/dev/null || true
echo "   ✅ Moved dashboard files"

# 02-BIGQUERY
echo "📂 02-BIGQUERY..."
mv -n BIGQUERY_*.md docs/02-BIGQUERY/ 2>/dev/null || true
mv -n STOP_DATA_ARCHITECTURE_REFERENCE.md docs/02-BIGQUERY/ 2>/dev/null || true
mv -n UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md docs/02-BIGQUERY/ 2>/dev/null || true
mv -n ACTUAL_DATA_INVENTORY.md docs/02-BIGQUERY/ 2>/dev/null || true
mv -n DATA_DICTIONARY.md docs/02-BIGQUERY/ 2>/dev/null || true
echo "   ✅ Moved BigQuery files"

# 03-IRIS-PIPELINE
echo "📂 03-IRIS-PIPELINE..."
mv -n IRIS_*.md docs/03-IRIS-PIPELINE/ 2>/dev/null || true
mv -n ALMALINUX_*.md docs/03-IRIS-PIPELINE/ 2>/dev/null || true
mv -n WINDOWS_DEPLOYMENT*.md docs/03-IRIS-PIPELINE/ 2>/dev/null || true
echo "   ✅ Moved IRIS pipeline files"

# 04-CHATGPT
echo "📂 04-CHATGPT..."
mv -n CHATGPT_*.md docs/04-CHATGPT/ 2>/dev/null || true
mv -n AI_*.md docs/04-CHATGPT/ 2>/dev/null || true
mv -n CHAT_HISTORY_QUICKSTART.md docs/04-CHATGPT/ 2>/dev/null || true
echo "   ✅ Moved ChatGPT/AI files"

# 05-BESS-VLP
echo "📂 05-BESS-VLP..."
mv -n BESS_*.md docs/05-BESS-VLP/ 2>/dev/null || true
mv -n NESO_ELEXON_BATTERY_VLP_DATA_GUIDE.md docs/05-BESS-VLP/ 2>/dev/null || true
echo "   ✅ Moved BESS/VLP files"

# 06-MAPS
echo "📂 06-MAPS..."
mv -n DNO_*.md docs/06-MAPS/ 2>/dev/null || true
mv -n MAP_*.md docs/06-MAPS/ 2>/dev/null || true
echo "   ✅ Moved map files"

# 07-ANALYSIS
echo "📂 07-ANALYSIS..."
mv -n STATISTICAL_*.md docs/07-ANALYSIS/ 2>/dev/null || true
mv -n ANALYSIS_*.md docs/07-ANALYSIS/ 2>/dev/null || true
mv -n ENHANCED_BI_ANALYSIS_README.md docs/07-ANALYSIS/ 2>/dev/null || true
echo "   ✅ Moved analysis files"

# 08-API-DEPLOYMENT
echo "📂 08-API-DEPLOYMENT..."
mv -n API_*.md docs/08-API-DEPLOYMENT/ 2>/dev/null || true
mv -n APPS_SCRIPT_*.md docs/08-API-DEPLOYMENT/ 2>/dev/null || true
mv -n DEPLOYMENT_*.md docs/08-API-DEPLOYMENT/ 2>/dev/null || true
mv -n AWS_SETUP_GUIDE.md docs/08-API-DEPLOYMENT/ 2>/dev/null || true
mv -n RAILWAY_QUICK_REFERENCE.md docs/08-API-DEPLOYMENT/ 2>/dev/null || true
echo "   ✅ Moved API/deployment files"

# 09-ARCHITECTURE
echo "📂 09-ARCHITECTURE..."
mv -n ARCHITECTURE_*.md docs/09-ARCHITECTURE/ 2>/dev/null || true
mv -n AUTOMATION_FRAMEWORK.md docs/09-ARCHITECTURE/ 2>/dev/null || true
mv -n BACKGROUND_MODE_GUIDE.md docs/09-ARCHITECTURE/ 2>/dev/null || true
mv -n BRIDGE_README.md docs/09-ARCHITECTURE/ 2>/dev/null || true
mv -n MONITORING_COMPLETE.md docs/09-ARCHITECTURE/ 2>/dev/null || true
echo "   ✅ Moved architecture files"

# Keep in root
echo ""
echo "📌 Keeping in root directory:"
echo "   • CHANGELOG.md"
echo "   • DOCUMENTATION_MASTER_INDEX.md"
echo "   • REPOSITORY_CLEANUP_GUIDE.md"
echo "   • FINAL_INDEXING_COMPLETE.md"

# Create index in each folder
echo ""
echo "📋 Creating index files in each folder..."

for folder in "${folders[@]}"; do
    if [ "$folder" != "docs/10-ARCHIVE" ]; then
        cat > "$folder/INDEX.md" << EOF
# $(basename $folder) Documentation

Files in this folder:

$(ls -1 "$folder"/*.md 2>/dev/null | xargs -I {} basename {} | grep -v INDEX.md || echo "No files yet")

---

**Back to**: [Master Index](../../DOCUMENTATION_MASTER_INDEX.md)
EOF
        echo "   ✅ Created index: $folder/INDEX.md"
    fi
done

echo ""
echo "=========================================================="
echo "✅ DOCUMENTATION ORGANIZATION COMPLETE!"
echo "=========================================================="
echo ""
echo "📊 Summary:"
echo "   • Created 11 categorized folders"
echo "   • Moved ~300+ .md files"
echo "   • Created folder indexes"
echo ""
echo "📚 Next steps:"
echo "   1. Review: docs/ folder structure"
echo "   2. Check: DOCUMENTATION_MASTER_INDEX.md"
echo "   3. Update: Internal links if needed"
echo ""
echo "🔗 Master Index: DOCUMENTATION_MASTER_INDEX.md"
echo ""
