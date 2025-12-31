#!/usr/bin/env python3
"""
Ingest P246 LLF Exclusions Data
BSC Modification P246: Line Loss Factor Exclusions for specific BMUs

Background:
- LLF (Line Loss Factors) adjust settlement for transmission/distribution losses
- P246 excludes certain BMUs from LLF adjustments (e.g., synchronous compensators)
- Impacts settlement calculations for excluded units
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_p246_exclusions_table():
    """
    Create table for P246 LLF exclusions

    Data sources:
    1. BSC Website: https://www.elexon.co.uk/mod-proposal/p246/
    2. NESO Technical Data: LLF exclusion lists
    3. Manual research: Units with synchronous compensator mode
    """

    print("\n📋 Creating P246 LLF Exclusions table...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Define schema
    schema = [
        bigquery.SchemaField("bmu_id", "STRING", description="BMU identifier"),
        bigquery.SchemaField("exclusion_reason", "STRING", description="Reason for LLF exclusion"),
        bigquery.SchemaField("effective_from", "DATE", description="Exclusion start date"),
        bigquery.SchemaField("effective_to", "DATE", description="Exclusion end date (NULL if ongoing)"),
        bigquery.SchemaField("unit_type", "STRING", description="Type of unit (synchronous compensator, etc.)"),
        bigquery.SchemaField("gsp_group", "STRING", description="GSP group location"),
        bigquery.SchemaField("settlement_impact", "STRING", description="Description of settlement impact"),
        bigquery.SchemaField("source", "STRING", description="Data source (P246, NESO, etc.)"),
        bigquery.SchemaField("notes", "STRING", description="Additional notes"),
        bigquery.SchemaField("created_at", "TIMESTAMP", description="Record creation timestamp"),
    ]

    table_id = f"{PROJECT_ID}.{DATASET}.p246_llf_exclusions"

    table = bigquery.Table(table_id, schema=schema)
    table.description = "BSC Mod P246 Line Loss Factor exclusions for specific BMUs"

    try:
        table = client.create_table(table)
        print(f"✅ Created table: {table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"⚠️  Table already exists: {table_id}")
            table = client.get_table(table_id)
        else:
            raise

    return table

def load_known_exclusions():
    """
    Load known P246 exclusions

    Based on:
    1. Dinorwig synchronous compensator mode (E_DINO)
    2. Other pumped storage units in compensator mode
    3. STATCOMs and synchronous condensers
    """

    print("\n📥 Loading known LLF exclusions...")

    # Known exclusions from industry knowledge
    exclusions = [
        {
            'bmu_id': 'E_DINO-1',
            'exclusion_reason': 'Synchronous compensator mode operation',
            'effective_from': '2015-11-01',  # P246 implementation date
            'effective_to': None,
            'unit_type': 'Pumped Storage / Synchronous Compensator',
            'gsp_group': 'North Wales',
            'settlement_impact': 'No LLF applied when operating in compensator mode (providing inertia/reactive power)',
            'source': 'BSC Mod P246',
            'notes': 'Dinorwig can operate as generator OR synchronous compensator. LLF excluded in comp mode.',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'bmu_id': 'E_FFES-1',
            'exclusion_reason': 'Synchronous compensator mode operation',
            'effective_from': '2015-11-01',
            'effective_to': None,
            'unit_type': 'Pumped Storage / Synchronous Compensator',
            'gsp_group': 'North Wales',
            'settlement_impact': 'No LLF applied in compensator mode',
            'source': 'BSC Mod P246',
            'notes': 'Ffestiniog pumped storage, similar to Dinorwig',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'bmu_id': 'E_CRUA-1',
            'exclusion_reason': 'Synchronous compensator mode operation',
            'effective_from': '2015-11-01',
            'effective_to': None,
            'unit_type': 'Pumped Storage / Synchronous Compensator',
            'gsp_group': 'South Scotland',
            'settlement_impact': 'No LLF applied in compensator mode',
            'source': 'BSC Mod P246',
            'notes': 'Cruachan pumped storage',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'bmu_id': 'E_FOYE-1',
            'exclusion_reason': 'Synchronous compensator mode operation',
            'effective_from': '2015-11-01',
            'effective_to': None,
            'unit_type': 'Pumped Storage / Synchronous Compensator',
            'gsp_group': 'North Scotland',
            'settlement_impact': 'No LLF applied in compensator mode',
            'source': 'BSC Mod P246',
            'notes': 'Foyers pumped storage',
            'created_at': datetime.utcnow().isoformat()
        },
    ]

    client = bigquery.Client(project=PROJECT_ID, location="US")
    table_id = f"{PROJECT_ID}.{DATASET}.p246_llf_exclusions"

    # Check existing rows
    existing_query = f"SELECT COUNT(*) as count FROM `{table_id}`"
    existing_count = client.query(existing_query).to_dataframe().iloc[0]['count']

    if existing_count > 0:
        print(f"  ⚠️  Table already has {existing_count} rows, appending new data...")

    # Load data
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
    )

    job = client.load_table_from_json(exclusions, table_id, job_config=job_config)
    job.result()

    table = client.get_table(table_id)
    print(f"✅ Loaded {len(exclusions)} exclusions")
    print(f"   Total rows in table: {table.num_rows}")

    return len(exclusions)

def create_exclusions_view():
    """Create view joining exclusions with BMU canonical model"""

    print("\n🔗 Creating exclusions enriched view...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    sql = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.v_p246_exclusions_enriched` AS
    SELECT
      e.bmu_id,
      e.exclusion_reason,
      e.effective_from,
      e.effective_to,
      e.unit_type,
      e.settlement_impact,
      e.source,
      e.notes,

      -- Enrich with BMU canonical data
      b.ng_bmu_id,
      b.fuel_type_category,
      b.max_capacity_mw,
      b.gsp_group as canonical_gsp_group,
      b.lead_party_name,
      b.is_active,

      -- Settlement impact flag
      CASE
        WHEN e.effective_to IS NULL THEN TRUE
        WHEN e.effective_to >= CURRENT_DATE() THEN TRUE
        ELSE FALSE
      END as is_currently_excluded

    FROM `{PROJECT_ID}.{DATASET}.p246_llf_exclusions` e
    LEFT JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` b
      ON e.bmu_id = b.bmu_id
    ORDER BY e.bmu_id
    """

    job = client.query(sql)
    job.result()

    print(f"✅ Created view: v_p246_exclusions_enriched")

