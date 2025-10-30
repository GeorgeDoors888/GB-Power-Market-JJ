#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Schema loader for year-specific BMRS schemas.
This module provides functions to load the appropriate schema for a dataset based on the year.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Base directory for schema files
SCHEMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemas")


def get_schema_for_year(dataset: str, year: int) -> Optional[List[Dict]]:
    """
    Load the schema for a dataset for a specific year.
    Falls back to the most recent available schema if the exact year is not available.
    """
    dataset = dataset.lower()

    # Try to load schema for the specific year
    year_dir = os.path.join(SCHEMA_DIR, str(year))
    schema_path = os.path.join(year_dir, f"bmrs_{dataset}.json")

    if os.path.exists(schema_path):
        with open(schema_path, "r") as f:
            return json.load(f)

    # If not found, try to find the closest year
    available_years = []
    for y in os.listdir(SCHEMA_DIR):
        if y.isdigit() and os.path.isdir(os.path.join(SCHEMA_DIR, y)):
            y_int = int(y)
            schema_path = os.path.join(SCHEMA_DIR, y, f"bmrs_{dataset}.json")
            if os.path.exists(schema_path):
                available_years.append(y_int)

    if not available_years:
        return None

    # Find the closest year (prefer older schemas for older data)
    closest_year = None
    min_diff = float("inf")
    for y in available_years:
        diff = abs(y - year)
        if diff < min_diff or (diff == min_diff and y < closest_year):
            min_diff = diff
            closest_year = y

    if closest_year:
        schema_path = os.path.join(
            SCHEMA_DIR, str(closest_year), f"bmrs_{dataset}.json"
        )
        with open(schema_path, "r") as f:
            return json.load(f)

    return None


def get_schema_for_date_range(
    dataset: str, start_date: datetime, end_date: datetime
) -> Optional[List[Dict]]:
    """
    Load the appropriate schema for a dataset based on a date range.
    Uses the schema for the year at the start of the range.
    """
    year = start_date.year
    return get_schema_for_year(dataset, year)
