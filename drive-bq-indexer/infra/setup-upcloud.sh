#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y docker.io python3-pip
sudo systemctl enable --now docker
mkdir -p /opt/driveindexer/secrets
chmod 700 /opt/driveindexer/secrets
echo "✅ UpCloud host ready for Drive→BigQuery Indexer"
