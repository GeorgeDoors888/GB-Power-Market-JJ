#!/usr/bin/env python
"""
Script to find SP Manweb charging methodology documents
by scraping their website.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime

# URL for SP Energy Networks charging statements page
BASE_URL = "https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx"

# Headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Search terms to identify SP Manweb documents
SP_MANWEB_KEYWORDS = ["sp manweb", "spm", "manweb"]

# Document types to search for
DOC_TYPES = [
    {"name": "Schedule of Charges", "keywords": ["schedule of charges", "charging statement", "use of system charging"]},
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

        # Check if it's likely a document download link
        if (href.endswith('.xlsx') or href.endswith('.xls') or
            '/userfiles/' in href or '/file/' in href):
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

            # Ensure the URL is absolute
            if not href.startswith('http'):
                if href.startswith('/'):
                    href = f"https://www.spenergynetworks.co.uk{href}"
                else:
                    href = f"https://www.spenergynetworks.co.uk/{href}"

            links.append({
                "url": href,
                "title": title
            })

    return links

def filter_sp_manweb_links(links):
    """Filter links to only include SP Manweb documents"""
    sp_manweb_links = []

    for link in links:
        title = link["title"].lower()
        url = link["url"].lower()

        # Check if it's an SP Manweb document
        is_sp_manweb = any(kw in title or kw in url for kw in SP_MANWEB_KEYWORDS)

        # Check if it's a relevant document type
        doc_types = []
        for doc_type in DOC_TYPES:
            if any(kw in title or kw in url for kw in doc_type["keywords"]):
                doc_types.append(doc_type["name"])

        # Check if it's for a relevant year
        years = []
        for year in YEARS:
            if year in title or year in url:
                years.append(year)

        # Only include if it's an SP Manweb document and has at least some categorization
        if is_sp_manweb and (doc_types or years):
            sp_manweb_links.append({
                "url": link["url"],
                "title": link["title"],
                "doc_types": doc_types,
                "years": years
            })

    return sp_manweb_links

def main():
    print("🔍 Searching for SP Manweb charging methodology documents")
    print("="*80)

    # Fetch the main page
    print(f"📄 Fetching main page: {BASE_URL}")
    soup = fetch_page(BASE_URL)

    if not soup:
        print("❌ Failed to fetch the main page.")
        return

    # Find document links
    print("🔎 Looking for document links...")
    links = find_document_links(soup)
    print(f"   Found {len(links)} potential document links")

    # Filter to SP Manweb links
    print("🔍 Filtering for SP Manweb documents...")
    sp_manweb_links = filter_sp_manweb_links(links)
    print(f"   Found {len(sp_manweb_links)} SP Manweb documents")

    # Create results directory
    results_dir = "spm_search_results"
    os.makedirs(results_dir, exist_ok=True)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(results_dir, f"spm_document_links_{timestamp}.json")
    with open(json_path, "w") as f:
        json.dump(sp_manweb_links, f, indent=2)

    # Create markdown report
    print("📝 Creating markdown report...")
    markdown_path = os.path.join(results_dir, f"spm_document_links_{timestamp}.md")
    with open(markdown_path, "w") as f:
        f.write("# SP Manweb Charging Methodology Documents\n\n")
        f.write(f"**Search date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Organize by document type and year
        for doc_type in DOC_TYPES:
            doc_type_name = doc_type["name"]
            f.write(f"## {doc_type_name}\n\n")

            doc_type_links = [link for link in sp_manweb_links if doc_type_name in link["doc_types"]]

            if not doc_type_links:
                f.write("*No documents found for this document type.*\n\n")
                continue

            for year in YEARS:
                f.write(f"### {year}\n\n")

                year_links = [link for link in doc_type_links if year in link["years"]]

                if not year_links:
                    f.write("*No documents found for this year.*\n\n")
                    continue

                f.write("| Title | URL |\n")
                f.write("|-------|-----|\n")

                for link in year_links:
                    f.write(f"| {link['title']} | [{link['url']}]({link['url']}) |\n")

                f.write("\n")

        # Add summary of all found links
        f.write("## All SP Manweb Documents\n\n")
        f.write("| Title | URL | Document Types | Years |\n")
        f.write("|-------|-----|----------------|-------|\n")

        for link in sp_manweb_links:
            doc_types = ", ".join(link["doc_types"]) if link["doc_types"] else "Unknown"
            years = ", ".join(link["years"]) if link["years"] else "Unknown"

            f.write(f"| {link['title']} | [{link['url']}]({link['url']}) | {doc_types} | {years} |\n")

    print(f"✅ Report saved to {markdown_path}")
    print(f"✅ JSON data saved to {json_path}")

    # Also generate a Python script with discovered URLs
    script_path = os.path.join(results_dir, "download_spm_files.py")
    with open(script_path, "w") as f:
        f.write('''#!/usr/bin/env python
"""
Download SP Manweb charging methodology files
with URLs found by the search script.
"""'''

import os
import requests
import time

# SP Manweb files discovered by the search script
SPM_FILES = [
""")

        # Add each discovered SP Manweb file
        for link in sp_manweb_links:
            doc_types = ", ".join(link["doc_types"]) if link["doc_types"] else "Unknown"
            years = ", ".join(link["years"]) if link["years"] else "Unknown"

            f.write('    {\n')
            f.write(f'        "url": "{link["url"]}",\n')
            f.write(f'        "title": "{link["title"]}",\n')
            f.write(f'        "doc_types": "{doc_types}",\n')
            f.write(f'        "years": "{years}",\n')

            # Generate a filename based on the URL
            url_parts = link["url"].split('/')
            filename = url_parts[-1] if url_parts else "unknown.xlsx"

            f.write(f'        "filename": "{filename}"\n')
            f.write('    },\n')

        # Add the download function and main code
        f.write("""
]

def download_file(url, output_path, max_retries=3, retry_delay=2):
    """Download a file from a URL to a specified path."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.spenergynetworks.co.uk/pages/use_of_system_charging_statements.aspx'
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
    print("📥 Downloading SP Manweb charging methodology files")
    print("=" * 80)

    output_dir = "duos_spm_data"
    os.makedirs(output_dir, exist_ok=True)

    print(f"📁 Output directory: {output_dir}")
    print(f"🔢 Total files: {len(SPM_FILES)}")

    success_count = 0
    fail_count = 0

    for file_info in SPM_FILES:
        url = file_info["url"]
        filename = file_info["filename"]
        output_path = os.path.join(output_dir, filename)

        if download_file(url, output_path):
            success_count += 1
        else:
            fail_count += 1

    print()
    print("📊 Download Summary")
    print("=" * 80)
    print(f"Total files: {len(SPM_FILES)}")
    print(f"Downloaded: {success_count}")
    print(f"Failed: {fail_count}")

    if len(SPM_FILES) > 0:
        success_rate = (success_count / len(SPM_FILES)) * 100
        print(f"Success rate: {success_rate:.1f}%")

    print()
    print("✅ Download completed!")

if __name__ == "__main__":
    main()
""")

    print(f"✅ Download script saved to {script_path}")

if __name__ == "__main__":
    main()
