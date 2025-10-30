#!/bin/bash
# Monitor script to clear FUELINST tables before repairs start

echo "======================================================================"
echo "FUELINST TABLE CLEANER - Monitoring for 2022 completion"
echo "======================================================================"
echo "Started: $(date)"
echo ""

# Wait for 2022 to complete by checking the log
LOG_DIR="logs_$(ls -t logs_* | head -1 | cut -d'_' -f2-)"
YEAR_2022_LOG="${LOG_DIR}/2022_full_year.log"

echo "Monitoring: $YEAR_2022_LOG"
echo "Waiting for 2022 ingestion to complete..."
echo ""

# Poll every 60 seconds
while true; do
    if grep -q "Ingestion run completed" "$YEAR_2022_LOG" 2>/dev/null; then
        echo "✅ 2022 ingestion completed at $(date)"
        echo ""
        break
    fi
    
    # Show progress every 5 minutes
    if [ $((SECONDS % 300)) -eq 0 ]; then
        progress=$(tail -100 "$YEAR_2022_LOG" 2>/dev/null | grep "Dataset:" | tail -1 || echo "Loading...")
        echo "[$(date +%H:%M)] Status: $progress"
    fi
    
    sleep 60
done

echo "======================================================================"
echo "CLEARING FUELINST/FREQ/FUELHH TABLES"
echo "======================================================================"
echo "Start: $(date)"
echo ""

# Clear the tables using Python
.venv/bin/python << 'EOF'
from google.cloud import bigquery

PROJECT = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT)

tables_to_clear = ["bmrs_fuelinst", "bmrs_freq", "bmrs_fuelhh"]

print("Clearing tables to remove empty window metadata...")
print()

for table_name in tables_to_clear:
    table_id = f"{PROJECT}.{DATASET}.{table_name}"
    
    try:
        # Check if table exists
        client.get_table(table_id)
        
        # Delete all data
        query = f"DELETE FROM `{table_id}` WHERE TRUE"
        print(f"Clearing {table_name}...", end=" ", flush=True)
        
        job = client.query(query)
        result = job.result()
        
        rows_deleted = job.num_dml_affected_rows if hasattr(job, 'num_dml_affected_rows') else 0
        print(f"✅ Deleted {rows_deleted:,} rows")
        
    except Exception as e:
        error_msg = str(e)
        if "Not found" in error_msg:
            print(f"{table_name}: ⏭️  Table doesn't exist (will be created fresh)")
        else:
            print(f"{table_name}: ❌ Error: {error_msg[:80]}")

print()
print("✅ Tables cleared - ready for fresh FUELINST data!")
print()
EOF

echo "======================================================================"
echo "CLEANUP COMPLETE"
echo "======================================================================"
echo "Completed: $(date)"
echo ""
echo "The repair script will now load fresh FUELINST data without conflicts."
echo "Monitor progress: tail -f complete_data_load_master.log"
echo "======================================================================"
