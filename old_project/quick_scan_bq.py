#!/usr/bin/env python3
"""
Quick scan for NESO and Elexon data in BigQuery.
"""

from google.cloud import bigquery

def main():
    print("NESO and Elexon Data Quick Report")
    print("=================================")
    
    client = bigquery.Client(project='jibber-jabber-knowledge')
    
    for dataset in client.list_datasets():
        ds = dataset.dataset_id
        print(f"\nDataset: {ds}")
        
        tables = list(client.list_tables(dataset))
        
        neso_tables = [t for t in tables if 'neso' in t.table_id.lower()]
        elexon_tables = [t for t in tables if 'elexon' in t.table_id.lower()]
        
        if neso_tables or elexon_tables:
            if neso_tables:
                print("  NESO tables:")
                for t in neso_tables:
                    print(f"    - {t.table_id}")
            
            if elexon_tables:
                print("  Elexon tables:")
                for t in elexon_tables:
                    print(f"    - {t.table_id}")
        else:
            print("  No NESO or Elexon tables found.")

if __name__ == "__main__":
    main()
