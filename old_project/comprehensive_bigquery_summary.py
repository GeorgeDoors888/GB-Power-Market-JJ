#!/usr/bin/env python3
"""
Comprehensive BigQuery Summary Generator

This script generates a detailed summary of all tables in the UK Energy BigQuery dataset,
including schema information, row counts, data ranges, and statistics.

The output is written to a text file for easy review.
"""

import os
import datetime
from google.cloud import bigquery
from typing import Dict, List, Tuple, Any, Optional
import time

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"
LOCATION = "europe-west2"
OUTPUT_FILE = "uk_energy_bigquery_comprehensive_summary.txt"

def setup_bigquery_client() -> bigquery.Client:
    """Creates and returns a BigQuery client with proper location settings"""
    return bigquery.Client(project=PROJECT_ID, location=LOCATION)

def get_all_tables(client: bigquery.Client) -> List[bigquery.table.TableListItem]:
    """Retrieves a list of all tables in the dataset"""
    dataset_ref = client.dataset(DATASET_ID)
    tables = list(client.list_tables(dataset_ref))
    return tables

def categorize_tables(tables: List[bigquery.table.TableListItem]) -> Tuple[List[str], List[str], List[str]]:
    """Categorizes tables by their name prefix"""
    neso_tables = []
    elexon_tables = []
    other_tables = []
    
    for table in tables:
        table_id = table.table_id
        if table_id.startswith('neso_'):
            neso_tables.append(table_id)
        elif table_id.startswith('elexon_'):
            elexon_tables.append(table_id)
        else:
            other_tables.append(table_id)
    
    return neso_tables, elexon_tables, other_tables

def categorize_neso_tables(neso_tables: List[str]) -> Dict[str, List[str]]:
    """Further categorizes NESO tables by their type"""
    categories = {
        'skip': [],
        'dispatch': [],
        'static': [],
        'transparency': [],
        'constraint': [],
        'balancing': [],
        'demand': [],
        'generation': [],
        'capacity': [],
        'network': [],
        'carbon': [],
        'other': []
    }
    
    for table in neso_tables:
        if 'skip' in table:
            categories['skip'].append(table)
        elif 'dispatch' in table:
            categories['dispatch'].append(table)
        elif 'static' in table or 'reference' in table:
            categories['static'].append(table)
        elif 'transparency' in table:
            categories['transparency'].append(table)
        elif 'constraint' in table:
            categories['constraint'].append(table)
        elif 'balancing' in table:
            categories['balancing'].append(table)
        elif 'demand' in table:
            categories['demand'].append(table)
        elif 'generation' in table:
            categories['generation'].append(table)
        elif 'capacity' in table:
            categories['capacity'].append(table)
        elif 'network' in table:
            categories['network'].append(table)
        elif 'carbon' in table:
            categories['carbon'].append(table)
        else:
            categories['other'].append(table)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def get_table_metadata(client: bigquery.Client, table_id: str) -> Dict[str, Any]:
    """Gets detailed metadata for a specific table"""
    table_ref = client.dataset(DATASET_ID).table(table_id)
    table = client.get_table(table_ref)
    
    metadata = {
        'id': table.table_id,
        'full_id': f"{table.project}.{table.dataset_id}.{table.table_id}",
        'description': table.description,
        'num_rows': table.num_rows,
        'created': table.created,
        'modified': table.modified,
        'schema': table.schema,
        'column_count': len(table.schema),
        'size_bytes': table.num_bytes,
        'schema_types': {},
    }
    
    # Categorize columns by data type
    for field in table.schema:
        field_type = field.field_type
        if field_type not in metadata['schema_types']:
            metadata['schema_types'][field_type] = []
        metadata['schema_types'][field_type].append(field.name)
    
    return metadata

def get_date_range(client: bigquery.Client, table_id: str, date_column: str) -> Optional[Tuple[Any, Any]]:
    """Gets the min and max values for a date column in a table"""
    try:
        query = f"""
        SELECT MIN({date_column}) as min_date, MAX({date_column}) as max_date
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}`
        """
        query_job = client.query(query)
        results = query_job.result()
        
        row = list(results)[0]
        return row.min_date, row.max_date
    except Exception as e:
        return None

def get_table_sample_values(client: bigquery.Client, table_id: str, limit: int = 5) -> Dict[str, List[Any]]:
    """Gets sample values for each column in the table"""
    try:
        table_ref = client.dataset(DATASET_ID).table(table_id)
        table = client.get_table(table_ref)
        
        columns = [field.name for field in table.schema]
        column_list = ", ".join([f"`{col}`" for col in columns])
        
        query = f"""
        SELECT {column_list}
        FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}`
        LIMIT {limit}
        """
        
        query_job = client.query(query)
        results = list(query_job.result())
        
        samples = {}
        if results:
            for col in columns:
                samples[col] = [getattr(row, col) for row in results if hasattr(row, col)]
        
        return samples
    except Exception as e:
        return {}

