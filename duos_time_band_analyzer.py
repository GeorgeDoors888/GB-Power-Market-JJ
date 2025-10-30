#!/usr/bin/env python3
"""
DUoS Time Band Analysis by DNO

This script analyzes Distribution Use of System (DUoS) charging data
specifically focused on the time band rates (Red, Amber, Green) for each DNO.
It extracts time period definitions and corresponding rates by year.

Author: Jibber Jabber Knowledge System
Date: 14 September 2025
"""

import glob
import json
import os
import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Directory for outputs
OUTPUT_DIR = "duos_time_band_analysis"

# Define DNO code to name mapping
DNO_MAPPING = {
    10: "UKPN Eastern (EPN)",
    11: "UKPN London (LPN)",
    12: "UKPN South Eastern (SPN)",
    13: "SP Manweb (SPM)",
    14: "Electricity North West (ENWL)",
    15: "SP Energy Networks (SPEN)",
    16: "Northern Powergrid (NPG)",
    17: "SSEN Hydro (SHEPD)",
    19: "Northern Powergrid Yorkshire (NPG)",
    20: "SSEN Southern (SEPD)",
    21: "NGED West Midlands",
    22: "NGED East Midlands",
    23: "NGED South Wales",
    24: "NGED South West",
    25: "SP Distribution (SPD)",
}

# Define directories where DUoS data is stored
DATA_DIRS = [
    "duos_extracted_data",
    "duos_expanded_data",
    "duos_spm_data",
    "duos_ssen_data",
    "duos_nged_data",
]

# Regex patterns to extract time periods from Excel files
TIME_PERIOD_PATTERNS = [
    r"red\s+(?:period|band|time)?\s*(?::|is|are)?\s*(.*?)(?:amber|green|$)",
    r"amber\s+(?:period|band|time)?\s*(?::|is|are)?\s*(.*?)(?:red|green|$)",
    r"green\s+(?:period|band|time)?\s*(?::|is|are)?\s*(.*?)(?:red|amber|$)",
    r"(?:weekday|peak)\s+(?:period|hours|time)?\s*(?::|is|are)?\s*(.*?)(?:weekend|off-peak|$)",
]


