#!/usr/bin/env python3
"""
Create accurate GSP flow map using correct BMRS data
"""

from google.cloud import bigquery
import json

def main():
    print("🔍 Querying LATEST GSP flow data...")
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    # Get the actual latest available date
    date_query = """
    SELECT MAX(DATE(settlementDate)) as latest_date
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
    """
    latest_date = list(client.query(date_query).result())[0].latest_date
    print(f"📅 Latest date in data: {latest_date}")
    
    # Get GSP flow for latest complete settlement period
    query = f"""
    WITH gen_data AS (
        SELECT 
            boundary,
            settlementPeriod,
            SUM(generation) as total_generation
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen`
        WHERE DATE(settlementDate) = '{latest_date}'
        GROUP BY boundary, settlementPeriod
    ),
    dem_data AS (
        SELECT 
            boundary,
            settlementPeriod,
            SUM(demand) as total_demand
        FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem`
        WHERE DATE(settlementDate) = '{latest_date}'
        GROUP BY boundary, settlementPeriod
    )
    SELECT 
        g.boundary as gsp,
        g.settlementPeriod as period,
        g.total_generation as gen_mw,
        d.total_demand as dem_mw,
        (g.total_generation + d.total_demand) as net_flow_mw
    FROM gen_data g
    INNER JOIN dem_data d 
        ON g.boundary = d.boundary 
        AND g.settlementPeriod = d.settlementPeriod
    WHERE g.settlementPeriod = (
        SELECT MAX(settlementPeriod) 
        FROM gen_data
    )
    ORDER BY net_flow_mw DESC
    """
    
    results = list(client.query(query).result())
    
    if not results:
        print("❌ No data found")
        return
    
    print(f"\n✅ Found {len(results)} GSP areas")
    print(f"📊 Settlement Period: {results[0].period}\n")
    
    print("=" * 80)
    print("GSP FLOW DATA (Generation vs Demand)")
    print("=" * 80)
    print(f"{'GSP':5} {'Generation (MW)':>15} {'Demand (MW)':>15} {'Net Flow (MW)':>15} {'Status':>12}")
    print("-" * 80)
    
    exporters = 0
    importers = 0
    
    for r in results:
        status = "EXPORTING" if r.net_flow_mw > 0 else "IMPORTING"
        if r.net_flow_mw > 0:
            exporters += 1
        else:
            importers += 1
        print(f"{r.gsp:5} {r.gen_mw:>15,.0f} {r.dem_mw:>15,.0f} {r.net_flow_mw:>15,.0f} {status:>12}")
    
    print("-" * 80)
    print(f"\n📈 Summary: {exporters} exporters, {importers} importers")
    
    # Now check generator data
    print("\n" + "=" * 80)
    print("CHECKING GENERATOR DATA")
    print("=" * 80)
    
    gen_query = """
    SELECT 
        COUNT(*) as total_count,
        COUNT(DISTINCT dno) as dno_count,
        COUNT(DISTINCT gsp) as gsp_count,
        SUM(CASE WHEN lat IS NOT NULL AND lng IS NOT NULL THEN 1 ELSE 0 END) as with_coords,
        SUM(CASE WHEN dno IS NOT NULL AND dno != '' THEN 1 ELSE 0 END) as with_dno,
        SUM(CASE WHEN gsp IS NOT NULL AND gsp != '' THEN 1 ELSE 0 END) as with_gsp
    FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators`
    """
    
    gen_info = list(client.query(gen_query).result())[0]
    print(f"Total generators: {gen_info.total_count:,}")
    print(f"With coordinates: {gen_info.with_coords:,}")
    print(f"With DNO data: {gen_info.with_dno:,}")
    print(f"With GSP data: {gen_info.with_gsp:,}")
    print(f"Distinct DNOs: {gen_info.dno_count}")
    print(f"Distinct GSPs: {gen_info.gsp_count}")

if __name__ == "__main__":
    main()
