#!/usr/bin/env python3
"""
Discover all DUoS datasets across Huwise/OpenDataSoft portals.

This script:
1. Searches known DNO OpenDataSoft portals
2. Discovers datasets related to DUoS/charging
3. Exports metadata (title, dataset_id, license, export URLs)
4. Saves to CSV for easy reference

Author: GB Power Market JJ
Date: 2025-10-29
"""

import requests
import time
import json
import csv
from datetime import datetime
from typing import List, Dict, Any
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Known DNO OpenDataSoft portals
DNO_PORTALS = {
    'UKPN': 'ukpowernetworks.opendatasoft.com',
    'NPg': 'northernpowergrid.opendatasoft.com',
    'ENWL': 'electricitynorthwest.opendatasoft.com',
    'SPEN': 'spenergynetworks.opendatasoft.com',
}

# Huwise Hub (for broader search)
HUWISE_HUB = 'hub.huwise.com'
PUBLIC_HUB = 'public.opendatasoft.com'

# Search terms for DUoS data
SEARCH_TERMS = [
    'duos',
    'distribution use of system',
    'charges',
    'charging',
    'dnoa',
    'tariff',
    'unit rate',
    'time of use',
    'red amber green',
]

# Rate limiting (be respectful!)
REQUEST_DELAY = 1.0  # seconds between requests


def list_all_datasets(portal: str) -> List[Dict[str, Any]]:
    """
    List ALL datasets from an OpenDataSoft portal (no filtering).
    
    Returns list of dataset metadata dicts.
    """
    # Try v1 API first (more reliable)
    url = f"https://{portal}/api/datasets/1.0/search/"
    
    params = {
        'rows': 1000,  # Get up to 1000 datasets
    }
    
    try:
        logger.info(f"Listing all datasets from {portal}")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        datasets = data.get('datasets', [])
        logger.info(f"  Found {len(datasets)} total datasets")
        
        return datasets
        
    except requests.exceptions.RequestException as e:
        logger.error(f"  Error listing {portal}: {e}")
        return []
    
    finally:
        time.sleep(REQUEST_DELAY)


def filter_duos_datasets(datasets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter datasets for DUoS-related content.
    """
    duos_keywords = [
        'duos', 'distribution', 'charges', 'charging', 
        'tariff', 'unit rate', 'time of use', 'red amber green',
        'dnoa', 'use of system', 'annex'
    ]
    
    filtered = []
    for ds in datasets:
        metas = ds.get('metas', {})
        title = metas.get('title', '').lower()
        description = metas.get('description', '').lower()
        dataset_id = ds.get('datasetid', '').lower()
        
        # Check if any keyword appears in title, description, or ID
        if any(keyword in title or keyword in description or keyword in dataset_id 
               for keyword in duos_keywords):
            filtered.append(ds)
            logger.info(f"  ✅ Match: {dataset_id}")
    
    return filtered


def get_dataset_details(portal: str, dataset_id: str) -> Dict[str, Any]:
    """
    Get detailed metadata for a specific dataset.
    """
    url = f"https://{portal}/api/v2/catalog/datasets/{dataset_id}"
    
    try:
        logger.info(f"  Fetching details for {dataset_id}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        return data.get('dataset', {})
        
    except requests.exceptions.RequestException as e:
        logger.error(f"  Error fetching {dataset_id}: {e}")
        return {}
    
    finally:
        time.sleep(REQUEST_DELAY)


def extract_metadata(portal: str, dataset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata from dataset object.
    """
    # Handle both v1 and v2 API formats
    dataset_id = dataset.get('dataset_id') or dataset.get('datasetid', '')
    metas = dataset.get('metas', {})
    
    # Get license info
    license_info = metas.get('license', 'Unknown')
    if isinstance(license_info, dict):
        license_info = license_info.get('name', 'Unknown')
    
    # Build export URLs
    csv_url = f"https://{portal}/explore/dataset/{dataset_id}/export/?format=csv"
    json_url = f"https://{portal}/api/records/1.0/search/?dataset={dataset_id}&rows=10000"
    geojson_url = f"https://{portal}/explore/dataset/{dataset_id}/export/?format=geojson"
    
    return {
        'portal': portal,
        'dataset_id': dataset_id,
        'title': metas.get('title', 'Untitled'),
        'description': metas.get('description', '')[:200] + '...' if metas.get('description') else '',
        'license': license_info,
        'modified': metas.get('modified', ''),
        'publisher': metas.get('publisher', ''),
        'records_count': dataset.get('metas', {}).get('records_count', 0),
        'csv_export_url': csv_url,
        'json_api_url': json_url,
        'geojson_export_url': geojson_url,
        'dataset_page_url': f"https://{portal}/explore/dataset/{dataset_id}/",
    }


def discover_all_datasets() -> List[Dict[str, Any]]:
    """
    Main discovery function - searches all portals for DUoS datasets.
    """
    all_datasets = []
    seen_ids = set()  # Avoid duplicates
    
    logger.info("=" * 60)
    logger.info("STARTING DNO DATASET DISCOVERY")
    logger.info("=" * 60)
    
    # Search each DNO portal
    for dno_name, portal in DNO_PORTALS.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"PORTAL: {dno_name} ({portal})")
        logger.info(f"{'='*60}")
        
        # List all datasets, then filter
        all_portal_datasets = list_all_datasets(portal)
        duos_datasets = filter_duos_datasets(all_portal_datasets)
        
        logger.info(f"  Filtered to {len(duos_datasets)} DUoS-related datasets")
        
        for dataset in duos_datasets:
            dataset_id = dataset.get('datasetid') or dataset.get('dataset_id', '')
            
            # Skip duplicates
            unique_key = f"{portal}:{dataset_id}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            
            # Extract metadata
            metadata = extract_metadata(portal, dataset)
            metadata['dno_name'] = dno_name
            all_datasets.append(metadata)
            
            title = metadata.get('title', 'Untitled')
            logger.info(f"  📊 {dataset_id}: {title[:50]}")
    
    # Search Huwise Hub (broader search)
    logger.info(f"\n{'='*60}")
    logger.info(f"SEARCHING HUWISE HUB")
    logger.info(f"{'='*60}")
    
    for hub_portal in [PUBLIC_HUB]:
        all_portal_datasets = list_all_datasets(hub_portal)
        duos_datasets = filter_duos_datasets(all_portal_datasets)
        
        logger.info(f"  Filtered to {len(duos_datasets)} DUoS-related datasets")
        
        for dataset in duos_datasets:
            dataset_id = dataset.get('datasetid') or dataset.get('dataset_id', '')
            
            # Skip duplicates
            unique_key = f"{hub_portal}:{dataset_id}"
            if unique_key in seen_ids:
                continue
            seen_ids.add(unique_key)
            
            metadata = extract_metadata(hub_portal, dataset)
            metadata['dno_name'] = 'HUB'
            all_datasets.append(metadata)
            
            title = metadata.get('title', 'Untitled')
            logger.info(f"  📊 {dataset_id}: {title[:50]}")
    
    return all_datasets


