#!/usr/bin/env python3
"""
Historical Temperature/Humidity Data Sources for Wind Farms
Comprehensive guide to data acquisition options
"""

# ============================================================================
# OPTION 1: ERA5 CDS API (Copernicus) - FREE, RECOMMENDED
# ============================================================================

"""
ERA5 Climate Data Store (CDS) API
- Provider: Copernicus Climate Change Service (C3S)
- Cost: FREE (unlimited downloads)
- Coverage: 1940-present (3 days lag)
- Resolution: 0.25° (~31km), hourly
- Variables: 100+ including temp, humidity, precip, wind, pressure

SETUP STEPS:
1. Create account: https://cds.climate.copernicus.eu/user/register
2. Accept Terms & Conditions: https://cds.climate.copernicus.eu/cdsapp#!/terms/licence-to-use-copernicus-products
3. Get API key: https://cds.climate.copernicus.eu/user
4. Install client: pip install cdsapi
5. Create ~/.cdsapirc with your API key

PROS:
+ FREE (no cost, unlimited downloads)
+ Official ERA5 data (gold standard)
+ All variables available
+ Reliable, well-documented
+ Global coverage

CONS:
- Requires account setup (~5 minutes)
- 3-day lag for latest data
- Downloads can be slow (queuing system)
- API rate limits (reasonable)
"""

# Example: Download ERA5 historical weather for UK wind farms
def download_era5_via_cds():
    import cdsapi
    
    c = cdsapi.Client()
    
    # Wind farm coordinates
    farms = [
        {"name": "Hornsea Two", "lat": 53.9167, "lon": 1.7833},
        {"name": "Beatrice", "lat": 58.2000, "lon": -3.0833},
        # ... add all 41 farms
    ]
    
    for farm in farms:
        # Download 2020-2025 data
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': [
                    '2m_temperature',           # Surface temperature
                    '2m_dewpoint_temperature',  # For humidity calculation
                    'total_precipitation',      # Rainfall
                    'total_cloud_cover',        # Cloud coverage
                    '100m_u_component_of_wind', # Wind U component
                    '100m_v_component_of_wind', # Wind V component
                ],
                'year': ['2020', '2021', '2022', '2023', '2024', '2025'],
                'month': [f'{m:02d}' for m in range(1, 13)],
                'day': [f'{d:02d}' for d in range(1, 32)],
                'time': [f'{h:02d}:00' for h in range(0, 24)],
                'area': [  # Bounding box [North, West, South, East]
                    farm['lat'] + 0.5,  # North
                    farm['lon'] - 0.5,  # West
                    farm['lat'] - 0.5,  # South
                    farm['lon'] + 0.5,  # East
                ],
                'format': 'netcdf',
            },
            f'era5_{farm["name"].replace(" ", "_")}.nc'
        )

"""
Expected download time: 2-6 hours for all farms (queuing + download)
Total data size: ~5-10 GB for 41 farms × 6 years
"""


# ============================================================================
# OPTION 2: Open-Meteo Historical Weather API - PAID/RATE LIMITED
# ============================================================================

"""
Open-Meteo Historical Weather API
- Provider: Open-Meteo.com
- Cost: FREE tier (10k requests/day) OR €50-150/month (Commercial API)
- Coverage: 1940-present (1 day lag)
- Resolution: Point-based, hourly
- Variables: Temp, humidity, precip, wind, pressure, cloud cover

PROS:
+ Simple JSON API (no setup)
+ Exact coordinates (not grid)
+ Fast responses
+ Good documentation

CONS:
- FREE tier rate limited (experienced yesterday)
- Historical API severely throttled
- Commercial plan needed for bulk downloads
- Less reliable than ERA5

RATE LIMITS (Free):
- 10,000 API calls per day
- ~10 API calls per farm per year = 41 farms × 6 years × 10 = 2,460 calls
- Would take 1 day if no throttling
- BUT: Archive API has additional throttling (429 errors)

PAID PLANS:
- Starter: €50/month (100k calls/day)
- Professional: €150/month (1M calls/day, priority)
"""

def download_openmeteo_historical():
    import requests
    import time
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": 53.9167,
        "longitude": 1.7833,
        "start_date": "2020-01-01",
        "end_date": "2025-12-31",
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "wind_speed_100m",
            "wind_direction_100m"
        ],
        "timezone": "Europe/London"
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 429:
        print("Rate limited - need paid plan")
    else:
        data = response.json()
        # Process data...

"""
RECOMMENDATION: Only use if you pay for Commercial API (€150/month)
"""


# ============================================================================
# OPTION 3: Met Office DataPoint API - PAID, UK-SPECIFIC
# ============================================================================

"""
Met Office DataPoint API
- Provider: UK Met Office
- Cost: £1,000-2,000/year (commercial license)
- Coverage: UK only, 2010-present
- Resolution: Weather stations (~20-50km apart), 15min/hourly
- Variables: Full suite of Met Office observations

PROS:
+ UK-specific, high quality
+ Official UK weather data
+ Higher temporal resolution (15min)
+ Weather station network (closer to farms)
+ Direct support

CONS:
- PAID (£1-2k/year)
- Limited historical depth (2010+)
- Requires commercial license application
- UK only (not global)

CONTACT:
- Email: enquiries@metoffice.gov.uk
- Web: https://www.metoffice.gov.uk/services/data/datapoint
"""


