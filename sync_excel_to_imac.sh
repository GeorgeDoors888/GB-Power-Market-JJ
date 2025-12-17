#!/bin/bash
# Auto-sync Excel dashboard to iMac
# Save this as ~/sync_excel_to_imac.sh on your iMac

DELL_HOST="george@100.119.237.107"
REMOTE_FILE="~/GB-Power-Market-JJ/GB_Power_Market_Dashboard_Enhanced.xlsx"
LOCAL_FILE="$HOME/Downloads/GB_Power_Market_Dashboard_Enhanced.xlsx"

echo "🔄 Syncing Excel dashboard from Dell server..."

# Download latest version
scp "$DELL_HOST:$REMOTE_FILE" "$LOCAL_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Updated: $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Optional: Auto-open in Excel
    # open -a "Microsoft Excel" "$LOCAL_FILE"
else
    echo "❌ Sync failed"
fi
