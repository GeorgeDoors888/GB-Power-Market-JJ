#!/usr/bin/env python3
"""
Generate Unicode text-based sparklines for Google Sheets
Much simpler and faster than image-based sparklines
"""

def generate_unicode_sparkline(data, bar_chars='▁▂▃▄▅▆▇█'):
    """
    Generate a Unicode sparkline from data - shows all values including zeros

    Args:
        data: List of numeric values
        bar_chars: Unicode block characters (lowest ▁ to highest █)

    Returns:
        String of Unicode bar characters representing the data
    """
    # Filter and normalize data
    clean_data = [float(v) if v not in (None, '') else 0 for v in data]

    if not clean_data or max(clean_data) == 0:
        return ''  # Return empty string if no data

    # Find last non-zero value to exclude trailing zeros (future periods only)
    last_nonzero_idx = -1
    for i in range(len(clean_data) - 1, -1, -1):
        if clean_data[i] != 0:
            last_nonzero_idx = i
            break

    if last_nonzero_idx == -1:
        return ''  # No actual data

    # Only use data up to last non-zero value (excludes future periods)
    active_data = clean_data[:last_nonzero_idx + 1]

    # Get min/max from ALL values (including zeros for proper scaling)
    min_val = min(active_data)
    max_val = max(active_data)

    if max_val == min_val:
        return bar_chars[4] * len(active_data)  # Middle character for flat data

    # Map each value to a bar character (include zeros as lowest bar)
    sparkline = ''
    for val in active_data:
        # Normalize: min_val → index 0 (▁), max_val → index 7 (█)
        normalized = (val - min_val) / (max_val - min_val)
        bar_index = min(int(normalized * (len(bar_chars) - 1)), len(bar_chars) - 1)
        sparkline += bar_chars[bar_index]

    return sparkline

if __name__ == '__main__':
    # Test sparkline generation
    test_data = [1, 4, 2, 8, 5, 7, 11, 9, 13, 15, 14, 17]

    sparkline = generate_unicode_sparkline(test_data)
    print(f'Test data: {test_data}')
    print(f'Sparkline: {sparkline}')
    print(f'Length: {len(sparkline)} characters')
    print('✅ Unicode sparkline generator ready')
