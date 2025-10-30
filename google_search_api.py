#!/usr/bin/env python3
"""
Google Search API Integration
============================

Uses your existing jibber_jabber_key.json service account credentials
to provide comprehensive Google Search functionality.

Features:
- Custom Search Engine integration
- Web search with filtering
- News search
- Image search
- Results caching
- Rate limiting protection
- BigQuery integration for search analytics

Requirements:
1. Enable Custom Search API in Google Cloud Console
2. Create a Custom Search Engine at: https://cse.google.com/
3. Set your Search Engine ID in environment variables

Setup:
    export GOOGLE_SEARCH_ENGINE_ID="your_search_engine_id_here"
    export GOOGLE_API_KEY="your_api_key_here"  # Optional: can use service account instead
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSearchAPI:
    """Comprehensive Google Search API client using service account authentication."""

    def __init__(
        self,
        service_account_path: str = "jibber_jabber_key.json",
        project_id: str = "jibber-jabber-knowledge",
        search_engine_id: Optional[str] = None,
    ):
        """
        Initialize Google Search API client.

        Args:
            service_account_path: Path to service account JSON file
            project_id: Google Cloud project ID
            search_engine_id: Custom Search Engine ID
        """
        self.service_account_path = Path(service_account_path)
        self.project_id = project_id
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")

        # Initialize clients
        self.credentials = self._setup_credentials()
        self.search_service = self._setup_search_service()
        self.bq_client = self._setup_bigquery_client()

        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests

        # Results cache
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL

        logger.info("✅ Google Search API client initialized")

    def _setup_credentials(self) -> service_account.Credentials:
        """Setup service account credentials."""
        if not self.service_account_path.exists():
            raise FileNotFoundError(
                f"Service account file not found: {self.service_account_path}"
            )

        credentials = service_account.Credentials.from_service_account_file(
            str(self.service_account_path),
            scopes=[
                "https://www.googleapis.com/auth/cse",
                "https://www.googleapis.com/auth/bigquery",
            ],
        )

        logger.info(
            f"✅ Loaded service account credentials from {self.service_account_path}"
        )
        return credentials

    def _setup_search_service(self):
        """Setup Google Custom Search service."""
        try:
            service = build("customsearch", "v1", credentials=self.credentials)
            logger.info("✅ Google Custom Search service initialized")
            return service
        except Exception as e:
            logger.error(f"❌ Failed to initialize Custom Search service: {e}")
            # Fallback to API key if available
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                service = build("customsearch", "v1", developerKey=api_key)
                logger.info("✅ Using API key for Custom Search service")
                return service
            raise

    def _setup_bigquery_client(self) -> bigquery.Client:
        """Setup BigQuery client for search analytics."""
        try:
            client = bigquery.Client(
                project=self.project_id, credentials=self.credentials
            )
            logger.info("✅ BigQuery client initialized for search analytics")
            return client
        except Exception as e:
            logger.warning(f"⚠️  BigQuery client setup failed: {e}")
            return None

    def _rate_limit(self):
        """Enforce rate limiting between API requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cache_key(self, query: str, **kwargs) -> str:
        """Generate cache key for search results."""
        cache_data = {"query": query, **kwargs}
        return hash(str(sorted(cache_data.items())))

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cached result is still valid."""
        return time.time() - timestamp < self.cache_ttl

    def search(
        self,
        query: str,
        num_results: int = 10,
        search_type: str = "web",
        language: str = "lang_en",
        country: str = "countryUK",
        date_restrict: Optional[str] = None,
        file_type: Optional[str] = None,
        site_search: Optional[str] = None,
        exact_terms: Optional[str] = None,
        exclude_terms: Optional[str] = None,
        cache_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform Google search with comprehensive filtering options.

        Args:
            query: Search query
            num_results: Number of results to return (1-100)
            search_type: Type of search ("web", "image", "news")
            language: Language restriction (e.g., "lang_en")
            country: Country restriction (e.g., "countryUK")
            date_restrict: Date restriction (e.g., "d1", "w1", "m1", "y1")
            file_type: File type filter (e.g., "pdf", "doc", "xls")
            site_search: Restrict to specific site (e.g., "gov.uk")
            exact_terms: Terms that must appear exactly
            exclude_terms: Terms to exclude from results
            cache_results: Whether to cache results

        Returns:
            Dict containing search results and metadata
        """
        if not self.search_engine_id:
            raise ValueError(
                "Search Engine ID not configured. Set GOOGLE_SEARCH_ENGINE_ID environment variable."
            )

        # Check cache first
        cache_key = self._get_cache_key(
            query,
            num_results=num_results,
            search_type=search_type,
            language=language,
            country=country,
            date_restrict=date_restrict,
            file_type=file_type,
            site_search=site_search,
            exact_terms=exact_terms,
            exclude_terms=exclude_terms,
        )

        if cache_results and cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if self._is_cache_valid(timestamp):
                logger.info(f"📋 Returning cached results for: {query}")
                return cached_result

        # Rate limiting
        self._rate_limit()

        try:
            # Build search parameters
            search_params = {
                "q": query,
                "cx": self.search_engine_id,
                "num": min(num_results, 100),  # API limit is 100
            }

            # Add optional parameters
            if language:
                search_params["lr"] = language
            if country:
                search_params["cr"] = country
            if date_restrict:
                search_params["dateRestrict"] = date_restrict
            if file_type:
                search_params["fileType"] = file_type
            if site_search:
                search_params["siteSearch"] = site_search
            if exact_terms:
                search_params["exactTerms"] = exact_terms
            if exclude_terms:
                search_params["excludeTerms"] = exclude_terms

            # Set search type
            if search_type == "image":
                search_params["searchType"] = "image"
            elif search_type == "news":
                search_params["sort"] = "date"

            logger.info(f"🔍 Searching Google: '{query}' ({search_type})")

            # Execute search
            result = self.search_service.cse().list(**search_params).execute()

            # Process results
            processed_result = self._process_search_results(result, query, search_type)

            # Cache results
            if cache_results:
                self.cache[cache_key] = (processed_result, time.time())

            # Log search to BigQuery (optional)
            self._log_search_to_bigquery(
                query, search_type, len(processed_result.get("items", []))
            )

            logger.info(
                f"✅ Found {len(processed_result.get('items', []))} results for '{query}'"
            )
            return processed_result

        except HttpError as e:
            logger.error(f"❌ Google Search API error: {e}")
            if "rateLimitExceeded" in str(e):
                logger.warning("⏱️  Rate limit exceeded, waiting 60 seconds...")
                time.sleep(60)
                return self.search(query, num_results, search_type, cache_results=False)
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected search error: {e}")
            raise

    def _process_search_results(
        self, raw_result: Dict, query: str, search_type: str
    ) -> Dict[str, Any]:
        """Process and enrich search results."""
        processed = {
            "query": query,
            "search_type": search_type,
            "timestamp": datetime.now().isoformat(),
            "total_results": int(
                raw_result.get("searchInformation", {}).get("totalResults", 0)
            ),
            "search_time": float(
                raw_result.get("searchInformation", {}).get("searchTime", 0)
            ),
            "items": [],
        }

        for item in raw_result.get("items", []):
            processed_item = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "display_link": item.get("displayLink", ""),
                "formatted_url": item.get("formattedUrl", ""),
            }

            # Add image-specific fields
            if search_type == "image" and "image" in item:
                processed_item.update(
                    {
                        "image_url": item["image"].get("contextLink", ""),
                        "thumbnail_link": item["image"].get("thumbnailLink", ""),
                        "image_width": item["image"].get("width"),
                        "image_height": item["image"].get("height"),
                    }
                )

            # Add page metadata if available
            if "pagemap" in item:
                pagemap = item["pagemap"]
                if "metatags" in pagemap and pagemap["metatags"]:
                    meta = pagemap["metatags"][0]
                    processed_item["meta"] = {
                        "description": meta.get("description", ""),
                        "keywords": meta.get("keywords", ""),
                        "author": meta.get("author", ""),
                        "publish_date": meta.get("article:published_time", ""),
                    }

            processed["items"].append(processed_item)

        return processed

    def _log_search_to_bigquery(self, query: str, search_type: str, results_count: int):
        """Log search activity to BigQuery for analytics."""
        if not self.bq_client:
            return

        try:
            table_id = f"{self.project_id}.uk_energy_insights.google_search_analytics"

            rows_to_insert = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "query": query,
                    "search_type": search_type,
                    "results_count": results_count,
                    "user_agent": "jibber-jabber-search-api",
                }
            ]

            errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
            if not errors:
                logger.debug(f"📊 Logged search to BigQuery: {query}")
            else:
                logger.warning(f"⚠️  BigQuery logging errors: {errors}")

        except Exception as e:
            logger.warning(f"⚠️  Failed to log search to BigQuery: {e}")

    def search_energy_news(
        self, keywords: List[str], days_back: int = 7, max_results: int = 20
    ) -> Dict[str, Any]:
        """Search for energy-related news articles."""
        query_terms = " OR ".join([f'"{keyword}"' for keyword in keywords])
        date_filter = f"d{days_back}"

        return self.search(
            query=query_terms,
            num_results=max_results,
            search_type="news",
            date_restrict=date_filter,
            site_search="",  # All news sites
            language="lang_en",
            country="countryUK",
        )

    def search_government_documents(
        self, topic: str, file_types: List[str] = ["pdf"], max_results: int = 10
    ) -> Dict[str, Any]:
        """Search UK government documents on specific topics."""
        results = {}

        for file_type in file_types:
            search_result = self.search(
                query=topic,
                num_results=max_results,
                search_type="web",
                file_type=file_type,
                site_search="gov.uk",
                language="lang_en",
                country="countryUK",
            )
            results[file_type] = search_result

        return results

    def search_energy_companies(
        self,
        company_name: str,
        context: str = "energy electricity",
        max_results: int = 15,
    ) -> Dict[str, Any]:
        """Search for information about energy companies."""
        query = f'"{company_name}" {context}'

        return self.search(
            query=query,
            num_results=max_results,
            search_type="web",
            language="lang_en",
            country="countryUK",
            exclude_terms="job jobs career careers",  # Exclude job listings
        )

    def clear_cache(self):
        """Clear search results cache."""
        self.cache.clear()
        logger.info("🧹 Search cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        valid_entries = sum(
            1
            for _, (_, timestamp) in self.cache.items()
            if self._is_cache_valid(timestamp)
        )

        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl_hours": self.cache_ttl / 3600,
        }


