#!/usr/bin/env python3
"""
Schema Fixer for UK Energy BigQuery Tables
==========================================
Fixes schema issues with the tables to ensure live data can be properly loaded
"""

import os
import sys
import logging
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"schema_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SchemaFixer:
    """Fixes schema issues with BigQuery tables"""
    
    def __init__(self):
        self.project_id = "jibber-jabber-knowledge"
        self.dataset_id = "uk_energy_prod"
        self.client = bigquery.Client(project=self.project_id)
        
        # Define schema fixes for each table
        self.schema_fixes = {
            # Elexon tables
            "elexon_demand_outturn": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("startTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("initialDemandOutturn", "FLOAT"),
                bigquery.SchemaField("initialTransmissionSystemDemandOutturn", "FLOAT")
            ],
            "elexon_generation_outturn": [
                bigquery.SchemaField("recordType", "STRING"),
                bigquery.SchemaField("startTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("demand", "FLOAT")
            ],
            "elexon_system_warnings": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("warningType", "STRING"),
                bigquery.SchemaField("messageText", "STRING"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("warningId", "STRING")
            ],
            
            # NESO tables
            "neso_demand_forecasts": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("demand", "FLOAT")
            ],
            "neso_wind_forecasts": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("quantity", "FLOAT"),
                bigquery.SchemaField("windType", "STRING")
            ],
            "neso_carbon_intensity": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("fuel_type", "STRING"),
                bigquery.SchemaField("generation", "FLOAT")
            ],
            "neso_interconnector_flows": [
                bigquery.SchemaField("publishTime", "TIMESTAMP"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("interconnector_name", "STRING"),
                bigquery.SchemaField("quantity", "FLOAT")
            ],
            "neso_balancing_services": [
                bigquery.SchemaField("dataset", "STRING"),
                bigquery.SchemaField("settlementDate", "DATE"),
                bigquery.SchemaField("settlementPeriod", "INTEGER"),
                bigquery.SchemaField("id", "INTEGER"),
                bigquery.SchemaField("cost", "FLOAT"),
                bigquery.SchemaField("volume", "FLOAT"),
                bigquery.SchemaField("soFlag", "BOOLEAN"),
                bigquery.SchemaField("storFlag", "BOOLEAN"),
                bigquery.SchemaField("partyId", "STRING"),
                bigquery.SchemaField("assetId", "STRING"),
                bigquery.SchemaField("isTendered", "BOOLEAN"),
                bigquery.SchemaField("service", "STRING")
            ]
        }
    
    def get_current_schema(self, table_name):
        """Gets the current schema of a table"""
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        try:
            table = self.client.get_table(table_id)
            return table.schema
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {str(e)}")
            return None
    
    def fix_table_schema(self, table_name):
        """Fixes the schema for a specific table"""
        if table_name not in self.schema_fixes:
            logger.warning(f"No schema fix defined for {table_name}")
            return False
        
        current_schema = self.get_current_schema(table_name)
        if current_schema is None:
            logger.warning(f"Table {table_name} doesn't exist, creating it")
            return self.create_table(table_name)
        
        # Compare current schema with desired schema
        current_fields = {field.name: field for field in current_schema}
        desired_fields = {field.name: field for field in self.schema_fixes[table_name]}
        
        # Check if schemas match
        schema_match = True
        for name, field in desired_fields.items():
            if name not in current_fields:
                schema_match = False
                logger.info(f"Field {name} missing in {table_name}")
                break
            if current_fields[name].field_type != field.field_type:
                schema_match = False
                logger.info(f"Field {name} has wrong type in {table_name} (is {current_fields[name].field_type}, should be {field.field_type})")
                break
        
        if schema_match:
            logger.info(f"Schema for {table_name} is already correct")
            return True
        
        # Fix the schema
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        new_schema = self.schema_fixes[table_name]
        
        # For simplicity, recreate the table with the correct schema
        try:
            # Export existing data to a temporary table
            temp_table_name = f"{table_name}_temp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            temp_table_id = f"{self.project_id}.{self.dataset_id}.{temp_table_name}"
            
            # Create temporary table with same schema as original
            query = f"""
            CREATE TABLE `{temp_table_id}`
            AS SELECT * FROM `{table_id}`
            """
            query_job = self.client.query(query)
            query_job.result()
            
            # Delete original table
            self.client.delete_table(table_id)
            
            # Create new table with correct schema
            table = bigquery.Table(table_id, schema=new_schema)
            table = self.client.create_table(table)
            
            # Copy data back, doing type conversion
            field_list = ", ".join(field.name for field in new_schema)
            query = f"""
            INSERT INTO `{table_id}` ({field_list})
            SELECT {field_list} FROM `{temp_table_id}`
            """
            
            query_job = self.client.query(query)
            try:
                query_job.result()
                logger.info(f"Successfully copied data to fixed table {table_name}")
            except Exception as e:
                logger.error(f"Error copying data to fixed table {table_name}: {str(e)}")
                # Don't delete the temp table if we couldn't copy the data
                return False
            
            # Delete temporary table
            self.client.delete_table(temp_table_id)
            
            logger.info(f"Successfully fixed schema for {table_name}")
            return True
        except Exception as e:
            logger.error(f"Error fixing schema for {table_name}: {str(e)}")
            return False
    
    def create_table(self, table_name):
        """Creates a new table with the correct schema"""
        if table_name not in self.schema_fixes:
            logger.warning(f"No schema defined for {table_name}")
            return False
        
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        schema = self.schema_fixes[table_name]
        
        try:
            table = bigquery.Table(table_id, schema=schema)
            table = self.client.create_table(table)
            logger.info(f"Created table {table_name} with correct schema")
            return True
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
            return False
    
    def fix_all_tables(self):
        """Fix schemas for all tables"""
        success_count = 0
        for table_name in self.schema_fixes:
            logger.info(f"Fixing schema for {table_name}")
            if self.fix_table_schema(table_name):
                success_count += 1
        
        logger.info(f"Fixed {success_count}/{len(self.schema_fixes)} tables")
        return success_count == len(self.schema_fixes)

if __name__ == "__main__":
    logger.info("Starting schema fix process")
    fixer = SchemaFixer()
    
    if len(sys.argv) > 1:
        # Fix specific tables
        for table_name in sys.argv[1:]:
            if table_name in fixer.schema_fixes:
                fixer.fix_table_schema(table_name)
            else:
                logger.warning(f"Unknown table: {table_name}")
    else:
        # Fix all tables
        fixer.fix_all_tables()
    
    logger.info("Schema fix process complete")
