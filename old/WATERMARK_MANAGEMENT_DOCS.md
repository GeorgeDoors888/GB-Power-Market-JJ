# Watermark File Management System

## Overview
This documentation explains the Watermark File Management System implemented for the jibber-jabber project. The system helps maintain disk space efficiency by keeping only the most recent watermark files while removing older ones that are no longer needed.

## What are Watermark Files?
Watermark files (named `watermarks_*.json`) track the latest data points or timestamps for various datasets in our BigQuery pipeline. These files are crucial for:

1. Tracking the most recent data loaded into each table
2. Enabling incremental data loading (only loading new data since the last watermark)
3. Monitoring data freshness and pipeline health

While these files are important for system operation, they accumulate over time and can consume unnecessary disk space.

## The Management Solution

### Script: `manage_watermarks.sh`
The script automatically manages watermark files by:

- Finding all `watermarks_*.json` files in the workspace
- Sorting them by modification time (newest first)
- Keeping the 5 most recent files
- Removing older files that are no longer needed
- Reporting on actions taken and space freed

### Default Configuration
- **Files Managed**: Any file matching `watermarks_*.json`
- **Retention Policy**: Keep the 5 most recent files
- **Search Location**: `/Users/georgemajor/jibber-jabber 24 august 2025 big bop`

## Usage

### Manual Execution
```bash
# Run the script directly
bash "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/manage_watermarks.sh"

# Or if made executable
chmod +x "/Users/georgemajor/jibber-jabber 24 august 2025 big bop/manage_watermarks.sh"
"/Users/georgemajor/jibber-jabber 24 august 2025 big bop/manage_watermarks.sh"
```

### Automated Execution
For automatic maintenance, add the script to your crontab:

```bash
# Run watermark file cleanup every day at 2:00 AM
0 2 * * * /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop/manage_watermarks.sh >> /Users/georgemajor/jibber-jabber\ 24\ august\ 2025\ big\ bop/watermarks_cleanup.log 2>&1
```

Add this to your crontab by running `crontab -e` and pasting the line above.

## Customization
You can modify the script to adjust:

1. The number of files to keep (`KEEP_COUNT`)
2. The file pattern to match (`FILE_PATTERN`)
3. The directory to search (`SEARCH_DIR`)

## Logs
The script outputs information about its operations, including:
- Number of files found
- List of files with their modification times
- Files that will be deleted
- Disk space freed
- Verification of remaining files

When run via cron, output will be written to `watermarks_cleanup.log`.

## Troubleshooting
If the script isn't working as expected:

1. Verify the script has execute permissions: `chmod +x manage_watermarks.sh`
2. Check that the search path is correct in the script
3. Ensure you have write permissions in the directory
4. Examine the log file for any error messages

## Integration with Data Pipeline
This script complements our data pipeline by ensuring that watermark tracking remains efficient without consuming unnecessary resources.
