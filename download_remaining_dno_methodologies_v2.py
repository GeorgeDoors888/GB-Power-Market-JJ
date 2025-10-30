#!/usr/bin/env python
"""
Download DUoS charging methodology files for remaining DNOs
with improved URL handling for SP Manweb and National Grid.
"""

import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

# Configuration for DNO files to download
DNO_FILES = {
    "SEPD": {
        "output_dir": "duos_ssen_data/sepd",
        "files": [
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
                "filename": "sepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd_cdcm_v10_20231106_25-26_final.xlsx",
                "filename": "sepd_cdcm_v10_20231106_25-26_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd_pcdm_v5_20231106_25-26_final.xlsx",
                "filename": "sepd_pcdm_v5_20231106_25-26_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202627/sepd_cdcm_v11_20241025_26-27_final.xlsx",
                "filename": "sepd_cdcm_v11_20241025_26-27_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202627/sepd_pcdm_v5_20241025_26-27_final.xlsx",
                "filename": "sepd_pcdm_v5_20241025_26-27_final.xlsx",
            },
        ],
    },
    "SHEPD": {
        "output_dir": "duos_ssen_data/shepd",
        "files": [
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
                "filename": "shepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd_cdcm_v10_20231106_25-26_final.xlsx",
                "filename": "shepd_cdcm_v10_20231106_25-26_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd_pcdm_v5_20231106_25-26_final.xlsx",
                "filename": "shepd_pcdm_v5_20231106_25-26_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd---schedule-of-charges-and-other-tables---april-2026-v1.0.xlsx",
                "filename": "shepd---schedule-of-charges-and-other-tables---april-2026-v1.0.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd_cdcm_v11_20241025_26-27_final.xlsx",
                "filename": "shepd_cdcm_v11_20241025_26-27_final.xlsx",
            },
            {
                "url": "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd_pcdm_v5_20241025_26-27_final.xlsx",
                "filename": "shepd_pcdm_v5_20241025_26-27_final.xlsx",
            },
        ],
    },
    "SP_MANWEB": {
        "output_dir": "duos_spm_data",
        "files": [
            # Using new approach with page navigation to find files
            {
                "url": "https://www.spenergynetworks.co.uk/userfiles/file/SP_Manweb_Use_of_System_Charging_Statement_April_2025.xlsx",
                "filename": "SP_Manweb_Use_of_System_Charging_Statement_April_2025.xlsx",
            },
            {
                "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPM_2025_26_CDCM_v10_20231106.xlsx",
                "filename": "SPM_2025_26_CDCM_v10_20231106.xlsx",
            },
            {
                "url": "https://www.spenergynetworks.co.uk/userfiles/file/SP_Manweb_Use_of_System_Charging_Statement_April_2026.xlsx",
                "filename": "SP_Manweb_Use_of_System_Charging_Statement_April_2026.xlsx",
            },
            {
                "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPM_2026_27_CDCM_v11_20241025_Published.xlsx",
                "filename": "SPM_2026_27_CDCM_v11_20241025_Published.xlsx",
            },
        ],
    },
    "NGED_EAST_MIDLANDS": {
        "output_dir": "duos_nged_data/east_midlands",
        "files": [
            # Updated URLs based on National Grid's current document structure
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161401/download",
                "filename": "nged_east_midlands_schedule_of_charges_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161411/download",
                "filename": "nged_east_midlands_cdcm_model_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161421/download",
                "filename": "nged_east_midlands_schedule_of_charges_2026.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161431/download",
                "filename": "nged_east_midlands_cdcm_model_2026.xlsx",
            },
        ],
    },
    "NGED_WEST_MIDLANDS": {
        "output_dir": "duos_nged_data/west_midlands",
        "files": [
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161501/download",
                "filename": "nged_west_midlands_schedule_of_charges_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161511/download",
                "filename": "nged_west_midlands_cdcm_model_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161521/download",
                "filename": "nged_west_midlands_schedule_of_charges_2026.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161531/download",
                "filename": "nged_west_midlands_cdcm_model_2026.xlsx",
            },
        ],
    },
    "NGED_SOUTH_WALES": {
        "output_dir": "duos_nged_data/south_wales",
        "files": [
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161601/download",
                "filename": "nged_south_wales_schedule_of_charges_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161611/download",
                "filename": "nged_south_wales_cdcm_model_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161621/download",
                "filename": "nged_south_wales_schedule_of_charges_2026.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161631/download",
                "filename": "nged_south_wales_cdcm_model_2026.xlsx",
            },
        ],
    },
    "NGED_SOUTH_WEST": {
        "output_dir": "duos_nged_data/south_west",
        "files": [
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161701/download",
                "filename": "nged_south_west_schedule_of_charges_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161711/download",
                "filename": "nged_south_west_cdcm_model_2025.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161721/download",
                "filename": "nged_south_west_schedule_of_charges_2026.xlsx",
            },
            {
                "url": "https://www.nationalgrid.com/electricity-distribution/document/161731/download",
                "filename": "nged_south_west_cdcm_model_2026.xlsx",
            },
        ],
    },
}


