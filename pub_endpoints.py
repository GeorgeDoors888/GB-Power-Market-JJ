"""
Pub Checker Endpoints
Add these to api_gateway.py to avoid interfering with energy market operations
Completely separate data source (pubs.csv) and history log
"""

from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
import pandas as pd

# Configuration - adjust paths as needed
# For local testing on Mac:
PUBS_CSV_PATH = Path("/tmp/pub_test/pubs.csv")
PUB_HISTORY_FILE = Path("/tmp/pub_test/pubs_history.jsonl")

# For production on server, use:
# PUBS_CSV_PATH = Path("/home/shared/data/raw/pubs.csv")
# PUB_HISTORY_FILE = Path("./logs/pubs_history.jsonl")

# Create router for pub endpoints
pub_router = APIRouter()


def _append_pub_history(entry: dict) -> None:
    """
    Append a single pub entry (dict) to the history file as JSONL.
    Fails silently if something goes wrong so it never breaks the endpoint.
    """
    try:
        PUB_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PUB_HISTORY_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # Logging errors should not break the API
        pass


def _read_pub_history(limit: int = 50) -> List[dict]:
    """
    Read the last N entries from the pub history file.
    Returns newest entries first.
    """
    if not PUB_HISTORY_FILE.exists():
        return []

    try:
        with PUB_HISTORY_FILE.open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return []
        # Last N lines
        selected = lines[-limit:]
        entries = []
        for line in selected:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        # Newest first
        entries.reverse()
        return entries
    except Exception:
        return []


@pub_router.get("/pub/random")
def random_pub(
    area: Optional[str] = Query(default=None, description="Filter by area/neighbourhood"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating"),
):
    """
    Return a random pub from pubs.csv.
    CSV expected columns: name, area, rating, notes
    """
    if not PUBS_CSV_PATH.exists():
        return {
            "error": f"File not found: {PUBS_CSV_PATH}",
            "hint": "Create pubs.csv in /home/shared/data/raw with columns: name,area,rating,notes",
        }

    df = pd.read_csv(PUBS_CSV_PATH)

    # Basic expected columns
    required_cols: List[str] = ["name"]
    for col in required_cols:
        if col not in df.columns:
            return {
                "error": f"Missing required column '{col}' in {PUBS_CSV_PATH}",
                "columns_found": list(df.columns),
            }

    # Optional filters: area, rating
    if area and "area" in df.columns:
        df = df[df["area"].astype(str).str.contains(area, case=False, na=False)]

    if min_rating is not None and "rating" in df.columns:
        df["rating_numeric"] = pd.to_numeric(df["rating"], errors="coerce")
        df = df[df["rating_numeric"] >= float(min_rating)]

    if df.empty:
        return {
            "error": "No pubs match the given filters.",
            "filters": {
                "area": area,
                "min_rating": min_rating,
            },
        }

    # Pick a random row
    row = df.sample(1).iloc[0]

    result = {
        "name": row.get("name"),
        "area": row.get("area") if "area" in df.columns else None,
        "rating": float(row.get("rating")) if "rating" in df.columns else None,
        "notes": row.get("notes") if "notes" in df.columns else None,
    }

    # Log this pub selection into history
    history_entry = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "name": result["name"],
        "area": result["area"],
        "rating": result["rating"],
        "notes": result["notes"],
    }
    _append_pub_history(history_entry)

    return {
        "pub": result,
        "source_file": str(PUBS_CSV_PATH),
        "filters_used": {
            "area": area,
            "min_rating": min_rating,
        },
    }


