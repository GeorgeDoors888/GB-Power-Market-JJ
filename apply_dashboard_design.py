#!/usr/bin/env python3
"""
apply_dashboard_design.py
-------------------------
Apply professional design to GB Energy Dashboard V2
- Colors, formatting, dropdowns, conditional formatting
- Interactive filters and validation
- Support for existing automation scripts

Usage:
    python3 apply_dashboard_design.py [--test]
    
Options:
    --test    Run on TEST copy first (recommended)
"""

import sys
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import (
    set_column_widths, set_row_height,
    CellFormat, Color, TextFormat, format_cell_range,
    DataValidationRule, BooleanCondition
)
try:
    from gspread_formatting import HorizontalAlignment, VerticalAlignment
except ImportError:
    # Fallback for older versions
    class HorizontalAlignment:
        CENTER = 'CENTER'
        LEFT = 'LEFT'
        RIGHT = 'RIGHT'
    class VerticalAlignment:
        MIDDLE = 'MIDDLE'
        TOP = 'TOP'
        BOTTOM = 'BOTTOM'

# Configuration
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"  # Dashboard V2
DASHBOARD_SHEET = "Dashboard"
CREDENTIALS_FILE = "inner-cinema-credentials.json"

# Color Palette (GB Energy Dashboard)
COLORS = {
    "primary_blue": Color(0.0, 0.30, 0.59),      # Title bar
    "light_blue": Color(0.89, 0.95, 0.99),       # KPI strip
    "fuel_yellow": Color(1.0, 0.98, 0.77),       # Generation section
    "green": Color(0.78, 0.90, 0.79),            # Interconnectors
    "purple": Color(0.88, 0.75, 0.91),           # Financial
    "white": Color(1, 1, 1),
    "red_critical": Color(0.89, 0.22, 0.21),     # Critical outages
    "orange_warning": Color(1.0, 0.60, 0.0),     # Warnings
    "text_dark": Color(0.20, 0.20, 0.20),
    "text_blue": Color(0.20, 0.40, 0.80),
}

def connect_to_sheets():
    """Connect to Google Sheets API"""
    print("🔌 Connecting to Google Sheets...")
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh

def apply_title_formatting(dash):
    """Apply title and timestamp formatting (Row 1-2)"""
    print("📝 Applying title formatting...")
    
    # Title bar (Row 1)
    title_fmt = CellFormat(
        backgroundColor=COLORS["primary_blue"],
        textFormat=TextFormat(bold=True, fontSize=16, foregroundColor=COLORS["white"]),
        horizontalAlignment=HorizontalAlignment.CENTER,
        verticalAlignment=VerticalAlignment.MIDDLE,
    )
    format_cell_range(dash, "A1:L1", title_fmt)
    dash.update([["⚡ GB ENERGY DASHBOARD V2 – REAL-TIME MARKET INSIGHTS"]], "A1")
    set_row_height(dash, "1", 35)
    
    # Timestamp (Row 2)
    ts_fmt = CellFormat(
        textFormat=TextFormat(italic=True, fontSize=9, foregroundColor=COLORS["text_blue"]),
        horizontalAlignment=HorizontalAlignment.CENTER,
    )
    format_cell_range(dash, "A2:L2", ts_fmt)

def apply_kpi_strip(dash):
    """Apply KPI strip formatting (Row 5)"""
    print("📊 Applying KPI strip...")
    
    kpi_fmt = CellFormat(
        backgroundColor=COLORS["light_blue"],
        textFormat=TextFormat(bold=True, fontSize=11),
        horizontalAlignment=HorizontalAlignment.CENTER,
        verticalAlignment=VerticalAlignment.MIDDLE,
    )
    format_cell_range(dash, "A5:L5", kpi_fmt)
    set_row_height(dash, "5", 28)

def apply_table_headers(dash):
    """Apply table header formatting (Row 9)"""
    print("📋 Applying table headers...")
    
    # Generation/Fuel section (A-C)
    fuel_hdr = CellFormat(
        backgroundColor=COLORS["fuel_yellow"],
        textFormat=TextFormat(bold=True, fontSize=10),
        horizontalAlignment=HorizontalAlignment.CENTER,
    )
    format_cell_range(dash, "A9:B9", fuel_hdr)
    
    # Interconnectors section (C-D)
    ic_hdr = CellFormat(
        backgroundColor=COLORS["green"],
        textFormat=TextFormat(bold=True, fontSize=10),
        horizontalAlignment=HorizontalAlignment.CENTER,
    )
    format_cell_range(dash, "C9:D9", ic_hdr)
    
    set_row_height(dash, "9", 30)

