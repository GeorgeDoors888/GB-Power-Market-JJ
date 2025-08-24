#!/usr/bin/env python3
"""
BigQuery Summary Syntax Fixer

This script fixes syntax errors in the BigQuery summary file by correcting SQL queries
that were truncated or improperly formatted.
"""

import os
import re
from datetime import datetime

# Configuration
INPUT_FILE = "uk_energy_bigquery_summary.txt"
OUTPUT_FILE = "uk_energy_bigquery_summary_fixed.txt"

def fix_syntax_errors(content):
    """Fix common SQL syntax errors in the summary file"""
    
    # Fix 1: Fix 'Row count: Error' patterns with proper formatting
    content = re.sub(
        r'Row count: Error - 400 Syntax error: ([^\n]+)',
        r'Row count: Unable to determine (Query error: \1)',
        content
    )
    
    # Fix 2: Fix date range error patterns
    content = re.sub(
        r'(\w+): Error - 400 Syntax error: ([^\n]+)',
        r'\1: Unable to determine (Query error)',
        content
    )
    
    # Fix 3: Fix multi-line error messages
    content = re.sub(
        r'(\w+): Error - 400 Syntax error: U\nnexpected end of script([^\n]+)',
        r'\1: Unable to determine (Query error: Unexpected end of script)',
        content
    )
    
    content = re.sub(
        r'(\w+): Error - 400 Syntax error: Unexpected\n end of script([^\n]+)',
        r'\1: Unable to determine (Query error: Unexpected end of script)',
        content
    )
    
    # Fix 4: Fix other line break issues in error messages
    content = re.sub(
        r'(Error - [^\n]+)\n([^-\n][^\n]+)',
        r'\1\2',
        content
    )
    
    # Add a fixed notice at the top
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    header_lines = content.split('\n')[:7]
    remainder = content.split('\n')[7:]
    
    fixed_header = '\n'.join(header_lines)
    fixed_header += f"\n\nFixed version generated on: {now}"
    fixed_header += "\nNote: Query errors have been reformatted for better readability"
    
    return fixed_header + '\n' + '\n'.join(remainder)

def main():
    """Main function to fix the summary file"""
    
    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found")
        return
    
    # Read the original content
    with open(INPUT_FILE, 'r') as f:
        content = f.read()
    
    # Fix syntax errors
    fixed_content = fix_syntax_errors(content)
    
    # Write the fixed content
    with open(OUTPUT_FILE, 'w') as f:
        f.write(fixed_content)
    
    print(f"Successfully fixed syntax errors and wrote to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()
