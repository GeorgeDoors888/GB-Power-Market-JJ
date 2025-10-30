#!/usr/bin/env python
"""
Watermark Analysis Tool

This script analyzes the watermark JSON files to provide insights about
data freshness across different datasets in the BigQuery pipeline.
"""

import argparse
import datetime
import glob
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze watermark files to track data freshness"
    )
    parser.add_argument(
        "--dir",
        default=os.getcwd(),
        help="Directory containing watermark files (default: current directory)",
    )
    parser.add_argument(
        "--pattern",
        default="watermarks_*.json",
        help="File pattern to match (default: watermarks_*.json)",
    )
    parser.add_argument(
        "--output",
        default="watermark_analysis_report.md",
        help="Output file for the report (default: watermark_analysis_report.md)",
    )
    return parser.parse_args()


def load_watermark_files(directory: str, pattern: str) -> List[Dict[str, Any]]:
    """Load all watermark files from the specified directory matching the pattern."""
    watermark_files = []
    file_paths = glob.glob(os.path.join(directory, pattern))

    for file_path in file_paths:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                # Add metadata about the file itself
                file_stat = os.stat(file_path)
                data["_file_metadata"] = {
                    "filename": os.path.basename(file_path),
                    "modified_time": datetime.datetime.fromtimestamp(
                        file_stat.st_mtime
                    ).isoformat(),
                    "size_bytes": file_stat.st_size,
                }
                watermark_files.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading {file_path}: {e}")

    return watermark_files


