#!/usr/bin/env bash
set -euo pipefail
echo "🚀 Starting full Drive→BQ indexing pipeline"
python -m src.cli index-drive
python -m src.cli extract --parallel "${MAX_WORKERS:-4}" --ocr "${OCR_MODE:-auto}"
python -m src.cli build-embeddings --provider "${EMBED_PROVIDER:-vertex}"
python -m src.cli quality-check --auto-tune
echo "✅ All steps complete"
