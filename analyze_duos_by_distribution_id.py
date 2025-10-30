#!/usr/bin/env python3
"""
Analyze DUoS (Distribution Use of System) charging data by Distribution ID/MPAN ID
Using only local hard drive data files
"""

import glob
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

# MPAN ID to DNO mapping based on official UK distribution areas
MPAN_TO_DNO = {
    10: "UK Power Networks Eastern (EPN)",
    11: "UK Power Networks London (LPN)",
    12: "UK Power Networks South Eastern (SPN)",
    13: "SP Manweb (SPM) - Wales & Merseyside",
    14: "SP Distribution (SPD) - South Scotland",
    15: "SP Energy Networks (SPEN) - Central & South Scotland",
    16: "Northern Powergrid (NEDL) - North East England",
    17: "Scottish Hydro Electric Power Distribution (SHEPD) - North Scotland",
    18: "UK Power Networks Eastern (EPN) - East England",
    19: "Northern Powergrid (YEDL) - Yorkshire",
    20: "Southern Electric Power Distribution (SEPD) - Southern England",
    21: "National Grid Electricity Distribution (NGED) - West Midlands",
    22: "National Grid Electricity Distribution (NGED) - East Midlands",
    23: "Electricity North West (ENWL) - North West England",
    24: "National Grid Electricity Distribution (NGED) - South Wales",
    25: "National Grid Electricity Distribution (NGED) - South West England",
}


def find_duos_data_directories():
    """Find all directories containing DUoS data"""
    base_path = Path(".")
    duos_dirs = []

    # Look for directories with 'duos' in the name
    for item in base_path.iterdir():
        if item.is_dir() and "duos" in item.name.lower():
            duos_dirs.append(item)

    print(f"📁 Found {len(duos_dirs)} DUoS data directories:")
    for dir_path in duos_dirs:
        print(f"   - {dir_path}")

    return duos_dirs


def load_extraction_summary(dir_path):
    """Load the extraction summary JSON file from a directory"""
    summary_file = dir_path / "duos_extraction_summary.json"

    if summary_file.exists():
        with open(summary_file, "r") as f:
            return json.load(f)
    return None


def analyze_csv_file(csv_path):
    """Analyze a single CSV file to extract Distribution ID info"""
    try:
        df = pd.read_csv(csv_path)

        # Extract info from filename
        filename = Path(csv_path).name

        # Try to identify DNO from filename
        dno_name = "Unknown"
        year = None

        # Parse filename for DNO and year info
        filename_lower = filename.lower()

        if "electricity_north_west" in filename_lower or "enwl" in filename_lower:
            dno_name = "Electricity North West (ENWL)"
            mpan_id = 23
        elif "uk_power_networks_eastern" in filename_lower:
            dno_name = "UK Power Networks Eastern (EPN)"
            mpan_id = 10
        elif "uk_power_networks_london" in filename_lower:
            dno_name = "UK Power Networks London (LPN)"
            mpan_id = 11
        elif "uk_power_networks_south" in filename_lower:
            dno_name = "UK Power Networks South Eastern (SPN)"
            mpan_id = 12
        elif "northern_powergrid" in filename_lower:
            dno_name = "Northern Powergrid"
            mpan_id = 16  # Could be 16 or 19, need more info
        elif "sp_distribution" in filename_lower:
            dno_name = "SP Distribution (SPD)"
            mpan_id = 14
        elif "sp_manweb" in filename_lower:
            dno_name = "SP Manweb (SPM)"
            mpan_id = 13
        else:
            mpan_id = None

        # Extract year from filename
        import re

        year_match = re.search(r"(\d{4})", filename)
        if year_match:
            year = int(year_match.group(1))

        return {
            "file_path": str(csv_path),
            "filename": filename,
            "dno_name": dno_name,
            "mpan_id": mpan_id,
            "year": year,
            "rows": len(df),
            "columns": list(df.columns),
            "column_count": len(df.columns),
            "data_sample": df.head(3).to_dict("records") if len(df) > 0 else [],
        }

    except Exception as e:
        return {"file_path": str(csv_path), "error": str(e)}


