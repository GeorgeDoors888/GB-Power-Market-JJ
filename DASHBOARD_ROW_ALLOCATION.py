"""
Dashboard Row Allocation Registry
Prevents conflicts between automated updaters by defining exclusive row ranges

SPREADSHEET: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
SHEET: Live Dashboard v2 (102 rows × 27 columns)
"""

# ==============================================================================
# ROW ALLOCATION MAP - SINGLE SOURCE OF TRUTH
# ==============================================================================

ROW_ALLOCATION = {
    # HEADER & STATUS (Auto-updated every 10 min)
    'header_status': {
        'rows': (1, 4),
        'columns': 'A:AA',
        'owner': 'update_live_metrics.py',
        'frequency': 'Every 10 min',
        'description': 'Dashboard title, last update timestamp, IRIS status'
    },
    
    # MARKET OVERVIEW KPIs (Auto-updated every 10 min)
    'market_kpis': {
        'rows': (5, 6),
        'columns': 'A:K',
        'owner': 'update_live_metrics.py',
        'frequency': 'Every 10 min',
        'description': 'Demand, Price, Carbon, Frequency, Interconnectors'
    },
    
    # SECTION DIVIDERS (Static)
    'section_headers': {
        'rows': (10, 12),
        'columns': 'A:N',
        'owner': 'Static',
        'frequency': 'Manual only',
        'description': 'Section headers (Gen Mix, Interconnectors, Market Dynamics)'
    },
    
    # GENERATION MIX (Auto-updated every 5 min)
    'generation_mix': {
        'rows': (13, 22),
        'columns': 'A:D',
        'owner': 'update_all_dashboard_sections_fast.py',
        'frequency': 'Every 5 min',
        'description': 'Fuel types, GW output, percentage, bar charts'
    },
    
    # INTERCONNECTORS (Auto-updated every 5 min for names, every 10 min for sparklines)
    'interconnectors': {
        'rows': (13, 22),
        'columns': 'G:H',
        'owner': 'update_all_dashboard_sections_fast.py (G), update_live_metrics.py (H)',
        'frequency': 'Every 5 min (names), Every 10 min (sparklines)',
        'description': 'Column G: Names, Column H: Time-series sparklines (PYTHON ONLY)'
    },
    
    # MARKET DYNAMICS KPIs (Auto-updated every 10 min)
    'market_dynamics': {
        'rows': (13, 22),
        'columns': 'K:N',
        'owner': 'update_live_metrics.py',
        'frequency': 'Every 10 min',
        'description': 'Prices, volumes, spreads, volatility metrics'
    },
    
    # ⚠️ RESERVED EMPTY SPACE (DO NOT USE)
    'reserved_empty': {
        'rows': (23, 24),
        'columns': 'A:N',
        'owner': 'Reserved',
        'frequency': 'N/A',
        'description': 'Buffer space between sections'
    },
    
    # WIND FORECAST & WEATHER ALERTS (Manual update) - ROWS 25-59
    'wind_forecast_dashboard': {
        'rows': (25, 59),  # Professional dashboard with sparklines
        'columns': 'A:H',  # 8 columns for sparklines and heatmap
        'owner': 'create_wind_analysis_dashboard_live.py',
        'frequency': 'Manual (on-demand)',
        'description': 'Professional wind forecast dashboard: KPIs, sparklines (not charts), revenue impact, farm heatmap'
    },
    
    # ACTIVE OUTAGES (Apps Script manual trigger)
    'active_outages': {
        'rows': (25, 35),
        'columns': 'G:J',
        'owner': 'Apps Script (Data.gs displayOutages)',
        'frequency': 'Manual trigger',
        'description': 'Current generation unit outages from REMIT'
    },
    
    # ✅ CLEARING ZONE REMOVED (Previously rows 25-43, columns A:F)
    # Clearing code removed from update_live_metrics.py line 1480-1482
    # Wind dashboard can now safely use rows 25-48 columns A:G
    
    # OUTAGE DETAILS (Apps Script continuation)
    'outage_details': {
        'rows': (43, 50),
        'columns': 'G:O',
        'owner': 'Apps Script (Data.gs displayOutages)',
        'frequency': 'Manual trigger',
        'description': 'Detailed outage information (type, start, duration, end)'
    },
    
    # ⚠️ AVAILABLE SPACE (Rows 74-102)
    'available_space': {
        'rows': (74, 102),
        'columns': 'A:AA',
        'owner': 'Unallocated',
        'frequency': 'Available',
        'description': 'Free space for new dashboards/features'
    },
}


# ==============================================================================
# CONFLICT DETECTION
# ==============================================================================

def check_row_conflict(start_row, end_row, columns='A:Z'):
    """
    Check if proposed row range conflicts with existing allocations
    
    Args:
        start_row: Starting row (1-indexed)
        end_row: Ending row (1-indexed, inclusive)
        columns: Column range (e.g., 'A:G')
    
    Returns:
        List of conflicts (empty if no conflicts)
    """
    conflicts = []
    
    for section_name, allocation in ROW_ALLOCATION.items():
        alloc_start, alloc_end = allocation['rows']
        
        # Check row overlap
        if not (end_row < alloc_start or start_row > alloc_end):
            # Check column overlap
            if columns_overlap(columns, allocation['columns']):
                conflicts.append({
                    'section': section_name,
                    'rows': allocation['rows'],
                    'columns': allocation['columns'],
                    'owner': allocation['owner'],
                    'description': allocation['description']
                })
    
    return conflicts


