#!/usr/bin/env python3
"""
Generate comprehensive JSON data dictionary for all NESO & Elexon datasets
Outputs: data_dictionary.json with searchable metadata
"""

from google.cloud import bigquery
import json
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

# Categorize tables by source/purpose
TABLE_CATEGORIES = {
    'BMRS Historical': ['bmrs_bod', 'bmrs_boalf', 'bmrs_freq', 'bmrs_mid', 'bmrs_costs', 
                        'bmrs_fuelinst', 'bmrs_disbsad', 'bmrs_indgen', 'bmrs_netbsad',
                        'bmrs_pn', 'bmrs_qpn', 'bmrs_remit', 'bmrs_sysdem', 'bmrs_windfor'],
    'BMRS Real-time (IRIS)': ['bmrs_bod_iris', 'bmrs_boalf_iris', 'bmrs_freq_iris', 
                              'bmrs_fuelinst_iris', 'bmrs_indgen_iris'],
    'P114 Settlement': ['p114_full', 'p114_settlement_canonical', 'elexon_p114_s0142_bpi',
                        'elexon_p114_s0142_derived'],
    'NESO Data': ['neso_constraint_breakdown', 'neso_dno_boundaries', 'neso_dno_reference',
                  'neso_skip_rates_summary', 'obp_physical_notifications'],
    'DNO & Network': ['duos_unit_rates', 'duos_time_bands', 'constraint_costs_timeline',
                     'constraint_costs_by_dno', 'constraint_costs_by_dno_latest'],
    'Generator Data': ['all_generators', 'generator_capacity', 'generator_types'],
    'VLP Analysis': ['vlp_units', 'vlp_revenue_summary', 'mart_vlp_revenue_p114'],
    'Balancing Mechanism': ['balancing_acceptances', 'balancing_dynamic_sel', 
                           'balancing_nonbm_volumes', 'bid_offer_data', 'boalf_with_prices'],
    'Market Analysis': ['bm_market_kpis', 'bm_kpi_summary', 'generation_mix_complete'],
    'BESS Data': ['bess_asset_config', 'bess_fr_schedule'],
}

def get_table_category(table_name):
    """Determine category for a table"""
    for category, tables in TABLE_CATEGORIES.items():
        if table_name in tables:
            return category
        # Check prefixes
        if table_name.startswith('bmrs_') and table_name.endswith('_iris'):
            return 'BMRS Real-time (IRIS)'
        elif table_name.startswith('bmrs_'):
            return 'BMRS Historical'
        elif table_name.startswith('neso_constraint_breakdown'):
            return 'NESO Data'
        elif table_name.startswith('p114_'):
            return 'P114 Settlement'
    return 'Other/Views'

def get_sample_data(client, table_ref, max_rows=3):
    """Fetch sample data from table"""
    try:
        query = f"""
        SELECT * FROM `{table_ref}`
        LIMIT {max_rows}
        """
        result = client.query(query).result()
        samples = []
        for row in result:
            samples.append(dict(row))
        return samples
    except Exception as e:
        return [{"error": str(e)}]

def get_table_stats(client, table_ref):
    """Get table statistics"""
    try:
        table = client.get_table(table_ref)
        return {
            'num_rows': table.num_rows,
            'size_mb': round(table.num_bytes / 1024 / 1024, 2),
            'created': table.created.isoformat() if table.created else None,
            'modified': table.modified.isoformat() if table.modified else None,
            'table_type': table.table_type,
        }
    except Exception as e:
        return {'error': str(e)}

def generate_data_dictionary():
    """Generate comprehensive data dictionary"""
    print('📚 Generating Data Dictionary for NESO & Elexon Datasets')
    print('='*80)
    
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # Get all tables
    print(f'\n📊 Scanning dataset: {DATASET}')
    tables = list(client.list_tables(f'{PROJECT_ID}.{DATASET}'))
    print(f'✅ Found {len(tables)} tables')
    
    dictionary = {
        'metadata': {
            'project': PROJECT_ID,
            'dataset': DATASET,
            'generated': datetime.now().isoformat(),
            'total_tables': len(tables),
            'generator': 'generate_data_dictionary.py'
        },
        'tables': []
    }
    
    # Process each table
    for idx, table_info in enumerate(tables, 1):
        table_id = table_info.table_id
        table_ref = f'{PROJECT_ID}.{DATASET}.{table_id}'
        
        print(f'\n[{idx}/{len(tables)}] Processing: {table_id}', end=' ... ')
        
        try:
            # Get schema
            table = client.get_table(table_ref)
            
            # Build schema info
            fields = []
            for field in table.schema:
                fields.append({
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description or ''
                })
            
            # Get stats
            stats = get_table_stats(client, table_ref)
            
            # Get category
            category = get_table_category(table_id)
            
            # Build table entry
            table_entry = {
                'table_name': table_id,
                'category': category,
                'stats': stats,
                'schema': fields,
                'description': table.description or '',
                'full_path': table_ref
            }
            
            dictionary['tables'].append(table_entry)
            print(f'✅ ({len(fields)} columns, {stats.get("num_rows", 0):,} rows)')
            
        except Exception as e:
            print(f'❌ Error: {str(e)[:50]}')
            dictionary['tables'].append({
                'table_name': table_id,
                'error': str(e)
            })
    
    # Add category summary
    categories = {}
    for table in dictionary['tables']:
        cat = table.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    dictionary['metadata']['categories'] = categories
    
    # Save to JSON
    output_file = 'data_dictionary.json'
    with open(output_file, 'w') as f:
        json.dump(dictionary, f, indent=2, default=str)
    
    print('\n' + '='*80)
    print(f'✅ SUCCESS: Data dictionary generated')
    print('='*80)
    print(f'\nOutput: {output_file}')
    print(f'Total tables: {len(tables)}')
    print(f'\nCategories:')
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f'  {cat:30} {count:4} tables')
    
    # Create summary file
    summary = {
        'total_tables': len(tables),
        'categories': categories,
        'key_tables': {
            'VLP Analysis': ['vlp_units', 'mart_vlp_revenue_p114', 'boalf_with_prices'],
            'Settlement': ['p114_settlement_canonical', 'elexon_p114_s0142_bpi'],
            'Real-time': ['bmrs_fuelinst_iris', 'bmrs_freq_iris', 'bmrs_bod_iris'],
            'Constraint Costs': ['constraint_costs_by_dno_latest', 'neso_constraint_breakdown_2025_2026'],
            'DNO': ['neso_dno_boundaries', 'neso_dno_reference', 'duos_unit_rates']
        },
        'most_important': [
            'bmrs_bod (391M rows) - Bid-Offer Data',
            'p114_settlement_canonical - Settlement revenue',
            'bmrs_boalf_complete - Balancing acceptances WITH PRICES',
            'neso_dno_boundaries - Geographic boundaries (GEOGRAPHY type)',
            'bmrs_fuelinst - Generation mix by fuel type'
        ]
    }
    
    with open('data_dictionary_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f'\n📄 Also created: data_dictionary_summary.json (quick reference)')
    print(f'\n💡 Use cases:')
    print(f'   - Explore: jq ".tables[] | select(.category == \\"VLP Analysis\\")" data_dictionary.json')
    print(f'   - Search: jq ".tables[] | select(.table_name | contains(\\"freq\\"))" data_dictionary.json')
    print(f'   - Schema: jq ".tables[] | select(.table_name == \\"bmrs_bod\\").schema" data_dictionary.json')

if __name__ == '__main__':
    generate_data_dictionary()
