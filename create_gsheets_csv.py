#!/usr/bin/env python3
"""
Google Sheets Optimized CSV Creator
----------------------------------
Creates CSV files specifically optimized for Google Sheets from the DNO DUoS data.
"""

import csv
import os
from datetime import datetime

import pandas as pd


def create_gsheets_csv(input_path, output_dir=None):
    """Create Google Sheets optimized CSV files from the DUoS data."""
    print("\n🚀 GOOGLE SHEETS OPTIMIZED CSV CREATOR")
    print("====================================")

    # Determine output directory
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(input_path), "gsheets_csv")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load the enhanced data
    print(f"📊 Loading data from: {input_path}")
    try:
        df = pd.read_csv(input_path)
        print(f"✅ Loaded {len(df)} records")
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return

    # Get timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save optimized CSVs
    try:
        # 1. Save complete data
        all_data_path = os.path.join(output_dir, f"DNO_DUoS_All_Data_{timestamp}.csv")
        df.to_csv(all_data_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"📄 Created All Data CSV: {all_data_path}")

        # 2. Create DNO reference data
        dno_mapping = [
            {
                "mpan_code": 12,
                "dno_key": "UKPN-LPN",
                "dno_name": "UK Power Networks (London)",
                "short_code": "LPN",
                "market_participant_id": "LOND",
                "gsp_group_id": "C",
                "gsp_group_name": "London",
            },
            {
                "mpan_code": 10,
                "dno_key": "UKPN-EPN",
                "dno_name": "UK Power Networks (Eastern)",
                "short_code": "EPN",
                "market_participant_id": "EELC",
                "gsp_group_id": "A",
                "gsp_group_name": "Eastern",
            },
            {
                "mpan_code": 19,
                "dno_key": "UKPN-SPN",
                "dno_name": "UK Power Networks (South Eastern)",
                "short_code": "SPN",
                "market_participant_id": "SEEB",
                "gsp_group_id": "J",
                "gsp_group_name": "South Eastern",
            },
            {
                "mpan_code": 16,
                "dno_key": "ENWL",
                "dno_name": "Electricity North West",
                "short_code": "ENWL",
                "market_participant_id": "NORW",
                "gsp_group_id": "G",
                "gsp_group_name": "North West",
            },
            {
                "mpan_code": 15,
                "dno_key": "NPg-NE",
                "dno_name": "Northern Powergrid (North East)",
                "short_code": "NE",
                "market_participant_id": "NEEB",
                "gsp_group_id": "F",
                "gsp_group_name": "North East",
            },
            {
                "mpan_code": 23,
                "dno_key": "NPg-Y",
                "dno_name": "Northern Powergrid (Yorkshire)",
                "short_code": "Y",
                "market_participant_id": "YELG",
                "gsp_group_id": "M",
                "gsp_group_name": "Yorkshire",
            },
            {
                "mpan_code": 18,
                "dno_key": "SP-Distribution",
                "dno_name": "SP Energy Networks (SPD)",
                "short_code": "SPD",
                "market_participant_id": "SPOW",
                "gsp_group_id": "N",
                "gsp_group_name": "South Scotland",
            },
            {
                "mpan_code": 13,
                "dno_key": "SP-Manweb",
                "dno_name": "SP Energy Networks (SPM)",
                "short_code": "SPM",
                "market_participant_id": "MANW",
                "gsp_group_id": "D",
                "gsp_group_name": "Merseyside & North Wales",
            },
            {
                "mpan_code": 17,
                "dno_key": "SSE-SHEPD",
                "dno_name": "Scottish Hydro Electric Power Distribution (SHEPD)",
                "short_code": "SHEPD",
                "market_participant_id": "HYDE",
                "gsp_group_id": "P",
                "gsp_group_name": "North Scotland",
            },
            {
                "mpan_code": 20,
                "dno_key": "SSE-SEPD",
                "dno_name": "Southern Electric Power Distribution (SEPD)",
                "short_code": "SEPD",
                "market_participant_id": "SOUT",
                "gsp_group_id": "H",
                "gsp_group_name": "Southern",
            },
            {
                "mpan_code": 14,
                "dno_key": "NGED-WM",
                "dno_name": "National Grid Electricity Distribution – West Midlands (WMID)",
                "short_code": "WMID",
                "market_participant_id": "MIDE",
                "gsp_group_id": "E",
                "gsp_group_name": "West Midlands",
            },
            {
                "mpan_code": 11,
                "dno_key": "NGED-EM",
                "dno_name": "National Grid Electricity Distribution – East Midlands (EMID)",
                "short_code": "EMID",
                "market_participant_id": "EMEB",
                "gsp_group_id": "B",
                "gsp_group_name": "East Midlands",
            },
            {
                "mpan_code": 22,
                "dno_key": "NGED-SW",
                "dno_name": "National Grid Electricity Distribution – South West (SWEST)",
                "short_code": "SWEST",
                "market_participant_id": "SWEB",
                "gsp_group_id": "L",
                "gsp_group_name": "South Western",
            },
            {
                "mpan_code": 21,
                "dno_key": "NGED-SWales",
                "dno_name": "National Grid Electricity Distribution – South Wales (SWALES)",
                "short_code": "SWALES",
                "market_participant_id": "SWAE",
                "gsp_group_id": "K",
                "gsp_group_name": "South Wales",
            },
        ]
        dno_ref_df = pd.DataFrame(dno_mapping)

        # Rename columns
        dno_ref_df.columns = [
            "MPAN_Code",
            "DNO_Key",
            "DNO_Name",
            "Short_Code",
            "Market_Participant_ID",
            "GSP_Group_ID",
            "GSP_Group_Name",
        ]

        # Save reference data
        ref_path = os.path.join(output_dir, f"DNO_Reference_{timestamp}.csv")
        dno_ref_df.to_csv(ref_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"📄 Created DNO Reference CSV: {ref_path}")

        # 3. Create summary statistics by DNO
        dno_summary = (
            df.groupby("dno_name")
            .agg(
                {
                    "file_path": "nunique",
                    "year": lambda x: sorted(x.unique()),
                    "band": lambda x: x.value_counts().to_dict(),
                }
            )
            .reset_index()
        )

        dno_summary.columns = [
            "DNO_Name",
            "Files_Count",
            "Years_Covered",
            "Band_Distribution",
        ]

        # Convert complex objects to strings for GSheets compatibility
        dno_summary["Years_Covered"] = dno_summary["Years_Covered"].apply(
            lambda x: ", ".join(map(str, x))
        )
        dno_summary["Band_Distribution"] = dno_summary["Band_Distribution"].apply(
            lambda x: f"RED: {x.get('RED', 0)}, AMBER: {x.get('AMBER', 0)}, GREEN: {x.get('GREEN', 0)}"
        )

        # Save summary data
        summary_path = os.path.join(output_dir, f"DNO_DUoS_Summary_{timestamp}.csv")
        dno_summary.to_csv(summary_path, index=False, quoting=csv.QUOTE_MINIMAL)
        print(f"📄 Created Summary CSV: {summary_path}")

        # 4. Create separate CSVs by year
        years = sorted(df["year"].unique())
        year_dir = os.path.join(output_dir, "by_year")
        os.makedirs(year_dir, exist_ok=True)

        for year in years:
            year_df = df[df["year"] == year].copy()
            year_path = os.path.join(year_dir, f"Year_{year}_{timestamp}.csv")
            year_df.to_csv(year_path, index=False, quoting=csv.QUOTE_MINIMAL)

        print(f"📄 Created {len(years)} year-specific CSV files in {year_dir}")

        # 5. Create separate CSVs by DNO
        dno_names = sorted(df["dno_name"].unique())
        dno_dir = os.path.join(output_dir, "by_dno")
        os.makedirs(dno_dir, exist_ok=True)

        for dno_name in dno_names:
            dno_df = df[df["dno_name"] == dno_name].copy()

            # Create safe filename
            safe_name = (
                dno_name.replace(" ", "_")
                .replace("/", "_")
                .replace("(", "")
                .replace(")", "")
                .replace("-", "_")
            )
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")

            dno_path = os.path.join(dno_dir, f"{safe_name}_{timestamp}.csv")
            dno_df.to_csv(dno_path, index=False, quoting=csv.QUOTE_MINIMAL)

        print(f"📄 Created {len(dno_names)} DNO-specific CSV files in {dno_dir}")

        print("\n✅ All Google Sheets optimized CSV files created successfully!")
        print("\n📋 INSTRUCTIONS:")
        print("   1. Go to Google Drive and create a new folder")
        print("   2. Upload the CSV files to this folder")
        print("   3. When opening, Google will automatically use Sheets to open them")
        print("   4. For the main data, use the file:")
        print(f"      {os.path.basename(all_data_path)}")

    except Exception as e:
        print(f"❌ Error creating CSV files: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    else:
        input_path = "duos_outputs2/duos_all_bands_enhanced_v3.csv"

    output_dir = None
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]

    create_gsheets_csv(input_path, output_dir)
