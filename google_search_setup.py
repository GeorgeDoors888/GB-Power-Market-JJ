#!/usr/bin/env python3
"""
Google Custom Search JSON API Setup and Configuration
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

import requests


class GoogleCustomSearch:
    """
    Google Custom Search JSON API client
    """

    def __init__(
        self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None
    ):
        """
        Initialize the Google Custom Search client

        Args:
            api_key: Google API key for Custom Search JSON API
            search_engine_id: Custom Search Engine ID (cx parameter)
        """
        self.api_key = (
            api_key
            or self._load_api_key_from_json()
            or os.getenv("GOOGLE_SEARCH_API_KEY")
        )
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"

        if not self.api_key:
            raise ValueError(
                "Google Search API key is required. Set GOOGLE_SEARCH_API_KEY environment variable, pass api_key parameter, or add to jibber_jaber_key.json"
            )

        if not self.search_engine_id:
            raise ValueError(
                "Google Search Engine ID is required. Set GOOGLE_SEARCH_ENGINE_ID environment variable or pass search_engine_id parameter."
            )

    def _load_api_key_from_json(self):
        """Load Google Search API key from the service account JSON file."""
        try:
            with open("jibber_jaber_key.json", "r") as f:
                credentials = json.load(f)
            return credentials.get("google_search_api_key")
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None

    def search(
        self,
        query: str,
        num_results: int = 10,
        start_index: int = 1,
        file_type: Optional[str] = None,
        site_search: Optional[str] = None,
        exclude_terms: Optional[List[str]] = None,
        exact_terms: Optional[str] = None,
        language: str = "en",
    ) -> Dict:
        """
        Perform a Google Custom Search

        Args:
            query: Search query string
            num_results: Number of results to return (1-10)
            start_index: Starting index for results (1-based)
            file_type: Filter by file type (e.g., 'pdf', 'doc', 'xls')
            site_search: Restrict search to specific site (e.g., 'example.com')
            exclude_terms: List of terms to exclude from search
            exact_terms: Exact phrase to search for
            language: Language for search results

        Returns:
            Dictionary containing search results
        """

        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),  # API limit is 10 per request
            "start": start_index,
            "hl": language,
        }

        # Add optional parameters
        if file_type:
            params["fileType"] = file_type

        if site_search:
            params["siteSearch"] = site_search

        if exclude_terms:
            params["excludeTerms"] = " ".join(exclude_terms)

        if exact_terms:
            params["exactTerms"] = exact_terms

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Error making search request: {e}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing response JSON: {e}")
            return {}

    def search_dno_data(
        self, dno_name: str, data_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for DNO (Distribution Network Operator) data

        Args:
            dno_name: Name of the DNO (e.g., "SSEN", "Northern Powergrid")
            data_types: List of data types to search for (e.g., ["DUoS", "charges", "tariffs"])

        Returns:
            List of relevant search results
        """

        if data_types is None:
            data_types = [
                "DUoS charges",
                "distribution charges",
                "tariffs",
                "open data",
            ]

        all_results = []

        for data_type in data_types:
            query = f"{dno_name} {data_type} site:*.gov.uk OR site:*.co.uk"

            print(f"🔍 Searching for: {query}")

            results = self.search(
                query=query,
                num_results=10,
                file_type="xlsx",  # Focus on Excel files which often contain tariff data
            )

            if "items" in results:
                for item in results["items"]:
                    all_results.append(
                        {
                            "title": item.get("title", ""),
                            "url": item.get("link", ""),
                            "snippet": item.get("snippet", ""),
                            "file_format": item.get("fileFormat", ""),
                            "dno": dno_name,
                            "search_term": data_type,
                        }
                    )

        return all_results

    def test_connection(self) -> bool:
        """
        Test the API connection with a simple search

        Returns:
            True if connection is successful, False otherwise
        """

        try:
            test_result = self.search("test", num_results=1)

            if "error" in test_result:
                print(f"❌ API Error: {test_result['error']['message']}")
                return False

            if "searchInformation" in test_result:
                total_results = test_result["searchInformation"].get(
                    "totalResults", "0"
                )
                print(
                    f"✅ API connection successful! Total searchable pages: {total_results}"
                )
                return True

            return False

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False