@pub_router.get("/pub/random/html", response_class=HTMLResponse)
def random_pub_html(
    area: Optional[str] = Query(default=None, description="Filter by area/neighbourhood"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating"),
):
    """
    HTML front-end for random pub selection.
    """
    result = random_pub(area=area, min_rating=min_rating)

    # If there's an error, show a simple error page
    if "error" in result:
        html_error = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Pub Checker</title>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    margin: 1.5rem;
                    background: #f5f5f5;
                    color: #333;
                }}
                .card {{
                    background: white;
                    padding: 1rem 1.2rem;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                }}
                button {{
                    padding: 0.5rem 1rem;
                    border-radius: 4px;
                    border: none;
                    background: #0078d4;
                    color: white;
                    font-size: 0.95rem;
                    cursor: pointer;
                }}
                .small {{
                    font-size: 0.9rem;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <h1>🍺 Pub Checker</h1>
            <div class="card">
                <h2>Error</h2>
                <p>{result.get("error")}</p>
                <p class="small">{result.get("hint","")}</p>
                <form method="get" action="/pub/random/html">
                    <button type="submit">Try again</button>
                </form>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_error)

    pub = result.get("pub", {}) or {}
    src = result.get("source_file")
    filters_used = result.get("filters_used", {})

    area_display = pub.get("area") or "Unknown"
    rating_display = pub.get("rating")
    if rating_display is None:
        rating_display = "N/A"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pub Checker</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 1.5rem;
                background: #f5f5f5;
                color: #333;
            }}
            .card {{
                background: white;
                padding: 1rem 1.2rem;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                max-width: 480px;
            }}
            h1 {{
                margin-bottom: 1rem;
            }}
            h2 {{
                margin-top: 0;
            }}
            .label {{
                font-weight: 600;
            }}
            .small {{
                font-size: 0.9rem;
                color: #666;
            }}
            button {{
                padding: 0.5rem 1rem;
                border-radius: 4px;
                border: none;
                background: #0078d4;
                color: white;
                font-size: 0.95rem;
                cursor: pointer;
            }}
            button:hover {{
                background: #005a9e;
            }}
            input {{
                padding: 0.4rem 0.6rem;
                margin-right: 0.3rem;
                border-radius: 4px;
                border: 1px solid #ccc;
                font-size: 0.9rem;
            }}
            form {{
                margin-top: 0.8rem;
                margin-bottom: 0.5rem;
            }}
            a.button-link {{
                text-decoration: none;
            }}
            a.button-link button {{
                margin-top: 0.5rem;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <h1>🍺 Pub Checker</h1>
        <div class="card">
            <h2>{pub.get("name")}</h2>
            <p><span class="label">Area:</span> {area_display}</p>
            <p><span class="label">Rating:</span> {rating_display}</p>
            <p><span class="label">Notes:</span> {pub.get("notes") or ""}</p>

            <p class="small">Source: {src}</p>

            <form method="get" action="/pub/random/html">
                <input type="text" name="area" placeholder="Area (optional)" value="{filters_used.get("area") or ""}" />
                <input type="number" step="0.1" name="min_rating" placeholder="Min rating" value="{filters_used.get("min_rating") or ""}" />
                <button type="submit">Another pub (with filters)</button>
            </form>

            <form method="get" action="/pub/random/html">
                <button type="submit">Totally random</button>
            </form>

            <a class="button-link" href="/pub/history/html">
                <button type="button">View history</button>
            </a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@pub_router.get("/pub/history")
def pub_history(limit: int = Query(default=50, ge=1, le=500)):
    """
    JSON API: return the last N pub selections (newest first).
    """
    entries = _read_pub_history(limit=limit)
    return {
        "limit": limit,
        "count": len(entries),
        "entries": entries,
        "history_file": str(PUB_HISTORY_FILE),
    }


@pub_router.get("/pub/history/html", response_class=HTMLResponse)
def pub_history_html(limit: int = Query(default=50, ge=1, le=500)):
    """
    HTML front-end showing last N pub selections.
    """
    entries = _read_pub_history(limit=limit)

    rows_html = ""
    for e in entries:
        rows_html += f"""
        <tr>
            <td>{e.get("time_utc","")}</td>
            <td>{e.get("name","")}</td>
            <td>{e.get("area","") or ""}</td>
            <td>{e.get("rating","") if e.get("rating") is not None else ""}</td>
            <td>{e.get("notes","") or ""}</td>
        </tr>
        """

    if not rows_html:
        rows_html = """
        <tr>
            <td colspan="5" style="text-align:center; color:#666;">No pub history yet.</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pub History</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                margin: 1.5rem;
                background: #f5f5f5;
                color: #333;
            }}
            .card {{
                background: white;
                padding: 1rem 1.2rem;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 0.5rem;
            }}
            th, td {{
                padding: 0.5rem;
                border-bottom: 1px solid #ddd;
                font-size: 0.9rem;
                text-align: left;
            }}
            th {{
                background: #f0f0f0;
            }}
            .small {{
                font-size: 0.9rem;
                color: #666;
            }}
            button {{
                padding: 0.5rem 1rem;
                border-radius: 4px;
                border: none;
                background: #0078d4;
                color: white;
                font-size: 0.95rem;
                cursor: pointer;
            }}
            button:hover {{
                background: #005a9e;
            }}
            .controls {{
                margin-bottom: 0.8rem;
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
            }}
            input {{
                padding: 0.4rem 0.6rem;
                border-radius: 4px;
                border: 1px solid #ccc;
                font-size: 0.9rem;
                width: 80px;
            }}
            a {{
                text-decoration: none;
            }}
        </style>
        <script>
            function reloadPage() {{
                window.location.reload();
            }}
        </script>
    </head>
    <body>
        <h1>🍺 Pub History</h1>
        <div class="card">
            <div class="controls">
                <form method="get" action="/pub/history/html">
                    <span class="small">Show last</span>
                    <input type="number" name="limit" value="{limit}" min="1" max="500" />
                    <span class="small">entries</span>
                    <button type="submit">Update</button>
                </form>
                <button onclick="reloadPage()">Refresh</button>
                <a href="/pub/random/html">
                    <button type="button">New pub</button>
                </a>
                <a href="/">
                    <button type="button">API Home</button>
                </a>
            </div>

            <p class="small">
                History file: {PUB_HISTORY_FILE}
            </p>

            <table>
                <thead>
                    <tr>
                        <th>Time (UTC)</th>
                        <th>Name</th>
                        <th>Area</th>
                        <th>Rating</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)
