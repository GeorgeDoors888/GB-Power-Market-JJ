#!/usr/bin/env python3
"""
MPAN to DNO Mapper
-----------------
Identifies Distribution Network Operators (DNOs) from MPANs in CSV files.

This script:
1. Parses and validates MPANs according to official UK electricity industry standards
2. Extracts the Distributor ID (first 2 digits of MPAN core)
3. Maps the Distributor ID to the corresponding DNO
4. Enriches CSV files with DNO information

Usage:
    python mpan_dno_mapper.py <input_csv> <output_csv> --mpan-column <column_name>
"""

import argparse
import csv
import os
import re
import sys
from typing import Dict, List, Optional, Union

import pandas as pd


# =============================================================================
# Constants & Lookup Data
# =============================================================================

# Primes used in the check digit calculation, per official MPAN rules
CHECK_PRIMES = [3, 5, 7, 13, 17, 19, 23, 29, 31, 37, 41, 43]

# DNO Lookup table: maps Distributor ID (as string) to a dict of DNO info
DNO_LOOKUP: Dict[str, Dict[str, str]] = {
    "10": {
        "DNO_Key": "UKPN-EPN",
        "DNO_Name": "UK Power Networks (Eastern)",
        "Short_Code": "EPN",
        "Market_Participant_ID": "EELC",
        "GSP_Group_ID": "A",
        "GSP_Group_Name": "Eastern",
    },
    "12": {
        "DNO_Key": "UKPN-LPN",
        "DNO_Name": "UK Power Networks (London)",
        "Short_Code": "LPN",
        "Market_Participant_ID": "LOND",
        "GSP_Group_ID": "C",
        "GSP_Group_Name": "London",
    },
    "19": {
        "DNO_Key": "UKPN-SPN",
        "DNO_Name": "UK Power Networks (South Eastern)",
        "Short_Code": "SPN",
        "Market_Participant_ID": "SEEB",
        "GSP_Group_ID": "J",
        "GSP_Group_Name": "South Eastern",
    },
    "16": {
        "DNO_Key": "ENWL",
        "DNO_Name": "Electricity North West",
        "Short_Code": "ENWL",
        "Market_Participant_ID": "NORW",
        "GSP_Group_ID": "G",
        "GSP_Group_Name": "North West",
    },
    "15": {
        "DNO_Key": "NPg-NE",
        "DNO_Name": "Northern Powergrid (North East)",
        "Short_Code": "NE",
        "Market_Participant_ID": "NEEB",
        "GSP_Group_ID": "F",
        "GSP_Group_Name": "North East",
    },
    "23": {
        "DNO_Key": "NPg-Y",
        "DNO_Name": "Northern Powergrid (Yorkshire)",
        "Short_Code": "Y",
        "Market_Participant_ID": "YELG",
        "GSP_Group_ID": "M",
        "GSP_Group_Name": "Yorkshire",
    },
    "18": {
        "DNO_Key": "SP-Distribution",
        "DNO_Name": "SP Energy Networks (SPD)",
        "Short_Code": "SPD",
        "Market_Participant_ID": "SPOW",
        "GSP_Group_ID": "N",
        "GSP_Group_Name": "South Scotland",
    },
    "13": {
        "DNO_Key": "SP-Manweb",
        "DNO_Name": "SP Energy Networks (SPM)",
        "Short_Code": "SPM",
        "Market_Participant_ID": "MANW",
        "GSP_Group_ID": "D",
        "GSP_Group_Name": "Merseyside & North Wales",
    },
    "17": {
        "DNO_Key": "SSE-SHEPD",
        "DNO_Name": "Scottish Hydro Electric Power Distribution (SHEPD)",
        "Short_Code": "SHEPD",
        "Market_Participant_ID": "HYDE",
        "GSP_Group_ID": "P",
        "GSP_Group_Name": "North Scotland",
    },
    "20": {
        "DNO_Key": "SSE-SEPD",
        "DNO_Name": "Southern Electric Power Distribution (SEPD)",
        "Short_Code": "SEPD",
        "Market_Participant_ID": "SOUT",
        "GSP_Group_ID": "H",
        "GSP_Group_Name": "Southern",
    },
    "14": {
        "DNO_Key": "NGED-WM",
        "DNO_Name": "National Grid Electricity Distribution – West Midlands (WMID)",
        "Short_Code": "WMID",
        "Market_Participant_ID": "MIDE",
        "GSP_Group_ID": "E",
        "GSP_Group_Name": "West Midlands",
    },
    "11": {
        "DNO_Key": "NGED-EM",
        "DNO_Name": "National Grid Electricity Distribution – East Midlands (EMID)",
        "Short_Code": "EMID",
        "Market_Participant_ID": "EMEB",
        "GSP_Group_ID": "B",
        "GSP_Group_Name": "East Midlands",
    },
    "22": {
        "DNO_Key": "NGED-SW",
        "DNO_Name": "National Grid Electricity Distribution – South West (SWEST)",
        "Short_Code": "SWEST",
        "Market_Participant_ID": "SWEB",
        "GSP_Group_ID": "L",
        "GSP_Group_Name": "South Western",
    },
    "21": {
        "DNO_Key": "NGED-SWales",
        "DNO_Name": "National Grid Electricity Distribution – South Wales (SWALES)",
        "Short_Code": "SWALES",
        "Market_Participant_ID": "SWAE",
        "GSP_Group_ID": "K",
        "GSP_Group_Name": "South Wales",
    },
}


