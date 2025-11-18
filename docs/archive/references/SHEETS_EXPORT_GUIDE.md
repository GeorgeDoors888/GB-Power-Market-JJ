# 📊 Google Drive Metadata Export to Sheets

## Overview

Export all Google Drive file metadata from BigQuery to Google Sheets, automatically handling Google Sheets size limits by creating multiple spreadsheets if needed.

---

## Features

✅ **Comprehensive Metadata** - Exports 18 columns per file:
- File ID
- File Name
- MIME Type
- Size (bytes and MB)
- Created Date
- Modified Date
- Owner(s)
- Last Modified By
- Web View Link
- Parent Folders
- Shared status
- Trashed status
- Starred status
- Viewed By Me status
- Description
- Folder Color
- Indexed At timestamp

✅ **Google Sheets Limits Handled**
- Max 1,000,000 rows per sheet (leaves safety margin)
- Automatically creates multiple sheets for large datasets
- Batched writing for performance

✅ **Professional Formatting**
- Headers with dark background and white text
- Frozen header row
- Auto-resized columns
- Clean, readable layout

---

## Prerequisites

### 1. Service Account Permissions

Your service account needs these Google Cloud roles:
- **BigQuery Data Viewer** - Read Drive metadata
- **BigQuery Job User** - Execute queries

Your service account also needs **Google Sheets API** and **Google Drive API** enabled.

### 2. Enable APIs (if not already done)

```bash
# On your local machine
gcloud services enable sheets.googleapis.com --project=jibber-jabber-knowledge
gcloud services enable drive.googleapis.com --project=jibber-jabber-knowledge
```

---

## Installation

### Option 1: Update Existing Deployment (Recommended)

Run the update script to add Google Sheets support to your UpCloud deployment:

```bash
./update-deployment-sheets.sh
```

This will:
1. Copy the export script to the server
2. Rebuild the Docker image with Sheets libraries
3. Restart the container
4. Verify the installation

### Option 2: Manual Installation on Server

```bash
# SSH into server
ssh root@94.237.55.15

# Install dependencies
docker exec driveindexer pip install gspread gspread-formatting

# Verify installation
docker exec driveindexer python -c "import gspread; print('✅ Sheets libraries installed')"
```

---

## Usage

### Run the Export

```bash
# From your local machine
ssh root@94.237.55.15 'docker exec driveindexer python scripts/export_to_sheets.py'
```

The script will:
1. Query BigQuery for all Drive file metadata
2. Calculate total cells needed
3. Split into multiple sheets if needed (every 1M rows)
4. Create Google Sheet(s) with formatted data
5. Print the URL(s) to access the sheets

### Example Output

```
==============================================================
Drive Metadata to Google Sheets Exporter
==============================================================
Project: jibber-jabber-knowledge
Dataset: uk_energy_insights

2025-11-03 00:20:15 - INFO - Querying BigQuery for Drive metadata...
2025-11-03 00:20:18 - INFO - Retrieved 2,543 files from BigQuery
2025-11-03 00:20:18 - INFO - Total cells: 45,774
2025-11-03 00:20:18 - INFO - Split data into 1 chunks
2025-11-03 00:20:18 - INFO - Creating sheet: Drive Metadata Export - 2025-11-03
2025-11-03 00:20:19 - INFO - Writing 2,544 rows to sheet...
2025-11-03 00:20:25 - INFO - Wrote rows 1 to 1000
2025-11-03 00:20:31 - INFO - Wrote rows 1001 to 2000
2025-11-03 00:20:36 - INFO - Wrote rows 2001 to 2544
2025-11-03 00:20:37 - INFO - Applied formatting to sheet

==============================================================
✅ Export Complete!
==============================================================
Created 1 Google Sheet(s):
  1. https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit
```

---

## Large Dataset Handling

### Automatic Chunking

If you have more than 1,000,000 files, the script automatically creates multiple sheets:

**Example with 2.5M files:**
- Part 1: 1,000,000 rows
- Part 2: 1,000,000 rows
- Part 3: 500,000 rows

Each sheet will have:
```
Drive Metadata Export - 2025-11-03 - Part 1
Drive Metadata Export - 2025-11-03 - Part 2
Drive Metadata Export - 2025-11-03 - Part 3
```

### Google Sheets Limits

| Limit | Value | Our Safety Margin |
|-------|-------|-------------------|
| Max cells per sheet | 10,000,000 | 5,000,000 |
| Max rows | ~5,000,000 | 1,000,000 |
| Max columns | 18,278 | 18 |

---

## Data Schema

### Columns Exported

