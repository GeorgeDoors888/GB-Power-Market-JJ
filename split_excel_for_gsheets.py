#!/usr/bin/env python3
"""
Split Excel File for Google Sheets
---------------------------------
Splits a large Excel file into smaller files more suitable for Google Sheets.
"""

import os
import sys
from datetime import datetime

import pandas as pd


def split_excel_for_google_sheets(file_path, max_rows=50000):
    """Split a large Excel file into smaller files for Google Sheets."""
    print(f"\n🔄 Splitting Excel file for Google Sheets: {file_path}")

    output_dir = os.path.dirname(file_path)
    base_name = os.path.basename(file_path).replace(".xlsx", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_base = os.path.join(output_dir, f"{base_name}_GSheets_{timestamp}")

    # Read the Excel file and extract sheet names
    print(f"📄 Reading Excel file...")
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names

    # Process each sheet
    sheet_count = len(sheet_names)
    print(f"📊 Found {sheet_count} sheets to process")

    # Group sheets into smaller files (approximately 5 sheets per file or fewer)
    max_sheets_per_file = 5
    num_files = (sheet_count + max_sheets_per_file - 1) // max_sheets_per_file

    file_sheet_map = {}

    # Group the sheets into files
    for i in range(num_files):
        start_idx = i * max_sheets_per_file
        end_idx = min((i + 1) * max_sheets_per_file, sheet_count)
        file_sheets = sheet_names[start_idx:end_idx]

        file_name = f"{output_base}_Part{i+1}.xlsx"
        file_sheet_map[file_name] = file_sheets

    # Create files with sheet subsets
    for file_name, sheets in file_sheet_map.items():
        print(f"\n📝 Creating file: {os.path.basename(file_name)}")
        print(f"   - Including sheets: {', '.join(sheets)}")

        with pd.ExcelWriter(file_name, engine="openpyxl") as writer:
            for sheet in sheets:
                print(f"   - Processing sheet: {sheet}")

                # Read the sheet
                df = pd.read_excel(file_path, sheet_name=sheet)
                rows = len(df)

                # Check if sheet is too large
                if rows > max_rows:
                    print(
                        f"   ⚠️ Sheet '{sheet}' has {rows} rows (over {max_rows} limit)"
                    )
                    print(f"   ⚠️ Splitting into multiple chunks")

                    # Split into chunks
                    chunks = (rows + max_rows - 1) // max_rows
                    for chunk in range(chunks):
                        start_row = chunk * max_rows
                        end_row = min((chunk + 1) * max_rows, rows)
                        chunk_df = df.iloc[start_row:end_row]

                        chunk_sheet_name = f"{sheet}_{chunk+1}" if chunks > 1 else sheet
                        chunk_sheet_name = chunk_sheet_name[
                            :31
                        ]  # Excel limits sheet names to 31 chars

                        chunk_df.to_excel(
                            writer, sheet_name=chunk_sheet_name, index=False
                        )
                        print(
                            f"      - Added chunk {chunk+1}/{chunks}: rows {start_row+1}-{end_row}"
                        )
                else:
                    # Sheet is small enough, add it as is
                    df.to_excel(writer, sheet_name=sheet, index=False)
                    print(f"      - Added complete sheet: {rows} rows")

    print(f"\n✅ Successfully split Excel file into {num_files} smaller files:")
    for file_name in file_sheet_map.keys():
        print(f"   - {os.path.basename(file_name)}")

    print("\n📋 INSTRUCTIONS:")
    print("   1. Upload these smaller files to Google Drive")
    print("   2. Open each with Google Sheets")
    print("   3. Use 'Save as Google Sheets' for each file")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(
            "Usage: python split_excel_for_gsheets.py <excel_file_path> [max_rows_per_sheet]"
        )
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)

    max_rows = 50000  # Default max rows per sheet
    if len(sys.argv) > 2:
        try:
            max_rows = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid max_rows value. Using default: {max_rows}")

    split_excel_for_google_sheets(file_path, max_rows)


if __name__ == "__main__":
    main()
