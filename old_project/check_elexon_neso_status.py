#!/usr/bin/env python3
"""
Elexon & NESO Live Data Status Check
===================================
Verifies that the system is correctly fetching and storing data
from Elexon and NESO for the last 24 hours
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from tabulate import tabulate

def check_data_status():
    """Check if we have recent data in all tables"""
    print("\n📊 Elexon & NESO Live Data Status Check")
    print("======================================")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to BigQuery
    client = bigquery.Client(project='jibber-jabber-knowledge')
    dataset_id = "uk_energy_prod"
    
    # Tables to check (Elexon and NESO only)
    tables = {
        # Elexon tables
        'elexon_demand_outturn': 'Elexon Demand Outturn',
        'elexon_generation_outturn': 'Elexon Generation Outturn',
        'elexon_system_warnings': 'Elexon System Warnings',
        
        # NESO tables (via Elexon API)
        'neso_demand_forecasts': 'NESO Demand Forecasts',
        'neso_wind_forecasts': 'NESO Wind Forecasts',
        'neso_carbon_intensity': 'NESO Carbon Intensity',
        'neso_interconnector_flows': 'NESO Interconnector Flows',
        'neso_balancing_services': 'NESO Balancing Services'
    }
    
    # Get the date 24 hours ago
    yesterday = datetime.now() - timedelta(hours=24)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    # Check each table
    status_rows = []
    
    for table_id, description in tables.items():
        try:
            # Query for the most recent data
            query = f"""
            SELECT 
                MAX(settlementDate) as latest_date,
                COUNT(*) as record_count,
                (TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(TIMESTAMP(settlementDate)), HOUR)) as hours_ago
            FROM 
                `jibber-jabber-knowledge.{dataset_id}.{table_id}`
            WHERE
                settlementDate >= TIMESTAMP("{yesterday_str}")
            """
            
            df = client.query(query).result().to_dataframe()
            
            if df.empty or df['latest_date'].iloc[0] is None:
                status = "❌ No data found in last 24 hours"
                latest = "N/A"
                count = 0
                hours = "N/A"
            else:
                latest = df['latest_date'].iloc[0].strftime('%Y-%m-%d %H:%M') if df['latest_date'].iloc[0] else "N/A"
                count = int(df['record_count'].iloc[0])
                hours = df['hours_ago'].iloc[0]
                
                if hours <= 1:
                    status = "✅ Recent data (< 1 hour)"
                elif hours <= 6:
                    status = "✅ Data present (< 6 hours)"
                else:
                    status = f"⚠️ Data outdated ({hours} hours old)"
            
            status_rows.append([description, latest, count, f"{hours} hours" if hours != "N/A" else "N/A", status])
            
        except Exception as e:
            status_rows.append([description, "ERROR", 0, "N/A", f"❌ Error: {str(e)[:50]}..."])
    
    # Print results as a table
    headers = ["Data Source", "Latest Data", "Records (24h)", "Age", "Status"]
    print(tabulate(status_rows, headers=headers, tablefmt="pretty"))
    
    # Summary
    success_count = sum(1 for row in status_rows if "✅" in row[4])
    warning_count = sum(1 for row in status_rows if "⚠️" in row[4])
    error_count = sum(1 for row in status_rows if "❌" in row[4])
    
    print(f"\nSummary: {success_count} tables up-to-date, {warning_count} warnings, {error_count} errors")
    
    if error_count > 0:
        print("\n⚠️ Some data sources have errors. Check logs for details.")
    elif warning_count > 0:
        print("\n⚠️ Some data is outdated. Check if the updater is running.")
    else:
        print("\n✅ All Elexon and NESO data sources are working correctly!")

if __name__ == "__main__":
    check_data_status()
