#!/bin/bash
# Property-Owning Companies Extractor for AlmaLinux Server
# Extracts distinct company registration numbers from BigQuery
# Runs daily via cron

LOG_DIR="/var/www/property_companies/logs"
OUTPUT_DIR="/var/www/property_companies/data"
OUTPUT_FILE="$OUTPUT_DIR/property_owning_companies_clean.csv"

# Create directories
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# Log function
log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/extraction_$(date +%Y%m%d).log"
}

log_msg "=== Starting Property Companies Extraction ==="

# Check if bq command exists
if ! command -v bq &> /dev/null; then
    log_msg "ERROR: bq command not found. Installing Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    source ~/.bashrc
fi

# Run BigQuery extraction
log_msg "Querying BigQuery for property-owning companies..."

bq query \
    --use_legacy_sql=false \
    --max_rows=800000 \
    --format=csv \
    'SELECT DISTINCT company_registration_no_1 
     FROM `inner-cinema-476211-u9.companies_house.land_registry_uk_companies` 
     WHERE company_registration_no_1 IS NOT NULL 
     AND LENGTH(company_registration_no_1) = 8 
     ORDER BY company_registration_no_1' \
    2>/dev/null | grep -E "^[0-9A-Z]{8}$" > "$OUTPUT_FILE"

# Check if extraction succeeded
if [ -f "$OUTPUT_FILE" ]; then
    COMPANY_COUNT=$(wc -l < "$OUTPUT_FILE")
    FILE_SIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
    FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)
    
    log_msg "✓ Extraction complete"
    log_msg "  Companies extracted: $COMPANY_COUNT"
    log_msg "  File size: $FILE_SIZE_MB MB"
    log_msg "  Output: $OUTPUT_FILE"
    
    # Show first 5 companies
    log_msg "Sample companies:"
    head -5 "$OUTPUT_FILE" | while read line; do
        log_msg "  - $line"
    done
    
    # Create web-accessible copy
    if [ -d "/var/www/html" ]; then
        cp "$OUTPUT_FILE" /var/www/html/property_companies.csv
        log_msg "✓ Web copy created: http://94.237.55.234/property_companies.csv"
    fi
    
else
    log_msg "ERROR: Extraction failed - output file not created"
    exit 1
fi

log_msg "=== Extraction Complete ==="
exit 0
