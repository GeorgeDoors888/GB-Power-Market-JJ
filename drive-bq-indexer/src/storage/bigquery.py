from __future__ import annotations
from google.cloud import bigquery
from .schemas import BQ_SCHEMAS
from ..auth.google_auth import bq_client

def ensure_tables(dataset: str):
    client = bq_client()
    for table in ("documents", "chunks", "chunk_embeddings"):
        schema = [bigquery.SchemaField(**fld) for fld in BQ_SCHEMAS[table]]
        tid = bigquery.Table(f"{client.project}.{dataset}.{table}", schema=schema)
        try:
            client.get_table(tid)
        except Exception:
            client.create_table(tid)

def load_rows(dataset: str, table: str, rows: list[dict]):
    client = bq_client()
    table_id = f"{client.project}.{dataset}.{table}"
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        raise RuntimeError(errors)
