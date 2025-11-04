# Operations

## One-off full backfill (UpCloud)

Runs: `index → extract → embeddings → quality → (prints tuning suggestions)`

## Daily incremental (cron/systemd timer)
- `index-drive --modified-since <yesterday>` *(extend CLI as needed)*
- `extract` *(skips unchanged if you add sha checks)*
- `build-embeddings` *(only-new query already included)*
- `quality-check --auto-tune`

## Runbooks
- **High OCR rate** → enable Vision, reduce parallelism, or increase CPU/RAM
- **Tiny chunks** → increase `CHUNK_SIZE`, reduce `CHUNK_OVERLAP`
- **BQ load errors** → check schema drift vs `config/bigquery_schemas.yaml`
