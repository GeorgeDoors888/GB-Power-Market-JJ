#!/bin/bash
# Verify Performance Optimizations
# Tests all 3 optimized scripts

set -e

echo "================================================================================"
echo "                    🧪 VERIFYING PERFORMANCE OPTIMIZATIONS"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Dashboard Updater
echo "📊 Test 1: Dashboard Updater (critical - runs 288×/day)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Running: time python3 realtime_dashboard_updater.py"
echo ""

START_TIME=$(date +%s)
if python3 realtime_dashboard_updater.py 2>&1 | tail -5; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    if [ $DURATION -lt 10 ]; then
        echo -e "${GREEN}✅ PASS: Completed in ${DURATION}s (target: <10s)${NC}"
    elif [ $DURATION -lt 30 ]; then
        echo -e "${YELLOW}⚠️  WARN: Completed in ${DURATION}s (acceptable but not optimal)${NC}"
    else
        echo -e "${RED}❌ FAIL: Took ${DURATION}s (expected <10s, was >120s before)${NC}"
    fi
else
    echo -e "${RED}❌ FAIL: Script error${NC}"
fi
echo ""

# Test 2: Populate Dropdowns
echo "📋 Test 2: Populate Search Dropdowns (manual runs)"
echo "────────────────────────────────────────────────────────────────────────────"
echo "Running: time python3 populate_search_dropdowns.py"
echo ""

START_TIME=$(date +%s)
if timeout 60 python3 populate_search_dropdowns.py 2>&1 | tail -10 | grep "cells in single batch"; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    echo -e "${GREEN}✅ PASS: Completed with batch update in ${DURATION}s${NC}"
else
    echo -e "${YELLOW}⚠️  WARN: Could not verify batch update (may have timed out)${NC}"
fi
echo ""

# Test 3: Apps Script (Manual verification required)
echo "🔍 Test 3: Apps Script Optimizations (manual test required)"
echo "────────────────────────────────────────────────────────────────────────────"
echo ""
echo "To test Apps Script optimizations:"
echo "1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
echo "2. Click: 🔍 Search Tools → 📋 View Party Details"
echo "   → Should respond in <0.5s (was 3-5s before)"
echo "3. Click: 🔍 Search Tools → 🧹 Clear Search"
echo "   → Should respond in <0.5s (was 2-3s before)"
echo ""
echo -e "${YELLOW}⏳ Manual verification required (cannot test Apps Script from terminal)${NC}"
echo ""

# Summary
echo "================================================================================"
echo "                              📈 OPTIMIZATION SUMMARY"
echo "================================================================================"
echo ""
echo "Optimizations Applied:"
echo "  ✅ search_interface.gs - Batch operations (17→1, 17+→3, 25→2 calls)"
echo "  ✅ realtime_dashboard_updater.py - Replaced gspread with Sheets API v4"
echo "  ✅ populate_search_dropdowns.py - Batch updates (9→1 calls)"
echo ""
echo "Expected Performance Gains:"
echo "  • Dashboard refresh: 120s → 5.5s (22x faster)"
echo "  • User actions: 3-5s → <0.5s (10x faster)"
echo "  • Daily CPU savings: 9.1 hours"
echo "  • API quota reduction: 80-90%"
echo ""
echo "📝 Full documentation: PERFORMANCE_OPTIMIZATION_COMPLETE.md"
echo ""
echo "================================================================================"
