.PHONY: install run today views

# Load credentials and sheet ID from .env
include .env
export

install:
	python3 -m venv .venv && . .venv/bin/activate && pip install -U pip -q && pip install -r requirements.txt

run:
	. .venv/bin/activate && python tools/refresh_live_dashboard.py

today:
	. .venv/bin/activate && python tools/refresh_live_dashboard.py --date $$(TZ=Europe/London date +%F)

views:
	bq query --use_legacy_sql=false < tools/bigquery_views.sql
