#!/usr/bin/env python3
"""
apply_orange_redesign.py
------------------------
Re-themes GB Energy Dashboard with orange palette (#FF8C00),
adds chart zones, map placeholders, and Outages sheet.

Color Scheme:
- Primary (Orange): #FF8C00 - Title bar, KPI highlights, accent bars
- Secondary (NG Blue): #004C97 - Chart axes, text emphasis
- Positive (Green): #43A047 - Normal/increasing performance
- Warning (Red): #E53935 - Outage/shortfall alerts
- Neutral Gray: #F5F5F5 - Filter band & panels
- Background: #FFF7F0 - Overall sheet background

Usage:
    python3 apply_orange_redesign.py
"""

import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    format_cell_range, CellFormat, Color, TextFormat,
    set_column_widths, set_row_height
)
try:
    from gspread_formatting import HorizontalAlignment, VerticalAlignment
except ImportError:
    class HorizontalAlignment:
        CENTER = 'CENTER'
        LEFT = 'LEFT'
        RIGHT = 'RIGHT'
    class VerticalAlignment:
        MIDDLE = 'MIDDLE'
        TOP = 'TOP'
        BOTTOM = 'BOTTOM'

# Configuration
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD = "Dashboard"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

print("=" * 70)
print("⚡ GB ENERGY DASHBOARD - ORANGE THEME REDESIGN")
print("=" * 70)
print()

