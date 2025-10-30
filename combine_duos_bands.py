#!/usr/bin/env python3
"""
DUoS Combined Red, Amber, Green Band Analyzer

This script combines and analyzes Distribution Use of System (DUoS) charging data
across all Red, Amber, and Green time bands from the collected DNO charging statements.

Features:
- Combines all time-of-use bands into a single dataset
- Analyzes pricing trends across DNOs and regions
- Calculates weighted averages and comparative metrics
- Generates summary reports and visualizations

Author: Jibber Jabber Knowledge System
Date: 14 September 2025
"""

import glob
import json
import os
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Define directories where DUoS data is stored
DATA_DIRS = [
    "duos_extracted_data",
    "duos_expanded_data",
    "duos_spm_data",
    "duos_ssen_data",
    "duos_nged_data",
]

# Define column patterns to identify Red, Amber, and Green bands
BAND_PATTERNS = {
    "red": ["red", "peak", "high", "r_"],
    "amber": ["amber", "shoulder", "medium", "a_"],
    "green": ["green", "off peak", "low", "g_"],
}

# MPAN to DNO mapping for standardization
MPAN_DNO_MAP = {
    10: "UKPN Eastern (EPN)",
    11: "UKPN London (LPN)",
    12: "UKPN South Eastern (SPN)",
    13: "SP Manweb (SPM)",
    14: "Electricity North West (ENWL)",
    15: "SP Energy Networks (SPEN)",
    16: "Northern Powergrid (NPG)",
    17: "SSEN Hydro (SHEPD)",
    19: "Northern Powergrid (NPG)",
    20: "SSEN Southern (SEPD)",
    21: "NGED West Midlands",
    22: "NGED East Midlands",
    23: "NGED South Wales",
    24: "NGED South West",
    25: "SP Distribution (SPD)",
}


