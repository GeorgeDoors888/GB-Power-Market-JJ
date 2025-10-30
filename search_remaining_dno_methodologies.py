#!/usr/bin/env python3
"""
Search for DUoS charging methodologies for remaining DNOs using Google Search API
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Constants
GOOGLE_API_KEY = "AIzaSyDcHN_xwNbw6V0tklBKY8J_YpPKdcUTZYQ"  # From jibber_jaber_key.json
BASE_URL = "https://www.googleapis.com/customsearch/v1"

# Target DNOs and search terms
SEARCH_TARGETS = [
    {
        "dno": "Scottish and Southern Energy Power Distribution (SEPD)",
        "mpan": 20,
        "region": "Southern England",
        "site": "https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/southern-electric-power-distribution/",
        "search_terms": [
            "SEPD DUoS charges schedule",
            "Southern Electric Power Distribution charging methodology",
            "SEPD Schedule of Charges Excel",
            "Southern Electric Power Distribution CDCM model",
        ],
    },
    {
        "dno": "Scottish Hydro Electric Power Distribution (SHEPD)",
        "mpan": 17,
        "region": "North Scotland",
        "site": "https://www.ssen.co.uk/about-ssen/library/charging-statements-and-information/scottish-hydro-electric-power-distribution/",
        "search_terms": [
            "SHEPD DUoS charges schedule",
            "Scottish Hydro Electric Power Distribution charging methodology",
            "SHEPD Schedule of Charges Excel",
            "Scottish Hydro Electric Power Distribution CDCM model",
        ],
    },
    {
        "dno": "SP Manweb (SPM)",
        "mpan": 13,
        "region": "Wales & Merseyside",
        "site": "https://www.scottishpower.com/pages/connections_use_of_system_and_metering_services.aspx",
        "search_terms": [
            "SP Manweb DUoS charges schedule",
            "SPM Schedule of Charges Excel",
            "SP Manweb charging methodology",
            "SP Manweb CDCM model",
        ],
    },
    {
        "dno": "National Grid Electricity Distribution (East Midlands)",
        "mpan": 11,
        "region": "East Midlands",
        "site": "https://www.nationalgrid.com/electricity-distribution/",
        "previous": "Western Power Distribution (East Midlands)",
        "search_terms": [
            "National Grid Electricity Distribution East Midlands DUoS charges",
            "NGED East Midlands Schedule of Charges",
            "NGED East Midlands CDCM model",
            "Western Power Distribution East Midlands charging methodology",
        ],
    },
    {
        "dno": "National Grid Electricity Distribution (West Midlands)",
        "mpan": 14,
        "region": "West Midlands",
        "site": "https://www.nationalgrid.com/electricity-distribution/",
        "previous": "Western Power Distribution (West Midlands)",
        "search_terms": [
            "National Grid Electricity Distribution West Midlands DUoS charges",
            "NGED West Midlands Schedule of Charges",
            "NGED West Midlands CDCM model",
            "Western Power Distribution West Midlands charging methodology",
        ],
    },
    {
        "dno": "National Grid Electricity Distribution (South Wales)",
        "mpan": 21,
        "region": "South Wales",
        "site": "https://www.nationalgrid.com/electricity-distribution/",
        "previous": "Western Power Distribution (South Wales)",
        "search_terms": [
            "National Grid Electricity Distribution South Wales DUoS charges",
            "NGED South Wales Schedule of Charges",
            "NGED South Wales CDCM model",
            "Western Power Distribution South Wales charging methodology",
        ],
    },
    {
        "dno": "National Grid Electricity Distribution (South West)",
        "mpan": 22,
        "region": "South West England",
        "site": "https://www.nationalgrid.com/electricity-distribution/",
        "previous": "Western Power Distribution (South West)",
        "search_terms": [
            "National Grid Electricity Distribution South West DUoS charges",
            "NGED South West Schedule of Charges",
            "NGED South West CDCM model",
            "Western Power Distribution South West charging methodology",
        ],
    },
]


def search_google(query: str, site: Optional[str] = None) -> Dict[str, Any]:
    """
    Search Google using the Custom Search JSON API

    Args:
        query: Search query
        site: Restrict search to specific site

    Returns:
        Search results
    """
    params = {"key": GOOGLE_API_KEY, "q": query}

    # If site is provided, restrict search to that site
    if site:
        params["q"] = f"site:{site} {query}"

    # Add cx parameter if we have a search engine ID
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    if search_engine_id and search_engine_id != "YOUR_SEARCH_ENGINE_ID_HERE":
        params["cx"] = search_engine_id

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error searching Google: {e}")
        return {"error": str(e)}


def extract_download_links(results: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract download links from search results

    Args:
        results: Search results

    Returns:
        List of download links
    """
    download_links = []

    if "items" not in results:
        return download_links

    for item in results.get("items", []):
        title = item.get("title", "")
        link = item.get("link", "")
        snippet = item.get("snippet", "")

        # Check if this is a DUoS charging related file
        is_relevant = any(
            keyword.lower() in (title + snippet).lower()
            for keyword in [
                "duos",
                "schedule of charges",
                "charging statement",
                "cdcm",
                "electricity distribution",
                "methodology",
            ]
        )

        # Check if this is likely a downloadable file
        is_download = any(
            ext in link.lower() for ext in [".xlsx", ".xls", ".csv", ".pdf", ".zip"]
        )

        download_links.append(
            {
                "title": title,
                "link": link,
                "snippet": snippet,
                "is_relevant": is_relevant,
                "is_download": is_download,
                "file_type": link.split(".")[-1].lower() if "." in link else "unknown",
            }
        )

    return download_links


