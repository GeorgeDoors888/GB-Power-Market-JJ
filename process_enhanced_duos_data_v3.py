#!/usr/bin/env python3
"""
Enhanced DNO DUoS Data Processor v3
-----------------------------------
This script processes the enhanced DNO data folder and outputs DUoS rates
in a standardized format with band time periods and unit rates.
Includes improved extraction of time bands and rates.
"""

import glob
import json
import os
import re
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)


class EnhancedDUoSProcessorV3:
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
            "Time bands",
            "Time Bands",
            "UoS Tariff",
            "Red Amber Green",
        ]

        # Common patterns for time bands
        self.time_band_patterns = {
            "RED": [
                r"red\s*(?:band|time)?:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"weekday\s*peak:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"peak\s*(?:time|period|hours)?:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"red\s*time\s*band.*?(\d{1,2}[:.]\d{2}).*?(\d{1,2}[:.]\d{2})",
            ],
            "AMBER": [
                r"amber\s*(?:band|time)?:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"shoulder:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"mid-?peak:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"amber\s*time\s*band.*?(\d{1,2}[:.]\d{2}).*?(\d{1,2}[:.]\d{2})",
            ],
            "GREEN": [
                r"green\s*(?:band|time)?:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"off-?peak:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"night:?\s*([\d:]+)\s*(?:to|-)?\s*([\d:]+)",
                r"green\s*time\s*band.*?(\d{1,2}[:.]\d{2}).*?(\d{1,2}[:.]\d{2})",
            ],
        }

        # Known typical time bands for DNOs (default fallback)
        self.default_time_bands = {
            # Most common UK DNO standard time bands
            "RED": "16:00-19:00 (weekdays)",
            "AMBER": "07:00-16:00, 19:00-23:00 (weekdays)",
            "GREEN": "23:00-07:00 (all days), all day (weekends)",
        }

        # Rate keywords to look for
        self.rate_keywords = [
            "p/kwh",
            "pkwh",
            "p/kw",
            "unit rate",
            "unit charge",
            "unit rates",
            "unit charges",
            "£/kwh",
            "p/kva",
            "pence/kwh",
            "pence/kw",
            "p per kwh",
            "pence per kwh",
            "p / kwh",
            "pence / kwh",
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

    def extract_time_bands_from_sheets(self, excel_file):
        """Extract time bands by scanning through all sheets."""
        time_bands = {"RED": None, "AMBER": None, "GREEN": None}

        # Try to find dedicated time band sheets first
        time_band_sheet_names = [
            "Time Bands",
            "Time bands",
            "Time Band",
            "Time band",
            "Red Amber Green",
        ]

        for sheet_name in excel_file.sheet_names:
            if any(tb in sheet_name for tb in time_band_sheet_names):
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    bands = self.extract_time_bands(df)

                    # Update any bands we found
                    for band, period in bands.items():
                        if period:
                            time_bands[band] = period
                except:
                    continue

        # Fall back to defaults if necessary
        for band in time_bands:
            if not time_bands[band]:
                time_bands[band] = self.default_time_bands[band] + " (default)"

        return time_bands

    def extract_time_bands(self, df):
        """Extract time bands from the dataframe."""
        time_bands = {"RED": None, "AMBER": None, "GREEN": None}

        # Convert dataframe to string for easier text searching
        df_str = df.astype(str)

        # Search for time band patterns
        for band, patterns in self.time_band_patterns.items():
            for pattern in patterns:
                # Search across the entire dataframe
                for _, row in df_str.iterrows():
                    for cell in row:
                        if not isinstance(cell, str):
                            continue
                        match = re.search(pattern, cell.lower())
                        if match:
                            start_time, end_time = match.groups()
                            # Standardize time format (replace . with : if needed)
                            start_time = start_time.replace(".", ":")
                            end_time = end_time.replace(".", ":")
                            time_bands[band] = f"{start_time}-{end_time}"
                            break
                    if time_bands[band]:
                        break
                if time_bands[band]:
                    break

        # Check for time bands in column headers
        for col in df.columns:
            if not isinstance(col, str):
                continue
            col_lower = col.lower()

            for band in ["RED", "AMBER", "GREEN"]:
                band_lower = band.lower()
                if band_lower in col_lower:
                    # Look for time patterns like 16:00-19:00 in the column name
                    time_match = re.search(
                        r"(\d{1,2}[:.]\d{2})[-\s]+(\d{1,2}[:.]\d{2})", col_lower
                    )
                    if time_match:
                        start_time, end_time = time_match.groups()
                        # Standardize time format (replace . with : if needed)
                        start_time = start_time.replace(".", ":")
                        end_time = end_time.replace(".", ":")
                        time_bands[band] = f"{start_time}-{end_time}"

        return time_bands

    def extract_rates_from_excel(self, file_path, dno_name, mpan_code, year):
        """Extract DUoS rates from Excel file."""
        try:
            # Load the Excel file
            try:
                excel_file = pd.ExcelFile(file_path)
            except Exception as e:
                print(f"⚠️ Could not open {os.path.basename(file_path)}: {str(e)}")
                return []

            # Extract time bands from dedicated sheets if available
            time_bands = self.extract_time_bands_from_sheets(excel_file)

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

                    # First try to locate keyword markers in the dataframe
                    rate_locations = self.find_rate_keywords(df)

                    if rate_locations:
                        band_data = self.extract_rates_from_locations(
                            df, rate_locations
                        )
                    else:
                        # Look for explicit rate columns and their band indicators
                        band_data = self.identify_bands_and_extract_rates(df)

                    # If we found rates, add them to our results with the time bands
                    if band_data:
                        for band, rates in band_data.items():
                            if rates and len(rates) > 0:
                                # Filter and convert rates to float
                                valid_rates = []
                                for r in rates:
                                    try:
                                        if isinstance(r, (int, float)):
                                            valid_rates.append(float(r))
                                        elif (
                                            isinstance(r, str)
                                            and r.replace(".", "", 1)
                                            .replace("-", "", 1)
                                            .isdigit()
                                        ):
                                            valid_rates.append(float(r))
                                    except:
                                        pass

                                if valid_rates:
                                    # Create result entry
                                    sheet_rates.append(
                                        {
                                            "file_path": file_path,
                                            "dno_name": dno_name,
                                            "mpan_code": mpan_code,
                                            "year": year,
                                            "band": band,
                                            "sheet_name": sheet_name,
                                            "time_period": time_bands[band],
                                            "min_rate": min(valid_rates),
                                            "max_rate": max(valid_rates),
                                            "mean_rate": sum(valid_rates)
                                            / len(valid_rates),
                                            "median_rate": sorted(valid_rates)[
                                                len(valid_rates) // 2
                                            ],
                                            "count": len(valid_rates),
                                            "unit": "p/kWh",  # Standard unit
                                        }
                                    )

                except Exception as e:
                    print(
                        f"⚠️ Error processing sheet '{sheet_name}' in {os.path.basename(file_path)}: {str(e)}"
                    )
                    continue

            return sheet_rates
        except Exception as e:
            print(f"⚠️ Error processing {os.path.basename(file_path)}: {str(e)}")
            return []

    def find_rate_keywords(self, df):
        """Find cells containing rate keywords and return their positions."""
        rate_locations = []

        # Convert to string for text searching
        df_str = df.astype(str)

        # Search for rate keywords
        for i, row in df_str.iterrows():
            for j, cell in enumerate(row):
                if isinstance(cell, str):
                    cell_lower = cell.lower()
                    if any(keyword in cell_lower for keyword in self.rate_keywords):
                        rate_locations.append((i, j))

        return rate_locations

    def extract_rates_from_locations(self, df, rate_locations):
        """Extract rates based on the locations of rate keywords."""
        band_data = {"RED": [], "AMBER": [], "GREEN": []}

        for i, j in rate_locations:
            # Look for band indicators and rates nearby
            search_range = 5  # Look up to 5 cells away

            # First check if there are band indicators nearby
            found_bands = set()
            for di in range(-search_range, search_range + 1):
                for dj in range(-search_range, search_range + 1):
                    if 0 <= i + di < len(df) and 0 <= j + dj < len(df.columns):
                        cell_val = str(df.iloc[i + di, j + dj]).lower()
                        if "red" in cell_val:
                            found_bands.add("RED")
                        elif "amber" in cell_val:
                            found_bands.add("AMBER")
                        elif "green" in cell_val:
                            found_bands.add("GREEN")

            # If we found band indicators, look for rates nearby
            if found_bands:
                # Check all cells around the rate keyword
                for di in range(-search_range, search_range + 1):
                    for dj in range(-search_range, search_range + 1):
                        if 0 <= i + di < len(df) and 0 <= j + dj < len(df.columns):
                            try:
                                cell_val = df.iloc[i + di, j + dj]
                                # Check if it's a potential rate value
                                if (
                                    isinstance(cell_val, (int, float))
                                    and 0 < cell_val < 50
                                ):  # Reasonable p/kWh values
                                    # Determine which band it belongs to
                                    for band_idx, band in enumerate(
                                        sorted(found_bands)
                                    ):
                                        if (
                                            di == band_idx
                                        ):  # Simple heuristic - assign by row offset
                                            band_data[band].append(float(cell_val))
                            except:
                                pass

        return band_data

    def identify_bands_and_extract_rates(self, df):
        """Identify Red, Amber, Green bands and extract their rates."""
        band_data = {"RED": [], "AMBER": [], "GREEN": []}

        # Convert dataframe to string for easier text searching
        df_str = df.astype(str)

        # Look for explicit band indicators
        band_indicators = {
            "RED": ["red", "red band", "red time", "peak", "weekday peak"],
            "AMBER": [
                "amber",
                "amber band",
                "amber time",
                "shoulder",
                "mid-peak",
                "mid peak",
            ],
            "GREEN": [
                "green",
                "green band",
                "green time",
                "off-peak",
                "off peak",
                "night",
            ],
        }

        # Search the dataframe for band indicators
        for band, indicators in band_indicators.items():
            for indicator in indicators:
                # Check column headers
                for col in df.columns:
                    if isinstance(col, str) and indicator in col.lower():
                        # Look for numeric values in this column
                        for i, val in enumerate(df[col]):
                            try:
                                if isinstance(val, (int, float)) and 0 < val < 50:
                                    band_data[band].append(float(val))
                                elif (
                                    isinstance(val, str)
                                    and val.replace(".", "", 1)
                                    .replace("-", "", 1)
                                    .isdigit()
                                ):
                                    float_val = float(val)
                                    if 0 < float_val < 50:  # Reasonable range for p/kWh
                                        band_data[band].append(float_val)
                            except:
                                pass

                # Look in the dataframe content
                for i, row in df_str.iterrows():
                    for j, cell in enumerate(row):
                        if isinstance(cell, str) and indicator in cell.lower():
                            # Check adjacent cells for numeric values
                            for offset in range(1, 4):
                                try:
                                    if i + offset < len(df):
                                        val = df.iloc[i + offset, j]
                                        if (
                                            isinstance(val, (int, float))
                                            and 0 < val < 50
                                        ):
                                            band_data[band].append(float(val))
                                        elif (
                                            isinstance(val, str)
                                            and val.replace(".", "", 1)
                                            .replace("-", "", 1)
                                            .isdigit()
                                        ):
                                            float_val = float(val)
                                            if 0 < float_val < 50:
                                                band_data[band].append(float_val)

                                    if j + offset < len(df.columns):
                                        val = df.iloc[i, j + offset]
                                        if (
                                            isinstance(val, (int, float))
                                            and 0 < val < 50
                                        ):
                                            band_data[band].append(float(val))
                                        elif (
                                            isinstance(val, str)
                                            and val.replace(".", "", 1)
                                            .replace("-", "", 1)
                                            .isdigit()
                                        ):
                                            float_val = float(val)
                                            if 0 < float_val < 50:
                                                band_data[band].append(float_val)
                                except:
                                    pass

        # If we found any band data, return it
        if any(len(rates) > 0 for rates in band_data.values()):
            return band_data

        # If no explicit band indicators were found, try pattern-based extraction
        # First, check if we have a table with unit rates (p/kWh) by time period
        unit_rate_cols = []
        for col in df.columns:
            if isinstance(col, str) and (
                "unit" in col.lower() and "rate" in col.lower()
            ):
                unit_rate_cols.append(col)

        if unit_rate_cols:
            for col in unit_rate_cols:
                values = []
                for val in df[col].dropna():
                    try:
                        if isinstance(val, (int, float)) and 0 < val < 50:
                            values.append(float(val))
                        elif (
                            isinstance(val, str)
                            and val.replace(".", "", 1).replace("-", "", 1).isdigit()
                        ):
                            float_val = float(val)
                            if 0 < float_val < 50:
                                values.append(float_val)
                    except:
                        pass

                if len(values) >= 3:
                    # Assume Red, Amber, Green order if 3 or more values
                    band_data["RED"] = [values[0]] if values else []
                    band_data["AMBER"] = [values[1]] if len(values) > 1 else []
                    band_data["GREEN"] = [values[2]] if len(values) > 2 else []

        # If we still don't have band data, look for rate columns by position
        if all(len(rates) == 0 for rates in band_data.values()):
            # Get columns with primarily numeric data
            numeric_cols = []
            for col in df.columns:
                numeric_count = 0
                total_count = 0
                for val in df[col].dropna():
                    total_count += 1
                    try:
                        if isinstance(val, (int, float)) or (
                            isinstance(val, str)
                            and val.replace(".", "", 1).replace("-", "", 1).isdigit()
                        ):
                            float_val = float(val) if isinstance(val, str) else val
                            if 0 < float_val < 50:  # Reasonable range for p/kWh
                                numeric_count += 1
                    except:
                        pass

                if (
                    total_count > 0 and numeric_count / total_count > 0.5
                ):  # Over 50% numeric
                    numeric_cols.append(col)

            if len(numeric_cols) >= 3:
                # Extract values from these columns
                for i, col in enumerate(numeric_cols[:3]):
                    values = []
                    for val in df[col].dropna():
                        try:
                            if isinstance(val, (int, float)) and 0 < val < 50:
                                values.append(float(val))
                            elif (
                                isinstance(val, str)
                                and val.replace(".", "", 1)
                                .replace("-", "", 1)
                                .isdigit()
                            ):
                                float_val = float(val)
                                if 0 < float_val < 50:
                                    values.append(float_val)
                        except:
                            pass

                    if i == 0:
                        band_data["RED"] = values
                    elif i == 1:
                        band_data["AMBER"] = values
                    elif i == 2:
                        band_data["GREEN"] = values

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
            if i % 5 == 0:
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
        csv_path = os.path.join(self.output_dir, "duos_all_bands_enhanced_v3.csv")
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved results to: {csv_path}")

        # Save as JSON
        json_path = os.path.join(self.output_dir, "duos_bands_enhanced_v3.json")
        with open(json_path, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"✅ Saved results to: {json_path}")

        # Generate a summary report
        self.generate_summary_report(df)

    def generate_summary_report(self, df):
        """Generate a summary report."""
        report_path = os.path.join(self.output_dir, "duos_enhanced_report_v3.txt")

        with open(report_path, "w") as f:
            f.write(f"DUoS ENHANCED DATA ANALYSIS REPORT V3\n")
            f.write(f"===================================\n\n")
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
                if not band_df.empty and band_df["mean_rate"].notna().any():
                    f.write(f"{band} Band:\n")

                    # Sample time periods
                    time_samples = band_df["time_period"].dropna().unique()[:3]
                    if len(time_samples) > 0:
                        f.write(f"  Time periods (sample): {', '.join(time_samples)}\n")

                    # Rate statistics if available
                    if band_df["min_rate"].notna().any():
                        f.write(
                            f"  Minimum rate: {band_df['min_rate'].min(skipna=True):.4f} p/kWh\n"
                        )
                        f.write(
                            f"  Maximum rate: {band_df['max_rate'].max(skipna=True):.4f} p/kWh\n"
                        )
                        f.write(
                            f"  Average mean rate: {band_df['mean_rate'].mean(skipna=True):.4f} p/kWh\n"
                        )
                        f.write(
                            f"  Average median rate: {band_df['median_rate'].mean(skipna=True):.4f} p/kWh\n\n"
                        )

            f.write(f"DNO RATE COMPARISON\n")
            f.write(f"------------------\n\n")

            for dno in df["dno_name"].unique():
                dno_df = df[df["dno_name"] == dno]
                f.write(f"{dno}:\n")

                for band in ["RED", "AMBER", "GREEN"]:
                    band_dno_df = dno_df[dno_df["band"] == band]
                    if not band_dno_df.empty and band_dno_df["mean_rate"].notna().any():
                        avg_rate = band_dno_df["mean_rate"].mean(skipna=True)
                        f.write(f"  {band} Band: {avg_rate:.4f} p/kWh (avg)\n")

                        # Sample time period for this DNO and band
                        time_sample = (
                            band_dno_df["time_period"].dropna().iloc[0]
                            if not band_dno_df["time_period"].isna().all()
                            else "Not available"
                        )
                        f.write(f"    Time period: {time_sample}\n")

                f.write("\n")

        print(f"✅ Generated summary report: {report_path}")

    def run(self):
        """Run the full processing pipeline."""
        print("🚀 ENHANCED DUoS DATA PROCESSOR V3")
        print("=================================")

        self.process_excel_files()
        self.save_results()

        print("\n🎊 PROCESSING COMPLETE!")


if __name__ == "__main__":
    input_dir = "dno_data_enhanced"
    output_dir = "duos_outputs2"

    processor = EnhancedDUoSProcessorV3(input_dir, output_dir)
    processor.run()
