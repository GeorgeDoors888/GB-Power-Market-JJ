#!/usr/bin/env python3
"""
Download DUoS charging methodology Excel files for remaining DNOs
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd
import requests

# Define the output directories
BASE_DIR = Path(".")
SSEN_DIR = BASE_DIR / "duos_ssen_data"
SPM_DIR = BASE_DIR / "duos_spm_data"
NGED_DIR = BASE_DIR / "duos_nged_data"

# Create directories if they don't exist
SSEN_DIR.mkdir(exist_ok=True)
SPM_DIR.mkdir(exist_ok=True)
NGED_DIR.mkdir(exist_ok=True)

# DNO file URLs to download
DNO_FILES = {
    "SEPD": {
        "dir": SSEN_DIR / "sepd",
        "files": [
            # 2025-2026
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd_cdcm_v10_20231106_25-26_final.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202526/sepd_pcdm_v5_20231106_25-26_final.xlsx",
            # 2026-2027
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202627/sepd---schedule-of-charges-and-other-tables---april-2026-v1.0.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202627/sepd_cdcm_v11_20241025_26-27_final.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-sepd/202627/sepd_pcdm_v5_20241025_26-27_final.xlsx",
        ],
    },
    "SHEPD": {
        "dir": SSEN_DIR / "shepd",
        "files": [
            # 2025-2026
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd---schedule-of-charges-and-other-tables---april-2025-v0.2.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd_cdcm_v10_20231106_25-26_final.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202526/shepd_pcdm_v5_20231106_25-26_final.xlsx",
            # 2026-2027
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd---schedule-of-charges-and-other-tables---april-2026-v1.0.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd_cdcm_v11_20241025_26-27_final.xlsx",
            "https://www.ssen.co.uk/globalassets/library/charging-statements-shepd/202627/shepd_pcdm_v5_20241025_26-27_final.xlsx",
        ],
    },
    "SP_MANWEB": {
        "dir": SPM_DIR,
        "files": [
            # 2025
            "https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx",
            "https://www.scottishpower.com/userfiles/file/SPM_2025_26_CDCM_v10_20231106.xlsx",
            # 2026
            "https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx",
            "https://www.scottishpower.com/userfiles/file/SPM%202026_27%20CDCM_v11_20241025_Published.xlsx",
        ],
    },
    "NGED_EAST_MIDLANDS": {
        "dir": NGED_DIR / "east_midlands",
        "files": [
            # 2025
            "https://www.nationalgrid.com/document/160206/download",  # Schedule of Charges 2025
            "https://www.nationalgrid.com/document/160196/download",  # CDCM Model 2025
            # 2026
            "https://www.nationalgrid.com/document/161711/download",  # Schedule of Charges 2026
            "https://www.nationalgrid.com/document/161716/download",  # CDCM Model 2026
        ],
    },
    "NGED_WEST_MIDLANDS": {
        "dir": NGED_DIR / "west_midlands",
        "files": [
            # 2025
            "https://www.nationalgrid.com/document/160211/download",  # Schedule of Charges 2025
            "https://www.nationalgrid.com/document/160201/download",  # CDCM Model 2025
            # 2026
            "https://www.nationalgrid.com/document/161726/download",  # Schedule of Charges 2026
            "https://www.nationalgrid.com/document/161731/download",  # CDCM Model 2026
        ],
    },
    "NGED_SOUTH_WALES": {
        "dir": NGED_DIR / "south_wales",
        "files": [
            # 2025
            "https://www.nationalgrid.com/document/160216/download",  # Schedule of Charges 2025
            "https://www.nationalgrid.com/document/160201/download",  # CDCM Model 2025
            # 2026
            "https://www.nationalgrid.com/document/161741/download",  # Schedule of Charges 2026
            "https://www.nationalgrid.com/document/161746/download",  # CDCM Model 2026
        ],
    },
    "NGED_SOUTH_WEST": {
        "dir": NGED_DIR / "south_west",
        "files": [
            # 2025
            "https://www.nationalgrid.com/document/160221/download",  # Schedule of Charges 2025
            "https://www.nationalgrid.com/document/160206/download",  # CDCM Model 2025
            # 2026
            "https://www.nationalgrid.com/document/161756/download",  # Schedule of Charges 2026
            "https://www.nationalgrid.com/document/161761/download",  # CDCM Model 2026
        ],
    },
}


def get_filename_from_url(url: str) -> str:
    """
    Extract filename from URL, handling special cases

    Args:
        url: URL to extract filename from

    Returns:
        Filename
    """
    # Parse URL
    parsed_url = urlparse(url)
    path = parsed_url.path

    # Extract filename from path
    filename = os.path.basename(path)

    # Handle National Grid document URLs
    if "nationalgrid.com/document" in url:
        # Extract document ID from URL
        doc_id = path.split("/")[-2]

        # Use URL format to determine document type and year
        if "160206" in url:
            return f"nged_east_midlands_schedule_of_charges_2025.xlsx"
        elif "160196" in url:
            return f"nged_east_midlands_cdcm_model_2025.xlsx"
        elif "161711" in url:
            return f"nged_east_midlands_schedule_of_charges_2026.xlsx"
        elif "161716" in url:
            return f"nged_east_midlands_cdcm_model_2026.xlsx"
        elif "160211" in url:
            return f"nged_west_midlands_schedule_of_charges_2025.xlsx"
        elif "160201" in url:
            return f"nged_west_midlands_cdcm_model_2025.xlsx"
        elif "161726" in url:
            return f"nged_west_midlands_schedule_of_charges_2026.xlsx"
        elif "161731" in url:
            return f"nged_west_midlands_cdcm_model_2026.xlsx"
        elif "160216" in url:
            return f"nged_south_wales_schedule_of_charges_2025.xlsx"
        elif "161741" in url:
            return f"nged_south_wales_schedule_of_charges_2026.xlsx"
        elif "161746" in url:
            return f"nged_south_wales_cdcm_model_2026.xlsx"
        elif "160221" in url:
            return f"nged_south_west_schedule_of_charges_2025.xlsx"
        elif "161756" in url:
            return f"nged_south_west_schedule_of_charges_2026.xlsx"
        elif "161761" in url:
            return f"nged_south_west_cdcm_model_2026.xlsx"
        else:
            return f"nged_doc_{doc_id}.xlsx"

    return filename


def download_file(url: str, output_dir: Path) -> Optional[Path]:
    """
    Download a file from a URL to a specified output directory

    Args:
        url: URL to download
        output_dir: Output directory

    Returns:
        Path to downloaded file or None if download failed
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(exist_ok=True, parents=True)

        # Get filename from URL
        filename = get_filename_from_url(url)
        output_path = output_dir / filename

        # Check if file already exists
        if output_path.exists():
            print(f"   ⚠️ File already exists: {output_path}")
            return output_path

        # Download file
        print(f"   📥 Downloading: {url}")
        print(f"      To: {output_path}")

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify file was downloaded successfully
        if output_path.exists() and output_path.stat().st_size > 0:
            print(
                f"   ✅ Downloaded: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)"
            )
            return output_path
        else:
            print(f"   ❌ Download failed: {output_path}")
            return None

    except Exception as e:
        print(f"   ❌ Error downloading {url}: {e}")
        return None


