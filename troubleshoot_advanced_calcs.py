#!/usr/bin/env python3
"""
Troubleshoot Advanced Calculations
Check why BOD data and other calculations are failing
"""

from google.cloud import bigquery
from datetime import datetime, timedelta

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET_ID = 'uk_energy_prod'

def check_table_exists(client, table_name):
    """Check if table exists and has data"""
    try:
        table_ref = f"`{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        query = f"SELECT COUNT(*) as count FROM {table_ref}"
        result = client.query(query).result()
        count = list(result)[0].count
        return True, count
    except Exception as e:
        return False, str(e)

def check_table_schema(client, table_name):
    """Get table schema"""
    try:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
        table = client.get_table(table_ref)
        return [{"name": field.name, "type": field.field_type} for field in table.schema]
    except Exception as e:
        return f"Error: {e}"

def check_date_range(client, table_name, date_col):
    """Check date range in table"""
    try:
        table_ref = f"`{PROJECT_ID}.{DATASET_ID}.{table_name}`"
        query = f"""
        SELECT 
            MIN(DATE({date_col})) as min_date,
            MAX(DATE({date_col})) as max_date
        FROM {table_ref}
        """
        result = client.query(query).result()
        row = list(result)[0]
        return row.min_date, row.max_date
    except Exception as e:
        return None, str(e)

def test_bod_query(client):
    """Test the BOD query that's failing"""
    print("\n🔍 Testing BOD Query...")
    
    # First check if table exists
    exists, info = check_table_exists(client, 'bmrs_bod')
    print(f"   Table 'bmrs_bod' exists: {exists}")
    if exists:
        print(f"   Row count: {info:,}")
    else:
        print(f"   Error: {info}")
        return
    
    # Check schema
    print("\n   Schema:")
    schema = check_table_schema(client, 'bmrs_bod')
    if isinstance(schema, list):
        for field in schema[:10]:  # First 10 fields
            print(f"      {field['name']} ({field['type']})")
    else:
        print(f"      {schema}")
    
    # Check date range
    print("\n   Checking date ranges with different column names...")
    for date_col in ['settlementDate', 'settlement_date', 'timeFrom', 'time_from']:
        try:
            min_d, max_d = check_date_range(client, 'bmrs_bod', date_col)
            if min_d and not isinstance(min_d, str):
                print(f"      {date_col}: {min_d} → {max_d}")
                
                # Try wind curtailment query with this date column
                print(f"\n   Testing wind curtailment query with {date_col}...")
                query = f"""
                SELECT COUNT(*) as count
                FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
                WHERE DATE({date_col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                    AND soFlag = 'B'
                """
                result = client.query(query).result()
                count = list(result)[0].count
                print(f"      BIDs in last 7 days: {count:,}")
                
                # Check if bmUnit column exists and has WIND
                wind_query = f"""
                SELECT COUNT(*) as count
                FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
                WHERE DATE({date_col}) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                    AND UPPER(bmUnit) LIKE '%WIND%'
                """
                result = client.query(wind_query).result()
                wind_count = list(result)[0].count
                print(f"      Records with WIND in bmUnit: {wind_count:,}")
                
                break
        except Exception as e:
            print(f"      {date_col}: Not found or error")

def test_balancing_stats_query(client):
    """Test balancing statistics query"""
    print("\n🔍 Testing Balancing Stats Query...")
    
    exists, info = check_table_exists(client, 'bmrs_bod')
    if not exists:
        print("   Table 'bmrs_bod' not found - skipping")
        return
    
    # Try the actual query from the script
    query = f"""
    SELECT
        soFlag,
        SUM(ABS(bidOfferAcceptanceLevel)) as total_volume_mwh,
        AVG(bidOfferAcceptancePrice) as avg_price,
        COUNT(*) as acceptance_count
    FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
    WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY soFlag
    """
    
    try:
        df = client.query(query).to_dataframe()
        if df.empty:
            print("   ⚠️  Query returned no results")
            print("   Checking if data exists with different column names...")
            
            # Try alternative column names
            alt_queries = [
                ("settlement_date + bid_offer_level", """
                SELECT soFlag, COUNT(*) as count
                FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
                WHERE DATE(settlement_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY soFlag
                """),
                ("timeFrom + level", """
                SELECT soFlag, COUNT(*) as count
                FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_bod`
                WHERE DATE(timeFrom) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
                GROUP BY soFlag
                """)
            ]
            
            for name, alt_q in alt_queries:
                try:
                    alt_df = client.query(alt_q).to_dataframe()
                    if not alt_df.empty:
                        print(f"\n   ✅ Found data with {name}:")
                        print(alt_df.to_string(index=False))
                except Exception as e:
                    print(f"   {name}: {str(e)[:100]}")
        else:
            print("   ✅ Query successful:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"   ❌ Query failed: {e}")

def check_all_tables(client):
    """Check all tables needed for advanced calculations"""
    print("\n📋 Checking All Required Tables...\n")
    
    tables_to_check = [
        ('bmrs_bod', 'settlementDate', 'BOD Acceptances'),
        ('bmrs_fuelinst', 'publishTime', 'Fuel Instructions'),
        ('bmrs_fuelinst_iris', 'publishTime', 'Fuel Instructions (IRIS)'),
        ('bmrs_freq', 'recordTime', 'Frequency'),
        ('bmrs_mid', 'settlementDate', 'Market Index Data'),
        ('bmrs_netbsad', 'settlementDate', 'Net BSAD'),
    ]
    
    results = []
    for table, date_col, description in tables_to_check:
        print(f"Checking {table} ({description})...")
        exists, info = check_table_exists(client, table)
        
        if exists:
            min_d, max_d = check_date_range(client, table, date_col)
            if min_d and not isinstance(min_d, str):
                results.append({
                    'table': table,
                    'exists': '✅',
                    'rows': f"{info:,}",
                    'date_range': f"{min_d} → {max_d}"
                })
            else:
                results.append({
                    'table': table,
                    'exists': '⚠️',
                    'rows': f"{info:,}",
                    'date_range': f"Error: {max_d}"
                })
        else:
            results.append({
                'table': table,
                'exists': '❌',
                'rows': 'N/A',
                'date_range': 'Table not found'
            })
    
    # Print summary table
    print("\n" + "=" * 100)
    print(f"{'Table':<25} {'Status':<8} {'Rows':<15} {'Date Range':<40}")
    print("=" * 100)
    for r in results:
        print(f"{r['table']:<25} {r['exists']:<8} {r['rows']:<15} {r['date_range']:<40}")
    print("=" * 100)

def main():
    print("🔬 Troubleshooting Advanced Calculations")
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🗄️  Dataset: {PROJECT_ID}.{DATASET_ID}\n")
    print("=" * 100)
    
    # Connect to BigQuery
    client = bigquery.Client(project=PROJECT_ID)
    
    # Check all tables
    check_all_tables(client)
    
    # Test specific queries
    test_bod_query(client)
    test_balancing_stats_query(client)
    
    print("\n" + "=" * 100)
    print("\n✅ Troubleshooting complete!")
    print("\n💡 Next Steps:")
    print("   1. If bmrs_bod doesn't exist, need to ingest BOD data")
    print("   2. If column names are different, update queries in update_analysis_with_calculations.py")
    print("   3. If no recent data, check ingestion pipeline")

if __name__ == '__main__':
    main()
