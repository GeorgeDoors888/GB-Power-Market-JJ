#!/bin/bash

# Configuration
TARGET_DIR="/home/george/GB-Power-Market-JJ/clasp-gb-live-2"
EXPECTED_SCRIPT_ID="1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GB Live Dashboard v2 Deployment ===${NC}"

# 1. Check Directory
if [ ! -d "$TARGET_DIR" ]; then
    echo -e "${RED}Error: Directory $TARGET_DIR not found!${NC}"
    exit 1
fi

cd "$TARGET_DIR" || exit

# 2. Verify Script ID
if [ ! -f ".clasp.json" ]; then
    echo -e "${RED}Error: .clasp.json not found in $TARGET_DIR${NC}"
    exit 1
fi

CURRENT_ID=$(grep "scriptId" .clasp.json | cut -d'"' -f4)

if [ "$CURRENT_ID" != "$EXPECTED_SCRIPT_ID" ]; then
    echo -e "${RED}CRITICAL ERROR: Script ID Mismatch!${NC}"
    echo "Expected: $EXPECTED_SCRIPT_ID"
    echo "Found:    $CURRENT_ID"
    echo "Please fix .clasp.json before deploying."
    exit 1
fi

echo "✅ Script ID verified: $CURRENT_ID"

# 3. Push
echo "🚀 Pushing code..."
clasp push

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployment Successful!${NC}"
    echo "Timestamp: $(date)"
else
    echo -e "${RED}❌ Deployment Failed!${NC}"
    exit 1
fi
