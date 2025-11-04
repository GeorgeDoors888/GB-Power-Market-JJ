#!/usr/bin/env python3
"""Export Drive metadata from BigQuery to CSV file."""
import os
import sys
import csv
import logging
from typing import List, Dict, Any
from datetime import datetime

from google.cloud import bigquery
from google.oauth2 import service_account

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DriveMetadataCSVExporter:
    """Export Drive metadata from BigQuery to CSV."""
    
    def __init__(self, service_account_path: str):
        """Initialize with BigQuery service account credentials."""
        self.credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        self.bq_client = bigquery.Client(credentials=self.credentials)
    
    def fetch_drive_metadata(self, project_id: str, dataset: str) -> List[Dict[str, Any]]:
        """Fetch all Drive file metadata from BigQuery."""
        query = f"""
        SELECT
            drive_id as file_id,
            name,
            mime_type,
            size_bytes,
            ROUND(size_bytes / 1024 / 1024, 2) as size_mb,
            created as created_at,
            updated as modified_at,
            owners as owner_emails,
            web_view_link,
            path as parent_folders,
            NULL as shared,
            NULL as trashed,
            NULL as starred,
            NULL as viewed_by_me,
            NULL as description,
            NULL as folder_color_rgb,
            CURRENT_TIMESTAMP() as indexed_at
        FROM `{project_id}.{dataset}.documents_clean`
        ORDER BY modified_at DESC
        """
        
        logger.info(f"Querying BigQuery for Drive metadata...")
        query_job = self.bq_client.query(query)
        results = list(query_job.result())
        
        logger.info(f"Retrieved {len(results)} files from BigQuery")
        return results
    
    def export_to_csv(self, project_id: str, dataset: str, output_path: str) -> str:
        """Export metadata to CSV file."""
        # Fetch data
        bq_results = self.fetch_drive_metadata(project_id, dataset)
        
        if not bq_results:
            logger.warning("No data to export")
            return None
        
        # Define CSV columns
        columns = [
            'file_id', 'name', 'mime_type', 'size_bytes', 'size_mb',
            'created_at', 'modified_at', 'owner_emails', 'web_view_link',
            'parent_folders', 'shared', 'trashed', 'starred',
            'viewed_by_me', 'description', 'folder_color_rgb', 'indexed_at'
        ]
        
        # Write to CSV
        logger.info(f"Writing {len(bq_results)} rows to CSV: {output_path}")
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for row in bq_results:
                # Convert BigQuery Row to dict
                row_dict = {}
                for col in columns:
                    value = row.get(col)
                    # Convert timestamps to strings
                    if value and hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    row_dict[col] = value if value is not None else ''
                writer.writerow(row_dict)
        
        logger.info(f"✅ CSV export complete: {output_path}")
        return output_path


def main():
    """Main entry point."""
    # Load .env file explicitly
    from dotenv import load_dotenv
    load_dotenv('/app/.env')
    
    # Get configuration from environment
    project_id = os.getenv('GCP_PROJECT', 'inner-cinema-476211-u9')
    dataset = os.getenv('BQ_DATASET', 'uk_energy_insights')
    sa_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/secrets/sa.json')
    
    # Output path
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = f'/tmp/drive_metadata_{timestamp}.csv'
    
    logger.info("=" * 60)
    logger.info("Drive Metadata to CSV Exporter")
    logger.info("=" * 60)
    logger.info(f"Project: {project_id}")
    logger.info(f"Dataset: {dataset}")
    logger.info(f"Service Account: {sa_path}")
    logger.info(f"Output: {output_path}")
    logger.info("")
    
    # Check if service account exists
    if not os.path.exists(sa_path):
        logger.error(f"Service account file not found: {sa_path}")
        sys.exit(1)
    
    try:
        # Initialize exporter
        exporter = DriveMetadataCSVExporter(sa_path)
        
        # Export to CSV
        csv_path = exporter.export_to_csv(project_id, dataset, output_path)
        
        # Print results
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Export Complete!")
        logger.info("=" * 60)
        logger.info(f"CSV file created: {csv_path}")
        logger.info(f"")
        logger.info("To download the file:")
        logger.info(f"  scp root@94.237.55.15:{csv_path} ./drive_metadata.csv")
        logger.info("")
        
    except Exception as e:
        logger.error(f"Error during export: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
