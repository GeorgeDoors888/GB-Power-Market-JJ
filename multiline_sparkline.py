#!/usr/bin/env python3
"""
Generate multi-line Unicode sparklines for better visibility in Google Sheets
Creates 3-line tall sparklines for clearer visualization
"""

def generate_multiline_sparkline(data, height=3):
    """
    Generate a multi-line Unicode sparkline (3 rows tall)

    Args:
        data: List of numeric values
        height: Number of rows (default 3 for good visibility)

    Returns:
        String with newlines creating a 3-line tall sparkline
    """
    # Filter and normalize data
    clean_data = [float(v) if v not in (None, '') else 0 for v in data]

    if not clean_data or max(clean_data) == 0:
        return ''

    # Find last non-zero value
    last_nonzero_idx = -1
    for i in range(len(clean_data) - 1, -1, -1):
        if clean_data[i] != 0:
            last_nonzero_idx = i
            break

    if last_nonzero_idx == -1:
        return ''

    active_data = clean_data[:last_nonzero_idx + 1]

    min_val = min(active_data)
    max_val = max(active_data)

    if max_val == min_val:
        mid_line = '▄' * len(active_data)
        return f"\n{mid_line}\n"

    # Create 3 lines (top, middle, bottom)
    lines = ['', '', '']

    # Unicode blocks for different heights
    # Top row: upper blocks
    # Middle row: middle blocks
    # Bottom row: lower blocks

    for val in active_data:
        normalized = (val - min_val) / (max_val - min_val)

        # Map to 0-8 range (9 levels across 3 rows)
        level = int(normalized * 8)

        if level >= 7:  # 87.5%-100% - fill all 3 rows
            lines[0] += '█'
            lines[1] += '█'
            lines[2] += '█'
        elif level == 6:  # 75%-87.5% - fill bottom 2.5 rows
            lines[0] += '▄'
            lines[1] += '█'
            lines[2] += '█'
        elif level == 5:  # 62.5%-75% - fill bottom 2 rows
            lines[0] += ' '
            lines[1] += '█'
            lines[2] += '█'
        elif level == 4:  # 50%-62.5% - fill bottom 1.5 rows
            lines[0] += ' '
            lines[1] += '▄'
            lines[2] += '█'
        elif level == 3:  # 37.5%-50% - fill bottom 1 row + bit
            lines[0] += ' '
            lines[1] += ' '
            lines[2] += '█'
        elif level == 2:  # 25%-37.5% - partial bottom row
            lines[0] += ' '
            lines[1] += ' '
            lines[2] += '▆'
        elif level == 1:  # 12.5%-25% - small bottom bar
            lines[0] += ' '
            lines[1] += ' '
            lines[2] += '▃'
        else:  # 0%-12.5% - minimal bar
            lines[0] += ' '
            lines[1] += ' '
            lines[2] += '▁'

    return f"{lines[0]}\n{lines[1]}\n{lines[2]}"


if __name__ == '__main__':
    # Test with CCGT pattern (low start, high end)
    ccgt_pattern = [2698, 2723, 2737, 2712, 2739, 2692, 2709, 2728,
                    2664, 2650, 2774, 3389, 4879, 6595, 9786, 10446,
                    10846, 11469, 11963, 12486, 12499, 12547, 12698,
                    13327, 13613, 14093, 14411]

    print("🏭 CCGT Multi-line Sparkline (3 rows tall):")
    print(generate_multiline_sparkline(ccgt_pattern))

    # Test with WIND pattern (high start, low end)
    wind_pattern = [12574, 12981, 12719, 12395, 12169, 12923, 13196,
                    12008, 11759, 12052, 11760, 11564, 11422, 11677,
                    11427, 11386, 11546, 11538, 10858, 10336, 9766,
                    9677, 9891, 9028, 8489, 8619, 8564]

    print("\n🌬️ WIND Multi-line Sparkline (3 rows tall):")
    print(generate_multiline_sparkline(wind_pattern))