def analyze_data_freshness(watermarks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the data freshness from watermark files."""
    tables_latest = {}
    tables_history = defaultdict(list)

    # Collect all watermarks for each table
    for wm_file in watermarks:
        file_date = datetime.datetime.fromisoformat(
            wm_file["_file_metadata"]["modified_time"]
        )

        for table_name, table_data in wm_file.items():
            if table_name == "_file_metadata":
                continue

            # Skip if not a proper table entry
            if not isinstance(table_data, dict):
                continue

            # Adapt to the actual watermark structure
            latest_data = table_data.get("max__ingested_utc") or table_data.get(
                "last_modified_time"
            )
            record_count = table_data.get("row_count", "Unknown")

            # Store the table data with the file date
            tables_history[table_name].append(
                {
                    "file_date": file_date,
                    "latest_data": latest_data,
                    "record_count": record_count,
                    "source": wm_file["_file_metadata"]["filename"],
                    "size_bytes": table_data.get("size_bytes", 0),
                }
            )

    # Find the latest watermark for each table
    for table_name, history in tables_history.items():
        # Sort by file date (newest first)
        sorted_history = sorted(history, key=lambda x: x["file_date"], reverse=True)
        tables_latest[table_name] = sorted_history[0]

        # Add a data age calculation
        if tables_latest[table_name]["latest_data"]:
            try:
                latest_data_time = datetime.datetime.fromisoformat(
                    tables_latest[table_name]["latest_data"].replace("Z", "+00:00")
                )
                now = datetime.datetime.now(datetime.timezone.utc)
                age_hours = (now - latest_data_time).total_seconds() / 3600
                tables_latest[table_name]["age_hours"] = age_hours
            except (ValueError, TypeError):
                tables_latest[table_name]["age_hours"] = None

    return {"tables_latest": tables_latest, "tables_history": dict(tables_history)}


def generate_freshness_report(analysis: Dict[str, Any], output_file: str) -> None:
    """Generate a markdown report of the data freshness analysis."""
    tables_latest = analysis["tables_latest"]

    with open(output_file, "w") as f:
        f.write("# Data Freshness Analysis Report\n\n")
        f.write(f"Generated on: {datetime.datetime.now().isoformat()}\n\n")

        f.write("## Tables Freshness Summary\n\n")
        f.write(
            "| Table Name | Latest Data | Age (hours) | Record Count | Size (GB) | Source File |\n"
        )
        f.write(
            "|------------|-------------|-------------|--------------|-----------|-------------|\n"
        )

        # Sort tables by age (stalest first)
        sorted_tables = sorted(
            [
                (name, data)
                for name, data in tables_latest.items()
                if data.get("age_hours") is not None
            ],
            key=lambda x: x[1]["age_hours"],
            reverse=True,
        )

        # Add tables with unknown age at the end
        sorted_tables += [
            (name, data)
            for name, data in tables_latest.items()
            if data.get("age_hours") is None
        ]

        total_size_bytes = 0
        total_records = 0

        for table_name, data in sorted_tables:
            age_display = (
                f"{data['age_hours']:.1f}"
                if data.get("age_hours") is not None
                else "Unknown"
            )
            latest_data = data.get("latest_data", "Unknown")
            record_count = data.get("record_count", "Unknown")

            # Calculate size in GB if available
            size_bytes = data.get("size_bytes", 0)
            if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                size_gb = size_bytes / (1024 * 1024 * 1024)
                size_display = f"{size_gb:.2f}"
                total_size_bytes += size_bytes
            else:
                size_display = "Unknown"

            # Add to total records if available
            if isinstance(record_count, (int, float)):
                total_records += record_count

            source = data.get("source", "Unknown")

            f.write(
                f"| {table_name} | {latest_data} | {age_display} | {record_count:,} | {size_display} | {source} |\n"
            )

        # Add summary row
        total_size_gb = (
            total_size_bytes / (1024 * 1024 * 1024) if total_size_bytes > 0 else 0
        )
        f.write(
            f"|**TOTAL**|**N/A**|**N/A**|**{total_records:,}**|**{total_size_gb:.2f}**|**N/A**|\n\n"
        )

        f.write("\n## Data Freshness Recommendations\n\n")

        # Identify stale tables (older than 24 hours)
        stale_tables = [
            (name, data)
            for name, data in sorted_tables
            if data.get("age_hours") is not None and data["age_hours"] > 24
        ]

        if stale_tables:
            f.write("### Stale Tables (older than 24 hours)\n\n")
            for table_name, data in stale_tables:
                f.write(
                    f"- **{table_name}**: {data['age_hours']:.1f} hours old (last updated: {data['latest_data']})\n"
                )

            f.write(
                "\nRecommendation: Consider refreshing the above tables to ensure data currency.\n\n"
            )
        else:
            f.write(
                "All tables appear to have been updated within the last 24 hours. Data freshness is good.\n\n"
            )

        # Unknown age tables
        unknown_age_tables = [
            name
            for name, data in tables_latest.items()
            if data.get("age_hours") is None
        ]

        if unknown_age_tables:
            f.write("### Tables with Unknown Age\n\n")
            for table_name in unknown_age_tables:
                f.write(f"- {table_name}\n")

            f.write(
                "\nRecommendation: Investigate these tables to ensure proper watermark tracking.\n\n"
            )

        # Storage analysis
        f.write("## Storage Analysis\n\n")

        # Sort tables by size (largest first)
        size_sorted_tables = sorted(
            [
                (name, data)
                for name, data in tables_latest.items()
                if data.get("size_bytes", 0) > 0
            ],
            key=lambda x: x[1]["size_bytes"],
            reverse=True,
        )

        if size_sorted_tables:
            f.write("### Largest Tables\n\n")
            for table_name, data in size_sorted_tables[:5]:  # Top 5 largest tables
                size_gb = data["size_bytes"] / (1024 * 1024 * 1024)
                f.write(
                    f"- **{table_name}**: {size_gb:.2f} GB ({data['record_count']:,} records)\n"
                )

            f.write(
                f"\nTotal storage across all tables: **{total_size_gb:.2f} GB**\n\n"
            )

        f.write("## Watermark Files Used\n\n")
        unique_files = set()
        for table_data in tables_latest.values():
            if "source" in table_data:
                unique_files.add(table_data["source"])

        for file_name in sorted(unique_files):
            f.write(f"- {file_name}\n")


def main():
    """Main execution function."""
    args = parse_arguments()
    watermarks = load_watermark_files(args.dir, args.pattern)

    if not watermarks:
        print(f"No watermark files found matching '{args.pattern}' in '{args.dir}'")
        return

    print(f"Loaded {len(watermarks)} watermark files")
    analysis = analyze_data_freshness(watermarks)
    generate_freshness_report(analysis, args.output)
    print(f"Analysis complete. Report written to {args.output}")


if __name__ == "__main__":
    main()