# =============================================================================
# MPAN / MPAN Core parsing and validation
# =============================================================================


def clean_mpan(raw: Union[str, None]) -> str:
    """
    Clean up MPAN input, remove spaces/hyphens, take the core 13 digits.
    
    Args:
        raw: Any string that contains or may contain an MPAN or MPAN core.
    
    Returns:
        The 13-digit MPAN core if possible, else returns empty string.
    """
    if raw is None:
        return ""
    
    # Convert to string if not already
    if not isinstance(raw, str):
        raw = str(raw)
    
    # Remove non-digits
    s = re.sub(r"[^0-9]", "", raw)
    
    # If it's longer than 13 digits, take last 13 digits (core is bottom row, usually last 13)
    if len(s) >= 13:
        core = s[-13:]
    else:
        core = s
    
    return core


def compute_check_digit(mpan_core13: str) -> Optional[int]:
    """
    Compute the check digit from the first 12 digits of the core (13 total).
    
    According to the algorithm: sum(digits[i] * primes[i] for i in 0..11), then mod 11, then mod 10.
    
    Args:
        mpan_core13: A 13-digit MPAN core string.
    
    Returns:
        The integer of computed check digit, or None if input invalid.
    """
    if len(mpan_core13) != 13 or not mpan_core13.isdigit():
        return None
    
    total = 0
    for i in range(12):
        d = int(mpan_core13[i])
        prime = CHECK_PRIMES[i]
        total += d * prime
    
    cd = (total % 11) % 10
    return cd


def is_valid_mpan_core(mpan_core13: str) -> bool:
    """
    Validate an MPAN core (13 digits).
    
    Checks it's numeric, correct length, and that the computed 
    check digit matches the 13th digit.
    
    Args:
        mpan_core13: A 13-digit MPAN core string.
    
    Returns:
        True if valid, False otherwise.
    """
    if len(mpan_core13) != 13 or not mpan_core13.isdigit():
        return False
    
    computed = compute_check_digit(mpan_core13)
    if computed is None:
        return False
    
    return computed == int(mpan_core13[-1])


def get_distributor_id(mpan_core13: str) -> Optional[str]:
    """
    Extract Distributor ID, which is the first 2 digits of the MPAN core.
    
    Args:
        mpan_core13: A 13-digit MPAN core string.
    
    Returns:
        The 2-digit string, or None if core is too short/malformed.
    """
    if len(mpan_core13) < 2 or not mpan_core13[:2].isdigit():
        return None
    
    return mpan_core13[:2]