def search_all_targets() -> Dict[str, Any]:
    """
    Search for all targets

    Returns:
        Combined search results
    """
    all_results = {"search_date": datetime.now().isoformat(), "dno_results": []}

    for target in SEARCH_TARGETS:
        dno_name = target["dno"]
        site = target.get("site")
        mpan = target.get("mpan")
        region = target.get("region")

        print(f"\n🔍 Searching for {dno_name} (MPAN {mpan}) - {region}")
        print(f"   Site: {site}")

        dno_result = {
            "dno": dno_name,
            "mpan": mpan,
            "region": region,
            "site": site,
            "searches": [],
        }

        for search_term in target["search_terms"]:
            print(f"   🔎 Searching for: {search_term}")

            # Search with site restriction
            results = search_google(search_term, site)

            # Extract download links
            download_links = extract_download_links(results)
            relevant_links = [link for link in download_links if link["is_relevant"]]

            search_result = {
                "term": search_term,
                "total_results": len(download_links),
                "relevant_results": len(relevant_links),
                "download_links": download_links,
                "raw_results": results,
            }

            # Print summary
            print(
                f"     - Found {len(download_links)} results ({len(relevant_links)} relevant)"
            )
            for i, link in enumerate(relevant_links[:5]):
                print(f"       {i+1}. {link['title']}")
                print(f"          URL: {link['link']}")
                print(f"          Type: {link['file_type']}")

            dno_result["searches"].append(search_result)

        all_results["dno_results"].append(dno_result)

    return all_results


def save_results(
    results: Dict[str, Any], output_file: str = "dno_methodology_search_results.json"
):
    """
    Save search results to file

    Args:
        results: Search results
        output_file: Output file name
    """
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Search results saved to {output_file}")

    # Create a summary CSV file
    summary_rows = []

    for dno_result in results["dno_results"]:
        dno = dno_result["dno"]
        mpan = dno_result["mpan"]
        region = dno_result["region"]

        for search in dno_result["searches"]:
            term = search["term"]

            for link in search["download_links"]:
                if link["is_relevant"]:
                    summary_rows.append(
                        {
                            "DNO": dno,
                            "MPAN": mpan,
                            "Region": region,
                            "Search Term": term,
                            "Title": link["title"],
                            "URL": link["link"],
                            "File Type": link["file_type"],
                            "Is Download": link["is_download"],
                            "Snippet": link["snippet"],
                        }
                    )

    if summary_rows:
        df = pd.DataFrame(summary_rows)
        csv_file = output_file.replace(".json", ".csv")
        df.to_csv(csv_file, index=False)
        print(f"📊 Summary CSV saved to {csv_file}")

    # Create a markdown summary
    md_content = f"# DUoS Charging Methodology Search Results\n\n"
    md_content += f"Search Date: {results['search_date']}\n\n"

    for dno_result in results["dno_results"]:
        dno = dno_result["dno"]
        mpan = dno_result["mpan"]
        region = dno_result["region"]
        site = dno_result["site"]

        md_content += f"## {dno} (MPAN {mpan}) - {region}\n\n"
        md_content += f"Site: {site}\n\n"

        # Count relevant results by file type
        file_types = {}
        for search in dno_result["searches"]:
            for link in search["download_links"]:
                if link["is_relevant"]:
                    file_type = link["file_type"]
                    file_types[file_type] = file_types.get(file_type, 0) + 1

        if file_types:
            md_content += "### File Types Found:\n\n"
            for file_type, count in file_types.items():
                md_content += f"- {file_type.upper()}: {count} files\n"
            md_content += "\n"

        # List top relevant results
        all_relevant = []
        for search in dno_result["searches"]:
            for link in search["download_links"]:
                if link["is_relevant"]:
                    all_relevant.append(link)

        if all_relevant:
            md_content += "### Top Relevant Results:\n\n"
            for i, link in enumerate(all_relevant[:10]):
                md_content += f"{i+1}. **{link['title']}**\n"
                md_content += f"   - URL: {link['link']}\n"
                md_content += f"   - Type: {link['file_type'].upper()}\n"
                if link["snippet"]:
                    md_content += f"   - Snippet: {link['snippet']}\n"
                md_content += "\n"

        md_content += "---\n\n"

    md_file = output_file.replace(".json", ".md")
    with open(md_file, "w") as f:
        f.write(md_content)

    print(f"📝 Markdown summary saved to {md_file}")


def main():
    """
    Main entry point
    """
    print("🔍 Searching for DUoS charging methodologies for remaining DNOs")
    print("=" * 80)

    # Check if we have a search engine ID
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    if not search_engine_id or search_engine_id == "YOUR_SEARCH_ENGINE_ID_HERE":
        print("\n⚠️  Warning: No Google Custom Search Engine ID found.")
        print("   Search results may be limited without a custom search engine.")
        print(
            "   You may need to set up a Google Custom Search Engine and update the ID."
        )

        # Offer to continue anyway
        response = input("\nContinue with limited search? (y/n): ")
        if response.lower() != "y":
            print("Exiting...")
            return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"dno_methodology_search_results_{timestamp}.json"

    # Search for all targets
    results = search_all_targets()

    # Save results
    save_results(results, output_file)

    # Print summary
    total_relevant = sum(
        len([link for link in search["download_links"] if link["is_relevant"]])
        for dno_result in results["dno_results"]
        for search in dno_result["searches"]
    )

    print(
        f"\n✅ Search completed! Found {total_relevant} relevant results across {len(SEARCH_TARGETS)} DNOs."
    )
    print(f"📊 Results saved to {output_file}")


if __name__ == "__main__":
    main()
