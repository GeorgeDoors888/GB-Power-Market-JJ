# Using documents_clean Table - Implementation Complete

## ✅ Changes Made

### Updated Files:
1. **`drive-bq-indexer/scripts/export_to_sheets.py`**
   - Changed query from `documents` to `documents_clean`
   - Line 92: Now queries the deduplicated table

2. **`drive-bq-indexer/scripts/export_to_csv.py`**
   - Changed query from `documents` to `documents_clean`
   - Line 49: Now queries the deduplicated table

### Already Using documents_clean:
- ✅ `drive-bq-indexer/src/cli.py` (extract command) - Line 109
- ✅ `drive-bq-indexer/src/cli_parallel.py` - Line 68
- ✅ `verify_architecture.py` - Line 24
- ✅ `check_file_sizes.py` - Lines 25, 60

## 📊 Table Status

### documents_clean (NEW - ACTIVE)
- **Rows:** 153,201 unique files
- **Purpose:** Deduplicated data for production queries
- **Updates:** Will be refreshed periodically from `documents` table

### documents (ORIGINAL - KEPT FOR INDEXING)
- **Rows:** 306,413 (includes duplicates)
- **Purpose:** Raw indexing target, receives all new indexed files
- **Updates:** Continues to receive new data from the indexer

## 🔄 Workflow

```
Google Drive Files
        ↓
[Indexer writes to]
        ↓
   documents (raw table with potential duplicates)
        ↓
[Periodic deduplication]
        ↓
   documents_clean (deduplicated table)
        ↓
[All queries read from]
        ↓
   Applications & Exports
```

## 📝 File Breakdown (Clean Data)
- PDFs: 139,035 (90.7%)
- Excel: 6,871 (4.5%)
- Google Sheets: 5,761 (3.8%)
- Word: 1,365 (0.9%)
- Google Docs: 135 (0.1%)
- PowerPoint: 34 (<0.1%)

## 🚀 Deployment

To deploy these changes to your remote server:

```bash
# Copy updated files to remote server
cd /Users/georgemajor/Overarch\ Jibber\ Jabber
scp -r drive-bq-indexer/scripts root@94.237.55.15:/tmp/

# Update the Docker container
ssh root@94.237.55.15 'docker cp /tmp/scripts/export_to_sheets.py driveindexer:/app/scripts/ && docker cp /tmp/scripts/export_to_csv.py driveindexer:/app/scripts/'

# Restart the container (if needed)
ssh root@94.237.55.15 'docker restart driveindexer'
```

## 🔍 Verification Queries

Check the clean table:
```sql
SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`
```

Compare with raw table:
```sql
SELECT 
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents`) as raw,
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`) as clean
```

## 🔄 Maintenance

To refresh the deduplicated table periodically:
```bash
# Run on remote server
ssh root@94.237.55.15 'docker exec driveindexer bash -c "cd /app && python /tmp/deduplicate_fixed.py"'
```

Or set up a cron job for automatic deduplication.

## ✅ Status
- [x] Deduplication completed (153,212 duplicates removed)
- [x] documents_clean table created
- [x] Export scripts updated to use documents_clean
- [x] Extract/processing scripts already using documents_clean
- [ ] Deploy changes to remote server
- [ ] Set up periodic deduplication (optional)