def analyze_all_duos_data():
    """Analyze all DUoS data files by Distribution ID/MPAN ID"""
    print("🔍 Analyzing DUoS Data by Distribution ID/MPAN ID")
    print("=" * 60)

    # Find all DUoS directories
    duos_dirs = find_duos_data_directories()

    # Collect all data by MPAN ID
    mpan_data = defaultdict(list)
    all_files = []

    for dir_path in duos_dirs:
        print(f"\n📂 Analyzing directory: {dir_path}")

        # Load extraction summary if available
        summary = load_extraction_summary(dir_path)
        if summary:
            print(f"   📄 Extraction Summary:")
            print(f"   - Extraction date: {summary.get('extraction_date', 'Unknown')}")
            print(f"   - Files processed: {summary.get('total_files_processed', 0)}")
            print(f"   - Sheets extracted: {summary.get('total_sheets_extracted', 0)}")
            print(f"   - DNOs covered: {summary.get('dnos_covered', 0)}")
            print(f"   - UK coverage: {summary.get('uk_coverage_percent', 0):.1f}%")
            print(f"   - MPAN codes: {summary.get('covered_mpan_codes', [])}")

        # Find all CSV files in the directory
        csv_files = list(dir_path.glob("*.csv"))
        print(f"   📊 Found {len(csv_files)} CSV files")

        for csv_file in csv_files:
            print(f"   📄 Analyzing: {csv_file.name}")
            analysis = analyze_csv_file(csv_file)
            all_files.append(analysis)

            if "error" not in analysis and analysis["mpan_id"]:
                mpan_data[analysis["mpan_id"]].append(analysis)

    # Create summary by MPAN ID
    print("\n📊 SUMMARY BY DISTRIBUTION ID/MPAN ID")
    print("=" * 60)

    for mpan_id in sorted(mpan_data.keys()):
        files = mpan_data[mpan_id]
        dno_name = MPAN_TO_DNO.get(mpan_id, f"Unknown MPAN {mpan_id}")

        print(f"\n🏢 MPAN {mpan_id}: {dno_name}")
        print(f"   📁 Files: {len(files)}")

        # Get years covered
        years = sorted([f["year"] for f in files if f["year"]])
        if years:
            print(
                f"   📅 Years: {min(years)} - {max(years)} ({len(set(years))} unique years)"
            )

        # Get total rows
        total_rows = sum([f["rows"] for f in files])
        print(f"   📈 Total data rows: {total_rows:,}")

        # Show file details
        for file_info in files:
            print(f"   📄 {file_info['filename']}")
            print(
                f"      Year: {file_info['year']}, Rows: {file_info['rows']:,}, Columns: {file_info['column_count']}"
            )

    # Create coverage summary
    print(f"\n📈 OVERALL COVERAGE SUMMARY")
    print("=" * 60)
    print(f"Total MPAN areas with data: {len(mpan_data)}/14 UK DNOs")
    print(f"Coverage percentage: {len(mpan_data)/14*100:.1f}%")

    covered_mpans = sorted(mpan_data.keys())
    missing_mpans = [mpan for mpan in range(10, 26) if mpan not in covered_mpans]

    print(f"\n✅ Covered MPAN areas: {covered_mpans}")
    for mpan_id in covered_mpans:
        print(f"   MPAN {mpan_id}: {MPAN_TO_DNO.get(mpan_id, 'Unknown')}")

    print(f"\n❌ Missing MPAN areas: {missing_mpans}")
    for mpan_id in missing_mpans:
        print(f"   MPAN {mpan_id}: {MPAN_TO_DNO.get(mpan_id, 'Unknown')}")

    # Save detailed analysis
    analysis_result = {
        "analysis_date": datetime.now().isoformat(),
        "mpan_data": dict(mpan_data),
        "coverage_summary": {
            "total_mpan_areas": len(mpan_data),
            "coverage_percentage": len(mpan_data) / 14 * 100,
            "covered_mpans": covered_mpans,
            "missing_mpans": missing_mpans,
        },
        "all_files": all_files,
    }

    with open("duos_analysis_by_mpan_id.json", "w") as f:
        json.dump(analysis_result, f, indent=2, default=str)

    print(f"\n💾 Detailed analysis saved to: duos_analysis_by_mpan_id.json")

    return analysis_result


if __name__ == "__main__":
    try:
        result = analyze_all_duos_data()
        print(f"\n✅ Analysis completed successfully!")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()
