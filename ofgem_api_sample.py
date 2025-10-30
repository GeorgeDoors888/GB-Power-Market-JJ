#!/usr/bin/env python3
"""
Sample usage of Ofgem API
"""

from ofgem_api import OfgemAPI, OfgemConfig

# Create configuration
config = OfgemConfig()
config.use_bigquery = False  # Set to True if you want to save to BigQuery
config.use_cloud_storage = False  # Set to True if you want to save to GCS

# Initialize API
api = OfgemAPI(config)

# Example 1: Get retail market data
print("Getting retail market indicators...")
retail_data = api.get_data_portal_charts("retail-market-indicators")
print(f"Found {len(retail_data.get('charts', []))} retail market charts")

# Example 2: Get licence information
print("\nGetting licence data...")
licence_data = api.get_licence_data("electricity")
print(f"Found {len(licence_data.get('licences', []))} electricity licences")

# Example 3: Get recent publications
print("\nGetting recent publications...")
publications = api.get_publications()
print(f"Found {len(publications.get('publications', []))} publications")

# Example 4: Collect everything
print("\nCollecting all data...")
all_data = api.collect_all_data()
print("Collection complete!")
