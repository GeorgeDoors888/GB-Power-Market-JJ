from __future__ import annotations
from ..auth.google_auth import bq_client

SIM_SQL = """
SELECT doc_id, chunk_id, text,
  (SELECT SUM(a*b) FROM UNNEST(vector) a WITH OFFSET i
   JOIN UNNEST(@qvec) b WITH OFFSET j ON i=j) AS score
FROM `{p}.{d}.chunk_embeddings` ce
JOIN `{p}.{d}.chunks` c USING (doc_id, chunk_id)
ORDER BY score DESC
LIMIT @k
"""

def topk(dataset: str, qvec: list[float], k: int = 5):
    client = bq_client()
    job = client.query(
        SIM_SQL.format(p=client.project, d=dataset),
        job_config=client._query_job_config(
            query_parameters=[
                client.ScalarQueryParameter("k", "INT64", k),
                client.ArrayQueryParameter("qvec", "FLOAT64", qvec),
            ]
        ),
    )
    return [dict(r) for r in job.result()]
