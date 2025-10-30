#!/usr/bin/env python
"""
Script to download all UK DNO DUoS charging methodology files
from the comprehensive guide.

This script will download files from:
1. National Grid Electricity Distribution (formerly WPD)
2. SP Manweb (Scottish Power)
3. SSEN (SHEPD & SEPD)

Usage:
    source .venv/bin/activate && python download_all_dno_duos_files.py
"""

import datetime
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="\033[1;34m%(message)s\033[0m",
)
logger = logging.getLogger(__name__)

# Constants
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"


# Create session with retry capability
def create_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
    )
    return session


def get_filename_from_url(url):
    """Extract filename from URL, handling encoded characters"""
    parsed_url = urlparse(url)
    path = unquote(parsed_url.path)
    return os.path.basename(path)


def download_file(session, url, output_path, file_name=None):
    """Download a file from a URL to a specified path"""
    if file_name is None:
        file_name = get_filename_from_url(url)

    full_path = os.path.join(output_path, file_name)

    # Check if file already exists
    if os.path.exists(full_path):
        logger.info(f"   ℹ️ File already exists: {full_path}")
        return {"status": "skipped", "path": full_path, "url": url}

    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)

    # Handle retries
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"   📥 Downloading: {url}")
            logger.info(f"      To: {full_path}")

            response = session.get(url, timeout=TIMEOUT, stream=True)
            response.raise_for_status()

            with open(full_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size_mb = os.path.getsize(full_path) / (1024 * 1024)
            logger.info(f"      ✅ Downloaded: {full_path} ({file_size_mb:.1f} MB)")
            return {
                "status": "success",
                "path": full_path,
                "url": url,
                "size_mb": file_size_mb,
            }

        except requests.exceptions.HTTPError as e:
            if attempt + 1 < MAX_RETRIES:
                logger.info(
                    f"      ⚠️ Retry {attempt+1}/{MAX_RETRIES} after error: {str(e)}"
                )
                time.sleep(RETRY_BACKOFF ** (attempt + 1))
            else:
                logger.info(f"   ❌ Error downloading {url}: {str(e)}")
                return {"status": "error", "url": url, "error": str(e)}

        except Exception as e:
            logger.info(f"   ❌ Error downloading {url}: {str(e)}")
            return {"status": "error", "url": url, "error": str(e)}


def download_nged_files():
    """Download National Grid Electricity Distribution files (formerly WPD)"""
    logger.info(
        "🏢 Downloading National Grid Electricity Distribution files (formerly WPD)"
    )
    logger.info("--------------------------------------------------------")

    output_dir = "duos_nged_data"
    session = create_session()

    # Define regions and file URLs
    regions = {
        "east_midlands": {
            "name": "East Midlands (MPAN 11)",
            "files": {
                "Schedule of Charges": [
                    {
                        "url": "https://www.nationalgrid.com/document/177846/download",
                        "file_name": "National_Grid_East_Midlands_Schedule_of_Charges_and_Other_Tables_April_2026.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172376/download",
                        "file_name": "National_Grid_East_Midlands_Schedule_of_Charges_and_Other_Tables_April_2025.xlsx",
                    },
                ],
                "CDCM Model": [
                    {
                        "url": "https://www.nationalgrid.com/document/177866/download",
                        "file_name": "National_Grid_East_Midlands_CDCM_Model_2026-27.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172396/download",
                        "file_name": "National_Grid_East_Midlands_CDCM_Model_2025-26.xlsx",
                    },
                ],
            },
        },
        "west_midlands": {
            "name": "West Midlands (MPAN 14)",
            "files": {
                "Schedule of Charges": [
                    {
                        "url": "https://www.nationalgrid.com/document/177851/download",
                        "file_name": "National_Grid_West_Midlands_Schedule_of_Charges_and_Other_Tables_April_2026.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172381/download",
                        "file_name": "National_Grid_West_Midlands_Schedule_of_Charges_and_Other_Tables_April_2025.xlsx",
                    },
                ],
                "CDCM Model": [
                    {
                        "url": "https://www.nationalgrid.com/document/177871/download",
                        "file_name": "National_Grid_West_Midlands_CDCM_Model_2026-27.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172401/download",
                        "file_name": "National_Grid_West_Midlands_CDCM_Model_2025-26.xlsx",
                    },
                ],
            },
        },
        "south_wales": {
            "name": "South Wales (MPAN 21)",
            "files": {
                "Schedule of Charges": [
                    {
                        "url": "https://www.nationalgrid.com/document/177856/download",
                        "file_name": "National_Grid_South_Wales_Schedule_of_Charges_and_Other_Tables_April_2026.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172386/download",
                        "file_name": "National_Grid_South_Wales_Schedule_of_Charges_and_Other_Tables_April_2025.xlsx",
                    },
                ],
                "CDCM Model": [
                    {
                        "url": "https://www.nationalgrid.com/document/177876/download",
                        "file_name": "National_Grid_South_Wales_CDCM_Model_2026-27.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172406/download",
                        "file_name": "National_Grid_South_Wales_CDCM_Model_2025-26.xlsx",
                    },
                ],
            },
        },
        "south_west": {
            "name": "South West (MPAN 22)",
            "files": {
                "Schedule of Charges": [
                    {
                        "url": "https://www.nationalgrid.com/document/177861/download",
                        "file_name": "National_Grid_South_West_Schedule_of_Charges_and_Other_Tables_April_2026.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172391/download",
                        "file_name": "National_Grid_South_West_Schedule_of_Charges_and_Other_Tables_April_2025.xlsx",
                    },
                ],
                "CDCM Model": [
                    {
                        "url": "https://www.nationalgrid.com/document/177881/download",
                        "file_name": "National_Grid_South_West_CDCM_Model_2026-27.xlsx",
                    },
                    {
                        "url": "https://www.nationalgrid.com/document/172411/download",
                        "file_name": "National_Grid_South_West_CDCM_Model_2025-26.xlsx",
                    },
                ],
            },
        },
    }

    # Count total files
    total_files = sum(
        len(file_list)
        for region in regions.values()
        for category in region["files"].values()
        for file_list in [category]
    )
    logger.info(f"   📁 Output directory: {output_dir}")
    logger.info(f"   🔢 Total files: {total_files}")

    results = []

    # Download files for each region
    for region_key, region_data in regions.items():
        region_dir = os.path.join(output_dir, region_key)

        for category, file_list in region_data["files"].items():
            logger.info(f"   📂 Region: {region_data['name']}")
            logger.info(f"   🔍 Category: {category}")

            for file_info in file_list:
                result = download_file(
                    session, file_info["url"], region_dir, file_info["file_name"]
                )
                results.append(result)

    # Summarize results
    success_count = sum(1 for r in results if r["status"] == "success")
    logger.info(
        f"   ✅ Summary: Successfully downloaded {success_count} files from National Grid"
    )

    return results


def download_spm_files():
    """Download SP Manweb files (Scottish Power)"""
    logger.info("🏢 Downloading SP Manweb files (Scottish Power)")
    logger.info("--------------------------------------------------------")

    output_dir = "duos_spm_data"
    session = create_session()

    # Define files to download
    files = {
        "Charging Statement": [
            {
                "url": "https://www.scottishpower.com/userfiles/file/LC14-Statement-2026_SPM_v01.pdf",
                "file_name": "LC14-Statement-2026_SPM_v01.pdf",
            },
            {
                "url": "https://www.scottishpower.com/userfiles/file/SPM_LC14_Statement_2025_V05.pdf",
                "file_name": "SPM_LC14_Statement_2025_V05.pdf",
            },
        ],
        "Schedule of Charges": [
            {
                "url": "https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx",
                "file_name": "SPM-Schedule-of-charges-and-other-tables-2026-V0.1-Annex-6.xlsx",
            },
            {
                "url": "https://www.scottishpower.com/userfiles/file/SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx",
                "file_name": "SPM-Schedule-of-charges-and-other-tables-2025-V.0.7-Annex-6.xlsx",
            },
        ],
        "CDCM Model": [
            {
                "url": "https://www.scottishpower.com/userfiles/file/SPM%202026_27%20CDCM_v11_20241025_Published.xlsx",
                "file_name": "SPM_2026_27_CDCM_v11_20241025_Published.xlsx",
            },
            {
                "url": "https://www.scottishpower.com/userfiles/file/SPM_2025_26_CDCM_v10_20231106.xlsx",
                "file_name": "SPM_2025_26_CDCM_v10_20231106.xlsx",
            },
        ],
    }

    # Count total files
    total_files = sum(len(file_list) for file_list in files.values())
    logger.info(f"   📁 Output directory: {output_dir}")
    logger.info(f"   🔢 Total files: {total_files}")

    results = []

    # Download files for each category
    for category, file_list in files.items():
        logger.info(f"   🔍 Category: {category}")

        for file_info in file_list:
            result = download_file(
                session, file_info["url"], output_dir, file_info["file_name"]
            )
            results.append(result)

    # Summarize results
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    if error_count > 0:
        logger.info(
            f"   ⚠️ Summary: Failed to download {error_count} files from Scottish Power due to website restrictions"
        )
    else:
        logger.info(
            f"   ✅ Summary: Successfully downloaded {success_count} files from Scottish Power"
        )

    return results


def check_ssen_files():
    """Check for already downloaded SSEN files"""
    logger.info("🏢 Checking already downloaded SSEN files")
    logger.info("--------------------------------------------------------")

    # Directories to check
    shepd_dir = "duos_ssen_data/shepd"
    sepd_dir = "duos_ssen_data/sepd"

    logger.info(f"   📁 Checking directories: {shepd_dir}, {sepd_dir}")

    # Count existing files
    shepd_count = 0
    sepd_count = 0

    if os.path.exists(shepd_dir):
        shepd_count = len(
            [
                f
                for f in os.listdir(shepd_dir)
                if os.path.isfile(os.path.join(shepd_dir, f))
            ]
        )

    if os.path.exists(sepd_dir):
        sepd_count = len(
            [
                f
                for f in os.listdir(sepd_dir)
                if os.path.isfile(os.path.join(sepd_dir, f))
            ]
        )

    total_count = shepd_count + sepd_count

    if total_count > 0:
        logger.info(f"   ✅ Found {total_count} already downloaded SSEN files")
    else:
        logger.info(
            f"   ⚠️ No SSEN files found - these may need to be downloaded manually"
        )

    return [{"status": "existing", "count": total_count}]


def main():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"all_dno_download_results_{timestamp}"

    logger.info("📥 Downloading all UK DNO DUoS charging methodology files")
    logger.info("========================================================")

    # Download files from different sources
    nged_results = download_nged_files()
    spm_results = download_spm_files()
    ssen_results = check_ssen_files()

    # Combine all results
    all_results = {
        "National Grid": nged_results,
        "SP Manweb": spm_results,
        "SSEN": ssen_results,
        "timestamp": timestamp,
    }

    # Count statistics
    total_success = sum(
        1 for r in nged_results + spm_results if r.get("status") == "success"
    )
    total_error = sum(
        1 for r in nged_results + spm_results if r.get("status") == "error"
    )
    total_existing = sum(
        r.get("count", 0) for r in ssen_results if r.get("status") == "existing"
    )
    total_files = total_success + total_error
    success_rate = (total_success / total_files * 100) if total_files > 0 else 0

    # Generate summary
    summary = {
        "timestamp": timestamp,
        "total_dnos": 3,
        "total_files": total_files,
        "success": total_success,
        "existing": total_existing,
        "error": total_error,
        "success_rate": success_rate,
    }

    # Save results as JSON
    with open(f"{results_file}.json", "w") as f:
        json.dump({"results": all_results, "summary": summary}, f, indent=2)

    # Generate markdown report
    markdown_report = f"""# UK DNO DUoS Charging Methodology Download Report

## Download Summary

**Date**: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

- Total DNOs processed: 3 (National Grid, SP Manweb, SSEN)
- Total files attempted: {total_files}
- Successfully downloaded: {total_success}
- Already downloaded: {total_existing}
- Failed: {total_error}
- Success rate: {success_rate:.1f}%

## Details by DNO

### National Grid Electricity Distribution (formerly WPD)
- East Midlands (MPAN 11)
- West Midlands (MPAN 14)
- South Wales (MPAN 21)
- South West (MPAN 22)

### SP Manweb (MPAN 13)
- Direct links sometimes fail due to website security restrictions
- Manual download recommended via [Scottish Power website](http://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.asp)

### SSEN (SHEPD & SEPD)
- Already found {total_existing} files in directories

## Recommendations

For any files that failed to download automatically:

1. Visit the respective DNO websites:
   - National Grid: [https://www.nationalgrid.co.uk/electricity-distribution/document-library/charging-and-connections](https://www.nationalgrid.co.uk/electricity-distribution/document-library/charging-and-connections)
   - Scottish Power: [http://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.asp](http://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.asp)
   - SSEN: [https://www.ssen.co.uk/our-services/use-of-system-and-connection-charging/](https://www.ssen.co.uk/our-services/use-of-system-and-connection-charging/)

2. Navigate to the appropriate section for charging methodologies

3. Download files manually
"""

    # Save markdown report
    with open(f"{results_file}.md", "w") as f:
        f.write(markdown_report)

    # Print summary
    logger.info("\n📊 Overall Download Summary")
    logger.info("========================================================")
    logger.info(f"Total DNOs processed: 3 (National Grid, SP Manweb, SSEN)")
    logger.info(f"Total files attempted: {total_files}")
    logger.info(f"Successfully downloaded: {total_success}")
    logger.info(f"Already downloaded: {total_existing}")
    logger.info(f"Failed: {total_error}")
    logger.info(f"Success rate: {success_rate:.1f}%\n")
    logger.info(f"💾 Results saved to {results_file}.json and {results_file}.md")
    logger.info("✅ Download completed!\n")

    if total_error > 0:
        logger.info(
            "📝 SP Manweb files need to be downloaded manually due to website restrictions."
        )
        logger.info(
            "Please visit: https://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.aspx"
        )
        logger.info(
            "ℹ️ See COMPLETE_UK_DNO_DUOS_CHARGING_GUIDE.md for step-by-step manual download instructions"
        )


if __name__ == "__main__":
    main()
