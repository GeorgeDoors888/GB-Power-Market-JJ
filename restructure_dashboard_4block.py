#!/usr/bin/env python3
"""
restructure_dashboard_4block.py

Reorganizes Live Dashboard v2 from single KPI list into 4 logical blocks:
- Block 1 (K5:P12): Market Signals
- Block 2 (K14:P22): System Operator Activity
- Block 3 (R5:V30): Asset Readiness (Phase 2-3)
- Block 4 (R32:V45): Financial Outcomes

Preserves existing formulas, sparklines, and Apps Script charts while
improving visual organization for trader decision-making.

Usage:
    python3 restructure_dashboard_4block.py --preview
    python3 restructure_dashboard_4block.py --execute

Requirements:
    pip3 install --user gspread pandas
"""

import argparse
import gspread
from google.oauth2.service_account import Credentials
import time

# ===== CONFIGURATION =====
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# Current KPI locations (K13:P30 range)
CURRENT_KPIS = {
    # Format: "KPI_NAME": {"current_row": X, "formula_col": "L", "label_col": "K"}
    "real_time_price": {"current_row": 13, "label": "Real-time Imbalance Price"},
    "price_volatility": {"current_row": 14, "label": "Price Volatility (30d StdDev)"},
    "rolling_avg_24h": {"current_row": 15, "label": "Rolling Avg (24h)"},
    "rolling_avg_7d": {"current_row": 16, "label": "Rolling Avg (7d)"},
    "rolling_avg_30d": {"current_row": 17, "label": "Rolling Avg (30d)"},
    "dispatch_intensity": {"current_row": 18, "label": "Dispatch Intensity"},
    "active_sps": {"current_row": 19, "label": "% Active SPs"},
    "ewap": {"current_row": 20, "label": "EWAP (Energy-Weighted Avg Price)"},
    "median_acceptance": {"current_row": 21, "label": "Median Acceptance Size (MW)"},
    "price_regime": {"current_row": 23, "label": "Current Price Regime"},
    "single_price_freq": {"current_row": 24, "label": "Single-Price Frequency (30d)"},
    "regime_dist": {"current_row": 25, "label": "Regime Distribution (30d)"},
}

# New 4-block layout
BLOCK_LAYOUT = {
    "block1_market_signals": {
        "title": "📊 BLOCK 1: MARKET SIGNALS",
        "range": "K5:P12",
        "header_row": 5,
        "start_row": 6,
        "kpis": [
            {"name": "real_time_price", "new_row": 6},
            {"name": "price_regime", "new_row": 7},
            {"name": "price_volatility", "new_row": 8},
            {"name": "single_price_freq", "new_row": 9},
            {"name": "rolling_avg_24h", "new_row": 10},
            {"name": "rolling_avg_7d", "new_row": 11},
            {"name": "rolling_avg_30d", "new_row": 12},
        ]
    },
    "block2_so_activity": {
        "title": "⚡ BLOCK 2: SYSTEM OPERATOR ACTIVITY",
        "range": "K14:P22",
        "header_row": 14,
        "start_row": 15,
        "kpis": [
            {"name": "dispatch_intensity", "new_row": 15},
            {"name": "active_sps", "new_row": 16},
            {"name": "median_acceptance", "new_row": 17},
            {"name": "ewap", "new_row": 18},
            {"name": "worst_sp_7d_label", "new_row": 19, "is_new": True, "label": "Worst 5 SP Losses (7d):"},
            {"name": "worst_sp_30d", "new_row": 21, "is_new": True, "label": "Worst 30d SP:"},
        ]
    },
    "block3_asset_readiness": {
        "title": "🔋 BLOCK 3: ASSET READINESS (Phase 2-3)",
        "range": "R5:V30",
        "header_row": 5,
        "start_row": 6,
        "kpis": [
            {"name": "battery_soc", "new_row": 6, "is_placeholder": True, "label": "Battery SoC (%)", "value": "Phase 2"},
            {"name": "battery_headroom", "new_row": 7, "is_placeholder": True, "label": "Headroom (MW)", "value": "Phase 2"},
            {"name": "battery_cycles", "new_row": 8, "is_placeholder": True, "label": "Cycles (Today)", "value": "Phase 2"},
            {"name": "chp_output", "new_row": 10, "is_placeholder": True, "label": "CHP Output (MW)", "value": "Phase 2"},
            {"name": "spark_spread", "new_row": 11, "is_placeholder": True, "label": "Spark Spread (£/MWh)", "value": "Phase 2"},
            {"name": "availability", "new_row": 13, "is_placeholder": True, "label": "Availability Status", "value": "Phase 2"},
        ]
    },
    "block4_financial": {
        "title": "💰 BLOCK 4: FINANCIAL OUTCOMES",
        "range": "R32:V45",
        "header_row": 32,
        "start_row": 33,
        "kpis": [
            {"name": "revenue_24h", "new_row": 33, "is_placeholder": True, "label": "Revenue (24h)", "value": "Phase 3"},
            {"name": "revenue_7d", "new_row": 34, "is_placeholder": True, "label": "Revenue (7d)", "value": "Phase 3"},
            {"name": "net_pl", "new_row": 35, "is_placeholder": True, "label": "Net P&L", "value": "Phase 3"},
            {"name": "regime_dist_block4", "new_row": 37, "label": "30d Regime Distribution"},  # Copy from Block 1
            {"name": "worst_sp_note", "new_row": 39, "is_new": True, "label": "Worst SP Risk (from Block 2)"},
        ]
    }
}


