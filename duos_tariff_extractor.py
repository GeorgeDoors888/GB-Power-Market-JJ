#!/usr/bin/env python3
"""
DUoS Tariff Extractor - Extract actual charging rates from DNO Excel methodologies

This tool extracts real Distribution Use of System (DUoS) charging rates from
official DNO "Schedule of Charges" Excel files.

Major Discovery: We have actual tariff schedules with real rates in p/kWh!
Coverage: ENWL, UKPN Eastern, Northern Powergrid, SP Distribution
Years: 2017-2025 historical data available

Author: Jibber Jabber Knowledge System
Date: September 13, 2025
"""

import glob
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd


class DUoSTariffExtractor:
    """Extract DUoS charging rates from DNO Excel methodology files"""

    def __init__(self, output_dir="duos_extracted_data"):
        self.output_dir = output_dir
        self.extracted_data = []
        self.summary_stats = {}

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # DNO mapping for MPAN identification
        self.dno_mapping = {
            "enwl": {"name": "Electricity North West", "mpan": 14},
            "eastern-power": {"name": "UK Power Networks Eastern", "mpan": 10},
            "london-power": {"name": "UK Power Networks London", "mpan": 11},
            "south-eastern": {"name": "UK Power Networks South Eastern", "mpan": 12},
            "northern": {"name": "Northern Powergrid", "mpan": 20},
            "yorkshire": {"name": "Northern Powergrid Yorkshire", "mpan": 21},
            "sp": {"name": "SP Distribution", "mpan": 25},  # Could be 25 or 26
            "southern": {
                "name": "Scottish & Southern Electricity Networks Southern",
                "mpan": 27,
            },
            "sepd": {
                "name": "Scottish & Southern Electricity Networks South East",
                "mpan": 28,
            },
        }

    def find_schedule_files(self):
        """Find all DNO schedule of charges Excel files"""
        patterns = [
            "**/*schedule*charges*.xlsx",
            "**/*schedule*charges*.xls",
            "*schedule*charges*.xlsx",
            "*schedule*charges*.xls",
        ]

        files = []
        for pattern in patterns:
            files.extend(glob.glob(pattern, recursive=True))

        # Remove duplicates and filter
        unique_files = list(set(files))
        schedule_files = []

        for file_path in unique_files:
            if os.path.getsize(file_path) > 50000:  # At least 50KB
                schedule_files.append(file_path)

        return sorted(schedule_files, key=lambda x: os.path.getsize(x), reverse=True)

    def identify_dno(self, filename):
        """Identify DNO from filename"""
        filename_lower = filename.lower()

        for key, info in self.dno_mapping.items():
            if key in filename_lower:
                return info["name"], info["mpan"]

        # Additional checks
        if "ukpn" in filename_lower or "uk power" in filename_lower:
            if "eastern" in filename_lower:
                return self.dno_mapping["eastern-power"]["name"], 10
            elif "london" in filename_lower:
                return self.dno_mapping["london-power"]["name"], 11
            elif "south" in filename_lower:
                return self.dno_mapping["south-eastern"]["name"], 12

        return "Unknown DNO", None

    def extract_year(self, filename):
        """Extract year from filename"""
        import re

        years = re.findall(r"20\d{2}", filename)
        if years:
            return int(years[-1])  # Take the latest year found
        return None

    def extract_tariff_data(self, file_path, sheet_name, skip_rows_range=(5, 20)):
        """Extract tariff data from a specific sheet"""
        try:
            for skip_rows in range(*skip_rows_range):
                try:
                    df = pd.read_excel(
                        file_path, sheet_name=sheet_name, skiprows=skip_rows, nrows=50
                    )

                    # Check if we have meaningful data
                    if len(df.columns) >= 3 and df.shape[0] > 3:
                        # Look for rate-related columns
                        rate_columns = []
                        for col in df.columns:
                            col_str = str(col).lower()
                            if any(
                                term in col_str
                                for term in [
                                    "charge",
                                    "rate",
                                    "p/kwh",
                                    "p/kva",
                                    "pence",
                                ]
                            ):
                                rate_columns.append(col)

                        if rate_columns:
                            # Found rate data!
                            return df, skip_rows, rate_columns

                except Exception:
                    continue

            return None, None, None

        except Exception as e:
            print(f"Error reading {sheet_name}: {e}")
            return None, None, None

    def process_file(self, file_path):
        """Process a single DNO schedule file"""
        filename = os.path.basename(file_path)
        dno_name, mpan_code = self.identify_dno(filename)
        year = self.extract_year(filename)
        file_size_kb = os.path.getsize(file_path) // 1024

        print(f"\n📊 Processing: {dno_name} ({year})")
        print(f"   File: {filename[:60]}...")
        print(f"   Size: {file_size_kb}KB, MPAN: {mpan_code}")

        try:
            # Get all sheets
            excel_file = pd.ExcelFile(file_path)
            sheets = excel_file.sheet_names

            # Priority sheets for tariff data
            priority_sheets = [
                "Annex 1 LV, HV and UMS charges",
                "Annex 1",
                "LV HV charges",
                "Tariff Schedule",
                "Distribution Charges",
                "Charges",
            ]

            # Find target sheets
            target_sheets = []
            for priority in priority_sheets:
                for sheet in sheets:
                    if priority.lower() in sheet.lower():
                        target_sheets.append(sheet)
                        break

            # If no priority sheets found, try any sheet with 'annex' or 'charge'
            if not target_sheets:
                for sheet in sheets:
                    if any(
                        term in sheet.lower() for term in ["annex", "charge", "tariff"]
                    ):
                        target_sheets.append(sheet)

            extracted_sheets = 0
            for sheet_name in target_sheets[:3]:  # Process top 3 relevant sheets
                df, skip_rows, rate_columns = self.extract_tariff_data(
                    file_path, sheet_name
                )

                if df is not None and rate_columns:
                    print(f"   ✅ Extracted: {sheet_name}")
                    print(f"      Rates found: {len(rate_columns)} columns")
                    print(f"      Data rows: {df.shape[0]}")

                    # Store extracted data
                    sheet_data = {
                        "file_path": file_path,
                        "dno_name": dno_name,
                        "mpan_code": mpan_code,
                        "year": year,
                        "sheet_name": sheet_name,
                        "skip_rows": skip_rows,
                        "columns": list(df.columns),
                        "rate_columns": rate_columns,
                        "data_rows": df.shape[0],
                        "data_cols": df.shape[1],
                        "extracted_at": datetime.now().isoformat(),
                    }

                    # Extract sample rates
                    sample_rates = {}
                    for col in rate_columns[:5]:  # Top 5 rate columns
                        rates = df[col].dropna()
                        if len(rates) > 0:
                            numeric_rates = pd.to_numeric(
                                rates, errors="coerce"
                            ).dropna()
                            if len(numeric_rates) > 0:
                                sample_rates[col] = {
                                    "min": float(numeric_rates.min()),
                                    "max": float(numeric_rates.max()),
                                    "mean": float(numeric_rates.mean()),
                                    "count": int(len(numeric_rates)),
                                    "sample_values": list(numeric_rates.head(5)),
                                }

                    sheet_data["sample_rates"] = sample_rates
                    self.extracted_data.append(sheet_data)

                    # Save the actual data as CSV
                    csv_filename = f"{dno_name.replace(' ', '_').lower()}_{year}_{sheet_name.replace(' ', '_').lower()}.csv"
                    csv_path = os.path.join(self.output_dir, csv_filename)
                    df.to_csv(csv_path, index=False)
                    sheet_data["csv_export"] = csv_path

                    extracted_sheets += 1

                    # Show sample of actual rates
                    print(f"      Sample rates:")
                    for col, stats in list(sample_rates.items())[:2]:
                        print(
                            f"        {col}: {stats['min']:.3f} to {stats['max']:.3f} (avg: {stats['mean']:.3f})"
                        )

            if extracted_sheets == 0:
                print(f"   ❌ No rate data found in {len(target_sheets)} sheets")

            return extracted_sheets

        except Exception as e:
            print(f"   ❌ Error processing file: {e}")
            return 0

    def generate_summary(self):
        """Generate summary of extracted data"""
        print(f"\n🎯 EXTRACTION SUMMARY")
        print("=" * 50)

        total_files = len(set(item["file_path"] for item in self.extracted_data))
        total_sheets = len(self.extracted_data)
        total_dnos = len(set(item["dno_name"] for item in self.extracted_data))

        print(f"📊 Processed: {total_files} files, {total_sheets} sheets")
        print(f"🏢 DNOs covered: {total_dnos}")

        # Group by DNO
        dno_summary = {}
        for item in self.extracted_data:
            dno = item["dno_name"]
            if dno not in dno_summary:
                dno_summary[dno] = {
                    "mpan_code": item["mpan_code"],
                    "years": set(),
                    "sheets": 0,
                    "total_rates": 0,
                }

            dno_summary[dno]["years"].add(item["year"])
            dno_summary[dno]["sheets"] += 1
            dno_summary[dno]["total_rates"] += len(item["rate_columns"])

        print(f"\n🏢 DNO BREAKDOWN:")
        for dno, info in dno_summary.items():
            years = sorted([y for y in info["years"] if y])
            year_range = (
                f"{min(years)}-{max(years)}"
                if len(years) > 1
                else str(years[0]) if years else "Unknown"
            )
            print(f"   {dno} (MPAN {info['mpan_code']})")
            print(f"      Years: {year_range}")
            print(
                f"      Sheets: {info['sheets']}, Rate columns: {info['total_rates']}"
            )

        # Calculate UK coverage
        known_mpans = set(
            item["mpan_code"] for item in self.extracted_data if item["mpan_code"]
        )
        uk_coverage = len(known_mpans) / 14 * 100  # 14 DNOs in UK

        print(f"\n🇬🇧 UK COVERAGE: {uk_coverage:.1f}% ({len(known_mpans)}/14 DNOs)")
        print(f"   Covered MPANs: {sorted(known_mpans)}")

        # Save summary
        summary = {
            "extraction_date": datetime.now().isoformat(),
            "total_files_processed": total_files,
            "total_sheets_extracted": total_sheets,
            "dnos_covered": total_dnos,
            "uk_coverage_percent": uk_coverage,
            "covered_mpan_codes": list(known_mpans),
            "dno_breakdown": {
                dno: {
                    "mpan_code": info["mpan_code"],
                    "years": list(info["years"]),
                    "sheets_extracted": info["sheets"],
                    "total_rate_columns": info["total_rates"],
                }
                for dno, info in dno_summary.items()
            },
            "detailed_extractions": self.extracted_data,
        }

        summary_path = os.path.join(self.output_dir, "duos_extraction_summary.json")
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n💾 Summary saved: {summary_path}")
        return summary


def main():
    """Main extraction process"""
    print("🚀 DUoS TARIFF EXTRACTOR")
    print("=" * 30)
    print("Discovering actual charging rates from DNO methodology files...")

    extractor = DUoSTariffExtractor()

    # Find all schedule files
    schedule_files = extractor.find_schedule_files()
    print(f"\n📁 Found {len(schedule_files)} schedule files")

    # Process each file
    total_extractions = 0
    for file_path in schedule_files[:10]:  # Process top 10 largest files
        extractions = extractor.process_file(file_path)
        total_extractions += extractions

    # Generate summary
    summary = extractor.generate_summary()

    print(f"\n🎊 EXTRACTION COMPLETE!")
    print(f"✅ Successfully extracted {total_extractions} tariff sheets")
    print(f"✅ Data exported to: {extractor.output_dir}/")
    print(f"✅ This is actual DUoS charging data - not just metadata!")

    return summary


if __name__ == "__main__":
    summary = main()
