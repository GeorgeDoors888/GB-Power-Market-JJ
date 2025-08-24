#!/usr/bin/env python3
"""
Create Remaining BigQuery Tables Script

This script creates the remaining tables needed for the UK Energy Dashboard in the
uk_energy_prod dataset. It defines schemas for tables that don't exist yet in the
source dataset.

Usage:
    python create_remaining_tables.py
"""

import os
import sys
import logging
from google.cloud import bigquery
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("create_tables.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "jibber-jabber-knowledge"
DATASET_ID = "uk_energy_prod"
LOCATION = "europe-west2"

# Schema definitions for tables that don't exist in source dataset
SCHEMA_DEFINITIONS = {
    "elexon_system_warnings": [
        bigquery.SchemaField("warning_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("warning_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("warning_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("start_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("end_time", "TIMESTAMP"),
        bigquery.SchemaField("severity", "STRING"),
        bigquery.SchemaField("message", "STRING"),
        bigquery.SchemaField("affected_area", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("resolution_time", "TIMESTAMP"),
        bigquery.SchemaField("impact_mw", "FLOAT")
    ],
    
    "neso_carbon_intensity": [
        bigquery.SchemaField("measurement_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("measurement_time", "TIME", mode="REQUIRED"),
        bigquery.SchemaField("carbon_intensity_gco2_kwh", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("forecast_carbon_intensity_gco2_kwh", "FLOAT"),
        bigquery.SchemaField("generation_mix", "STRING"),
        bigquery.SchemaField("region", "STRING"),
        bigquery.SchemaField("data_source", "STRING")
    ],
    
    "neso_interconnector_flows": [
        bigquery.SchemaField("settlement_date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("settlement_period", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("interconnector_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("interconnector_name", "STRING"),
        bigquery.SchemaField("connected_country", "STRING"),
        bigquery.SchemaField("flow_mw", "FLOAT", mode="REQUIRED"),
        bigquery.SchemaField("direction", "STRING"),
        bigquery.SchemaField("capacity_mw", "FLOAT"),
        bigquery.SchemaField("utilization_pct", "FLOAT"),
        bigquery.SchemaField("price_differential_gbp_mwh", "FLOAT"),
        bigquery.SchemaField("forecast_timestamp", "TIMESTAMP")
    ]
}

# Table clustering and partitioning configurations
TABLE_CONFIGS = {
    "elexon_system_warnings": {
        "partitioning": {
            "field": "warning_date",
            "type": "DAY"
        },
        "clustering": ["warning_type", "severity"],
        "description": "Contains system warnings and notices from Elexon BMRS"
    },
    
    "neso_carbon_intensity": {
        "partitioning": {
            "field": "measurement_date",
            "type": "DAY"
        },
        "clustering": ["region"],
        "description": "Contains carbon intensity measurements and forecasts"
    },
    
    "neso_interconnector_flows": {
        "partitioning": {
            "field": "settlement_date",
            "type": "DAY"
        },
        "clustering": ["interconnector_id", "settlement_period"],
        "description": "Contains interconnector flow data between UK and other countries"
    }
}

def init_client():
    """Initialize BigQuery client."""
    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception as e:
        logger.error(f"Failed to initialize BigQuery client: {e}")
        return None

def create_table(client, table_name):
    """Create a table using predefined schema and configuration."""
    try:
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        
        # Check if table exists
        try:
            client.get_table(table_id)
            logger.info(f"Table {table_name} already exists.")
            return True
        except Exception:
            # Table doesn't exist, proceed with creation
            pass
        
        # Get schema definition
        if table_name not in SCHEMA_DEFINITIONS:
            logger.error(f"Schema definition not found for table {table_name}")
            return False
        
        schema = SCHEMA_DEFINITIONS[table_name]
        
        # Create table
        table = bigquery.Table(table_id, schema=schema)
        
        # Apply partitioning if configured
        if table_name in TABLE_CONFIGS and "partitioning" in TABLE_CONFIGS[table_name]:
            part_config = TABLE_CONFIGS[table_name]["partitioning"]
            table.time_partitioning = bigquery.TimePartitioning(
                type_=part_config["type"],
                field=part_config["field"]
            )
        
        # Apply clustering if configured
        if table_name in TABLE_CONFIGS and "clustering" in TABLE_CONFIGS[table_name]:
            table.clustering_fields = TABLE_CONFIGS[table_name]["clustering"]
        
        # Set description
        if table_name in TABLE_CONFIGS and "description" in TABLE_CONFIGS[table_name]:
            table.description = TABLE_CONFIGS[table_name]["description"]
        
        # Create the table
        table = client.create_table(table, exists_ok=False)
        logger.info(f"Created table {table_name}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to create table {table_name}: {e}")
        return False

def main():
    """Main execution function."""
    logger.info("Starting creation of remaining BigQuery tables")
    
    # Initialize client
    client = init_client()
    if not client:
        logger.error("Failed to initialize BigQuery client. Exiting.")
        sys.exit(1)
    
    # Tables to create
    tables_to_create = [
        "elexon_system_warnings",
        "neso_carbon_intensity",
        "neso_interconnector_flows"
    ]
    
    # Create each table
    success_count = 0
    for table_name in tables_to_create:
        logger.info(f"Creating table {table_name}...")
        if create_table(client, table_name):
            success_count += 1
    
    logger.info(f"Created {success_count} out of {len(tables_to_create)} tables")

if __name__ == "__main__":
    main()