| Column # | Name | Description | Example |
|----------|------|-------------|---------|
| 1 | File ID | Unique Drive file identifier | `1ABC...XYZ` |
| 2 | File Name | Name of the file | `Q4 Report.pdf` |
| 3 | MIME Type | File type | `application/pdf` |
| 4 | Size (bytes) | Raw file size | `1048576` |
| 5 | Size (MB) | Human-readable size | `1.00` |
| 6 | Created Date | When file was created | `2025-01-15 14:30:22` |
| 7 | Modified Date | Last modification time | `2025-10-30 09:15:00` |
| 8 | Owner(s) | File owners | `user@example.com` |
| 9 | Last Modified By | Last person to edit | `editor@example.com` |
| 10 | Web View Link | Direct link to file | `https://drive.google.com/...` |
| 11 | Parent Folders | Parent folder IDs | `folder1, folder2` |
| 12 | Shared | Is file shared? | `Yes` / `No` |
| 13 | Trashed | Is file in trash? | `Yes` / `No` |
| 14 | Starred | Is file starred? | `Yes` / `No` |
| 15 | Viewed By Me | Have I viewed it? | `Yes` / `No` |
| 16 | Description | File description | `Important report` |
| 17 | Folder Color | Folder color code | `#FF0000` |
| 18 | Indexed At | When indexed | `2025-11-02 23:45:12` |

---

## Customization

### Filter by Date

Edit `scripts/export_to_sheets.py` to add date filters:

```python
query = f"""
SELECT * FROM `{project_id}.{dataset}.drive_files`
WHERE modified_time >= '2025-01-01'  -- Only files modified this year
ORDER BY modified_time DESC
"""
```

### Filter by MIME Type

Export only PDFs:

```python
query = f"""
SELECT * FROM `{project_id}.{dataset}.drive_files`
WHERE mime_type = 'application/pdf'
ORDER BY modified_time DESC
"""
```

### Custom Sheet Title

```bash
# Edit script to change base_title
base_title = "My Custom Export Name"
```

---

## Sharing & Permissions

### Make Sheet Public

Edit `scripts/export_to_sheets.py` and uncomment:

```python
# Share with anyone who has the link
spreadsheet.share('', perm_type='anyone', role='reader', with_link=True)
```

### Share with Specific Users

```python
# Share with specific email
spreadsheet.share('colleague@example.com', perm_type='user', role='writer')
```

### Share with Domain

```python
# Share with everyone in your organization
spreadsheet.share('', perm_type='domain', role='reader', with_link=True)
```

---

## Monitoring & Troubleshooting

### Check if Script Exists

```bash
ssh root@94.237.55.15 'docker exec driveindexer ls -la scripts/export_to_sheets.py'
```

### Test Import

```bash
ssh root@94.237.55.15 'docker exec driveindexer python -c "import gspread; print(\"✅ OK\")"'
```

### View Logs

```bash
ssh root@94.237.55.15 'docker logs driveindexer --tail 100 | grep -i sheets'
```

### Common Errors

**Error: No module named 'gspread'**
```bash
# Install dependencies
ssh root@94.237.55.15 'docker exec driveindexer pip install gspread gspread-formatting'
```

**Error: Insufficient permissions**
- Enable Sheets API and Drive API in Google Cloud Console
- Make sure service account has necessary BigQuery roles

**Error: Quota exceeded**
- Google Sheets API has rate limits
- Add delays between requests if exporting very large datasets
- Consider running during off-peak hours

---

## Performance

### Expected Export Times

| Files | Rows | Time Estimate |
|-------|------|---------------|
| 1,000 | 1,001 | ~30 seconds |
| 10,000 | 10,001 | ~5 minutes |
| 100,000 | 100,001 | ~45 minutes |
| 1,000,000 | 1,000,001 | ~7 hours |

### Optimization Tips

1. **Filter First** - Export only what you need
2. **Run During Off-Peak** - Avoid API rate limits
3. **Batch Size** - Current setting: 1,000 rows per batch
4. **Use Multiple Exports** - Split by date/type for parallel processing

---

## Integration with Existing Workflow

### After Indexing

```bash
# Full pipeline including export
ssh root@94.237.55.15 << 'EOF'
docker exec driveindexer python -m src.cli index-drive
docker exec driveindexer python -m src.cli extract
docker exec driveindexer python -m src.cli build-embeddings
docker exec driveindexer python scripts/export_to_sheets.py
EOF
```

### Scheduled Export (Cron)

```bash
# Add to server crontab for daily export at 2 AM
0 2 * * * docker exec driveindexer python scripts/export_to_sheets.py >> /var/log/sheets-export.log 2>&1
```

---

## Quick Reference

```bash
# Update deployment with Sheets support
./update-deployment-sheets.sh

# Run export
ssh root@94.237.55.15 'docker exec driveindexer python scripts/export_to_sheets.py'

# Check installation
ssh root@94.237.55.15 'docker exec driveindexer pip list | grep gspread'

# View export logs
ssh root@94.237.55.15 'docker logs driveindexer --tail 100'
```

---

## Files Created

- `scripts/export_to_sheets.py` - Main export script
- `requirements-sheets.txt` - Additional dependencies
- `update-deployment-sheets.sh` - Deployment update script
- `SHEETS_EXPORT_GUIDE.md` - This guide

---

**Ready to export your Drive metadata to Google Sheets! 📊**
