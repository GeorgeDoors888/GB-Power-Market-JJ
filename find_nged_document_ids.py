#!/usr/bin/env python
"""
Script to find National Grid Electricity Distribution document IDs
by scraping their document library page.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

# URL for National Grid Electricity Distribution document library
BASE_URL = "https://www.nationalgrid.com/electricity-distribution/document-library/charging-statements"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Regions to search for
REGIONS = [
    {"name": "East Midlands", "keywords": ["east midlands"]},
    {"name": "West Midlands", "keywords": ["west midlands"]},
    {"name": "South Wales", "keywords": ["south wales"]},
    {"name": "South West", "keywords": ["south west"]}
]

# Document types to search for
DOC_TYPES = [
    {"name": "Schedule of Charges", "keywords": ["schedule of charges", "charging statement"]},
    {"name": "CDCM Model", "keywords": ["cdcm", "common distribution charging methodology"]}
]

# Years to search for
YEARS = ["2025", "2026"]

def fetch_page(url):
    """Fetch a web page and return the BeautifulSoup object"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_document_links(soup):
    """Find all document links on the page"""
    links = []

    # Look for links that might be document downloads
    for a in soup.find_all('a', href=True):
        href = a.get('href', '')

        # Check if it's a document download link
        if 'document' in href and 'download' in href:
            title = a.get_text().strip()
            if not title:
                # Try to find a nearby title
                parent = a.parent
                for i in range(3):  # Look up to 3 levels up
                    if parent:
                        potential_title = parent.get_text().strip()
                        if potential_title:
                            title = potential_title
                            break
                        parent = parent.parent

            links.append({
                "url": href if href.startswith('http') else f"https://www.nationalgrid.com{href}",
                "title": title
            })

    return links

def categorize_links(links):
    """Categorize links by region, document type, and year"""
    categorized = []

    for link in links:
        title = link["title"].lower()
        url = link["url"]

        matching_regions = []
        for region in REGIONS:
            if any(kw in title for kw in region["keywords"]):
                matching_regions.append(region["name"])

        matching_doc_types = []
        for doc_type in DOC_TYPES:
            if any(kw in title for kw in doc_type["keywords"]):
                matching_doc_types.append(doc_type["name"])

        matching_years = []
        for year in YEARS:
            if year in title:
                matching_years.append(year)

        # If we couldn't determine from title, try the URL
        if not matching_regions:
            for region in REGIONS:
                if any(kw.replace(" ", "-") in url.lower() for kw in region["keywords"]):
                    matching_regions.append(region["name"])

        if not matching_doc_types:
            for doc_type in DOC_TYPES:
                if any(kw.replace(" ", "-") in url.lower() for kw in doc_type["keywords"]):
                    matching_doc_types.append(doc_type["name"])

        if not matching_years:
            for year in YEARS:
                if year in url:
                    matching_years.append(year)

        # Only add if we have at least some categorization
        if matching_regions or matching_doc_types or matching_years:
            categorized.append({
                "url": url,
                "title": link["title"],
                "regions": matching_regions,
                "doc_types": matching_doc_types,
                "years": matching_years
            })

    return categorized

