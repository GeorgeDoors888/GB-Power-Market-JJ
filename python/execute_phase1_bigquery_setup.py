#!/usr/bin/env python3
"""
Execute BigQuery Table and View Creation - Phase 1

Creates:
1. iris.vlp_revenue_sp fact table (Task 1)
2. iris.bod_boalf_7d_summary view (Task 2)

This script reads the SQL files and executes them against BigQuery.
"""

from google.cloud import bigquery
import sys
import time

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def execute_sql_file(client, sql_file_path, description):
    """Execute a SQL file against BigQuery"""
    print(f"\n{'='*80}")
    print(f"📊 {description}")
    print(f"{'='*80}")
    
    try:
        # Read SQL file
        with open(sql_file_path, 'r') as f:
            sql = f.read()
        
        # Remove comments and split into statements
        lines = []
        for line in sql.split('\n'):
            # Skip comment lines
            if line.strip().startswith('--'):
                continue
            lines.append(line)
        
        sql_clean = '\n'.join(lines)
        
        print(f"\n📄 Reading: {sql_file_path}")
        print(f"📝 SQL length: {len(sql_clean)} characters")
        
        # Execute query
        print(f"\n⏳ Executing query...")
        start_time = time.time()
        
        job = client.query(sql_clean)
        result = job.result()  # Wait for completion
        
        elapsed = time.time() - start_time
        
        print(f"\n✅ Success!")
        print(f"⏱️  Execution time: {elapsed:.2f} seconds")
        
        # Get job statistics
        if job.total_bytes_processed:
            gb_processed = job.total_bytes_processed / (1024**3)
            print(f"📊 Data processed: {gb_processed:.2f} GB")
        
        if hasattr(job, 'num_dml_affected_rows') and job.num_dml_affected_rows:
            print(f"📝 Rows affected: {job.num_dml_affected_rows:,}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_table_exists(client, table_id):
    """Verify that a table or view exists and show sample data"""
    print(f"\n🔍 Verifying: {table_id}")
    
    try:
        table = client.get_table(table_id)
        print(f"   ✅ Exists: {table.table_type}")
        print(f"   📊 Rows: {table.num_rows:,}" if table.num_rows else "   📊 View (no row count)")
        print(f"   💾 Size: {table.num_bytes / (1024**2):.2f} MB" if table.num_bytes else "")
        
        # Get sample data
        query = f"SELECT * FROM `{table_id}` LIMIT 5"
        df = client.query(query).to_dataframe()
        
        print(f"\n   📋 Sample data ({len(df)} rows):")
        print(f"   Columns: {', '.join(df.columns.tolist()[:10])}")
        if len(df) > 0:
            print(f"   Date range: {df.iloc[0].get('settlement_date', 'N/A')} to {df.iloc[-1].get('settlement_date', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Not found or error: {e}")
        return False


def main():
    print("🚀 BigQuery Table & View Creation - Phase 1")
    print(f"📍 Project: {PROJECT_ID}")
    print(f"📍 Dataset: {DATASET}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID, location="US")
        print(f"\n✅ Connected to BigQuery")
    except Exception as e:
        print(f"\n❌ Failed to connect to BigQuery: {e}")
        return 1
    
    success = True
    
    # Task 1: Create vlp_revenue_sp fact table
    sql_file_1 = '/Users/georgemajor/GB-Power-Market-JJ/sql/create_vlp_revenue_sp_fact_table.sql'
    if not execute_sql_file(client, sql_file_1, "TASK 1: Create vlp_revenue_sp Fact Table"):
        success = False
        print("\n⚠️  Task 1 failed! Cannot proceed to Task 2 (view depends on this table)")
        return 1
    
    # Verify table creation
    table_id = f"{PROJECT_ID}.{DATASET}.vlp_revenue_sp"
    if not verify_table_exists(client, table_id):
        print(f"\n⚠️  Table {table_id} not found after creation!")
        success = False
        return 1
    
    print("\n" + "="*80)
    print("⏸️  Pausing 5 seconds before Task 2...")
    print("="*80)
    time.sleep(5)
    
    # Task 2: Create bod_boalf_7d_summary view
    sql_file_2 = '/Users/georgemajor/GB-Power-Market-JJ/sql/create_bod_boalf_7d_summary_view.sql'
    if not execute_sql_file(client, sql_file_2, "TASK 2: Create bod_boalf_7d_summary View"):
        success = False
    
    # Verify view creation
    view_id = f"{PROJECT_ID}.{DATASET}.bod_boalf_7d_summary"
    if not verify_table_exists(client, view_id):
        print(f"\n⚠️  View {view_id} not found after creation!")
        success = False
    
    # Final summary
    print("\n" + "="*80)
    print("📊 PHASE 1 COMPLETION SUMMARY")
    print("="*80)
    
    if success:
        print("\n✅ Phase 1 Complete!")
        print("\n📍 Created:")
        print(f"   1. Table: {PROJECT_ID}.{DATASET}.vlp_revenue_sp")
        print(f"   2. View:  {PROJECT_ID}.{DATASET}.bod_boalf_7d_summary")
        
        print("\n🎯 Next Steps (Phase 2):")
        print("   Task 3: Fix Dashboard V3 KPI F9 (VLP Revenue)")
        print("   Task 4: Fix Dashboard V3 KPI I9 (All-GB Net Margin)")
        print("   Task 5: Fix Dashboard V3 KPI J9 (Selected DNO Net Margin)")
        print("   Task 6: Fix Dashboard V3 KPI K9 (Selected DNO Volume)")
        print("   Task 7: Fix Dashboard V3 KPI L9 (Selected DNO Revenue)")
        
        print("\n💡 Test Query:")
        print(f"   SELECT * FROM `{view_id}` WHERE breakdown = 'GB_total';")
        
        return 0
    else:
        print("\n❌ Phase 1 failed with errors")
        return 1


if __name__ == '__main__':
    sys.exit(main())
