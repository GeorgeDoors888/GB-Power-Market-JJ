from __future__ import annotations
from ..auth.google_auth import bq_client

METRICS_SQL = {
    "avg_chars": "SELECT AVG(n_chars) avg_chars FROM `{p}.{d}.chunks`",
    "ocr_rate":  "SELECT SUM(IF(n_chars<50,1,0))/COUNT(*) ocr_like_rate FROM `{p}.{d}.chunks`",
}

def fetch_metrics(dataset: str) -> dict:
    client = bq_client()
    out = {}
    for k, sql in METRICS_SQL.items():
        q = sql.format(p=client.project, d=dataset)
        rows = client.query(q).result()
        for r in rows:
            out[k] = list(r.values())[0]
    return out
