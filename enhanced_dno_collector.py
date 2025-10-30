#!/usr/bin/env python3
"""
Enhanced DNO Data Collector
Combines comprehensive API access with our existing discovery framework
"""

import json
import logging
import os
import sqlite3
import time
import urllib.parse as up
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------
# Configuration
# --------------------

OUT_ROOT = Path("data_all_dnos")
DB_PATH = OUT_ROOT / "dno_enhanced.sqlite"
LOG_FILE = OUT_ROOT / "dno_collection_log.json"

# OpenDataSoft domains (standardized API access)
DNOS_ODS = {
    "UKPN": "https://ukpowernetworks.opendatasoft.com",
    "SPEN": "https://spenergynetworks.opendatasoft.com",
    "NPG": "https://northernpowergrid.opendatasoft.com",
    "ENWL": "https://electricitynorthwest.opendatasoft.com",
}

# API credentials (set as environment variables)
SPEN_API_KEY = os.getenv("SPEN_API_KEY", "")
NGED_API_TOKEN = os.getenv("NGED_API_TOKEN", "")

# Additional sources
SSEN_ECR_PAGE = "https://data.ssen.co.uk/ssen-distribution/embedded_capacity_register"
SSEN_CATALOG_URL = "https://ckan-prod.sse.datopian.com/catalog.jsonld"

# Enhanced search terms for comprehensive discovery
SEARCH_TERMS = [
    "duos",
    "use of system",
    "embedded capacity",
    "capacity",
    "outage",
    "flexibility",
    "asset",
    "substation",
    "generation",
    "connection",
    "EV",
    "demand",
    "tariff",
    "charges",
    "network",
    "distribution",
    "voltage",
    "transformer",
    "fault",
    "interruption",
    "load",
    "peak",
    "constraint",
    "planning",
    "development",
]

# HTTP session with proper headers
session = requests.Session()
session.headers.update(
    {
        "User-Agent": "UK-Energy-Data-Collector/2.0",
        "Accept": "application/json, text/csv, text/html",
        "Accept-Encoding": "gzip, deflate",
    }
)

# Collection statistics
collection_stats = {
    "start_time": datetime.now().isoformat(),
    "dnos_processed": {},
    "total_datasets": 0,
    "successful_downloads": 0,
    "failed_downloads": 0,
    "total_rows": 0,
}

# --------------------
# Utilities
# --------------------


def slug(s: str) -> str:
    """Convert string to safe filename"""
    import re

    return re.sub(r"[^A-Za-z0-9_]+", "_", s).strip("_").lower()


def save_dataframe(df: pd.DataFrame, dno: str, name: str, metadata: dict = None):
    """Save dataframe to multiple formats with metadata"""
    if df.empty:
        logger.warning(f"Empty dataframe for {dno}/{name}")
        return

    # Create directory structure
    dno_dir = OUT_ROOT / dno
    dno_dir.mkdir(parents=True, exist_ok=True)

    safe_name = slug(name)

    # Save as Parquet (most efficient)
    parquet_path = dno_dir / f"{safe_name}.parquet"
    df.to_parquet(parquet_path, index=False, engine="pyarrow")

    # Save as CSV (human readable)
    csv_path = dno_dir / f"{safe_name}.csv"
    df.to_csv(csv_path, index=False)

    # Save metadata
    if metadata:
        metadata_path = dno_dir / f"{safe_name}_metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

    # SQLite storage
    try:
        conn = sqlite3.connect(DB_PATH)
        table_name = f"{slug(dno)}__{safe_name}"
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        logger.info(f"✅ Saved {dno}/{name}: {len(df)} rows")

        # Update stats
        collection_stats["successful_downloads"] += 1
        collection_stats["total_rows"] += len(df)

    except Exception as e:
        logger.error(f"❌ Failed to save {dno}/{name}: {e}")
        collection_stats["failed_downloads"] += 1


def log_collection_progress():
    """Save collection progress to log file"""
    collection_stats["end_time"] = datetime.now().isoformat()
    collection_stats["duration_minutes"] = (
        datetime.fromisoformat(collection_stats["end_time"])
        - datetime.fromisoformat(collection_stats["start_time"])
    ).total_seconds() / 60

    with open(LOG_FILE, "w") as f:
        json.dump(collection_stats, f, indent=2, default=str)


