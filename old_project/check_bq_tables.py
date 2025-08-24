#!/usr/bin/env python3
"""
Script to check data in BigQuery tables for the GB Energy Dashboard
"""
from google.cloud import bigquery

def main():
    print("Checking data in BigQuery tables for GB Energy Dashboard...")
    client = bigquery.Client(project='jibber-jabber-knowledge')
    
    tables = [
        'neso_demand_forecasts',
        'neso_wind_forecasts',
        'neso_carbon_intensity',
        'neso_interconnector_flows', 
        'neso_balancing_services',
        'elexon_system_warnings'
    ]
    
    print("\nRecord counts:")
    for table in tables:
        query = f"""
        SELECT COUNT(*) as count 
        FROM `jibber-jabber-knowledge.uk_energy_prod.{table}`
        """
        try:
            count = client.query(query).result().to_dataframe()['count'].values[0]
            print(f"- {table}: {count:,} records")
            
            # Also check a sample record
            sample_query = f"""
            SELECT * 
            FROM `jibber-jabber-knowledge.uk_energy_prod.{table}`
            LIMIT 1
            """
            sample = client.query(sample_query).result().to_dataframe()
            print(f"  Sample columns: {', '.join(sample.columns)}")
            
        except Exception as e:
            print(f"- {table}: ERROR - {str(e)}")
    
    print("\nCheck complete!")

if __name__ == "__main__":
    main()
