"""
Load REAL NESO DNO and GSP Group data from Master Reference CSV
This is the official data we've been working with!
"""

from google.cloud import bigquery
import pandas as pd
import json

def load_neso_dno_data():
    """Load the official NESO DNO Master Reference data"""
    
    print("🗄️  Loading OFFICIAL NESO DNO Master Reference...")
    
    # Load the CSV
    csv_path = "/Users/georgemajor/Jibber-Jabber-Work/DNO_Master_Reference.csv"
    df = pd.read_csv(csv_path)
    
    print(f"✅ Loaded {len(df)} DNO records")
    print("\nDNO Records:")
    print(df[['DNO_Name', 'DNO_Short_Code', 'GSP_Group_ID', 'GSP_Group_Name', 'Primary_Coverage_Area']].to_string())
    
    return df

def create_bigquery_table(df):
    """Create BigQuery table with real NESO DNO data"""
    
    print("\n🗄️  Loading to BigQuery...")
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    table_id = "inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference"
    
    # Filter out non-DNO entries (NESO, Elexon)
    dno_df = df[~df['DNO_Short_Code'].isin(['NESO', 'ELEXON'])].copy()
    
    # Create schema
    schema = [
        bigquery.SchemaField("mpan_distributor_id", "INTEGER"),
        bigquery.SchemaField("dno_key", "STRING"),
        bigquery.SchemaField("dno_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_short_code", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("market_participant_id", "STRING"),
        bigquery.SchemaField("gsp_group_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("website_url", "STRING"),
        bigquery.SchemaField("document_library_url", "STRING"),
        bigquery.SchemaField("contact_info", "STRING"),
        bigquery.SchemaField("primary_coverage_area", "STRING"),
    ]
    
    # Prepare data
    records = []
    for _, row in dno_df.iterrows():
        records.append({
            "mpan_distributor_id": int(row['MPAN_Distributor_ID']),
            "dno_key": str(row['DNO_Key']),
            "dno_name": str(row['DNO_Name']),
            "dno_short_code": str(row['DNO_Short_Code']),
            "market_participant_id": str(row['Market_Participant_ID']),
            "gsp_group_id": str(row['GSP_Group_ID']),
            "gsp_group_name": str(row['GSP_Group_Name']),
            "website_url": str(row['Website_URL']),
            "document_library_url": str(row['Document_Library_URL']),
            "contact_info": str(row['Contact_Info']),
            "primary_coverage_area": str(row['Primary_Coverage_Area']),
        })
    
    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        job = client.load_table_from_json(records, table_id, job_config=job_config)
        job.result()  # Wait for completion
        
        table = client.get_table(table_id)
        print(f"✅ Loaded {table.num_rows} DNO records to BigQuery")
        print(f"   Table: {table_id}")
        
        # Verify the data
        query = f"""
        SELECT 
            dno_short_code,
            dno_name,
            gsp_group_id,
            gsp_group_name,
            primary_coverage_area
        FROM `{table_id}`
        ORDER BY mpan_distributor_id
        """
        
        print("\n📊 Loaded DNO Reference Data:")
        print("-" * 120)
        
        results = client.query(query).result()
        for row in results:
            print(f"{row.dno_short_code:8} | {row.dno_name:50} | GSP {row.gsp_group_id:2} ({row.gsp_group_name:20}) | {row.primary_coverage_area}")
        
        return table_id
        
    except Exception as e:
        print(f"❌ Error loading to BigQuery: {e}")
        return None

def create_gsp_groups_table():
    """Create separate GSP groups table"""
    
    print("\n🗄️  Creating GSP Groups table...")
    
    csv_path = "/Users/georgemajor/Jibber-Jabber-Work/DNO_Master_Reference.csv"
    df = pd.read_csv(csv_path)
    
    # Filter DNOs only
    dno_df = df[~df['DNO_Short_Code'].isin(['NESO', 'ELEXON'])].copy()
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    table_id = "inner-cinema-476211-u9.uk_energy_prod.neso_gsp_groups"
    
    # Create GSP records
    gsp_records = []
    for _, row in dno_df.iterrows():
        gsp_records.append({
            "gsp_group_id": str(row['GSP_Group_ID']),
            "gsp_group_name": str(row['GSP_Group_Name']),
            "dno_short_code": str(row['DNO_Short_Code']),
            "dno_name": str(row['DNO_Name']),
            "primary_coverage_area": str(row['Primary_Coverage_Area']),
        })
    
    schema = [
        bigquery.SchemaField("gsp_group_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gsp_group_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("dno_short_code", "STRING"),
        bigquery.SchemaField("dno_name", "STRING"),
        bigquery.SchemaField("primary_coverage_area", "STRING"),
    ]
    
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    try:
        job = client.load_table_from_json(gsp_records, table_id, job_config=job_config)
        job.result()
        
        table = client.get_table(table_id)
        print(f"✅ Loaded {table.num_rows} GSP groups to BigQuery")
        print(f"   Table: {table_id}")
        
        return table_id
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🗺️  NESO DNO & GSP Group Reference Data Loader")
    print("=" * 60)
    print("\nLoading OFFICIAL NESO data from Master Reference CSV")
    print()
    
    # Load and display data
    df = load_neso_dno_data()
    
    # Load to BigQuery
    dno_table = create_bigquery_table(df)
    gsp_table = create_gsp_groups_table()
    
    if dno_table and gsp_table:
        print("\n✅ SUCCESS!")
        print("\nTables created:")
        print(f"1. {dno_table}")
        print(f"2. {gsp_table}")
        print("\nThis is the REAL NESO data with:")
        print("  - 14 DNO operators")
        print("  - 14 GSP groups (A-P, excluding I and O)")
        print("  - MPAN distributor IDs")
        print("  - Market participant IDs")
        print("  - Coverage areas")
        print("  - Contact information")
