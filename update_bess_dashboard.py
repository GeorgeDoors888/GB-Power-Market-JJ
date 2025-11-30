#!/usr/bin/env python3
"""
Update BESS Dashboard with Cost Analysis Controls
Adds:
1. Time period dropdown (All Data, Non-COVID, Since SLP, 1 Year, 2 Year)
2. Detailed cost breakdown table with rates, kWh, and total £
3. Enhanced formatting and controls
"""

import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *
from datetime import datetime

# Configuration
DASHBOARD_V2_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
CREDENTIALS_FILE = 'inner-cinema-credentials.json'

# Cost rates (2025/26)
COST_RATES = {
    'SSP': {'rate': 'Variable', 'avg_mwh': 51.52, 'color': '#2E86AB', 'emoji': '🔵', 'name': 'System Sell Price'},
    'DUoS_RED': {'rate_kwh': 0.01764, 'rate_mwh': 17.64, 'color': '#A23B72', 'emoji': '🟣', 'name': 'DUoS (RED Peak)'},
    'DUoS_AMBER': {'rate_kwh': 0.00205, 'rate_mwh': 2.05, 'color': '#A23B72', 'emoji': '🟣', 'name': 'DUoS (AMBER Mid)'},
    'DUoS_GREEN': {'rate_kwh': 0.00011, 'rate_mwh': 0.11, 'color': '#A23B72', 'emoji': '🟣', 'name': 'DUoS (GREEN Off)'},
    'RO': {'rate_kwh': 0.0619, 'rate_mwh': 61.90, 'color': '#F18F01', 'emoji': '🟠', 'name': 'Renewables Obligation'},
    'CCL': {'rate_kwh': 0.00775, 'rate_mwh': 7.75, 'color': '#C73E1D', 'emoji': '🔴', 'name': 'Climate Change Levy'},
    'FiT': {'rate_kwh': 0.0115, 'rate_mwh': 11.50, 'color': '#6A994E', 'emoji': '🟢', 'name': 'Feed-in Tariff'},
    'BSUoS': {'rate_kwh': 0.0045, 'rate_mwh': 4.50, 'color': '#BC4B51', 'emoji': '🔴', 'name': 'Balancing Services'},
    'TNUoS': {'rate_kwh': 0.0125, 'rate_mwh': 12.50, 'color': '#8B7E74', 'emoji': '🟤', 'name': 'Transmission Network'},
}

def connect():
    """Connect to Google Sheets"""
    creds = Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    return gspread.authorize(creds)

def create_time_period_dropdown(bess):
    """Create time period selection dropdown"""
    print("\n📅 Creating time period dropdown...")
    
    # Add dropdown in K6
    time_periods = [
        'All Data',
        'Non-COVID Data',
        'Since SLP Data',
        '1 Year',
        '2 Year'
    ]
    
    # Create validation rule
    validation_rule = DataValidationRule(
        BooleanCondition('ONE_OF_LIST', time_periods),
        showCustomUi=True
    )
    
    set_data_validation_for_cell_range(bess, 'L6', validation_rule)
    
    # Set labels and default value
    bess.update(values=[['Time Period:']], range_name='K6')
    bess.update(values=[['1 Year']], range_name='L6')
    
    # Format labels
    fmt_label = cellFormat(
        backgroundColor=color(0.95, 0.95, 0.95),
        textFormat=textFormat(bold=True, fontSize=10),
        horizontalAlignment='RIGHT'
    )
    format_cell_range(bess, 'K6', fmt_label)
    
    # Format dropdown
    fmt_dropdown = cellFormat(
        backgroundColor=color(1, 1, 1),
        borders=borders(
            top=border('SOLID', color(0, 0, 0)),
            bottom=border('SOLID', color(0, 0, 0)),
            left=border('SOLID', color(0, 0, 0)),
            right=border('SOLID', color(0, 0, 0))
        )
    )
    format_cell_range(bess, 'L6', fmt_dropdown)
    
    print("   ✅ Time period dropdown created in K6:L6")
    print(f"      Options: {', '.join(time_periods)}")

