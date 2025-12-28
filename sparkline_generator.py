#!/usr/bin/env python3
"""
Generate inline sparkline images for Google Sheets
Replaces SPARKLINE formulas with actual chart images
"""

import io
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def generate_sparkline_image(data, width=200, height=40, chart_type='column', color='#4285F4'):
    """
    Generate a sparkline chart as a base64-encoded PNG image
    
    Args:
        data: List of numeric values
        width: Image width in pixels
        height: Image height in pixels
        chart_type: 'column' or 'line'
        color: Hex color code
    
    Returns:
        Base64-encoded PNG image string suitable for IMAGE() formula
    """
    # Filter out None/empty values and convert to float
    clean_data = [float(v) if v not in (None, '', 0) else 0 for v in data]
    
    # Create figure with specific size
    dpi = 100
    fig_width = width / dpi
    fig_height = height / dpi
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # Remove all margins and axes
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.axis('off')
    
    # Plot based on chart type
    x = np.arange(len(clean_data))
    
    if chart_type == 'column':
        # Bar chart
        ax.bar(x, clean_data, color=color, width=0.8, edgecolor='none')
    else:
        # Line chart
        ax.plot(x, clean_data, color=color, linewidth=2)
        ax.fill_between(x, clean_data, alpha=0.3, color=color)
    
    # Set y-axis limits with some padding
    if max(clean_data) > 0:
        ax.set_ylim(min(clean_data) * 1.1 if min(clean_data) < 0 else 0, 
                    max(clean_data) * 1.1)
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, 
                transparent=True, dpi=dpi)
    plt.close(fig)
    
    # Encode as base64
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    
    return img_base64

def create_image_formula(base64_data):
    """
    Create Google Sheets IMAGE() formula from base64 data
    
    Args:
        base64_data: Base64-encoded PNG image
    
    Returns:
        IMAGE() formula string
    """
    return f'=IMAGE("data:image/png;base64,{base64_data}")'

if __name__ == '__main__':
    # Test sparkline generation
    test_data = [10, 15, 12, 18, 22, 19, 25, 23, 28, 30, 27, 32]
    
    print('Generating test column sparkline...')
    img_data = generate_sparkline_image(test_data, chart_type='column')
    formula = create_image_formula(img_data)
    print(f'Formula length: {len(formula)} chars')
    print(f'First 100 chars: {formula[:100]}...')
    
    print('\nGenerating test line sparkline...')
    img_data2 = generate_sparkline_image(test_data, chart_type='line', color='#EA4335')
    formula2 = create_image_formula(img_data2)
    print(f'Formula length: {len(formula2)} chars')
    print('✅ Sparkline generator ready')