def main():
    print("🔍 Searching for National Grid Electricity Distribution document IDs")
    print("="*80)

    # Fetch the main document library page
    print(f"📄 Fetching main page: {BASE_URL}")
    soup = fetch_page(BASE_URL)

    if not soup:
        print("❌ Failed to fetch the main page.")
        return

    # Find document links
    print("🔎 Looking for document links...")
    links = find_document_links(soup)
    print(f"   Found {len(links)} potential document links")

    # Categorize links
    print("🏷️ Categorizing links...")
    categorized = categorize_links(links)
    print(f"   Categorized {len(categorized)} links")

    # Create results directory
    results_dir = "nged_search_results"
    os.makedirs(results_dir, exist_ok=True)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(results_dir, f"nged_document_links_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(categorized, f, indent=2)

    # Create markdown report
    print("📝 Creating markdown report...")
    markdown_path = os.path.join(results_dir, f"nged_document_links_{timestamp}.md")
    with open(markdown_path, "w") as f:
        f.write("# National Grid Electricity Distribution Document Links\n\n")
        f.write(f"**Search date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Organize by region, then doc type, then year
        for region in REGIONS:
            region_name = region["name"]
            f.write(f"## {region_name}\n\n")

            region_links = [link for link in categorized if region_name in link["regions"]]

            if not region_links:
                f.write("*No documents found for this region.*\n\n")
                continue

            for doc_type in DOC_TYPES:
                doc_type_name = doc_type["name"]
                f.write(f"### {doc_type_name}\n\n")

                doc_type_links = [link for link in region_links if doc_type_name in link["doc_types"]]

                if not doc_type_links:
                    f.write("*No documents found for this document type.*\n\n")
                    continue

                for year in YEARS:
                    f.write(f"#### {year}\n\n")

                    year_links = [link for link in doc_type_links if year in link["years"]]

                    if not year_links:
                        f.write("*No documents found for this year.*\n\n")
                        continue

                    f.write("| Title | URL | Document ID |\n")
                    f.write("|-------|-----|------------|\n")

                    for link in year_links:
                        # Extract document ID from URL
                        doc_id_match = re.search(r'document/(\d+)/download', link["url"])
                        doc_id = doc_id_match.group(1) if doc_id_match else "Unknown"

                        f.write(f"| {link['title']} | [{link['url']}]({link['url']}) | {doc_id} |\n")

                    f.write("\n")

        # Add summary of all found links
        f.write("## All Found Links\n\n")
        f.write("| URL | Title | Regions | Document Types | Years |\n")
        f.write("|-----|-------|---------|----------------|-------|\n")

        for link in categorized:
            regions = ", ".join(link["regions"]) if link["regions"] else "Unknown"
            doc_types = ", ".join(link["doc_types"]) if link["doc_types"] else "Unknown"
            years = ", ".join(link["years"]) if link["years"] else "Unknown"

            f.write(f"| [{link['url']}]({link['url']}) | {link['title']} | {regions} | {doc_types} | {years} |\n")

    print(f"✅ Report saved to {markdown_path}")
    print(f"✅ JSON data saved to {json_path}")

    # Also generate a Python script with updated URLs
    script_path = os.path.join(results_dir, "download_nged_files.py")
    with open(script_path, "w") as f:
        f.write("""#!/usr/bin/env python
\"\"\"
Download National Grid Electricity Distribution files
with document IDs found by the search script.
\"\"\"

import os
import requests
import time

# URLs discovered by the search script
NGED_FILES = {
""")

        # For each region
        for region in REGIONS:
            region_name = region["name"]
            region_var = region_name.replace(" ", "_").upper()
            region_dir = region_name.replace(" ", "_").lower()

            f.write(f'    "{region_var}": {{\n')
            f.write(f'        "output_dir": "duos_nged_data/{region_dir}",\n')
            f.write('        "files": [\n')

            region_links = [link for link in categorized if region_name in link["regions"]]

            # For each document type and year combination
            for doc_type in DOC_TYPES:
                doc_type_name = doc_type["name"]
                doc_type_var = doc_type_name.replace(" ", "_").lower()

                for year in YEARS:
                    matching_links = [
                        link for link in region_links
                        if doc_type_name in link["doc_types"] and year in link["years"]
                    ]

                    if matching_links:
                        # Just use the first match
                        link = matching_links[0]
                        filename = f"nged_{region_dir}_{doc_type_var}_{year}.xlsx"

                        f.write('            {\n')
                        f.write(f'                "url": "{link["url"]}",\n')
                        f.write(f'                "filename": "{filename}"\n')
                        f.write('            },\n')

            f.write('        ]\n')
            f.write('    },\n')

        # Add the download function and main code
        f.write("""
}

def download_file(url, output_path, max_retries=3, retry_delay=2):
    """Download a file from a URL to a specified path."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    }

    for attempt in range(max_retries):
        try:
            print(f"   📥 Downloading: {url}")
            print(f"      To: {output_path}")

            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size_kb = os.path.getsize(output_path) / 1024
            print(f"   ✅ Downloaded: {output_path} ({file_size_kb:.1f} KB)")
            return True

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"      ⚠️ Retry {attempt + 1}/{max_retries} after error: {e}")
                time.sleep(retry_delay)
            else:
                print(f"   ❌ Error downloading {url}: {e}")
                return False

def main():
    print("📥 Downloading National Grid Electricity Distribution files")
    print("=" * 80)

    success_count = 0
    fail_count = 0

    for dno_name, dno_info in NGED_FILES.items():
        output_dir = dno_info["output_dir"]
        files = dno_info["files"]

        print(f"🏢 Downloading files for {dno_name}")
        print(f"   📁 Output directory: {output_dir}")
        print(f"   🔢 Total files: {len(files)}")

        dno_success = 0
        dno_fail = 0

        for file_info in files:
            url = file_info["url"]
            filename = file_info["filename"]
            output_path = os.path.join(output_dir, filename)

            if download_file(url, output_path):
                dno_success += 1
                success_count += 1
            else:
                dno_fail += 1
                fail_count += 1

        print(f"   ✅ Downloaded: {dno_success} files")
        print(f"   ❌ Failed: {dno_fail} files")
        print()

    print("📊 Download Summary")
    print("=" * 80)
    print(f"Total files: {success_count + fail_count}")
    print(f"Downloaded: {success_count}")
    print(f"Failed: {fail_count}")

    if success_count + fail_count > 0:
        success_rate = (success_count / (success_count + fail_count)) * 100
        print(f"Success rate: {success_rate:.1f}%")

    print()
    print("✅ Download completed!")

if __name__ == "__main__":
    main()
""")

    print(f"✅ Download script saved to {script_path}")

if __name__ == "__main__":
    main()
