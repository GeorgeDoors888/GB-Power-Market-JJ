import os
import requests
import pandas as pd
import yaml
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BMRS_API_KEY = os.getenv("BMRS_API_KEY")

with open("config/datasets.yml") as f:
    cfg = yaml.safe_load(f)

out_dir = Path("data")
out_dir.mkdir(exist_ok=True)

today = datetime.utcnow().strftime("%Y-%m-%d")

def fetch_and_save(name, url):
    params = {"from": today, "to": today, "apiKey": BMRS_API_KEY}
    r = requests.get(url, params=params)
    if r.ok:
        df = pd.DataFrame(r.json().get("data", []))
        file_path = out_dir / f"{name}_{today}.csv"
        df.to_csv(file_path, index=False)
        print(f"Saved {len(df)} rows to {file_path}")
    else:
        print(f"Failed {name}: {r.status_code}")

for name, url in {**cfg["datasets"], **cfg["balancing"]}.items():
    fetch_and_save(name, url)