class DUoSCombinedAnalyzer:
    """Analyze and combine DUoS Red, Amber, Green bands across all DNOs"""

    def __init__(self, output_dir="duos_combined_analysis"):
        """Initialize the analyzer"""
        self.output_dir = output_dir
        self.combined_data = pd.DataFrame()
        self.summary_stats = {}
        self.band_data = {
            "red": pd.DataFrame(),
            "amber": pd.DataFrame(),
            "green": pd.DataFrame(),
        }

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

    def find_all_csv_files(self):
        """Find all CSV files in the data directories"""
        all_files = []

        for dir_path in DATA_DIRS:
            if os.path.exists(dir_path):
                # Get all CSV files in this directory and subdirectories
                pattern = os.path.join(dir_path, "**", "*.csv")
                files = glob.glob(pattern, recursive=True)
                all_files.extend(files)

        return sorted(all_files)

    def identify_band_columns(self, df):
        """Identify Red, Amber, Green band columns in the dataframe"""
        band_columns = {"red": [], "amber": [], "green": []}

        for col in df.columns:
            col_lower = col.lower()

            # Check each band pattern
            for band, patterns in BAND_PATTERNS.items():
                if any(pattern in col_lower for pattern in patterns):
                    band_columns[band].append(col)

        return band_columns

    def extract_tariff_info(self, file_path):
        """Extract year and DNO info from file path"""
        file_name = os.path.basename(file_path)
        parts = file_name.lower().split("_")

        # Extract year (look for 4-digit numbers)
        year = None
        for part in parts:
            if part.isdigit() and len(part) == 4 and 2010 <= int(part) <= 2030:
                year = int(part)
                break

        # If no 4-digit year found, try to extract from patterns like 2025-26 or 25-26
        if not year:
            for part in parts:
                if "-" in part:
                    year_parts = part.split("-")
                    if len(year_parts) == 2:
                        # Try to handle formats like 2025-26 or 25-26
                        try:
                            if len(year_parts[0]) == 4:  # 2025-26 format
                                year = int(year_parts[0])
                            elif len(year_parts[0]) == 2:  # 25-26 format
                                year = int("20" + year_parts[0])
                        except ValueError:
                            pass

        # Extract DNO name
        dno_name = "Unknown"
        mpan_code = None

        dno_patterns = {
            "ukpn": {"name": "UK Power Networks", "patterns": ["ukpn", "uk power"]},
            "eastern": {
                "name": "UKPN Eastern",
                "mpan": 10,
                "patterns": ["eastern", "epn"],
            },
            "london": {
                "name": "UKPN London",
                "mpan": 11,
                "patterns": ["london", "lpn"],
            },
            "south eastern": {
                "name": "UKPN South Eastern",
                "mpan": 12,
                "patterns": ["south eastern", "spn"],
            },
            "enwl": {
                "name": "Electricity North West",
                "mpan": 14,
                "patterns": ["enwl", "electricity north west"],
            },
            "northern": {
                "name": "Northern Powergrid",
                "mpan": 16,
                "patterns": ["northern", "npg", "northeast"],
            },
            "yorkshire": {
                "name": "Northern Powergrid Yorkshire",
                "mpan": 19,
                "patterns": ["yorkshire", "yorks"],
            },
            "spm": {"name": "SP Manweb", "mpan": 13, "patterns": ["spm", "manweb"]},
            "spd": {
                "name": "SP Distribution",
                "mpan": 25,
                "patterns": ["spd", "sp distribution"],
            },
            "shepd": {"name": "SSEN Hydro", "mpan": 17, "patterns": ["shepd", "hydro"]},
            "sepd": {
                "name": "SSEN Southern",
                "mpan": 20,
                "patterns": ["sepd", "southern electric"],
            },
            "nged": {
                "name": "National Grid Electricity Distribution",
                "patterns": ["nged", "national grid"],
            },
            "east midlands": {
                "name": "NGED East Midlands",
                "mpan": 22,
                "patterns": ["east midlands"],
            },
            "west midlands": {
                "name": "NGED West Midlands",
                "mpan": 21,
                "patterns": ["west midlands"],
            },
            "south wales": {
                "name": "NGED South Wales",
                "mpan": 23,
                "patterns": ["south wales"],
            },
            "south west": {
                "name": "NGED South West",
                "mpan": 24,
                "patterns": ["south west"],
            },
        }

        file_path_lower = file_path.lower()
        file_name_lower = file_name.lower()

        for key, info in dno_patterns.items():
            if any(
                pattern in file_path_lower or pattern in file_name_lower
                for pattern in info["patterns"]
            ):
                dno_name = info["name"]
                if "mpan" in info:
                    mpan_code = info["mpan"]
                break

        return {
            "dno_name": dno_name,
            "mpan_code": mpan_code,
            "year": year,
            "file_name": file_name,
        }

    def process_csv_file(self, file_path):
        """Process a CSV file and extract Red, Amber, Green band data"""
        print(f"\n📊 Processing: {os.path.basename(file_path)}")

        try:
            # Read CSV file
            df = pd.read_csv(file_path)

            # Get tariff info
            tariff_info = self.extract_tariff_info(file_path)
            print(f"   DNO: {tariff_info['dno_name']}, Year: {tariff_info['year']}")

            # Identify band columns
            band_columns = self.identify_band_columns(df)
            red_cols = band_columns["red"]
            amber_cols = band_columns["amber"]
            green_cols = band_columns["green"]

            print(f"   Red columns: {len(red_cols)}")
            print(f"   Amber columns: {len(amber_cols)}")
            print(f"   Green columns: {len(green_cols)}")

            if not (red_cols or amber_cols or green_cols):
                print("   ⚠️ No band columns found, attempting pattern matching...")

                # Try pattern matching on all numeric columns
                for col in df.columns:
                    if (
                        df[col].dtype in [np.float64, np.int64]
                        or "float" in str(df[col].dtype)
                        or "int" in str(df[col].dtype)
                    ):
                        col_lower = col.lower()

                        # Check for rate-related keywords
                        if any(
                            term in col_lower
                            for term in ["rate", "charge", "p/kwh", "price"]
                        ):
                            # Try to infer the band from context
                            if any(term in col_lower for term in ["peak", "high"]):
                                band_columns["red"].append(col)
                            elif any(
                                term in col_lower for term in ["shoulder", "medium"]
                            ):
                                band_columns["amber"].append(col)
                            elif any(term in col_lower for term in ["off", "low"]):
                                band_columns["green"].append(col)

                red_cols = band_columns["red"]
                amber_cols = band_columns["amber"]
                green_cols = band_columns["green"]

                print(f"   After pattern matching:")
                print(f"   Red columns: {len(red_cols)}")
                print(f"   Amber columns: {len(amber_cols)}")
                print(f"   Green columns: {len(green_cols)}")

            # Extract data for each band
            band_data = {}

            for band, cols in band_columns.items():
                if cols:
                    # Process each column in this band
                    for col in cols:
                        # Clean and convert to numeric
                        df[col] = pd.to_numeric(df[col], errors="coerce")

                    # Collect statistics for this band
                    band_df = df[cols].copy()

                    # Calculate statistics
                    stats = {
                        "min": band_df.min().min(),
                        "max": band_df.max().max(),
                        "mean": band_df.mean().mean(),
                        "median": band_df.median().median(),
                        "count": band_df.count().sum(),
                    }

                    # Add to band data
                    band_data[band] = {"columns": cols, "stats": stats}

                    # Add a row to the appropriate band dataframe
                    row_data = {
                        "file_path": file_path,
                        "dno_name": tariff_info["dno_name"],
                        "mpan_code": tariff_info["mpan_code"],
                        "year": tariff_info["year"],
                        "band": band,
                        "min_rate": stats["min"],
                        "max_rate": stats["max"],
                        "mean_rate": stats["mean"],
                        "median_rate": stats["median"],
                        "count": stats["count"],
                    }

                    # Add to band-specific dataframe
                    self.band_data[band] = pd.concat(
                        [self.band_data[band], pd.DataFrame([row_data])],
                        ignore_index=True,
                    )

            # Print summary of findings
            for band, data in band_data.items():
                if "stats" in data:
                    stats = data["stats"]
                    print(
                        f"   {band.upper()} band: {stats['min']:.4f} to {stats['max']:.4f} p/kWh (avg: {stats['mean']:.4f})"
                    )

            return band_data

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return None

    def combine_all_band_data(self):
        """Combine all band data into a single dataset"""
        print("\n🔄 Combining all band data...")

        # Create combined dataframe from all bands
        combined_data = pd.DataFrame()

        for band, df in self.band_data.items():
            if not df.empty:
                # Add band identifier
                df["band"] = band.upper()
                combined_data = pd.concat([combined_data, df], ignore_index=True)

        # Fill missing MPAN codes where possible
        for idx, row in combined_data.iterrows():
            if pd.isna(row["mpan_code"]):
                # Try to infer from DNO name
                dno_lower = row["dno_name"].lower()

                for mpan, dno_name in MPAN_DNO_MAP.items():
                    if dno_lower in dno_name.lower():
                        combined_data.loc[idx, "mpan_code"] = mpan
                        break

        # Save the combined dataframe
        self.combined_data = combined_data

        print(f"   ✅ Combined dataset created with {len(combined_data)} rows")
        print(f"   DNOs represented: {combined_data['dno_name'].nunique()}")
        print(
            f"   Years covered: {combined_data['year'].min()} to {combined_data['year'].max()}"
        )
        print(f"   Total band entries: {len(combined_data)}")

        # Save the combined data
        csv_path = os.path.join(self.output_dir, "duos_all_bands_combined.csv")
        combined_data.to_csv(csv_path, index=False)
        print(f"   💾 Combined data saved to: {csv_path}")

        return combined_data

    def generate_summary_statistics(self):
        """Generate summary statistics for the combined dataset"""
        print("\n📊 Generating summary statistics...")

        df = self.combined_data

        if df.empty:
            print("   ⚠️ No data to analyze")
            return

        # Calculate overall statistics
        overall_stats = {
            "total_entries": len(df),
            "dnos_represented": df["dno_name"].nunique(),
            "mpan_codes_represented": df["mpan_code"].nunique(),
            "years_covered": df["year"].nunique(),
            "min_year": int(df["year"].min()),
            "max_year": int(df["year"].max()),
            "red_entries": len(df[df["band"] == "RED"]),
            "amber_entries": len(df[df["band"] == "AMBER"]),
            "green_entries": len(df[df["band"] == "GREEN"]),
            "overall_min_rate": df["min_rate"].min(),
            "overall_max_rate": df["max_rate"].max(),
            "overall_mean_rate": df["mean_rate"].mean(),
            "timestamp": datetime.now().isoformat(),
        }

        # Calculate statistics by band
        band_stats = (
            df.groupby("band")
            .agg(
                {
                    "min_rate": "min",
                    "max_rate": "max",
                    "mean_rate": "mean",
                    "median_rate": "median",
                    "count": "sum",
                }
            )
            .to_dict()
        )

        # Calculate statistics by DNO
        dno_stats = (
            df.groupby("dno_name")
            .agg(
                {
                    "min_rate": "min",
                    "max_rate": "max",
                    "mean_rate": "mean",
                    "year": ["min", "max", "nunique"],
                    "band": "count",
                }
            )
            .reset_index()
        )

        dno_stats.columns = [
            "dno_name",
            "min_rate",
            "max_rate",
            "mean_rate",
            "min_year",
            "max_year",
            "years_covered",
            "entries",
        ]
        dno_stats_dict = dno_stats.to_dict(orient="records")

        # Calculate statistics by year
        year_stats = (
            df.groupby("year")
            .agg(
                {
                    "min_rate": "min",
                    "max_rate": "max",
                    "mean_rate": "mean",
                    "dno_name": "nunique",
                    "band": "count",
                }
            )
            .reset_index()
        )

        year_stats.columns = [
            "year",
            "min_rate",
            "max_rate",
            "mean_rate",
            "dnos_represented",
            "entries",
        ]
        year_stats_dict = year_stats.to_dict(orient="records")

        # Combine all statistics
        summary = {
            "overall": overall_stats,
            "by_band": band_stats,
            "by_dno": dno_stats_dict,
            "by_year": year_stats_dict,
        }

        # Save summary statistics
        json_path = os.path.join(self.output_dir, "duos_combined_summary.json")
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"   💾 Summary statistics saved to: {json_path}")

        # Create a text report
        report_path = os.path.join(self.output_dir, "duos_combined_report.txt")
        with open(report_path, "w") as f:
            f.write("DUoS COMBINED RED, AMBER, GREEN BAND ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            f.write(
                f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            f.write("OVERALL SUMMARY\n")
            f.write("-" * 30 + "\n")
            f.write(f"Total entries: {overall_stats['total_entries']}\n")
            f.write(f"DNOs represented: {overall_stats['dnos_represented']}\n")
            f.write(f"MPAN codes: {overall_stats['mpan_codes_represented']}\n")
            f.write(
                f"Years covered: {overall_stats['min_year']} to {overall_stats['max_year']}\n"
            )
            f.write(f"Red entries: {overall_stats['red_entries']}\n")
            f.write(f"Amber entries: {overall_stats['amber_entries']}\n")
            f.write(f"Green entries: {overall_stats['green_entries']}\n")
            f.write(
                f"Overall rate range: {overall_stats['overall_min_rate']:.4f} to {overall_stats['overall_max_rate']:.4f} p/kWh\n"
            )
            f.write(
                f"Overall mean rate: {overall_stats['overall_mean_rate']:.4f} p/kWh\n\n"
            )

            f.write("BAND STATISTICS\n")
            f.write("-" * 30 + "\n")
            for band in ["RED", "AMBER", "GREEN"]:
                if band in band_stats["min_rate"]:
                    f.write(f"{band} band:\n")
                    f.write(
                        f"  Range: {band_stats['min_rate'][band]:.4f} to {band_stats['max_rate'][band]:.4f} p/kWh\n"
                    )
                    f.write(f"  Mean: {band_stats['mean_rate'][band]:.4f} p/kWh\n")
                    f.write(f"  Median: {band_stats['median_rate'][band]:.4f} p/kWh\n")
                    f.write(f"  Count: {band_stats['count'][band]}\n\n")

            f.write("DNO STATISTICS\n")
            f.write("-" * 30 + "\n")
            for dno in dno_stats_dict:
                f.write(f"{dno['dno_name']}:\n")
                f.write(
                    f"  Range: {dno['min_rate']:.4f} to {dno['max_rate']:.4f} p/kWh\n"
                )
                f.write(f"  Mean: {dno['mean_rate']:.4f} p/kWh\n")
                f.write(
                    f"  Years: {int(dno['min_year'])} to {int(dno['max_year'])} ({dno['years_covered']} years)\n"
                )
                f.write(f"  Entries: {dno['entries']}\n\n")

            f.write("YEAR STATISTICS\n")
            f.write("-" * 30 + "\n")
            for year in sorted(year_stats_dict, key=lambda x: x["year"]):
                f.write(f"{int(year['year'])}:\n")
                f.write(
                    f"  Range: {year['min_rate']:.4f} to {year['max_rate']:.4f} p/kWh\n"
                )
                f.write(f"  Mean: {year['mean_rate']:.4f} p/kWh\n")
                f.write(f"  DNOs: {year['dnos_represented']}\n")
                f.write(f"  Entries: {year['entries']}\n\n")

        print(f"   📝 Detailed report saved to: {report_path}")

        # Save the summary stats for later use
        self.summary_stats = summary
        return summary

    def generate_visualizations(self):
        """Generate visualizations for the combined dataset"""
        print("\n📈 Generating visualizations...")

        df = self.combined_data

        if df.empty:
            print("   ⚠️ No data to visualize")
            return

        # Create a plots directory
        plots_dir = os.path.join(self.output_dir, "plots")
        os.makedirs(plots_dir, exist_ok=True)

        # 1. Band rates comparison
        plt.figure(figsize=(10, 6))
        band_means = df.groupby("band")["mean_rate"].mean()
        bars = plt.bar(
            band_means.index, band_means.values, color=["red", "orange", "green"]
        )
        plt.title("Average DUoS Rates by Time Band (p/kWh)")
        plt.ylabel("p/kWh")
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
            os.path.join(plots_dir, "duos_band_comparison.png"),
            dpi=300,
            bbox_inches="tight",
        )

        # 2. Year trend analysis
        if df["year"].nunique() > 1:
            plt.figure(figsize=(12, 7))
            year_band_means = (
                df.groupby(["year", "band"])["mean_rate"].mean().reset_index()
            )

            for band in ["RED", "AMBER", "GREEN"]:
                band_data = year_band_means[year_band_means["band"] == band]
                if not band_data.empty:
                    plt.plot(
                        band_data["year"],
                        band_data["mean_rate"],
                        marker="o",
                        label=band,
                        linewidth=2,
                        color={"RED": "red", "AMBER": "orange", "GREEN": "green"}[band],
                    )

            plt.title("DUoS Rate Trends by Year and Time Band")
            plt.xlabel("Year")
            plt.ylabel("p/kWh")
            plt.grid(linestyle="--", alpha=0.7)
            plt.legend()
            plt.savefig(
                os.path.join(plots_dir, "duos_year_trend.png"),
                dpi=300,
                bbox_inches="tight",
            )

        # 3. DNO comparison (top 10 by entries)
        top_dnos = df.groupby("dno_name").size().nlargest(10).index
        dno_band_data = df[df["dno_name"].isin(top_dnos)]

        plt.figure(figsize=(14, 8))
        dno_band_means = (
            dno_band_data.groupby(["dno_name", "band"])["mean_rate"]
            .mean()
            .reset_index()
        )

        bar_width = 0.25
        x = np.arange(len(top_dnos))

        for i, band in enumerate(["RED", "AMBER", "GREEN"]):
            band_data = dno_band_means[dno_band_means["band"] == band]
            if not band_data.empty:
                # Create a mapping of DNO names to their mean rates
                dno_rates = {dno: 0 for dno in top_dnos}
                for _, row in band_data.iterrows():
                    if row["dno_name"] in top_dnos:
                        dno_rates[row["dno_name"]] = row["mean_rate"]

                # Get rates in the same order as top_dnos
                rates = [dno_rates[dno] for dno in top_dnos]

                plt.bar(
                    x + i * bar_width - bar_width,
                    rates,
                    bar_width,
                    label=band,
                    color={"RED": "red", "AMBER": "orange", "GREEN": "green"}[band],
                )

        plt.xlabel("Distribution Network Operator")
        plt.ylabel("p/kWh")
        plt.title("DUoS Rates Comparison by DNO and Time Band")
        plt.xticks(
            x,
            [dno[:15] + "..." if len(dno) > 15 else dno for dno in top_dnos],
            rotation=45,
            ha="right",
        )
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.savefig(
            os.path.join(plots_dir, "duos_dno_comparison.png"),
            dpi=300,
            bbox_inches="tight",
        )

        print(f"   ✅ Visualizations saved to: {plots_dir}")

    def run_analysis(self):
        """Run the complete analysis process"""
        print("🚀 DUoS COMBINED RED, AMBER, GREEN BAND ANALYZER")
        print("=" * 50)

        # Find all CSV files
        csv_files = self.find_all_csv_files()
        print(f"\n📁 Found {len(csv_files)} CSV files to analyze")

        # Process each file
        for file_path in csv_files:
            self.process_csv_file(file_path)

        # Combine all band data
        self.combine_all_band_data()

        # Generate summary statistics
        self.generate_summary_statistics()

        # Generate visualizations
        self.generate_visualizations()

        print("\n🎊 ANALYSIS COMPLETE!")
        print(
            f"✅ Combined {len(self.combined_data)} band entries across Red, Amber, and Green periods"
        )
        print(f"✅ Data and reports exported to: {self.output_dir}/")
        print(
            f"✅ This analysis provides a comprehensive view of DUoS time-of-use pricing across all DNOs"
        )


if __name__ == "__main__":
    analyzer = DUoSCombinedAnalyzer()
    analyzer.run_analysis()