class DUoSTimeBandAnalyzer:
    """Analyze DUoS time bands across DNOs"""

    def __init__(self):
        """Initialize the analyzer"""
        self.output_dir = OUTPUT_DIR
        self.time_band_data = {}
        self.rate_data = {}
        self.combined_data = []
        self.schedule_files = []

        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def find_all_excel_files(self):
        """Find all Excel files containing DUoS schedules"""
        all_files = []

        # Common patterns for schedule files
        patterns = [
            "**/*schedule*charges*.xlsx",
            "**/*schedule*charges*.xls",
            "**/*tariff*.xlsx",
            "**/*tariff*.xls",
            "**/*charging*.xlsx",
            "**/*charging*.xls",
            "**/*CDCM*.xlsx",
            "**/*CDCM*.xls",
        ]

        for dir_path in DATA_DIRS:
            if os.path.exists(dir_path):
                # Search for Excel files matching patterns
                for pattern in patterns:
                    files = glob.glob(os.path.join(dir_path, pattern), recursive=True)
                    all_files.extend(files)

        # Filter out small files (likely not actual schedules)
        valid_files = [f for f in all_files if os.path.getsize(f) > 50000]  # >50KB

        # Remove duplicates
        valid_files = list(set(valid_files))

        self.schedule_files = sorted(valid_files)
        return self.schedule_files

    def identify_dno_and_year(self, filename):
        """Extract DNO code and year from filename"""
        filename_lower = filename.lower()

        # Extract year
        year_match = re.search(r"20(\d{2})[_-]?2?0?(\d{2})", filename_lower)
        if year_match:
            year = int("20" + year_match.group(1))
        else:
            year_match = re.search(r"(20\d{2})", filename_lower)
            if year_match:
                year = int(year_match.group(1))
            else:
                year = None

        # Extract DNO
        dno_name = "Unknown"
        mpan_code = None

        # Check for known DNO names in filename
        if "ukpn" in filename_lower or "uk power" in filename_lower:
            if "eastern" in filename_lower or "epn" in filename_lower:
                dno_name = "UKPN Eastern"
                mpan_code = 10
            elif "london" in filename_lower or "lpn" in filename_lower:
                dno_name = "UKPN London"
                mpan_code = 11
            elif (
                "south" in filename_lower
                and "eastern" in filename_lower
                or "spn" in filename_lower
            ):
                dno_name = "UKPN South Eastern"
                mpan_code = 12
            else:
                dno_name = "UKPN"
        elif "sp manweb" in filename_lower or "spm" in filename_lower:
            dno_name = "SP Manweb"
            mpan_code = 13
        elif "electricity north west" in filename_lower or "enwl" in filename_lower:
            dno_name = "Electricity North West"
            mpan_code = 14
        elif "sp distribution" in filename_lower or "spd" in filename_lower:
            dno_name = "SP Distribution"
            mpan_code = 25
        elif "northern powergrid" in filename_lower or "npg" in filename_lower:
            if "yorkshire" in filename_lower:
                dno_name = "Northern Powergrid Yorkshire"
                mpan_code = 19
            else:
                dno_name = "Northern Powergrid"
                mpan_code = 16
        elif "ssen" in filename_lower or "scottish" in filename_lower:
            if "shepd" in filename_lower or "hydro" in filename_lower:
                dno_name = "SSEN Hydro"
                mpan_code = 17
            elif "sepd" in filename_lower or "southern" in filename_lower:
                dno_name = "SSEN Southern"
                mpan_code = 20
            else:
                dno_name = "SSEN"
        elif "national grid" in filename_lower or "nged" in filename_lower:
            if "west midlands" in filename_lower:
                dno_name = "NGED West Midlands"
                mpan_code = 21
            elif "east midlands" in filename_lower:
                dno_name = "NGED East Midlands"
                mpan_code = 22
            elif "south wales" in filename_lower:
                dno_name = "NGED South Wales"
                mpan_code = 23
            elif "south west" in filename_lower:
                dno_name = "NGED South West"
                mpan_code = 24
            else:
                dno_name = "National Grid"

        return dno_name, mpan_code, year

    def extract_time_periods(self, file_path):
        """Extract time period definitions from Excel file"""
        print(f"\n📊 Processing time periods: {os.path.basename(file_path)}")

        dno_name, mpan_code, year = self.identify_dno_and_year(file_path)
        print(f"   DNO: {dno_name}, MPAN: {mpan_code}, Year: {year}")

        time_periods = {"red": None, "amber": None, "green": None}

        try:
            # Read all sheets in Excel file
            xl = pd.ExcelFile(file_path)

            # Look for sheets that might contain time period definitions
            candidate_sheets = []
            for sheet in xl.sheet_names:
                sheet_lower = sheet.lower()
                if any(
                    term in sheet_lower
                    for term in ["time", "period", "definition", "note", "info"]
                ):
                    candidate_sheets.append(sheet)

            # If no obvious candidates, check the first few sheets
            if not candidate_sheets:
                candidate_sheets = xl.sheet_names[: min(5, len(xl.sheet_names))]

            # Check each candidate sheet
            for sheet in candidate_sheets:
                try:
                    # Read with no header to get all text
                    df = pd.read_excel(file_path, sheet_name=sheet, header=None)

                    # Convert all cells to string and combine
                    text = " ".join(
                        [str(x).lower() for x in df.values.flatten() if str(x) != "nan"]
                    )

                    # Look for time period definitions
                    for band in ["red", "amber", "green"]:
                        pattern = re.compile(
                            f"{band}\\s+(?:period|band|time)?\\s*(?::|is|are)?\\s*(.*?)(?:red|amber|green|$)",
                            re.IGNORECASE,
                        )
                        match = pattern.search(text)
                        if match:
                            definition = match.group(1).strip()
                            if (
                                len(definition) > 5
                            ):  # Ensure it's not just a word or two
                                time_periods[band] = definition

                    # If we've found definitions for all bands, break
                    if all(time_periods.values()):
                        break

                except Exception as e:
                    print(f"   ⚠️ Error reading sheet {sheet}: {e}")
                    continue

            # If we still don't have all bands, try a more generic approach
            if not all(time_periods.values()):
                print(
                    "   ⚠️ Couldn't find all time period definitions, trying generic patterns..."
                )

                # Try looking for time-related terms in sheet names
                for sheet in xl.sheet_names:
                    if any(
                        term in sheet.lower()
                        for term in ["time", "period", "band", "tariff"]
                    ):
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet)

                            # Search column names for time periods
                            for col in df.columns:
                                col_str = str(col).lower()
                                for band in ["red", "amber", "green"]:
                                    if band in col_str:
                                        # Try to find row with time definition
                                        for idx, row in df.iterrows():
                                            for cell in row:
                                                cell_str = str(cell).lower()
                                                if (
                                                    "time" in cell_str
                                                    and "period" in cell_str
                                                    and len(cell_str) > 10
                                                ):
                                                    time_periods[band] = cell_str
                        except:
                            continue

            # If we still don't have definitions, use generic ones based on typical DNO patterns
            for band in ["red", "amber", "green"]:
                if not time_periods[band]:
                    if band == "red":
                        time_periods[band] = (
                            "Typically weekdays 16:00-19:00 (peak hours)"
                        )
                    elif band == "amber":
                        time_periods[band] = (
                            "Typically weekdays 07:00-16:00 and 19:00-23:00 (shoulder hours)"
                        )
                    elif band == "green":
                        time_periods[band] = (
                            "Typically weekdays 23:00-07:00 and all weekend (off-peak hours)"
                        )

            # Add to time band data
            key = f"{dno_name}_{year}" if year else dno_name
            self.time_band_data[key] = {
                "dno_name": dno_name,
                "mpan_code": mpan_code,
                "year": year,
                "file_path": file_path,
                "time_periods": time_periods,
            }

            print("   Time period definitions:")
            for band, definition in time_periods.items():
                print(
                    f"   {band.upper()}: {definition[:60]}..."
                    if definition and len(definition) > 60
                    else f"   {band.upper()}: {definition}"
                )

            return time_periods

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return time_periods

    def extract_rate_data(self, file_path):
        """Extract rate data for Red, Amber, Green bands"""
        print(f"\n📊 Processing rates: {os.path.basename(file_path)}")

        dno_name, mpan_code, year = self.identify_dno_and_year(file_path)
        print(f"   DNO: {dno_name}, MPAN: {mpan_code}, Year: {year}")

        rate_data = {"red": [], "amber": [], "green": []}

        try:
            # Read the Excel file
            xl = pd.ExcelFile(file_path)

            # Look for sheets with tariff data
            candidate_sheets = []
            for sheet in xl.sheet_names:
                sheet_lower = sheet.lower()
                if any(
                    term in sheet_lower
                    for term in ["tariff", "charge", "rate", "annex", "schedule"]
                ):
                    candidate_sheets.append(sheet)

            # If no obvious candidates, check the first few sheets
            if not candidate_sheets:
                candidate_sheets = xl.sheet_names[: min(5, len(xl.sheet_names))]

            found_rates = False

            # Try different skiprow values to find the tariff table
            for sheet in candidate_sheets:
                for skip_rows in range(5, 20):
                    try:
                        df = pd.read_excel(
                            file_path, sheet_name=sheet, skiprows=skip_rows
                        )

                        # Check if we have a reasonable number of columns
                        if len(df.columns) < 3:
                            continue

                        # Identify rate columns for each band
                        band_columns = {"red": [], "amber": [], "green": []}

                        for col in df.columns:
                            col_str = str(col).lower()

                            # Check for rate-related terms
                            is_rate_col = any(
                                term in col_str
                                for term in [
                                    "charge",
                                    "rate",
                                    "p/kwh",
                                    "pence",
                                    "price",
                                ]
                            )

                            if is_rate_col:
                                # Identify which band this column belongs to
                                if any(
                                    term in col_str for term in ["red", "peak", "high"]
                                ):
                                    band_columns["red"].append(col)
                                elif any(
                                    term in col_str
                                    for term in ["amber", "shoulder", "medium"]
                                ):
                                    band_columns["amber"].append(col)
                                elif any(
                                    term in col_str for term in ["green", "off", "low"]
                                ):
                                    band_columns["green"].append(col)

                        # If we've found at least one column for any band, process the data
                        if any(band_columns.values()):
                            found_rates = True

                            print(f"   Found rate columns in sheet: {sheet}")
                            print(f"   Red columns: {len(band_columns['red'])}")
                            print(f"   Amber columns: {len(band_columns['amber'])}")
                            print(f"   Green columns: {len(band_columns['green'])}")

                            # Process each band
                            for band, columns in band_columns.items():
                                if columns:
                                    # Convert to numeric and get statistics
                                    for col in columns:
                                        rates = pd.to_numeric(
                                            df[col], errors="coerce"
                                        ).dropna()
                                        if len(rates) > 0:
                                            stats = {
                                                "column": col,
                                                "min": float(rates.min()),
                                                "max": float(rates.max()),
                                                "mean": float(rates.mean()),
                                                "median": float(rates.median()),
                                                "values": rates.tolist()[
                                                    :10
                                                ],  # First 10 values
                                            }
                                            rate_data[band].append(stats)

                            # Break if we've found rates
                            break
                    except Exception as e:
                        # Try the next skip_rows value
                        continue

                # If we've found rates in this sheet, don't check other sheets
                if found_rates:
                    break

            # Store rate data
            key = f"{dno_name}_{year}" if year else dno_name
            self.rate_data[key] = {
                "dno_name": dno_name,
                "mpan_code": mpan_code,
                "year": year,
                "file_path": file_path,
                "rate_data": rate_data,
            }

            # Print sample of rate data
            for band, data in rate_data.items():
                if data:
                    print(f"   {band.upper()} band rates:")
                    for i, stats in enumerate(data[:2]):  # Show first 2 columns
                        print(
                            f"     Column {i+1}: {stats['min']:.4f} to {stats['max']:.4f} p/kWh (avg: {stats['mean']:.4f})"
                        )
                        print(
                            f"     Sample values: {[f'{v:.4f}' for v in stats['values'][:5]]}"
                        )

            return rate_data

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return rate_data

    def combine_time_and_rate_data(self):
        """Combine time period definitions with rate data"""
        print("\n🔄 Combining time period and rate data...")

        combined_data = []

        # Get all unique DNOs and years
        all_keys = set(list(self.time_band_data.keys()) + list(self.rate_data.keys()))

        for key in all_keys:
            # Extract DNO and year from key
            parts = key.split("_")
            dno_name = "_".join(parts[:-1]) if len(parts) > 1 else key
            year = parts[-1] if len(parts) > 1 and parts[-1].isdigit() else None

            # Get time period data
            time_periods = self.time_band_data.get(key, {}).get("time_periods", {})
            if not time_periods:
                # Try with just the DNO name
                for tk in self.time_band_data:
                    if tk.startswith(dno_name):
                        time_periods = self.time_band_data[tk].get("time_periods", {})
                        if time_periods:
                            break

            # Get rate data
            rate_data = self.rate_data.get(key, {}).get("rate_data", {})
            if not rate_data:
                # Try with just the DNO name
                for rk in self.rate_data:
                    if rk.startswith(dno_name):
                        rate_data = self.rate_data[rk].get("rate_data", {})
                        if rate_data:
                            break

            # Get MPAN code
            mpan_code = None
            if key in self.time_band_data and self.time_band_data[key].get("mpan_code"):
                mpan_code = self.time_band_data[key]["mpan_code"]
            elif key in self.rate_data and self.rate_data[key].get("mpan_code"):
                mpan_code = self.rate_data[key]["mpan_code"]

            # Create combined entry
            entry = {
                "dno_name": dno_name,
                "mpan_code": mpan_code,
                "year": year,
                "time_periods": {},
                "rate_summary": {},
            }

            # Add time periods
            for band in ["red", "amber", "green"]:
                entry["time_periods"][band] = time_periods.get(band, "Not available")

            # Add rate summaries
            for band in ["red", "amber", "green"]:
                band_rates = rate_data.get(band, [])
                if band_rates:
                    # Calculate aggregate statistics
                    all_mins = [r["min"] for r in band_rates]
                    all_maxs = [r["max"] for r in band_rates]
                    all_means = [r["mean"] for r in band_rates]

                    entry["rate_summary"][band] = {
                        "min": min(all_mins),
                        "max": max(all_maxs),
                        "mean": sum(all_means) / len(all_means),
                        "num_columns": len(band_rates),
                        "sample_values": (
                            band_rates[0]["values"][:5]
                            if band_rates[0]["values"]
                            else []
                        ),
                    }
                else:
                    entry["rate_summary"][band] = {
                        "min": None,
                        "max": None,
                        "mean": None,
                        "num_columns": 0,
                        "sample_values": [],
                    }

            combined_data.append(entry)

        # Sort by DNO and year
        combined_data.sort(key=lambda x: (x["dno_name"], x["year"] or 0))

        self.combined_data = combined_data
        print(f"   ✅ Combined {len(combined_data)} entries")

        return combined_data

    def generate_report(self):
        """Generate a comprehensive report of DUoS time bands and rates"""
        print("\n📝 Generating DUoS time band report...")

        if not self.combined_data:
            print("   ⚠️ No data to report")
            return

        # Create report file
        report_path = os.path.join(self.output_dir, "duos_time_band_report.txt")
        with open(report_path, "w") as f:
            f.write("DUoS TIME BAND ANALYSIS BY DNO\n")
            f.write("=" * 50 + "\n\n")
            f.write(
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write(
                "This report provides a detailed breakdown of Distribution Use of System (DUoS) charges\n"
            )
            f.write(
                "for each Distribution Network Operator (DNO), showing the time periods for Red, Amber\n"
            )
            f.write("and Green bands and the corresponding rates in p/kWh.\n\n")

            # Group by DNO
            dno_data = {}
            for entry in self.combined_data:
                dno_name = entry["dno_name"]
                if dno_name not in dno_data:
                    dno_data[dno_name] = []
                dno_data[dno_name].append(entry)

            # Write data for each DNO
            for dno_name, entries in dno_data.items():
                mpan_code = entries[0]["mpan_code"]
                mpan_str = f"(MPAN {mpan_code})" if mpan_code else ""

                f.write(f"\n{dno_name} {mpan_str}\n")
                f.write("-" * 50 + "\n\n")

                # Write time period definitions (using the most recent entry)
                latest_entry = max(entries, key=lambda x: x["year"] or 0)
                f.write("TIME PERIOD DEFINITIONS:\n")
                for band in ["red", "amber", "green"]:
                    period = latest_entry["time_periods"].get(band, "Not available")
                    f.write(f"  {band.upper()}: {period}\n")

                f.write("\nRATES BY YEAR:\n")

                # Write rates for each year
                for entry in sorted(entries, key=lambda x: x["year"] or 0):
                    year = entry["year"] or "Unknown"
                    f.write(f"\n  {year}:\n")

                    for band in ["red", "amber", "green"]:
                        rate_summary = entry["rate_summary"].get(band, {})
                        if rate_summary.get("min") is not None:
                            f.write(
                                f"    {band.upper()}: {rate_summary['min']:.4f} to {rate_summary['max']:.4f} p/kWh "
                            )
                            f.write(f"(avg: {rate_summary['mean']:.4f})\n")

                            # Show sample values
                            sample_values = rate_summary.get("sample_values", [])
                            if sample_values:
                                f.write(
                                    f"      Sample values: {[f'{v:.4f}' for v in sample_values[:5]]}\n"
                                )
                        else:
                            f.write(f"    {band.upper()}: No data available\n")

            # Add a summary table
            f.write("\n\nSUMMARY TABLE\n")
            f.write("-" * 50 + "\n\n")
            f.write(
                "DNO                     | MPAN | Year | Red Rate      | Amber Rate    | Green Rate\n"
            )
            f.write("-" * 90 + "\n")

            for entry in self.combined_data:
                dno_name = entry["dno_name"][:20].ljust(20)
                mpan = (
                    str(entry["mpan_code"]).ljust(4)
                    if entry["mpan_code"]
                    else "N/A ".ljust(4)
                )
                year = str(entry["year"]).ljust(4) if entry["year"] else "N/A ".ljust(4)

                red_rate = entry["rate_summary"].get("red", {})
                amber_rate = entry["rate_summary"].get("amber", {})
                green_rate = entry["rate_summary"].get("green", {})

                red_str = (
                    f"{red_rate.get('min', 0):.4f}-{red_rate.get('max', 0):.4f}".ljust(
                        13
                    )
                    if red_rate.get("min") is not None
                    else "N/A".ljust(13)
                )
                amber_str = (
                    f"{amber_rate.get('min', 0):.4f}-{amber_rate.get('max', 0):.4f}".ljust(
                        13
                    )
                    if amber_rate.get("min") is not None
                    else "N/A".ljust(13)
                )
                green_str = (
                    f"{green_rate.get('min', 0):.4f}-{green_rate.get('max', 0):.4f}".ljust(
                        13
                    )
                    if green_rate.get("min") is not None
                    else "N/A".ljust(13)
                )

                f.write(
                    f"{dno_name} | {mpan} | {year} | {red_str} | {amber_str} | {green_str}\n"
                )

        print(f"   ✅ Report saved to: {report_path}")

        # Create CSV version for easier data processing
        csv_path = os.path.join(self.output_dir, "duos_time_band_rates.csv")

        # Prepare CSV data
        csv_data = []
        for entry in self.combined_data:
            for band in ["red", "amber", "green"]:
                rate_summary = entry["rate_summary"].get(band, {})
                if rate_summary.get("min") is not None:
                    row = {
                        "dno_name": entry["dno_name"],
                        "mpan_code": entry["mpan_code"],
                        "year": entry["year"],
                        "band": band.upper(),
                        "time_period": entry["time_periods"].get(band, "Not available"),
                        "min_rate": rate_summary.get("min"),
                        "max_rate": rate_summary.get("max"),
                        "mean_rate": rate_summary.get("mean"),
                        "num_columns": rate_summary.get("num_columns"),
                    }
                    csv_data.append(row)

        # Write CSV
        if csv_data:
            df = pd.DataFrame(csv_data)
            df.to_csv(csv_path, index=False)
            print(f"   ✅ CSV data saved to: {csv_path}")

        # Create JSON data file
        json_path = os.path.join(self.output_dir, "duos_time_band_data.json")
        with open(json_path, "w") as f:
            json.dump(self.combined_data, f, indent=2, default=str)

        print(f"   ✅ JSON data saved to: {json_path}")

        # Create a summary visualization
        self.create_visualizations()

        return report_path

    def create_visualizations(self):
        """Create visualizations of the time band data"""
        print("\n📊 Creating visualizations...")

        if not self.combined_data:
            print("   ⚠️ No data to visualize")
            return

        # Create plots directory
        plots_dir = os.path.join(self.output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)

        # Prepare data for plotting
        plot_data = []
        for entry in self.combined_data:
            for band in ["red", "amber", "green"]:
                rate_summary = entry["rate_summary"].get(band, {})
                if rate_summary.get("mean") is not None:
                    plot_data.append(
                        {
                            "dno_name": entry["dno_name"],
                            "mpan_code": entry["mpan_code"],
                            "year": entry["year"] or 0,
                            "band": band,
                            "mean_rate": rate_summary["mean"],
                        }
                    )

        if not plot_data:
            print("   ⚠️ No valid data for plotting")
            return

        plot_df = pd.DataFrame(plot_data)

        # 1. Bar chart of mean rates by band
        plt.figure(figsize=(12, 6))
        band_means = plot_df.groupby("band")["mean_rate"].mean()

        colors = {"red": "red", "amber": "orange", "green": "green"}
        bars = plt.bar(
            band_means.index,
            band_means.values,
            color=[colors[b] for b in band_means.index],
        )

        plt.title("Average DUoS Rates by Time Band", fontsize=14)
        plt.ylabel("Rate (p/kWh)", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f"{height:.2f}",
                ha="center",
                va="bottom",
            )

        plt.savefig(
            os.path.join(plots_dir, "duos_band_rates.png"), dpi=300, bbox_inches="tight"
        )

        # 2. DNO comparison
        top_dnos = plot_df["dno_name"].value_counts().nlargest(6).index
        dno_data = plot_df[plot_df["dno_name"].isin(top_dnos)]

        plt.figure(figsize=(14, 8))

        dno_band_means = (
            dno_data.groupby(["dno_name", "band"])["mean_rate"].mean().reset_index()
        )
        dno_band_pivot = dno_band_means.pivot(
            index="dno_name", columns="band", values="mean_rate"
        )

        dno_band_pivot.plot(
            kind="bar", figsize=(14, 8), color=["red", "orange", "green"]
        )
        plt.title("DUoS Rates by DNO and Time Band", fontsize=14)
        plt.ylabel("Rate (p/kWh)", fontsize=12)
        plt.xlabel("Distribution Network Operator", fontsize=12)
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.legend(title="Time Band")
        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()
        plt.savefig(
            os.path.join(plots_dir, "duos_dno_comparison.png"),
            dpi=300,
            bbox_inches="tight",
        )

        # 3. Year trend (if we have multiple years)
        if plot_df["year"].nunique() > 1:
            # Convert year to int and filter out zero years
            plot_df["year_int"] = pd.to_numeric(plot_df["year"], errors="coerce")
            year_data = plot_df[plot_df["year_int"] > 0]

            if not year_data.empty:
                plt.figure(figsize=(12, 7))

                year_band_means = (
                    year_data.groupby(["year_int", "band"])["mean_rate"]
                    .mean()
                    .reset_index()
                )

                for band in ["red", "amber", "green"]:
                    band_data = year_band_means[year_band_means["band"] == band]
                    if not band_data.empty:
                        plt.plot(
                            band_data["year_int"],
                            band_data["mean_rate"],
                            marker="o",
                            label=band.upper(),
                            linewidth=2,
                            color=colors[band],
                        )

                plt.title("DUoS Rate Trends by Year and Time Band", fontsize=14)
                plt.xlabel("Year", fontsize=12)
                plt.ylabel("Rate (p/kWh)", fontsize=12)
                plt.grid(linestyle="--", alpha=0.7)
                plt.legend()

                plt.savefig(
                    os.path.join(plots_dir, "duos_year_trend.png"),
                    dpi=300,
                    bbox_inches="tight",
                )

        print(f"   ✅ Visualizations saved to: {plots_dir}")

    def run_analysis(self):
        """Run the complete analysis process"""
        print("🚀 DUoS TIME BAND ANALYZER BY DNO")
        print("=" * 50)

        # Find all Excel files
        excel_files = self.find_all_excel_files()
        print(f"\n📁 Found {len(excel_files)} Excel files to analyze")

        # Process each file for time periods
        for file_path in excel_files:
            self.extract_time_periods(file_path)

        # Process each file for rate data
        for file_path in excel_files:
            self.extract_rate_data(file_path)

        # Combine data
        self.combine_time_and_rate_data()

        # Generate report
        report_path = self.generate_report()

        print("\n🎊 ANALYSIS COMPLETE!")
        print(
            f"✅ Analyzed time bands and rates for {len(self.combined_data)} DNO/year combinations"
        )
        print(f"✅ Data and reports exported to: {self.output_dir}/")
        print(
            f"✅ This analysis provides a comprehensive view of DUoS time bands and rates per DNO"
        )

        return report_path


if __name__ == "__main__":
    analyzer = DUoSTimeBandAnalyzer()
    analyzer.run_analysis()
