#!/usr/bin/env python3
"""
Comprehensive API Diagnostics - Check all API connections and status
"""
import sys
sys.path.insert(0, "drive-bq-indexer")

import os
import json
from datetime import datetime
from google.cloud import bigquery
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Setup
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gridsmart_service_account.json"

def print_header(title):
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print(f"{'='*70}")

def check_service_account():
    """Check if service account file exists and is valid"""
    print_header("SERVICE ACCOUNT CHECK")
    
    sa_path = "gridsmart_service_account.json"
    
    if not os.path.exists(sa_path):
        print(f"❌ Service account file not found: {sa_path}")
        return False
    
    print(f"✅ Service account file exists: {sa_path}")
    
    try:
        with open(sa_path, 'r') as f:
            sa_data = json.load(f)
        
        print(f"✅ Service account JSON is valid")
        print(f"   Project ID: {sa_data.get('project_id')}")
        print(f"   Client Email: {sa_data.get('client_email')}")
        print(f"   Type: {sa_data.get('type')}")
        
        return True
    except Exception as e:
        print(f"❌ Error reading service account: {e}")
        return False

def check_bigquery_access():
    """Check BigQuery API access"""
    print_header("BIGQUERY API CHECK")
    
    try:
        client = bigquery.Client()
        print(f"✅ BigQuery client initialized")
        print(f"   Project: {client.project}")
        
        # List datasets
        datasets = list(client.list_datasets())
        print(f"✅ Can access BigQuery datasets: {len(datasets)} found")
        for dataset in datasets:
            print(f"   - {dataset.dataset_id}")
        
        # Check specific dataset
        dataset_id = "uk_energy_insights"
        try:
            dataset = client.get_dataset(dataset_id)
            print(f"✅ Dataset '{dataset_id}' accessible")
            
            # List tables
            tables = list(client.list_tables(dataset))
            print(f"✅ Tables in dataset: {len(tables)}")
            for table in tables:
                table_ref = client.get_table(table)
                print(f"   - {table.table_id}: {table_ref.num_rows:,} rows")
        except Exception as e:
            print(f"⚠️  Cannot access dataset '{dataset_id}': {e}")
        
        return True
    except Exception as e:
        print(f"❌ BigQuery access failed: {e}")
        return False

def check_drive_access():
    """Check Google Drive API access"""
    print_header("GOOGLE DRIVE API CHECK")
    
    try:
        # Build Drive service
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Try domain-wide delegation
        delegated_creds = creds.with_subject('george@upowerenergy.uk')
        service = build('drive', 'v3', credentials=delegated_creds)
        
        print(f"✅ Drive API client initialized")
        print(f"   Impersonating: george@upowerenergy.uk")
        
        # Test query
        results = service.files().list(
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Drive API access successful")
        print(f"   Retrieved {len(files)} sample files:")
        for f in files[:5]:
            print(f"   - {f['name']} ({f['mimeType']})")
        
        return True
    except Exception as e:
        print(f"❌ Drive API access failed: {e}")
        print(f"   This might indicate:")
        print(f"   - Domain-wide delegation not configured")
        print(f"   - Service account lacks Drive API access")
        print(f"   - Wrong impersonation email")
        return False

def check_sheets_access():
    """Check Google Sheets API access"""
    print_header("GOOGLE SHEETS API CHECK")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        service = build('sheets', 'v4', credentials=creds)
        print(f"✅ Sheets API client initialized")
        
        # Note: Can't test without a specific sheet ID
        print(f"   (Need a Sheet ID to test read/write)")
        
        return True
    except Exception as e:
        print(f"❌ Sheets API access failed: {e}")
        return False

def check_network_connectivity():
    """Check network connectivity to Google APIs"""
    print_header("NETWORK CONNECTIVITY CHECK")
    
    import urllib.request
    import ssl
    
    endpoints = {
        "Google APIs": "https://www.googleapis.com",
        "BigQuery": "https://bigquery.googleapis.com",
        "Drive API": "https://www.googleapis.com/drive/v3/about",
        "Sheets API": "https://sheets.googleapis.com",
    }
    
    for name, url in endpoints.items():
        try:
            # Create SSL context (ignore cert verification for testing)
            context = ssl.create_default_context()
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5, context=context)
            status = response.getcode()
            print(f"✅ {name}: HTTP {status}")
        except Exception as e:
            print(f"❌ {name}: {str(e)[:60]}")

