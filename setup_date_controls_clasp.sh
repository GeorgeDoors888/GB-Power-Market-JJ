#!/bin/bash
# setup_date_controls_clasp.sh
# Proper Clasp deployment for date range controls to Main Analysis Dashboard

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════"
echo "  Date Range Controls - Clasp Setup"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Target spreadsheet
TARGET_SHEET_ID="1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I"
TARGET_SHEET_URL="https://docs.google.com/spreadsheets/d/${TARGET_SHEET_ID}/edit"

echo "📊 Target: GB Live/BTM Dashboard"
echo "   ID: ${TARGET_SHEET_ID}"
echo "   URL: ${TARGET_SHEET_URL}"
echo ""

# Step 1: Check if clasp is installed
if ! command -v clasp &> /dev/null; then
    echo "❌ Clasp not installed!"
    echo ""
    echo "Install with:"
    echo "  npm install -g @google/clasp"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Clasp installed: $(clasp --version)"
echo ""

# Step 2: Check if logged in
echo "🔐 Checking Clasp authentication..."
if ! clasp list &> /dev/null; then
    echo "❌ Not logged in to Clasp"
    echo ""
    echo "Run: clasp login"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Clasp authenticated"
echo ""

# Step 3: Get Apps Script ID from user
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MANUAL STEP REQUIRED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open this URL in your browser:"
echo "   ${TARGET_SHEET_URL}"
echo ""
echo "2. Click: Extensions → Apps Script"
echo ""
echo "3. Copy the Script ID from the URL:"
echo "   https://script.google.com/d/SCRIPT_ID_HERE/edit"
echo "                                ^^^^^^^^^^^^^^^^"
echo ""
echo "4. Paste it below (press Enter when done):"
echo ""

read -p "Apps Script ID: " SCRIPT_ID

if [ -z "$SCRIPT_ID" ]; then
    echo "❌ No Script ID provided. Exiting."
    exit 1
fi

echo ""
echo "✅ Script ID: $SCRIPT_ID"
echo ""

# Step 4: Create Clasp project directory
PROJECT_DIR="date-range-controls-clasp"

if [ -d "$PROJECT_DIR" ]; then
    echo "⚠️  Directory $PROJECT_DIR already exists"
    read -p "   Delete and recreate? (y/N): " CONFIRM
    if [ "$CONFIRM" = "y" ]; then
        rm -rf "$PROJECT_DIR"
        echo "   ✅ Deleted old directory"
    else
        echo "   ❌ Cancelled"
        exit 1
    fi
fi

mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "✅ Created directory: $PROJECT_DIR"
echo ""

# Step 5: Create .clasp.json
cat > .clasp.json << EOF
{
  "scriptId": "${SCRIPT_ID}",
  "rootDir": "."
}
EOF

echo "✅ Created .clasp.json"
echo ""

# Step 6: Pull existing code (if any)
echo "📥 Pulling existing Apps Script code..."
if clasp pull; then
    echo "✅ Pulled existing code"
else
    echo "⚠️  No existing code (this is OK for new projects)"
fi
echo ""

# Step 7: Copy and fix date controls code
echo "📝 Copying date controls code..."

# Copy the file
cp ../add_date_range_controls.gs Code.gs

# Fix spreadsheet ID in comments/strings
sed -i "s/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/${TARGET_SHEET_ID}/g" Code.gs

echo "✅ Copied and corrected Code.gs"
echo ""

# Step 8: Create appsscript.json if not exists
if [ ! -f "appsscript.json" ]; then
    cat > appsscript.json << EOF
{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
EOF
    echo "✅ Created appsscript.json"
else
    echo "✅ appsscript.json already exists"
fi
echo ""

# Step 9: Push to Apps Script
echo "🚀 Pushing to Apps Script..."
if clasp push; then
    echo "✅ Code deployed successfully!"
else
    echo "❌ Deployment failed"
    exit 1
fi
echo ""

# Step 10: Open in browser
echo "🌐 Opening Apps Script editor..."
clasp open
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FINAL STEPS (In Apps Script Editor)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. In the Apps Script editor that just opened:"
echo "   - Select function: setupDateRangeControls"
echo "   - Click Run (▶️ button)"
echo "   - Authorize permissions (first time only)"
echo ""
echo "2. Return to your Google Sheet:"
echo "   ${TARGET_SHEET_URL}"
echo ""
echo "3. Verify date controls appear:"
echo "   ✓ D65: From Date (with calendar picker)"
echo "   ✓ E66: To Date (with calendar picker)"
echo ""
echo "4. Test the pickers:"
echo "   - Click D65 → Calendar popup should appear"
echo "   - Click E66 → Calendar popup should appear"
echo "   - Menu → 📊 Analysis Controls → Show Selected Range"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Setup complete!"
echo ""
echo "Location: $(pwd)"
echo ""
echo "To update code in future:"
echo "  cd date-range-controls-clasp"
echo "  # Edit Code.gs"
echo "  clasp push"
echo ""
