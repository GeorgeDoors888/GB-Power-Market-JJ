#!/bin/bash
# Automatically download all years (2025, 2024, 2023, 2022) sequentially
# This script runs without requiring user approval between years

set -e  # Exit on any error

# Set up environment
export GOOGLE_APPLICATION_CREDENTIALS="/Users/georgemajor/GB Power Market JJ/jibber_jabber_key.json"
PYTHON_BIN="/Users/georgemajor/GB Power Market JJ/.venv/bin/python"
SCRIPT_DIR="/Users/georgemajor/GB Power Market JJ"

echo "=========================================="
echo "🚀 AUTOMATIC MULTI-YEAR DOWNLOAD"
echo "=========================================="
echo "Years: 2025, 2024, 2023, 2022"
echo "Will run sequentially without approval"
echo "=========================================="
echo ""

# Download 2025
echo "📅 Starting 2025 download..."
echo "=========================================="
"$PYTHON_BIN" "$SCRIPT_DIR/download_multi_year_streaming.py" 2025
echo ""
echo "✅ 2025 COMPLETE"
echo ""

# Download 2024
echo "📅 Starting 2024 download..."
echo "=========================================="
"$PYTHON_BIN" "$SCRIPT_DIR/download_multi_year_streaming.py" 2024
echo ""
echo "✅ 2024 COMPLETE"
echo ""

# Download 2023
echo "📅 Starting 2023 download..."
echo "=========================================="
"$PYTHON_BIN" "$SCRIPT_DIR/download_multi_year_streaming.py" 2023
echo ""
echo "✅ 2023 COMPLETE"
echo ""

# Download 2022
echo "📅 Starting 2022 download..."
echo "=========================================="
"$PYTHON_BIN" "$SCRIPT_DIR/download_multi_year_streaming.py" 2022
echo ""
echo "✅ 2022 COMPLETE"
echo ""

echo "=========================================="
echo "🎉 ALL YEARS DOWNLOADED!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✅ 2025: Complete"
echo "  ✅ 2024: Complete"
echo "  ✅ 2023: Complete"
echo "  ✅ 2022: Complete"
echo ""
echo "Total: 4 years × 44 datasets = 176 downloads"
echo ""
echo "Check results files:"
echo "  multi_year_streaming_results_*.json"
echo ""