def check_extraction_status():
    """Check current extraction status"""
    print_header("EXTRACTION STATUS CHECK")
    
    try:
        client = bigquery.Client()
        
        # Check documents
        query = """
        SELECT 
            COUNT(*) as total_docs,
            COUNT(DISTINCT doc_id) as unique_docs
        FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
        """
        
        result = list(client.query(query).result())[0]
        print(f"📊 Documents (clean):")
        print(f"   Total: {result.total_docs:,}")
        print(f"   Unique: {result.unique_docs:,}")
        
        # Check chunks
        query = """
        SELECT 
            COUNT(*) as total_chunks,
            COUNT(DISTINCT doc_id) as docs_with_chunks
        FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`
        """
        
        result = list(client.query(query).result())[0]
        print(f"📊 Chunks:")
        print(f"   Total chunks: {result.total_chunks:,}")
        print(f"   Docs with chunks: {result.docs_with_chunks:,}")
        
        # Check embeddings
        query = """
        SELECT COUNT(*) as total_embeddings
        FROM `inner-cinema-476211-u9.uk_energy_insights.chunk_embeddings`
        """
        
        result = list(client.query(query).result())[0]
        print(f"📊 Embeddings:")
        print(f"   Total: {result.total_embeddings:,}")
        
        # Calculate progress
        docs_total = 153201
        docs_processed = result.docs_with_chunks
        remaining = docs_total - docs_processed
        progress = (docs_processed / docs_total) * 100
        
        print(f"\n⏳ Progress:")
        print(f"   Processed: {docs_processed:,} / {docs_total:,}")
        print(f"   Remaining: {remaining:,}")
        print(f"   Progress: {progress:.1f}%")
        
        return True
    except Exception as e:
        print(f"❌ Could not check extraction status: {e}")
        return False

def check_server_status():
    """Check UpCloud server status"""
    print_header("UPCLOUD SERVER CHECK")
    
    import subprocess
    
    server_ip = "94.237.55.15"
    
    # Ping test
    try:
        result = subprocess.run(
            ['ping', '-c', '2', server_ip],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Server {server_ip} is reachable")
        else:
            print(f"❌ Server {server_ip} is not responding to ping")
    except Exception as e:
        print(f"⚠️  Could not ping server: {e}")
    
    # SSH test
    try:
        result = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=5', f'root@{server_ip}', 'echo "OK"'],
            capture_output=True,
            timeout=10,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ SSH connection to server successful")
            
            # Check Docker
            result = subprocess.run(
                ['ssh', f'root@{server_ip}', 'docker ps --format "{{.Names}}: {{.Status}}"'],
                capture_output=True,
                timeout=10,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ Docker containers:")
                for line in result.stdout.strip().split('\n'):
                    if line:
                        print(f"   {line}")
        else:
            print(f"❌ SSH connection failed")
    except Exception as e:
        print(f"⚠️  Could not SSH to server: {e}")

def main():
    """Run all diagnostic checks"""
    print("\n" + "="*70)
    print("🏥 COMPREHENSIVE API DIAGNOSTICS")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {
        "Service Account": check_service_account(),
        "Network Connectivity": check_network_connectivity(),
        "BigQuery Access": check_bigquery_access(),
        "Google Drive Access": check_drive_access(),
        "Google Sheets Access": check_sheets_access(),
        "Extraction Status": check_extraction_status(),
        "Server Status": check_server_status(),
    }
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for check, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {check}")
    
    print(f"\n📊 Overall: {passed}/{total} checks passed")
    
    if failed > 0:
        print(f"\n⚠️  {failed} checks failed - review details above")
    else:
        print(f"\n🎉 All systems operational!")

if __name__ == "__main__":
    main()
