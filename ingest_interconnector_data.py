#!/usr/bin/env python3
"""
Ingest UK interconnector flow data from NESO API
Covers 7 interconnectors: IFA, IFA2, BritNed, Nemo, NSL, Viking, ElecLink
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ingest_neso_api import fetch_resource_data, upload_to_bigquery

# Interconnector dataset IDs from NESO API
INTERCONNECTOR_DATASETS = {
    'NSL': {
        'name': 'North Sea Link',
        'dataset_id': '7bf2e43d-1a24-4a0e-95b0-6ba4eba3daa9',
        'resource_id': '9db51c01-922d-413d-8b67-3938fdc14bdb',  # Current data
        'table_name': 'neso_nsl_capacity'
    },
    'Viking': {
        'name': 'Viking Link',
        'dataset_id': '53a942cc-f9ab-4ad3-a274-5beed51635ec',
        'resource_id': None,  # Will fetch first resource
        'table_name': 'neso_viking_capacity'
    },
    'ElecLink': {
        'name': 'ElecLink',
        'dataset_id': '46daeb44-95a7-4032-8a22-914c896ed261',
        'resource_id': None,
        'table_name': 'neso_eleclink_capacity'
    },
    'Nemo': {
        'name': 'NemoLink',
        'dataset_id': '24b229de-2806-45a6-89a9-88097d67e5f2',
        'resource_id': None,
        'table_name': 'neso_nemo_capacity'
    },
    'IFA': {
        'name': 'IFA',
        'dataset_id': 'a95d222b-e390-4ad0-af17-09de957616ed',
        'resource_id': None,
        'table_name': 'neso_ifa_capacity'
    },
    'IFA2': {
        'name': 'IFA2',
        'dataset_id': '860c8221-c656-4af3-800a-281b9e500489',
        'resource_id': None,
        'table_name': 'neso_ifa2_capacity'
    },
}

def ingest_interconnector_data():
    """Download all interconnector capacity data"""
    print('🔌 Ingesting UK Interconnector Capacity Data')
    print('='*80)
    
    results = {}
    
    for code, info in INTERCONNECTOR_DATASETS.items():
        print(f'\\n📊 {info["name"]} ({code})')
        print('-'*60)
        
        try:
            # If no resource_id, get first resource from dataset
            if info['resource_id'] is None:
                print(f'   Fetching dataset metadata...')
                # Would need to call API to get resources
                print(f'   ⚠️  Resource ID not specified - skipping for now')
                print(f'   💡 Run: python3 ingest_neso_api.py --dataset-id {info["dataset_id"]}')
                results[code] = 'NEEDS_RESOURCE_ID'
                continue
            
            # Download data
            print(f'   Downloading from NESO API...')
            df = fetch_resource_data(info['resource_id'])
            
            if df is None or len(df) == 0:
                print(f'   ❌ No data retrieved')
                results[code] = 'FAILED'
                continue
            
            print(f'   ✅ Retrieved {len(df):,} rows')
            
            # Upload to BigQuery
            print(f'   Uploading to BigQuery: {info["table_name"]}')
            success = upload_to_bigquery(df, info['table_name'])
            
            if success:
                print(f'   ✅ Upload complete')
                results[code] = 'SUCCESS'
            else:
                print(f'   ❌ Upload failed')
                results[code] = 'UPLOAD_FAILED'
                
        except Exception as e:
            print(f'   ❌ Error: {str(e)[:100]}')
            results[code] = f'ERROR: {str(e)[:50]}'
    
    # Summary
    print('\\n' + '='*80)
    print('✅ INTERCONNECTOR INGESTION SUMMARY')
    print('='*80)
    
    for code, status in results.items():
        icon = '✅' if status == 'SUCCESS' else '⚠️' if 'NEEDS' in status else '❌'
        print(f'{icon} {code:10} {status}')
    
    success_count = sum(1 for s in results.values() if s == 'SUCCESS')
    print(f'\\n📊 Success Rate: {success_count}/{len(results)} interconnectors')
    
    if success_count < len(results):
        print('\\n💡 Next steps:')
        print('   1. Get resource IDs for remaining interconnectors:')
        for code, info in INTERCONNECTOR_DATASETS.items():
            if results.get(code) == 'NEEDS_RESOURCE_ID':
                print(f'      python3 ingest_neso_api.py --dataset-id {info["dataset_id"]}')
        print('   2. Update INTERCONNECTOR_DATASETS dict with resource_id values')
        print('   3. Re-run this script')

if __name__ == '__main__':
    # Note: NESO API only has CAPACITY data (limits), not actual FLOWS
    print('⚠️  IMPORTANT: NESO API provides CAPACITY/LIMITS data')
    print('   For actual interconnector FLOWS, use BMRS PHYBMDATA stream')
    print('   Interconnector units: IFA-1, IFA2-1, INTEW-1 (ElecLink), etc.')
    print('\\n   Continuing with capacity data download...\\n')
    
    ingest_interconnector_data()
    
    print('\\n' + '='*80)
    print('📌 RECOMMENDATION: Ingest actual flows from BMRS')
    print('='*80)
    print('   Table: bmrs_indgen (Indicated Generation - includes interconnectors)')
    print('   Filter: bmUnitId IN (\\'IFA-1\\', \\'IFA2-1\\', \\'INTEW-1\\', \\'INTNED-1\\', etc.)')
    print('   Already ingested: Check existing bmrs_indgen table')