def download_all_files():
    """
    Download all files for all DNOs
    """
    print("📥 Downloading DUoS charging methodology files for remaining DNOs")
    print("=" * 80)

    results = {"download_date": datetime.now().isoformat(), "dnos": {}}

    total_files = sum(len(dno["files"]) for dno in DNO_FILES.values())
    downloaded_files = 0
    failed_files = 0

    for dno_name, dno_info in DNO_FILES.items():
        output_dir = dno_info["dir"]
        files = dno_info["files"]

        print(f"\n🏢 Downloading files for {dno_name}")
        print(f"   📁 Output directory: {output_dir}")
        print(f"   🔢 Total files: {len(files)}")

        dno_results = {
            "total_files": len(files),
            "downloaded_files": 0,
            "failed_files": 0,
            "file_details": [],
        }

        for url in files:
            result = download_file(url, output_dir)

            file_detail = {
                "url": url,
                "filename": get_filename_from_url(url) if result else None,
                "success": result is not None,
                "file_size": result.stat().st_size if result else None,
            }

            dno_results["file_details"].append(file_detail)

            if result:
                dno_results["downloaded_files"] += 1
                downloaded_files += 1
            else:
                dno_results["failed_files"] += 1
                failed_files += 1

            # Small delay to avoid overloading the server
            time.sleep(1)

        results["dnos"][dno_name] = dno_results

        print(f"   ✅ Downloaded: {dno_results['downloaded_files']} files")
        print(f"   ❌ Failed: {dno_results['failed_files']} files")

    # Save results
    with open("dno_download_results.json", "w") as f:
        import json

        json.dump(results, f, indent=2)

    # Print summary
    print("\n📊 Download Summary")
    print("=" * 80)
    print(f"Total files: {total_files}")
    print(f"Downloaded: {downloaded_files}")
    print(f"Failed: {failed_files}")
    print(f"Success rate: {downloaded_files / total_files * 100:.1f}%")

    # Create markdown summary
    md_content = f"# DUoS Charging Methodology Download Results\n\n"
    md_content += f"Download Date: {results['download_date']}\n\n"
    md_content += f"## Summary\n\n"
    md_content += f"- Total files: {total_files}\n"
    md_content += f"- Downloaded: {downloaded_files}\n"
    md_content += f"- Failed: {failed_files}\n"
    md_content += f"- Success rate: {downloaded_files / total_files * 100:.1f}%\n\n"

    for dno_name, dno_results in results["dnos"].items():
        md_content += f"## {dno_name}\n\n"
        md_content += f"- Total files: {dno_results['total_files']}\n"
        md_content += f"- Downloaded: {dno_results['downloaded_files']}\n"
        md_content += f"- Failed: {dno_results['failed_files']}\n\n"

        md_content += "### Files\n\n"
        for file_detail in dno_results["file_details"]:
            status = "✅ Downloaded" if file_detail["success"] else "❌ Failed"
            file_size = (
                f" ({file_detail['file_size'] / 1024:.1f} KB)"
                if file_detail["success"]
                else ""
            )
            md_content += f"- {status}: {file_detail['filename']}{file_size}\n"

        md_content += "\n"

    with open("dno_download_results.md", "w") as f:
        f.write(md_content)

    print(
        f"\n💾 Results saved to dno_download_results.json and dno_download_results.md"
    )


if __name__ == "__main__":
    try:
        download_all_files()
        print("\n✅ Download completed!")

    except Exception as e:
        print(f"\n❌ Error during download: {e}")
        import traceback

        traceback.print_exc()
