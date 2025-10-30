#!/usr/bin/env python3
"""
DNO API Diagnostic Tool
Find the correct API endpoints and test authentication requirements
"""

import json
from datetime import datetime

import requests


def test_opendatasoft_endpoints():
    """Test various OpenDataSoft API endpoint patterns"""

    domains = {
        "UKPN": "https://ukpowernetworks.opendatasoft.com",
        "SPEN": "https://spenergynetworks.opendatasoft.com",
        "NPG": "https://northernpowergrid.opendatasoft.com",
        "ENWL": "https://electricitynorthwest.opendatasoft.com",
    }

    # Different API patterns to test
    api_patterns = [
        "/api/v2/catalog/datasets",
        "/api/catalog/v2/datasets",
        "/api/datasets",
        "/api/v1/catalog/datasets",
        "/explore/api/catalog/v2/datasets",
        "/api/explore/v2.1/catalog/datasets",
    ]

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    )

    results = {}

    for dno, domain in domains.items():
        print(f"\n🔍 Testing {dno} - {domain}")
        results[dno] = {"domain": domain, "tests": {}}

        # First check if domain is accessible
        try:
            r = session.get(domain, timeout=10)
            print(f"   Base domain: {r.status_code}")
            results[dno]["base_status"] = r.status_code
        except Exception as e:
            print(f"   Base domain: ERROR - {e}")
            results[dno]["base_status"] = f"ERROR: {e}"
            continue

        # Test different API endpoints
        for pattern in api_patterns:
            url = f"{domain}{pattern}"
            try:
                r = session.get(url, timeout=10, params={"rows": 1})
                print(f"   {pattern}: {r.status_code}")

                if r.status_code == 200:
                    try:
                        data = r.json()
                        datasets = data.get("datasets", data.get("records", []))
                        print(f"      ✅ SUCCESS - Found {len(datasets)} datasets")
                        results[dno]["tests"][pattern] = {
                            "status": r.status_code,
                            "working": True,
                            "dataset_count": len(datasets),
                        }
                    except:
                        print(f"      ⚠️ 200 but not JSON")
                        results[dno]["tests"][pattern] = {
                            "status": r.status_code,
                            "working": False,
                            "note": "Not JSON response",
                        }
                else:
                    results[dno]["tests"][pattern] = {
                        "status": r.status_code,
                        "working": False,
                    }

            except Exception as e:
                print(f"   {pattern}: ERROR - {e}")
                results[dno]["tests"][pattern] = {
                    "status": f"ERROR: {e}",
                    "working": False,
                }

    return results


def test_alternative_sources():
    """Test alternative data sources we know work"""

    print(f"\n🔍 Testing Known Working Sources")

    known_sources = {
        "SSEN_catalog": "https://ckan-prod.sse.datopian.com/catalog.jsonld",
        "SSEN_portal": "https://data.ssen.co.uk",
        "NGED_portal": "https://connecteddata.westernpower.co.uk",
        "SPD_charges": "https://www.spenergynetworks.co.uk/pages/charges_and_agreements.aspx",
    }

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
    )

    working_sources = {}

    for name, url in known_sources.items():
        try:
            r = session.get(url, timeout=15)
            print(f"   {name}: {r.status_code}")

            if r.status_code == 200:
                content_length = len(r.content)
                print(f"      ✅ SUCCESS - {content_length} bytes")
                working_sources[name] = {
                    "url": url,
                    "status": r.status_code,
                    "content_length": content_length,
                    "working": True,
                }
            else:
                working_sources[name] = {
                    "url": url,
                    "status": r.status_code,
                    "working": False,
                }

        except Exception as e:
            print(f"   {name}: ERROR - {e}")
            working_sources[name] = {
                "url": url,
                "status": f"ERROR: {e}",
                "working": False,
            }

    return working_sources


def main():
    print("🚀 DNO API DIAGNOSTIC TOOL")
    print("=" * 60)

    # Test OpenDataSoft endpoints
    print("\n📋 TESTING OPENDATASOFT APIS")
    ods_results = test_opendatasoft_endpoints()

    # Test alternative sources
    print("\n📋 TESTING ALTERNATIVE SOURCES")
    alt_results = test_alternative_sources()

    # Save results
    diagnostic_results = {
        "timestamp": datetime.now().isoformat(),
        "opendatasoft_tests": ods_results,
        "alternative_sources": alt_results,
    }

    with open("dno_api_diagnostic.json", "w") as f:
        json.dump(diagnostic_results, f, indent=2, default=str)

    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)

    print("\n🔍 OpenDataSoft Results:")
    for dno, result in ods_results.items():
        working_apis = [
            pattern
            for pattern, test in result.get("tests", {}).items()
            if test.get("working", False)
        ]
        if working_apis:
            print(f"   ✅ {dno}: {len(working_apis)} working API(s)")
            for api in working_apis:
                datasets = result["tests"][api].get("dataset_count", 0)
                print(f"      - {api} ({datasets} datasets)")
        else:
            print(f"   ❌ {dno}: No working APIs found")

    print("\n🔍 Alternative Sources:")
    for name, result in alt_results.items():
        if result.get("working", False):
            print(f"   ✅ {name}: Working ({result.get('content_length', 0)} bytes)")
        else:
            print(f"   ❌ {name}: Not working ({result.get('status', 'Unknown')})")

    print("\n💡 RECOMMENDATIONS:")

    # Count working sources
    working_ods = sum(
        1
        for dno, result in ods_results.items()
        if any(test.get("working", False) for test in result.get("tests", {}).values())
    )
    working_alt = sum(
        1 for result in alt_results.values() if result.get("working", False)
    )

    print(f"   • OpenDataSoft APIs: {working_ods}/4 DNOs accessible")
    print(f"   • Alternative sources: {working_alt}/{len(alt_results)} working")

    if working_ods > 0:
        print("   • Use OpenDataSoft for DNOs with working APIs")
    if working_alt > 0:
        print("   • Use manual collection for remaining DNOs")

    print(f"\n📄 Full results saved to: dno_api_diagnostic.json")


if __name__ == "__main__":
    main()
