#!/usr/bin/env python3
"""
DNO DUoS Data ZIP Archive Creator for Google Sheets
--------------------------------------------------
Creates a ZIP file containing all CSV files in the Google Sheets-optimized
format for easy sharing and uploading to Google Sheets.

This tool:
1. Finds all CSV files in the gsheets_csv directory
2. Creates a well-organized ZIP file with all CSV data
3. Provides clear instructions for manual upload to Google Sheets
"""

import argparse
import datetime
import os
import shutil
import zipfile
from pathlib import Path

import pandas as pd


def create_zip_file(csv_dir, output_path=None):
    """Create a ZIP file containing all CSV files in the directory structure."""
    # Get timestamp for unique filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"DNO_DUoS_Sheets_Data_{timestamp}.zip"

    if output_path:
        zip_filename = os.path.join(output_path, zip_filename)

    print(f"\n📦 CREATING ZIP FILE: {zip_filename}")
    print("========================================")

    csv_path = Path(csv_dir)
    if not csv_path.exists():
        print(f"❌ CSV directory not found: {csv_dir}")
        return None

    # Track all files to be included in the ZIP
    files_added = []

    # Create the ZIP file
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add main CSV files
        for file in csv_path.glob("*.csv"):
            print(f"Adding file: {file.name}")
            zipf.write(file, file.name)
            files_added.append(file.name)

        # Add files from by_dno directory
        by_dno_path = csv_path / "by_dno"
        if by_dno_path.exists():
            for file in by_dno_path.glob("*.csv"):
                arcname = f"by_dno/{file.name}"
                print(f"Adding file: {arcname}")
                zipf.write(file, arcname)
                files_added.append(arcname)

        # Add files from by_year directory
        by_year_path = csv_path / "by_year"
        if by_year_path.exists():
            for file in by_year_path.glob("*.csv"):
                arcname = f"by_year/{file.name}"
                print(f"Adding file: {arcname}")
                zipf.write(file, arcname)
                files_added.append(arcname)

        # Create and add README file with instructions
        readme_content = create_readme(files_added, csv_dir)
        zipf.writestr("README.txt", readme_content)
        print(f"Adding file: README.txt")

        # Create and add an index HTML file for easy navigation
        html_index = create_html_index(files_added)
        zipf.writestr("index.html", html_index)
        print(f"Adding file: index.html")

    # Make a copy in the outputs directory for convenience
    try:
        outputs_dir = os.path.join(
            os.path.dirname(os.path.dirname(csv_path)), "outputs"
        )
        os.makedirs(outputs_dir, exist_ok=True)
        output_zip = os.path.join(outputs_dir, os.path.basename(zip_filename))
        shutil.copy(zip_filename, output_zip)
        print(f"\n📂 Copy saved in outputs: {os.path.abspath(output_zip)}")
    except Exception as e:
        print(f"Note: Could not save copy to outputs directory: {str(e)}")

    print("\n✅ ZIP file created successfully!")
    print(f"📂 Location: {os.path.abspath(zip_filename)}")

    return zip_filename


def create_readme(files_list, csv_dir):
    """Create a README text file with instructions."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    readme = f"""
DNO DUoS DATA FOR GOOGLE SHEETS
===============================
Created: {timestamp}

This ZIP file contains CSV files optimized for Google Sheets with the DNO Distribution Use of System (DUoS) charges data.

FILES INCLUDED:
--------------
{len(files_list)} total files in this archive:

"""

    # Group files by directory
    main_files = [f for f in files_list if "/" not in f]
    by_dno_files = [f for f in files_list if f.startswith("by_dno/")]
    by_year_files = [f for f in files_list if f.startswith("by_year/")]

    # Add main files
    readme += "MAIN DATA FILES:\n"
    for file in main_files:
        readme += f"- {file}\n"

    # Add by_year files
    if by_year_files:
        readme += "\nYEAR-SPECIFIC FILES:\n"
        for file in by_year_files:
            readme += f"- {file}\n"

    # Add by_dno files
    if by_dno_files:
        readme += "\nDNO-SPECIFIC FILES:\n"
        for file in by_dno_files:
            readme += f"- {file}\n"

    # Add instructions
    readme += """
