#!/usr/bin/env python3
"""
BigQuery Configuration for UK Energy Document Search
Project: inner-cinema-476211-u9
Dataset: uk_energy_prod
Table: document_chunks
"""

import os

# BigQuery Project Settings
BIGQUERY_PROJECT_ID = "inner-cinema-476211-u9"
BIGQUERY_DATASET = "uk_energy_prod"
BIGQUERY_TABLE = "document_chunks"

# Credentials path
CREDENTIALS_PATH = os.path.expanduser("~/.config/google-cloud/bigquery-credentials.json")

# Full table reference
TABLE_REFERENCE = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}"

# Search terms for revenue settlement
REVENUE_SETTLEMENT_TERMS = [
    'revenue settlement',
    'settlement revenue',
    'energy settlement',
    'settlement process',
    'financial settlement',
    'settlement mechanisms',
    'settlement calculation',
]

# Search terms for Virtual Lead Party (VLP)
VLP_TERMS = [
    'Virtual Lead Party',
    'VLP',
    'virtual lead',
    'lead party',
    'VLP role',
    'VLP responsibilities',
]

# Document sources to filter
DOCUMENT_SOURCES = [
    'BSC',
    'bsc',
    'Ofgem',
    'ofgem',
    'NESO',
    'neso',
    'Elexon',
    'elexon',
    'National Grid ESO',
    'National Grid',
]

# Output settings
OUTPUT_CSV = "bigquery_search_results.csv"
OUTPUT_JSON = "bigquery_search_results.json"

# Query settings
MAX_RESULTS = 1000  # Maximum number of results to return
MIN_RELEVANCE_SCORE = 0.0  # Minimum relevance score (if applicable)

# Column names in document_chunks table (adjust if needed)
COLUMN_MAPPINGS = {
    'content': 'chunk_text',  # or 'content', 'text', 'document_text'
    'source': 'source',  # or 'document_source', 'doc_source'
    'title': 'document_name',  # or 'title', 'doc_title'
    'url': 'url',  # or 'document_url', 'source_url'
    'chunk_id': 'chunk_id',
    'document_id': 'document_id',
}

# Legacy compatibility (for bigquery_to_sheets_updater.py)
PROJECT_ID = BIGQUERY_PROJECT_ID
DATASET_ID = BIGQUERY_DATASET
TABLE_ID = BIGQUERY_TABLE

# Google Sheets configuration
SPREADSHEET_NAME = "UK Energy Documents Analysis"
WORKSHEET_NAME = "Documents"