# --------------------
# OpenDataSoft Enhanced Functions
# --------------------


def ods_list_datasets(domain: str, search_term: str = "", limit=200) -> list:
    """List datasets from OpenDataSoft domain"""
    url = f"{domain}/api/v2/catalog/datasets"
    params = {"rows": limit}
    if search_term:
        params["search"] = search_term

    try:
        r = session.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("datasets", [])
    except Exception as e:
        logger.error(f"Failed to list datasets from {domain}: {e}")
        return []


def ods_get_dataset_metadata(domain: str, dataset_id: str) -> dict:
    """Get detailed metadata for dataset"""
    url = f"{domain}/api/v2/catalog/datasets/{dataset_id}"
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning(f"Failed to get metadata for {dataset_id}: {e}")
        return {}


def ods_download_csv(domain: str, dataset_id: str) -> pd.DataFrame | None:
    """Download dataset as CSV"""
    url = f"{domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/exports/csv"
    try:
        r = session.get(url, timeout=120)
        if r.status_code == 200:
            from io import StringIO

            return pd.read_csv(StringIO(r.content.decode("utf-8", errors="ignore")))
    except Exception as e:
        logger.warning(f"CSV download failed for {dataset_id}: {e}")
    return None


def ods_download_json(domain: str, dataset_id: str, limit=5000) -> pd.DataFrame | None:
    """Download dataset as JSON and convert to DataFrame"""
    url = f"{domain}/api/explore/v2.1/catalog/datasets/{dataset_id}/records"
    params = {"limit": limit}
    try:
        r = session.get(url, params=params, timeout=60)
        if r.status_code == 200:
            j = r.json()
            records = j.get("results", []) or j.get("records", [])
            if records:
                return pd.json_normalize(records)
    except Exception as e:
        logger.warning(f"JSON download failed for {dataset_id}: {e}")
    return None


def ods_fetch_dno_comprehensive(domain: str, dno: str, api_key: str = None):
    """Comprehensive fetch for OpenDataSoft DNO"""
    logger.info(f"🔍 Starting comprehensive collection for {dno}")

    # Set authentication if provided
    if api_key and dno == "SPEN":
        session.headers["Authorization"] = f"Apikey {api_key}"

    datasets_processed = 0
    seen_datasets = set()

    # First, get ALL datasets (no search filter)
    logger.info(f"📋 Discovering all datasets for {dno}")
    all_datasets = ods_list_datasets(domain, "", limit=500)

    for ds in all_datasets:
        dataset_id = ds.get("dataset_id")
        if not dataset_id or dataset_id in seen_datasets:
            continue
        seen_datasets.add(dataset_id)

        # Get metadata
        metadata = ods_get_dataset_metadata(domain, dataset_id)
        title = metadata.get("metas", {}).get("title", dataset_id)

        logger.info(f"📊 Processing {dno} dataset: {title}")

        # Try CSV first (usually more complete)
        df_csv = ods_download_csv(domain, dataset_id)
        if df_csv is not None and not df_csv.empty:
            save_dataframe(df_csv, dno, f"{dataset_id}_csv", metadata)
            datasets_processed += 1
        else:
            # Fallback to JSON
            df_json = ods_download_json(domain, dataset_id)
            if df_json is not None and not df_json.empty:
                save_dataframe(df_json, dno, f"{dataset_id}_json", metadata)
                datasets_processed += 1

        # Rate limiting
        time.sleep(0.3)

    # Then, search with specific terms for missed datasets
    for term in SEARCH_TERMS:
        logger.info(f"🔍 Searching {dno} for '{term}'")
        search_datasets = ods_list_datasets(domain, term, limit=100)

        for ds in search_datasets:
            dataset_id = ds.get("dataset_id")
            if not dataset_id or dataset_id in seen_datasets:
                continue
            seen_datasets.add(dataset_id)

            metadata = ods_get_dataset_metadata(domain, dataset_id)
            title = metadata.get("metas", {}).get("title", dataset_id)

            logger.info(f"📊 Found additional {dno} dataset: {title}")

            df_csv = ods_download_csv(domain, dataset_id)
            if df_csv is not None and not df_csv.empty:
                save_dataframe(df_csv, dno, f"{dataset_id}_search_{term}", metadata)
                datasets_processed += 1

        time.sleep(0.5)

    # Clean up auth header
    session.headers.pop("Authorization", None)

    collection_stats["dnos_processed"][dno] = {
        "datasets_found": len(seen_datasets),
        "datasets_processed": datasets_processed,
        "completion_time": datetime.now().isoformat(),
    }

    logger.info(
        f"✅ {dno} collection complete: {datasets_processed} datasets processed"
    )