def columns_overlap(range1, range2):
    """Check if two column ranges overlap (simplified)"""
    # Basic overlap detection - can be enhanced
    return True  # For now, assume overlap exists


def get_next_available_row(min_rows_needed=10):
    """Find the next available contiguous row block"""
    used_rows = set()
    
    for allocation in ROW_ALLOCATION.values():
        start, end = allocation['rows']
        for row in range(start, end + 1):
            used_rows.add(row)
    
    # Find first contiguous block
    current_start = None
    current_count = 0
    
    for row in range(1, 103):  # 102 rows max
        if row not in used_rows:
            if current_start is None:
                current_start = row
            current_count += 1
            
            if current_count >= min_rows_needed:
                return current_start, current_start + min_rows_needed - 1
        else:
            current_start = None
            current_count = 0
    
    return None, None


def print_allocation_map():
    """Print visual allocation map"""
    print("=" * 80)
    print("GOOGLE SHEETS DASHBOARD ROW ALLOCATION MAP")
    print("=" * 80)
    print(f"Spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA")
    print(f"Sheet: Live Dashboard v2 (102 rows × 27 columns)")
    print("=" * 80)
    
    # Sort by row start
    sorted_sections = sorted(
        ROW_ALLOCATION.items(),
        key=lambda x: x[1]['rows'][0]
    )
    
    print(f"\n{'Rows':<12} {'Columns':<12} {'Owner':<40} {'Update Freq':<20}")
    print("-" * 80)
    
    for section_name, allocation in sorted_sections:
        start, end = allocation['rows']
        row_range = f"{start}-{end}"
        
        # Color code by owner
        if 'update_live_metrics' in allocation['owner']:
            marker = '🔄'
        elif 'update_all_dashboard' in allocation['owner']:
            marker = '⚡'
        elif 'Apps Script' in allocation['owner']:
            marker = '📱'
        elif 'CLEARS' in allocation['owner']:
            marker = '⚠️'
        elif allocation['owner'] == 'Static':
            marker = '📌'
        elif allocation['owner'] == 'Reserved':
            marker = '🚫'
        elif allocation['owner'] == 'Unallocated':
            marker = '✅'
        else:
            marker = '📊'
        
        print(f"{marker} {row_range:<10} {allocation['columns']:<12} {allocation['owner']:<40} {allocation['frequency']:<20}")
        print(f"   └─ {allocation['description']}")
        print()


# ==============================================================================
# SAFE UPDATE HELPERS
# ==============================================================================

def get_safe_range(section_name):
    """Get the safe update range for a given section"""
    if section_name not in ROW_ALLOCATION:
        raise ValueError(f"Unknown section: {section_name}")
    
    allocation = ROW_ALLOCATION[section_name]
    start, end = allocation['rows']
    columns = allocation['columns']
    
    return f"Live Dashboard v2!{columns}{start}:{columns}{end}"


def is_safe_to_write(start_row, end_row, columns, script_name):
    """
    Check if it's safe for a script to write to a range
    
    Args:
        start_row: Starting row (1-indexed)
        end_row: Ending row (1-indexed)
        columns: Column range (e.g., 'A:G')
        script_name: Name of script attempting to write
    
    Returns:
        (bool, str): (is_safe, reason)
    """
    conflicts = check_row_conflict(start_row, end_row, columns)
    
    if not conflicts:
        return True, "No conflicts"
    
    # Check if conflicts are with sections owned by this script
    for conflict in conflicts:
        if script_name not in conflict['owner']:
            return False, f"Conflict with {conflict['section']} (owned by {conflict['owner']})"
    
    return True, "Writing to own section"


# ==============================================================================
# USAGE EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print_allocation_map()
    
    print("\n" + "=" * 80)
    print("CONFLICT DETECTION EXAMPLES")
    print("=" * 80)
    
    # Example 1: Check if wind dashboard at rows 25-48 conflicts
    print("\n1. Checking wind dashboard at rows 25-48, columns A:G...")
    conflicts = check_row_conflict(25, 48, 'A:G')
    if conflicts:
        print(f"   ⚠️ CONFLICTS FOUND ({len(conflicts)}):")
        for c in conflicts:
            print(f"      - {c['section']}: rows {c['rows']}, owner: {c['owner']}")
    else:
        print("   ✅ No conflicts")
    
    # Example 2: Check if wind dashboard at rows 50-73 conflicts
    print("\n2. Checking wind dashboard at rows 50-73, columns A:G...")
    conflicts = check_row_conflict(50, 73, 'A:G')
    if conflicts:
        print(f"   ⚠️ CONFLICTS FOUND ({len(conflicts)}):")
        for c in conflicts:
            print(f"      - {c['section']}: rows {c['rows']}, owner: {c['owner']}")
    else:
        print("   ✅ No conflicts - SAFE LOCATION")
    
    # Example 3: Find next available space
    print("\n3. Finding next available 20-row block...")
    start, end = get_next_available_row(20)
    if start:
        print(f"   ✅ Available: rows {start}-{end}")
    else:
        print("   ⚠️ No contiguous 20-row block available")
    
    print("\n" + "=" * 80)
    print("SAFE RANGE HELPERS")
    print("=" * 80)
    
    print("\n✅ Safe ranges for common updates:")
    print(f"   Generation Mix: {get_safe_range('generation_mix')}")
    print(f"   Market KPIs: {get_safe_range('market_kpis')}")
    print(f"   Wind Dashboard: {get_safe_range('wind_forecast_dashboard')}")
