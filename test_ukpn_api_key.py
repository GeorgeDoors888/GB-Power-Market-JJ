#!/usr/bin/env python3
"""
UKPN API Key Test
================

Test the UKPN API key to see if it resolves the 403 Forbidden issues.
"""

import json
import logging
from datetime import datetime

import requests

# Setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class UKPNAPITester:
    """Test UKPN API access with the provided key."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Authorization": f"apikey {api_key}",  # Try different auth formats
                "X-API-Key": api_key,
                "apikey": api_key,
            }
        )

    def test_endpoint_access(self, url: str, description: str) -> dict:
        """Test access to a specific endpoint."""

        logger.info(f"🔍 Testing: {description}")
        logger.info(f"URL: {url}")

        try:
            # Try GET request first
            response = self.session.get(url, timeout=15)

            result = {
                "url": url,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_size": len(response.content),
                "content_type": response.headers.get("content-type", "unknown"),
                "headers": dict(response.headers),
                "error": None,
            }

            if response.status_code == 200:
                logger.info(
                    f"✅ SUCCESS: {response.status_code} - {len(response.content)} bytes"
                )

                # Try to preview content
                if "text/csv" in response.headers.get("content-type", ""):
                    preview = response.text[:500]
                    logger.info(f"📊 CSV Preview: {preview[:100]}...")
                    result["preview"] = preview[:200]
                elif "application/json" in response.headers.get("content-type", ""):
                    try:
                        json_data = response.json()
                        logger.info(
                            f"📊 JSON Structure: {type(json_data)} with {len(json_data) if isinstance(json_data, (list, dict)) else 'unknown'} items"
                        )
                        result["json_preview"] = (
                            str(json_data)[:200] if json_data else "Empty"
                        )
                    except:
                        logger.info("📊 JSON parsing failed")

            else:
                logger.warning(f"❌ FAILED: {response.status_code} - {response.reason}")
                result["error"] = f"{response.status_code}: {response.reason}"

            return result

        except Exception as e:
            logger.error(f"💥 EXCEPTION: {e}")
            return {"url": url, "status_code": None, "success": False, "error": str(e)}

    def test_api_discovery(self):
        """Test API discovery endpoints."""

        logger.info("🚀 Testing UKPN API Discovery")
        logger.info("=" * 50)

        discovery_endpoints = [
            ("Main Portal", "https://ukpowernetworks.opendatasoft.com/"),
            ("API Root", "https://ukpowernetworks.opendatasoft.com/api/"),
            (
                "API v2.1 Catalog",
                "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/",
            ),
            (
                "API v2.1 Datasets",
                "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/",
            ),
        ]

        results = {}
        for name, url in discovery_endpoints:
            results[name] = self.test_endpoint_access(url, name)

        return results

    def test_specific_datasets(self):
        """Test access to specific UKPN datasets that previously failed."""

        logger.info("\n🎯 Testing Specific UKPN Datasets")
        logger.info("=" * 40)

        # Key datasets that were failing before
        datasets = [
            {
                "name": "LTDS Circuit Data",
                "id": "ltds-table-1-circuit-data",
                "description": "Long Term Development Statement - Circuit Data",
            },
            {
                "name": "Network Capacity Map",
                "id": "network-capacity-map",
                "description": "Distribution network capacity mapping",
            },
            {
                "name": "Primary Transformer Data",
                "id": "ukpn-primary-transformer-power-flow-historic-monthly",
                "description": "Historical primary transformer power flows",
            },
            {
                "name": "Circuit Operational Data",
                "id": "ukpn-33kv-circuit-operational-data-monthly",
                "description": "33kV circuit monthly operational data",
            },
            {
                "name": "Network Losses",
                "id": "ukpn-network-losses",
                "description": "Distribution network loss data",
            },
        ]

        results = {}

        for dataset in datasets:
            logger.info(f"\n📊 Dataset: {dataset['name']}")
            logger.info(f"Description: {dataset['description']}")

            # Test different URL patterns
            urls_to_test = [
                # v2.1 API formats
                f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset['id']}/",
                f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset['id']}/exports/csv",
                f"https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset['id']}/records/",
                # v1.0 API formats
                f"https://ukpowernetworks.opendatasoft.com/api/records/1.0/search/?dataset={dataset['id']}",
                f"https://ukpowernetworks.opendatasoft.com/api/records/1.0/download/?dataset={dataset['id']}&format=csv",
            ]

            dataset_results = {}
            for url in urls_to_test:
                url_type = "v2.1" if "v2.1" in url else "v1.0"
                if "exports/csv" in url:
                    url_type += "_csv_export"
                elif "records" in url:
                    url_type += "_records"
                elif "search" in url:
                    url_type += "_search"

                dataset_results[url_type] = self.test_endpoint_access(
                    url, f"{dataset['name']} - {url_type}"
                )

            results[dataset["name"]] = dataset_results

        return results

    def run_comprehensive_test(self):
        """Run comprehensive API key test."""

        logger.info("🔑 UKPN API Key Comprehensive Test")
        logger.info("=" * 60)
        logger.info(f"API Key: {self.api_key[:20]}... (truncated)")
        logger.info(f"Test Time: {datetime.now()}")

        # Test discovery
        discovery_results = self.test_api_discovery()

        # Test specific datasets
        dataset_results = self.test_specific_datasets()

        # Generate summary
        logger.info("\n📋 TEST SUMMARY")
        logger.info("=" * 30)

        total_tests = 0
        successful_tests = 0

        # Count discovery results
        for name, result in discovery_results.items():
            total_tests += 1
            if result.get("success"):
                successful_tests += 1
                logger.info(f"✅ {name}: SUCCESS")
            else:
                logger.info(f"❌ {name}: {result.get('error', 'FAILED')}")

        # Count dataset results
        for dataset_name, dataset_tests in dataset_results.items():
            for test_type, result in dataset_tests.items():
                total_tests += 1
                if result.get("success"):
                    successful_tests += 1
                    logger.info(f"✅ {dataset_name} ({test_type}): SUCCESS")
                else:
                    error = result.get("error", "FAILED")[:50]
                    logger.info(f"❌ {dataset_name} ({test_type}): {error}")

        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0

        logger.info(f"\n🎯 OVERALL RESULTS:")
        logger.info(
            f"Success Rate: {successful_tests}/{total_tests} ({success_rate:.1f}%)"
        )

        if successful_tests > 0:
            logger.info("🎉 API KEY IS WORKING! Some endpoints are accessible.")
            logger.info("✅ You can now collect UKPN data!")
        else:
            logger.info("❌ API key did not resolve access issues.")
            logger.info(
                "💡 May need different authentication method or additional permissions."
            )

        return {
            "discovery": discovery_results,
            "datasets": dataset_results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate,
            },
        }


def main():
    """Main execution."""

    # API Key provided by user
    api_key = "d9bf83f6ad2d8960ace2fec0cd5bbc2243f5771144e06abc9acb16bf"

    print("🔑 Testing UKPN API Key")
    print("=" * 30)
    print(f"Key: {api_key[:30]}...")
    print()

    tester = UKPNAPITester(api_key)
    results = tester.run_comprehensive_test()

    # Save results for reference
    import json

    results_file = f"ukpn_api_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n📄 Detailed results saved: {results_file}")

    if results["summary"]["successful_tests"] > 0:
        print("\n🚀 NEXT STEPS:")
        print("1. ✅ API key is working for some endpoints")
        print("2. 🔄 Update DNO collector to use this API key")
        print("3. 📥 Download UKPN datasets")
        print("4. 🏗️ Integrate with your BMRS data pipeline")
    else:
        print("\n🔍 TROUBLESHOOTING:")
        print("1. ❓ Check if API key needs activation time")
        print("2. 📧 Contact UKPN support for authentication format")
        print("3. 🔄 Try different header formats")
        print("4. 📖 Check UKPN API documentation")


if __name__ == "__main__":
    main()
