#!/usr/bin/env python3
"""
Export Google Drive metadata to multiple Google Sheets.

This script:
1. Queries BigQuery for all indexed Drive files
2. Chunks the data to respect Google Sheets limits
3. Creates multiple sheets if necessary
4. Includes comprehensive metadata columns
"""

import os
import sys
from typing import List, Dict, Any
import logging
from datetime import datetime

# Google Cloud imports
from google.cloud import bigquery
from google.oauth2 import service_account
import gspread
from gspread_formatting import (
    cellFormat,
    textFormat,
    color,
    format_cell_range,
)

# Configuration
SHEETS_MAX_ROWS = 1000000  # Leave room for headers and safety margin
SHEETS_MAX_COLS = 18  # Number of metadata columns we'll export
BATCH_SIZE = 1000  # Rows to write at once

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DriveMetadataExporter:
    """Export Drive metadata from BigQuery to Google Sheets."""
    
    def __init__(self, bq_service_account_path: str, sheets_service_account_path: str = None):
        """Initialize with service account credentials.
        
        Args:
            bq_service_account_path: Service account for BigQuery access
            sheets_service_account_path: Service account for Sheets/Drive (optional, uses bq_sa if not provided)
        """
        # BigQuery credentials (inner-cinema for querying)
        self.bq_credentials = service_account.Credentials.from_service_account_file(
            bq_service_account_path,
            scopes=['https://www.googleapis.com/auth/bigquery']
        )
        self.bq_client = bigquery.Client(credentials=self.bq_credentials)
        
        # Sheets/Drive credentials (jibber-jabber-knowledge for creating sheets)
        sheets_sa = sheets_service_account_path or bq_service_account_path
        self.sheets_credentials = service_account.Credentials.from_service_account_file(
            sheets_sa,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        self.sheets_client = gspread.authorize(self.sheets_credentials)
        
    def fetch_drive_metadata(self, project_id: str, dataset: str) -> List[Dict[str, Any]]:
        """Fetch all Drive file metadata from BigQuery."""
        query = f"""
        SELECT
            drive_id as file_id,
            name as file_name,
            mime_type,
            size_bytes as file_size,
            created as created_time,
            updated as modified_time,
            owners,
            '' as last_modifying_user,
            web_view_link,
            '' as parent_folder_ids,
            '' as parents,
            FALSE as shared,
            FALSE as trashed,
            FALSE as starred,
            FALSE as viewed_by_me,
            '' as description,
            '' as folder_color_rgb,
            CURRENT_TIMESTAMP() as indexed_at
        FROM `{project_id}.{dataset}.documents_clean`
        ORDER BY updated DESC
        """
        
        logger.info("Querying BigQuery for Drive metadata...")
        query_job = self.bq_client.query(query)
        results = list(query_job.result())
        
        logger.info(f"Retrieved {len(results)} files from BigQuery")
        return results
    
    def prepare_data_for_sheets(self, bq_results: List[Any]) -> List[List[str]]:
        """Convert BigQuery results to sheets-compatible format."""
        headers = [
            "File ID",
            "File Name",
            "MIME Type",
            "Size (bytes)",
            "Size (MB)",
            "Created Date",
            "Modified Date",
            "Owner(s)",
            "Last Modified By",
            "Web View Link",
            "Parent Folders",
            "Shared",
            "Trashed",
            "Starred",
            "Viewed By Me",
            "Description",
            "Folder Color",
            "Indexed At"
        ]
        
        data = [headers]
        
        for row in bq_results:
            # Convert file size to MB for readability
            size_mb = ""
            if row.file_size:
                size_mb = f"{row.file_size / (1024 * 1024):.2f}"
            
            # Format dates
            created = row.created_time.strftime('%Y-%m-%d %H:%M:%S') if row.created_time else ""
            modified = row.modified_time.strftime('%Y-%m-%d %H:%M:%S') if row.modified_time else ""
            indexed = row.indexed_at.strftime('%Y-%m-%d %H:%M:%S') if row.indexed_at else ""
            
            # Convert lists to comma-separated strings
            owners = ", ".join(row.owners) if row.owners else ""
            parent_folders = ", ".join(row.parent_folder_ids) if row.parent_folder_ids else ""
            
            data.append([
                row.file_id or "",
                row.file_name or "",
                row.mime_type or "",
                str(row.file_size) if row.file_size else "",
                size_mb,
                created,
                modified,
                owners,
                row.last_modifying_user or "",
                row.web_view_link or "",
                parent_folders,
                "Yes" if row.shared else "No",
                "Yes" if row.trashed else "No",
                "Yes" if row.starred else "No",
                "Yes" if row.viewed_by_me else "No",
                row.description or "",
                row.folder_color_rgb or "",
                indexed
            ])
        
        return data
    
    def chunk_data(self, data: List[List[str]]) -> List[List[List[str]]]:
        """Split data into chunks that fit within Sheets limits."""
        headers = data[0]
        rows = data[1:]
        
        chunks = []
        for i in range(0, len(rows), SHEETS_MAX_ROWS):
            chunk = [headers] + rows[i:i + SHEETS_MAX_ROWS]
            chunks.append(chunk)
        
        logger.info(f"Split data into {len(chunks)} chunks")
        return chunks
    
    def format_sheet(self, worksheet):
        """Apply formatting to the worksheet."""
        # Format header row
        header_format = cellFormat(
            backgroundColor=color(0.2, 0.2, 0.2),
            textFormat=textFormat(bold=True, foregroundColor=color(1, 1, 1)),
        )
        format_cell_range(worksheet, 'A1:R1', header_format)
        
        # Freeze header row
        worksheet.freeze(rows=1)
        
        # Auto-resize columns
        worksheet.columns_auto_resize(0, SHEETS_MAX_COLS - 1)
        
        logger.info("Applied formatting to sheet")
    
    def create_sheet(self, title: str, data: List[List[str]], owner_email: str = None) -> str:
        """Create a new Google Sheet with the provided data.
        
        Args:
            title: Title of the spreadsheet
            data: Data to write (rows x columns)
            owner_email: Email to share the sheet with as owner/editor
        """
        logger.info(f"Creating sheet: {title}")
        
        # Create spreadsheet
        spreadsheet = self.sheets_client.create(title)
        worksheet = spreadsheet.sheet1
        
        # Update worksheet title
        worksheet.update_title(f"Drive Metadata - Part 1")
        
        # Write data in batches
        logger.info(f"Writing {len(data)} rows to sheet...")
        for i in range(0, len(data), BATCH_SIZE):
            batch = data[i:i + BATCH_SIZE]
            start_row = i + 1
            end_row = start_row + len(batch) - 1
            
            worksheet.update(
                f'A{start_row}:R{end_row}',
                batch,
                value_input_option='RAW'
            )
            
            logger.info(f"Wrote rows {start_row} to {end_row}")
        
        # Apply formatting
        self.format_sheet(worksheet)
        
        # Share with owner email if provided
        if owner_email:
            try:
                logger.info(f"Sharing sheet with {owner_email} as editor...")
                spreadsheet.share(owner_email, perm_type='user', role='writer', notify=True)
                logger.info(f"✅ Sheet shared with {owner_email}")
            except Exception as e:
                logger.warning(f"Could not share with {owner_email}: {e}")
        
        url = spreadsheet.url
        logger.info(f"Created sheet: {url}")
        
        return url
    
    def export_to_sheets(self, project_id: str, dataset: str, base_title: str = None, owner_email: str = None) -> List[str]:
        """Export Drive metadata to one or more Google Sheets.
        
        Args:
            project_id: GCP project ID
            dataset: BigQuery dataset name
            base_title: Base title for sheets (default: auto-generated)
            owner_email: Email to share sheets with
        """
        # Fetch data
        bq_results = self.fetch_drive_metadata(project_id, dataset)
        
        if not bq_results:
            logger.warning("No data found in BigQuery")
            return []
        
        # Prepare data
        data = self.prepare_data_for_sheets(bq_results)
        
        # Calculate total cells
        total_cells = len(data) * SHEETS_MAX_COLS
        logger.info(f"Total cells: {total_cells:,}")
        
        # Chunk data if necessary
        chunks = self.chunk_data(data)
        
        # Create sheets
        if base_title is None:
            base_title = f"Drive Metadata Export - {datetime.now().strftime('%Y-%m-%d')}"
        
        urls = []
        for idx, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                title = f"{base_title} - Part {idx}"
            else:
                title = base_title
            
            url = self.create_sheet(title, chunk, owner_email)
            urls.append(url)
        
        return urls


def main():
    """Main entry point."""
    # Load .env file explicitly
    from dotenv import load_dotenv
    load_dotenv('/app/.env')
    
    # Get configuration from environment
    project_id = os.getenv('GCP_PROJECT', 'inner-cinema-476211-u9')
    dataset = os.getenv('BQ_DATASET', 'uk_energy_insights')
    sa_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/secrets/sa.json')
    owner_email = os.getenv('DRIVE_OWNER_EMAIL')  # Email to share sheets with
    
    logger.info("=" * 60)
    logger.info("Drive Metadata to Google Sheets Exporter")
    logger.info("=" * 60)
    logger.info(f"Project: {project_id}")
    logger.info(f"Dataset: {dataset}")
    logger.info(f"Service Account: {sa_path}")
    if owner_email:
        logger.info(f"Will share with: {owner_email}")
    logger.info("")
    
    # Get Drive service account (for creating sheets)
    drive_sa_path = os.getenv('DRIVE_SERVICE_ACCOUNT', sa_path)
    
    # Check if service accounts exist
    if not os.path.exists(sa_path):
        logger.error(f"BigQuery service account file not found: {sa_path}")
        sys.exit(1)
    if not os.path.exists(drive_sa_path):
        logger.error(f"Drive service account file not found: {drive_sa_path}")
        sys.exit(1)
    
    logger.info(f"Using BigQuery SA: {sa_path}")
    logger.info(f"Using Drive/Sheets SA: {drive_sa_path}")
    logger.info("")
    
    try:
        # Initialize exporter with both service accounts
        exporter = DriveMetadataExporter(sa_path, drive_sa_path)
        
        # Export to sheets
        urls = exporter.export_to_sheets(project_id, dataset, owner_email=owner_email)
        
        # Print results
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ Export Complete!")
        logger.info("=" * 60)
        logger.info(f"Created {len(urls)} Google Sheet(s):")
        for idx, url in enumerate(urls, 1):
            logger.info(f"  {idx}. {url}")
        logger.info("")
        
    except Exception as e:
        logger.error(f"Error during export: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
