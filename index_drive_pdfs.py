#!/usr/bin/env python3
"""
Index all PDFs from Google Drive into BigQuery with full metadata.
Features: Progress tracking, resumable, saves state.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.cloud import bigquery
import json
import os
from datetime import datetime

# Configuration
WORKSPACE_CREDS = 'workspace-credentials.json'
BQ_CREDS = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
TABLE = 'pdf_metadata_index'
STATE_FILE = 'pdf_index_state.json'

def load_state():
    """Load progress state if exists"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {'processed_ids': [], 'last_page_token': None, 'total_found': 0}

def save_state(state):
    """Save progress state"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def main():
    print("="*80)
    print("📊 Google Drive PDF Indexer")
    print("="*80)
    
    # Load state
    state = load_state()
    print(f"\n📂 Resume from: {len(state['processed_ids'])} PDFs already indexed")
    
    # Load workspace credentials
    print("\n🔐 Loading Google Drive credentials...")
    with open(WORKSPACE_CREDS, 'r') as f:
        workspace_dict = json.load(f)
    
    drive_creds = service_account.Credentials.from_service_account_info(
        workspace_dict,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    ).with_subject('george@upowerenergy.uk')
    
    drive_service = build('drive', 'v3', credentials=drive_creds)
    
    # Load BigQuery credentials
    print("🔐 Loading BigQuery credentials...")
    bq_client = bigquery.Client.from_service_account_json(
        BQ_CREDS,
        project=PROJECT_ID
    )
    
    # Create table if not exists
    print(f"📊 Preparing BigQuery table: {PROJECT_ID}.{DATASET}.{TABLE}")
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    
    schema = [
        bigquery.SchemaField("file_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("filename", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("file_size", "INTEGER"),
        bigquery.SchemaField("created_time", "TIMESTAMP"),
        bigquery.SchemaField("modified_time", "TIMESTAMP"),
        bigquery.SchemaField("web_view_link", "STRING"),
        bigquery.SchemaField("drive_url", "STRING"),
        bigquery.SchemaField("parent_folders", "STRING", mode="REPEATED"),
        bigquery.SchemaField("mime_type", "STRING"),
        bigquery.SchemaField("indexed_at", "TIMESTAMP"),
        bigquery.SchemaField("is_chunked", "BOOLEAN"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    try:
        table = bq_client.create_table(table)
        print(f"✅ Created table {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"✅ Table {table_id} already exists")
        else:
            print(f"⚠️  Table warning: {e}")
    
    # Search for PDFs and insert in batches
    print("\n🔍 Scanning Google Drive for PDFs...")
    query = "mimeType='application/pdf' and trashed=false"
    page_token = state.get('last_page_token')
    
    batch_pdfs = []
    page_num = state.get('pages_scanned', 0)
    total_inserted = len(state['processed_ids'])
    BATCH_SIZE = 1000
    
    # Check which are already chunked (do this once at start)
    print(f"\n🔍 Checking which PDFs are already chunked...")
    chunked_check_query = f"""
    SELECT DISTINCT JSON_VALUE(metadata, '$.drive_url') as drive_url
    FROM `{PROJECT_ID}.{DATASET}.document_chunks`
    WHERE JSON_VALUE(metadata, '$.mime_type') = 'application/pdf'
    """
    chunked_results = bq_client.query(chunked_check_query).result()
    chunked_urls = {row.drive_url for row in chunked_results if row.drive_url}
    print(f"✅ Found {len(chunked_urls)} PDFs already chunked")
    
    try:
        while True:
            page_num += 1
            print(f"\r📄 Page {page_num} | Batch: {len(batch_pdfs)}/{BATCH_SIZE} | Inserted: {total_inserted:,}", end="", flush=True)
            
            results = drive_service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, size, createdTime, modifiedTime, webViewLink, parents, mimeType)",
                pageToken=page_token
            ).execute()
            
            files = results.get('files', [])
            
            # Filter out already processed
            new_files = [f for f in files if f['id'] not in state['processed_ids']]
            batch_pdfs.extend(new_files)
            
            page_token = results.get('nextPageToken')
            state['last_page_token'] = page_token
            state['pages_scanned'] = page_num
            
            # Insert batch when we reach BATCH_SIZE or no more pages
            if len(batch_pdfs) >= BATCH_SIZE or not page_token:
                if batch_pdfs:
                    print(f"\n💾 Inserting batch of {len(batch_pdfs)} PDFs into BigQuery...")
                    
                    rows_to_insert = []
                    for pdf in batch_pdfs:
                        drive_url = f"https://drive.google.com/file/d/{pdf['id']}/view?usp=drivesdk"
                        is_chunked = drive_url in chunked_urls
                        
                        row = {
                            "file_id": pdf['id'],
                            "filename": pdf['name'],
                            "file_size": int(pdf.get('size', 0)) if pdf.get('size') else 0,
                            "created_time": pdf.get('createdTime'),
                            "modified_time": pdf.get('modifiedTime'),
                            "web_view_link": pdf.get('webViewLink'),
                            "drive_url": drive_url,
                            "parent_folders": pdf.get('parents', []),
                            "mime_type": pdf['mimeType'],
                            "indexed_at": datetime.utcnow().isoformat(),
                            "is_chunked": is_chunked,
                        }
                        rows_to_insert.append(row)
                    
                    # Insert into BigQuery
                    errors = bq_client.insert_rows_json(table_id, rows_to_insert)
                    
                    if errors:
                        print(f"❌ Errors: {errors[:3]}")  # Show first 3 errors
                    else:
                        total_inserted += len(batch_pdfs)
                        state['processed_ids'].extend([pdf['id'] for pdf in batch_pdfs])
                        state['total_found'] = total_inserted
                        save_state(state)
                        print(f"✅ Inserted {len(batch_pdfs)} PDFs | Total: {total_inserted:,}")
                    
                    batch_pdfs = []  # Clear batch
            
            if not page_token:
                break
        
        print(f"\n\n✅ Scan complete!")
        print(f"📊 Total PDFs indexed: {total_inserted:,}")
        
        # Summary
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Total PDFs indexed: {total_inserted:,}")
        print(f"Chunked in document_chunks: {len(chunked_urls)}")
        print(f"Not yet chunked: {total_inserted - len([url for url in chunked_urls if any(pid in url for pid in state['processed_ids'])])}")
        print(f"\nBigQuery table: {table_id}")
        print(f"State file: {STATE_FILE}")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted! Progress saved.")
        print(f"   Processed: {len(state['processed_ids'])} PDFs")
        print(f"   Run again to resume from where you left off.")
        save_state(state)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"   Progress saved. Run again to resume.")
        save_state(state)
        raise

if __name__ == "__main__":
    main()
