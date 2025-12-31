#!/usr/bin/env python3
"""
Fix Dashboard KPI Labels - Trader-Correct Terminology
Updates Live Dashboard v2 with accurate market terminology
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# Corrected KPI labels (trader-correct terminology)
CORRECTED_KPIS = {
    # Current → Corrected
    "💷 System Price (Real-time)": "💷 Single Imbalance Price (Real-time)",
    "📈 Hourly Average": "📈 Hourly Average SIP",
    "📊 7-Day Average": "📊 7-Day Average SIP",
    "📉 30-Day Range (Low)": "📉 30-Day Min SIP",
    "📅 30-Day Average": "📅 30-Day Average SIP",
    "📈 30-Day Range (High)": "📈 30-Day Max SIP",
    "⚙️ BM Dispatch Rate": "⚙️ BM Acceptance Rate (%)",
    "🎯 BM Volume-Weighted Price": "🎯 BM Volume-Weighted Avg Price",
    "Single-Price Frequency": "📊 Single-Price Frequency (%)",
    "💰 Total BM Cashflow": "💰 Total BM Cashflow (£M)",
}

# Additional KPIs to add (if space available)
NEW_KPIS = [
    "🎲 Price Regime",  # Low/Normal/High/Spike classification
    "📈 Tail Risk (95th %ile)",  # 95th percentile price
    "⚡ Peak Price Today",  # Highest settlement period price
]

def connect_to_sheets():
    """Connect to Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
    return gspread.authorize(creds)

def get_current_kpis(sheet):
    """Get current KPI labels from dashboard"""
    print("\n📊 Current KPI Labels:")

    kpi_cells = sheet.range('K13:K22')
    current_kpis = {}

    for i, cell in enumerate(kpi_cells, start=13):
        if cell.value:
            current_kpis[i] = cell.value
            print(f"  Row {i}: {cell.value}")

    return current_kpis

def update_kpi_labels(sheet, current_kpis):
    """Update KPI labels with corrected terminology"""
    print("\n✏️  Updating KPI labels...")

    updates = []
    corrections_made = []

    for row, current_label in current_kpis.items():
        if current_label in CORRECTED_KPIS:
            new_label = CORRECTED_KPIS[current_label]
            updates.append({
                'range': f'K{row}',
                'values': [[new_label]]
            })
            corrections_made.append({
                'row': row,
                'old': current_label,
                'new': new_label
            })
            print(f"  Row {row}: {current_label}")
            print(f"           → {new_label}")

    if updates:
        sheet.batch_update(updates, value_input_option='USER_ENTERED')
        print(f"\n✅ Updated {len(updates)} KPI labels")
    else:
        print("\n✅ No corrections needed - all labels already correct")

    return corrections_made

def add_formatting(sheet, rows):
    """Add consistent formatting to KPI labels"""
    print("\n🎨 Applying formatting...")

    # Bold KPI labels
    for row in rows:
        sheet.format(f'K{row}', {
            'textFormat': {'bold': True, 'fontSize': 10},
            'horizontalAlignment': 'LEFT',
            'verticalAlignment': 'MIDDLE'
        })

    # Format value cells (right-aligned, larger font)
    for row in rows:
        sheet.format(f'L{row}', {
            'textFormat': {'fontSize': 11},
            'horizontalAlignment': 'RIGHT',
            'verticalAlignment': 'MIDDLE',
            'numberFormat': {
                'type': 'NUMBER',
                'pattern': '#,##0.00'
            }
        })

    print("✅ Formatting applied")

def add_explanatory_notes(sheet):
    """Add explanatory notes below KPIs"""
    print("\n📝 Adding explanatory notes...")

    notes = [
        [""],
        ["📖 TERMINOLOGY NOTES:"],
        ["• Single Imbalance Price (SIP) = SSP = SBP since Nov 2015 (BSC Mod P305)"],
        ["• BM Acceptance Rate = % of settlement periods with balancing actions"],
        ["• Price Regime: Low (<£30), Normal (£30-70), High (£70-200), Spike (>£200)"],
        ["• Tail Risk = 95th percentile price (VaR 95%)"],
    ]

    sheet.update('K24:K29', notes, value_input_option='USER_ENTERED')

    # Format notes as smaller, italic text
    sheet.format('K24:K29', {
        'textFormat': {'italic': True, 'fontSize': 8},
        'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}
    })

    print("✅ Notes added")

def create_change_log(corrections):
    """Document changes made"""
    print("\n📋 Change Log:")
    print("="*80)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_content = f"""
KPI LABEL CORRECTIONS - {timestamp}
{'='*80}

Changes Made:
"""

    for change in corrections:
        log_content += f"\nRow {change['row']}:\n"
        log_content += f"  OLD: {change['old']}\n"
        log_content += f"  NEW: {change['new']}\n"

    log_content += f"""
{'='*80}
Terminology Standards Applied:

1. Single Imbalance Price (SIP)
   - Replaces ambiguous "System Price"
   - Clarifies that SSP = SBP since P305 (Nov 2015)

2. BM Acceptance Rate
   - More accurate than "Dispatch Rate"
   - Measures % of periods with balancing actions

3. Explicit Units
   - All percentages marked with (%)
   - All monetary values marked with (£M) or (£)

4. Trader-Focused Language
   - "Volume-Weighted Avg" instead of generic "BM Price"
   - "Peak Price Today" instead of "Range (High)"

Reference:
- BSC Modification P305: https://www.elexon.co.uk/mod-proposal/p305/
- Balancing Mechanism Guide: BMRS documentation
- Energy Trading terminology standards

"""

    # Save to file
    with open('kpi_corrections_log.txt', 'w') as f:
        f.write(log_content)

    print(log_content)
    print(f"✅ Log saved to kpi_corrections_log.txt")

def main():
    print("="*80)
    print("DASHBOARD KPI LABEL CORRECTIONS")
    print("Trader-Correct Terminology Update")
    print("="*80)

    try:
        # Connect
        print(f"\n🔗 Connecting to spreadsheet: {SPREADSHEET_ID}")
        client = connect_to_sheets()
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        sheet = spreadsheet.worksheet(SHEET_NAME)

        # Get current state
        current_kpis = get_current_kpis(sheet)

        # Make corrections
        corrections = update_kpi_labels(sheet, current_kpis)

        # Apply formatting
        if current_kpis:
            add_formatting(sheet, list(current_kpis.keys()))

        # Add notes
        add_explanatory_notes(sheet)

        # Create log
        if corrections:
            create_change_log(corrections)

        # Summary
        print("\n" + "="*80)
        print("✅ KPI LABELS UPDATED SUCCESSFULLY")
        print("="*80)
        print(f"Corrections made: {len(corrections)}")
        print(f"Sheet: {SHEET_NAME}")
        print(f"URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")

        if corrections:
            print("\nKey Changes:")
            for change in corrections[:5]:
                print(f"  • {change['old']}")
                print(f"    → {change['new']}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