# --------------------
# NGED Enhanced CKAN Functions
# --------------------


def nged_comprehensive_fetch():
    """Enhanced NGED data collection via CKAN API"""
    if not NGED_API_TOKEN:
        logger.warning("⚠️ NGED_API_TOKEN not set, skipping NGED")
        return

    logger.info("🔍 Starting comprehensive NGED collection")

    base_url = "https://connecteddata.nationalgrid.co.uk/api/3/action/"
    headers = {"Authorization": NGED_API_TOKEN}

    # Get all packages first
    try:
        r = session.get(f"{base_url}package_list", headers=headers, timeout=30)
        r.raise_for_status()
        all_packages = r.json()["result"]
        logger.info(f"📋 Found {len(all_packages)} total NGED packages")
    except Exception as e:
        logger.error(f"❌ Failed to get NGED package list: {e}")
        return

    datasets_processed = 0

    for pkg_id in all_packages:
        try:
            # Get package details
            r = session.get(
                f"{base_url}package_show",
                params={"id": pkg_id},
                headers=headers,
                timeout=30,
            )
            r.raise_for_status()
            package = r.json()["result"]

            title = package.get("title", pkg_id)
            logger.info(f"📊 Processing NGED package: {title}")

            # Process all resources
            for resource in package.get("resources", []):
                url = resource.get("url")
                fmt = (resource.get("format", "")).lower()
                name = resource.get("name", f"resource_{resource.get('id', 'unknown')}")

                if not url:
                    continue

                try:
                    if fmt == "csv" or url.lower().endswith(".csv"):
                        r_data = session.get(url, timeout=120)
                        if r_data.status_code == 200:
                            df = pd.read_csv(
                                pd.compat.StringIO(
                                    r_data.content.decode("utf-8", errors="ignore")
                                )
                            )
                            if not df.empty:
                                save_dataframe(
                                    df,
                                    "NGED",
                                    f"{pkg_id}_{name}_csv",
                                    {"package": package, "resource": resource},
                                )
                                datasets_processed += 1

                    elif fmt == "json" or url.lower().endswith(".json"):
                        r_data = session.get(url, timeout=120)
                        if r_data.status_code == 200:
                            js = r_data.json()
                            # Handle different JSON structures
                            if isinstance(js, list):
                                rows = js
                            elif isinstance(js, dict):
                                rows = js.get(
                                    "records", js.get("results", js.get("data", [js]))
                                )
                            else:
                                rows = [js]

                            if rows:
                                df = pd.json_normalize(rows)
                                if not df.empty:
                                    save_dataframe(
                                        df,
                                        "NGED",
                                        f"{pkg_id}_{name}_json",
                                        {"package": package, "resource": resource},
                                    )
                                    datasets_processed += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to process NGED resource {url}: {e}")

                time.sleep(0.3)

        except Exception as e:
            logger.warning(f"⚠️ Failed to process NGED package {pkg_id}: {e}")

        time.sleep(0.5)

    collection_stats["dnos_processed"]["NGED"] = {
        "packages_found": len(all_packages),
        "datasets_processed": datasets_processed,
        "completion_time": datetime.now().isoformat(),
    }

    logger.info(f"✅ NGED collection complete: {datasets_processed} datasets processed")


# --------------------
# SSEN Enhanced Functions
# --------------------


