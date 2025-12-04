#!/bin/bash
# Download all key files for ChatGPT when browser tool is disabled
# Usage: ./download_files_for_chatgpt.sh

DEST_DIR="chatgpt_files"
mkdir -p "$DEST_DIR"

echo "📦 Downloading files for ChatGPT..."
echo ""

# Python files
echo "Downloading Python scripts..."
curl -s -o "$DEST_DIR/bess_revenue_engine.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/bess_revenue_engine.py

curl -s -o "$DEST_DIR/fr_revenue_optimiser.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/fr_revenue_optimiser.py

curl -s -o "$DEST_DIR/update_analysis_bi_enhanced.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/update_analysis_bi_enhanced.py

curl -s -o "$DEST_DIR/realtime_dashboard_updater.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/realtime_dashboard_updater.py

curl -s -o "$DEST_DIR/format_dashboard.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/format_dashboard.py

curl -s -o "$DEST_DIR/enhance_dashboard_layout.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/enhance_dashboard_layout.py

curl -s -o "$DEST_DIR/dno_lookup_python.py" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/dno_lookup_python.py

# Apps Script
echo "Downloading Apps Script files..."
curl -s -o "$DEST_DIR/apps_script_code.gs" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/apps_script_code.gs

curl -s -o "$DEST_DIR/bess_auto_trigger.gs" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/bess_auto_trigger.gs

curl -s -o "$DEST_DIR/bess_dno_lookup.gs" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/bess_dno_lookup.gs

# Documentation
echo "Downloading documentation..."
curl -s -o "$DEST_DIR/PROJECT_INDEX.md" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/PROJECT_INDEX.md

curl -s -o "$DEST_DIR/BESS_ENGINE_DEPLOYMENT.md" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/BESS_ENGINE_DEPLOYMENT.md

curl -s -o "$DEST_DIR/PROJECT_CONFIGURATION.md" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/PROJECT_CONFIGURATION.md

curl -s -o "$DEST_DIR/STOP_DATA_ARCHITECTURE_REFERENCE.md" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/STOP_DATA_ARCHITECTURE_REFERENCE.md

curl -s -o "$DEST_DIR/copilot-instructions.md" \
  https://raw.githubusercontent.com/GeorgeDoors888/GB-Power-Market-JJ/main/.github/copilot-instructions.md

echo ""
echo "✅ Downloaded $(ls -1 $DEST_DIR | wc -l) files to $DEST_DIR/"
echo ""
echo "📤 Upload these files to ChatGPT:"
echo "   1. Go to ChatGPT"
echo "   2. Click the attachment icon (📎)"
echo "   3. Select all files in $DEST_DIR/"
echo "   4. Upload and tell ChatGPT: 'Analyze these files and provide VLP improvements'"
echo ""
echo "Or create a ZIP:"
echo "   zip -r chatgpt_files.zip $DEST_DIR/"
echo "   Then upload chatgpt_files.zip to ChatGPT"
