#!/bin/bash
# FUELINST Historical Data Reload (No Overwrite)
# Loads 2023-2025 data without trying to clear existing data

cd '/Users/georgemajor/GB Power Market JJ'

echo "================================================================================"
echo "FUELINST HISTORICAL DATA RELOAD - 2023-2025"
echo "================================================================================"
echo ""

# Reload 2023
echo "Loading 2023 FUELINST data..."
echo "Start: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --only FUELINST \
  2>&1 | tail -20
echo "End: $(date)"
echo ""

# Reload 2024
echo "Loading 2024 FUELINST data..."
echo "Start: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --only FUELINST \
  2>&1 | tail -20
echo "End: $(date)"
echo ""

# Reload 2025  
echo "Loading 2025 FUELINST data (Jan-Oct)..."
echo "Start: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2025-01-01 \
  --end 2025-10-29 \
  --only FUELINST \
  2>&1 | tail -20
echo "End: $(date)"
echo ""

echo "✅ Load complete!"
