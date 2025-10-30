#!/usr/bin/env python3
"""
Test Alternative OpenDataSoft Endpoints
=======================================

Test different API versions and endpoints to find working access methods
for OpenDataSoft portals (UKPN, SPEN, NPG, ENWL).
"""

import json
import logging
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class OpenDataSoftTester:
    """Test various OpenDataSoft API endpoints and formats"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

        self.portals = {
            "UKPN": "https://ukpowernetworks.opendatasoft.com",
            "SPEN": "https://spenergynetworks.opendatasoft.com",
            "NPG": "https://northernpowergrid.opendatasoft.com",
            "ENWL": "https://electricitynorthwest.opendatasoft.com",
        }

        self.results = {}

    def test_all_endpoints(self, dataset_id: str) -> dict:
        """Test all possible endpoint variations for a dataset"""

        endpoints = {
            # API v2.1 (current)
            "v2.1_records": "/api/explore/v2.1/catalog/datasets/{}/records",
            "v2.1_csv_export": "/api/explore/v2.1/catalog/datasets/{}/exports/csv",
            "v2.1_json_export": "/api/explore/v2.1/catalog/datasets/{}/exports/json",
            "v2.1_parquet_export": "/api/explore/v2.1/catalog/datasets/{}/exports/parquet",
            # API v2.0
            "v2.0_records": "/api/v2/catalog/datasets/{}/records",
            "v2.0_exports": "/api/v2/catalog/datasets/{}/exports",
            # API v1.0 (legacy)
            "v1.0_download_csv": "/api/records/1.0/download/?dataset={}&format=csv",
            "v1.0_download_json": "/api/records/1.0/download/?dataset={}&format=json",
            "v1.0_search": "/api/records/1.0/search/?dataset={}",
            # Direct download attempts
            "direct_csv": "/explore/dataset/{}/download/?format=csv",
            "direct_json": "/explore/dataset/{}/download/?format=json",
            # OData endpoints
            "odata": "/api/odata/catalog/datasets/{}",
        }

        results = {}

        for portal_name, base_url in self.portals.items():
            portal_results = {}

            for endpoint_name, endpoint_template in endpoints.items():
                endpoint_url = base_url + endpoint_template.format(dataset_id)

                try:
                    response = self.session.get(endpoint_url, timeout=10)

                    portal_results[endpoint_name] = {
                        "url": endpoint_url,
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type", ""),
                        "content_length": len(response.content),
                        "success": response.status_code == 200,
                        "has_data": response.status_code == 200
                        and len(response.content) > 100,
                    }

                    # Log promising results
                    if response.status_code == 200:
                        logger.info(
                            f"✅ {portal_name}/{endpoint_name}: {response.status_code} ({len(response.content)} bytes)"
                        )
                    elif response.status_code == 403:
                        logger.warning(
                            f"🔒 {portal_name}/{endpoint_name}: 403 Forbidden"
                        )
                    else:
                        logger.debug(
                            f"❌ {portal_name}/{endpoint_name}: {response.status_code}"
                        )

                except Exception as e:
                    portal_results[endpoint_name] = {
                        "url": endpoint_url,
                        "error": str(e),
                        "success": False,
                    }
                    logger.debug(f"💥 {portal_name}/{endpoint_name}: {e}")

                time.sleep(0.2)  # Rate limiting

            results[portal_name] = portal_results
            time.sleep(0.5)  # Portal rate limiting

        return results

    def find_working_endpoints(self) -> dict:
        """Test with known dataset IDs to find working access methods"""

        # Test datasets from our previous successful collection
        test_datasets = [
            "ukpn-network-losses",  # Known UKPN dataset
            "flex_dispatch",  # Known SPEN dataset
            "smart-meter-penetration-by-transformer-level",  # SPEN
        ]

        all_results = {}
        working_methods = {}

        for dataset_id in test_datasets:
            logger.info(f"\n🧪 Testing dataset: {dataset_id}")
            results = self.test_all_endpoints(dataset_id)
            all_results[dataset_id] = results

            # Find working methods for this dataset
            for portal_name, portal_results in results.items():
                working_endpoints = [
                    endpoint
                    for endpoint, result in portal_results.items()
                    if result.get("success") and result.get("has_data")
                ]

                if working_endpoints:
                    if portal_name not in working_methods:
                        working_methods[portal_name] = {}
                    working_methods[portal_name][dataset_id] = working_endpoints

                    logger.info(
                        f"🎉 {portal_name} has {len(working_endpoints)} working endpoints for {dataset_id}"
                    )

        return all_results, working_methods

    def test_public_access_patterns(self) -> dict:
        """Test if any datasets are still publicly accessible"""

        public_patterns = {}

        for portal_name, base_url in self.portals.items():
            logger.info(f"\n🔍 Testing public access patterns for {portal_name}")

            # Test catalog access
            catalog_url = f"{base_url}/api/v2/catalog/datasets"
            try:
                response = self.session.get(catalog_url, params={"rows": 5}, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    datasets = data.get("datasets", [])

                    logger.info(
                        f"📊 {portal_name}: Catalog accessible, {len(datasets)} datasets found"
                    )

                    # Test if any individual datasets are public
                    public_count = 0
                    for dataset_info in datasets:
                        dataset_data = dataset_info.get("dataset", {})
                        dataset_id = dataset_data.get("dataset_id")

                        if dataset_id:
                            # Try simple records endpoint
                            records_url = f"{base_url}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
                            try:
                                records_response = self.session.get(
                                    records_url, params={"limit": 1}, timeout=5
                                )
                                if records_response.status_code == 200:
                                    public_count += 1
                                    logger.info(
                                        f"✅ {portal_name}/{dataset_id}: Records accessible"
                                    )
                            except:
                                pass

                    public_patterns[portal_name] = {
                        "catalog_accessible": True,
                        "total_datasets": len(datasets),
                        "public_datasets": public_count,
                        "has_public_data": public_count > 0,
                    }

                else:
                    logger.warning(
                        f"❌ {portal_name}: Catalog not accessible ({response.status_code})"
                    )
                    public_patterns[portal_name] = {"catalog_accessible": False}

            except Exception as e:
                logger.error(f"💥 {portal_name}: Error testing catalog - {e}")
                public_patterns[portal_name] = {"error": str(e)}

        return public_patterns


def main():
    """Test all alternative OpenDataSoft endpoints"""

    logger.info("🚀 Testing Alternative OpenDataSoft Endpoints")
    logger.info("=" * 60)

    tester = OpenDataSoftTester()

    # Test specific endpoints
    logger.info("\n1️⃣ Testing specific dataset endpoints...")
    all_results, working_methods = tester.find_working_endpoints()

    # Test public access patterns
    logger.info("\n2️⃣ Testing public access patterns...")
    public_patterns = tester.test_public_access_patterns()

    # Save results
    output_dir = Path("ods_endpoint_test_results")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "all_endpoint_results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    with open(output_dir / "working_methods.json", "w") as f:
        json.dump(working_methods, f, indent=2)

    with open(output_dir / "public_access_patterns.json", "w") as f:
        json.dump(public_patterns, f, indent=2)

    # Summary
    logger.info("\n📋 SUMMARY")
    logger.info("=" * 30)

    total_working = sum(len(methods) for methods in working_methods.values())
    total_public = sum(
        1 for pattern in public_patterns.values() if pattern.get("has_public_data")
    )

    logger.info(f"Working endpoint combinations found: {total_working}")
    logger.info(f"Portals with public data: {total_public}/{len(tester.portals)}")

    for portal_name, pattern in public_patterns.items():
        if pattern.get("has_public_data"):
            logger.info(
                f"✅ {portal_name}: {pattern.get('public_datasets', 0)} public datasets"
            )
        else:
            logger.info(f"❌ {portal_name}: No public data access")

    logger.info(f"\nResults saved to: {output_dir}")

    return len(working_methods) > 0


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Found working OpenDataSoft endpoints!")
    else:
        print(
            "\n😞 No working OpenDataSoft endpoints found - need alternative approaches"
        )
