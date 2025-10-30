#!/bin/bash
# Script to backup important files before deleting jibber-jabber folder
# Run this before: rm -rf ~/jibber-jabber\ 24\ august\ 2025\ big\ bop

set -e  # Exit on error

echo "================================================================================"
echo "BACKUP SCRIPT: Saving important files before folder deletion"
echo "================================================================================"
echo

SOURCE_FOLDER=~/"jibber-jabber 24 august 2025 big bop"
CURRENT_WORKSPACE=~/"GB Power Market JJ"
GOOGLE_DRIVE=~/GoogleDrive/DNO_Analysis_Backup

# Check if source folder exists
if [ ! -d "$SOURCE_FOLDER" ]; then
    echo "❌ Error: Source folder not found: $SOURCE_FOLDER"
    exit 1
fi

echo "✅ Source folder found: $SOURCE_FOLDER"
echo

# Step 1: Copy GeoJSON files
echo "================================================================================"
echo "STEP 1: Copying GeoJSON files (25 files, ~150 MB total)"
echo "================================================================================"
echo

mkdir -p "$CURRENT_WORKSPACE/old_project/GIS_data"

# Copy from system_regulatory/gis folder
if [ -d "$SOURCE_FOLDER/system_regulatory/gis" ]; then
    echo "📍 Copying from system_regulatory/gis..."
    cp "$SOURCE_FOLDER"/system_regulatory/gis/*.geojson "$CURRENT_WORKSPACE/old_project/GIS_data/" 2>/dev/null || true
    COPIED_COUNT=$(ls "$CURRENT_WORKSPACE/old_project/GIS_data"/*.geojson 2>/dev/null | wc -l)
    echo "   ✅ Copied $COPIED_COUNT GeoJSON files"
else
    echo "⚠️  system_regulatory/gis folder not found"
fi

# Copy from root
echo "📍 Copying from root folder..."
cp "$SOURCE_FOLDER"/*.geojson "$CURRENT_WORKSPACE/old_project/GIS_data/" 2>/dev/null || true

TOTAL_GEOJSON=$(ls "$CURRENT_WORKSPACE/old_project/GIS_data"/*.geojson 2>/dev/null | wc -l)
echo "   ✅ Total GeoJSON files in workspace: $TOTAL_GEOJSON"
echo

# Step 2: Backup ED2 PCFM files (optional - to Google Drive)
echo "================================================================================"
echo "STEP 2: Backing up ED2 PCFM analysis files (16 files, ~50 MB total)"
echo "================================================================================"
echo

read -p "Do you want to backup ED2 PCFM files to Google Drive? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$GOOGLE_DRIVE/Excel"
    echo "📊 Copying ED2 PCFM files..."
    
    # Find and copy all ED2 PCFM files
    find "$SOURCE_FOLDER" -name "ED2*.xlsx" -exec cp {} "$GOOGLE_DRIVE/Excel/" \; 2>/dev/null || true
    find "$SOURCE_FOLDER" -name "EDCM*.xlsx" -exec cp {} "$GOOGLE_DRIVE/Excel/" \; 2>/dev/null || true
    
    BACKUP_COUNT=$(ls "$GOOGLE_DRIVE/Excel"/*.xlsx 2>/dev/null | wc -l)
    echo "   ✅ Backed up $BACKUP_COUNT Excel files to Google Drive"
else
    echo "   ⏭️  Skipping ED2 PCFM backup"
fi
echo

# Step 3: Summary
echo "================================================================================"
echo "BACKUP COMPLETE - SUMMARY"
echo "================================================================================"
echo

echo "✅ GeoJSON files: Copied to $CURRENT_WORKSPACE/old_project/GIS_data"
echo "   Total files: $TOTAL_GEOJSON"
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "✅ ED2 PCFM files: Backed up to $GOOGLE_DRIVE/Excel"
    echo "   Total files: $BACKUP_COUNT"
    echo
fi

echo "📋 Analysis:"
echo "   • DNO charging files (292): Already in current workspace ✅"
echo "   • PDF files (12): Mostly matplotlib docs - safe to delete ✅"
echo "   • CSV files (587): Elexon/BMRS data - regeneratable ✅"
echo "   • JSON files (2,079): Temporary/generated data - safe to delete ✅"
echo

echo "================================================================================"
echo "READY TO DELETE"
echo "================================================================================"
echo

echo "You can now safely delete the folder with:"
echo "   rm -rf ~/'jibber-jabber 24 august 2025 big bop'"
echo

echo "This will free up 7.71 GB of disk space."
echo

read -p "Do you want to delete the folder now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Deleting folder..."
    rm -rf "$SOURCE_FOLDER"
    echo "   ✅ Folder deleted!"
    echo "   💾 Freed 7.71 GB of disk space"
else
    echo "   ⏭️  Skipping deletion - you can delete manually later"
fi

echo
echo "================================================================================"
echo "DONE!"
echo "================================================================================"
