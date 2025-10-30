#!/usr/bin/env python3
"""
DNO DUoS Data CSV Generator
--------------------------
Creates simple CSV files from the enhanced DUoS data,
with separate files for DNO reference, summary, and all data.
"""

import os
from datetime import datetime

import numpy as np
import pandas as pd


class DNODuosCSVGenerator:
    def __init__(self):
        """Initialize the generator with DNO mapping data."""
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
            "National Grid East Midlands": "National Grid Electricity Distribution – East Midlands (EMID)",
            "National Grid West Midlands": "National Grid Electricity Distribution – West Midlands (WMID)",
            "National Grid South Wales": "National Grid Electricity Distribution – South Wales (SWALES)",
            "National Grid South West": "National Grid Electricity Distribution – South West (SWEST)",
            "SSEN Hydro": "Scottish Hydro Electric Power Distribution (SHEPD)",
            "SSEN Southern": "Southern Electric Power Distribution (SEPD)",
            "UKPN Eastern": "UK Power Networks (Eastern)",
            "UKPN London": "UK Power Networks (London)",
            "UKPN South Eastern": "UK Power Networks (South Eastern)",
            "Northern Powergrid Northeast": "Northern Powergrid (North East)",
            "Northern Powergrid Yorkshire": "Northern Powergrid (Yorkshire)",
            "SP Distribution": "SP Energy Networks (SPD)",
            "SP Manweb": "SP Energy Networks (SPM)",
            "Electricity North West": "Electricity North West",  # Already matches
        }

    def generate_csv_files(self):
        """Generate multiple CSV files for the DNO DUoS data."""
        print("🚀 DNO DUoS DATA CSV GENERATOR")
        print("============================")

        # Input and output paths
        input_path = "duos_outputs2/duos_all_bands_enhanced_v3.csv"
        output_dir = "duos_outputs2"

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

        # Standardize DNO names using our mapping
        print("🔄 Standardizing DNO names and adding metadata")
        df = self.standardize_dno_data(df)

        # Generate CSV files
        try:
            # 1. DNO Reference CSV
            self.generate_dno_reference_csv(output_dir)

            # 2. By DNO CSVs
            self.generate_dno_csvs(df, output_dir)

            # 3. By Year CSVs
            self.generate_year_csvs(df, output_dir)

            # 4. All Data CSV
            self.generate_all_data_csv(df, output_dir)

            # 5. Summary CSV
            self.generate_summary_csv(df, output_dir)

            print("✅ All CSV files generated successfully!")

        except Exception as e:
            print(f"❌ Error generating CSV files: {str(e)}")
            import traceback

            traceback.print_exc()

    def standardize_dno_data(self, df):
        """Standardize DNO names and add metadata from the mapping."""
        # Make a copy to avoid modifying the original
        df_enhanced = df.copy()

        # Standardize DNO names using our mapping dictionary
        df_enhanced["original_dno_name"] = df_enhanced["dno_name"]
        df_enhanced["dno_name"] = (
            df_enhanced["dno_name"]
            .map(self.name_mapping)
            .fillna(df_enhanced["dno_name"])
        )

        # Add DNO metadata based on mpan_code
        df_enhanced["mpan_code"] = (
            df_enhanced["mpan_code"].astype(float).astype("Int64")
        )  # Ensure integer type

        # Create a dictionary for each metadata column
        meta_columns = [
            "dno_key",
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

    def generate_dno_reference_csv(self, output_dir):
        """Generate CSV with all DNO reference information."""
        # Create reference dataframe
        dno_ref_df = self.dno_mapping_df.copy()

        # Add headers
        dno_ref_df.columns = [
            "MPAN_Code",
            "DNO_Key",
            "DNO_Name",
            "Short_Code",
            "Market_Participant_ID",
            "GSP_Group_ID",
            "GSP_Group_Name",
        ]

        # Save to CSV
        output_path = os.path.join(output_dir, "DNO_Reference.csv")
        dno_ref_df.to_csv(output_path, index=False)
        print(f"📄 Created DNO reference file: {output_path}")

    def generate_dno_csvs(self, df, output_dir):
        """Generate separate CSVs for each DNO."""
        # Create DNO output directory
        dno_dir = os.path.join(output_dir, "by_dno")
        os.makedirs(dno_dir, exist_ok=True)

        # Group by standardized DNO name
        dno_groups = df.groupby("dno_name")

        for dno_name, dno_df in dno_groups:
            # Create a clean filename
            safe_name = self.get_safe_filename(dno_name)
            filename = f"{safe_name}.csv"
            output_path = os.path.join(dno_dir, filename)

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
                "mpan_code": "MPAN_Code",
                "dno_key": "DNO_Key",
                "short_code": "Short_Code",
                "band": "Band",
                "time_period": "Time_Period",
                "min_rate": "Min_Rate_p_kWh",
                "max_rate": "Max_Rate_p_kWh",
                "mean_rate": "Mean_Rate_p_kWh",
                "median_rate": "Median_Rate_p_kWh",
                "gsp_group_id": "GSP_Group_ID",
                "gsp_group_name": "GSP_Group_Name",
                "count": "Count",
                "unit": "Unit",
                "file_path": "File_Path",
            }
            dno_display_df.rename(columns=column_renames, inplace=True)

            # Save to CSV
            dno_display_df.to_csv(output_path, index=False)

        print(f"📄 Created {len(dno_groups)} DNO-specific CSV files in {dno_dir}")

    def generate_year_csvs(self, df, output_dir):
        """Generate separate CSVs for each year."""
        # Create year output directory
        year_dir = os.path.join(output_dir, "by_year")
        os.makedirs(year_dir, exist_ok=True)

        # Get unique years
        years = sorted(df["year"].unique())

        for year in years:
            year_df = df[df["year"] == year].copy()

            # Create filename
            filename = f"Year_{year}.csv"
            output_path = os.path.join(year_dir, filename)

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
                "dno_name": "DNO_Name",
                "mpan_code": "MPAN_Code",
                "dno_key": "DNO_Key",
                "short_code": "Short_Code",
                "band": "Band",
                "time_period": "Time_Period",
                "min_rate": "Min_Rate_p_kWh",
                "max_rate": "Max_Rate_p_kWh",
                "mean_rate": "Mean_Rate_p_kWh",
                "median_rate": "Median_Rate_p_kWh",
                "gsp_group_id": "GSP_Group_ID",
                "gsp_group_name": "GSP_Group_Name",
                "count": "Count",
                "unit": "Unit",
                "file_path": "File_Path",
            }
            year_display_df.rename(columns=column_renames, inplace=True)

            # Save to CSV
            year_display_df.to_csv(output_path, index=False)

        print(f"📄 Created {len(years)} year-specific CSV files in {year_dir}")

    def generate_all_data_csv(self, df, output_dir):
        """Generate a single CSV with all data."""
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
            "dno_name": "DNO_Name",
            "dno_key": "DNO_Key",
            "mpan_code": "MPAN_Code",
            "short_code": "Short_Code",
            "year": "Year",
            "band": "Band",
            "time_period": "Time_Period",
            "min_rate": "Min_Rate_p_kWh",
            "max_rate": "Max_Rate_p_kWh",
            "mean_rate": "Mean_Rate_p_kWh",
            "median_rate": "Median_Rate_p_kWh",
            "gsp_group_id": "GSP_Group_ID",
            "gsp_group_name": "GSP_Group_Name",
            "count": "Count",
            "unit": "Unit",
            "file_path": "File_Path",
        }
        all_display_df.rename(columns=column_renames, inplace=True)

        # Save to CSV
        output_path = os.path.join(output_dir, "DNO_DUoS_All_Data.csv")
        all_display_df.to_csv(output_path, index=False)
        print(f"📄 Created all data file: {output_path}")

    def generate_summary_csv(self, df, output_dir):
        """Generate a summary CSV with key statistics."""
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
            "DNO_Name",
            "Files_Count",
            "Years_Covered",
            "Band_Distribution",
        ]

        # Format the years and band distributions
        dno_summary["Years_Covered"] = dno_summary["Years_Covered"].apply(
            lambda x: ", ".join(map(str, x))
        )
        dno_summary["Band_Distribution"] = dno_summary["Band_Distribution"].apply(
            lambda x: f"RED: {x.get('RED', 0)}, AMBER: {x.get('AMBER', 0)}, GREEN: {x.get('GREEN', 0)}"
        )

        # Save to CSV
        output_path = os.path.join(output_dir, "DNO_DUoS_Summary.csv")
        dno_summary.to_csv(output_path, index=False)
        print(f"📄 Created summary file: {output_path}")

        # Generate band statistics
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
            "Min_Rate_Min",
            "Min_Rate_Avg",
            "Max_Rate_Max",
            "Max_Rate_Avg",
            "Avg_Mean_Rate",
            "Avg_Median_Rate",
            "Total_Count",
        ]

        # Save to CSV
        band_stats_path = os.path.join(output_dir, "DNO_DUoS_Band_Stats.csv")
        band_stats.to_csv(band_stats_path, index=False)
        print(f"📄 Created band statistics file: {band_stats_path}")

    def get_safe_filename(self, name):
        """Convert a DNO name to a valid filename."""
        # Map long DNO names to shorter versions
        name_map = {
            "National Grid Electricity Distribution – East Midlands (EMID)": "NGED-East_Midlands",
            "National Grid Electricity Distribution – West Midlands (WMID)": "NGED-West_Midlands",
            "National Grid Electricity Distribution – South Wales (SWALES)": "NGED-South_Wales",
            "National Grid Electricity Distribution – South West (SWEST)": "NGED-South_West",
            "Scottish Hydro Electric Power Distribution (SHEPD)": "SSE-SHEPD",
            "Southern Electric Power Distribution (SEPD)": "SSE-SEPD",
            "UK Power Networks (Eastern)": "UKPN-Eastern",
            "UK Power Networks (London)": "UKPN-London",
            "UK Power Networks (South Eastern)": "UKPN-South_Eastern",
            "Northern Powergrid (North East)": "NPg-North_East",
            "Northern Powergrid (Yorkshire)": "NPg-Yorkshire",
            "SP Energy Networks (SPD)": "SP-Distribution",
            "SP Energy Networks (SPM)": "SP-Manweb",
        }

        # Use the map if available
        if name in name_map:
            return name_map[name]

        # Otherwise make a safe filename
        safe_name = (
            name.replace(" ", "_")
            .replace("/", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "_")
        )
        return safe_name


if __name__ == "__main__":
    generator = DNODuosCSVGenerator()
    generator.generate_csv_files()
