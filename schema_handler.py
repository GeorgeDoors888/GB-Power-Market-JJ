#!/usr/bin/env python
"""
schema_handler.py - Helper script for managing year-specific Elexon BMRS schemas

This script provides functions to:
1. Determine the appropriate schema file based on dataset and year
2. Extract schemas from existing data files (if available)
3. Create new schemas for years that don't have explicit definitions

Usage:
    from schema_handler import get_schema_for_dataset_and_year

    # Get schema for BOD dataset for year 2022
    schema = get_schema_for_dataset_and_year('BOD', 2022)
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

# Base directory for schema files
SCHEMA_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")

# Mapping of years to expected schema patterns
YEAR_SCHEMA_PATTERNS = {
    # 2022-2024 have all 7 metadata fields
    2022: "extended",  # Has _source_columns, _source_api, _hash_source_cols, _hash_key
    2023: "extended",
    2024: "extended",
    # 2025 has only 4 metadata fields
    2025: "simple",  # Lacks the additional metadata fields
}

# Define metadata fields based on pattern
METADATA_FIELDS = {
    "simple": [
        {"mode": "NULLABLE", "name": "_dataset", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_window_from_utc", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_window_to_utc", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_ingested_utc", "type": "STRING"},
    ],
    "extended": [
        {"mode": "NULLABLE", "name": "_dataset", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_window_from_utc", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_window_to_utc", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_ingested_utc", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_source_columns", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_source_api", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_hash_source_cols", "type": "STRING"},
        {"mode": "NULLABLE", "name": "_hash_key", "type": "STRING"},
    ],
}


def get_schema_filepath(dataset: str, year: int) -> str:
    """
    Get the path to the schema file for a specific dataset and year.

    Args:
        dataset: The BMRS dataset code (e.g., 'BOD', 'FREQ')
        year: The year (e.g., 2022)

    Returns:
        str: Path to the schema file
    """
    return os.path.join(SCHEMA_BASE_DIR, str(year), f"bmrs_{dataset.lower()}.json")


def schema_exists(dataset: str, year: int) -> bool:
    """
    Check if a schema file exists for the given dataset and year.

    Args:
        dataset: The BMRS dataset code
        year: The year

    Returns:
        bool: True if the schema file exists, False otherwise
    """
    filepath = get_schema_filepath(dataset, year)
    return os.path.exists(filepath)


def load_schema(filepath: str) -> List[Dict]:
    """
    Load a schema from a file.

    Args:
        filepath: Path to the schema file

    Returns:
        List[Dict]: The schema definition
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading schema from {filepath}: {e}")
        return []


def save_schema(schema: List[Dict], filepath: str) -> bool:
    """
    Save a schema to a file.

    Args:
        schema: The schema definition
        filepath: Path to save the schema file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(schema, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving schema to {filepath}: {e}")
        return False


def extract_business_fields(schema: List[Dict]) -> List[Dict]:
    """
    Extract business fields (non-metadata) from a schema.

    Args:
        schema: The full schema definition

    Returns:
        List[Dict]: The business fields
    """
    return [field for field in schema if not field["name"].startswith("_")]


def get_reference_year_for_schema(target_year: int) -> int:
    """
    Get the reference year to use for schema pattern.

    Args:
        target_year: The year to find a reference for

    Returns:
        int: The reference year
    """
    # Default reference years
    if target_year <= 2022:
        return 2022
    elif target_year <= 2024:
        return 2024
    else:
        return 2025


def adapt_schema_for_year(schema: List[Dict], target_year: int) -> List[Dict]:
    """
    Adapt a schema for a specific year by adjusting the metadata fields.

    Args:
        schema: The schema to adapt
        target_year: The year to adapt for

    Returns:
        List[Dict]: The adapted schema
    """
    # Get the pattern for the target year
    pattern = YEAR_SCHEMA_PATTERNS.get(
        target_year, "extended" if target_year < 2025 else "simple"
    )

    # Extract business fields
    business_fields = extract_business_fields(schema)

    # Combine with appropriate metadata fields
    return business_fields + METADATA_FIELDS[pattern]


def get_schema_for_dataset_and_year(
    dataset: str, year: int, create_if_missing: bool = True
) -> Optional[List[Dict]]:
    """
    Get the schema for a specific dataset and year.

    Args:
        dataset: The BMRS dataset code
        year: The year
        create_if_missing: Whether to create the schema if it doesn't exist

    Returns:
        Optional[List[Dict]]: The schema definition, or None if not found
    """
    dataset = dataset.lower()
    filepath = get_schema_filepath(dataset, year)

    # If schema exists, return it
    if schema_exists(dataset, year):
        return load_schema(filepath)

    if not create_if_missing:
        return None

    # Try to find a reference schema
    reference_year = get_reference_year_for_schema(year)
    if reference_year != year and schema_exists(dataset, reference_year):
        ref_schema = load_schema(get_schema_filepath(dataset, reference_year))

        # Adapt the schema for the target year
        adapted_schema = adapt_schema_for_year(ref_schema, year)

        # Save the adapted schema
        if save_schema(adapted_schema, filepath):
            return adapted_schema

    return None


def list_available_datasets_for_year(year: int) -> List[str]:
    """
    List all available datasets for a specific year.

    Args:
        year: The year

    Returns:
        List[str]: List of dataset codes
    """
    year_dir = os.path.join(SCHEMA_BASE_DIR, str(year))
    if not os.path.exists(year_dir):
        return []

    datasets = []
    for filename in os.listdir(year_dir):
        if filename.startswith("bmrs_") and filename.endswith(".json"):
            dataset = filename[5:-5].upper()  # Extract dataset code
            datasets.append(dataset)

    return sorted(datasets)


def get_schema_year_from_date(date_str: str) -> int:
    """
    Extract the year from a date string.

    Args:
        date_str: Date string in ISO format (YYYY-MM-DD)

    Returns:
        int: The year
    """
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        return date.year
    except ValueError:
        # If date parsing fails, return current year
        return datetime.now().year


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) < 3:
        print("Usage: python schema_handler.py <dataset> <year>")
        sys.exit(1)

    dataset = sys.argv[1].upper()
    year = int(sys.argv[2])

    schema = get_schema_for_dataset_and_year(dataset, year)
    if schema:
        print(f"Schema for {dataset} ({year}):")
        print(json.dumps(schema, indent=2))
    else:
        print(f"No schema found for {dataset} ({year})")
