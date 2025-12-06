#!/bin/bash
# Quick deployment script for Apps Script changes

echo "🚀 Deploying Apps Script to Google Sheets..."
cd /home/george/GB-Power-Market-JJ/clasp-sheet-project

# Push code
clasp push

echo "✅ Deployed! Changes are live in your sheet."
echo "📊 Open sheet: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit"
