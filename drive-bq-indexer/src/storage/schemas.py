from __future__ import annotations
import yaml

with open("config/bigquery_schemas.yaml", "r") as f:
    BQ_SCHEMAS = yaml.safe_load(f)
