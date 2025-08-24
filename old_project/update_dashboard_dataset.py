#!/usr/bin/env python3
"""
Update Dashboard Dataset Script

This script updates the SQL queries in the interactive_dashboard_app.py file
to point to the new uk_energy_prod dataset instead of uk_energy.

Usage:
    python update_dashboard_dataset.py
"""

import re
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def update_dashboard_file():
    """Update the dashboard file to use the new dataset."""
    dashboard_file = "interactive_dashboard_app.py"
    
    if not os.path.exists(dashboard_file):
        logger.error(f"Dashboard file {dashboard_file} not found")
        return False
    
    # Read the original file
    with open(dashboard_file, 'r') as f:
        content = f.read()
    
    # Check if the file contains BigQuery queries
    if "`uk_energy." not in content:
        logger.warning(f"No BigQuery queries found in {dashboard_file}")
        return False
    
    # Replace dataset references
    new_content = content.replace("`uk_energy.", "`uk_energy_prod.")
    
    # Backup the original file
    backup_file = f"{dashboard_file}.bak"
    with open(backup_file, 'w') as f:
        f.write(content)
    logger.info(f"Backed up original dashboard file to {backup_file}")
    
    # Write the updated content
    with open(dashboard_file, 'w') as f:
        f.write(new_content)
    
    logger.info(f"Updated {dashboard_file} to use uk_energy_prod dataset")
    return True

def update_ingestion_scripts():
    """Find and update data ingestion scripts to use the new dataset."""
    ingestion_files = [
        "fast_cloud_backfill.py",
        "ingestion_loader.py",
        "cloud_data_collector.py"
    ]
    
    updated_files = []
    
    for filename in ingestion_files:
        if not os.path.exists(filename):
            logger.warning(f"Ingestion file {filename} not found")
            continue
        
        # Read the original file
        with open(filename, 'r') as f:
            content = f.read()
        
        # Check if the file contains BigQuery dataset references
        if "uk_energy" not in content:
            logger.warning(f"No dataset references found in {filename}")
            continue
        
        # Replace dataset references (be careful with string vs variable references)
        # This is a simplistic approach and may need manual verification
        new_content = re.sub(r'(["\'])uk_energy(["\'])', r'\1uk_energy_prod\2', content)
        new_content = re.sub(r'dataset_id\s*=\s*(["\'])uk_energy(["\'])', r'dataset_id=\1uk_energy_prod\2', new_content)
        
        # Backup the original file
        backup_file = f"{filename}.bak"
        with open(backup_file, 'w') as f:
            f.write(content)
        logger.info(f"Backed up original file to {backup_file}")
        
        # Write the updated content
        with open(filename, 'w') as f:
            f.write(new_content)
        
        logger.info(f"Updated {filename} to use uk_energy_prod dataset")
        updated_files.append(filename)
    
    return updated_files

def main():
    """Main function to update all necessary files."""
    logger.info("Starting dataset reference update process")
    
    # Update dashboard file
    dashboard_updated = update_dashboard_file()
    
    # Update ingestion scripts
    updated_scripts = update_ingestion_scripts()
    
    # Summary
    if dashboard_updated:
        logger.info("Successfully updated dashboard file to use new dataset")
    else:
        logger.warning("Dashboard file was not updated")
    
    if updated_scripts:
        logger.info(f"Successfully updated {len(updated_scripts)} ingestion scripts")
        for script in updated_scripts:
            logger.info(f"  - {script}")
    else:
        logger.warning("No ingestion scripts were updated")
    
    logger.info("Dataset reference update process completed")
    logger.info("IMPORTANT: Please verify the changes manually before committing them")

if __name__ == "__main__":
    main()