# ============================================================================
# OPTION 4: NOAA ISD (Integrated Surface Database) - FREE
# ============================================================================

"""
NOAA Integrated Surface Database
- Provider: NOAA (US National Oceanic and Atmospheric Administration)
- Cost: FREE
- Coverage: 1901-present, global weather stations
- Resolution: Station-based, hourly
- Variables: Temp, humidity, wind, pressure, precip

UK WEATHER STATIONS:
- ~200 stations in UK
- Closest to offshore farms: coastal stations (10-50km away)
- Historical data available via FTP

PROS:
+ FREE
+ Very long historical record
+ Reliable, quality-controlled
+ Many UK coastal stations

CONS:
- Station-based (not grid/offshore)
- Nearest stations 10-50km from offshore farms
- Need to interpolate to farm locations
- Download process more complex (FTP)

ACCESS:
- Web: https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database
- FTP: ftp://ftp.ncdc.noaa.gov/pub/data/noaa/
"""

def find_uk_stations():
    """
    UK weather stations near offshore wind farms:
    
    Closest to North Sea farms (Hornsea, Dogger Bank):
    - Bridlington
    - Spurn Head
    - Donna Nook
    
    Closest to Scottish farms (Beatrice, Moray):
    - Wick Airport
    - Lossiemouth
    - Kinloss
    
    Closest to Irish Sea farms (Walney):
    - Blackpool
    - Ronaldsway (Isle of Man)
    
    Closest to English Channel farms (Rampion):
    - Shoreham
    - Portsmouth
    """


# ============================================================================
# OPTION 5: Use Existing GFS Forecasts (PARTIAL SOLUTION)
# ============================================================================

"""
What we already have in BigQuery:
- Table: uk_energy_prod.gfs_forecast_weather
- Rows: 6,888 (today's forecasts)
- Variables: temperature_2m, relative_humidity_2m, precipitation, etc.
- Coverage: Last ~4 hours, forward 7 days

LIMITATION:
- Only FUTURE forecasts (no historical data)
- Can detect icing risk going forward
- Cannot validate past icing events

USE CASE:
- Real-time icing alerts (forward-looking)
- 7-day icing risk forecasts
- Operational decision support
"""


# ============================================================================
# RECOMMENDATION: BEST APPROACH
# ============================================================================

"""
RECOMMENDED SOLUTION: ERA5 CDS API (Option 1)

WHY:
1. FREE (no cost)
2. Gold standard data quality
3. Complete historical coverage (2020-2025)
4. All variables needed (temp, humidity, precip, cloud)
5. Well-documented, reliable
6. One-time setup (~5 minutes)

IMPLEMENTATION PLAN:
1. Setup (5 minutes):
   - Create CDS account
   - Accept terms
   - Get API key
   - Install cdsapi

2. Download (2-6 hours):
   - Request all 41 farms × 6 years
   - Downloads run in background (queued)
   - ~5-10 GB total data

3. Upload to BigQuery (1 hour):
   - Parse NetCDF files
   - Upload to era5_weather_data table
   - 946k rows expected (41 farms × 6 years × 365 days × 24 hours / 2)

4. Use for icing validation:
   - Join with bmrs_pn (actual generation)
   - Identify periods of underperformance
   - Filter for icing conditions (temp, humidity, precip)
   - Validate simplified icing classifier

ALTERNATIVE (if urgent):
Pay for Open-Meteo Commercial API (€150/month)
- Faster setup (no account needed)
- Simpler JSON API
- Good for short-term use
- Cancel after data downloaded

COST COMPARISON:
- ERA5 CDS: £0 (FREE)
- Open-Meteo Commercial: £130/month (€150)
- Met Office DataPoint: £1,500/year

RECOMMENDATION: ERA5 CDS (FREE, high quality, complete)
"""


# ============================================================================
# QUICK START: ERA5 CDS SETUP
# ============================================================================

def setup_era5_cds():
    """
    1. Create account:
       https://cds.climate.copernicus.eu/user/register
    
    2. Accept T&Cs:
       https://cds.climate.copernicus.eu/cdsapp#!/terms/licence-to-use-copernicus-products
    
    3. Get API key:
       https://cds.climate.copernicus.eu/user
       (under "API key" section)
    
    4. Create ~/.cdsapirc file:
       
       url: https://cds.climate.copernicus.eu/api/v2
       key: YOUR_UID:YOUR_API_KEY
    
    5. Install client:
       pip3 install cdsapi
    
    6. Test:
       python3 -c "import cdsapi; c = cdsapi.Client(); print('✅ Setup complete')"
    
    7. Download data (script provided below)
    """
    print("See ERA5 CDS Setup Guide above")


if __name__ == "__main__":
    print("=" * 80)
    print("HISTORICAL TEMPERATURE/HUMIDITY DATA FOR WIND FARMS")
    print("=" * 80)
    print()
    print("RECOMMENDED: ERA5 CDS API (FREE)")
    print()
    print("See code above for:")
    print("  - 5 data source options")
    print("  - Pros/cons of each")
    print("  - Setup instructions")
    print("  - Download scripts")
    print()
    print("Next step: Choose Option 1 (ERA5 CDS) and follow setup guide")
    print("=" * 80)
