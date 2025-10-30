#!/usr/bin/env python3
"""
DNO DUoS Data Consolidator (Complete)
------------------------------------
Creates consolidated Excel spreadsheet from the enhanced DUoS data,
with separate sheets for each DNO and each year.
Includes comprehensive DNO mapping information.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd


class DNODuosConsolidator:
    def __init__(self):
        """Initialize the consolidator with DNO mapping data."""
        # Complete DNO mapping as provided
        self.dno_mapping = [
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

        # Create a DataFrame from the mapping for easier manipulation
        self.dno_mapping_df = pd.DataFrame(self.dno_mapping)

        # Create lookup dictionary for mapping old names to standardized names
        self.name_mapping = {
            # NGED (National Grid) mappings with all possible variations
            "National Grid East Midlands": "NGED-EM",
            "National Grid West Midlands": "NGED-WM",
            "National Grid South Wales": "NGED-SWales",
            "National Grid South West": "NGED-SW",
            "NGED East Midlands": "NGED-EM",
            "NGED West Midlands": "NGED-WM",
            "NGED South Wales": "NGED-SWales",
            "NGED South West": "NGED-SW",
            "EMID": "NGED-EM",
            "WMID": "NGED-WM",
            "SWALES": "NGED-SWales",
            "SWEST": "NGED-SW",
            # UKPN mappings with all possible variations
            "UKPN Eastern": "UKPN-EPN",
            "UKPN London": "UKPN-LPN",
            "UKPN South Eastern": "UKPN-SPN",
            "UK Power Networks Eastern": "UKPN-EPN",
            "UK Power Networks London": "UKPN-LPN",
            "UK Power Networks South Eastern": "UKPN-SPN",
            "EPN": "UKPN-EPN",
            "LPN": "UKPN-LPN",
            "SPN": "UKPN-SPN",
            # Other DNO mappings
            "SSEN Hydro": "SSE-SHEPD",
            "SSEN Southern": "SSE-SEPD",
            "Northern Powergrid Northeast": "NPg-NE",
            "Northern Powergrid Yorkshire": "NPg-Y",
            "SP Distribution": "SP-Distribution",
            "SP Manweb": "SP-Manweb",
            "Electricity North West": "ENWL",  # Using consistent short form
        }

    def create_consolidated_spreadsheet(self):
        """Create a consolidated spreadsheet with separate sheets for each DNO and year."""
        print("🚀 DNO DUoS DATA CONSOLIDATOR (COMPLETE)")
        print("=======================================")

        # Input and output paths
        input_path = "duos_outputs2/duos_all_bands_enhanced_v3.csv"
        output_dir = "duos_outputs2"
        output_path = os.path.join(
            output_dir, "DNO_DUoS_All_Data_Consolidated_Complete.xlsx"
        )

        # Load the enhanced data
        print(f"📊 Loading data from: {input_path}")
        try:
            df = pd.read_csv(input_path)
            print(f"✅ Loaded {len(df)} records")
        except Exception as e:
            print(f"❌ Error loading data: {str(e)}")
            return

        # Standardize DNO names using our mapping
        print("🔄 Standardizing DNO names and adding metadata")
        df = self.standardize_dno_data(df)

        # Create Excel writer
        print(f"📝 Creating Excel file: {output_path}")
        try:
            with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
                # Create DNO reference sheet
                print("📋 Creating DNO Reference sheet")
                self.create_dno_reference_sheet(writer)

                # Create summary sheet
                print("📋 Creating Summary sheet")
                self.create_summary_sheet(df, writer)

                # Create sheets by DNO
                print("📋 Creating DNO-specific sheets")
                self.create_dno_sheets(df, writer)

                # Create sheets by year
                print("📋 Creating year-specific sheets")
                self.create_year_sheets(df, writer)

                # Create sheet with all data
                print("📋 Creating All Data sheet")
                self.create_all_data_sheet(df, writer)

                # Format the Excel file
                self.format_excel(writer)

            print(f"✅ Excel file created successfully: {output_path}")
        except Exception as e:
            print(f"❌ Error creating Excel file: {str(e)}")
            return

    def standardize_dno_data(self, df):
        """Standardize DNO names and add metadata from the mapping."""
        # Make a copy to avoid modifying the original
        df_enhanced = df.copy()

        # Store original DNO names
        df_enhanced["original_dno_name"] = df_enhanced["dno_name"]

        # First map to standardized dno_key format
        df_enhanced["dno_key"] = df_enhanced["dno_name"].map(self.name_mapping)

        # Keep track of any unmapped DNOs
        unmapped = df_enhanced[df_enhanced["dno_key"].isna()]["dno_name"].unique()
        if len(unmapped) > 0:
            print("⚠️ Warning: Found unmapped DNO names:", unmapped)

        # For any unmapped names, try to infer from original name
        df_enhanced.loc[df_enhanced["dno_key"].isna(), "dno_key"] = (
            df_enhanced.loc[df_enhanced["dno_key"].isna(), "dno_name"]
            .str.replace("National Grid", "NGED")
            .str.replace("UK Power Networks", "UKPN")
        )

        # Map DNO keys to full metadata from our mapping DataFrame
        meta_df = pd.merge(
            df_enhanced,
            self.dno_mapping_df,
            on="dno_key",
            how="left",
            suffixes=("_orig", ""),
        )

        # Convert MPAN code to integer
        meta_df["mpan_code"] = pd.to_numeric(
            meta_df["mpan_code"], errors="coerce"
        ).astype("Int64")

        # Define which columns we want to keep from the metadata
        meta_columns = [
            "dno_key",
            "dno_name",
            "short_code",
            "market_participant_id",
            "gsp_group_id",
            "gsp_group_name",
        ]

        for col in meta_columns:
            mapping_dict = dict(
                zip(self.dno_mapping_df["mpan_code"], self.dno_mapping_df[col])
            )
            df_enhanced[col] = df_enhanced["mpan_code"].map(mapping_dict)

        return df_enhanced

    def create_dno_reference_sheet(self, writer):
        """Create a reference sheet with all DNO information."""
        # Add headers
        headers = [
            "MPAN Code",
            "DNO Key",
            "DNO Name",
            "Short Code",
            "Market Participant ID",
            "GSP Group ID",
            "GSP Group Name",
        ]

        # Create DataFrame from mapping
        dno_ref_df = self.dno_mapping_df.copy()
        dno_ref_df.columns = headers

        # Write to Excel with a nice header
        dno_ref_df.to_excel(writer, sheet_name="DNO Reference", index=False)

        # Get the worksheet
        worksheet = writer.sheets["DNO Reference"]

        # Add a title
        title_format = writer.book.add_format(
            {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
        )
        worksheet.merge_range("A1:G1", "DNO Reference Information", title_format)

        # Move the actual data down one row
        dno_ref_df.to_excel(writer, sheet_name="DNO Reference", startrow=1, index=False)

    def create_summary_sheet(self, df, writer):
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
        dno_summary.to_excel(writer, sheet_name="Summary", startrow=1, index=False)

        # Add a title
        worksheet = writer.sheets["Summary"]
        title_format = writer.book.add_format(
            {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
        )
        worksheet.merge_range("A1:D1", "DNO DUoS Data Summary", title_format)

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
            writer, sheet_name="Summary", startrow=len(dno_summary) + 5, index=False
        )

        # Add a subtitle
        subtitle_format = writer.book.add_format(
            {"bold": True, "font_size": 12, "align": "center", "valign": "vcenter"}
        )
        worksheet.merge_range(
            f"A{len(dno_summary) + 4}:H{len(dno_summary) + 4}",
            "Rate Band Statistics",
            subtitle_format,
        )

    def create_dno_sheets(self, df, writer):
        """Create separate sheets for each DNO."""
        # Group by standardized DNO name
        dno_groups = df.groupby("dno_name")

        for dno_name, dno_df in dno_groups:
            # Create a clean sheet name (Excel sheet names limited to 31 chars)
            sheet_name = self.get_safe_sheet_name(dno_name)

            # Sort by year and band
            dno_df = dno_df.sort_values(["year", "band"])

            # Select and reorder columns for better readability
            selected_cols = [
                "year",
                "mpan_code",
                "dno_key",
                "short_code",
                "band",
                "time_period",
                "min_rate",
                "max_rate",
                "mean_rate",
                "median_rate",
                "gsp_group_id",
                "gsp_group_name",
                "count",
                "unit",
                "file_path",
            ]

            # Filter to only include columns that exist in the DataFrame
            selected_cols = [col for col in selected_cols if col in dno_df.columns]
            dno_display_df = dno_df[selected_cols].copy()

            # Rename columns for better readability
            column_renames = {
                "year": "Year",
                "mpan_code": "MPAN Code",
                "dno_key": "DNO Key",
                "short_code": "Short Code",
                "band": "Band",
                "time_period": "Time Period",
                "min_rate": "Min Rate (p/kWh)",
                "max_rate": "Max Rate (p/kWh)",
                "mean_rate": "Mean Rate (p/kWh)",
                "median_rate": "Median Rate (p/kWh)",
                "gsp_group_id": "GSP Group ID",
                "gsp_group_name": "GSP Group Name",
                "count": "Count",
                "unit": "Unit",
                "file_path": "File Path",
            }
            dno_display_df.rename(columns=column_renames, inplace=True)

            # Write to Excel with a title
            dno_display_df.to_excel(
                writer, sheet_name=sheet_name, startrow=1, index=False
            )

            # Add a title
            worksheet = writer.sheets[sheet_name]
            title_format = writer.book.add_format(
                {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
            )

            # Merge cells across all columns
            last_col = chr(64 + len(dno_display_df.columns))
            worksheet.merge_range(
                f"A1:{last_col}1", f"DUoS Rates: {dno_name}", title_format
            )

    def create_year_sheets(self, df, writer):
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
            selected_cols = [
                "dno_name",
                "mpan_code",
                "dno_key",
                "short_code",
                "band",
                "time_period",
                "min_rate",
                "max_rate",
                "mean_rate",
                "median_rate",
                "gsp_group_id",
                "gsp_group_name",
                "count",
                "unit",
                "file_path",
            ]

            # Filter to only include columns that exist in the DataFrame
            selected_cols = [col for col in selected_cols if col in year_df.columns]
            year_display_df = year_df[selected_cols].copy()

            # Rename columns for better readability
            column_renames = {
                "dno_name": "DNO Name",
                "mpan_code": "MPAN Code",
                "dno_key": "DNO Key",
                "short_code": "Short Code",
                "band": "Band",
                "time_period": "Time Period",
                "min_rate": "Min Rate (p/kWh)",
                "max_rate": "Max Rate (p/kWh)",
                "mean_rate": "Mean Rate (p/kWh)",
                "median_rate": "Median Rate (p/kWh)",
                "gsp_group_id": "GSP Group ID",
                "gsp_group_name": "GSP Group Name",
                "count": "Count",
                "unit": "Unit",
                "file_path": "File Path",
            }
            year_display_df.rename(columns=column_renames, inplace=True)

            # Write to Excel with a title
            year_display_df.to_excel(
                writer, sheet_name=sheet_name, startrow=1, index=False
            )

            # Add a title
            worksheet = writer.sheets[sheet_name]
            title_format = writer.book.add_format(
                {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
            )

            # Merge cells across all columns
            last_col = chr(64 + len(year_display_df.columns))
            worksheet.merge_range(
                f"A1:{last_col}1", f"DUoS Rates for Year {year}", title_format
            )

    def create_all_data_sheet(self, df, writer):
        """Create a sheet with all data."""
        all_data_df = df.copy()

        # Sort by DNO, year, and band
        all_data_df = all_data_df.sort_values(["dno_name", "year", "band"])

        # Select and reorder columns for better readability
        selected_cols = [
            "dno_name",
            "dno_key",
            "mpan_code",
            "short_code",
            "year",
            "band",
            "time_period",
            "min_rate",
            "max_rate",
            "mean_rate",
            "median_rate",
            "gsp_group_id",
            "gsp_group_name",
            "count",
            "unit",
            "file_path",
        ]

        # Filter to only include columns that exist in the DataFrame
        selected_cols = [col for col in selected_cols if col in all_data_df.columns]
        all_display_df = all_data_df[selected_cols].copy()

        # Rename columns for better readability
        column_renames = {
            "dno_name": "DNO Name",
            "dno_key": "DNO Key",
            "mpan_code": "MPAN Code",
            "short_code": "Short Code",
            "year": "Year",
            "band": "Band",
            "time_period": "Time Period",
            "min_rate": "Min Rate (p/kWh)",
            "max_rate": "Max Rate (p/kWh)",
            "mean_rate": "Mean Rate (p/kWh)",
            "median_rate": "Median Rate (p/kWh)",
            "gsp_group_id": "GSP Group ID",
            "gsp_group_name": "GSP Group Name",
            "count": "Count",
            "unit": "Unit",
            "file_path": "File Path",
        }
        all_display_df.rename(columns=column_renames, inplace=True)

        # Write to Excel with a title
        all_display_df.to_excel(writer, sheet_name="All Data", startrow=1, index=False)

        # Add a title
        worksheet = writer.sheets["All Data"]
        title_format = writer.book.add_format(
            {"bold": True, "font_size": 14, "align": "center", "valign": "vcenter"}
        )

        # Merge cells across all columns
        last_col = chr(64 + len(all_display_df.columns))
        worksheet.merge_range(f"A1:{last_col}1", "All DNO DUoS Rate Data", title_format)

    def format_excel(self, writer):
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

            # Manually format the header row
            worksheet.set_row(1, 20, header_format)

            # Add autofilter (starting from row 1 which is our header row after the title)
            first_row = 1
            if worksheet.name == "DNO Reference":
                first_row = 2  # Because we have an extra title row in this sheet

            # Get the dimensions of the worksheet
            (max_row, max_col) = worksheet.dim_rowmax, worksheet.dim_colmax

            # Apply the autofilter
            worksheet.autofilter(first_row, 0, first_row, max_col)

    def get_safe_sheet_name(self, name):
        """Convert a DNO name to a valid Excel sheet name (31 chars max)."""
        # Map long DNO names to shorter versions
        name_map = {
            "National Grid Electricity Distribution – East Midlands (EMID)": "NGED-East Midlands",
            "National Grid Electricity Distribution – West Midlands (WMID)": "NGED-West Midlands",
            "National Grid Electricity Distribution – South Wales (SWALES)": "NGED-South Wales",
            "National Grid Electricity Distribution – South West (SWEST)": "NGED-South West",
            "Scottish Hydro Electric Power Distribution (SHEPD)": "SSE-SHEPD",
            "Southern Electric Power Distribution (SEPD)": "SSE-SEPD",
            "UK Power Networks (Eastern)": "UKPN-Eastern",
            "UK Power Networks (London)": "UKPN-London",
            "UK Power Networks (South Eastern)": "UKPN-South Eastern",
            "Northern Powergrid (North East)": "NPg-North East",
            "Northern Powergrid (Yorkshire)": "NPg-Yorkshire",
            "SP Energy Networks (SPD)": "SP-Distribution",
            "SP Energy Networks (SPM)": "SP-Manweb",
        }

        # Use the map if available
        if name in name_map:
            return name_map[name]

        # Otherwise truncate to 31 chars
        return name[:31]


if __name__ == "__main__":
    consolidator = DNODuosConsolidator()
    consolidator.create_consolidated_spreadsheet()