def create_cost_breakdown_table(bess):
    """Create detailed cost breakdown table"""
    print("\n💰 Creating cost breakdown table...")
    
    # Example consumption for calculations (1 MWh = 1,000 kWh)
    example_kwh = 1000  # 1 MWh for easy comparison
    
    # Build table data
    table_data = [
        [""],
        ["ENERGY COST BREAKDOWN - Per MWh Analysis"],
        ["Updated:", datetime.now().strftime('%Y-%m-%d %H:%M')],
        ["Based on 1,000 kWh (1 MWh) consumption"],
        [""],
        ["Component", "Rate", "kWh", "Total £", "% of Fixed", "Notes"],
        [""],
        # SSP - Variable
        [
            f"{COST_RATES['SSP']['emoji']} {COST_RATES['SSP']['name']}",
            "Variable",
            "1,000",
            "£51.52",
            "-",
            "Average market price (varies by SP)"
        ],
        [""],
        # DUoS - Time band sensitive
        [
            f"{COST_RATES['DUoS_RED']['emoji']} {COST_RATES['DUoS_RED']['name']}",
            f"£{COST_RATES['DUoS_RED']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['DUoS_RED']['rate_mwh']:.2f}",
            f"{COST_RATES['DUoS_RED']['rate_mwh']/98.15*100:.1f}%",
            "Peak 16:00-19:30 (highest)"
        ],
        [
            f"{COST_RATES['DUoS_AMBER']['emoji']} {COST_RATES['DUoS_AMBER']['name']}",
            f"£{COST_RATES['DUoS_AMBER']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['DUoS_AMBER']['rate_mwh']:.2f}",
            f"{COST_RATES['DUoS_AMBER']['rate_mwh']/98.15*100:.1f}%",
            "Mid-peak 08:00-16:00, 19:30-22:00"
        ],
        [
            f"{COST_RATES['DUoS_GREEN']['emoji']} {COST_RATES['DUoS_GREEN']['name']}",
            f"£{COST_RATES['DUoS_GREEN']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['DUoS_GREEN']['rate_mwh']:.2f}",
            f"{COST_RATES['DUoS_GREEN']['rate_mwh']/98.15*100:.1f}%",
            "Off-peak 00:00-08:00, 22:00-24:00"
        ],
        [""],
        # Fixed Levies
        [
            f"{COST_RATES['RO']['emoji']} {COST_RATES['RO']['name']}",
            f"£{COST_RATES['RO']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['RO']['rate_mwh']:.2f}",
            f"{COST_RATES['RO']['rate_mwh']/98.15*100:.1f}%",
            "Largest levy (fixed)"
        ],
        [
            f"{COST_RATES['CCL']['emoji']} {COST_RATES['CCL']['name']}",
            f"£{COST_RATES['CCL']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['CCL']['rate_mwh']:.2f}",
            f"{COST_RATES['CCL']['rate_mwh']/98.15*100:.1f}%",
            "Climate levy (fixed)"
        ],
        [
            f"{COST_RATES['FiT']['emoji']} {COST_RATES['FiT']['name']}",
            f"£{COST_RATES['FiT']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['FiT']['rate_mwh']:.2f}",
            f"{COST_RATES['FiT']['rate_mwh']/98.15*100:.1f}%",
            "Renewable incentive (fixed)"
        ],
        [
            f"{COST_RATES['BSUoS']['emoji']} {COST_RATES['BSUoS']['name']}",
            f"£{COST_RATES['BSUoS']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['BSUoS']['rate_mwh']:.2f}",
            f"{COST_RATES['BSUoS']['rate_mwh']/98.15*100:.1f}%",
            "Grid balancing (fixed)"
        ],
        [
            f"{COST_RATES['TNUoS']['emoji']} {COST_RATES['TNUoS']['name']}",
            f"£{COST_RATES['TNUoS']['rate_kwh']:.5f}/kWh",
            "1,000",
            f"£{COST_RATES['TNUoS']['rate_mwh']:.2f}",
            f"{COST_RATES['TNUoS']['rate_mwh']/98.15*100:.1f}%",
            "Transmission charge (fixed)"
        ],
        [""],
        ["SUMMARY"],
        ["Total Fixed Levies (excl. DUoS)", "", "", "£98.15", "100.0%", "Constant cost"],
        ["DUoS Range", "£0.11 - £17.64", "", "", "", "Time-band variable"],
        ["SSP Average", "~£51.52/MWh", "", "", "", "Market variable"],
        [""],
        ["TOTAL COST EXAMPLES"],
        ["GREEN Time (Off-peak)", "", "", "£149.78", "", "SSP + DUoS GREEN + Fixed"],
        ["AMBER Time (Mid-peak)", "", "", "£151.72", "", "SSP + DUoS AMBER + Fixed"],
        ["RED Time (Peak)", "", "", "£167.31", "", "SSP + DUoS RED + Fixed"],
        [""],
        ["KEY INSIGHTS"],
        ["• Fixed levies represent 66% of total costs"],
        ["• DUoS variation (£17.53/MWh) drives time-band differences"],
        ["• Charging in GREEN saves £17.53/MWh vs RED"],
        ["• RO is largest single component at £61.90/MWh (41% of fixed)"],
    ]
    
    # Write to sheet
    bess.update(values=table_data, range_name='A250:F285')
    
    # Format header
    fmt_header = cellFormat(
        backgroundColor=color(0.2, 0.4, 0.6),
        textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1), fontSize=12),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'A251:F251', fmt_header)
    
    # Format subheaders
    fmt_subheader = cellFormat(
        backgroundColor=color(0.9, 0.9, 0.9),
        textFormat=textFormat(bold=True, fontSize=10),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'A255:F255', fmt_subheader)  # Column headers
    format_cell_range(bess, 'A271', fmt_subheader)  # SUMMARY
    format_cell_range(bess, 'A275', fmt_subheader)  # TOTAL COST EXAMPLES
    format_cell_range(bess, 'A280', fmt_subheader)  # KEY INSIGHTS
    
    # Format data rows
    fmt_data = cellFormat(
        backgroundColor=color(1, 1, 1),
        textFormat=textFormat(fontSize=9),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'A257:F270', fmt_data)
    
    # Format currency columns
    fmt_currency = cellFormat(
        numberFormat=numberFormat(type='CURRENCY', pattern='£#,##0.00'),
        horizontalAlignment='RIGHT'
    )
    format_cell_range(bess, 'D257:D270', fmt_currency)
    
    # Format percentage column
    fmt_percent = cellFormat(
        horizontalAlignment='RIGHT'
    )
    format_cell_range(bess, 'E257:E270', fmt_percent)
    
    # Add borders
    fmt_border = cellFormat(
        borders=borders(
            top=border('SOLID', color(0.7, 0.7, 0.7)),
            bottom=border('SOLID', color(0.7, 0.7, 0.7)),
            left=border('SOLID', color(0.7, 0.7, 0.7)),
            right=border('SOLID', color(0.7, 0.7, 0.7))
        )
    )
    format_cell_range(bess, 'A255:F279', fmt_border)
    
    # Highlight summary rows
    fmt_summary = cellFormat(
        backgroundColor=color(1, 1, 0.8),
        textFormat=textFormat(bold=True),
        borders=borders(
            top=border('SOLID_MEDIUM', color(0, 0, 0)),
            bottom=border('SOLID_MEDIUM', color(0, 0, 0))
        )
    )
    format_cell_range(bess, 'A272:F274', fmt_summary)
    format_cell_range(bess, 'A276:F278', fmt_summary)
    
    print("   ✅ Cost breakdown table created in A250:F285")
    print("      Includes: Rates, kWh, Total £, % breakdown, and notes")

