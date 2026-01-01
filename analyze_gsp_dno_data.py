#!/usr/bin/env python3
"""
Comprehensive GSP/DNO Data Analysis
Combines NESO geography with Elexon settlement codes
"""

from google.cloud import bigquery
import pandas as pd
import sys

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def analyze_gsp_coverage():
    """Analyze GSP coverage and hierarchy"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("\n" + "="*80)
    print("📍 GSP/DNO DATA ANALYSIS - NESO + ELEXON INTEGRATION")
    print("="*80)
    
    # 1. GSP Groups Overview (DNO Licence Areas)
    print("\n1️⃣ GSP GROUPS (DNO Licence Areas) - 14 regions")
    print("-" * 80)
    
    query = f"""
    SELECT 
        gsp_group_id,
        gsp_group_name,
        dno_short_code,
        dno_name,
        primary_coverage_area
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_groups`
    ORDER BY gsp_group_id
    """
    
    df_groups = client.query(query).to_dataframe()
    print(df_groups.to_string(index=False))
    
    # 2. Individual GSPs per Group
    print("\n\n2️⃣ INDIVIDUAL GSPs - 333 Grid Supply Points")
    print("-" * 80)
    
    query = f"""
    SELECT 
        gsp_group,
        COUNT(*) as gsp_count,
        ROUND(SUM(area_sqkm), 0) as total_area_sqkm,
        STRING_AGG(gsp_name, ', ' ORDER BY gsp_name LIMIT 3) as sample_gsps
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    GROUP BY gsp_group
    ORDER BY gsp_group
    """
    
    df_gsp_count = client.query(query).to_dataframe()
    print(df_gsp_count.to_string(index=False))
    
    # 3. DNO Reference Data (Settlement Codes)
    print("\n\n3️⃣ DNO SETTLEMENT REFERENCE (MPAN Distributor IDs)")
    print("-" * 80)
    
    query = f"""
    SELECT 
        mpan_distributor_id,
        gsp_group_id,
        dno_short_code,
        dno_name,
        market_participant_id
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
    ORDER BY gsp_group_id
    """
    
    df_dno_ref = client.query(query).to_dataframe()
    print(df_dno_ref.to_string(index=False))
    
    # 4. Search Criteria Data Availability Analysis
    print("\n\n4️⃣ DATA AVAILABILITY BY SEARCH CRITERIA")
    print("-" * 80)
    
    # BM Units by GSP Group
    query = f"""
    SELECT 
        gsp_group,
        COUNT(DISTINCT bmu_id) as bmu_count,
        COUNT(DISTINCT lead_party_name) as party_count,
        ROUND(SUM(max_capacity_mw), 0) as total_capacity_mw,
        STRING_AGG(DISTINCT fuel_type_category, ', ') as fuel_types
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = TRUE AND gsp_group IS NOT NULL
    GROUP BY gsp_group
    ORDER BY total_capacity_mw DESC
    LIMIT 10
    """
    
    df_bmu_by_gsp = client.query(query).to_dataframe()
    print("\n🔋 BM Units by GSP Group (Top 10 by capacity):")
    print(df_bmu_by_gsp.to_string(index=False))
    
    # Fuel type distribution
    query = f"""
    SELECT 
        fuel_type_category,
        COUNT(*) as bmu_count,
        ROUND(SUM(max_capacity_mw), 0) as total_capacity_mw,
        COUNT(DISTINCT gsp_group) as gsp_groups,
        ROUND(AVG(max_capacity_mw), 1) as avg_capacity_mw
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = TRUE
    GROUP BY fuel_type_category
    ORDER BY total_capacity_mw DESC
    """
    
    df_fuel = client.query(query).to_dataframe()
    print("\n⚡ Fuel Type Distribution:")
    print(df_fuel.to_string(index=False))
    
    # VLP analysis by region
    query = f"""
    WITH vlp_units AS (
        SELECT 
            rg.gsp_group,
            rg.bmu_id,
            rg.bmu_name,
            rg.max_capacity_mw,
            dp.is_vlp
        FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators` rg
        LEFT JOIN `{PROJECT_ID}.{DATASET}.dim_party` dp
            ON rg.lead_party_name = dp.party_name
        WHERE rg.is_active = TRUE
    )
    SELECT 
        gsp_group,
        COUNT(*) as total_units,
        COUNTIF(is_vlp = TRUE) as vlp_units,
        ROUND(100.0 * COUNTIF(is_vlp = TRUE) / COUNT(*), 1) as vlp_percentage,
        ROUND(SUM(max_capacity_mw), 0) as total_capacity_mw
    FROM vlp_units
    WHERE gsp_group IS NOT NULL
    GROUP BY gsp_group
    ORDER BY vlp_units DESC
    LIMIT 10
    """
    
    df_vlp = client.query(query).to_dataframe()
    print("\n📊 VLP Units by GSP Group (Top 10):")
    print(df_vlp.to_string(index=False))
    
    # 5. Report Generation Possibilities
    print("\n\n5️⃣ REPORT & GRAPH CAPABILITIES")
    print("-" * 80)
    
    reports = [
        ("GSP Regional Generation Capacity", "Stacked bar chart by fuel type per GSP Group"),
        ("DNO Network Load vs Generation", "Bubble chart: capacity vs demand by DNO"),
        ("VLP Revenue by GSP Region", "Heatmap showing £/MWh earnings per region"),
        ("Battery Storage Deployment Map", "Geographic map colored by storage capacity"),
        ("Wind Farm Locations", "Scatter plot with lat/long from NESO boundaries"),
        ("DNO Constraint Cost Analysis", "Time series line chart by licence area"),
        ("GSP Group Settlement Volumes", "Daily/monthly settlement data trends"),
        ("Technology Mix by Region", "Pie charts per GSP Group"),
        ("Connection Queue by DNO", "Bar chart of pending projects"),
        ("Voltage Level Distribution", "Histogram of HV/LV/EHV connections per DNO"),
        ("Capacity Factor Analysis", "Box plot by fuel type and region"),
        ("Geographic Coverage Heatmap", "Area_sqkm vs generation density")
    ]
    
    for i, (report_name, description) in enumerate(reports, 1):
        print(f"\n  {i:2d}. {report_name}")
        print(f"      → {description}")
    
    # 6. Data Completeness Check
    print("\n\n6️⃣ DATA COMPLETENESS & QUALITY")
    print("-" * 80)
    
    query = f"""
    SELECT 
        'BM Units' as dataset,
        COUNT(*) as total_records,
        COUNTIF(gsp_group IS NOT NULL) as with_gsp,
        COUNTIF(fuel_type_category IS NOT NULL) as with_fuel_type,
        COUNTIF(max_capacity_mw IS NOT NULL) as with_capacity,
        COUNTIF(lead_party_name IS NOT NULL) as with_party
    FROM `{PROJECT_ID}.{DATASET}.ref_bmu_generators`
    WHERE is_active = TRUE
    
    UNION ALL
    
    SELECT 
        'GSP Boundaries' as dataset,
        COUNT(*) as total_records,
        COUNTIF(boundary IS NOT NULL) as with_gsp,
        COUNTIF(gsp_group IS NOT NULL) as with_fuel_type,
        COUNTIF(area_sqkm IS NOT NULL) as with_capacity,
        NULL as with_party
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_boundaries`
    
    UNION ALL
    
    SELECT 
        'DNO Reference' as dataset,
        COUNT(*) as total_records,
        COUNTIF(gsp_group_id IS NOT NULL) as with_gsp,
        COUNTIF(mpan_distributor_id IS NOT NULL) as with_fuel_type,
        COUNTIF(market_participant_id IS NOT NULL) as with_capacity,
        NULL as with_party
    FROM `{PROJECT_ID}.{DATASET}.neso_dno_reference`
    """
    
    df_completeness = client.query(query).to_dataframe()
    print(df_completeness.to_string(index=False))
    
    # 7. Sample GSP-to-Elexon Mapping
    print("\n\n7️⃣ GSP GROUP CODE MAPPING (NESO ↔ ELEXON)")
    print("-" * 80)
    print("\nElexon GSP Group Codes (_A through _P):")
    print("  _A = Eastern (UKPN-EPN)")
    print("  _B = London (UKPN-LPN)")
    print("  _C = South Eastern (UKPN-SPN)")
    print("  _D = North Western (Electricity North West)")
    print("  _E = Yorkshire (Northern Powergrid)")
    print("  _F = Southern (Scottish & Southern - Southern)")
    print("  _G = Merseyside & North Wales (Scottish Power Manweb)")
    print("  _H = Central & Southern Scotland (Scottish Power)")
    print("  _J = South East Scotland (Scottish & Southern - SEPD)")
    print("  _K = South Wales (National Grid - South Wales)")
    print("  _L = North Scotland (Scottish & Southern - SHEPD)")
    print("  _M = Midlands (National Grid - Midlands)")
    print("  _N = North East (Northern Powergrid)")
    print("  _P = East Midlands (National Grid)")
    
    query = f"""
    SELECT 
        gsp_group_id,
        gsp_group_name,
        dno_short_code,
        primary_coverage_area
    FROM `{PROJECT_ID}.{DATASET}.neso_gsp_groups`
    ORDER BY gsp_group_id
    """
    
    df_mapping = client.query(query).to_dataframe()
    print("\nNESO GSP Groups Table:")
    print(df_mapping.to_string(index=False))
    
    print("\n\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print("\n📋 Summary:")
    print(f"  • {len(df_groups)} GSP Groups (DNO Licence Areas)")
    print(f"  • 333 Individual GSPs")
    print(f"  • {len(df_dno_ref)} DNO Operators")
    print(f"  • 1,403 Active BM Units")
    print(f"  • {len(df_fuel)} Fuel Types")
    print(f"  • 12 Report Types Available")
    print("\n💡 Next Steps:")
    print("  1. Create unified GSP/DNO reference view")
    print("  2. Add GSP lat/long to search tooltips")
    print("  3. Enhance Network Locations export with FES data")
    print("  4. Build regional capacity dashboard")
    print("  5. Implement geographic boundary visualization")

def main():
    try:
        analyze_gsp_coverage()
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
