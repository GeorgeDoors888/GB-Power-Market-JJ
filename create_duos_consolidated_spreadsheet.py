#!/usr/bin/env python3
"""
DNO DUoS Data Consolidator
--------------------------
Creates consolidated Excel spreadsheet from the enhanced DUoS data,
with separate sheets for each DNO and each year.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd


def create_consolidated_spreadsheet():
    """Create a consolidated spreadsheet with separate sheets for each DNO and year."""
    print("🚀 DNO DUoS DATA CONSOLIDATOR")
    print("============================")

    # Input and output paths
    input_path = "duos_outputs2/duos_all_bands_enhanced_v3.csv"
    output_dir = "duos_outputs2"
    output_path = os.path.join(output_dir, "DNO_DUoS_All_Data_Consolidated.xlsx")

    # Load the enhanced data
    print(f"📊 Loading data from: {input_path}")
    try:
        df = pd.read_csv(input_path)
        print(f"✅ Loaded {len(df)} records")
    except Exception as e:
        print(f"❌ Error loading data: {str(e)}")
        return

    # Create Excel writer
    print(f"📝 Creating Excel file: {output_path}")
    try:
        with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
            # Create summary sheet
            print("📋 Creating Summary sheet")
            create_summary_sheet(df, writer)

            # Create sheets by DNO
            print("📋 Creating DNO-specific sheets")
            create_dno_sheets(df, writer)

            # Create sheets by year
            print("📋 Creating year-specific sheets")
            create_year_sheets(df, writer)

            # Create sheet with all data
            print("📋 Creating All Data sheet")
            create_all_data_sheet(df, writer)

            # Format the Excel file
            format_excel(writer)

        print(f"✅ Excel file created successfully: {output_path}")
    except Exception as e:
        print(f"❌ Error creating Excel file: {str(e)}")
        return


def create_summary_sheet(df, writer):
    """Create a summary sheet with key statistics."""
    # Create summary dataframes
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
        "DNO Name",
        "Files Count",
        "Years Covered",
        "Band Distribution",
    ]

    # Format the years and band distributions
    dno_summary["Years Covered"] = dno_summary["Years Covered"].apply(
        lambda x: ", ".join(map(str, x))
    )
    dno_summary["Band Distribution"] = dno_summary["Band Distribution"].apply(
        lambda x: f"RED: {x.get('RED', 0)}, AMBER: {x.get('AMBER', 0)}, GREEN: {x.get('GREEN', 0)}"
    )

    # Write to Excel
    dno_summary.to_excel(writer, sheet_name="Summary", index=False)

    # Get rate statistics by band
    band_stats = (
        df.groupby("band")
        .agg(
            {
                "min_rate": ["min", "mean"],
                "max_rate": ["max", "mean"],
                "mean_rate": "mean",
                "median_rate": "mean",
                "count": "sum",
            }
        )
        .reset_index()
    )

    # Flatten multi-level columns
    band_stats.columns = [
        "Band",
        "Min Rate (Min)",
        "Min Rate (Avg)",
        "Max Rate (Max)",
        "Max Rate (Avg)",
        "Avg Mean Rate",
        "Avg Median Rate",
        "Total Count",
    ]

    # Write band stats below the DNO summary
    band_stats.to_excel(
        writer, sheet_name="Summary", startrow=len(dno_summary) + 3, index=False
    )


def create_dno_sheets(df, writer):
    """Create separate sheets for each DNO."""
    # Get unique DNOs
    dnos = sorted(df["dno_name"].unique())

    for dno in dnos:
        dno_df = df[df["dno_name"] == dno].copy()

        # Create a clean sheet name (Excel sheet names limited to 31 chars)
        sheet_name = dno[:30]

        # Sort by year and band
        dno_df = dno_df.sort_values(["year", "band"])

        # Select and reorder columns for better readability
        dno_df = dno_df[
            [
                "year",
                "mpan_code",
                "band",
                "time_period",
                "min_rate",
                "max_rate",
                "mean_rate",
                "median_rate",
                "sheet_name",
                "count",
                "unit",
                "file_path",
            ]
        ]

        # Rename columns for better readability
        dno_df.columns = [
            "Year",
            "MPAN Code",
            "Band",
            "Time Period",
            "Min Rate (p/kWh)",
            "Max Rate (p/kWh)",
            "Mean Rate (p/kWh)",
            "Median Rate (p/kWh)",
            "Source Sheet",
            "Count",
            "Unit",
            "File Path",
        ]

        # Write to Excel
        dno_df.to_excel(writer, sheet_name=sheet_name, index=False)


def create_year_sheets(df, writer):
    """Create separate sheets for each year."""
    # Get unique years
    years = sorted(df["year"].unique())

    for year in years:
        year_df = df[df["year"] == year].copy()

        # Create sheet name
        sheet_name = f"Year {year}"

        # Sort by DNO and band
        year_df = year_df.sort_values(["dno_name", "band"])

        # Select and reorder columns for better readability
        year_df = year_df[
            [
                "dno_name",
                "mpan_code",
                "band",
                "time_period",
                "min_rate",
                "max_rate",
                "mean_rate",
                "median_rate",
                "sheet_name",
                "count",
                "unit",
                "file_path",
            ]
        ]

        # Rename columns for better readability
        year_df.columns = [
            "DNO Name",
            "MPAN Code",
            "Band",
            "Time Period",
            "Min Rate (p/kWh)",
            "Max Rate (p/kWh)",
            "Mean Rate (p/kWh)",
            "Median Rate (p/kWh)",
            "Source Sheet",
            "Count",
            "Unit",
            "File Path",
        ]

        # Write to Excel
        year_df.to_excel(writer, sheet_name=sheet_name, index=False)


def create_all_data_sheet(df, writer):
    """Create a sheet with all data."""
    all_data_df = df.copy()

    # Sort by DNO, year, and band
    all_data_df = all_data_df.sort_values(["dno_name", "year", "band"])

    # Select and reorder columns for better readability
    all_data_df = all_data_df[
        [
            "dno_name",
            "year",
            "mpan_code",
            "band",
            "time_period",
            "min_rate",
            "max_rate",
            "mean_rate",
            "median_rate",
            "sheet_name",
            "count",
            "unit",
            "file_path",
        ]
    ]

    # Rename columns for better readability
    all_data_df.columns = [
        "DNO Name",
        "Year",
        "MPAN Code",
        "Band",
        "Time Period",
        "Min Rate (p/kWh)",
        "Max Rate (p/kWh)",
        "Mean Rate (p/kWh)",
        "Median Rate (p/kWh)",
        "Source Sheet",
        "Count",
        "Unit",
        "File Path",
    ]

    # Write to Excel
    all_data_df.to_excel(writer, sheet_name="All Data", index=False)


def format_excel(writer):
    """Apply formatting to the Excel workbook."""
    workbook = writer.book

    # Define formats
    header_format = workbook.add_format(
        {
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#D9E1F2",
            "border": 1,
        }
    )

    # Apply formatting to each worksheet
    for worksheet in writer.sheets.values():
        # Set column widths
        worksheet.set_column("A:Z", 15)

        # Manually format the header row without using worksheet.table
        worksheet.set_row(0, 20, header_format)


if __name__ == "__main__":
    create_consolidated_spreadsheet()
