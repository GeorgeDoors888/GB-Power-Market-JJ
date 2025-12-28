#!/bin/bash
# Fix ALL spreadsheet IDs to use CORRECT GB Live 2 spreadsheet
# CORRECT:  1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
# WRONG:    1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

WRONG_ID="1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
CORRECT_ID="1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

echo "🔧 FIXING ALL SPREADSHEET IDs"
echo "================================"
echo "WRONG (deprecated):  $WRONG_ID"
echo "CORRECT (GB Live 2): $CORRECT_ID"
echo ""

# Find all Python files with wrong ID
FILES=$(grep -l "$WRONG_ID" *.py 2>/dev/null)

if [ -z "$FILES" ]; then
    echo "✅ No Python files found with wrong ID!"
else
    echo "📝 Found $(echo "$FILES" | wc -l) Python files to fix"
    echo ""
    
    for file in $FILES; do
        echo "  Fixing: $file"
        sed -i "s/$WRONG_ID/$CORRECT_ID/g" "$file"
    done
    
    echo ""
    echo "✅ Fixed all Python files!"
fi

echo ""
echo "🔍 Verifying..."
REMAINING=$(grep -l "$WRONG_ID" *.py 2>/dev/null | wc -l)

if [ "$REMAINING" -eq 0 ]; then
    echo "✅ SUCCESS! All Python files now use correct spreadsheet ID"
else
    echo "⚠️  WARNING: $REMAINING files still have wrong ID"
    grep -l "$WRONG_ID" *.py 2>/dev/null
fi

echo ""
echo "🔗 Correct spreadsheet: https://docs.google.com/spreadsheets/d/$CORRECT_ID/edit"
