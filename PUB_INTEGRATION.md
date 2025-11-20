# Pub Checker Integration Guide

## Quick Start (3 steps)

### 1. Enable pub endpoints

Edit `api_gateway.py` and uncomment these two lines (around line 1103):

```python
# ============================================
# PUB ENDPOINTS (OPTIONAL)
# ============================================
# Uncomment the following lines to enable pub checker feature:
from pub_endpoints import pub_router  # UNCOMMENT THIS
app.include_router(pub_router)        # UNCOMMENT THIS
```

### 2. Create your pubs CSV file

Copy the example file to your data directory:

```bash
# On your server
mkdir -p /home/shared/data/raw
cp example_pubs.csv /home/shared/data/raw/pubs.csv

# Edit to add your favorite pubs
nano /home/shared/data/raw/pubs.csv
```

Or start from scratch with the format:
```csv
name,area,rating,notes
The Crown,Islington,4.6,Good Sunday roast
```

### 3. Restart the API gateway

```bash
# If running manually
python3 api_gateway.py

# If running as a service
sudo systemctl restart ai-gateway
```

## Testing

### From command line:
```bash
# JSON endpoint
curl http://localhost:8000/pub/random

# With filters
curl "http://localhost:8000/pub/random?area=Covent&min_rating=4.5"

# History
curl http://localhost:8000/pub/history?limit=10
```

### From browser:
- Random pub: http://localhost:8000/pub/random/html
- History: http://localhost:8000/pub/history/html

### From iPhone via Tailscale:
- Replace `localhost` with your Tailscale IP (e.g., `100.x.x.x`)
- Bookmark on home screen for quick access

## Configuration Options

Edit paths in `pub_endpoints.py` if needed:

```python
# Configuration - adjust paths as needed
PUBS_CSV_PATH = Path("/home/shared/data/raw/pubs.csv")
PUB_HISTORY_FILE = Path("./logs/pubs_history.jsonl")
```

## Verify No Interference

After enabling, check:

```bash
# 1. Energy market endpoints still work
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/bigquery/prices?days=7

# 2. Pub endpoints work
curl http://localhost:8000/pub/random

# 3. Health check shows all services
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/health
```

## Troubleshooting

### "File not found: pubs.csv"
- Check file exists: `ls -la /home/shared/data/raw/pubs.csv`
- Check path in `pub_endpoints.py` matches your setup

### "ModuleNotFoundError: pub_endpoints"
- Ensure `pub_endpoints.py` is in same directory as `api_gateway.py`
- Check you uncommented the import lines

### No history appearing
- History file creates automatically on first pub request
- Check: `ls -la ./logs/pubs_history.jsonl`
- Permissions: `chmod 666 ./logs/pubs_history.jsonl`

## Security Notes

- Pub endpoints **do not require API key** (safe read-only feature)
- If you want to protect them, add `api_key: str = Depends(verify_api_key)` to each endpoint
- History log is local-only (not synced to BigQuery or Sheets)
- CSV file should not contain sensitive data

## Uninstalling

To remove pub feature:

1. Comment out the two lines in `api_gateway.py`:
```python
# from pub_endpoints import pub_router
# app.include_router(pub_router)
```

2. Optionally delete files:
```bash
rm pub_endpoints.py
rm docs/PUB_HISTORY.md
rm example_pubs.csv
rm logs/pubs_history.jsonl
```

---

**Created**: November 19, 2025  
**Part of**: GB Power Market JJ project
