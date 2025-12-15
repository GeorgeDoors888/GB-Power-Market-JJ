#!/bin/bash
# GB Energy Dashboard - Map Integration Setup
# Quick installation script

echo "================================================"
echo "GB Energy Dashboard - Interactive Map Setup"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "inner-cinema-credentials.json" ]; then
    echo "❌ Error: inner-cinema-credentials.json not found"
    echo "Please run this script from the GB Power Market JJ directory"
    exit 1
fi

echo "✅ Credentials found"
echo ""

# Test Python dependencies
echo "🔍 Checking Python dependencies..."

python3 -c "import google.cloud.bigquery" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing: google-cloud-bigquery"
    echo "Installing..."
    pip3 install --user google-cloud-bigquery
fi

python3 -c "import gspread" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing: gspread"
    echo "Installing..."
    pip3 install --user gspread
fi

python3 -c "import pandas" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing: pandas"
    echo "Installing..."
    pip3 install --user pandas
fi

echo "✅ All Python dependencies installed"
echo ""

# Test BigQuery connection
echo "🔍 Testing BigQuery connection..."
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = 'SELECT 1 as test'
result = client.query(query).result()
print('✅ BigQuery connection successful')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ BigQuery connection failed"
    echo "Please check your credentials and project settings"
    exit 1
fi

# Test Google Sheets connection
echo "🔍 Testing Google Sheets connection..."
python3 -c "
import gspread
from google.oauth2.service_account import Credentials

scopes = ['https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=scopes)
gc = gspread.authorize(creds)
sh = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
print('✅ Google Sheets connection successful')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Google Sheets connection failed"
    echo "Please check your service account permissions"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ All tests passed!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Open Google Sheets dashboard:"
echo "   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
echo ""
echo "2. Go to: Extensions → Apps Script"
echo ""
echo "3. Create two files:"
echo "   - map_integration.gs (copy from local file)"
echo "   - dynamicMapView.html (copy from local file)"
echo ""
echo "4. Save and refresh spreadsheet"
echo ""
echo "5. Run initial data refresh:"
echo "   python3 refresh_map_data.py"
echo ""
echo "6. Open map from menu:"
echo "   🗺️ Map Tools → 🌍 Open Interactive Map"
echo ""
echo "================================================"
echo ""

# Offer to run initial data refresh
read -p "Would you like to run the initial data refresh now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 Running initial data refresh..."
    python3 refresh_map_data.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Data refresh complete!"
        echo ""
        echo "Now install the Apps Script code and open the map!"
    else
        echo ""
        echo "❌ Data refresh failed. Check the output above for errors."
    fi
fi

echo ""
echo "📚 For full documentation, see:"
echo "   ENERGY_DASHBOARD_MAPS_INTEGRATION.md"
echo ""
