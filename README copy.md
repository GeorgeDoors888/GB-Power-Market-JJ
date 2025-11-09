# GB Energy Dashboard — v2.2 (Apps Script + BigQuery + Vercel Proxy)

This bundle contains:
- **Apps Script** (`apps_script/google_sheets_dashboard_v2.gs`) — Live dashboard with 5‑min auto‑refresh, IC vs Spread overlay, and Calendar heatmaps.
- **Python analytics** (`python/advanced_stats_bigquery.py`) — Full statistical suite writing results to `uk_energy_analysis`.
- **SQL views** (`sql/views/*.sql`) — Canonical HH views (prices, gen/dem, interconnector, BOALF, BOD VWAPs) and daily SSP/SBP for Calendar.
- **Docs** (`docs/*.md`) — Setup guides and capabilities.

## Quick Start
1. Open your Sheet → Extensions → Apps Script → Paste `google_sheets_dashboard_v2.gs` → **Save**.
2. Run `Setup_Dashboard_AutoRefresh()` once → Authorize → Menu **⚡ Power Market** appears.
3. Data auto-refreshes every 5 minutes via Vercel proxy: `https://gb-power-market-jj.vercel.app/api/proxy-v2`.

## Python
Edit CONFIG in `python/advanced_stats_bigquery.py` then run via your Codex server `/execute` or locally.
Writes to: `jibber-jabber-knowledge.uk_energy_analysis` (adjust in script).

## SQL
Deploy views in BigQuery UI or `bq query --use_legacy_sql=false < file.sql`.