# Connect
creds = Credentials.from_service_account_file("inner-cinema-credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
dash = sh.worksheet(DASHBOARD)
print("✅ Connected to Dashboard sheet")

# ---------------------------------------------------------------------------
# 1. Color Palette (Orange Theme)
# ---------------------------------------------------------------------------
COLORS = {
    "orange": Color(1.0, 0.55, 0.0),          # #FF8C00 - Primary
    "blue": Color(0.0, 0.30, 0.59),           # #004C97 - NG Blue
    "green": Color(0.26, 0.63, 0.28),         # #43A047 - Positive
    "red": Color(0.90, 0.22, 0.21),           # #E53935 - Warning
    "gray": Color(0.96, 0.96, 0.96),          # #F5F5F5 - Neutral
    "bg_cream": Color(1.0, 0.97, 0.94),       # #FFF7F0 - Background
    "orange_light": Color(1.0, 0.93, 0.85),   # Light orange tint
    "orange_pale": Color(1.0, 0.82, 0.50),    # #FFD180 - DNO borders
    "fuel_yellow": Color(1.0, 0.97, 0.77),    # Fuel section
    "ic_green": Color(0.78, 0.90, 0.79),      # Interconnector section
    "white": Color(1, 1, 1)
}

# ---------------------------------------------------------------------------
# 2. Title Bar (Orange)
# ---------------------------------------------------------------------------
print("🎨 Applying orange title bar...")
title_fmt = CellFormat(
    backgroundColor=COLORS["orange"],
    textFormat=TextFormat(bold=True, fontSize=16, foregroundColor=COLORS["white"]),
    horizontalAlignment=HorizontalAlignment.CENTER,
)
format_cell_range(dash, "A1:L1", title_fmt)
set_row_height(dash, "1", 30)
dash.update([["⚡ GB ENERGY DASHBOARD – REAL-TIME MARKET INSIGHTS (Orange Theme)"]], "A1")

# Timestamp row
ts_fmt = CellFormat(
    textFormat=TextFormat(italic=True, foregroundColor=COLORS["blue"])
)
format_cell_range(dash, "A2", ts_fmt)

# ---------------------------------------------------------------------------
# 3. Filter Bar (Neutral Gray #F5F5F5)
# ---------------------------------------------------------------------------
print("🔍 Formatting filter bar...")
filter_fmt = CellFormat(
    backgroundColor=COLORS["gray"],
    textFormat=TextFormat(bold=True, fontSize=10),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(dash, "A3:L3", filter_fmt)
set_row_height(dash, "3", 35)

# Filter labels
dash.update([["⏱️ Time Range:"]], "A3")
dash.update([["🗺️ Region:"]], "C3")
dash.update([["🔔 Alerts:"]], "E3")
dash.update([["📅 Start Date:"]], "G3")
dash.update([["📅 End Date:"]], "I3")

# ---------------------------------------------------------------------------
# 4. KPI Strip (Light Orange)
# ---------------------------------------------------------------------------
print("📊 Formatting KPI strip...")
kpi_fmt = CellFormat(
    backgroundColor=COLORS["orange_light"],
    textFormat=TextFormat(bold=True, fontSize=11),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(dash, "A5:L5", kpi_fmt)
set_row_height(dash, "5", 25)

# ---------------------------------------------------------------------------
# 5. Column Widths
# ---------------------------------------------------------------------------
print("📐 Setting column widths...")
set_column_widths(dash, [
    ("A", 140), ("B", 100), ("C", 100),
    ("D", 120), ("E", 150), ("F", 120),
    ("G", 120), ("H", 140), ("I", 100),
    ("J", 100), ("K", 100), ("L", 100)
])

# ---------------------------------------------------------------------------
# 6. Table Headers (Color-coded sections)
# ---------------------------------------------------------------------------
print("📋 Applying table headers...")
set_row_height(dash, "9", 22)

# Fuel Mix section (A9:C9) - Yellow
fuel_hdr = CellFormat(
    backgroundColor=COLORS["fuel_yellow"],
    textFormat=TextFormat(bold=True)
)
format_cell_range(dash, "A9:C9", fuel_hdr)

# Interconnectors section (E9:F9) - Green
ic_hdr = CellFormat(
    backgroundColor=COLORS["ic_green"],
    textFormat=TextFormat(bold=True)
)
format_cell_range(dash, "E9:F9", ic_hdr)

# Financial KPIs section (H9:L9) - Orange tint
fin_hdr = CellFormat(
    backgroundColor=Color(1.0, 0.85, 0.70),  # Light orange
    textFormat=TextFormat(bold=True)
)
format_cell_range(dash, "H9:L9", fin_hdr)

# ---------------------------------------------------------------------------
# 7. Chart Placeholder Zones
# ---------------------------------------------------------------------------
print("📊 Defining chart placeholder zones...")

# Zone 1: Fuel Mix Pie (A20:F40)
dash.update([["📊 CHART ZONE: Fuel Mix Pie (Doughnut)"]], "A20")
chart_zone_fmt = CellFormat(
    backgroundColor=Color(1.0, 0.95, 0.90),
    textFormat=TextFormat(bold=True, italic=True, foregroundColor=COLORS["orange"])
)
format_cell_range(dash, "A20:F20", chart_zone_fmt)

# Zone 2: Interconnector Flows (G20:L40)
dash.update([["📊 CHART ZONE: Interconnector Flows (Multi-line)"]], "G20")
format_cell_range(dash, "G20:L20", chart_zone_fmt)

# Zone 3: Demand vs Generation (A45:F65)
dash.update([["📊 CHART ZONE: Demand vs Generation (Stacked Area)"]], "A45")
format_cell_range(dash, "A45:F45", chart_zone_fmt)

# Zone 4: System Prices (G45:L65)
dash.update([["📊 CHART ZONE: System Prices SSP/SBP/MID (3-Line)"]], "G45")
format_cell_range(dash, "G45:L45", chart_zone_fmt)

# Zone 5: Financial KPIs (A68:L90)
dash.update([["📊 CHART ZONE: Financial KPIs BOD/BID/Imbalance (Column)"]], "A68")
format_cell_range(dash, "A68:L68", chart_zone_fmt)

# ---------------------------------------------------------------------------
# 8. Top 12 Outages Section (A70:L82)
# ---------------------------------------------------------------------------
print("⚠️  Creating Top 12 Outages section...")
dash.update([["⚠️  TOP 12 ACTIVE OUTAGES (by MW Unavailable)"]], "A70")
outage_hdr_fmt = CellFormat(
    backgroundColor=COLORS["red"],
    textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"]),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(dash, "A70:L70", outage_hdr_fmt)

# Outage table headers (Row 71)
outage_headers = [["BM Unit", "Plant", "Fuel", "MW Lost", "Region", "Start", "End", "Status"]]
dash.update(outage_headers, "A71")
outage_col_hdr = CellFormat(
    backgroundColor=Color(1.0, 0.90, 0.90),  # Light red
    textFormat=TextFormat(bold=True)
)
format_cell_range(dash, "A71:H71", outage_col_hdr)

# ---------------------------------------------------------------------------
# 9. Create/Format Outages Sheet (Full History)
# ---------------------------------------------------------------------------
print("📝 Creating/formatting Outages sheet...")
try:
    outages = sh.worksheet("Outages")
    print("   ✓ Outages sheet exists")
except gspread.WorksheetNotFound:
    outages = sh.add_worksheet(title="Outages", rows=1000, cols=10)
    print("   ✓ Created Outages sheet")

# Headers
outage_full_headers = [[
    "BM Unit ID", "Plant Name", "Fuel", "MW Unavailable", "Region",
    "Outage Start", "Outage End", "Reason", "Status", "Last Updated"
]]
outages.update(outage_full_headers, "A1")

# Orange header
outage_sheet_hdr = CellFormat(
    backgroundColor=COLORS["orange"],
    textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"]),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(outages, "A1:J1", outage_sheet_hdr)
set_row_height(outages, "1", 25)

# ---------------------------------------------------------------------------
# 10. Create/Format Energy_Map Sheet
# ---------------------------------------------------------------------------
print("🗺️  Creating/formatting Energy_Map sheet...")
try:
    map_ws = sh.worksheet("Energy_Map")
    print("   ✓ Energy_Map exists")
except gspread.WorksheetNotFound:
    map_ws = sh.add_worksheet(title="Energy_Map", rows=1000, cols=26)
    print("   ✓ Created Energy_Map sheet")

# Map title
map_ws.update([["🗺️  ENERGY MAP – DNO REGIONS, GSP CONNECTIONS & OFFSHORE WIND"]], "A1")
map_title_fmt = CellFormat(
    backgroundColor=COLORS["orange"],
    textFormat=TextFormat(bold=True, fontSize=14, foregroundColor=COLORS["white"]),
    horizontalAlignment=HorizontalAlignment.CENTER
)
format_cell_range(map_ws, "A1:Z1", map_title_fmt)
set_row_height(map_ws, "1", 30)

# Layer description table
map_ws.update([
    ["Layer", "Colour", "Description"],
    ["DNO Boundaries", "#FFD180", "Polygon overlay per DNO region"],
    ["GSP Points", "#004C97", "Grid Supply Points (hover shows ID & MW)"],
    ["Offshore Wind", "#FF8C00", "Wind farms & connecting GSP lines"],
    ["Outages", "#E53935", "Active outage markers on map"]
], "A3")

map_table_hdr = CellFormat(
    backgroundColor=COLORS["gray"],
    textFormat=TextFormat(bold=True)
)
format_cell_range(map_ws, "A3:C3", map_table_hdr)

# ---------------------------------------------------------------------------
# 11. Wind_Warnings Sheet (if exists, add header)
# ---------------------------------------------------------------------------
try:
    wind_ws = sh.worksheet("Wind_Warnings")
    print("✓ Wind_Warnings sheet exists")
    # Add orange header if needed
    wind_ws.update([["⚠️  WIND FORECAST VS ACTUAL WARNINGS"]], "A1")
    format_cell_range(wind_ws, "A1:D1", CellFormat(
        backgroundColor=COLORS["orange"],
        textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"])
    ))
except gspread.WorksheetNotFound:
    print("   ⚠️  Wind_Warnings sheet not found (will be created by automation)")

# ---------------------------------------------------------------------------
print()
print("=" * 70)
print("✅ ORANGE THEME REDESIGN COMPLETE!")
print("=" * 70)
print()
print("🎨 Applied:")
print("   • Orange title bar (#FF8C00)")
print("   • Neutral gray filter bar (#F5F5F5)")
print("   • Light orange KPI strip")
print("   • Color-coded table headers (Fuel/IC/Financial)")
print("   • 5 chart placeholder zones marked")
print("   • Top 12 Outages section (A70:L82)")
print("   • Outages sheet with full history columns")
print("   • Energy_Map sheet with layer descriptions")
print()
print("🌐 View dashboard:")
print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
print()
print("📋 Next steps:")
print("   1. Run add_validation_and_formatting.py for dropdowns/conditional formatting")
print("   2. Verify existing automation scripts still work")
print("   3. Add charts via Apps Script using defined zones")
print("   4. Test Top 12 Outages auto-refresh with live data")
print()
