# Pub Endpoints & History

This project includes a small "pub checker" feature backed by a CSV file and a JSONL history log.

## 🍺 Purpose

Separate from the GB Power Market analysis, this provides a fun way to:
- Get random pub suggestions
- Filter by area/rating
- Track pub visit history
- Access via mobile-friendly HTML interface

## Files

### Pubs CSV (input data)
- **Path**: `/home/shared/data/raw/pubs.csv`
- **Configurable via**: `PUBS_CSV_PATH` in `pub_endpoints.py`

**Example CSV:**
```csv
name,area,rating,notes
The Crown,Islington,4.6,Good Sunday roast
The Anchor,Bankside,4.3,Riverside pub
The Harp,Covent Garden,4.7,Great cask ales
```

### History log (output)
- **Path**: `./logs/pubs_history.jsonl`
- **Configurable via**: `PUB_HISTORY_FILE` in `pub_endpoints.py`

Each line is a JSON object:
```json
{"time_utc": "2025-11-19T21:01:23.456789+00:00", "name": "The Harp", "area": "Covent Garden", "rating": 4.7, "notes": "Great cask ales"}
```

## Integration with api_gateway.py

Add to your `api_gateway.py`:

```python
# Near the top with other imports
from pub_endpoints import pub_router

# After app initialization
app.include_router(pub_router)
```

That's it! No config changes needed in `.env.ai-gateway`.

## Endpoints

### 1. Random pub (JSON)

```bash
GET /pub/random?area=Islington&min_rating=4.5
```

**Query parameters:**
- `area` (optional) – filter by area/neighbourhood (substring match, case-insensitive)
- `min_rating` (optional) – minimum rating (numeric)

**Response:**
```json
{
  "pub": {
    "name": "The Crown",
    "area": "Islington",
    "rating": 4.6,
    "notes": "Good Sunday roast"
  },
  "source_file": "/home/shared/data/raw/pubs.csv",
  "filters_used": {
    "area": "Islington",
    "min_rating": 4.5
  }
}
```

Every successful call appends a line to the history file.

### 2. Random pub (HTML)

```bash
GET /pub/random/html
```

Mobile-friendly HTML front-end showing:
- Name, area, rating, notes
- Controls:
  - New random pub (with optional filters)
  - Totally random pub
  - Link to Pub history

### 3. Pub history (JSON)

```bash
GET /pub/history?limit=50
```

**Query parameters:**
- `limit` – number of entries to return (default 50, max 500)

**Response:**
```json
{
  "limit": 50,
  "count": 10,
  "entries": [
    {
      "time_utc": "2025-11-19T21:01:23.456789+00:00",
      "name": "The Harp",
      "area": "Covent Garden",
      "rating": 4.7,
      "notes": "Great cask ales"
    }
    // newest first...
  ],
  "history_file": "./logs/pubs_history.jsonl"
}
```

### 4. Pub history (HTML)

```bash
GET /pub/history/html
```

Shows a table of recent pubs (default last 50, newest first).

**Controls:**
- Change limit and reload
- Refresh
- Jump to New pub
- Jump to API Home

## Typical Usage

### On the server (if running locally):
```bash
python3 api_gateway.py
# Server runs on http://0.0.0.0:8000
```

### From your Mac or iPhone (via Tailscale):
- API health: `http://<server-ip>:8000/`
- Pub checker: `http://<server-ip>:8000/pub/random/html`
- Pub history: `http://<server-ip>:8000/pub/history/html`

## No Interference with Energy Market Systems

This feature is **completely isolated**:
- ✅ Different endpoint namespace (`/pub/*` vs `/bigquery/*`, `/workspace/*`)
- ✅ Separate data source (`pubs.csv` vs BigQuery tables)
- ✅ Independent history log (`pubs_history.jsonl` vs audit logs)
- ✅ No shared authentication (uses same API key but different endpoints)
- ✅ No rate limit conflicts (uses same limiter instance)

## Example pubs.csv

Create this file to get started:

```csv
name,area,rating,notes
The Churchill Arms,Kensington,4.8,Amazing flower-covered pub
The Anchor,Bankside,4.3,Riverside pub with Thames views
The Harp,Covent Garden,4.7,Great cask ales
Ye Olde Cheshire Cheese,Fleet Street,4.5,Historic pub dating to 1667
The Spaniards Inn,Hampstead Heath,4.6,Classic 16th century pub
The Mayflower,Rotherhithe,4.4,Historic pub with river terrace
The Holly Bush,Hampstead,4.7,Traditional Victorian pub
The French House,Soho,4.5,Legendary Soho pub
The Dove,Hammersmith,4.6,Thames-side pub with great beer
The Lamb,Bloomsbury,4.5,Victorian pub with snob screens
```

---

**Last Updated**: November 19, 2025  
**Part of**: GB Power Market JJ project