def main():
    """Demo usage of Google Search API."""
    try:
        # Initialize search client
        search_api = GoogleSearchAPI()

        print("🔍 Google Search API Demo")
        print("=" * 50)

        # Example 1: Energy news search
        print("\n📰 Searching energy news...")
        news_results = search_api.search_energy_news(
            keywords=["renewable energy", "wind power", "solar", "battery storage"],
            days_back=7,
            max_results=5,
        )

        print(f"Found {len(news_results.get('items', []))} news articles")
        for item in news_results.get("items", [])[:3]:
            print(f"  • {item['title']}")
            print(f"    {item['link']}")

        # Example 2: Government document search
        print("\n📄 Searching government documents...")
        gov_docs = search_api.search_government_documents(
            topic="energy transition net zero", file_types=["pdf"], max_results=3
        )

        pdf_results = gov_docs.get("pdf", {}).get("items", [])
        print(f"Found {len(pdf_results)} PDF documents")
        for item in pdf_results[:2]:
            print(f"  • {item['title']}")
            print(f"    {item['link']}")

        # Example 3: Energy company search
        print("\n🏢 Searching energy company info...")
        company_results = search_api.search_energy_companies(
            company_name="National Grid",
            context="electricity transmission UK",
            max_results=5,
        )

        print(f"Found {len(company_results.get('items', []))} results")
        for item in company_results.get("items", [])[:2]:
            print(f"  • {item['title']}")
            print(f"    {item['snippet'][:100]}...")

        # Cache stats
        print(f"\n📊 Cache stats: {search_api.get_cache_stats()}")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("\n📋 Setup checklist:")
        print("  1. Enable Custom Search API in Google Cloud Console")
        print("  2. Create Custom Search Engine at: https://cse.google.com/")
        print("  3. Set environment variable: export GOOGLE_SEARCH_ENGINE_ID='your_id'")
        print("  4. Ensure jibber_jabber_key.json has proper permissions")


if __name__ == "__main__":
    main()