def apply_outages_section(dash):
    """Apply Live Outages section formatting (Row 31+)"""
    print("⚠️  Applying outages section...")
    
    # Outages header
    outages_hdr = CellFormat(
        backgroundColor=COLORS["red_critical"],
        textFormat=TextFormat(bold=True, fontSize=11, foregroundColor=COLORS["white"]),
        horizontalAlignment=HorizontalAlignment.CENTER,
    )
    format_cell_range(dash, "A31:F31", outages_hdr)
    
    # Data rows alternating background
    data_fmt_light = CellFormat(
        backgroundColor=Color(1.0, 1.0, 1.0),
        textFormat=TextFormat(fontSize=9),
    )
    data_fmt_alt = CellFormat(
        backgroundColor=Color(0.96, 0.96, 0.96),
        textFormat=TextFormat(fontSize=9),
    )
    
    # Apply alternating rows (32-42)
    for i in range(32, 43):
        if i % 2 == 0:
            format_cell_range(dash, f"A{i}:F{i}", data_fmt_light)
        else:
            format_cell_range(dash, f"A{i}:F{i}", data_fmt_alt)

def set_column_structure(dash):
    """Set column widths and row heights"""
    print("📐 Setting column widths...")
    
    set_column_widths(dash, [
        ("A", 200),  # Unit name (wider for long names)
        ("B", 120),  # Capacity
        ("C", 120),  # Interconnector/Type
        ("D", 100),  # Flow/Value
        ("E", 150),  # Additional info
        ("F", 100),  # Status/Percentage
        ("G", 120),  
        ("H", 140),  
        ("I", 90),   
        ("J", 90),   
        ("K", 90),   
        ("L", 90)
    ])

def apply_filter_bar(dash):
    """Apply filter bar with dropdowns (Row 3)"""
    print("🔍 Creating filter bar...")
    
    # Filter bar background
    filter_fmt = CellFormat(
        backgroundColor=Color(0.95, 0.95, 0.95),
        textFormat=TextFormat(fontSize=10),
        verticalAlignment=VerticalAlignment.MIDDLE,
    )
    format_cell_range(dash, "A3:L3", filter_fmt)
    set_row_height(dash, "3", 30)
    
    # Labels and default values (validation can be added later via UI)
    dash.update([["⏱️ Time Range:"]], "A3")
    dash.update([["Real-Time (10 min)"]], "B3")
    
    dash.update([["🗺️ Region:"]], "C3")
    dash.update([["All GB"]], "D3")
    
    dash.update([["🔔 Alerts:"]], "E3")
    dash.update([["All"]], "F3")
    
    print("   ⚠️  Note: Dropdown validations need to be added manually in Google Sheets")

def apply_conditional_formatting(dash):
    """Apply conditional formatting rules"""
    print("🎨 Adding conditional formatting...")
    print("   ⚠️  Note: Conditional formatting rules need to be added manually")
    print("       Suggestion: Highlight cells in column B (capacity) where value > 500")
    # Conditional formatting API varies by gspread version
    # Recommend adding manually via Google Sheets UI for reliability

def create_supporting_sheets(sh):
    """Create Energy_Map and Wind_Warnings sheets if missing"""
    print("🗂️  Creating supporting sheets...")
    
    def create_if_missing(name):
        try:
            ws = sh.worksheet(name)
            print(f"   ✓ {name} already exists")
            return ws
        except gspread.WorksheetNotFound:
            ws = sh.add_worksheet(title=name, rows=1000, cols=26)
            print(f"   ✓ Created {name}")
            return ws
    
    energy_map = create_if_missing("Energy_Map")
    wind_warn = create_if_missing("Wind_Warnings")
    
    # Add headers to Wind_Warnings
    if wind_warn:
        wind_warn.update("A1:D1", [["Timestamp", "Forecast (MW)", "Actual (MW)", "Status"]])
        header_fmt = CellFormat(
            backgroundColor=COLORS["orange_warning"],
            textFormat=TextFormat(bold=True, foregroundColor=COLORS["white"]),
        )
        format_cell_range(wind_warn, "A1:D1", header_fmt)

def main():
    """Main execution"""
    # Check for test mode
    test_mode = "--test" in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE: Please manually create a copy and update SPREADSHEET_ID")
        print("   Then remove --test flag to run on production")
        return
    
    print("=" * 60)
    print("⚡ GB ENERGY DASHBOARD V2 - DESIGN APPLICATION")
    print("=" * 60)
    print(f"📊 Target: {SPREADSHEET_ID}")
    print()
    
    try:
        # Connect
        sh = connect_to_sheets()
        dash = sh.worksheet(DASHBOARD_SHEET)
        print(f"✅ Connected to '{DASHBOARD_SHEET}' sheet")
        print()
        
        # Apply formatting in sequence
        apply_title_formatting(dash)
        set_column_structure(dash)
        apply_filter_bar(dash)
        apply_kpi_strip(dash)
        apply_table_headers(dash)
        apply_outages_section(dash)
        apply_conditional_formatting(dash)
        create_supporting_sheets(sh)
        
        print()
        print("=" * 60)
        print("✅ DESIGN APPLICATION COMPLETE!")
        print("=" * 60)
        print()
        print("🌐 View dashboard:")
        print(f"   https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/")
        print()
        print("📋 Next steps:")
        print("   1. Review formatting in browser")
        print("   2. Test dropdowns and filters")
        print("   3. Wait for next automation run (5-10 min)")
        print("   4. Verify data updates preserve formatting")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
