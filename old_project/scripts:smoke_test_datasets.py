import os
import requests
import pandas as pd
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")
INSIGHTS_BASE_URL = os.getenv("INSIGHTS_BASE_URL")

with open("config/datasets.yml") as f:
    cfg = yaml.safe_load(f)

start_date = (datetime.utcnow() - timedelta(days=14)).strftime("%Y-%m-%d")
end_date = datetime.utcnow().strftime("%Y-%m-%d")

def test_endpoint(name, url):
    print(f"=== Testing {name} ===")
    params = {"from": start_date, "to": end_date, "apiKey": BMRS_API_KEY}
    r = requests.get(url, params=params)
    print(f"Status: {r.status_code}")
    if r.ok:
        try:
            df = pd.DataFrame(r.json().get("data", []))
            print(f"Rows: {len(df)}")
            if not df.empty:
                print(df.head(3))
        except Exception as e:
            print(f"Parse error: {e}")
    print()

for name, url in cfg["datasets"].items():
    test_endpoint(name, url)

for name, url in cfg["balancing"].items():
    test_endpoint(name, url)