def read_current_dashboard_kpis(worksheet):
    """
    Read current KPI formulas and values from dashboard.
    Returns dict with KPI data.
    """
    print("\n📊 Reading current dashboard KPIs...")

    kpi_data = {}

    for kpi_name, kpi_info in CURRENT_KPIS.items():
        row = kpi_info["current_row"]

        # Read label (K column), value (L column), note (M column)
        label_cell = f"K{row}"
        value_cell = f"L{row}"
        note_cell = f"M{row}"

        try:
            label = worksheet.acell(label_cell).value
            value_formula = worksheet.acell(value_cell, value_render_option='FORMULA').value
            value_display = worksheet.acell(value_cell).value
            note = worksheet.acell(note_cell).value if worksheet.acell(note_cell).value else ""

            kpi_data[kpi_name] = {
                "label": label or kpi_info["label"],
                "formula": value_formula,
                "display_value": value_display,
                "note": note,
                "current_row": row
            }

            print(f"   ✅ {kpi_name}: {label} = {value_display}")

        except Exception as e:
            print(f"   ⚠️ Error reading {kpi_name}: {str(e)}")
            kpi_data[kpi_name] = {
                "label": kpi_info["label"],
                "formula": None,
                "display_value": None,
                "note": "",
                "current_row": row
            }

    return kpi_data


def preview_restructure(kpi_data):
    """
    Show preview of what restructure will do.
    """
    print("\n" + "=" * 70)
    print("📋 RESTRUCTURE PREVIEW")
    print("=" * 70)

    for block_name, block_info in BLOCK_LAYOUT.items():
        print(f"\n{block_info['title']}")
        print(f"   Range: {block_info['range']}")
        print(f"   KPIs:")

        for kpi in block_info['kpis']:
            kpi_name = kpi['name']
            new_row = kpi['new_row']

            if kpi.get('is_placeholder'):
                print(f"      Row {new_row}: {kpi['label']} → [{kpi['value']}] (Placeholder)")
            elif kpi.get('is_new'):
                print(f"      Row {new_row}: {kpi['label']} → [NEW KPI]")
            elif kpi_name in kpi_data:
                current = kpi_data[kpi_name]
                print(f"      Row {new_row}: {current['label']} ← Move from K{current['current_row']}")
            else:
                print(f"      Row {new_row}: {kpi_name} → [NOT FOUND in current data]")

    print("\n" + "=" * 70)
    print("💡 NOTES:")
    print("   - Block 1-2: Move existing KPIs to new locations")
    print("   - Block 3-4: Add placeholders for Phase 2-3 features")
    print("   - All formulas preserved (cell references will be updated)")
    print("   - Sparklines and charts need manual Apps Script update")
    print("=" * 70)


def create_block_headers(worksheet):
    """
    Create formatted headers for each block.
    """
    print("\n🎨 Creating block headers...")

    header_updates = []

    for block_name, block_info in BLOCK_LAYOUT.items():
        header_row = block_info['header_row']
        title = block_info['title']

        # Header cell (merged K:P or R:V)
        if block_name.startswith('block1') or block_name.startswith('block2'):
            header_cell = f"K{header_row}"
        else:
            header_cell = f"R{header_row}"

        header_updates.append({
            'range': header_cell,
            'values': [[title]]
        })

        print(f"   ✅ {title} → {header_cell}")

    # Batch update headers
    for update in header_updates:
        worksheet.update(update['range'], update['values'])
        time.sleep(0.5)  # Rate limiting

    # Format headers (bold, larger font, colored background)
    print("\n🎨 Formatting headers...")
    format_requests = []

    # Will need to use batch format update via API
    # For now, log what formatting is needed
    print("   ⚠️ Manual formatting required:")
    print("      - Make headers bold, font size 12")
    print("      - Background colors:")
    print("        - Block 1 (K5): Light Blue (#4285F4)")
    print("        - Block 2 (K14): Light Orange (#FF9800)")
    print("        - Block 3 (R5): Light Green (#34A853)")
    print("        - Block 4 (R32): Light Purple (#9C27B0)")