def lookup_dno(distributor_id: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Given a distributor_id, return the DNO info from lookup.
    
    Args:
        distributor_id: A 2-digit string representing the Distributor ID.
    
    Returns:
        Dict with DNO information, or None if not found.
    """
    if distributor_id is None:
        return None
    
    return DNO_LOOKUP.get(distributor_id)


# =============================================================================
# CSV Processing
# =============================================================================


def enrich_dataframe(df: pd.DataFrame, mpan_column: str = "MPAN") -> pd.DataFrame:
    """
    Given a DataFrame with a column containing raw MPAN or MPAN core, add DNO information.
    
    Adds columns:
      - mpan_core (cleaned 13 digit string)
      - distributor_id (2 digit string)
      - mpan_valid (True/False)
      - DNO_Key, DNO_Name, Short_Code, Market_Participant_ID, GSP_Group_ID, GSP_Group_Name
    
    Args:
        df: Pandas DataFrame with MPAN data.
        mpan_column: Name of the column containing MPANs.
    
    Returns:
        Enriched DataFrame with added columns.
    """
    # Copy to avoid modifying original
    df2 = df.copy()
    
    # If the specified column doesn't exist, try to find a similar one
    if mpan_column not in df2.columns:
        possible_columns = [
            col for col in df2.columns
            if "mpan" in col.lower() or "meter" in col.lower() or "id" in col.lower()
        ]
        if possible_columns:
            mpan_column = possible_columns[0]
            print(f"Warning: Using column '{mpan_column}' for MPAN data")
        else:
            raise KeyError(f"Column '{mpan_column}' not found in input data")
    
    # Clean MPAN core
    df2["mpan_core"] = df2[mpan_column].astype(str).apply(clean_mpan)
    
    # Distributor ID
    df2["distributor_id"] = df2["mpan_core"].apply(get_distributor_id)
    
    # Valid flag
    df2["mpan_valid"] = df2["mpan_core"].apply(is_valid_mpan_core)
    
    # Initialize DNO columns
    dno_columns = [
        "DNO_Key", "DNO_Name", "Short_Code", "Market_Participant_ID", 
        "GSP_Group_ID", "GSP_Group_Name"
    ]
    for col in dno_columns:
        df2[col] = None
    
    # Map DNO info
    for idx, row in df2.iterrows():
        did = row["distributor_id"]
        dno_info = lookup_dno(did)
        if dno_info:
            for col in dno_columns:
                df2.at[idx, col] = dno_info.get(col)
        else:
            # Mark unknown DNO
            df2.at[idx, "DNO_Key"] = "UNKNOWN"
    
    return df2


def process_csv_file(input_path: str, output_path: str, mpan_column: str = "MPAN"):
    """
    Read CSV, enrich it, write out a new CSV with added columns.
    
    Args:
        input_path: Path to input CSV file.
        output_path: Path to output CSV file.
        mpan_column: Name of the column containing MPANs.
    """
    print(f"Processing {input_path}...")
    
    try:
        df = pd.read_csv(input_path, dtype=str)
        df_enriched = enrich_dataframe(df, mpan_column=mpan_column)
        df_enriched.to_csv(output_path, index=False)
        
        # Print summary
        total_rows = len(df_enriched)
        valid_mpans = df_enriched["mpan_valid"].sum()
        known_dnos = df_enriched["DNO_Key"].notna().sum() - df_enriched["DNO_Key"].eq("UNKNOWN").sum()
        
        print(f"\nSummary:")
        print(f"  Total rows: {total_rows}")
        print(f"  Valid MPANs: {valid_mpans} ({valid_mpans/total_rows*100:.1f}%)")
        print(f"  Known DNOs: {known_dnos} ({known_dnos/total_rows*100:.1f}%)")
        print(f"\nEnriched CSV written to {output_path}")
        
    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise


# =============================================================================
# Integration with DNO DUoS data
# =============================================================================


def merge_with_duos_data(
    mpan_data_path: str, 
    duos_data_path: str, 
    output_path: str,
    mpan_column: str = "MPAN"
):
    """
    Merge MPAN data with DUoS data based on DNO_Key.
    
    Args:
        mpan_data_path: Path to CSV with MPAN data (enriched with DNO info).
        duos_data_path: Path to DUoS data CSV file.
        output_path: Path to output CSV file.
        mpan_column: Name of the column containing MPANs.
    """
    print(f"Merging MPAN data with DUoS data...")
    
    try:
        # Load and enrich MPAN data
        mpan_df = pd.read_csv(mpan_data_path, dtype=str)
        enriched_df = enrich_dataframe(mpan_df, mpan_column=mpan_column)
        
        # Load DUoS data
        duos_df = pd.read_csv(duos_data_path, dtype=str)
        
        # Determine the right column names for joining
        # Check if the reference file has MPAN_Code column
        if "MPAN_Code" in duos_df.columns and "DNO_Key" in duos_df.columns:
            # This is the reference file format
            # Merge on distributor_id and MPAN_Code
            merged_df = pd.merge(
                enriched_df, 
                duos_df,
                left_on="distributor_id",
                right_on="MPAN_Code",
                how="left",
                suffixes=("", "_ref")
            )
        elif "dno_name" in duos_df.columns:
            # This might be a DUoS data file
            # Merge on DNO_Name
            merged_df = pd.merge(
                enriched_df, 
                duos_df,
                left_on="DNO_Name",
                right_on="dno_name",
                how="left",
                suffixes=("", "_duos")
            )
        elif "dno_key" in duos_df.columns:
            # Try to merge on DNO_Key
            merged_df = pd.merge(
                enriched_df, 
                duos_df,
                left_on="DNO_Key",
                right_on="dno_key",
                how="left",
                suffixes=("", "_duos")
            )
        else:
            # Just return the enriched data with a warning
            print("Warning: Could not determine how to merge with DUoS data")
            print("Columns in DUoS file:", duos_df.columns.tolist())
            merged_df = enriched_df
        
        # Save merged data
        merged_df.to_csv(output_path, index=False)
        
        print(f"Merged data written to {output_path}")
        
    except Exception as e:
        print(f"Error merging data: {str(e)}")
        raise


# =============================================================================
# Example / Test functions
# =============================================================================


def test_examples():
    """Test MPAN parsing and validation with various examples."""
    examples = [
        "1001234567895",           # 10-prefix, 13 digits
        "S 00 100 123 4567895",    # with spaces, non-digit chars
        "1200000000000",           # 12-prefix, maybe invalid check digit
        "9912345678901",           # unknown distributor id 99
        "130123456789X",           # invalid non-digit
        "10abcdefghijk5",          # invalid
    ]
    
    print("\nTesting MPAN examples:")
    print(f"{'Raw MPAN':<25} {'MPAN Core':<15} {'Valid':<7} {'Dist ID':<8} {'DNO'}")
    print("-" * 80)
    
    for raw in examples:
        core = clean_mpan(raw)
        valid = is_valid_mpan_core(core)
        did = get_distributor_id(core)
        dno_info = lookup_dno(did)
        dno_name = dno_info["DNO_Name"] if dno_info else "Unknown"
        
        print(f"{raw:<25} {core:<15} {str(valid):<7} {did if did else 'N/A':<8} {dno_name}")


def main():
    """Main function to process command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Map MPANs to DNOs and enrich CSV files with DNO information."
    )
    
    parser.add_argument(
        "input_file", 
        help="Input CSV file containing MPAN data"
    )
    parser.add_argument(
        "output_file", 
        help="Output CSV file to write enriched data"
    )
    parser.add_argument(
        "--mpan-column", 
        default="MPAN",
        help="Name of the column containing MPANs (default: MPAN)"
    )
    parser.add_argument(
        "--duos-file",
        help="Optional DUoS data file to merge with (if provided, output will contain merged data)"
    )
    parser.add_argument(
        "--test", 
        action="store_true",
        help="Run test examples instead of processing files"
    )
    
    args = parser.parse_args()
    
    if args.test:
        test_examples()
        return
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    
    process_csv_file(args.input_file, args.output_file, args.mpan_column)
    
    if args.duos_file:
        if not os.path.exists(args.duos_file):
            print(f"Error: DUoS file '{args.duos_file}' not found")
            sys.exit(1)
        
        merged_output = os.path.splitext(args.output_file)[0] + "_with_duos.csv"
        merge_with_duos_data(args.output_file, args.duos_file, merged_output, args.mpan_column)


if __name__ == "__main__":
    main()
