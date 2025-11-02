# Setup

## Prerequisites
- Python **3.11+**
- Google Cloud SDK (`gcloud`) with your project set
- BigQuery dataset in `europe-west2`
- UpCloud Ubuntu 22.04 host with Docker & systemd (for long runs)

## Environment
Copy `.env.sample` → `.env` and fill values:

## Local dev (Codespaces minimal)
Codespaces/devcontainers are kept lightweight — PR/tests only. Long jobs run on UpCloud.

## UpCloud deploy
1. Copy SA JSON to `/opt/driveindexer/secrets/sa.json` (chmod 600)
2. Copy `.env` to `/opt/driveindexer/.env`
3. Build & run:
   ```bash
   docker build -f infra/docker/Dockerfile.runtime -t driveindexer:latest .
   docker run -d --name driveindexer --restart=always \
     --env-file /opt/driveindexer/.env \
     -v /opt/driveindexer/secrets:/secrets \
     -p 8080:8080 driveindexer:latest
   ```
