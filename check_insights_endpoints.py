#!/usr/bin/env python3
"""
Check BMRS API endpoints for the missing data types
Based on the API documentation provided by the user
"""

import json

import requests

# Base URLs for different BMRS/Insights APIs
BMRS_BASE = "https://data.elexon.co.uk/bmrs/api/v1"
INSIGHTS_BASE = "https://data.elexon.co.uk/insights/api/v1"


def check_insights_endpoint(endpoint, description):
    """Check if an insights endpoint is available"""
    url = f"{INSIGHTS_BASE}/{endpoint}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return f"✅ {description} - Available at /insights/api/v1/{endpoint}"
        else:
            return f"❌ {description} - Not available ({response.status_code})"
    except Exception as e:
        return f"❌ {description} - Error: {str(e)[:50]}"


# Map the missing requirements to likely API endpoints
endpoints_to_check = [
    # Adjustment data
    (
        "balancing/adjustment/netbsad",
        "NETBSAD - Net Balancing Services Adjustment Data",
    ),
    (
        "balancing/adjustment/disbsad",
        "DISBSAD - Disaggregated Balancing Services Adjustment Data",
    ),
    # System prices
    ("balancing/pricing/system", "System Buy/Sell Prices"),
    ("balancing/pricing/market-index", "Market Index Prices"),
    # Demand forecasts
    ("forecast/demand/day-ahead", "Day-ahead Demand Forecast"),
    ("forecast/demand/week-ahead", "Week-ahead Demand Forecast"),
    ("demand/outturn", "Demand Outturn"),
    ("demand/outturn/daily", "Daily Demand Outturn"),
    # Generation forecasts
    ("forecast/generation/day-ahead", "Day-ahead Generation Forecast"),
    ("forecast/generation/wind-solar", "Wind & Solar Generation Forecast"),
    ("forecast/margin/daily", "Daily Margin Forecast"),
    ("forecast/surplus/daily", "Daily Surplus Forecast"),
    # STOR and reserves
    ("balancing/reserve/stor", "Short Term Operating Reserve (STOR)"),
    ("balancing/reserve/volumes", "Reserve Volumes"),
    # Restoration and peak data
    ("demand/peak/triad", "Triad Peak Demand"),
    ("demand/peak/indicative", "Indicative Peak Demand"),
    ("restoration/region/demand", "Restoration Region Demand"),
    # Other
    ("generation/actual/per-type", "Actual Generation by Type"),
    ("generation/actual/wind-solar", "Actual Wind & Solar Generation"),
]

print("🔍 Checking BMRS Insights API endpoints...")
print("=" * 80)

for endpoint, description in endpoints_to_check:
    result = check_insights_endpoint(endpoint, description)
    print(result)

print("\n" + "=" * 80)
print("✅ = Available, ❌ = Not available or different endpoint name")
print("Note: Some endpoints might require specific date ranges or parameters")