def ssen_comprehensive_fetch():
    """Enhanced SSEN data collection"""
    logger.info("🔍 Starting comprehensive SSEN collection")

    datasets_processed = 0

    # 1. Process JSON catalog
    try:
        logger.info("📋 Processing SSEN JSON catalog")
        r = session.get(SSEN_CATALOG_URL, timeout=30)
        r.raise_for_status()
        catalog = r.json()

        for item in catalog:
            if not isinstance(item, dict):
                continue

            # Extract metadata
            title = None
            download_url = None
            if "http://purl.org/dc/terms/title" in item:
                title = item["http://purl.org/dc/terms/title"][0]["@value"]

            # Look for download URLs
            url_fields = [
                "http://www.w3.org/ns/dcat#downloadURL",
                "http://www.w3.org/ns/dcat#accessURL",
            ]

            for field in url_fields:
                if field in item:
                    download_url = item[field][0]["@id"]
                    break

            if title and download_url:
                try:
                    if download_url.lower().endswith(".csv"):
                        df = pd.read_csv(download_url)
                        if not df.empty:
                            save_dataframe(df, "SSEN", f"catalog_{slug(title)}", item)
                            datasets_processed += 1
                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to download SSEN catalog item {title}: {e}"
                    )

                time.sleep(0.3)

    except Exception as e:
        logger.error(f"❌ Failed to process SSEN catalog: {e}")

    # 2. Scrape ECR page
    try:
        logger.info("📋 Scraping SSEN ECR page")
        r = session.get(SSEN_ECR_PAGE, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        csv_links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = up.urljoin(SSEN_ECR_PAGE, href)
            if full_url.lower().endswith(".csv"):
                csv_links.add(full_url)

        for link in csv_links:
            try:
                r_csv = session.get(link, timeout=120)
                if r_csv.status_code == 200:
                    name = link.split("/")[-1].replace(".csv", "")
                    df = pd.read_csv(
                        pd.compat.StringIO(
                            r_csv.content.decode("utf-8", errors="ignore")
                        )
                    )
                    if not df.empty:
                        save_dataframe(df, "SSEN", f"ecr_{name}", {"source_url": link})
                        datasets_processed += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to download SSEN ECR file {link}: {e}")

            time.sleep(0.3)

    except Exception as e:
        logger.error(f"❌ Failed to scrape SSEN ECR page: {e}")

    collection_stats["dnos_processed"]["SSEN"] = {
        "datasets_processed": datasets_processed,
        "completion_time": datetime.now().isoformat(),
    }

    logger.info(f"✅ SSEN collection complete: {datasets_processed} datasets processed")


# --------------------
# Main Execution
# --------------------


def main():
    """Execute comprehensive DNO data collection"""
    logger.info("🚀 Starting comprehensive UK DNO data collection")

    # Create output directory
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    collection_stats["total_datasets"] = 0

    # 1. OpenDataSoft DNOs
    for dno, domain in DNOS_ODS.items():
        logger.info(f"{'='*60}")
        logger.info(f"🔄 Processing {dno} via OpenDataSoft")
        logger.info(f"{'='*60}")

        api_key = SPEN_API_KEY if dno == "SPEN" else None
        ods_fetch_dno_comprehensive(domain, dno, api_key)

    # 2. NGED via CKAN
    logger.info(f"{'='*60}")
    logger.info(f"🔄 Processing NGED via CKAN")
    logger.info(f"{'='*60}")
    nged_comprehensive_fetch()

    # 3. SSEN via multiple sources
    logger.info(f"{'='*60}")
    logger.info(f"🔄 Processing SSEN via multiple sources")
    logger.info(f"{'='*60}")
    ssen_comprehensive_fetch()

    # 4. Final statistics
    log_collection_progress()

    logger.info("🎉 DNO data collection complete!")
    logger.info(f"📊 Total datasets: {collection_stats['successful_downloads']}")
    logger.info(f"📊 Total rows: {collection_stats['total_rows']:,}")
    logger.info(f"📊 Failed downloads: {collection_stats['failed_downloads']}")
    logger.info(
        f"📊 Duration: {collection_stats.get('duration_minutes', 0):.1f} minutes"
    )

    # Print summary by DNO
    print("\n" + "=" * 70)
    print("🎯 DNO COLLECTION SUMMARY")
    print("=" * 70)
    for dno, stats in collection_stats["dnos_processed"].items():
        datasets = stats.get("datasets_processed", 0)
        print(
            f"{dno:10} | {datasets:3} datasets | {stats.get('completion_time', 'N/A')}"
        )
    print("=" * 70)


if __name__ == "__main__":
    main()
