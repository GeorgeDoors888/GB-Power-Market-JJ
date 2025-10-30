#!/bin/bash
#
# Complete solution: Clean duplicates and restart ingestion with proper monitoring
#

set -e  # Exit on error

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Duplicate Cleanup & Ingestion Restart"
echo "=========================================="
echo ""

# Step 1: Check for running processes
echo "Step 1: Checking for running processes..."
if pgrep -f "ingest_elexon_fixed.py" > /dev/null; then
    echo "⚠️  Ingestion process is still running. Stopping it..."
    pkill -f "ingest_elexon_fixed.py"
    sleep 3
fi
echo "✅ No ingestion processes running"
echo ""

# Step 2: List all BMRS tables to clean
echo "Step 2: Getting list of BMRS tables..."
TABLES=$(bq ls uk_energy_prod | grep "^  bmrs_" | awk '{print $1}')
TABLE_COUNT=$(echo "$TABLES" | wc -l | tr -d ' ')
echo "Found $TABLE_COUNT BMRS tables"
echo ""

# Step 3: Clean duplicates from each table
echo "Step 3: Cleaning duplicates from all tables..."
echo "This may take several minutes..."
echo ""

cat > /tmp/deduplicate_all_tables.py << 'PYEOF'
#!/usr/bin/env python3
import sys
from google.cloud import bigquery
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

def deduplicate_table(client, project_id, dataset_id, table_name):
    """Remove duplicates from a table using _hash_key"""
    full_table_id = f"{project_id}.{dataset_id}.{table_name}"
    
    # Check if table has _hash_key column
    try:
        table = client.get_table(full_table_id)
        has_hash_key = any(field.name == '_hash_key' for field in table.schema)
        
        if not has_hash_key:
            logging.info(f"  ⏭️  {table_name}: No _hash_key column, skipping")
            return
            
        # Count duplicates
        check_query = f"""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT _hash_key) as unique_keys,
            COUNT(*) - COUNT(DISTINCT _hash_key) as duplicates
        FROM `{full_table_id}`
        WHERE _hash_key IS NOT NULL
        """
        
        result = list(client.query(check_query).result())[0]
        
        if result.duplicates == 0:
            logging.info(f"  ✅ {table_name}: No duplicates ({result.total:,} rows)")
            return
        
        logging.info(f"  🔧 {table_name}: Removing {result.duplicates:,} duplicates...")
        
        # Create deduplicated temp table
        temp_table = f"{full_table_id}_temp"
        dedup_query = f"""
        CREATE OR REPLACE TABLE `{temp_table}` AS
        SELECT * EXCEPT(row_num)
        FROM (
            SELECT *, ROW_NUMBER() OVER (PARTITION BY _hash_key ORDER BY _ingested_utc DESC) as row_num
            FROM `{full_table_id}`
            WHERE _hash_key IS NOT NULL
        )
        WHERE row_num = 1
        """
        
        client.query(dedup_query).result()
        
        # Replace original with deduplicated version
        client.delete_table(full_table_id)
        
        replace_query = f"CREATE TABLE `{full_table_id}` AS SELECT * FROM `{temp_table}`"
        client.query(replace_query).result()
        
        client.delete_table(temp_table, not_found_ok=True)
        
        logging.info(f"  ✅ {table_name}: Cleaned! ({result.unique_keys:,} unique rows)")
        
    except Exception as e:
        logging.error(f"  ❌ {table_name}: Error - {e}")

if __name__ == "__main__":
    client = bigquery.Client(project="inner-cinema-476211-u9")
    
    tables = sys.stdin.read().strip().split('\n')
    total = len([t for t in tables if t.strip()])
    
    logging.info(f"Processing {total} tables...\n")
    
    for i, table_name in enumerate(tables, 1):
        table_name = table_name.strip()
        if not table_name:
            continue
        logging.info(f"[{i}/{total}] {table_name}")
        deduplicate_table(client, "inner-cinema-476211-u9", "uk_energy_prod", table_name)
    
    logging.info("\n✅ All tables processed!")
PYEOF

echo "$TABLES" | .venv/bin/python /tmp/deduplicate_all_tables.py

echo ""
echo "=========================================="
echo "Step 4: Restarting ingestion with improvements"
echo "=========================================="
echo ""

# Step 4: Restart ingestion
LOG_FILE="jan_aug_ingest_$(date +%Y%m%d_%H%M%S).log"

echo "Starting 2025 ingestion..."
echo "Log file: $LOG_FILE"

nohup .venv/bin/python ingest_elexon_fixed.py --start 2025-01-01 --end 2025-08-31 > "$LOG_FILE" 2>&1 &
PID_2025=$!

echo "✅ Process started (PID: $PID_2025)"
echo ""

# Wait a few seconds and check it's running
sleep 5

if ps -p $PID_2025 > /dev/null; then
    echo "✅ Ingestion is running!"
    echo ""
    echo "To monitor: tail -f $LOG_FILE"
    echo "To check process: ps aux | grep $PID_2025"
    echo ""
    
    # Setup auto-start for 2024
    echo "Setting up automatic 2024 ingestion..."
    cat > /tmp/start_2024.sh << SHEOF
#!/bin/bash
while kill -0 $PID_2025 2>/dev/null; do
    sleep 60
done
echo "\$(date): 2025 complete, starting 2024..."
cd "$PROJECT_DIR"
nohup .venv/bin/python ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31 > year_2024_ingest.log 2>&1 &
SHEOF
    
    chmod +x /tmp/start_2024.sh
    nohup /tmp/start_2024.sh > auto_2024_starter.log 2>&1 &
    
    echo "✅ Auto-start for 2024 configured"
    echo ""
    echo "=========================================="
    echo "All done! Ingestion is running."
    echo "=========================================="
else
    echo "❌ Process failed to start. Check $LOG_FILE for errors"
    exit 1
fi