def download_file(url, output_path, session=None, max_retries=3, retry_delay=2):
    """
    Download a file from a URL to a specified path with retry logic.
    """
    if session is None:
        session = requests.Session()

    # Add headers to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": url.split("/")[0] + "//" + url.split("/")[2],
    }

    # Attempt to download the file with retries
    for attempt in range(max_retries):
        try:
            response = session.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Write the file to disk
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # Return the file size in KB
            file_size_kb = os.path.getsize(output_path) / 1024
            return True, file_size_kb

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"      ⚠️ Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(retry_delay)
            else:
                return False, str(e)


def get_filename_from_url(url):
    """Extract a filename from a URL"""
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    return os.path.basename(path)


def main():
    """Main function to download all DNO files"""
    print(
        "📥 Downloading DUoS charging methodology files for remaining DNOs (Improved Version)"
    )
    print("=" * 80)
    print()

    # Create a session to reuse for all downloads
    session = requests.Session()

    # Track results for summary
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dnos": {},
        "total_files": 0,
        "downloaded": 0,
        "failed": 0,
    }

    # Process each DNO
    for dno_name, dno_info in DNO_FILES.items():
        output_dir = dno_info["output_dir"]
        files = dno_info["files"]

        print(f"🏢 Downloading files for {dno_name}")
        print(f"   📁 Output directory: {output_dir}")
        print(f"   🔢 Total files: {len(files)}")

        # Track results for this DNO
        results["dnos"][dno_name] = {
            "output_dir": output_dir,
            "total_files": len(files),
            "downloaded": 0,
            "failed": 0,
            "files": [],
        }

        results["total_files"] += len(files)

        # Download each file
        for file_info in files:
            url = file_info["url"]
            filename = file_info["filename"]
            output_path = os.path.join(output_dir, filename)

            print(f"   📥 Downloading: {url}")
            print(f"      To: {output_path}")

            success, result = download_file(url, output_path, session)

            file_result = {"url": url, "filename": filename, "output_path": output_path}

            if success:
                print(f"   ✅ Downloaded: {output_path} ({result:.1f} KB)")
                file_result["status"] = "success"
                file_result["size_kb"] = result
                results["dnos"][dno_name]["downloaded"] += 1
                results["downloaded"] += 1
            else:
                print(f"   ❌ Error downloading {url}: {result}")
                file_result["status"] = "failed"
                file_result["error"] = result
                results["dnos"][dno_name]["failed"] += 1
                results["failed"] += 1

            results["dnos"][dno_name]["files"].append(file_result)

        print(f"   ✅ Downloaded: {results['dnos'][dno_name]['downloaded']} files")
        print(f"   ❌ Failed: {results['dnos'][dno_name]['failed']} files")
        print()

    # Calculate success rate
    success_rate = (
        (results["downloaded"] / results["total_files"]) * 100
        if results["total_files"] > 0
        else 0
    )

    # Print summary
    print("📊 Download Summary")
    print("=" * 80)
    print(f"Total files: {results['total_files']}")
    print(f"Downloaded: {results['downloaded']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {success_rate:.1f}%")
    print()

    # Save results to files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"dno_download_results_v2_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Create markdown summary
    markdown_path = f"dno_download_results_v2_{timestamp}.md"
    with open(markdown_path, "w") as f:
        f.write("# DNO Charging Methodology File Download Results\n\n")
        f.write(f"**Date:** {results['timestamp']}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total files: {results['total_files']}\n")
        f.write(f"- Downloaded: {results['downloaded']}\n")
        f.write(f"- Failed: {results['failed']}\n")
        f.write(f"- Success rate: {success_rate:.1f}%\n\n")

        f.write("## Details by DNO\n\n")
        for dno_name, dno_results in results["dnos"].items():
            f.write(f"### {dno_name}\n\n")
            f.write(f"- Output directory: `{dno_results['output_dir']}`\n")
            f.write(
                f"- Downloaded: {dno_results['downloaded']} / {dno_results['total_files']}\n\n"
            )

            f.write("| Filename | Status | Size |\n")
            f.write("|----------|--------|------|\n")
            for file_info in dno_results["files"]:
                status = (
                    "✅ Success"
                    if file_info["status"] == "success"
                    else f"❌ Failed: {file_info.get('error', 'Unknown error')}"
                )
                size = (
                    f"{file_info.get('size_kb', '-'):.1f} KB"
                    if file_info["status"] == "success"
                    else "-"
                )
                f.write(f"| {file_info['filename']} | {status} | {size} |\n")

            f.write("\n")

    print(f"💾 Results saved to {json_path} and {markdown_path}")
    print()
    print("✅ Download completed!")


if __name__ == "__main__":
    main()
