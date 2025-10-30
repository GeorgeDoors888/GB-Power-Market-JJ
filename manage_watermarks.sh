#!/bin/bash
# manage_watermarks.sh
# Script to maintain only the most recent 5 watermarks JSON files
# Created: September 21, 2025

# Set the directory to search
SEARCH_DIR="/Users/georgemajor/jibber-jabber 24 august 2025 big bop"

# Set the file pattern to match
FILE_PATTERN="watermarks_*.json"

# Set the number of recent files to keep
KEEP_COUNT=5

# Print header
echo "===== Watermarks File Management ====="
echo "Running on: $(date)"
echo "Keeping the $KEEP_COUNT most recent '$FILE_PATTERN' files"
echo "Searching in: $SEARCH_DIR"
echo ""

# Count total matching files before cleanup
TOTAL_FILES=$(find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f | wc -l)
echo "Found $TOTAL_FILES matching files"

echo "Current watermark files (from newest to oldest):"
find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f -print0 | \
    xargs -0 ls -lt | head -n "$TOTAL_FILES" | awk '{print $6, $7, $8, $9}'
echo ""

if [ "$TOTAL_FILES" -le "$KEEP_COUNT" ]; then
    echo "No cleanup needed - we have $TOTAL_FILES files which is not more than the $KEEP_COUNT we want to keep."
    exit 0
fi

# List files that will be deleted (for confirmation)
echo "The following files will be deleted:"
find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f -print0 | \
    xargs -0 ls -lt | tail -n +$((KEEP_COUNT+1)) | awk '{print $9}'

# Calculate disk space to be freed
SPACE_FREED=$(find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f -print0 | \
    xargs -0 ls -lt | tail -n +$((KEEP_COUNT+1)) | \
    xargs du -ch | grep total$ | cut -f1)

echo "This will free approximately $SPACE_FREED of disk space"
echo ""

# Perform the deletion
echo "Deleting old files..."
find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f -print0 | \
    xargs -0 ls -t | tail -n +$((KEEP_COUNT+1)) | xargs rm -f

# Count remaining files as verification
REMAINING_FILES=$(find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f | wc -l)
echo "Cleanup complete. $REMAINING_FILES watermark files remain."
echo ""
echo "===== Schedule Recommendation ====="
echo "To run this script automatically, add it to your crontab with:"
echo "# Run watermark file cleanup every day at 2:00 AM"
echo "0 2 * * * $(pwd)/manage_watermarks.sh >> $(pwd)/watermarks_cleanup.log 2>&1"
echo ""
echo "To edit your crontab, run: crontab -e"
echo "Cleanup complete. $REMAINING_FILES files remain."

# List remaining files
echo "Remaining files:"
find "$SEARCH_DIR" -name "$FILE_PATTERN" -type f -print0 | \
    xargs -0 ls -lt | awk '{print $9 " - " $6 " " $7 " " $8}'

echo "===== Script Complete ====="
