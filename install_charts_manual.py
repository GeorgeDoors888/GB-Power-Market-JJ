#!/usr/bin/env python3
"""
Simple Dashboard Charts Installation
Opens the script editor and provides copy-paste instructions
"""

import webbrowser
from pathlib import Path

SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SCRIPT_FILE = "dashboard_charts.gs"

print("=" * 70)
print("  📊 DASHBOARD CHARTS - QUICK INSTALLATION (2 MINUTES)")
print("=" * 70)

# Check if script file exists
if not Path(SCRIPT_FILE).exists():
    print(f"\n❌ Error: {SCRIPT_FILE} not found")
    exit(1)

# Read the script content
with open(SCRIPT_FILE, 'r') as f:
    code = f.read()

print(f"\n✅ Loaded {len(code)} characters from {SCRIPT_FILE}")
print(f"\n📋 STEP-BY-STEP INSTRUCTIONS:")
print(f"\n1️⃣  Opening Google Sheet in browser...")

# Open the sheet
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
try:
    webbrowser.open(sheet_url)
    print(f"   ✅ Browser opened: {sheet_url}")
except:
    print(f"   ⚠️  Could not open browser automatically")
    print(f"   📎 Open manually: {sheet_url}")

print(f"\n2️⃣  In Google Sheets:")
print("   • Click: Extensions → Apps Script")
print("   • This opens the Apps Script editor")

print(f"\n3️⃣  In Apps Script editor:")
print("   • If you see existing code, ADD a new file:")
print("     Click: + (plus icon) → Script")
print("     Name it: DashboardCharts")
print("   • Or replace Code.gs content")

print(f"\n4️⃣  Copy the chart code:")
print("   • File location: {SCRIPT_FILE}")
print("   • Lines: {lines} lines".format(lines=code.count('\\n') + 1))

# Copy to clipboard if possible
try:
    import pyperclip
    pyperclip.copy(code)
    print("   ✅ CODE COPIED TO CLIPBOARD!")
    print("   • Just paste (Cmd+V / Ctrl+V) in Apps Script editor")
except ImportError:
    print("   ⚠️  Manual copy required:")
    print(f"   • Open: {SCRIPT_FILE}")
    print("   • Select all (Cmd+A / Ctrl+A)")
    print("   • Copy (Cmd+C / Ctrl+C)")
    print("   • Paste in Apps Script editor")

print(f"\n5️⃣  Save and run:")
print("   • Click: 💾 Save (or Cmd+S / Ctrl+S)")
print("   • Select function: createDashboardCharts")
print("   • Click: ▶️ Run")
print("   • Grant permissions when prompted")
print("   • Click: Allow")

print(f"\n6️⃣  Verify charts:")
print("   • Return to Google Sheets")
print("   • You should see 4 charts:")
print("     1. ⚡ 24-Hour Generation Trend (Column H)")
print("     2. 🥧 Generation Mix Pie Chart (Column Q)")
print("     3. 📊 Stacked Area Chart (Column H, Row 26)")
print("     4. 📊 Top Sources Column Chart (Column Q, Row 26)")

print(f"\n💡 ALTERNATIVE - Use Menu:")
print("   • After saving code, reload sheet")
print("   • Menu: 📊 Dashboard → 🔄 Create/Update Charts")

print(f"\n📚 TROUBLESHOOTING:")
print("   • If 'Data not found' error:")
print("     Run: python3 enhance_dashboard_layout.py")
print("   • If charts don't appear:")
print("     Check Dashboard sheet has data")
print("   • If permission error:")
print("     Click 'Advanced' → 'Go to Dashboard Charts (unsafe)' → Allow")

print(f"\n" + "=" * 70)
print("  ✅ READY TO INSTALL - Follow steps above!")
print("=" * 70)
print(f"\n🔗 Quick links:")
print(f"   • Spreadsheet: {sheet_url}")
print(f"   • Script file: {Path(SCRIPT_FILE).absolute()}")
print(f"\n⏱️  Time estimate: 2 minutes")
