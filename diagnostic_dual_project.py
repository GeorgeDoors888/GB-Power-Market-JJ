#!/usr/bin/env python3
"""
Dual-Project API Diagnostics
- jibber-jabber-knowledge: Google Workspace APIs (Drive, Sheets, Docs, Apps Script, Maps)
- inner-cinema-476211-u9: BigQuery only (Smart Grid data)
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

# Project configurations
WORKSPACE_PROJECT = "jibber-jabber-knowledge"  # @upowerenergy.uk
BIGQUERY_PROJECT = "inner-cinema-476211-u9"     # Smart Grid
IMPERSONATE_USER = "george@upowerenergy.uk"

def print_header(title):
    print(f"\n{'='*70}")
    print(f"🔍 {title}")
    print(f"{'='*70}")

def check_service_account():
    """Check service account configuration"""
    print_header("SERVICE ACCOUNT CHECK")
    
    sa_path = "gridsmart_service_account.json"
    
    if not os.path.exists(sa_path):
        print(f"❌ Service account not found: {sa_path}")
        return False
    
    with open(sa_path, 'r') as f:
        sa_data = json.load(f)
    
    print(f"✅ Service account file valid")
    print(f"   Project: {sa_data.get('project_id')}")
    print(f"   Email: {sa_data.get('client_email')}")
    print(f"   Client ID: {sa_data.get('client_id')}")
    
    return True

def check_google_drive():
    """Check Google Drive API access (@upowerenergy.uk)"""
    print_header("GOOGLE DRIVE API - jibber-jabber-knowledge")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/drive.readonly']
        )
        
        # Domain-wide delegation
        delegated_creds = creds.with_subject(IMPERSONATE_USER)
        service = build('drive', 'v3', credentials=delegated_creds)
        
        print(f"✅ Drive API initialized")
        print(f"   Impersonating: {IMPERSONATE_USER}")
        
        # Test API call
        results = service.files().list(
            pageSize=5,
            fields="files(id, name, mimeType, owners)"
        ).execute()
        
        files = results.get('files', [])
        print(f"✅ Drive API working: {len(files)} files retrieved")
        
        if files:
            print(f"   Sample files:")
            for f in files[:3]:
                owner = f.get('owners', [{}])[0].get('emailAddress', 'unknown')
                print(f"   - {f['name'][:40]} ({owner})")
        
        return True
        
    except Exception as e:
        print(f"❌ Drive API failed: {str(e)[:200]}")
        if "unauthorized_client" in str(e):
            print(f"   ⚠️  Domain-wide delegation not configured!")
            print(f"   → Go to admin.google.com → Security → API Controls")
            print(f"   → Manage Domain Wide Delegation")
            print(f"   → Add Client ID with Drive scopes")
        return False

def check_google_sheets():
    """Check Google Sheets API access"""
    print_header("GOOGLE SHEETS API - jibber-jabber-knowledge")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        delegated_creds = creds.with_subject(IMPERSONATE_USER)
        service = build('sheets', 'v4', credentials=delegated_creds)
        
        print(f"✅ Sheets API initialized")
        print(f"   Impersonating: {IMPERSONATE_USER}")
        print(f"   (Needs Sheet ID to test read/write)")
        
        return True
        
    except Exception as e:
        print(f"❌ Sheets API failed: {str(e)[:200]}")
        return False

def check_google_docs():
    """Check Google Docs API access"""
    print_header("GOOGLE DOCS API - jibber-jabber-knowledge")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        
        delegated_creds = creds.with_subject(IMPERSONATE_USER)
        service = build('docs', 'v1', credentials=delegated_creds)
        
        print(f"✅ Docs API initialized")
        print(f"   Impersonating: {IMPERSONATE_USER}")
        print(f"   (Needs Doc ID to test reading)")
        
        return True
        
    except Exception as e:
        print(f"❌ Docs API failed: {str(e)[:200]}")
        return False

def check_apps_script():
    """Check Apps Script API access"""
    print_header("APPS SCRIPT API - jibber-jabber-knowledge")
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            "gridsmart_service_account.json",
            scopes=['https://www.googleapis.com/auth/script.projects.readonly']
        )
        
        delegated_creds = creds.with_subject(IMPERSONATE_USER)
        service = build('script', 'v1', credentials=delegated_creds)
        
        print(f"✅ Apps Script API initialized")
        print(f"   Impersonating: {IMPERSONATE_USER}")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Apps Script API: {str(e)[:100]}")
        print(f"   (May not be enabled in project)")
        return False

def check_google_maps():
    """Check Google Maps API access"""
    print_header("GOOGLE MAPS API - jibber-jabber-knowledge")
    
    try:
        # Note: Maps API typically uses API keys, not service accounts
        print(f"ℹ️  Google Maps API typically uses API keys")
        print(f"   Service account access is limited")
        print(f"   Check: console.cloud.google.com/google/maps-apis")
        
        return None  # Neutral result
        
    except Exception as e:
        print(f"⚠️  Maps API check: {str(e)[:100]}")
        return False

def check_bigquery_smart_grid():
    """Check BigQuery access for Smart Grid data"""
    print_header("BIGQUERY API - inner-cinema-476211-u9 (Smart Grid)")
    
    try:
        client = bigquery.Client(project=BIGQUERY_PROJECT)
        
        print(f"✅ BigQuery client initialized")
        print(f"   Project: {BIGQUERY_PROJECT}")
        
        # Check uk_energy_insights dataset
        dataset_id = "uk_energy_insights"
        dataset = client.get_dataset(dataset_id)
        
        print(f"✅ Dataset '{dataset_id}' accessible")
        
        # Check key tables
        tables_to_check = [
            "documents_clean",
            "chunks", 
            "chunk_embeddings"
        ]
        
        print(f"\n   📊 Key Tables:")
        for table_name in tables_to_check:
            try:
                table = client.get_table(f"{BIGQUERY_PROJECT}.{dataset_id}.{table_name}")
                print(f"   ✅ {table_name}: {table.num_rows:,} rows")
            except Exception as e:
                print(f"   ❌ {table_name}: {str(e)[:60]}")
        
        # Get extraction progress
        try:
            query = f"""
            SELECT 
                COUNT(DISTINCT doc_id) as docs_with_chunks
            FROM `{BIGQUERY_PROJECT}.{dataset_id}.chunks`
            """
            result = list(client.query(query).result())[0]
            
            query2 = f"""
            SELECT COUNT(*) as total_docs
            FROM `{BIGQUERY_PROJECT}.{dataset_id}.documents_clean`
            """
            result2 = list(client.query(query2).result())[0]
            
            processed = result.docs_with_chunks
            total = result2.total_docs
            remaining = total - processed
            progress = (processed / total * 100) if total > 0 else 0
            
            print(f"\n   📈 Extraction Progress:")
            print(f"   Processed: {processed:,} / {total:,} ({progress:.1f}%)")
            print(f"   Remaining: {remaining:,}")
            
        except Exception as e:
            print(f"   ⚠️  Could not get progress: {str(e)[:60]}")
        
        return True
        
    except Exception as e:
        print(f"❌ BigQuery failed: {str(e)[:200]}")
        return False

def check_chatgpt_apis():
    """Check if ChatGPT can access APIs via OAuth"""
    print_header("CHATGPT API ACCESS CHECK")
    
    print("ℹ️  ChatGPT needs OAuth access to:")
    print("   - Google Drive (@upowerenergy.uk)")
    print("   - Google Sheets (@upowerenergy.uk)")
    print("")
    print("   To enable:")
    print("   1. Go to: https://myaccount.google.com/permissions")
    print("   2. Look for 'ChatGPT' or 'OpenAI'")
    print("   3. If not listed or has issues, remove and re-auth")
    print("")
    print("   In ChatGPT:")
    print("   - Click profile → Settings → Data Controls")
    print("   - Connect Google Drive")
    print("   - Authorize with george@upowerenergy.uk account")
    
    return None

def main():
    """Run diagnostics for both projects"""
    print("\n" + "="*70)
    print("🏥 DUAL-PROJECT API DIAGNOSTICS")
    print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    print("\n📋 PROJECT CONFIGURATION:")
    print(f"   Workspace APIs: {WORKSPACE_PROJECT} (@upowerenergy.uk)")
    print(f"   BigQuery: {BIGQUERY_PROJECT} (Smart Grid)")
    print(f"   Impersonate: {IMPERSONATE_USER}")
    
    results = {}
    
    # Basic checks
    results["Service Account"] = check_service_account()
    
    # Workspace APIs (jibber-jabber-knowledge)
    print("\n" + "="*70)
    print("📱 GOOGLE WORKSPACE APIs - jibber-jabber-knowledge")
    print("="*70)
    results["Google Drive"] = check_google_drive()
    results["Google Sheets"] = check_google_sheets()
    results["Google Docs"] = check_google_docs()
    results["Apps Script"] = check_apps_script()
    results["Google Maps"] = check_google_maps()
    
    # BigQuery (inner-cinema-476211-u9)
    print("\n" + "="*70)
    print("🔌 SMART GRID DATA - inner-cinema-476211-u9")
    print("="*70)
    results["BigQuery Smart Grid"] = check_bigquery_smart_grid()
    
    # ChatGPT
    check_chatgpt_apis()
    
    # Summary
    print_header("DIAGNOSTIC SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    neutral = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for check, status in results.items():
        if status is True:
            icon = "✅"
        elif status is False:
            icon = "❌"
        else:
            icon = "ℹ️ "
        print(f"{icon} {check}")
    
    print(f"\n📊 Results: {passed} passed / {failed} failed / {neutral} info")
    
    if failed > 0:
        print(f"\n⚠️  ISSUES FOUND:")
        if results.get("Google Drive") is False:
            print(f"   🔧 Fix Google Drive:")
            print(f"      1. Go to admin.google.com (as admin@upowerenergy.uk)")
            print(f"      2. Security → API Controls → Domain Wide Delegation")
            print(f"      3. Add service account Client ID with Drive scopes")
        
        if results.get("BigQuery Smart Grid") is False:
            print(f"   🔧 Fix BigQuery:")
            print(f"      Check service account permissions in:")
            print(f"      console.cloud.google.com/iam-admin/iam?project={BIGQUERY_PROJECT}")
    else:
        print(f"\n🎉 All critical systems operational!")

if __name__ == "__main__":
    main()