def create_period_definitions(bess):
    """Create definitions for time periods"""
    print("\n📖 Creating time period definitions...")
    
    definitions = [
        [""],
        ["TIME PERIOD DEFINITIONS"],
        [""],
        ["Period", "Description", "Start Date", "Data Points"],
        ["All Data", "Complete historical dataset", "Earliest available", "All records"],
        ["Non-COVID Data", "Excludes COVID-19 period", "April 2021 onwards", "Post-lockdown"],
        ["Since SLP Data", "Since System Long Position data", "Jan 2023 onwards", "Modern data"],
        ["1 Year", "Last 12 months", "Dec 2024 onwards", "~17,520 SPs"],
        ["2 Year", "Last 24 months", "Dec 2023 onwards", "~35,040 SPs"],
        [""],
        ["NOTES:"],
        ["• All Data: Maximum historical context but includes anomalies"],
        ["• Non-COVID: Excludes distorted pricing (Mar 2020 - Mar 2021)"],
        ["• Since SLP: Clean modern data with consistent market structure"],
        ["• 1/2 Year: Most relevant for current operations"],
        [""],
        ["RECOMMENDED: '1 Year' for standard analysis"],
        ["USE CASE: 'All Data' for long-term trends, '2 Year' for patterns"],
    ]
    
    bess.update(values=definitions, range_name='K8:N25')
    
    # Format header
    fmt_header = cellFormat(
        backgroundColor=color(0.2, 0.6, 0.4),
        textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1), fontSize=11),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K9:N9', fmt_header)
    
    # Format column headers
    fmt_col_header = cellFormat(
        backgroundColor=color(0.9, 0.9, 0.9),
        textFormat=textFormat(bold=True, fontSize=9),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K11:N11', fmt_col_header)
    
    # Format data
    fmt_data = cellFormat(
        textFormat=textFormat(fontSize=9),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K12:N16', fmt_data)
    
    # Format notes
    fmt_notes = cellFormat(
        backgroundColor=color(1, 1, 0.9),
        textFormat=textFormat(fontSize=8, italic=True),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K18:N24', fmt_notes)
    
    # Add borders
    fmt_border = cellFormat(
        borders=borders(
            top=border('SOLID', color(0.7, 0.7, 0.7)),
            bottom=border('SOLID', color(0.7, 0.7, 0.7)),
            left=border('SOLID', color(0.7, 0.7, 0.7)),
            right=border('SOLID', color(0.7, 0.7, 0.7))
        )
    )
    format_cell_range(bess, 'K11:N16', fmt_border)
    
    print("   ✅ Time period definitions created in K8:N25")

def update_control_panel(bess):
    """Update control panel with new features"""
    print("\n🎛️  Updating control panel...")
    
    # Add section header
    header_data = [
        [""],
        ["⚙️ ANALYSIS CONTROLS"],
    ]
    
    bess.update(values=header_data, range_name='K4:L5')
    
    # Format header
    fmt_header = cellFormat(
        backgroundColor=color(0.1, 0.1, 0.4),
        textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1), fontSize=12),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    )
    format_cell_range(bess, 'K5:L5', fmt_header)
    
    # Note: Cells K5:L5 formatted as merged header
    
    print("   ✅ Control panel updated in K4:L5")

def add_usage_instructions(bess):
    """Add usage instructions"""
    print("\n📋 Adding usage instructions...")
    
    instructions = [
        [""],
        ["HOW TO USE DASHBOARD CONTROLS"],
        [""],
        ["1️⃣  SELECT TIME PERIOD (L6)"],
        ["   Choose analysis period from dropdown"],
        ["   Default: '1 Year' (most relevant)"],
        [""],
        ["2️⃣  RUN ANALYSIS"],
        ["   Execute: python3 calculate_ppa_arbitrage.py"],
        ["   Or: python3 calculate_bess_revenue.py"],
        [""],
        ["3️⃣  VIEW RESULTS"],
        ["   • Rows 90+: PPA arbitrage analysis"],
        ["   • Rows 170+: Revenue breakdown"],
        ["   • Rows 210+: Cost visualization summary"],
        ["   • Rows 250+: Detailed cost breakdown"],
        [""],
        ["4️⃣  GENERATE CHARTS"],
        ["   Execute: python3 visualize_ppa_costs.py"],
        ["   Output: ppa_cost_analysis.png"],
    ]
    
    bess.update(values=instructions, range_name='K27:N46')
    
    # Format
    fmt_instructions = cellFormat(
        backgroundColor=color(0.95, 0.98, 1),
        textFormat=textFormat(fontSize=9),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K27:N46', fmt_instructions)
    
    # Format header
    fmt_inst_header = cellFormat(
        backgroundColor=color(0.3, 0.5, 0.7),
        textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1), fontSize=11),
        horizontalAlignment='LEFT'
    )
    format_cell_range(bess, 'K28:N28', fmt_inst_header)
    
    print("   ✅ Usage instructions added in K27:N46")

