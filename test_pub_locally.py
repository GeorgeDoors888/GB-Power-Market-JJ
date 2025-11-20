#!/usr/bin/env python3
"""
Quick test script to run just the pub endpoints locally
No BigQuery/Sheets credentials needed!
"""

from fastapi import FastAPI
from pub_endpoints import pub_router
import uvicorn

app = FastAPI(title="Pub Checker Test", version="1.0.0")
app.include_router(pub_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Pub checker test server",
        "endpoints": [
            "/pub/random",
            "/pub/random/html",
            "/pub/history",
            "/pub/history/html",
            "/docs"
        ]
    }

if __name__ == "__main__":
    print("🍺 Starting pub checker test server...")
    print("📍 Endpoints:")
    print("   - http://localhost:8000/pub/random")
    print("   - http://localhost:8000/pub/random/html")
    print("   - http://localhost:8000/pub/history/html")
    print("   - http://localhost:8000/docs (API documentation)")
    print("\n✨ Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
