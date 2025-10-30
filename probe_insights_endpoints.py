#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import pandas as pd
import requests
import yaml


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def probe_endpoint(
    base_url: str,
    endpoint_cfg: Dict[str, Any],
    api_key: str,
    from_dt: datetime,
    to_dt: datetime,
) -> Dict[str, Any]:
    name = endpoint_cfg.get("name", "unnamed")
    path = endpoint_cfg.get("path", "")
    if not path:
        return {"name": name, "status": "FAIL", "reason": "Missing path in config"}

    url = f"{base_url}{path}"
    from_param = endpoint_cfg.get("from_param", "from")
    to_param = endpoint_cfg.get("to_param", "to")
    fmt = endpoint_cfg.get("format", "csv")

    params = {
        from_param: from_dt.isoformat(),
        to_param: to_dt.isoformat(),
        "format": fmt,
    }
    headers = {"Accept": f"application/{fmt}"}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        r = requests.get(url, params=params, timeout=(5, 30), headers=headers)
        r.raise_for_status()
        return {"name": name, "status": "OK", "http_code": r.status_code, "url": r.url}
    except requests.HTTPError as e:
        return {
            "name": name,
            "status": "FAIL",
            "http_code": e.response.status_code,
            "reason": str(e),
            "url": e.response.url,
        }
    except Exception as e:
        return {"name": name, "status": "FAIL", "reason": str(e), "url": url}


def main():
    ap = argparse.ArgumentParser(
        description="Probe Elexon Insights API endpoints from a YAML config."
    )
    ap.add_argument("--config", required=True, help="Path to insights_endpoints.yml")
    ap.add_argument(
        "--days",
        type=int,
        default=1,
        help="Number of past days to query for the probe.",
    )
    ap.add_argument(
        "--out", default="insights_probe.tsv", help="Output TSV file for results."
    )
    args = ap.parse_args()

    try:
        cfg = load_config(args.config)
    except Exception as e:
        print(f"Error loading YAML config {args.config}: {e}", file=sys.stderr)
        sys.exit(1)

    base_url = cfg.get("base_url")
    endpoints = cfg.get("endpoints", [])
    if not base_url or not endpoints:
        print(
            "Config must contain 'base_url' and a list of 'endpoints'.", file=sys.stderr
        )
        sys.exit(1)

    api_key = os.getenv("ELEXON_API_KEY", "")
    if not api_key:
        print("Warning: ELEXON_API_KEY environment variable not set.", file=sys.stderr)

    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=args.days)

    results = []
    for endpoint in endpoints:
        if isinstance(endpoint, dict) and endpoint.get("name"):
            # Skip param fanout jobs for probing
            if "param_lists" in endpoint:
                print(f"Skipping probe for fan-out endpoint: {endpoint['name']}")
                continue
            print(f"Probing: {endpoint['name']}...")
            res = probe_endpoint(base_url, endpoint, api_key, start_dt, end_dt)
            results.append(res)

    df = pd.DataFrame(results)
    df.to_csv(args.out, sep="\t", index=False)
    print(f"\nProbe complete. Results saved to {args.out}")

    ok_count = len(df[df["status"] == "OK"])
    fail_count = len(df[df["status"] == "FAIL"])
    print(f"Summary: {ok_count} OK, {fail_count} FAIL")


if __name__ == "__main__":
    main()
