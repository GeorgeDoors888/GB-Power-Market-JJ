# Security
- Service account scoped to Drive (read) + BigQuery (write) + Vision (optional)
- No SA JSON committed; mount at runtime
- `.env` only on hosts; GitHub Actions injects secrets at deploy time
- GDPR: filter private folders with allowlist/denylist in `config/settings.yaml`