def format_metadata_for_output(
    metadata: Dict[str, Any], 
    date_ranges: Dict[str, Optional[Tuple[Any, Any]]],
    samples: Dict[str, List[Any]]
) -> str:
    """Formats the metadata into a readable text format"""
    output = []
    
    # Basic info
    output.append(f"Table: {metadata['id']}")
    output.append("-" * (len(metadata['id']) + 7))
    
    # Row count
    output.append(f"Row count: {metadata['num_rows']:,}")
    
    # Creation and modification dates
    created = metadata['created'].strftime('%Y-%m-%d %H:%M:%S UTC') if metadata['created'] else 'Unknown'
    modified = metadata['modified'].strftime('%Y-%m-%d %H:%M:%S UTC') if metadata['modified'] else 'Unknown'
    output.append(f"Created: {created}")
    output.append(f"Last modified: {modified}")
    
    # Size
    size_mb = metadata['size_bytes'] / (1024 * 1024) if metadata['size_bytes'] else 0
    output.append(f"Size: {size_mb:.2f} MB")
    
    # Schema summary
    output.append(f"\nSchema ({metadata['column_count']} columns):")
    for field_type, fields in metadata['schema_types'].items():
        output.append(f"  - {field_type}: {len(fields)} columns")
    
    # Sample fields
    output.append("\nSample fields:")
    field_count = 0
    for field in metadata['schema']:
        if field_count < 10:  # Show first 10 fields
            output.append(f"  - {field.name} ({field.field_type})")
            field_count += 1
        else:
            remaining = metadata['column_count'] - 10
            output.append(f"  ... and {remaining} more fields")
            break
    
    # Date ranges for date/time columns
    if date_ranges:
        output.append("\nDate ranges:")
        for col, range_tuple in date_ranges.items():
            if range_tuple:
                min_val, max_val = range_tuple
                output.append(f"  - {col}: {min_val} to {max_val}")
            else:
                output.append(f"  - {col}: No data or error retrieving range")
    
    # Sample values for a few columns (first 3)
    if samples:
        output.append("\nSample values:")
        count = 0
        for col, values in samples.items():
            if count < 3 and values:  # Only show first 3 columns with data
                val_str = ", ".join([str(v) if v is not None else "NULL" for v in values[:3]])
                output.append(f"  - {col}: {val_str}")
                count += 1
            if count >= 3:
                break
    
    return "\n".join(output)

def generate_summary(client: bigquery.Client, tables: List[bigquery.table.TableListItem]) -> str:
    """Generates a comprehensive summary of all tables"""
    output = []
    
    # Header
    output.append("UK ENERGY DATASET IN BIGQUERY - COMPREHENSIVE SUMMARY")
    output.append("=" * 58)
    output.append("")
    
    # Generation info
    now = datetime.datetime.now()
    output.append(f"Generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    output.append(f"BigQuery project: {PROJECT_ID}")
    output.append(f"BigQuery dataset: {DATASET_ID}")
    output.append(f"Dataset location: {LOCATION} (London)")
    output.append("")
    
    # Get and categorize tables
    neso_tables, elexon_tables, other_tables = categorize_tables(tables)
    
    # Summary statistics
    output.append("SUMMARY STATISTICS")
    output.append("-" * 18)
    output.append(f"Total tables: {len(tables)}")
    output.append(f"NESO tables: {len(neso_tables)}")
    output.append(f"Elexon tables: {len(elexon_tables)}")
    output.append(f"Other tables: {len(other_tables)}")
    output.append("")
    
    # NESO categories
    neso_categories = categorize_neso_tables(neso_tables)
    output.append("NESO DATA CATEGORIES")
    output.append("-" * 19)
    for category, tables_in_category in neso_categories.items():
        output.append(f"{category}: {len(tables_in_category)} tables")
    output.append("")
    
    # Table details
    output.append("TABLE DETAILS")
    output.append("-" * 13)
    output.append("")
    
    # Process all tables with 5-second pause between each to avoid rate limiting
    all_tables = neso_tables + elexon_tables + other_tables
    for i, table_id in enumerate(all_tables):
        print(f"Processing table {i+1}/{len(all_tables)}: {table_id}")
        
        try:
            metadata = get_table_metadata(client, table_id)
            
            # Get date ranges for date/datetime columns
            date_ranges = {}
            for field in metadata['schema']:
                if field.field_type in ('DATE', 'DATETIME', 'TIMESTAMP'):
                    range_result = get_date_range(client, table_id, field.name)
                    date_ranges[field.name] = range_result
            
            # Get sample values
            samples = get_table_sample_values(client, table_id, limit=3)
            
            # Format and add to output
            table_output = format_metadata_for_output(metadata, date_ranges, samples)
            output.append(table_output)
            output.append("\n" + "=" * 50 + "\n")
            
            # Short pause to avoid hitting API limits
            if i < len(all_tables) - 1:
                time.sleep(1)
                
        except Exception as e:
            output.append(f"Table: {table_id}")
            output.append("-" * (len(table_id) + 7))
            output.append(f"Error retrieving metadata: {str(e)}")
            output.append("\n" + "=" * 50 + "\n")
    
    return "\n".join(output)

def main():
    """Main function to generate the summary"""
    print(f"Generating comprehensive BigQuery summary for {PROJECT_ID}.{DATASET_ID}...")
    
    client = setup_bigquery_client()
    tables = get_all_tables(client)
    
    print(f"Found {len(tables)} tables. Generating summary...")
    summary = generate_summary(client, tables)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(summary)
    
    print(f"Summary generated successfully and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