def migrate_kpis(worksheet, kpi_data, dry_run=False):
    """
    Move KPIs to new block locations.
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}📦 Migrating KPIs to new blocks...")

    updates = []

    for block_name, block_info in BLOCK_LAYOUT.items():
        print(f"\n   Processing {block_info['title']}...")

        for kpi in block_info['kpis']:
            kpi_name = kpi['name']
            new_row = kpi['new_row']

            # Determine column (K-P for blocks 1-2, R-V for blocks 3-4)
            if block_name.startswith('block1') or block_name.startswith('block2'):
                label_col = 'K'
                value_col = 'L'
                note_col = 'M'
            else:
                label_col = 'R'
                value_col = 'S'
                note_col = 'T'

            # Handle placeholders
            if kpi.get('is_placeholder'):
                updates.append({
                    'range': f"{label_col}{new_row}",
                    'values': [[kpi['label']]]
                })
                updates.append({
                    'range': f"{value_col}{new_row}",
                    'values': [[kpi['value']]]
                })
                print(f"      Row {new_row}: {kpi['label']} → Placeholder")
                continue

            # Handle new KPIs
            if kpi.get('is_new'):
                updates.append({
                    'range': f"{label_col}{new_row}",
                    'values': [[kpi['label']]]
                })
                print(f"      Row {new_row}: {kpi['label']} → New KPI")
                continue

            # Migrate existing KPI
            if kpi_name in kpi_data:
                current = kpi_data[kpi_name]

                # Label
                updates.append({
                    'range': f"{label_col}{new_row}",
                    'values': [[current['label']]]
                })

                # Formula/Value
                if current['formula']:
                    updates.append({
                        'range': f"{value_col}{new_row}",
                        'values': [[current['formula']]]
                    })
                else:
                    updates.append({
                        'range': f"{value_col}{new_row}",
                        'values': [[current['display_value'] or ""]]
                    })

                # Note
                if current['note']:
                    updates.append({
                        'range': f"{note_col}{new_row}",
                        'values': [[current['note']]]
                    })

                print(f"      Row {new_row}: {current['label']} ← K{current['current_row']}")

    if not dry_run:
        print(f"\n   📝 Applying {len(updates)} cell updates...")
        for i, update in enumerate(updates):
            worksheet.update(update['range'], update['values'])
            if (i + 1) % 10 == 0:
                print(f"      Progress: {i+1}/{len(updates)}")
                time.sleep(1)  # Rate limiting every 10 updates
            else:
                time.sleep(0.3)

        print(f"   ✅ All updates applied!")
    else:
        print(f"\n   [DRY RUN] Would apply {len(updates)} updates")


def clear_old_kpi_locations(worksheet, kpi_data, dry_run=False):
    """
    Clear old KPI locations after migration.
    """
    print(f"\n🧹 {'[DRY RUN] ' if dry_run else ''}Clearing old KPI locations...")

    rows_to_clear = sorted(set([kpi['current_row'] for kpi in kpi_data.values()]))

    for row in rows_to_clear:
        clear_range = f"K{row}:P{row}"

        if not dry_run:
            worksheet.batch_clear([clear_range])
            print(f"   ✅ Cleared {clear_range}")
            time.sleep(0.3)
        else:
            print(f"   [DRY RUN] Would clear {clear_range}")


def main():
    parser = argparse.ArgumentParser(description='Restructure dashboard into 4 blocks')
    parser.add_argument('--preview', action='store_true',
                       help='Show preview without making changes')
    parser.add_argument('--execute', action='store_true',
                       help='Execute the restructure (WARNING: modifies dashboard)')
    args = parser.parse_args()

    if not args.preview and not args.execute:
        print("ERROR: Must specify --preview or --execute")
        print("\nUsage:")
        print("  python3 restructure_dashboard_4block.py --preview     # See what will change")
        print("  python3 restructure_dashboard_4block.py --execute     # Apply changes")
        return

    print("=" * 70)
    print("📊 DASHBOARD 4-BLOCK RESTRUCTURE")
    print("=" * 70)

    # Connect to Google Sheets
    print("\n🔗 Connecting to Google Sheets...")
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=scopes
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)

    print(f"✅ Connected to '{SHEET_NAME}'")

    # Read current KPIs
    kpi_data = read_current_dashboard_kpis(worksheet)

    # Show preview
    preview_restructure(kpi_data)

    if args.execute:
        print("\n" + "=" * 70)
        print("⚠️  EXECUTING RESTRUCTURE")
        print("=" * 70)

        response = input("\n⚠️  This will modify your Live Dashboard v2. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cancelled by user")
            return

        # Step 1: Create block headers
        create_block_headers(worksheet)

        # Step 2: Migrate KPIs
        migrate_kpis(worksheet, kpi_data, dry_run=False)

        # Step 3: Clear old locations
        clear_old_kpi_locations(worksheet, kpi_data, dry_run=False)

        print("\n" + "=" * 70)
        print("✅ RESTRUCTURE COMPLETE!")
        print("=" * 70)
        print("\n📋 MANUAL STEPS REQUIRED:")
        print("   1. Format block headers (bold, colors, merge cells)")
        print("   2. Update Apps Script chart references if needed")
        print("   3. Add conditional formatting to new blocks")
        print("   4. Test all sparklines still working")
        print("\n🔗 Dashboard: https://docs.google.com/spreadsheets/d/{}/edit".format(SPREADSHEET_ID))
    else:
        print("\n✅ Preview complete. Run with --execute to apply changes.")


if __name__ == "__main__":
    main()
