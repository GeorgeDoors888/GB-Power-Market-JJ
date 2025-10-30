#!/usr/bin/env python3
"""
Ofgem Data Collection API

This module provides functionality to collect data from Ofgem's various data sources:
1. Data Portal - Interactive charts and CSV downloads
2. Electronic Public Register (EPR) - Licence information
3. Publications API - Regulatory documents
4. Google Drive - Regulatory documents (your existing 1,156 files)

Unlike BMRS which has a REST API, Ofgem provides data through web scraping,
file downloads, and document repositories.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google.cloud import bigquery, storage
from google.oauth2 import service_account

# Load environment variables
load_dotenv("api.env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ofgem_api.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class OfgemConfig:
    """Configuration for Ofgem data collection"""

    # Base URLs
    base_url: str = "https://www.ofgem.gov.uk"
    data_portal_url: str = "https://www.ofgem.gov.uk/news-and-insight/data/data-portal"
    epr_url: str = "https://epr.ofgem.gov.uk"
    publications_url: str = "https://www.ofgem.gov.uk/publications"

    # Data categories
    data_categories: List[str] = None

    # Storage configuration
    use_bigquery: bool = True
    use_cloud_storage: bool = True
    project_id: str = "jibber-jabber-knowledge"
    dataset_id: str = "uk_energy_insights"
    bucket_name: str = "energy-data-collection"

    # Rate limiting
    request_delay: float = 1.0  # seconds between requests
    max_retries: int = 3

    # Output directories
    output_dir: str = "./data/ofgem"
    csv_dir: str = "./data/ofgem/csv"
    documents_dir: str = "./data/ofgem/documents"

    def __post_init__(self):
        if self.data_categories is None:
            self.data_categories = [
                "retail-market-indicators",
                "wholesale-market-indicators",
                "energy-network-indicators",
                "customer-service-data",
            ]

        # Create output directories
        for dir_path in [self.output_dir, self.csv_dir, self.documents_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


class OfgemAPI:
    """Main class for Ofgem data collection"""

    def __init__(self, config: Optional[OfgemConfig] = None):
        self.config = config or OfgemConfig()
        self.session = self._create_session()

        # Initialize cloud clients if enabled
        self.bq_client = None
        self.storage_client = None

        if self.config.use_bigquery or self.config.use_cloud_storage:
            self._initialize_cloud_clients()

        logger.info("🚀 Ofgem API initialized")

    def _create_session(self) -> requests.Session:
        """Create a requests session with proper headers"""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "OfgemDataCollector/1.0 (Research)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-GB,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        return session

    def _initialize_cloud_clients(self):
        """Initialize Google Cloud clients"""
        try:
            credentials_path = "jibber_jabber_key.json"
            if os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )

                if self.config.use_bigquery:
                    self.bq_client = bigquery.Client(
                        credentials=credentials, project=self.config.project_id
                    )
                    logger.info("✅ BigQuery client initialized")

                if self.config.use_cloud_storage:
                    self.storage_client = storage.Client(
                        credentials=credentials, project=self.config.project_id
                    )
                    logger.info("✅ Cloud Storage client initialized")

        except Exception as e:
            logger.warning(f"⚠️ Could not initialize cloud clients: {e}")
            self.config.use_bigquery = False
            self.config.use_cloud_storage = False

    def get_data_portal_charts(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape available charts from Ofgem data portal

        Args:
            category: Specific category to fetch, or None for all

        Returns:
            Dictionary of chart information
        """
        logger.info(f"📊 Fetching data portal charts for category: {category or 'all'}")

        if category:
            url = f"{self.config.data_portal_url}/{category}"
        else:
            url = f"{self.config.data_portal_url}/all-available-charts"

        try:
            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            charts = []

            # Look for chart containers (this may need adjustment based on actual HTML structure)
            chart_elements = soup.find_all(
                ["div", "section"], class_=re.compile(r"chart|data|visualization")
            )

            for element in chart_elements:
                chart_info = self._extract_chart_info(element)
                if chart_info:
                    charts.append(chart_info)

            # Also look for download links
            download_links = soup.find_all("a", href=re.compile(r"\.csv|download|data"))

            for link in download_links:
                download_info = self._extract_download_info(link)
                if download_info:
                    charts.append(download_info)

            logger.info(f"✅ Found {len(charts)} charts/datasets")
            return {
                "category": category or "all",
                "charts": charts,
                "scraped_at": datetime.now().isoformat(),
                "url": url,
            }

        except Exception as e:
            logger.error(f"❌ Error fetching data portal charts: {e}")
            return {"error": str(e), "category": category}

    def _extract_chart_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract chart information from HTML element"""
        try:
            title_elem = element.find(["h1", "h2", "h3", "h4", "title"])
            title = title_elem.get_text(strip=True) if title_elem else None

            desc_elem = element.find(
                ["p", "div"], class_=re.compile(r"description|summary")
            )
            description = desc_elem.get_text(strip=True) if desc_elem else None

            # Look for data attributes or embedded JSON
            data_attrs = {
                k: v for k, v in element.attrs.items() if k.startswith("data-")
            }

            if title:
                return {
                    "type": "chart",
                    "title": title,
                    "description": description,
                    "data_attributes": data_attrs,
                    "html_id": element.get("id"),
                    "css_classes": element.get("class", []),
                }
        except Exception as e:
            logger.debug(f"Error extracting chart info: {e}")
        return None

    def _extract_download_info(self, link) -> Optional[Dict[str, Any]]:
        """Extract download link information"""
        try:
            href = link.get("href")
            if not href:
                return None

            # Make absolute URL
            if href.startswith("/"):
                href = self.config.base_url + href

            link_text = link.get_text(strip=True)

            return {
                "type": "download",
                "title": link_text,
                "url": href,
                "file_type": href.split(".")[-1].lower() if "." in href else "unknown",
            }
        except Exception as e:
            logger.debug(f"Error extracting download info: {e}")
        return None

    def download_csv_data(
        self, url: str, filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Download CSV data from a URL

        Args:
            url: URL to download from
            filename: Optional filename to save as

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"📥 Downloading CSV from: {url}")

            response = self.session.get(url)
            response.raise_for_status()

            if not filename:
                # Generate filename from URL or timestamp
                filename = url.split("/")[-1]
                if not filename.endswith(".csv"):
                    filename = (
                        f"ofgem_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    )

            file_path = Path(self.config.csv_dir) / filename

            with open(file_path, "wb") as f:
                f.write(response.content)

            logger.info(f"✅ Downloaded: {file_path}")

            # Upload to cloud storage if enabled
            if self.config.use_cloud_storage and self.storage_client:
                self._upload_to_gcs(file_path, f"ofgem/csv/{filename}")

            return str(file_path)

        except Exception as e:
            logger.error(f"❌ Error downloading CSV: {e}")
            return None

    def get_licence_data(self, licence_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch licence data from Electronic Public Register

        Args:
            licence_type: Type of licence to fetch (e.g., 'electricity', 'gas')

        Returns:
            Dictionary of licence information
        """
        logger.info(f"📋 Fetching licence data: {licence_type or 'all types'}")

        try:
            # EPR search URL - may need adjustment based on actual EPR structure
            search_url = f"{self.config.epr_url}/search"

            response = self.session.get(search_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            licences = []

            # Look for licence tables or lists
            licence_elements = soup.find_all(
                ["table", "div"], class_=re.compile(r"licence|permit")
            )

            for element in licence_elements:
                licence_info = self._extract_licence_info(element, licence_type)
                if licence_info:
                    licences.append(licence_info)

            logger.info(f"✅ Found {len(licences)} licences")
            return {
                "licence_type": licence_type or "all",
                "licences": licences,
                "scraped_at": datetime.now().isoformat(),
                "source": "EPR",
            }

        except Exception as e:
            logger.error(f"❌ Error fetching licence data: {e}")
            return {"error": str(e), "licence_type": licence_type}

    def _extract_licence_info(
        self, element, licence_type: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Extract licence information from HTML element"""
        try:
            # This will need to be customized based on actual EPR structure
            rows = element.find_all("tr") if element.name == "table" else []

            licence_data = {}

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    licence_data[key] = value

            # Filter by licence type if specified
            if licence_type and licence_type.lower() not in str(licence_data).lower():
                return None

            if licence_data:
                licence_data["extracted_at"] = datetime.now().isoformat()
                return licence_data

        except Exception as e:
            logger.debug(f"Error extracting licence info: {e}")
        return None

    def get_publications(
        self, search_term: Optional[str] = None, limit: int = 50
    ) -> Dict[str, Any]:
        """
        Fetch recent publications from Ofgem

        Args:
            search_term: Optional search term to filter publications
            limit: Maximum number of publications to fetch

        Returns:
            Dictionary of publication information
        """
        logger.info(f"📚 Fetching publications: {search_term or 'recent'}")

        try:
            url = self.config.publications_url
            if search_term:
                url += f"?search={search_term}"

            response = self.session.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            publications = []

            # Look for publication links
            pub_elements = soup.find_all(
                "a", href=re.compile(r"\.pdf|publication|document")
            )

            for element in pub_elements[:limit]:
                pub_info = self._extract_publication_info(element)
                if pub_info:
                    publications.append(pub_info)

            logger.info(f"✅ Found {len(publications)} publications")
            return {
                "search_term": search_term,
                "publications": publications,
                "scraped_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Error fetching publications: {e}")
            return {"error": str(e), "search_term": search_term}

    def _extract_publication_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract publication information from HTML element"""
        try:
            href = element.get("href")
            if not href:
                return None

            # Make absolute URL
            if href.startswith("/"):
                href = self.config.base_url + href

            title = element.get_text(strip=True)

            # Try to extract date from surrounding elements
            date_elem = element.find_parent().find(
                ["time", "span"], class_=re.compile(r"date")
            )
            date = date_elem.get_text(strip=True) if date_elem else None

            return {
                "title": title,
                "url": href,
                "date": date,
                "file_type": href.split(".")[-1].lower() if "." in href else "html",
            }

        except Exception as e:
            logger.debug(f"Error extracting publication info: {e}")
        return None

    def _upload_to_gcs(self, local_path: str, gcs_path: str):
        """Upload file to Google Cloud Storage"""
        try:
            bucket = self.storage_client.bucket(self.config.bucket_name)
            blob = bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)
            logger.info(
                f"📤 Uploaded to GCS: gs://{self.config.bucket_name}/{gcs_path}"
            )
        except Exception as e:
            logger.error(f"❌ Error uploading to GCS: {e}")

    def save_to_bigquery(self, data: Dict[str, Any], table_name: str):
        """Save data to BigQuery"""
        if not self.bq_client:
            logger.warning("⚠️ BigQuery client not available")
            return

        try:
            # Convert data to DataFrame
            if "charts" in data:
                df = pd.DataFrame(data["charts"])
            elif "licences" in data:
                df = pd.DataFrame(data["licences"])
            elif "publications" in data:
                df = pd.DataFrame(data["publications"])
            else:
                df = pd.DataFrame([data])

            # Create table reference
            table_id = f"{self.config.project_id}.{self.config.dataset_id}.{table_name}"

            # Upload to BigQuery
            job_config = bigquery.LoadJobConfig(
                write_disposition="WRITE_APPEND", autodetect=True
            )

            job = self.bq_client.load_table_from_dataframe(
                df, table_id, job_config=job_config
            )
            job.result()  # Wait for job to complete

            logger.info(f"📊 Loaded {len(df)} rows to {table_id}")

        except Exception as e:
            logger.error(f"❌ Error saving to BigQuery: {e}")

    def collect_all_data(self):
        """Collect data from all Ofgem sources"""
        logger.info("🚀 Starting comprehensive Ofgem data collection")

        results = {}

        # 1. Data Portal Charts
        for category in self.config.data_categories:
            logger.info(f"📊 Collecting data portal: {category}")
            charts_data = self.get_data_portal_charts(category)
            results[f"charts_{category}"] = charts_data

            if self.config.use_bigquery:
                self.save_to_bigquery(
                    charts_data, f"ofgem_charts_{category.replace('-', '_')}"
                )

            time.sleep(self.config.request_delay)

        # 2. Licence Data
        logger.info("📋 Collecting licence data")
        licence_data = self.get_licence_data()
        results["licences"] = licence_data

        if self.config.use_bigquery:
            self.save_to_bigquery(licence_data, "ofgem_licences")

        time.sleep(self.config.request_delay)

        # 3. Publications
        logger.info("📚 Collecting publications")
        publications_data = self.get_publications()
        results["publications"] = publications_data

        if self.config.use_bigquery:
            self.save_to_bigquery(publications_data, "ofgem_publications")

        # 4. Save summary
        summary_file = (
            Path(self.config.output_dir)
            / f"collection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"✅ Collection complete! Summary saved to: {summary_file}")
        return results


def main():
    """Main function to run Ofgem data collection"""
    print("🏛️ OFGEM DATA COLLECTION API")
    print("=" * 50)

    # Initialize API
    config = OfgemConfig()
    api = OfgemAPI(config)

    print("\nWhat would you like to do?")
    print("1. Collect all Ofgem data")
    print("2. Get data portal charts")
    print("3. Get licence information")
    print("4. Get publications")
    print("5. Download specific CSV")

    choice = input("\nEnter choice (1-5): ").strip()

    if choice == "1":
        print("🚀 Starting comprehensive data collection...")
        results = api.collect_all_data()
        print(f"\n✅ Collection complete! Found:")
        for key, data in results.items():
            if isinstance(data, dict) and "charts" in data:
                print(f"  - {key}: {len(data['charts'])} items")
            elif isinstance(data, dict) and "licences" in data:
                print(f"  - {key}: {len(data['licences'])} items")
            elif isinstance(data, dict) and "publications" in data:
                print(f"  - {key}: {len(data['publications'])} items")

    elif choice == "2":
        category = input("Enter category (or press Enter for all): ").strip()
        category = category if category else None
        charts = api.get_data_portal_charts(category)
        print(f"\n📊 Found {len(charts.get('charts', []))} charts")

    elif choice == "3":
        licence_type = input("Enter licence type (or press Enter for all): ").strip()
        licence_type = licence_type if licence_type else None
        licences = api.get_licence_data(licence_type)
        print(f"\n📋 Found {len(licences.get('licences', []))} licences")

    elif choice == "4":
        search_term = input("Enter search term (or press Enter for recent): ").strip()
        search_term = search_term if search_term else None
        publications = api.get_publications(search_term)
        print(f"\n📚 Found {len(publications.get('publications', []))} publications")

    elif choice == "5":
        url = input("Enter CSV URL to download: ").strip()
        if url:
            file_path = api.download_csv_data(url)
            if file_path:
                print(f"✅ Downloaded to: {file_path}")
            else:
                print("❌ Download failed")


if __name__ == "__main__":
    main()
