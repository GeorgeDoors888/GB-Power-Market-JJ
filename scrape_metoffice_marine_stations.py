import re
import time
import csv
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

INDEX_URL = "https://weather.metoffice.gov.uk/specialist-forecasts/coast-and-sea/observations"
OUT_CSV = "metoffice_marine_station_locations.csv"

# Polite crawling (adjust if needed)
REQUEST_SLEEP_S = 0.3
TIMEOUT = 30

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MetOfficeStationScraper/1.0; +https://example.com)"
})

def fetch_html(url: str) -> str:
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text

def extract_station_links(index_html: str):
    """
    Returns list of (name, href) from the index page.
    Station pages look like: /specialist-forecasts/coast-and-sea/observations/<station_id>
    """
    soup = BeautifulSoup(index_html, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        text = " ".join(a.get_text(" ", strip=True).split())
        if not text:
            continue
        # Match station pages with a numeric id at end
        m = re.search(r"/specialist-forecasts/coast-and-sea/observations/(\d+)$", href)
        if m:
            links.append((text, href))
    # de-dupe while preserving order
    seen = set()
    out = []
    for name, href in links:
        abs_url = urljoin(INDEX_URL, href)
        if abs_url not in seen:
            seen.add(abs_url)
            out.append((name, abs_url))
    return out

def parse_station_page(station_name: str, station_url: str):
    html = fetch_html(station_url)
    soup = BeautifulSoup(html, "html.parser")

    # Station id from URL
    station_id = station_url.rstrip("/").split("/")[-1]

    text = soup.get_text("\n", strip=True)

    # Look for "Location <lat>, <lon>"
    # Example appears on station pages like: "Location 48.59, -12.44"
    m = re.search(r"\bLocation\s+(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\b", text)
    lat = lon = None
    if m:
        lat = float(m.group(1))
        lon = float(m.group(2))

    # Try to capture a more official page title if present
    # e.g., "Marine observations - K1"
    title = soup.title.get_text(strip=True) if soup.title else station_name

    return {
        "station_id": station_id,
        "name_from_index": station_name,
        "page_title": title,
        "url": station_url,
        "latitude": lat,
        "longitude": lon,
    }

def main():
    index_html = fetch_html(INDEX_URL)
    stations = extract_station_links(index_html)
    print(f"Found {len(stations)} station links")

    rows = []
    for i, (name, url) in enumerate(stations, 1):
        try:
            row = parse_station_page(name, url)
            if row["latitude"] is None or row["longitude"] is None:
                print(f"[{i}/{len(stations)}] Missing coords: {name} -> {url}")
            else:
                print(f"[{i}/{len(stations)}] {name}: {row['latitude']}, {row['longitude']}")
            rows.append(row)
        except Exception as e:
            print(f"[{i}/{len(stations)}] ERROR for {name} ({url}): {e}")
        time.sleep(REQUEST_SLEEP_S)

    # Write CSV
    fieldnames = ["station_id", "name_from_index", "page_title", "latitude", "longitude", "url"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    print(f"\nSaved: {OUT_CSV}")

if __name__ == "__main__":
    main()
