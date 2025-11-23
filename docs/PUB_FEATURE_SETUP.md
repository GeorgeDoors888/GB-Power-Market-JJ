# 🍺 Pub Feature - Complete Setup Guide

## Overview

The pub feature is a lightweight addition to your GB Power Market project that provides random pub recommendations via API and mobile-friendly HTML interface. It's completely isolated from your energy market systems.

---

## Quick Setup (60 seconds)

### 1. Enable the Feature

Edit `api_gateway.py` around line 1111-1112 and uncomment these lines:

```python
# BEFORE:
# from pub_endpoints import pub_router
# app.include_router(pub_router)

# AFTER:
from pub_endpoints import pub_router
app.include_router(pub_router)
```

### 2. Configure Paths

Edit `pub_endpoints.py` lines 12-18:

**For local Mac testing:**
```python
PUBS_CSV_PATH = Path("/tmp/pub_test/pubs.csv")
PUB_HISTORY_FILE = Path("/tmp/pub_test/pubs_history.jsonl")
```

**For production server:**
```python
PUBS_CSV_PATH = Path("/home/shared/data/raw/pubs.csv")
PUB_HISTORY_FILE = Path("./logs/pubs_history.jsonl")
```

### 3. Create CSV File

Use the provided `example_pubs.csv` or create your own:

```csv
name,area,rating,notes
The Crown,Islington,4.6,Good Sunday roast
The Anchor,Bankside,4.3,Riverside pub
The Harp,Covent Garden,4.7,Great cask ales
```

**On Mac (for testing):**
```bash
mkdir -p /tmp/pub_test
cp example_pubs.csv /tmp/pub_test/pubs.csv
```

**On server (for production):**
```bash
mkdir -p /home/shared/data/raw
scp example_pubs.csv root@94.237.55.15:/home/shared/data/raw/pubs.csv
```

### 4. Test Locally (Mac Only)

```bash
# Simple test server (no credentials needed)
python3 test_pub_locally.py

# In another terminal or browser:
curl http://localhost:8000/pub/random
open http://localhost:8000/pub/random/html
```

### 5. Deploy to Production

```bash
# Upload files
scp pub_endpoints.py root@94.237.55.15:/opt/arbitrage/
scp example_pubs.csv root@94.237.55.15:/home/shared/data/raw/pubs.csv

# SSH to server and restart
ssh root@94.237.55.15
cd /opt/arbitrage
# Edit pub_endpoints.py to use production paths
nano pub_endpoints.py  # Change PUBS_CSV_PATH and PUB_HISTORY_FILE
systemctl restart ai-gateway
```

---

## API Endpoints

### 1. `/pub/random` (JSON)
Get a random pub with optional filters.

**Request:**
```bash
# Basic
curl http://localhost:8000/pub/random

# Filter by area
curl "http://localhost:8000/pub/random?area=Soho"

# Filter by minimum rating
curl "http://localhost:8000/pub/random?min_rating=4.5"

# Both filters
curl "http://localhost:8000/pub/random?area=Covent&min_rating=4.6"
```

**Response:**
```json
{
  "pub": {
    "name": "The Harp",
    "area": "Covent Garden",
    "rating": 4.7,
    "notes": "Great cask ales"
  },
  "source_file": "/tmp/pub_test/pubs.csv",
  "filters_used": {
    "area": null,
    "min_rating": null
  }
}
```

### 2. `/pub/random/html` (Mobile Interface)
Mobile-friendly HTML interface with:
- Random pub display
- Filter controls (area, min rating)
- "Another pub" and "Totally random" buttons
- Link to history

**Access:**
```bash
# Mac
open http://localhost:8000/pub/random/html

# iPhone via Tailscale
http://<tailscale-ip>:8000/pub/random/html
```

### 3. `/pub/history` (JSON)
Get history of pub selections.

**Request:**
```bash
# Last 50 (default)
curl http://localhost:8000/pub/history

# Last 100
curl "http://localhost:8000/pub/history?limit=100"
```

**Response:**
```json
{
  "limit": 50,
  "count": 3,
  "entries": [
    {
      "time_utc": "2025-11-19T22:59:19.627323+00:00",
      "name": "The French House",
      "area": "Soho",
      "rating": 4.5,
      "notes": "Legendary Soho pub"
    }
  ],
  "history_file": "/tmp/pub_test/pubs_history.jsonl"
}
```

### 4. `/pub/history/html` (History Table)
Scrollable table showing recent pub selections.

---

## Files Structure

```
GB Power Market JJ/
├── api_gateway.py              # Main API (add 2 lines to enable)
├── pub_endpoints.py            # Pub feature implementation
├── test_pub_locally.py         # Local test server (Mac only)
├── example_pubs.csv            # Sample data
├── PUB_FEATURE_SETUP.md        # This file
├── docs/
│   └── PUB_HISTORY.md          # Full documentation
└── logs/
    └── pubs_history.jsonl      # Created automatically
```

---

## No Interference with Energy Systems

| Component | Pub Feature | Energy Market | Conflict? |
|-----------|-------------|---------------|-----------|
| **Endpoints** | `/pub/*` | `/bigquery/*`, `/workspace/*` | ✅ None |
| **Data** | `pubs.csv` (local) | BigQuery tables | ✅ Separate |
| **History** | `pubs_history.jsonl` | Audit logs | ✅ Different files |
| **Auth** | Optional | API key required | ✅ Independent |
| **Dependencies** | pandas (already have) | google-cloud-* | ✅ No new deps |

---

## Troubleshooting

### "File not found: pubs.csv"
```bash
# Check file exists
ls -la /tmp/pub_test/pubs.csv  # Mac
ls -la /home/shared/data/raw/pubs.csv  # Server

# Create if missing
cp example_pubs.csv /tmp/pub_test/pubs.csv
```

### "ModuleNotFoundError: pub_endpoints"
```bash
# Ensure pub_endpoints.py is in same directory as api_gateway.py
ls -la pub_endpoints.py

# Check you uncommented the import lines in api_gateway.py
grep "pub_router" api_gateway.py
```

### "No module named 'fastapi'" (Mac only)
```bash
# Install FastAPI (already done if you followed setup)
pip3 install --user --break-system-packages fastapi 'uvicorn[standard]'

# Add to PATH if needed
echo 'export PATH="$HOME/Library/Python/3.14/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Server won't start
```bash
# Check for syntax errors
python3 -c "import ast; ast.parse(open('api_gateway.py').read())"

# Check port 8000 is free
lsof -ti:8000
# If in use, kill it: kill $(lsof -ti:8000)
```

---

## To Disable

1. Re-comment the lines in `api_gateway.py`:
```python
# from pub_endpoints import pub_router
# app.include_router(pub_router)
```

2. Restart server:
```bash
python3 api_gateway.py  # Mac
sudo systemctl restart ai-gateway  # Server
```

---

## Next Steps (Optional Enhancements)

- **Add more fields**: `postcode`, `website`, `phone`, `coordinates`
- **Google Maps links**: Add lat/long, generate maps URLs
- **Photos**: Add `image_url` field
- **Favorites**: Track liked pubs separately
- **Visit dates**: Mark pubs as visited with timestamps
- **API integration**: Import from Google Places/Yelp

---

**Status**: ✅ Ready to deploy  
**Risk**: ✅ Zero impact on energy systems  
**Setup time**: ⚡ 2 minutes  
**Created**: November 19, 2025