def save_to_csv(datasets: List[Dict[str, Any]], filename: str):
    """
    Save discovered datasets to CSV.
    """
    if not datasets:
        logger.warning("No datasets to save!")
        return
    
    fieldnames = [
        'dno_name',
        'portal',
        'dataset_id',
        'title',
        'description',
        'license',
        'records_count',
        'modified',
        'publisher',
        'dataset_page_url',
        'csv_export_url',
        'json_api_url',
        'geojson_export_url',
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(datasets)
    
    logger.info(f"\n✅ Saved {len(datasets)} datasets to {filename}")


def save_to_json(datasets: List[Dict[str, Any]], filename: str):
    """
    Save discovered datasets to JSON (more detailed).
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            'discovery_date': datetime.now().isoformat(),
            'total_datasets': len(datasets),
            'portals_searched': list(DNO_PORTALS.values()) + [PUBLIC_HUB],
            'search_terms': SEARCH_TERMS,
            'datasets': datasets,
        }, f, indent=2)
    
    logger.info(f"✅ Saved detailed JSON to {filename}")


def print_summary(datasets: List[Dict[str, Any]]):
    """
    Print discovery summary.
    """
    logger.info("\n" + "=" * 60)
    logger.info("DISCOVERY SUMMARY")
    logger.info("=" * 60)
    
    # Group by portal
    by_portal = {}
    for ds in datasets:
        portal = ds['portal']
        if portal not in by_portal:
            by_portal[portal] = []
        by_portal[portal].append(ds)
    
    for portal, ds_list in sorted(by_portal.items()):
        logger.info(f"\n{portal}: {len(ds_list)} datasets")
        for ds in ds_list:
            logger.info(f"  • {ds['dataset_id']}")
            logger.info(f"    Title: {ds['title']}")
            logger.info(f"    Records: {ds['records_count']}")
            logger.info(f"    License: {ds['license']}")
    
    logger.info(f"\n📊 TOTAL DATASETS DISCOVERED: {len(datasets)}")


def main():
    """
    Main entry point.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Discover datasets
    datasets = discover_all_datasets()
    
    if not datasets:
        logger.error("❌ No datasets found!")
        return
    
    # Save results
    csv_filename = f"ods_datasets_discovery_{timestamp}.csv"
    json_filename = f"ods_datasets_discovery_{timestamp}.json"
    
    save_to_csv(datasets, csv_filename)
    save_to_json(datasets, json_filename)
    
    # Print summary
    print_summary(datasets)
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ DISCOVERY COMPLETE")
    logger.info("=" * 60)
    logger.info(f"\n📁 Files created:")
    logger.info(f"  • {csv_filename}")
    logger.info(f"  • {json_filename}")
    logger.info(f"\n💡 Next steps:")
    logger.info("  1. Review CSV for relevant DUoS datasets")
    logger.info("  2. Use export URLs to download data")
    logger.info("  3. Update download_duos_complete.py with discovered dataset IDs")


if __name__ == '__main__':
    main()