def setup_environment():
    """
    Interactive setup for Google Custom Search API credentials
    """

    print("🔧 GOOGLE CUSTOM SEARCH JSON API SETUP")
    print("=" * 50)
    print()

    print("📋 You'll need:")
    print("1. Google API Key with Custom Search JSON API enabled")
    print("2. Custom Search Engine ID (cx parameter)")
    print()
    print("📖 Setup Guide:")
    print("1. Go to: https://console.developers.google.com/")
    print("2. Create/select a project")
    print("3. Enable 'Custom Search JSON API'")
    print("4. Create credentials (API Key)")
    print("5. Go to: https://cse.google.com/cse/")
    print("6. Create a Custom Search Engine")
    print("7. Get the Search Engine ID")
    print()

    # Check if credentials already exist
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if api_key and search_engine_id:
        print("✅ Found existing credentials in environment variables:")
        print(f"   API Key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
        print(f"   Search Engine ID: {search_engine_id}")

        # Test the connection
        try:
            search_client = GoogleCustomSearch(api_key, search_engine_id)
            if search_client.test_connection():
                print("✅ API is working correctly!")
                return search_client
            else:
                print("❌ API test failed - please check your credentials")
        except Exception as e:
            print(f"❌ Error testing API: {e}")

    print("\n🔑 Please enter your credentials:")

    if not api_key:
        api_key = input("Google API Key: ").strip()

    if not search_engine_id:
        search_engine_id = input("Custom Search Engine ID: ").strip()

    # Create environment file
    env_content = f"""# Google Custom Search JSON API Configuration
GOOGLE_SEARCH_API_KEY={api_key}
GOOGLE_SEARCH_ENGINE_ID={search_engine_id}
"""

    with open(".env.search", "w") as f:
        f.write(env_content)

    print("\n💾 Credentials saved to .env.search file")
    print("💡 To use in your shell, run: source .env.search")

    # Test the new credentials
    try:
        os.environ["GOOGLE_SEARCH_API_KEY"] = api_key
        os.environ["GOOGLE_SEARCH_ENGINE_ID"] = search_engine_id

        search_client = GoogleCustomSearch()
        if search_client.test_connection():
            print("✅ Setup successful! API is working.")
            return search_client
        else:
            print("❌ Setup failed - please check your credentials")
            return None
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return None


def demo_dno_search(search_client: GoogleCustomSearch):
    """
    Demonstrate DNO data search functionality
    """

    print("\n🔍 DEMO: Searching for DNO Data")
    print("=" * 40)

    # List of DNOs to search for
    dnos_to_search = [
        "SSEN Scottish Hydro Electric",
        "Northern Powergrid",
        "National Grid Electricity Distribution",
        "SP Energy Networks",
        "Electricity North West ENWL",
    ]

    all_found_data = []

    for dno in dnos_to_search:
        print(f"\n📊 Searching for {dno} data...")

        results = search_client.search_dno_data(
            dno_name=dno,
            data_types=["DUoS charges", "distribution tariffs", "connection charges"],
        )

        if results:
            print(f"   ✅ Found {len(results)} potential data sources")
            for result in results[:3]:  # Show first 3 results
                print(f"     • {result['title']}")
                print(f"       {result['url']}")
            all_found_data.extend(results)
        else:
            print(f"   ❌ No data found for {dno}")

    # Save results
    if all_found_data:
        output_file = (
            f"dno_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w") as f:
            json.dump(all_found_data, f, indent=2)

        print(f"\n💾 Search results saved to: {output_file}")
        print(f"📊 Total data sources found: {len(all_found_data)}")


if __name__ == "__main__":
    # Setup the API
    search_client = setup_environment()

    if search_client:
        # Run demo search
        demo_dno_search(search_client)
    else:
        print("❌ Setup failed. Please check your credentials and try again.")
