#!/bin/bash

# CVA Data Pipeline - Resume/Complete Script
# This script resumes the scraping process and completes the full pipeline

echo "🔋 CVA Data Pipeline - Resume & Complete"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "scrape_plants_optimized.py" ]; then
    echo "❌ Error: Not in the correct directory"
    echo "   Please cd to: /Users/georgemajor/GB Power Market JJ"
    exit 1
fi

# Check if checkpoint exists
if [ -f "cva_plants_data.json" ]; then
    SCRAPED=$(python -c "import json; print(len(json.load(open('cva_plants_data.json'))))" 2>/dev/null || echo "0")
    echo "📊 Current Status: $SCRAPED / 2705 plants scraped"
    echo ""
fi

# Step 1: Resume/Complete Scraping
echo "Step 1: Web Scraping"
echo "-------------------"
if [ -f "cva_plants_data.json" ]; then
    SCRAPED=$(python -c "import json; print(len(json.load(open('cva_plants_data.json'))))" 2>/dev/null || echo "0")
    if [ "$SCRAPED" -ge "2700" ]; then
        echo "✅ Scraping already complete ($SCRAPED plants)"
    else
        echo "🔄 Resuming from plant $SCRAPED..."
        echo "   ETA: ~$((2705 - SCRAPED)) plants × 0.5s = ~$(((2705 - SCRAPED) / 2)) seconds"
        echo ""
        read -p "   Press Enter to start scraping (or Ctrl+C to skip)..."
        python scrape_plants_optimized.py
    fi
else
    echo "🚀 Starting fresh scrape of 2,705 plants..."
    echo "   ETA: ~35 minutes"
    echo ""
    read -p "   Press Enter to start scraping (or Ctrl+C to skip)..."
    python scrape_plants_optimized.py
fi

echo ""
echo "✅ Scraping complete!"
echo ""

# Step 2: Generate Map JSON
echo "Step 2: Generate Map JSON"
echo "------------------------"
echo "🔄 Converting scraped data to map format..."
python generate_cva_map_json.py
echo "✅ Map JSON generated: cva_plants_map.json"
echo ""

# Step 3: Upload to BigQuery
echo "Step 3: Upload to BigQuery"
echo "-------------------------"
read -p "Upload to BigQuery? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 Uploading to uk_energy_prod.cva_plants..."
    python load_cva_to_bigquery.py
    echo "✅ BigQuery upload complete!"
else
    echo "⏭️  Skipping BigQuery upload"
fi
echo ""

# Step 4: Generate Statistics
echo "Step 4: Generate Statistics"
echo "--------------------------"
python -c "
import json

# Load map JSON
with open('cva_plants_map.json', 'r') as f:
    plants = json.load(f)

print(f'✅ Total CVA Plants: {len(plants):,}')

# Count by type
from collections import Counter
types = [p.get('type_category', 'Unknown') for p in plants]
type_counts = Counter(types)

print('\n📊 Breakdown by Type:')
for type_name, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
    pct = (count / len(plants)) * 100
    print(f'   {type_name}: {count} ({pct:.1f}%)')

# Calculate capacity
plants_with_capacity = [p for p in plants if p.get('capacity')]
total_capacity = sum(p['capacity'] for p in plants_with_capacity)

print(f'\n⚡ Total Capacity: {total_capacity:,.0f} MW')
print(f'   Average: {total_capacity/len(plants_with_capacity):.1f} MW per plant')

# Coordinates
plants_with_coords = [p for p in plants if 'lat' in p and 'lng' in p]
print(f'\n📍 Coordinate Coverage: {len(plants_with_coords):,} / {len(plants):,} ({len(plants_with_coords)/len(plants)*100:.1f}%)')
"

echo ""
echo "✅ Pipeline Complete!"
echo ""
echo "🌐 Next Steps:"
echo "   1. Open dno_energy_map_advanced.html in a browser"
echo "   2. Click 'CVA (Transmission)' button"
echo "   3. Verify triangle markers appear"
echo "   4. Test with 'SVA (Embedded)' layer for comparison"
echo ""
echo "📝 Documentation:"
echo "   - Full guide: CVA_DATA_COMPLETE.md"
echo "   - Status: CVA_DATA_STATUS.md"
echo ""