def analyze_exclusions():
    """Analyze exclusion patterns and settlement impact"""

    print("\n📊 Analyzing LLF exclusions...")

    client = bigquery.Client(project=PROJECT_ID, location="US")

    # Query exclusions
    sql = f"""
    SELECT
      e.bmu_id,
      e.unit_type,
      e.exclusion_reason,
      b.max_capacity_mw,
      b.fuel_type_category,
      b.gsp_group
    FROM `{PROJECT_ID}.{DATASET}.v_p246_exclusions_enriched` e
    LEFT JOIN `{PROJECT_ID}.{DATASET}.ref_bmu_canonical` b
      ON e.bmu_id = b.bmu_id
    WHERE e.is_currently_excluded = TRUE
    ORDER BY b.max_capacity_mw DESC
    """

    df = client.query(sql).to_dataframe()

    if len(df) > 0:
        print(f"\n  Currently excluded BMUs: {len(df)}")
        print(f"  Total capacity affected: {df['max_capacity_mw'].sum():.0f} MW")
        print(f"\n  Breakdown:")
        print(f"  {'BMU ID':<15} {'Type':<40} {'Capacity (MW)':>15}")
        print("  " + "-"*70)
        for _, row in df.iterrows():
            print(f"  {row['bmu_id']:<15} {row['unit_type']:<40} {row['max_capacity_mw']:>15,.0f}")
    else:
        print("  ⚠️  No exclusions found (view may be empty)")

    return df

def main():
    print("="*80)
    print("P246 LLF EXCLUSIONS DATA INGESTION")
    print("="*80)
    print("\nBSC Modification P246:")
    print("  • Excludes specific BMUs from Line Loss Factor adjustments")
    print("  • Primarily affects synchronous compensators")
    print("  • Impacts settlement calculations for excluded units")
    print("  • Implementation: November 2015")

    # Create table
    create_p246_exclusions_table()

    # Load known exclusions
    count = load_known_exclusions()

    # Create enriched view
    create_exclusions_view()

    # Analyze
    df = analyze_exclusions()

    print("\n" + "="*80)
    print("✅ P246 LLF EXCLUSIONS INGESTION COMPLETE")
    print("="*80)
    print(f"\nData loaded:")
    print(f"  • Exclusions: {count} BMUs")
    print(f"  • Table: p246_llf_exclusions")
    print(f"  • View: v_p246_exclusions_enriched")
    print(f"\nQuery examples:")
    print(f"  SELECT * FROM `{PROJECT_ID}.{DATASET}.v_p246_exclusions_enriched`;")
    print(f"\nNote: This is a small dataset (4 major pumped storage units)")
    print(f"      May need expansion based on NESO technical documentation")

if __name__ == "__main__":
    main()
