#!/usr/bin/env python
"""
Script to find SP Manweb charging methodology documents
by scraping their website.
"""

import json
import os
import re
import time
from datetime import datetime

import requests

# URL for SP Energy Networks charging statements page
BASE_URL = (
    "https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx"
)

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.spenergynetworks.co.uk/",
}

# Try to download files directly with these predefined URLs
SP_MANWEB_FILES = [
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPManweb_Use_of_System_Charging_Statement_April_2025.xlsx",
        "filename": "SPManweb_Use_of_System_Charging_Statement_April_2025.xlsx",
        "description": "SP Manweb Schedule of Charges 2025-26",
    },
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPM_2025_26_CDCM_v10_20231106.xlsx",
        "filename": "SPM_2025_26_CDCM_v10_20231106.xlsx",
        "description": "SP Manweb CDCM Model 2025-26",
    },
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPManweb_Use_of_System_Charging_Statement_April_2026.xlsx",
        "filename": "SPManweb_Use_of_System_Charging_Statement_April_2026.xlsx",
        "description": "SP Manweb Schedule of Charges 2026-27",
    },
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SPM_2026_27_CDCM_v11_20241025_Published.xlsx",
        "filename": "SPM_2026_27_CDCM_v11_20241025_Published.xlsx",
        "description": "SP Manweb CDCM Model 2026-27",
    },
    # Alternative URLs
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SP_Manweb_Use_of_System_Charging_Statement_April_2025.xlsx",
        "filename": "SP_Manweb_Use_of_System_Charging_Statement_April_2025.xlsx",
        "description": "SP Manweb Schedule of Charges 2025-26 (Alt)",
    },
    {
        "url": "https://www.spenergynetworks.co.uk/userfiles/file/SP_Manweb_Use_of_System_Charging_Statement_April_2026.xlsx",
        "filename": "SP_Manweb_Use_of_System_Charging_Statement_April_2026.xlsx",
        "description": "SP Manweb Schedule of Charges 2026-27 (Alt)",
    },
]


def download_file(url, output_path, max_retries=3, retry_delay=2):
    """Download a file from a URL to a specified path."""
    for attempt in range(max_retries):
        try:
            print(f"   📥 Downloading: {url}")
            print(f"      To: {output_path}")

            response = requests.get(url, headers=HEADERS, stream=True, timeout=30)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size_kb = os.path.getsize(output_path) / 1024
            print(f"   ✅ Downloaded: {output_path} ({file_size_kb:.1f} KB)")
            return True, file_size_kb

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"      ⚠️ Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(retry_delay)
            else:
                print(f"   ❌ Error downloading {url}: {e}")
                return False, str(e)


def main():
    print("📥 Downloading SP Manweb charging methodology files (Direct URLs)")
    print("=" * 80)

    output_dir = "duos_spm_data"
    os.makedirs(output_dir, exist_ok=True)

    print(f"📁 Output directory: {output_dir}")
    print(f"🔢 Total files: {len(SP_MANWEB_FILES)}")

    # Results tracking
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_files": len(SP_MANWEB_FILES),
        "downloaded": 0,
        "failed": 0,
        "files": [],
    }

    # Download each file
    for file_info in SP_MANWEB_FILES:
        url = file_info["url"]
        filename = file_info["filename"]
        description = file_info["description"]
        output_path = os.path.join(output_dir, filename)

        print(f"🔍 Trying: {description}")
        success, result = download_file(url, output_path)

        file_result = {
            "url": url,
            "filename": filename,
            "description": description,
            "output_path": output_path,
        }

        if success:
            file_result["status"] = "success"
            file_result["size_kb"] = result
            results["downloaded"] += 1
        else:
            file_result["status"] = "failed"
            file_result["error"] = result
            results["failed"] += 1

        results["files"].append(file_result)

    # Calculate success rate
    success_rate = (
        (results["downloaded"] / results["total_files"]) * 100
        if results["total_files"] > 0
        else 0
    )

    # Print summary
    print()
    print("📊 Download Summary")
    print("=" * 80)
    print(f"Total files: {results['total_files']}")
    print(f"Downloaded: {results['downloaded']}")
    print(f"Failed: {results['failed']}")
    print(f"Success rate: {success_rate:.1f}%")

    # Save results to files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"spm_download_results_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # Create markdown summary
    markdown_path = f"spm_download_results_{timestamp}.md"
    with open(markdown_path, "w") as f:
        f.write("# SP Manweb Charging Methodology File Download Results\n\n")
        f.write(f"**Date:** {results['timestamp']}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- Total files: {results['total_files']}\n")
        f.write(f"- Downloaded: {results['downloaded']}\n")
        f.write(f"- Failed: {results['failed']}\n")
        f.write(f"- Success rate: {success_rate:.1f}%\n\n")

        f.write("## Details\n\n")
        f.write("| Description | Filename | Status | Size |\n")
        f.write("|-------------|----------|--------|------|\n")

        for file_info in results["files"]:
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

            f.write(
                f"| {file_info['description']} | {file_info['filename']} | {status} | {size} |\n"
            )

    print(f"💾 Results saved to {json_path} and {markdown_path}")
    print()
    print("✅ Download completed!")


if __name__ == "__main__":
    main()
