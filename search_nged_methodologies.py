#!/usr/bin/env python3
"""
Search for National Grid Electricity Distribution DUoS Methodology Documents
Targeting the 4 missing NGED regions: East Midlands, West Midlands, South Wales, South West
"""

import os
import sys

from google_search_setup import GoogleCustomSearch


def search_nged_methodologies():
    """Search for NGED DUoS methodology documents"""

    print("🔍 SEARCHING FOR NATIONAL GRID ELECTRICITY DISTRIBUTION DUOS METHODOLOGIES")
    print("=" * 75)

    # You'll need to add your Custom Search Engine ID to jibber_jaber_key.json
    # For now, let's try with environment variable
    search_engine_id = os.getenv(
        "GOOGLE_SEARCH_ENGINE_ID", "YOUR_SEARCH_ENGINE_ID_HERE"
    )

    if search_engine_id == "YOUR_SEARCH_ENGINE_ID_HERE":
        print("⚠️  Please set up your Custom Search Engine ID")
        print("1. Go to: https://cse.google.com/cse/")
        print("2. Create a Custom Search Engine")
        print("3. Get the Search Engine ID")
        print("4. Add it to your jibber_jaber_key.json file")
        print("5. Or set GOOGLE_SEARCH_ENGINE_ID environment variable")
        return

    try:
        # Initialize the search client
        search_client = GoogleCustomSearch()

        # Search queries for NGED regions
        search_queries = [
            # General NGED searches
            "National Grid Electricity Distribution DUoS methodology charges schedule",
            "NGED distribution use of system charges methodology",
            "National Grid Electricity Distribution tariff methodology",
            # Region-specific searches
            "National Grid Electricity Distribution East Midlands DUoS charges schedule",
            "National Grid Electricity Distribution West Midlands DUoS charges schedule",
            "National Grid Electricity Distribution South Wales DUoS charges schedule",
            "National Grid Electricity Distribution South West DUoS charges schedule",
            # File-specific searches
            "National Grid Electricity Distribution schedule charges methodology filetype:xlsx",
            "NGED DUoS tariff methodology filetype:pdf",
            "Western Power Distribution charges schedule filetype:xlsx",  # Legacy name
        ]

        all_results = []

        for i, query in enumerate(search_queries, 1):
            print(f"\n🔍 Search {i}/{len(search_queries)}: {query}")
            print("-" * 60)

            try:
                results = search_client.search(
                    query=query,
                    num_results=5,
                    file_type=None,  # Allow all file types
                    site_search="commercial.nationalgrid.co.uk",  # Focus on official site
                )

                if results:
                    for j, result in enumerate(results, 1):
                        print(f"  {j}. {result['title']}")
                        print(f"     URL: {result['link']}")
                        if "snippet" in result:
                            print(f"     Description: {result['snippet'][:100]}...")
                        print()

                        # Store unique results
                        if result not in all_results:
                            all_results.append(result)
                else:
                    print("  No results found")

            except Exception as e:
                print(f"  ❌ Search failed: {e}")

        # Summary
        print(f"\n📊 SEARCH SUMMARY:")
        print(f"   Total unique results found: {len(all_results)}")
        print(f"   Target: DUoS methodology documents for 4 NGED regions")

        # Look for Excel files specifically
        excel_files = [
            r for r in all_results if ".xlsx" in r["link"] or ".xls" in r["link"]
        ]
        pdf_files = [r for r in all_results if ".pdf" in r["link"]]

        print(f"   📊 Excel files found: {len(excel_files)}")
        print(f"   📄 PDF files found: {len(pdf_files)}")

        if excel_files:
            print(f"\n📊 EXCEL FILES (Likely DUoS Schedules):")
            for i, result in enumerate(excel_files, 1):
                print(f"   {i}. {result['title']}")
                print(f"      {result['link']}")

        # Missing regions check
        print(f"\n🎯 MISSING REGIONS TO TARGET:")
        missing_regions = [
            "MPAN 11: National Grid ED – East Midlands",
            "MPAN 14: National Grid ED – West Midlands",
            "MPAN 21: National Grid ED – South Wales",
            "MPAN 22: National Grid ED – South West",
        ]

        for region in missing_regions:
            print(f"   ❌ {region}")

        print(f"\n💡 NEXT STEPS:")
        print("1. 🔗 Visit the National Grid commercial website directly")
        print("2. 📂 Navigate to Use of System charges section")
        print("3. 📊 Look for 'Schedule of Charges' or 'Methodology' documents")
        print("4. 🎯 Download Excel files for each of the 4 NGED regions")
        print("5. 🔄 Run our extraction tool on the downloaded files")

    except Exception as e:
        print(f"❌ Search setup failed: {e}")
        print("Please check your Google Custom Search configuration.")


if __name__ == "__main__":
    search_nged_methodologies()
