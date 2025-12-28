#!/usr/bin/env python3
"""
Bidirectional sparkline generator for import/export visualization
Shows positive values (imports) in green, negative values (exports) in red
"""

def generate_bidirectional_sparkline(data, bar_chars='▁▂▃▄▅▆▇█'):
    """
    Generate a bidirectional sparkline with color coding
    
    Args:
        data: List of numeric values (positive = import/green, negative = export/red)
        bar_chars: Unicode block characters for height
    
    Returns:
        String with colored sparkline showing imports (+) vs exports (-)
    """
    if not data or len(data) == 0:
        return ''
    
    # Filter out None values
    clean_data = [x if x is not None else 0 for x in data]
    
    # Find max absolute value for scaling
    max_abs = max(abs(x) for x in clean_data)
    if max_abs == 0:
        return '─' * len(clean_data)  # Flat line for all zeros
    
    # Generate sparkline with directional indicators
    result = []
    for val in clean_data:
        if val == 0:
            result.append('·')  # Middle point for zero
        else:
            # Scale to 0-7 range based on absolute value
            normalized = abs(val) / max_abs
            index = min(int(normalized * len(bar_chars)), len(bar_chars) - 1)
            char = bar_chars[index]
            
            # Add directional indicator
            if val > 0:
                result.append(f'🟢{char}')  # Green for import
            else:
                result.append(f'🔴{char}')  # Red for export
    
    return ''.join(result)


def generate_simple_bidirectional_sparkline(data, up_char='▲', down_char='▼', zero_char='─'):
    """
    Generate a simple bidirectional sparkline without colors (for terminals)
    
    Args:
        data: List of numeric values (positive = up, negative = down)
        up_char: Character for positive values
        down_char: Character for negative values
        zero_char: Character for zero values
    
    Returns:
        String with directional sparkline
    """
    if not data or len(data) == 0:
        return ''
    
    clean_data = [x if x is not None else 0 for x in data]
    
    result = []
    for val in clean_data:
        if val > 0:
            result.append(up_char)  # Import
        elif val < 0:
            result.append(down_char)  # Export
        else:
            result.append(zero_char)  # Zero
    
    return ''.join(result)


if __name__ == '__main__':
    # Test data: mix of imports and exports
    test_data = [1000, -500, 200, -800, 0, 300, -400, 600, -100, 50]
    
    print("Bidirectional Sparkline Test:")
    print("Data:", test_data)
    print("Colored:", generate_bidirectional_sparkline(test_data))
    print("Simple:", generate_simple_bidirectional_sparkline(test_data))