def main():
    """Main execution"""
    print("=" * 80)
    print("📊 BESS DASHBOARD UPDATE")
    print("=" * 80)
    print("\n✅ Adding:")
    print("   1. Time period dropdown control")
    print("   2. Detailed cost breakdown table")
    print("   3. Period definitions and usage guide")
    
    try:
        # Connect
        print("\n🔐 Connecting...")
        gs_client = connect()
        ss = gs_client.open_by_key(DASHBOARD_V2_ID)
        bess = ss.worksheet('BESS')
        print("   ✅ Connected")
        
        # Create updates
        update_control_panel(bess)
        create_time_period_dropdown(bess)
        create_period_definitions(bess)
        add_usage_instructions(bess)
        create_cost_breakdown_table(bess)
        
        print("\n" + "=" * 80)
        print("✅ DASHBOARD UPDATE COMPLETE!")
        print("=" * 80)
        
        print("\n📊 New Features:")
        print("   • Time Period Dropdown: K6:L6")
        print("     Options: All Data, Non-COVID, Since SLP, 1 Year, 2 Year")
        print()
        print("   • Cost Breakdown Table: A250:F285")
        print("     Shows: Component, Rate, kWh, Total £, %, Notes")
        print("     Components: SSP, DUoS (3 bands), RO, CCL, FiT, BSUoS, TNUoS")
        print()
        print("   • Period Definitions: K8:N25")
        print("     Details each time period option")
        print()
        print("   • Usage Instructions: K27:N47")
        print("     How to use dashboard controls")
        
        print("\n💡 Next Steps:")
        print("   1. Select time period in L6")
        print("   2. Run analysis scripts:")
        print("      python3 calculate_ppa_arbitrage.py")
        print("      python3 calculate_bess_revenue.py")
        print("      python3 visualize_ppa_costs.py")
        print()
        print("   3. View updated results throughout dashboard")
        
        print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{DASHBOARD_V2_ID}/edit")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
