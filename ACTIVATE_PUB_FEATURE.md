# 🍺 Pub Feature - One-Minute Activation

## Step 1: Edit api_gateway.py

Find lines 1111-1112 (near the end of the file):

### BEFORE (commented out):
```python
# ============================================
# PUB ENDPOINTS (OPTIONAL)
# ============================================
# Uncomment the following lines to enable pub checker feature:
# from pub_endpoints import pub_router
# app.include_router(pub_router)
```

### AFTER (uncommented):
```python
# ============================================
# PUB ENDPOINTS (OPTIONAL)
# ============================================
# Uncomment the following lines to enable pub checker feature:
from pub_endpoints import pub_router
app.include_router(pub_router)
```

**Just remove the `#` from the last two lines!**

## Step 2: Create pubs CSV

```bash
# On your server (adjust path as needed)
mkdir -p /home/shared/data/raw
cp example_pubs.csv /home/shared/data/raw/pubs.csv
```

Or create manually:
```bash
cat > /home/shared/data/raw/pubs.csv << 'EOF'
name,area,rating,notes
The Crown,Islington,4.6,Good Sunday roast
The Anchor,Bankside,4.3,Riverside views
The Harp,Covent Garden,4.7,Great ales
EOF
```

## Step 3: Restart API

```bash
# If running manually
python3 api_gateway.py

# If running as systemd service
sudo systemctl restart ai-gateway

# If running in screen/tmux
# Kill old process, restart
```

## Step 4: Test!

### From command line:
```bash
curl http://localhost:8000/pub/random
```

Expected output:
```json
{
  "pub": {
    "name": "The Harp",
    "area": "Covent Garden",
    "rating": 4.7,
    "notes": "Great ales"
  },
  "source_file": "/home/shared/data/raw/pubs.csv",
  "filters_used": {
    "area": null,
    "min_rating": null
  }
}
```

### From browser:
- **Random pub**: http://localhost:8000/pub/random/html
- **History**: http://localhost:8000/pub/history/html

### From iPhone (via Tailscale):
- Replace `localhost` with your Tailscale IP
- Bookmark on home screen for instant access

## Verify No Conflicts

Energy market endpoints still working?
```bash
# Test BigQuery access (requires API key)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/bigquery/prices?days=7

# Test Sheets access (requires API key)
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://localhost:8000/workspace/dashboard
```

Both should work unchanged!

## To Disable Later

Just add `#` back to those two lines:
```python
# from pub_endpoints import pub_router
# app.include_router(pub_router)
```

Restart, done. Zero permanent changes to your system.

---

**Time required**: 60 seconds  
**Risk level**: Zero (completely isolated feature)  
**Dependencies**: None (pandas already installed)
