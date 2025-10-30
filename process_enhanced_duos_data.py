#!/usr/bin/env python3
"""
Enhanced DNO DUoS Data Processor
--------------------------------
This script processes the enhanced DNO data folder and outputs DUoS rates
in a standardized format matching duos_combined_analysis/duos_all_bands_combined.csv
"""

import glob
import json
import os
import re
import warnings
from datetime import datetime

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)


class EnhancedDUoSProcessor:
    def __init__(self, input_dir, output_dir):
        """Initialize the processor with directories and settings."""
        self.input_dir = input_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Define DNO mapping
        self.dno_mapping = {
            "EMEB": {"name": "National Grid East Midlands", "mpan": 12},
            "MIDE": {"name": "National Grid East Midlands", "mpan": 12},
            "WMID": {"name": "National Grid West Midlands", "mpan": 14},
            "SWAE": {"name": "National Grid South Wales", "mpan": 21},
            "SWEB": {"name": "National Grid South West", "mpan": 22},
            "SPD": {"name": "SP Distribution", "mpan": 16},
            "SPM": {"name": "SP Manweb", "mpan": 13},
            "SHEPD": {"name": "SSEN Hydro", "mpan": 17},
            "SEPD": {"name": "SSEN Southern", "mpan": 20},
            "EPN": {"name": "UKPN Eastern", "mpan": 10},
            "LPN": {"name": "UKPN London", "mpan": 11},
            "SPN": {"name": "UKPN South Eastern", "mpan": 19},
            "NPgN": {"name": "Northern Powergrid Northeast", "mpan": 23},
            "NPgY": {"name": "Northern Powergrid Yorkshire", "mpan": 15},
            "ENWL": {"name": "Electricity North West", "mpan": 16},
            "eastern": {"name": "UKPN Eastern", "mpan": 10},
            "london": {"name": "UKPN London", "mpan": 11},
            "south-eastern": {"name": "UKPN South Eastern", "mpan": 19},
            "Northeast": {"name": "Northern Powergrid Northeast", "mpan": 23},
            "Yorkshire": {"name": "Northern Powergrid Yorkshire", "mpan": 15},
        }

        # List of sheet names that typically contain charge data
        self.rate_sheet_names = [
            "Annex 1 LV, HV and UMS charges",
            "Annex 1 LV and HV charges",
            "Annex 1",
            "All UMS Tariffs",
            "LV Sub Tariffs",
            "LV Tariffs",
            "HV Tariffs",
            "Standing charge factors",
            "Table 1",
            "Schedule of Charges",
            "Schedule of charges",
        ]

        self.results = []

    def identify_dno_and_year(self, file_path):
        """Identify DNO and year from the file name."""
        file_name = os.path.basename(file_path).lower()

        # Try to identify the DNO
        dno_name = "Unknown"
        mpan_code = None

        for key, value in self.dno_mapping.items():
            if key.lower() in file_name:
                dno_name = value["name"]
                mpan_code = value["mpan"]
                break

        # Try to identify the year
        year_match = re.search(r"20(\d{2})", file_name)
        year = int("20" + year_match.group(1)) if year_match else None

        return dno_name, mpan_code, year

    def extract_rates_from_excel(self, file_path, dno_name, mpan_code, year):
        """Extract DUoS rates from Excel file."""
        try:
            # Load the Excel file
            try:
                excel_file = pd.ExcelFile(file_path)
            except Exception as e:
                print(f"⚠️ Could not open {os.path.basename(file_path)}: {str(e)}")
                return []

            sheet_rates = []

            # Try all potential sheet names
            for sheet_name in excel_file.sheet_names:
                # Skip sheets that likely don't contain rate data
                if any(
                    skip in sheet_name.lower()
                    for skip in ["contents", "index", "glossary", "notes", "legal"]
                ):
                    continue

                # Prioritize sheets that likely contain rate data
                priority = 1
                for rate_sheet in self.rate_sheet_names:
                    if rate_sheet.lower() in sheet_name.lower():
                        priority = 0
                        break

                try:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)

                    # Look for columns containing rate information
                    for col in df.columns:
                        col_str = str(col).lower()
                        if isinstance(col, str) and (
                            "p/kwh" in col_str or "p/kw" in col_str
                        ):
                            # Look for band indicators in the same row or column
                            band_data = self.identify_bands_and_extract_rates(df, col)
                            if band_data:
                                for band, rates in band_data.items():
                                    if rates and len(rates) > 0:
                                        rates = [
                                            r
                                            for r in rates
                                            if isinstance(r, (int, float))
                                            or (
                                                isinstance(r, str)
                                                and r.replace(".", "", 1)
                                                .replace("-", "", 1)
                                                .isdigit()
                                            )
                                        ]
                                        if rates:
                                            rates = [float(r) for r in rates]
                                            sheet_rates.append(
                                                {
                                                    "file_path": file_path,
                                                    "dno_name": dno_name,
                                                    "mpan_code": mpan_code,
                                                    "year": year,
                                                    "band": band,
                                                    "sheet_name": sheet_name,
                                                    "min_rate": min(rates),
                                                    "max_rate": max(rates),
                                                    "mean_rate": sum(rates)
                                                    / len(rates),
                                                    "median_rate": sorted(rates)[
                                                        len(rates) // 2
                                                    ],
                                                    "count": len(rates),
                                                }
                                            )
                                break
                except Exception as e:
                    print(
                        f"⚠️ Error processing sheet '{sheet_name}' in {os.path.basename(file_path)}: {str(e)}"
                    )
                    continue

            return sheet_rates
        except Exception as e:
            print(f"⚠️ Error processing {os.path.basename(file_path)}: {str(e)}")
            return []

    def identify_bands_and_extract_rates(self, df, rate_column):
        """Identify Red, Amber, Green bands and extract their rates."""
        band_data = {"RED": [], "AMBER": [], "GREEN": []}

        # Convert dataframe to string for easier text searching
        df_str = df.astype(str)

        # Look for explicit band indicators
        band_indicators = {
            "RED": ["red", "red band", "red time", "peak"],
            "AMBER": ["amber", "amber band", "amber time", "shoulder"],
            "GREEN": ["green", "green band", "green time", "off-peak"],
        }

        # Search the dataframe for band indicators
        for band, indicators in band_indicators.items():
            for indicator in indicators:
                # Check column headers
                for col in df.columns:
                    if isinstance(col, str) and indicator in col.lower():
                        values = df[col].dropna().tolist()
                        if values:
                            band_data[band].extend(
                                [
                                    v
                                    for v in values
                                    if str(v)
                                    .replace(".", "", 1)
                                    .replace("-", "", 1)
                                    .isdigit()
                                ]
                            )

                # If no explicit headers, look in the dataframe content
                if not band_data[band]:
                    for i, row in df_str.iterrows():
                        for j, cell in enumerate(row):
                            if isinstance(cell, str) and indicator in cell.lower():
                                # Check adjacent cells for numeric values
                                for offset in range(1, 4):
                                    if i + offset < len(df):
                                        val = df.iloc[i + offset, j]
                                        if isinstance(val, (int, float)) or (
                                            isinstance(val, str)
                                            and val.replace(".", "", 1)
                                            .replace("-", "", 1)
                                            .isdigit()
                                        ):
                                            band_data[band].append(float(val))
                                    if j + offset < len(df.columns):
                                        val = df.iloc[i, j + offset]
                                        if isinstance(val, (int, float)) or (
                                            isinstance(val, str)
                                            and str(val)
                                            .replace(".", "", 1)
                                            .replace("-", "", 1)
                                            .isdigit()
                                        ):
                                            band_data[band].append(float(val))

        # If we found any band data, return it
        if any(len(rates) > 0 for rates in band_data.values()):
            return band_data

        # If no explicit band indicators were found, try pattern-based extraction
        # This is a heuristic approach based on common file structures

        # First, check if we have a table with unit rates (p/kWh) by time period
        unit_rate_cols = [
            col
            for col in df.columns
            if isinstance(col, str) and "unit" in col.lower() and "rate" in col.lower()
        ]

        if unit_rate_cols:
            for col in unit_rate_cols:
                values = df[col].dropna().tolist()
                if len(values) >= 3:
                    # Assume Red, Amber, Green order if 3 or more values
                    band_data["RED"] = (
                        [float(values[0])]
                        if str(values[0])
                        .replace(".", "", 1)
                        .replace("-", "", 1)
                        .isdigit()
                        else []
                    )
                    band_data["AMBER"] = (
                        [float(values[1])]
                        if str(values[1])
                        .replace(".", "", 1)
                        .replace("-", "", 1)
                        .isdigit()
                        else []
                    )
                    band_data["GREEN"] = (
                        [float(values[2])]
                        if str(values[2])
                        .replace(".", "", 1)
                        .replace("-", "", 1)
                        .isdigit()
                        else []
                    )

        # If we still don't have band data, look for rate columns by position
        if all(len(rates) == 0 for rates in band_data.values()):
            numeric_cols = [
                col for col in df.columns if df[col].dtype in ["float64", "int64"]
            ]

            if len(numeric_cols) >= 3:
                # Extract values from these columns
                for i, col in enumerate(numeric_cols[:3]):
                    values = df[col].dropna().tolist()
                    if values and len(values) > 0:
                        if i == 0:
                            band_data["RED"] = [
                                float(v) for v in values if isinstance(v, (int, float))
                            ]
                        elif i == 1:
                            band_data["AMBER"] = [
                                float(v) for v in values if isinstance(v, (int, float))
                            ]
                        elif i == 2:
                            band_data["GREEN"] = [
                                float(v) for v in values if isinstance(v, (int, float))
                            ]

        return band_data

    def process_excel_files(self):
        """Process all Excel files in the input directory."""
        print(f"🔍 Searching for Excel files in: {self.input_dir}")

        # Find all Excel files
        excel_files = []
        for extension in ["*.xlsx", "*.xls"]:
            excel_files.extend(glob.glob(os.path.join(self.input_dir, extension)))

        print(f"📊 Found {len(excel_files)} Excel files to process")

        # Process each Excel file
        for i, file_path in enumerate(excel_files):
            if i % 10 == 0:
                print(
                    f"⏳ Processing file {i+1}/{len(excel_files)}: {os.path.basename(file_path)}"
                )

            dno_name, mpan_code, year = self.identify_dno_and_year(file_path)

            if year:
                file_results = self.extract_rates_from_excel(
                    file_path, dno_name, mpan_code, year
                )
                self.results.extend(file_results)

        print(
            f"✅ Processed {len(excel_files)} files and found {len(self.results)} rate entries"
        )

    def save_results(self):
        """Save the results to CSV and JSON files."""
        if not self.results:
            print("⚠️ No results to save")
            return

        # Convert results to DataFrame
        df = pd.DataFrame(self.results)

        # Create a relative path for display in the CSV
        df["file_path"] = df["file_path"].apply(
            lambda x: os.path.relpath(x, os.path.dirname(self.input_dir))
        )

        # Save as CSV
        csv_path = os.path.join(self.output_dir, "duos_all_bands_enhanced.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved results to: {csv_path}")

        # Save as JSON
        json_path = os.path.join(self.output_dir, "duos_bands_enhanced.json")
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ Saved results to: {json_path}")

        # Generate a summary report
        self.generate_summary_report(df)

    def generate_summary_report(self, df):
        """Generate a summary report."""
        report_path = os.path.join(self.output_dir, "duos_enhanced_report.txt")

        with open(report_path, "w") as f:
            f.write(f"DUoS ENHANCED DATA ANALYSIS REPORT\n")
            f.write(f"=================================\n\n")
            f.write(
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write(f"SUMMARY STATISTICS\n")
            f.write(f"-----------------\n\n")

            # Overall statistics
            f.write(f"Total files processed: {len(df['file_path'].unique())}\n")
            f.write(f"Total rate entries found: {len(df)}\n\n")

            # DNO statistics
            f.write(f"DNO COVERAGE\n")
            f.write(f"-----------\n\n")
            dno_counts = df["dno_name"].value_counts()
            for dno, count in dno_counts.items():
                f.write(f"{dno}: {count} entries\n")

            f.write(f"\nYEAR COVERAGE\n")
            f.write(f"------------\n\n")
            year_counts = df["year"].value_counts().sort_index()
            for year, count in year_counts.items():
                f.write(f"{year}: {count} entries\n")

            f.write(f"\nBAND RATES SUMMARY\n")
            f.write(f"-----------------\n\n")

            for band in ["RED", "AMBER", "GREEN"]:
                band_df = df[df["band"] == band]
                if not band_df.empty:
                    f.write(f"{band} Band:\n")
                    f.write(f"  Minimum rate: {band_df['min_rate'].min():.4f} p/kWh\n")
                    f.write(f"  Maximum rate: {band_df['max_rate'].max():.4f} p/kWh\n")
                    f.write(
                        f"  Average mean rate: {band_df['mean_rate'].mean():.4f} p/kWh\n"
                    )
                    f.write(
                        f"  Average median rate: {band_df['median_rate'].mean():.4f} p/kWh\n\n"
                    )

            f.write(f"DNO RATE COMPARISON\n")
            f.write(f"------------------\n\n")

            for dno in df["dno_name"].unique():
                dno_df = df[df["dno_name"] == dno]
                f.write(f"{dno}:\n")

                for band in ["RED", "AMBER", "GREEN"]:
                    band_dno_df = dno_df[dno_df["band"] == band]
                    if not band_dno_df.empty:
                        f.write(
                            f"  {band} Band: {band_dno_df['mean_rate'].mean():.4f} p/kWh (avg)\n"
                        )

                f.write("\n")

        print(f"✅ Generated summary report: {report_path}")

    def run(self):
        """Run the full processing pipeline."""
        print("🚀 ENHANCED DUoS DATA PROCESSOR")
        print("===============================")

        self.process_excel_files()
        self.save_results()

        print("\n🎊 PROCESSING COMPLETE!")


if __name__ == "__main__":
    input_dir = "dno_data_enhanced"
    output_dir = "duos_outputs2"

    processor = EnhancedDUoSProcessor(input_dir, output_dir)
    processor.run()
