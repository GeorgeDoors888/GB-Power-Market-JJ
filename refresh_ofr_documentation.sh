#!/usr/bin/env bash
# refresh_ofr_documentation.sh
#
# Regenerates OFR pricing statistics from DISBSAD and updates documentation.
# Run this monthly or after significant market events.
#
# Usage: ./refresh_ofr_documentation.sh [--days N]

set -euo pipefail

# Default to 30-day window
DAYS=${1:-30}
if [[ "$1" == "--days" ]]; then
    DAYS=${2:-30}
fi

PROJECT="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
TABLE="bmrs_disbsad"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     OFR PRICING DOCUMENTATION REFRESH                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "Analysis Window: Last $DAYS days"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Step 1: Run the analysis
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1: Running OFR pricing analysis..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 ofr_pricing_analysis.py \
    --project "$PROJECT" \
    --dataset "$DATASET" \
    --table "$TABLE" \
    --days "$DAYS" \
    --compare-non-ofr | tee /tmp/ofr_analysis_output.txt

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2: Extract key statistics"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Parse output for key metrics
AVG_PRICE=$(grep "Volume-weighted avg:" /tmp/ofr_analysis_output.txt | awk '{print $3}')
MIN_PRICE=$(grep "Min:" /tmp/ofr_analysis_output.txt | head -1 | awk '{print $2}')
MAX_PRICE=$(grep "Max:" /tmp/ofr_analysis_output.txt | head -1 | awk '{print $2}')
Q1_PRICE=$(grep "Q1:" /tmp/ofr_analysis_output.txt | awk '{print $2}')
MEDIAN_PRICE=$(grep "Median:" /tmp/ofr_analysis_output.txt | awk '{print $2}')
Q3_PRICE=$(grep "Q3:" /tmp/ofr_analysis_output.txt | awk '{print $2}')
ACTIONS=$(grep "Actions:" /tmp/ofr_analysis_output.txt | awk '{gsub(",",""); print $2}')
TOTAL_COST=$(grep "Total cost:" /tmp/ofr_analysis_output.txt | awk '{gsub(",",""); gsub("£",""); print $3}')
TOTAL_VOLUME=$(grep "Total volume:" /tmp/ofr_analysis_output.txt | awk '{gsub(",",""); print $3}')

START_DATE=$(date -d "$DAYS days ago" '+%B %d, %Y' 2>/dev/null || date -v-${DAYS}d '+%B %d, %Y')
END_DATE=$(date '+%B %d, %Y')

echo "✓ Extracted statistics:"
echo "  - Period: $START_DATE → $END_DATE"
echo "  - Volume-weighted avg: £$AVG_PRICE/MWh"
echo "  - Range: £$MIN_PRICE - £$MAX_PRICE/MWh"
echo "  - Actions: $ACTIONS"
echo "  - Total cost: £$TOTAL_COST"
echo "  - Total volume: $TOTAL_VOLUME MWh"
echo ""

# Step 3: Manual update reminder
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3: Documentation update required"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⚠️  MANUAL ACTION REQUIRED:"
echo ""
echo "Update the following files with the statistics above:"
echo ""
echo "1. docs/DISBSAD_OFR_PRICING_ANALYSIS.md"
echo "   - Update date header to: $(date '+%B %d, %Y')"
echo "   - Update analysis period to: $START_DATE - $END_DATE"
echo "   - Replace pricing characteristics section with:"
echo "     Volume-Weighted Avg: £$AVG_PRICE/MWh"
echo "     Range: £$MIN_PRICE - £$MAX_PRICE/MWh"
echo "     Q1=$Q1_PRICE, Median=$MEDIAN_PRICE, Q3=$Q3_PRICE"
echo "     Actions: $ACTIONS"
echo "     Total: £$TOTAL_COST for $TOTAL_VOLUME MWh"
echo ""
echo "2. docs/WHY_CONSTRAINT_COSTS_ARE_NA.md"
echo "   - Update OFR pricing example section"
echo ""
echo "3. docs/OFR_PRICING_METHODOLOGY.md"
echo "   - Update 'Current Statistics' section"
echo "   - Update 'Last Updated' date"
echo ""
echo "Full output saved to: /tmp/ofr_analysis_output.txt"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ANALYSIS COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Review /tmp/ofr_analysis_output.txt"
echo "  2. Update documentation files listed above"
echo "  3. Commit changes: git add docs/*.md && git commit -m 'Update OFR pricing ($END_DATE)'"
echo ""