UPLOAD INSTRUCTIONS:
------------------
OPTION 1 - UPLOAD TO GOOGLE DRIVE:
1. Go to Google Drive (https://drive.google.com)
2. Create a new folder for the DUoS data
3. Upload this ZIP file to that folder
4. Right-click the ZIP file in Google Drive and select "Open with" > "Google Workspace"
5. The ZIP file will be extracted and CSV files will be available to open with Google Sheets

OPTION 2 - MANUAL IMPORT TO GOOGLE SHEETS:
1. Extract this ZIP file on your computer
2. Go to Google Sheets (https://sheets.new) to create a new spreadsheet
3. Click on File > Import > Upload > Select the CSV files you want to import
4. Choose import options (recommended: "Replace spreadsheet" for the first file)
5. For additional files, use File > Import again but choose "Insert new sheet(s)"

OPTION 3 - USE IN MICROSOFT EXCEL:
1. Extract this ZIP file on your computer
2. Open Microsoft Excel
3. Use File > Open to open each CSV file
4. Save as Excel workbook (.xlsx) if desired

ABOUT THIS DATA:
--------------
This dataset contains Distribution Use of System (DUoS) charges from UK Distribution Network Operators (DNOs).
The data includes:
- Time-based charging bands (Red, Amber, Green)
- Unit rates (p/kWh) for each band
- Fixed charges
- Data organized by DNO and year

For more information about the data structure, see the DNO_Reference CSV file.
"""

    return readme


def create_html_index(files_list):
    """Create a simple HTML index file to navigate the CSV files."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DNO DUoS Data Index</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 20px; }}
        .file-list {{ margin-left: 20px; }}
        .file-item {{ margin: 5px 0; }}
        .file-link {{ text-decoration: none; color: #2980b9; }}
        .file-link:hover {{ text-decoration: underline; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #eee; border-radius: 5px; }}
        .instructions {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; }}
    </style>
</head>
<body>
    <h1>DNO DUoS Data for Google Sheets</h1>
    <p>Created: {timestamp}</p>
    
    <div class="section">
        <h2>Data Files</h2>
"""

    # Group files by directory
    main_files = [f for f in files_list if "/" not in f]
    by_dno_files = [f for f in files_list if f.startswith("by_dno/")]
    by_year_files = [f for f in files_list if f.startswith("by_year/")]

    # Add main files
    html += """
        <h3>Main Data Files</h3>
        <div class="file-list">
"""

    for file in main_files:
        html += f'            <div class="file-item"><a href="{file}" class="file-link">{file}</a></div>\n'

    html += "        </div>\n"

    # Add by_year files
    if by_year_files:
        html += """
        <h3>Year-Specific Files</h3>
        <div class="file-list">
"""
        for file in by_year_files:
            file_name = file.split("/")[-1]
            html += f'            <div class="file-item"><a href="{file}" class="file-link">{file_name}</a></div>\n'

        html += "        </div>\n"

    # Add by_dno files
    if by_dno_files:
        html += """
        <h3>DNO-Specific Files</h3>
        <div class="file-list">
"""
        for file in by_dno_files:
            file_name = file.split("/")[-1]
            html += f'            <div class="file-item"><a href="{file}" class="file-link">{file_name}</a></div>\n'

        html += "        </div>\n"

    # Add instructions
    html += """
    </div>
    
    <div class="section instructions">
        <h2>Upload Instructions</h2>
        
        <h3>Option 1 - Upload to Google Drive</h3>
        <ol>
            <li>Go to <a href="https://drive.google.com" target="_blank">Google Drive</a></li>
            <li>Create a new folder for the DUoS data</li>
            <li>Upload all CSV files to that folder</li>
            <li>When opening each file, Google will automatically use Sheets</li>
        </ol>
        
        <h3>Option 2 - Manual Import to Google Sheets</h3>
        <ol>
            <li>Go to <a href="https://sheets.new" target="_blank">Google Sheets</a> to create a new spreadsheet</li>
            <li>Click on File > Import > Upload > Select a CSV file</li>
            <li>Choose import options (recommended: "Replace spreadsheet" for the first file)</li>
            <li>For additional files, use File > Import again but choose "Insert new sheet(s)"</li>
        </ol>
        
        <h3>Option 3 - Use in Microsoft Excel</h3>
        <ol>
            <li>Open Microsoft Excel</li>
            <li>Use File > Open to open each CSV file</li>
            <li>Save as Excel workbook (.xlsx) if desired</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>About This Data</h2>
        <p>This dataset contains Distribution Use of System (DUoS) charges from UK Distribution Network Operators (DNOs).</p>
        <p>The data includes:</p>
        <ul>
            <li>Time-based charging bands (Red, Amber, Green)</li>
            <li>Unit rates (p/kWh) for each band</li>
            <li>Fixed charges</li>
            <li>Data organized by DNO and year</li>
        </ul>
        <p>For more information about the data structure, see the DNO_Reference CSV file.</p>
    </div>
    
    <footer style="margin-top: 30px; text-align: center; color: #7f8c8d; font-size: 0.9em;">
        Generated by DUoS Data Zipper Tool
    </footer>
</body>
</html>
"""

    return html


def find_csv_directory():
    """Try to find the gsheets_csv directory automatically."""
    possible_paths = [
        "duos_outputs2/gsheets_csv",
        "duos_outputs/gsheets_csv",
        "outputs/gsheets_csv",
        "gsheets_csv",
    ]

    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            return path

    return None


def main():
    """Main function to create the ZIP file."""
    parser = argparse.ArgumentParser(
        description="Create a ZIP file with DNO DUoS data optimized for Google Sheets"
    )
    parser.add_argument(
        "--csv-dir", dest="csv_dir", help="Directory containing the CSV files"
    )
    parser.add_argument(
        "--output", dest="output_path", help="Output directory for the ZIP file"
    )
    args = parser.parse_args()

    print("\n📦 DNO DUoS DATA ZIP CREATOR FOR GOOGLE SHEETS")
    print("=============================================")

    # Determine CSV directory
    csv_dir = args.csv_dir
    if not csv_dir:
        csv_dir = find_csv_directory()
        if not csv_dir:
            csv_dir = "duos_outputs2/gsheets_csv"  # Default path

    print(f"🔍 Using CSV directory: {csv_dir}")

    # Create the ZIP file
    zip_file = create_zip_file(csv_dir, args.output_path)

    if zip_file:
        print("\n📋 NEXT STEPS:")
        print("1. The ZIP file contains all CSV files organized in folders")
        print("2. Upload this ZIP file to Google Drive")
        print("3. In Google Drive, right-click and extract with Google Workspace")
        print(
            "4. Alternatively, extract locally and upload individual files to Google Sheets"
        )
        print(
            "\n📚 Full instructions are included in the README.txt file inside the ZIP"
        )


if __name__ == "__main__":
    main()
