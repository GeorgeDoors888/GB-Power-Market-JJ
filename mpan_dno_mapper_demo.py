#!/usr/bin/env python3
"""
MPAN to DNO Mapper Demo
----------------------
Demonstrates how to use the mpan_dno_mapper.py script to:
1. Process a sample CSV file with MPANs
2. Identify DNOs from the MPANs
3. Merge with DUoS data
"""

import os
import sys
import pandas as pd

# Import the MPAN to DNO mapper module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from mpan_dno_mapper import (
    enrich_dataframe, 
    process_csv_file, 
    merge_with_duos_data,
    test_examples
)


def main():
    """Run the demo."""
    print("\n==== MPAN to DNO Mapper Demo ====\n")
    
    # Step 1: Run test examples
    print("Step 1: Running test examples...\n")
    test_examples()
    
    # Step 2: Process example CSV file
    input_file = "example_mpan_data.csv"
    output_file = "example_mpan_data_enriched.csv"
    
    print(f"\nStep 2: Processing {input_file}...\n")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return
    
    process_csv_file(input_file, output_file, mpan_column="MPAN")
    
    # Step 3: Display results
    print("\nStep 3: Displaying results...\n")
    
    enriched_df = pd.read_csv(output_file)
    
    # Display a summary of DNOs found
    dno_counts = enriched_df["DNO_Name"].value_counts()
    
    print("DNO Distribution:")
    for dno, count in dno_counts.items():
        print(f"  {dno}: {count} records")
    
    # Step 4: Merge with DUoS data (if available)
    duos_ref_file = "duos_outputs2/gsheets_csv/DNO_Reference_20250914_195528.csv"
    
    if os.path.exists(duos_ref_file):
        print(f"\nStep 4: Merging with DUoS data from {duos_ref_file}...\n")
        
        merged_output = "example_mpan_data_with_duos.csv"
        merge_with_duos_data(output_file, duos_ref_file, merged_output, mpan_column="MPAN")
        
        print("\nDone! Check the following files:")
        print(f"  - {output_file} (MPAN data with DNO information)")
        print(f"  - {merged_output} (MPAN data merged with DUoS reference)")
    else:
        print(f"\nDUoS reference file not found: {duos_ref_file}")
        print("Skipping merge step.")
        
        print("\nDone! Check the following file:")
        print(f"  - {output_file} (MPAN data with DNO information)")


if __name__ == "__main__":
    main()
